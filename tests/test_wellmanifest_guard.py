"""Tests for Wellmanifest governance guard and worktree manager."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from prefact.config import Config
from prefact.fixer import Fixer
from prefact.models import Fix, Issue, Severity
from prefact.wellmanifest import (
    TicketAllocation,
    WellmanifestViolationError,
    WellmanifestWorktreeManager,
    find_wellmanifest_root,
    is_safe_to_modify,
    is_wellmanifest_repo,
)


def test_non_wellmanifest_repo_detection(tmp_path: Path):
    non_gov = tmp_path / "plain_repo"
    non_gov.mkdir()
    assert find_wellmanifest_root(non_gov) is None
    assert is_wellmanifest_repo(non_gov) is False

    safe, msg = is_safe_to_modify(non_gov / "foo.py")
    assert safe is True
    assert "not inside a Wellmanifest" in msg


def test_wellmanifest_repo_detection_and_guard(tmp_path: Path):
    gov_repo = tmp_path / "gov_repo"
    gov_repo.mkdir()
    (gov_repo / ".git").mkdir()
    (gov_repo / "project").mkdir()
    (gov_repo / "project" / "new-ticket.sh").write_text("#!/bin/bash\n")
    (gov_repo / "project" / "new-ticket.sh").chmod(0o755)

    assert find_wellmanifest_root(gov_repo) == gov_repo
    assert is_wellmanifest_repo(gov_repo) is True

    # Test when on branch 'main'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")
        safe, msg = is_safe_to_modify(gov_repo / "src" / "app.py")
        assert safe is False
        assert "Blocked by Wellmanifest Host Contract" in msg
        assert "Modifying files directly on 'main'" in msg

    # Test when inside .worktrees/ticket-101/
    worktree_file = gov_repo / ".worktrees" / "ticket-101" / "src" / "app.py"
    worktree_file.parent.mkdir(parents=True)
    worktree_file.write_text("x = 1\n")
    safe, msg = is_safe_to_modify(worktree_file)
    assert safe is True
    assert "isolated ticket worktree" in msg

    # Test when on branch 'ticket/101-fix'
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="ticket/101-fix\n", stderr="")
        safe, msg = is_safe_to_modify(gov_repo / "src" / "app.py")
        assert safe is True
        assert "ticket branch" in msg


def test_fixer_blocks_modification_on_main(tmp_path: Path):
    gov_repo = tmp_path / "gov_repo"
    gov_repo.mkdir()
    (gov_repo / ".git").mkdir()
    (gov_repo / "project").mkdir()
    (gov_repo / "project" / "new-ticket.sh").write_text("#!/bin/bash\n")

    target_file = gov_repo / "main_code.py"
    target_file.write_text("original = 1\n")

    cfg = Config()
    cfg.enforce_wellmanifest = True
    cfg.allow_dirty_checkout = False
    fixer = Fixer(cfg)

    issue = Issue(
        rule_id="test-rule",
        file=target_file,
        line=1,
        col=0,
        message="test issue",
        severity=Severity.ERROR,
    )

    dummy_fix = Fix(
        issue=issue,
        file=target_file,
        original_code="original = 1\n",
        fixed_code="modified = 2\n",
        applied=True,
    )
    dummy_rule = MagicMock()
    dummy_rule.fix.return_value = ("modified = 2\n", [dummy_fix])
    fixer._rules["test-rule"] = dummy_rule

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")
        source, fixes = fixer.fix_file_with_source(target_file, "original = 1\n", [issue])
        # Fixer should have blocked the modification!
        assert fixes == []
        assert target_file.read_text() == "original = 1\n"

    # Now test with allow_dirty_checkout=True
    cfg.allow_dirty_checkout = True
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n", stderr="")
        source, fixes = fixer.fix_file_with_source(target_file, "original = 1\n", [issue])
        assert len(fixes) == 1
        assert target_file.read_text() == "modified = 2\n"


def test_worktree_manager_merge_disposition(tmp_path: Path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "project").mkdir()
    new_ticket = repo_root / "project" / "new-ticket.sh"
    new_ticket.write_text("#!/bin/bash\n")
    new_ticket.chmod(0o755)

    gov_check = repo_root / "project" / "governance-check.sh"
    gov_check.write_text("#!/bin/bash\nexit 0\n")
    gov_check.chmod(0o755)

    mgr = WellmanifestWorktreeManager(repo_root)
    assert mgr.can_allocate() is True

    wt_dir = repo_root / ".worktrees" / "ticket-999"
    wt_dir.mkdir(parents=True)

    allocation = TicketAllocation(
        ticket_id="ticket-999",
        worktree_path=wt_dir,
        branch_name="ticket/999",
        repo_root=repo_root,
    )

    decision = mgr.evaluate_merge_disposition(allocation)
    assert decision["schema"] == "wellmanifest.merge-decision/v1"
    assert decision["disposition"] == "adopt"
    assert decision["candidate"]["ticketId"] == "ticket-999"
    assert decision["evidence"]["governancePassed"] is True
