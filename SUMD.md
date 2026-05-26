# prefact

Python code quality tool with LLM-aware rules, plugin system, and enterprise features

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `prefact`
- **version**: `0.0.0`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(3 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: prefact;
  version: 0.0.0;
}

dependencies {
  runtime: "ast-decompiler>=0.7.0, click>=8.0.0, libcst>=0.4.0, pyyaml>=6.0, rich>=12.0.0, tomli>=2.0.0; python_version<'3.11', goal>=2.1.218, costs>=0.1.20, pfix>=0.1.60, planfile>=0.1.86";
  dev: "pytest>=7.0.0, pytest-cov>=4.0.0, pytest-asyncio>=0.21.0, black>=23.0.0, isort>=5.10.0, mypy>=1.0.0, ruff>=0.5.0, pre-commit>=3.0.0, goal>=2.1.218, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="prefact"] {

}

workflow[name="venv"] {
  trigger: manual;
  step-1: run cmd=if [ ! -x "$(PYTHON)" ]; then \;
  step-2: run cmd=echo "Creating virtual environment in $(VENV)..."; \;
  step-3: run cmd=python3 -m venv "$(VENV)"; \;
  step-4: run cmd=fi;
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e .;
  step-2: run cmd=echo "✓ code2llm installed with TOON format support";
}

workflow[name="dev-install"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e ".[dev]";
  step-2: run cmd=echo "✓ code2llm installed with dev dependencies";
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest tests/ -v --tb=short;
}

workflow[name="test-fast"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -m "not slow and not integration" -v --tb=short -n auto;
}

workflow[name="test-slow"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -m "slow" -v --tb=short;
}

workflow[name="test-integration"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -m "integration" -v --tb=short;
}

workflow[name="test-unit"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest -m "unit" -v --tb=short;
}

workflow[name="test-cov"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m pytest tests/ --cov=code2llm --cov-report=html --cov-report=term 2>/dev/null || echo "No tests yet";
}

workflow[name="test-toon"] {
  trigger: manual;
  step-1: run cmd=echo "🎯 Testing TOON format...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./test_toon -m hybrid -f toon;
  step-3: run cmd=$(PYTHON) validate_toon.py test_toon/analysis.toon;
  step-4: run cmd=echo "✓ TOON format test complete";
}

workflow[name="validate-toon"] {
  trigger: manual;
  step-1: depend target=test-toon;
}

workflow[name="test-all-formats"] {
  trigger: manual;
  step-1: run cmd=echo "📊 Testing all output formats...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./test_all -m hybrid -f all;
  step-3: run cmd=$(PYTHON) validate_toon.py test_all/analysis.toon;
  step-4: run cmd=echo "✓ All formats test complete";
}

workflow[name="test-comprehensive"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Running comprehensive test suite...";
  step-2: run cmd=bash project.sh;
  step-3: run cmd=echo "✓ Comprehensive tests complete";
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m flake8 code2llm/ --max-line-length=100 --ignore=E203,W503 2>/dev/null || echo "flake8 not installed";
  step-2: run cmd=$(PYTHON) -m black --check code2llm/ 2>/dev/null || echo "black not installed";
  step-3: run cmd=echo "✓ Linting complete";
}

workflow[name="format"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m black code2llm/ --line-length=100 2>/dev/null || echo "black not installed, run: pip install black";
  step-2: run cmd=echo "✓ Code formatted";
}

workflow[name="typecheck"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m mypy code2llm/ --ignore-missing-imports 2>/dev/null || echo "mypy not installed";
}

workflow[name="check"] {
  trigger: manual;
  step-1: run cmd=echo "✓ All checks passed";
}

workflow[name="run"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m code2llm ../python/stts_core -v -o ./output;
}

workflow[name="analyze"] {
  trigger: manual;
  step-1: run cmd=echo "🎯 Running TOON format analysis on current project...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./analysis -m hybrid -f toon;
  step-3: run cmd=$(PYTHON) validate_toon.py analysis/analysis.toon;
  step-4: run cmd=echo "✓ TOON analysis complete - check analysis/analysis.toon";
}

workflow[name="analyze-all"] {
  trigger: manual;
  step-1: run cmd=echo "📊 Running analysis with all formats...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./analysis_all -m hybrid -f all;
  step-3: run cmd=$(PYTHON) validate_toon.py analysis_all/analysis.toon;
  step-4: run cmd=echo "✓ All formats analysis complete - check analysis_all/";
}

workflow[name="toon-demo"] {
  trigger: manual;
  step-1: run cmd=echo "🎯 Quick TOON format demo...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./demo -m hybrid -f toon;
  step-3: run cmd=echo "📁 Generated: demo/analysis.toon";
  step-4: run cmd=echo "📊 Size: $$(du -h demo/analysis.toon | cut -f1)";
  step-5: run cmd=echo "🔍 Preview:";
  step-6: run cmd=head -20 demo/analysis.toon;
}

workflow[name="toon-compare"] {
  trigger: manual;
  step-1: run cmd=echo "📊 Comparing TOON vs YAML formats...";
  step-2: run cmd=$(PYTHON) -m code2llm ./ -v -o ./compare -m hybrid -f toon,yaml;
  step-3: run cmd=echo "📁 Files generated:";
  step-4: run cmd=echo "  - TOON:  compare/analysis.toon  ($$(du -h compare/analysis.toon | cut -f1))";
  step-5: run cmd=echo "  - YAML:  compare/analysis.yaml  ($$(du -h compare/analysis.yaml | cut -f1))";
  step-6: run cmd=echo "  - Ratio: $$(echo "scale=1; $$(du -k compare/analysis.yaml | cut -f1) / $$(du -k compare/analysis.toon | cut -f1)" | bc)x smaller";
  step-7: run cmd=$(PYTHON) validate_toon.py compare/analysis.yaml compare/analysis.toon;
}

workflow[name="toon-validate"] {
  trigger: manual;
  step-1: run cmd=echo "🔍 Validating TOON format structure...";
  step-2: run cmd=$(PYTHON) validate_toon.py analysis/analysis.toon 2>/dev/null || $(PYTHON) validate_toon.py test_toon/analysis.toon 2>/dev/null || echo "Run 'make test-toon' first";
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=rm -rf build/ dist/ *.egg-info;
  step-2: run cmd=$(PYTHON) -m build;
  step-3: run cmd=echo "✓ Build complete - check dist/";
}

workflow[name="publish-test"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Publishing to TestPyPI...";
  step-2: run cmd=bash -c 'if [ -z "$${TWINE_USERNAME}" ] && [ -z "$${TWINE_PASSWORD}" ] && [ -z "$${PYPI_API_TOKEN}" ]; then \;
  step-3: run cmd=echo "⚠️  No PyPI credentials found. Set TWINE_USERNAME and TWINE_PASSWORD or PYPI_API_TOKEN"; \;
  step-4: run cmd=echo "   Example: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx make publish-test"; \;
  step-5: run cmd=echo "   Skipping publish-test."; \;
  step-6: run cmd=else \;
  step-7: run cmd=$(PYTHON) -m venv publish-test-env && \;
  step-8: run cmd=publish-test-env/bin/pip install twine && \;
  step-9: run cmd=publish-test-env/bin/python -m twine upload --repository testpypi dist/* && \;
  step-10: run cmd=rm -rf publish-test-env && \;
  step-11: run cmd=echo "✓ Published to TestPyPI"; \;
  step-12: run cmd=fi';
}

workflow[name="bump-patch"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping patch version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py patch 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="bump-minor"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping minor version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py minor 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="bump-major"] {
  trigger: manual;
  step-1: run cmd=echo "🔢 Bumping major version...";
  step-2: run cmd=$(PYTHON) scripts/bump_version.py major 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually";
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Publishing to PyPI...";
  step-2: run cmd=bash -c 'if [ -z "$${TWINE_USERNAME}" ] && [ -z "$${TWINE_PASSWORD}" ] && [ -z "$${PYPI_API_TOKEN}" ]; then \;
  step-3: run cmd=echo "⚠️  No PyPI credentials found. Set TWINE_USERNAME and TWINE_PASSWORD or PYPI_API_TOKEN"; \;
  step-4: run cmd=echo "   Example: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx make publish"; \;
  step-5: run cmd=echo "   Skipping publish."; \;
  step-6: run cmd=else \;
  step-7: run cmd=echo "🔢 Bumping patch version..."; \;
  step-8: run cmd=$(MAKE) bump-patch; \;
  step-9: run cmd=echo "🔨 Rebuilding package with new version..."; \;
  step-10: run cmd=$(MAKE) build; \;
  step-11: run cmd=echo "📦 Publishing to PyPI..."; \;
  step-12: run cmd=$(PYTHON) -m venv publish-env; \;
  step-13: run cmd=publish-env/bin/pip install twine; \;
  step-14: run cmd=publish-env/bin/python -m twine upload dist/*; \;
  step-15: run cmd=rm -rf publish-env; \;
  step-16: run cmd=echo "✓ Published to PyPI"; \;
  step-17: run cmd=fi';
}

workflow[name="mermaid-png"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) mermaid_to_png.py --batch output output;
}

workflow[name="install-mermaid"] {
  trigger: manual;
  step-1: run cmd=npm install -g @mermaid-js/mermaid-cli;
}

workflow[name="check-mermaid"] {
  trigger: manual;
  step-1: run cmd=echo "Checking available Mermaid renderers...";
  step-2: run cmd=which mmdc > /dev/null && echo "✓ mmdc (mermaid-cli)" || echo "✗ mmdc (run: npm install -g @mermaid-js/mermaid-cli)";
  step-3: run cmd=which npx > /dev/null && echo "✓ npx (for @mermaid-js/mermaid-cli)" || echo "✗ npx (install Node.js)";
  step-4: run cmd=which puppeteer > /dev/null && echo "✓ puppeteer" || echo "✗ puppeteer (run: npm install -g puppeteer)";
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf build/ dist/ *.egg-info;
  step-2: run cmd=rm -rf .pytest_cache .coverage htmlcov/;
  step-3: run cmd=rm -rf code2llm/__pycache__ code2llm/*/__pycache__;
  step-4: run cmd=rm -rf test_* demo compare analysis analysis_all output_* 2>/dev/null || true;
  step-5: run cmd=find . -name "*.pyc" -delete 2>/dev/null || true;
  step-6: run cmd=find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true;
  step-7: run cmd=echo "✓ Cleaned build artifacts and test outputs";
}

workflow[name="clean-png"] {
  trigger: manual;
  step-1: run cmd=rm -f output/*.png;
  step-2: run cmd=echo "✓ Cleaned PNG files";
}

workflow[name="quickstart"] {
  trigger: manual;
  step-1: run cmd=echo "🚀 Quick Start with code2llm TOON format:";
  step-2: run cmd=echo "";
  step-3: run cmd=echo "1. Install:        make install";
  step-4: run cmd=echo "2. Test TOON:      make test-toon";
  step-5: run cmd=echo "3. Analyze:        make analyze";
  step-6: run cmd=echo "4. Compare:        make toon-compare";
  step-7: run cmd=echo "5. All formats:    make test-all-formats";
  step-8: run cmd=echo "";
  step-9: run cmd=echo "📖 For more: make help";
}

workflow[name="fmt"] {
  trigger: manual;
  step-1: run cmd=ruff format .;
}

workflow[name="health"] {
  trigger: manual;
  step-1: run cmd=docker compose ps;
  step-2: run cmd=docker compose exec app echo "Health check passed";
}

workflow[name="all"] {
  trigger: manual;
  step-1: run cmd=taskfile run install;
  step-2: run cmd=taskfile run lint;
  step-3: run cmd=taskfile run test;
}

workflow[name="help"] {
  trigger: manual;
  step-1: run cmd=echo "prefact — available tasks:";
  step-2: run cmd=echo "";
  step-3: run cmd=taskfile list;
}

workflow[name="sumd"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd))" > SUMD.md
echo "" >> SUMD.md
echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
echo "" >> SUMD.md
echo "## Contents" >> SUMD.md
echo "" >> SUMD.md
echo "- [Metadata](#metadata)" >> SUMD.md
echo "- [Architecture](#architecture)" >> SUMD.md
echo "- [Dependencies](#dependencies)" >> SUMD.md
echo "- [Source Map](#source-map)" >> SUMD.md
echo "- [Intent](#intent)" >> SUMD.md
echo "" >> SUMD.md
echo "## Metadata" >> SUMD.md
echo "" >> SUMD.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
echo "" >> SUMD.md
echo "## Architecture" >> SUMD.md
echo "" >> SUMD.md
echo '```' >> SUMD.md
echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
echo '```' >> SUMD.md
echo "" >> SUMD.md
echo "## Source Map" >> SUMD.md
echo "" >> SUMD.md
find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
echo "Generated SUMD.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
project_name = Path.cwd().name
py_files = list(Path('.').rglob('*.py'))
py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
data = {
    'project_name': project_name,
    'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
    'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
}
with open('sumd.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated sumd.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

workflow[name="sumr"] {
  trigger: manual;
  step-1: run cmd=echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
echo "" >> SUMR.md
echo "SUMR - Summary Report for project analysis" >> SUMR.md
echo "" >> SUMR.md
echo "## Contents" >> SUMR.md
echo "" >> SUMR.md
echo "- [Metadata](#metadata)" >> SUMR.md
echo "- [Quality Status](#quality-status)" >> SUMR.md
echo "- [Metrics](#metrics)" >> SUMR.md
echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
echo "- [Intent](#intent)" >> SUMR.md
echo "" >> SUMR.md
echo "## Metadata" >> SUMR.md
echo "" >> SUMR.md
echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
echo "" >> SUMR.md
echo "## Quality Status" >> SUMR.md
echo "" >> SUMR.md
if [ -f pyqual.yaml ]; then
  echo "- **pyqual_config**: ✅ Present" >> SUMR.md
  echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
else
  echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
fi
echo "" >> SUMR.md
echo "## Metrics" >> SUMR.md
echo "" >> SUMR.md
py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
echo "- **python_files**: $py_files" >> SUMR.md
lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
echo "- **total_lines**: $lines" >> SUMR.md
echo "" >> SUMR.md
echo "## Refactoring Analysis" >> SUMR.md
echo "" >> SUMR.md
echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
echo "Generated SUMR.md";
  step-2: run cmd=python3 -c "
import json, os, subprocess
from pathlib import Path
from datetime import datetime
project_name = Path.cwd().name
py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
data = {
    'project_name': project_name,
    'report_type': 'SUMR',
    'generated_at': datetime.now().isoformat(),
    'metrics': {
        'python_files': py_files,
        'has_pyqual_config': Path('pyqual.yaml').exists()
    }
}
with open('SUMR.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Generated SUMR.json')
" 2>/dev/null || echo 'Python generation failed, using fallback';
}

deploy {
  target: makefile;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  python_version: >=3.10;
}
```

## Interfaces

### CLI Entry Points

- `prefact`
- `prefact-scan`
- `prefact-fix`
- `prefact-config`
- `prefact-git-hooks`

### testql Scenarios

#### `testql-scenarios/generated-cli-tests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-cli-tests.testql.toon.yaml
# SCENARIO: CLI Command Tests
# TYPE: cli
# GENERATED: true

CONFIG[2]{key, value}:
  cli_command, python -mprefact
  timeout_ms, 10000

LOG[3]{message}:
  "Test CLI help command"
  "Test CLI version command"
  "Test CLI main workflow"
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

LOG[2]{message}:
  "Test: ScopeProviderTest_test_except_handler"
  "Test: test_except_handler"

INCLUDE[7]{file}:
  "/home/tom/github/semcod/prefact/tests/test_integrations.py"
  "/home/tom/github/semcod/prefact/tests/test_integrations.py"
  "/home/tom/github/semcod/prefact/tests/test_integrations.py"
  "/home/tom/github/semcod/prefact/tests/test_integrations.py"
  "/home/tom/github/semcod/prefact/.algitex/backups/batch_20260328_174839/examples/test_env/lib/python3.13/site-packages/libcst/tests/test_pyre_integration.py"
```

## Workflows

### Taskfile Tasks (`Taskfile.yml`)

```yaml markpact:taskfile path=Taskfile.yml
version: '1'
name: prefact
description: Minimal Taskfile
variables:
  APP_NAME: prefact
environments:
  local:
    container_runtime: docker
    compose_command: docker compose
pipeline:
  python_version: "3.12"
  runner_image: ubuntu-latest
  branches: [main]
  cache: [~/.cache/pip]
  artifacts: [dist/]

  stages:
    - name: lint
      tasks: [lint]

    - name: test
      tasks: [test]

    - name: build
      tasks: [build]
      when: "branch:main"

tasks:
  install:
    desc: Install Python dependencies (editable)
    cmds:
    - pip install -e .[dev]
  test:
    desc: Run pytest suite
    cmds:
    - pytest -q
  lint:
    desc: Run ruff lint check
    cmds:
    - ruff check .
  fmt:
    desc: Auto-format with ruff
    cmds:
    - ruff format .
  build:
    desc: Build wheel + sdist
    cmds:
    - python -m build
  clean:
    desc: Remove build artefacts
    cmds:
    - rm -rf build/ dist/ *.egg-info
  health:
    desc: '[from doql] workflow: health'
    cmds:
    - docker compose ps
    - docker compose exec app echo "Health check passed"
  all:
    desc: Run install, lint, test
    cmds:
    - taskfile run install
    - taskfile run lint
    - taskfile run test
  help:
    desc: Show available tasks
    cmds:
    - echo "prefact — available tasks:"
    - echo ""
    - taskfile list
  format:
    desc: Auto-format with ruff (alias of fmt)
    cmds:
    - ruff format .
  sumd:
    desc: Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description
    cmds:
    - |
      echo "# $(basename $(pwd))" > SUMD.md
      echo "" >> SUMD.md
      echo "$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('description','Project description'))" 2>/dev/null || echo 'Project description')" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Contents" >> SUMD.md
      echo "" >> SUMD.md
      echo "- [Metadata](#metadata)" >> SUMD.md
      echo "- [Architecture](#architecture)" >> SUMD.md
      echo "- [Dependencies](#dependencies)" >> SUMD.md
      echo "- [Source Map](#source-map)" >> SUMD.md
      echo "- [Intent](#intent)" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Metadata" >> SUMD.md
      echo "" >> SUMD.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMD.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMD.md
      echo "- **python_requires**: \`>=$(python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d. -f1,2)\`" >> SUMD.md
      echo "- **license**: $(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('license',{}).get('text','MIT'))" 2>/dev/null || echo 'MIT')" >> SUMD.md
      echo "- **ecosystem**: SUMD + DOQL + testql + taskfile" >> SUMD.md
      echo "- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/" >> SUMD.md
      echo "" >> SUMD.md
      echo "## Architecture" >> SUMD.md
      echo "" >> SUMD.md
      echo '```' >> SUMD.md
      echo "SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)" >> SUMD.md
      echo '```' >> SUMD.md
      echo "" >> SUMD.md
      echo "## Source Map" >> SUMD.md
      echo "" >> SUMD.md
      find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -not -path './__pycache__/*' -not -path './.git/*' | head -50 | sed 's|^./||' | sed 's|^|- |' >> SUMD.md
      echo "Generated SUMD.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      project_name = Path.cwd().name
      py_files = list(Path('.').rglob('*.py'))
      py_files = [f for f in py_files if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])]
      data = {
          'project_name': project_name,
          'description': 'SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization',
          'files': [{'path': str(f), 'type': 'python'} for f in py_files[:100]]
      }
      with open('sumd.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated sumd.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
  sumr:
    desc: Generate SUMR (Summary Report) with project metrics and health status
    cmds:
    - |
      echo "# $(basename $(pwd)) - Summary Report" > SUMR.md
      echo "" >> SUMR.md
      echo "SUMR - Summary Report for project analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Contents" >> SUMR.md
      echo "" >> SUMR.md
      echo "- [Metadata](#metadata)" >> SUMR.md
      echo "- [Quality Status](#quality-status)" >> SUMR.md
      echo "- [Metrics](#metrics)" >> SUMR.md
      echo "- [Refactoring Analysis](#refactoring-analysis)" >> SUMR.md
      echo "- [Intent](#intent)" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Metadata" >> SUMR.md
      echo "" >> SUMR.md
      echo "- **name**: \`$(basename $(pwd))\`" >> SUMR.md
      echo "- **version**: \`$(python3 -c "import tomllib; f=open('pyproject.toml','rb'); d=tomllib.load(f); print(d.get('project',{}).get('version','unknown'))" 2>/dev/null || echo 'unknown')\`" >> SUMR.md
      echo "- **generated_at**: \`$(date -Iseconds)\`" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Quality Status" >> SUMR.md
      echo "" >> SUMR.md
      if [ -f pyqual.yaml ]; then
        echo "- **pyqual_config**: ✅ Present" >> SUMR.md
        echo "- **last_run**: $(stat -c %y .pyqual/pipeline.db 2>/dev/null | cut -d' ' -f1 || echo 'N/A')" >> SUMR.md
      else
        echo "- **pyqual_config**: ❌ Missing" >> SUMR.md
      fi
      echo "" >> SUMR.md
      echo "## Metrics" >> SUMR.md
      echo "" >> SUMR.md
      py_files=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' | wc -l)
      echo "- **python_files**: $py_files" >> SUMR.md
      lines=$(find . -name '*.py' -not -path './.venv/*' -not -path './venv/*' -exec cat {} \; 2>/dev/null | wc -l)
      echo "- **total_lines**: $lines" >> SUMR.md
      echo "" >> SUMR.md
      echo "## Refactoring Analysis" >> SUMR.md
      echo "" >> SUMR.md
      echo "Run \`code2llm ./ -f evolution\` for detailed refactoring queue." >> SUMR.md
      echo "Generated SUMR.md"
    - |
      python3 -c "
      import json, os, subprocess
      from pathlib import Path
      from datetime import datetime
      project_name = Path.cwd().name
      py_files = len([f for f in Path('.').rglob('*.py') if not any(x in str(f) for x in ['.venv', 'venv', '__pycache__', '.git'])])
      data = {
          'project_name': project_name,
          'report_type': 'SUMR',
          'generated_at': datetime.now().isoformat(),
          'metrics': {
              'python_files': py_files,
              'has_pyqual_config': Path('pyqual.yaml').exists()
          }
      }
      with open('SUMR.json', 'w') as f:
          json.dump(data, f, indent=2)
      print('Generated SUMR.json')
      " 2>/dev/null || echo 'Python generation failed, using fallback'
```

## Quality Pipeline (`pyqual.yaml`)

```yaml markpact:pyqual path=pyqual.yaml
pipeline:
  name: prefact-quality-loop

  # ── Quality gates ─────────────────────────────────────────────────
  # Pipeline iterates until ALL pass
  metrics:
    cc_max: 15           # cyclomatic complexity per function
    vallm_pass_min: 60   # current: ~65%
    coverage_min: 40     # current: ~43%

  # ── Pipeline stages ───────────────────────────────────────────────
  # Use 'tool:' for built-in presets or 'run:' for custom commands.
  # Each test group is a separate stage so it can be controlled,
  # retried, or skipped independently.
  stages:

    # ── Analysis ────────────────────────────────────────────────────
    - name: analyze
      tool: code2llm
      when: first_iteration

    # ── Dependency freshness ────────────────────────────────────────
    - name: check-deps
      run: |
        prefact check-deps --path . --format json --max-outdated 0
      when: first_iteration
      timeout: 180

    # ── Unit tests (by marker) ──────────────────────────────────────
    - name: test-config
      run: .venv/bin/pytest -m config --tb=short -q
      timeout: 60

    - name: test-engine
      run: .venv/bin/pytest -m engine --tb=short -q
      timeout: 120

    - name: test-rules
      run: .venv/bin/pytest -m rules --tb=short -q
      timeout: 120

    - name: test-relative-imports
      run: .venv/bin/pytest -m relative_imports --tb=short -q
      timeout: 60

    - name: test-unused-imports
      run: .venv/bin/pytest -m unused_imports --tb=short -q
      timeout: 60

    - name: test-deps
      run: .venv/bin/pytest -m deps --tb=short -q
      timeout: 60

    # ── Integration tests (by marker) ───────────────────────────────
    - name: test-ruff
      run: .venv/bin/pytest -m ruff --tb=short -q
      timeout: 120
      optional: true

    - name: test-mypy
      run: .venv/bin/pytest -m mypy --tb=short -q
      timeout: 120
      optional: true

    - name: test-isort
      run: .venv/bin/pytest -m isort --tb=short -q
      timeout: 120
      optional: true

    - name: test-autoflake
      run: .venv/bin/pytest -m autoflake --tb=short -q
      timeout: 120
      optional: true

    # ── Coverage ────────────────────────────────────────────────────
    - name: coverage
      run: |
        .venv/bin/pytest --cov=src/prefact --cov-report=json:.pyqual/coverage.json -m "not slow" -q
      timeout: 300

    # ── Validation ──────────────────────────────────────────────────
    - name: validate
      tool: vallm

    # ── Prefact self-scan ───────────────────────────────────────────
    - name: prefact
      tool: prefact
      optional: true
      when: any_stage_fail
      timeout: 900

    # ── LLX-powered code fix ────────────────────────────────────────
    - name: fix
      tool: llx-fix
      optional: true
      when: any_stage_fail
      timeout: 1800

    # ── Post-fix verification ───────────────────────────────────────
    - name: verify
      tool: vallm
      optional: true
      when: after_fix
      timeout: 300

    # ── Performance benchmark ───────────────────────────────────────
    - name: benchmark
      run: |
        mkdir -p .pyqual
        .venv/bin/pytest -m performance --tb=short -q 2>&1 | tee .pyqual/benchmark.txt
      when: always
      optional: true
      timeout: 300

  # ── Loop behavior ─────────────────────────────────────────────────
  loop:
    max_iterations: 3
    on_fail: report      # report | create_ticket | block

  # ── Environment (optional) ────────────────────────────────────────
  env:
    LLM_MODEL: openrouter/qwen/qwen3-coder-next
    LLX_DEFAULT_TIER: balanced
    LLX_VERBOSE: true
```

## Configuration

```yaml
project:
  name: prefact
  version: 0.0.0
  env: local
```

## Dependencies

### Runtime

```text markpact:deps python
ast-decompiler>=0.7.0
click>=8.0.0
libcst>=0.4.0
pyyaml>=6.0
rich>=12.0.0
tomli>=2.0.0; python_version<'3.11'
goal>=2.1.218
costs>=0.1.20
pfix>=0.1.60
planfile>=0.1.86
```

### Development

```text markpact:deps python scope=dev
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
isort>=5.10.0
mypy>=1.0.0
ruff>=0.5.0
pre-commit>=3.0.0
goal>=2.1.218
costs>=0.1.20
pfix>=0.1.60
```

## Deployment

```bash markpact:run
pip install prefact

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `*(not set)*` | Required: OpenRouter API key (https://openrouter.ai/keys) |
| `PFIX_MODEL` | `openrouter/qwen/qwen3-coder-next` | Model (default: openrouter/qwen/qwen3-coder-next) |
| `PFIX_AUTO_APPLY` | `true` | true = apply fixes without asking |
| `PFIX_AUTO_INSTALL_DEPS` | `true` | true = auto pip/uv install |
| `PFIX_AUTO_RESTART` | `false` | true = os.execv restart after fix |
| `PFIX_MAX_RETRIES` | `3` |  |
| `PFIX_DRY_RUN` | `false` |  |
| `PFIX_ENABLED` | `true` |  |
| `PFIX_GIT_COMMIT` | `false` | true = auto-commit fixes |
| `PFIX_GIT_PREFIX` | `pfix:` | commit message prefix |
| `PFIX_CREATE_BACKUPS` | `false` | false = disable .pfix_backups/ directory |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`prefact`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `venv/lib/python3.13/site-packages/cryptography/__init__.py:__version__`

## Makefile Targets

- `VENV`
- `PYTHON`
- `PIP`
- `help` — Default target
- `venv`
- `VENV_TARGETS`
- `install`
- `dev-install`
- `test`
- `test-fast` — Fast tests - exclude slow and integration tests
- `test-slow` — Slow tests only
- `test-integration` — Integration tests only
- `test-unit` — Unit tests only
- `test-cov`
- `test-toon`
- `validate-toon`
- `test-all-formats`
- `test-comprehensive`
- `lint`
- `format`
- `typecheck`
- `check`
- `run`
- `analyze`
- `analyze-all`
- `toon-demo`
- `toon-compare`
- `toon-validate`
- `build`
- `publish-test`
- `bump-patch`
- `bump-minor`
- `bump-major`
- `publish`
- `mermaid-png`
- `install-mermaid`
- `check-mermaid`
- `clean`
- `clean-png`
- `quickstart`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# prefact | 129f 18582L | python:121,shell:3,javascript:2,css:1,less:1,typescript:1 | 2026-05-24
# stats: 182 func | 158 cls | 129 mod | CC̄=3.0 | critical:5 | cycles:0
# alerts[5]: CC print_report=14; CC _match_gitignore_pattern=12; CC run_prefact_example=11; CC test_run_testql_creates_and_syncs_tickets=11; CC _collect_all_exports=10
# hotspots[5]: run_integration_tests fan=16; main fan=13; cached_file_operation fan=13; test_ruff_integration fan=13; test_performance_comparison fan=13
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[129]:
  app.doql.css,74
  app.doql.less,424
  benchmark_ram_optimization.py,236
  examples/01-individual-rules/duplicate-imports/after.py,9
  examples/01-individual-rules/duplicate-imports/before.py,9
  examples/01-individual-rules/missing-return-type/after.py,20
  examples/01-individual-rules/missing-return-type/before.py,20
  examples/01-individual-rules/print-statements/after.py,16
  examples/01-individual-rules/print-statements/before.py,16
  examples/01-individual-rules/relative-imports/after.py,27
  examples/01-individual-rules/relative-imports/before.py,27
  examples/01-individual-rules/sorted-imports/after.py,7
  examples/01-individual-rules/sorted-imports/before.py,7
  examples/01-individual-rules/string-concat/after.py,14
  examples/01-individual-rules/string-concat/before.py,14
  examples/01-individual-rules/unused-imports/after.py,42
  examples/01-individual-rules/unused-imports/before.py,42
  examples/01-individual-rules/wildcard-imports/after.py,14
  examples/01-individual-rules/wildcard-imports/before.py,14
  examples/02-multiple-rules/messy_module.py,55
  examples/03-output-formats/sample_code.py,18
  examples/04-custom-rules/custom_rules/__init__.py,7
  examples/04-custom-rules/custom_rules/no_todo_rule.py,113
  examples/06-api-usage/example.py,199
  examples/generate_examples.py,233
  examples/run_all.sh,144
  examples/run_examples.py,138
  examples/sample-project/cli.py,63
  examples/sample-project/core.py,37
  examples/sample-project/models.py,60
  examples/sample-project/utils.py,41
  examples/tests/test_examples.py,7
  project.sh,47
  src/prefact/__init__.py,4
  src/prefact/_base.py,7
  src/prefact/autonomous/__init__.py,313
  src/prefact/autonomous/_base.py,74
  src/prefact/autonomous/dependency_checker.py,238
  src/prefact/autonomous/docs_manager.py,286
  src/prefact/autonomous/project_scanner.py,297
  src/prefact/autonomous/setup_manager.py,143
  src/prefact/autonomous/testql_manager.py,219
  src/prefact/autonomous/todo_manager.py,431
  src/prefact/autonomous.py,18
  src/prefact/benchmark.py,312
  src/prefact/cli.py,425
  src/prefact/config.py,178
  src/prefact/config_extended/__init__.py,13
  src/prefact/config_extended/config.py,143
  src/prefact/config_extended/constants.py,16
  src/prefact/config_extended/generator.py,162
  src/prefact/config_extended/models.py,84
  src/prefact/config_extended/utils.py,12
  src/prefact/config_extended/validation.py,71
  src/prefact/config_extended/validators.py,53
  src/prefact/defaults.py,22
  src/prefact/engine.py,171
  src/prefact/fixer.py,59
  src/prefact/git_hooks.py,384
  src/prefact/logging/__init__.py,14
  src/prefact/logging/exceptions.py,36
  src/prefact/logging/formatters.py,27
  src/prefact/logging/levels.py,14
  src/prefact/logging/logger.py,154
  src/prefact/models.py,91
  src/prefact/performance/__init__.py,42
  src/prefact/performance/cache/__init__.py,31
  src/prefact/performance/cache/base.py,103
  src/prefact/performance/cache/config.py,33
  src/prefact/performance/cache/globals.py,52
  src/prefact/performance/cache/hash.py,32
  src/prefact/performance/cache/rule.py,40
  src/prefact/performance/cache/scan.py,54
  src/prefact/performance/cache.py,441
  src/prefact/performance/cache_adapters.py,131
  src/prefact/performance/cache_state.py,73
  src/prefact/performance/parallel.py,358
  src/prefact/plugins/__init__.py,331
  src/prefact/plugins/builtin.py,14
  src/prefact/reporters/__init__.py,2
  src/prefact/reporters/console.py,71
  src/prefact/reporters/json_reporter.py,58
  src/prefact/rules/__init__.py,257
  src/prefact/rules/_ast_cache.py,50
  src/prefact/rules/ai_boilerplate.py,79
  src/prefact/rules/autoflake_based.py,298
  src/prefact/rules/benchmark.py,162
  src/prefact/rules/composite_factory.py,122
  src/prefact/rules/composite_rules.py,293
  src/prefact/rules/duplicate_imports.py,103
  src/prefact/rules/import_linter_based.py,481
  src/prefact/rules/importchecker_based.py,500
  src/prefact/rules/isort_based.py,520
  src/prefact/rules/llm_generated_code.py,197
  src/prefact/rules/llm_hallucinations.py,221
  src/prefact/rules/magic_numbers.py,139
  src/prefact/rules/migration.py,235
  src/prefact/rules/mypy_based.py,417
  src/prefact/rules/print_statements.py,63
  src/prefact/rules/pylint_based.py,425
  src/prefact/rules/registry.py,274
  src/prefact/rules/relative_imports.py,236
  src/prefact/rules/ruff_based.py,360
  src/prefact/rules/sorted_imports.py,72
  src/prefact/rules/strategies.py,159
  src/prefact/rules/string_concat.py,73
  src/prefact/rules/string_transformations.py,502
  src/prefact/rules/type_hints.py,51
  src/prefact/rules/unimport_based.py,460
  src/prefact/rules/unused_imports.py,278
  src/prefact/rules/wildcard_imports.py,50
  src/prefact/scanner.py,168
  src/prefact/validator.py,33
  test_large_files.py,50
  test_ram_implementation.py,54
  tests/test_autonomous_limits.py,350
  tests/test_config.py,96
  tests/test_dependency_checker.py,153
  tests/test_engine.py,102
  tests/test_integrations.py,550
  tests/test_refactoring.py,12
  tests/test_relative_imports.py,134
  tests/test_rules.py,162
  tests/test_testql_manager.py,243
  tests/test_unused_imports.py,66
  tree.sh,2
  vscode-extension/out/extension.js,355
  vscode-extension/src/extension.ts,438
  vscode-extension/test/prefact.test.js,6
D:
  benchmark_ram_optimization.py:
    e: create_test_files,benchmark_without_rampreload,benchmark_with_rampreload,run_benchmark,main
    create_test_files(base_dir;num_files;file_size_kb)
    benchmark_without_rampreload(config)
    benchmark_with_rampreload(config)
    run_benchmark(num_files;file_size_kb)
    main()
  examples/01-individual-rules/duplicate-imports/after.py:
    e: process_data
    process_data()
  examples/01-individual-rules/duplicate-imports/before.py:
    e: process_data
    process_data()
  examples/01-individual-rules/missing-return-type/after.py:
    e: add,get_user,Processor
    Processor: process(1)  # Processor class.
    add(a;b)
    get_user(user_id)
  examples/01-individual-rules/missing-return-type/before.py:
    e: add,get_user,Processor
    Processor: process(1)  # Processor class.
    add(a;b)
    get_user(user_id)
  examples/01-individual-rules/print-statements/after.py:
    e: process_data,calculate
    process_data(data)
    calculate(a;b)
  examples/01-individual-rules/print-statements/before.py:
    e: process_data,calculate
    process_data(data)
    calculate(a;b)
  examples/01-individual-rules/relative-imports/after.py:
    e: process_user,Processor
    Processor: __init__(0),process(0)  # Processor class with absolute imports.
    process_user(user_id)
  examples/01-individual-rules/relative-imports/before.py:
    e: process_user,Processor
    Processor: __init__(0),process(0)  # Processor class with relative imports.
    process_user(user_id)
  examples/01-individual-rules/sorted-imports/after.py:
    e: process
    process()
  examples/01-individual-rules/sorted-imports/before.py:
    e: process
    process()
  examples/01-individual-rules/string-concat/after.py:
    e: greet,format_data
    greet(name;age)
    format_data(data)
  examples/01-individual-rules/string-concat/before.py:
    e: greet,format_data
    greet(name;age)
    format_data(data)
  examples/01-individual-rules/unused-imports/after.py:
    e: process_data,format_timestamp,read_file,DataProcessor
    DataProcessor: __init__(0),add_data(2),get_data(1)  # A class with clean imports.
    process_data(data)
    format_timestamp(ts)
    read_file(filepath)
  examples/01-individual-rules/unused-imports/before.py:
    e: process_data,format_timestamp,read_file,DataProcessor
    DataProcessor: __init__(0),add_data(2),get_data(1)  # A class with unused imports.
    process_data(data)
    format_timestamp(ts)
    read_file(filepath)
  examples/01-individual-rules/wildcard-imports/after.py:
    e: process
    process()
  examples/01-individual-rules/wildcard-imports/before.py:
    e: process
    process()
  examples/02-multiple-rules/messy_module.py:
    e: process_users,generate_report,DataProcessor
    DataProcessor: __init__(0),process(1)  # A class with various issues.
    process_users(users)
    generate_report(data)
  examples/03-output-formats/sample_code.py:
    e: process_data,calculate_sum
    process_data(data)
    calculate_sum(numbers)
  examples/04-custom-rules/custom_rules/__init__.py:
  examples/04-custom-rules/custom_rules/no_todo_rule.py:
    e: NoTodoRule,NoPrintRule
    NoTodoRule: __init__(1),scan_file(2),fix(3),validate(3)  # Rule that detects TODO comments in code.
    NoPrintRule: scan_file(2),fix(3),validate(3)  # Custom rule that detects print statements (alternative to bu
  examples/06-api-usage/example.py:
    e: run_prefact_example,custom_rule_example,batch_processing_example,main
    run_prefact_example(project_path;config_file;dry_run)
    custom_rule_example()
    batch_processing_example()
    main()
  examples/generate_examples.py:
  examples/run_examples.py:
    e: run_example,find_examples,main
    run_example(example_dir)
    find_examples(examples_dir)
    main()
  examples/sample-project/cli.py:
    e: main,admin,users
    main(name;email)
    admin()
    users()
  examples/sample-project/core.py:
    e: process_data,calculate_sum,DataProcessor
    DataProcessor: __init__(0),add_item(1),get_summary(0)  # A class that processes data.
    process_data(data)
    calculate_sum(numbers)
  examples/sample-project/models.py:
    e: create_user,load_users_from_file,User,Post
    User: __post_init__(0)  # User model.
    Post: __post_init__(0),get_summary(0)  # Post model.
    create_user(name;email)
    load_users_from_file(filepath)
  examples/sample-project/utils.py:
    e: format_name,validate_email,helper_function,UtilClass
    UtilClass: __init__(0),get_cached(1)  # Utility class.
    format_name(first;last)
    validate_email(email)
    helper_function(data)
  examples/tests/test_examples.py:
    e: test_placeholder
    test_placeholder()
  src/prefact/__init__.py:
  src/prefact/_base.py:
  src/prefact/autonomous/__init__.py:
    e: AutonomousRefact
    AutonomousRefact: __init__(2),run_autonomous(1),create_refact_config(0),detect_project_info(0),run_examples(0),scan_project(0),group_issues(1),update_planfile(0),create_default_planfile(0),create_ticket_from_issue(1),ticket_exists(2),manage_documentation(0),update_todo_md(0),execute_todos(0),update_changelog_md(0),run_testql(1),run_testql_all(0),_print_autonomous_summary(0),run_tests(0)  # Autonomous prefact manager.
  src/prefact/autonomous/_base.py:
    e: BaseManager
    BaseManager: __init__(1),get_autonomous_limit(1),_load_autonomous_limits(0)  # Base class for autonomous managers.
  src/prefact/autonomous/dependency_checker.py:
    e: DependencyChecker
    DependencyChecker: __init__(1),check_dependencies(0),_collect_declared_deps(0),_parse_pyproject_toml(0),_parse_requirements_files(0),_query_pip_outdated(0),_build_issue_groups(0),_find_dep_source_file(0),_find_dep_line(2),_normalize(1),_parse_dep_string(1)  # Checks for outdated project dependencies.
  src/prefact/autonomous/docs_manager.py:
    e: DocsManager
    DocsManager: __init__(1),update_planfile(0),_count_existing_tickets(1),_should_remove_obsolete_ticket(2),_is_autonomous_ticket(1),create_default_planfile(0),create_ticket_from_issue(1),ticket_exists(2),update_changelog_md(0),_get_relative_file_path(1)  # Manages documentation files - planfile.yaml and CHANGELOG.md
  src/prefact/autonomous/project_scanner.py:
    e: ProjectScanner
    ProjectScanner: __init__(2),scan_project(0),_scan_files_with_progress(3),_scan_files_parallel(6),_scan_files_sequential(5),_scan_single_file(2),group_issues(1)  # Handles project scanning operations.
  src/prefact/autonomous/setup_manager.py:
    e: SetupManager
    SetupManager: create_refact_config(0),detect_project_info(0),run_examples(0)  # Handles project setup - configuration and examples.
  src/prefact/autonomous/testql_manager.py:
    e: TestQLManager
    TestQLManager: run(1),discover_scenarios(1),run_all(0)  # Run TestQL DSL validation and bridge results into planfile.
  src/prefact/autonomous/todo_manager.py:
    e: TodoManager
    TodoManager: __init__(1),update_todo_md(0),_parse_existing_todos(0),_generate_current_todos(1),_find_completed_tasks(2),_write_todo_md(4),_get_relative_file_path(1),execute_todos(0),_parse_todo_tasks(0),_get_refactoring_config(0),_limit_todo_execution_tasks(1),_execute_todo_tasks(1),_group_tasks_by_file(1),_process_file_tasks(4),_update_todo_with_execution_results(4)  # Manages TODO.md file operations.
  src/prefact/autonomous.py:
  src/prefact/benchmark.py:
    e: _make_inprocess_probe,build_prefact_suite,benchmark_library,main,ScanProbe
    ScanProbe: __init__(4),run(0)  # Prefact-specific: creates N temp Python files and measures s
    _make_inprocess_probe()
    build_prefact_suite()
    benchmark_library(module;cli_commands;test_path;threshold_import;threshold_cli;threshold_tests)
    main()
  src/prefact/cli.py:
    e: main,_common_options,_build_config,scan,fix,check,init,autonomous_cmd,testql_cmd,rules,_output
    main(ctx;autonomous;init_only;skip_tests;skip_examples;exclude;with_testql;testql_dir)
    _common_options(fn)
    _build_config(project_path;package_name;config_file;verbose;exclude)
    scan()
    fix(dry_run;no_backup)
    check(filepath)
    init(project_path)
    autonomous_cmd(project_path;init_only;skip_tests;skip_examples;exclude;with_testql;testql_dir)
    testql_cmd(scenario_path;project_path;url;dry_run;strategy_path;create_tickets;sync_targets;max_tickets;testql_bin;testql_repo_path)
    rules()
    _output(result;kwargs)
  src/prefact/config.py:
    e: RuleConfig,Config
    RuleConfig:  # Configuration for a single rule.
    Config: from_yaml(2),_parse_rules(2),_get_default_patterns(1),rule_enabled(1),is_rule_enabled(1),rule_options(1),get_rule_option(3),set_rule_option(3),detect_package_name(0),_detect_from_pyproject(0),_get_tomllib(0),_detect_from_src_layout(0),_detect_from_root_layout(0)  # Top-level configuration.
  src/prefact/config_extended/__init__.py:
  src/prefact/config_extended/config.py:
    e: ExtendedConfig
    ExtendedConfig: __init__(9),from_yaml(3),_parse_rules(1),_deep_merge(2),get_tool_config(1),get_performance_setting(2),get_plugin_config(1),to_dict(0)  # Extended configuration with additional features.
  src/prefact/config_extended/constants.py:
  src/prefact/config_extended/generator.py:
    e: ConfigGenerator
    ConfigGenerator: generate_extended_config(3),generate_composite_rule_config(4),save_config(2)  # Generate configuration files.
  src/prefact/config_extended/models.py:
    e: ExtendedConfig
    ExtendedConfig: __init__(9),from_yaml(3),to_dict(0)
  src/prefact/config_extended/utils.py:
    e: deep_merge
    deep_merge(base;override)
  src/prefact/config_extended/validation.py:
    e: ConfigValidator
    ConfigValidator: validate(1),_validate_ruff_config(1),_validate_mypy_config(1),_validate_isort_config(1),_validate_performance_config(1),_validate_rule_config(2)  # Validate configuration files.
  src/prefact/config_extended/validators.py:
    e: ConfigValidator
    ConfigValidator: validate(1),_validate_ruff_config(1),_validate_mypy_config(1),_validate_performance_config(1)
  src/prefact/defaults.py:
  src/prefact/engine.py:
    e: RefactoringEngine
    RefactoringEngine: __init__(1),run(0),scan_only(0),run_file(1),_preload_sources(1)  # Main entry point: scan the project, apply fixes, validate re
  src/prefact/fixer.py:
    e: Fixer
    Fixer: __init__(1),fix_file(2),fix_file_with_source(3)
  src/prefact/git_hooks.py:
    e: install_git_hooks,uninstall_git_hooks,list_git_hooks,main,GitHooks,PreCommitConfig
    GitHooks: __init__(2),_find_git_dir(0),install_hooks(1),_install_hook(2),_generate_hook_script(1),_pre_commit_hook(0),_pre_push_hook(0),_commit_msg_hook(0),uninstall_hooks(1),list_hooks(0),test_hook(1)  # Manages Git hooks for prefact.
    PreCommitConfig: generate_config(1),install(1)  # Generate pre-commit configuration for prefact.
    install_git_hooks(repo_root)
    uninstall_git_hooks(repo_root)
    list_git_hooks(repo_root)
    main()
  src/prefact/logging/__init__.py:
  src/prefact/logging/exceptions.py:
    e: PprefactException,ConfigurationError,RuleError,PluginError
    PprefactException: __init__(3)
    ConfigurationError:
    RuleError: __init__(3)
    PluginError: __init__(2)
  src/prefact/logging/formatters.py:
    e: JsonFormatter
    JsonFormatter: format(1)
  src/prefact/logging/levels.py:
    e: LogLevel
    LogLevel:  # Log levels for prefact.
  src/prefact/logging/logger.py:
    e: LogLevel,PprefactLogger
    LogLevel:
    PprefactLogger: __init__(5),_setup_handlers(0),debug(1),info(1),warning(1),error(2),critical(2),_log(2),_send_telemetry(1),add_telemetry_callback(1),log_scan_start(2),log_scan_complete(3),log_rule_execution(4),log_plugin_loaded(2),log_performance_metrics(1)
  src/prefact/models.py:
    e: Severity,Phase,Issue,Fix,ValidationResult,PipelineResult
    Severity:  # How critical an issue is.
    Phase:  # Pipeline phase.
    Issue: location(0)  # A single detected problem in the codebase.
    Fix:  # A concrete code change to apply.
    ValidationResult:  # Result of post-fix validation.
    PipelineResult: total_issues(0),total_fixed(0),total_failed(0),all_valid(0)  # Aggregate result of the full scan → fix → validate pipeline.
  src/prefact/performance/__init__.py:
  src/prefact/performance/cache/__init__.py:
  src/prefact/performance/cache/base.py:
    e: Cache
    Cache: __init__(2),get(2),set(3),delete(1),clear(0),get_stats(0),close(0)  # Wrapper for diskcache with additional functionality.
  src/prefact/performance/cache/config.py:
    e: ConfigCache
    ConfigCache: __init__(1),get_key(1),get(1),set(2)  # Cache for rule configurations.
  src/prefact/performance/cache/globals.py:
    e: initialize_cache,get_cache,get_scan_cache
    initialize_cache(config)
    get_cache()
    get_scan_cache()
  src/prefact/performance/cache/hash.py:
    e: FileHashCache
    FileHashCache: __init__(1),get_hash(1),set_hash(2)  # Cache for file hashes.
  src/prefact/performance/cache/rule.py:
    e: RuleResultCache
    RuleResultCache: __init__(1),get_key(4),get(4),set(6)  # Cache for individual rule results.
  src/prefact/performance/cache/scan.py:
    e: ScanResultCache
    ScanResultCache: __init__(1),get_key(4),get(4),set(6),invalidate_file(1)  # Specialized cache for scan results.
  src/prefact/performance/cache.py:
    e: initialize_cache,get_cache,get_scan_cache,get_config_cache,get_rule_cache,get_hash_cache,cleanup_cache,cached_result,cached_file_operation,clear_cache,get_cache_info,Cache,ScanResultCache,ConfigCache,RuleResultCache,FileHashCache,CacheContext
    Cache: __init__(2),get(2),set(3),delete(1),clear(0),get_stats(0),close(0)  # Wrapper for diskcache with additional functionality.
    ScanResultCache: __init__(1),get_key(4),get(4),set(6),invalidate_file(1)  # Specialized cache for scan results.
    ConfigCache: __init__(1),get_key(1),get(1),set(2)  # Cache for rule configurations.
    RuleResultCache: __init__(1),get_key(4),get(4),set(6)  # Cache for individual rule results.
    FileHashCache: __init__(1),get_hash(1),set_hash(2)  # Cache for file hashes.
    CacheContext: __init__(1),__enter__(0),__exit__(3)  # Context manager for cache operations.
    initialize_cache(config)
    get_cache()
    get_scan_cache()
    get_config_cache()
    get_rule_cache()
    get_hash_cache()
    cleanup_cache()
    cached_result(expire;key_func)
    cached_file_operation(expire)
    clear_cache(pattern)
    get_cache_info()
  src/prefact/performance/cache_adapters.py:
    e: ScanResultCache,ConfigCache,RuleResultCache,FileHashCache
    ScanResultCache: __init__(1),get_key(4),get(4),set(6),invalidate_file(1)  # Specialized cache for scan results.
    ConfigCache: __init__(1),get_key(1),get(1),set(2)  # Cache for rule configurations.
    RuleResultCache: __init__(1),get_key(4),get(4),set(6)  # Cache for individual rule results.
    FileHashCache: __init__(1),get_hash(1),set_hash(2)  # Cache for file hashes.
  src/prefact/performance/cache_state.py:
    e: initialize_cache,get_cache,get_scan_cache,get_config_cache,get_rule_cache,get_hash_cache,close_cache
    initialize_cache(config)
    get_cache()
    get_scan_cache()
    get_config_cache()
    get_rule_cache()
    get_hash_cache()
    close_cache()
  src/prefact/performance/parallel.py:
    e: init_worker,scan_file_worker,get_performance_monitor,ParallelScanTask,ParallelEngine,ParallelScanner,PerformanceMonitor
    ParallelScanTask: __init__(4),_calculate_file_hash(0),execute(0)  # A task for parallel scanning.
    ParallelEngine: __init__(1),scan_files(2),_scan_with_thread_pool(1),_scan_with_process_pool(1),_execute_task_wrapper(1),_get_enabled_rule_ids(0),fix_files(2)  # Parallel processing engine for prefact.
    ParallelScanner: __init__(1),scan_directory(4),scan_workspace(1),get_performance_stats(0)  # High-level interface for parallel scanning.
    PerformanceMonitor: __init__(0),start_timing(0),end_timing(1),record_cache_hit(0),record_cache_miss(0),get_stats(0)  # Monitor performance of parallel operations.
    init_worker()
    scan_file_worker(args)
    get_performance_monitor()
  src/prefact/plugins/__init__.py:
    e: get_plugin_manager,register_plugin_rule,PluginMetadata,PluginValidator,PluginManager
    PluginMetadata: __init__(6),_check_compatibility(0)  # Metadata for a loaded plugin.
    PluginValidator: validate_plugin_module(1),validate_plugin_path(1)  # Validates plugins before loading.
    PluginManager: __init__(1),discover_plugins(0),_discover_entry_point_plugins(0),_discover_local_plugins(1),load_plugin(1),load_all_plugins(0),get_rule(1),_load_plugin_for_rule(1),list_plugins(0),_is_rule_from_plugin(2),unload_plugin(1)  # Manages loading and registration of plugins.
    get_plugin_manager(config)
    register_plugin_rule(plugin_name;version)
  src/prefact/plugins/builtin.py:
  src/prefact/reporters/__init__.py:
  src/prefact/reporters/console.py:
    e: print_report
    print_report(result)
  src/prefact/reporters/json_reporter.py:
    e: to_dict,dump
    to_dict(result)
    dump(result)
  src/prefact/rules/__init__.py:
    e: register,get_all_rules,get_rule,BaseRule
    BaseRule: __init__(1),scan_file(2),fix(3),validate(3),_validate_by_rescan(5)  # Base class every prefactoring rule must implement.
    register(cls)
    get_all_rules()
    get_rule(rule_id)
  src/prefact/rules/_ast_cache.py:
    e: parse_cached,clear
    parse_cached(source)
    clear()
  src/prefact/rules/ai_boilerplate.py:
    e: AIBoilerplateRule
    AIBoilerplateRule: _get_boilerplate_patterns(0),_check_line(3),scan_file(2),fix(3),validate(3)  # Detect AI boilerplate and template code.
  src/prefact/rules/autoflake_based.py:
    e: build_autoflake_check_command,parse_autoflake_output,run_autoflake_command,create_temp_file_with_source,build_autoflake_fix_command,create_issues_from_results,extract_import_name,create_fixes_from_issues,validate_unused_imports,AutoflakeHelper,AutoflakeUnusedImports,AutoflakeUnusedVariables
    AutoflakeHelper: check_file(2),check_source(2),fix_file(2),fix_source(2)  # Helper class for Autoflake operations.
    AutoflakeUnusedImports: __init__(1),_load_autoflake_config(0),scan_file(2),fix(3),validate(3)  # Remove unused imports using Autoflake.
    AutoflakeUnusedVariables: __init__(1)  # Remove unused variables using Autoflake.
    build_autoflake_check_command(file_path;config)
    parse_autoflake_output(output_lines)
    run_autoflake_command(cmd)
    create_temp_file_with_source(source)
    build_autoflake_fix_command(file_path;config)
    create_issues_from_results(results;path;rule_id)
    extract_import_name(line)
    create_fixes_from_issues(issues;path)
    validate_unused_imports(fixed;autoflake_config;path)
  src/prefact/rules/benchmark.py:
    e: benchmark_file,benchmark_project,print_benchmark_results,main
    benchmark_file(file_path;config)
    benchmark_project(project_root;config)
    print_benchmark_results(results)
    main()
  src/prefact/rules/composite_factory.py:
    e: register_composite_rules,CompositeRuleFactory
    CompositeRuleFactory: create_composite_rule(5)  # Factory for creating composite rules dynamically.
    register_composite_rules(config)
  src/prefact/rules/composite_rules.py:
    e: CompositeUnusedImports,CompositeImportRules,CompositeTypeChecking
    CompositeUnusedImports: __init__(1),_create_strategy(0),_load_tools(0),scan_file(2),fix(3),validate(3)  # Composite rule for unused imports using multiple tools.
    CompositeImportRules: __init__(1),_load_tools(0),scan_file(2),fix(3),validate(3)  # Composite rule for all import-related checks.
    CompositeTypeChecking: __init__(1),_load_tools(0),scan_file(2),fix(3),validate(3)  # Composite rule for type checking using multiple tools.
  src/prefact/rules/duplicate_imports.py:
    e: DuplicateImports
    DuplicateImports: scan_file(2),fix(3),validate(3)
  src/prefact/rules/import_linter_based.py:
    e: generate_import_linter_config,ImportLinterHelper,ImportLinterLayers,ImportLinterNoRelative,ImportLinterIndependence,ImportLinterCustomArchitecture
    ImportLinterHelper: create_config(2),run_linter(1),check_file(2)  # Helper class for import-linter operations.
    ImportLinterLayers: __init__(1),_load_linter_config(0),scan_file(2),fix(3),validate(3)  # Enforce import layering rules using import-linter.
    ImportLinterNoRelative: __init__(1),_load_linter_config(0),scan_file(2),fix(3),validate(3)  # Block relative imports using import-linter.
    ImportLinterIndependence: __init__(1),_load_linter_config(0),scan_file(2),fix(3),validate(3)  # Ensure module independence using import-linter.
    ImportLinterCustomArchitecture: __init__(1),_load_custom_config(0),scan_file(2),fix(3),validate(3)  # Enforce custom architectural rules using import-linter.
    generate_import_linter_config(config;output_path)
  src/prefact/rules/importchecker_based.py:
    e: ImportCheckerHelper,ImportCheckerUnusedImports,ImportCheckerDuplicateImports,ImportDependencyAnalysis,ImportOptimizer
    ImportCheckerHelper: check_file(1),_get_module_name(1),check_source(2)  # Helper class for importchecker operations.
    ImportCheckerUnusedImports: __init__(1),_load_checker_config(0),scan_file(2),_find_import_lines(1),fix(3),validate(3)  # Detect unused imports using importchecker.
    ImportCheckerDuplicateImports: scan_file(2),fix(3),validate(3)  # Detect duplicate imports using importchecker.
    ImportDependencyAnalysis: __init__(1),_load_checker_config(0),scan_file(2),_extract_imports(1),_detect_circular_imports(2),fix(3),validate(3)  # Analyze import dependencies using importchecker.
    ImportOptimizer: scan_file(2),_extract_all_imports(1),_count_usage(2),fix(3),validate(3)  # Optimize imports based on importchecker analysis.
  src/prefact/rules/isort_based.py:
    e: ISortHelper,ISortedImports,ImportSectionSeparator,CustomImportOrganization
    ISortHelper: check_file(2),check_source(2),_find_import_blocks(1),_is_block_sorted(2),_needs_section_separators(2),fix_file(2),fix_source(2)  # Helper class for ISort operations.
    ISortedImports: __init__(1),_load_isort_config(0),scan_file(2),fix(3),validate(3)  # Sort imports using ISort.
    ImportSectionSeparator: __init__(1),scan_file(2),fix(3),validate(3)  # Ensure import sections are properly separated.
    CustomImportOrganization: __init__(1),_load_custom_rules(0),scan_file(2),_check_grouping(2),_check_alphabetical(2),fix(3),validate(3)  # Organize imports according to custom rules.
  src/prefact/rules/llm_generated_code.py:
    e: LLMGeneratedCodeRule
    LLMGeneratedCodeRule: __init__(1),_load_indicators(0),scan_file(2),_check_comment_ratio(2),_check_docstring_patterns(2),_has_llm_docstring_pattern(1),_map_severity(1),fix(3),validate(3)  # Detect code that appears to be LLM-generated.
  src/prefact/rules/llm_hallucinations.py:
    e: LLMHallucinationRule
    LLMHallucinationRule: __init__(1),_load_patterns(0),scan_file(2),_check_ast_patterns(2),_is_suspicious_function_name(1),_is_suspicious_import(1),_map_severity(1),fix(3),validate(3)  # Detect LLM hallucination patterns in code.
  src/prefact/rules/magic_numbers.py:
    e: MagicNumberRule
    MagicNumberRule: __init__(1),_load_allowed_numbers(0),scan_file(2),_extract_literal_issues(2),_extract_comparison_issues(2),_is_magic_number(1),fix(3),validate(3)  # Detect magic numbers in code.
  src/prefact/rules/migration.py:
    e: add_ruff_config_to_prefact_yaml,RuleMigrationManager,HybridScanner,PerformanceProfiler
    RuleMigrationManager: __init__(1),get_migrated_rule(1),should_use_ruff(1),create_hybrid_rule(1)  # Manages migration from AST-based rules to Ruff-based rules.
    HybridScanner: __init__(1),_load_rules(0),scan_file(2)  # Scanner that can use both AST and Ruff-based rules.
    PerformanceProfiler: profile_rule(3),compare_implementations(3)  # Compare performance between AST and Ruff implementations.
    add_ruff_config_to_prefact_yaml(config_path)
  src/prefact/rules/mypy_based.py:
    e: MyPyHelper,MyPyMissingReturnType,MyPyTypeChecking,ReturnTypeInferrer,ReturnTypeAdder,SmartReturnTypeRule
    MyPyHelper: check_file(2),check_source(2)  # Helper class for MyPy operations.
    MyPyMissingReturnType: __init__(1),_load_mypy_config(0),scan_file(2),_is_public_function(2),fix(3),validate(3)  # Detect missing return type annotations using MyPy.
    MyPyTypeChecking: __init__(1),_load_mypy_config(0),scan_file(2),fix(3),validate(3)  # General type checking using MyPy.
    ReturnTypeInferrer: infer_return_type(2),_analyze_return_types(1),_get_return_value_type(1),_unify_types(1)  # Infer return types for simple functions.
    ReturnTypeAdder: __init__(2),leave_FunctionDef(2)  # Transformer to add return type annotations to functions.
    SmartReturnTypeRule: scan_file(2),fix(3),validate(3)  # Smart return type detection with inference suggestions.
  src/prefact/rules/print_statements.py:
    e: PrintStatements
    PrintStatements: scan_file(2),fix(3),validate(3)
  src/prefact/rules/pylint_based.py:
    e: generate_pylint_rc,PylintHelper,PylintPrintStatements,PylintStringConcat,PprefactPylintPlugin,PylintComprehensive
    PylintHelper: check_file(2),check_source(2),fix_file(2)  # Helper class for Pylint operations.
    PylintPrintStatements: __init__(1),_load_pylint_config(0),scan_file(2),fix(3),validate(3)  # Detect print statements using Pylint.
    PylintStringConcat: __init__(1),_load_pylint_config(0),scan_file(2),fix(3),validate(3)  # Detect string concatenation using Pylint.
    PprefactPylintPlugin: register(1)  # Custom Pylint plugin for prefact-specific checks.
    PylintComprehensive: __init__(1),_load_pylint_config(0),scan_file(2),_map_pylint_to_prefact(1),_map_pylint_severity(1),fix(3),validate(3)  # Comprehensive analysis using Pylint with custom rules.
    generate_pylint_rc(config;output_path)
  src/prefact/rules/registry.py:
    e: get_lazy_registry,get_all_rules,get_rule,register,_initialize_built_in_rules,LazyRuleRegistry
    LazyRuleRegistry: __init__(0),get_rule(1),_load_module(1),_find_rule_class(2),get_all_rules(0),list_available_rules(0),register_rule(2),register_rule_module(2)  # Registry that lazily loads rule classes.
    get_lazy_registry()
    get_all_rules()
    get_rule(rule_id)
    register(rule_class)
    _initialize_built_in_rules()
  src/prefact/rules/relative_imports.py:
    e: _module_to_str,_str_to_module,_RelativeImportFixer,RelativeToAbsoluteImports
    _RelativeImportFixer: __init__(3),leave_ImportFrom(2),_resolve(2)  # Transform relative imports to absolute using the resolved pa
    RelativeToAbsoluteImports: __init__(1),scan_file(2),fix(3),validate(3)
    _module_to_str(node)
    _str_to_module(dotted)
  src/prefact/rules/ruff_based.py:
    e: RuffHelper,RuffWildcardImports,RuffPrintStatements,RuffUnusedImports,RuffSortedImports,RuffDuplicateImports
    RuffHelper: check_file(2),fix_file(2),fix_source(2)  # Helper class for Ruff operations.
    RuffWildcardImports: scan_file(2),fix(3),validate(3)  # Wildcard imports detection using Ruff.
    RuffPrintStatements: scan_file(2),_should_ignore_file(1),fix(3),validate(3)  # Print statements detection using Ruff.
    RuffUnusedImports: scan_file(2),fix(3),validate(3)  # Unused imports detection and removal using Ruff.
    RuffSortedImports: scan_file(2),fix(3),validate(3)  # Import sorting using Ruff.
    RuffDuplicateImports: scan_file(2),fix(3),validate(3)  # Duplicate imports detection using Ruff.
  src/prefact/rules/sorted_imports.py:
    e: _sort_key,SortedImports
    SortedImports: scan_file(2),fix(3),validate(3)
    _sort_key(node)
  src/prefact/rules/strategies.py:
    e: ToolStrategy,ParallelScanStrategy,SequentialScanStrategy,PriorityBasedStrategy
    ToolStrategy: scan(3),fix(4)  # Abstract base class for tool orchestration strategies.
    ParallelScanStrategy: __init__(1),scan(3),fix(4)  # Run all tools in parallel and merge results.
    SequentialScanStrategy: scan(3),fix(4)  # Run tools sequentially, passing results between them.
    PriorityBasedStrategy: __init__(1),scan(3),fix(4)  # Use tool priority to resolve conflicts.
  src/prefact/rules/string_concat.py:
    e: _is_str_concat,_flatten_add,StringConcatToFstring
    StringConcatToFstring: scan_file(2),fix(3),validate(3)
    _is_str_concat(node)
    _flatten_add(node)
  src/prefact/rules/string_transformations.py:
    e: StringConcatTransformer,StringConcatToFString,FlyntHelper,FlyntStringFormatting,ContextAwareStringTransformer,ContextAwareStringConcat
    StringConcatTransformer: __init__(0),_get_line_number(1),leave_BinaryOperation(2),_collect_string_parts(1),_eval_string(1),_should_transform(1),_create_fstring(1)  # Transform string concatenations to f-strings.
    StringConcatToFString: scan_file(2),_is_string_concat(1),fix(3),validate(3)  # Convert string concatenations to f-strings.
    FlyntHelper: fix_source(1)  # Helper for using flynt library for string formatting.
    FlyntStringFormatting: scan_file(2),fix(3),validate(3)  # Use flynt library for string formatting optimizations.
    ContextAwareStringTransformer: __init__(1),visit_FunctionDef(1),leave_FunctionDef(1),visit_ClassDef(1),leave_ClassDef(1),leave_BinaryOperation(2),_should_skip_context(1),_is_in_logging_statement(1)  # Transform string concatenations with context awareness.
    ContextAwareStringConcat: __init__(1),scan_file(2),fix(3),validate(3)  # Context-aware string concatenation to f-string conversion.
  src/prefact/rules/type_hints.py:
    e: MissingReturnType
    MissingReturnType: scan_file(2),fix(3),validate(3)
  src/prefact/rules/unimport_based.py:
    e: UnimportHelper,UnimportUnusedImports,UnimportDuplicateImports,UnimportStarImports,UnimportAll
    UnimportHelper: check_file(2),check_source(2),_extract_import_name(1),fix_file(2),fix_source(2)  # Helper class for unimport operations.
    UnimportUnusedImports: __init__(1),_load_unimport_config(0),scan_file(2),fix(3),validate(3)  # Remove unused imports using unimport.
    UnimportDuplicateImports: __init__(1),scan_file(2),fix(3),validate(3)  # Remove duplicate imports using unimport.
    UnimportStarImports: __init__(1),scan_file(2),fix(3),validate(3)  # Handle star imports using unimport.
    UnimportAll: __init__(1),scan_file(2),fix(3),validate(3)  # Apply all unimport fixes.
  src/prefact/rules/unused_imports.py:
    e: _collect_imported_names,_collect_used_names,_collect_all_exports,UnusedImports
    UnusedImports: scan_file(2),validate(3),fix(3),remove_lines(2),process_import_from(7),process_import(7),_remove_unused_from_line(2),_remove_unused_from_import_line(2)
    _collect_imported_names(tree)
    _collect_used_names(tree)
    _collect_all_exports(tree)
  src/prefact/rules/wildcard_imports.py:
    e: WildcardImports
    WildcardImports: scan_file(2),fix(3),validate(3)
  src/prefact/scanner.py:
    e: _load_gitignore,_match_gitignore_pattern,Scanner
    Scanner: __init__(1),collect_files(0),scan(1),scan_sources(1),_excluded(1)  # Discovers Python files and runs all enabled rules against th
    _load_gitignore(root)
    _match_gitignore_pattern(path;pattern)
  src/prefact/validator.py:
    e: Validator
    Validator: __init__(1),validate_file(4)
  test_large_files.py:
    e: test_large_file_handling
    test_large_file_handling()
  test_ram_implementation.py:
  tests/test_autonomous_limits.py:
    e: _write_prefact_config,_issue_group,test_config_generator_includes_autonomous_limits,test_config_validator_rejects_invalid_autonomous_limits,test_project_scanner_respects_configured_example_limit,test_project_scanner_caps_files_to_scan,test_project_scanner_caps_issues_per_file,test_autonomous_refact_caps_grouped_issues_before_distribution,test_autonomous_refact_stops_before_docs_when_time_limit_exceeded,test_autonomous_refact_prints_final_summary,test_docs_manager_respects_total_ticket_limit,test_docs_manager_reports_skipped_ticket_count,test_todo_manager_reports_skipped_todo_counts,test_todo_manager_limits_output_and_normalizes_existing_paths,test_todo_manager_execute_todos_respects_execution_limit
    _write_prefact_config(project_root;performance)
    _issue_group(file_path;rule_id;example_count)
    test_config_generator_includes_autonomous_limits(tmp_path)
    test_config_validator_rejects_invalid_autonomous_limits(tmp_path)
    test_project_scanner_respects_configured_example_limit(tmp_path)
    test_project_scanner_caps_files_to_scan(tmp_path)
    test_project_scanner_caps_issues_per_file(tmp_path)
    test_autonomous_refact_caps_grouped_issues_before_distribution(tmp_path)
    test_autonomous_refact_stops_before_docs_when_time_limit_exceeded(tmp_path)
    test_autonomous_refact_prints_final_summary(tmp_path;capsys)
    test_docs_manager_respects_total_ticket_limit(tmp_path)
    test_docs_manager_reports_skipped_ticket_count(tmp_path;capsys)
    test_todo_manager_reports_skipped_todo_counts(tmp_path;capsys)
    test_todo_manager_limits_output_and_normalizes_existing_paths(tmp_path)
    test_todo_manager_execute_todos_respects_execution_limit(tmp_path)
  tests/test_config.py:
    e: project_with_pyproject,TestConfig
    TestConfig: test_detect_from_pyproject(1),test_detect_from_src_layout(1),test_detect_top_level_package(1),test_from_yaml(1),test_rule_defaults(0),test_config_uses_defaults_include(0),test_config_uses_defaults_exclude(0),test_venv_variants_in_defaults(0),test_scanner_excludes_venv_test(1),test_config_extended_constants_reexport(0)
    project_with_pyproject(tmp_path)
  tests/test_dependency_checker.py:
    e: project_with_pyproject,project_with_requirements,pip_outdated_json,TestDependencyChecker
    TestDependencyChecker: test_parse_pyproject_toml(1),test_parse_requirements_txt(1),test_no_dep_files(1),test_outdated_filtering(3),test_all_up_to_date(2),test_issue_group_shape(3),test_line_number_detection(3),test_normalize(0),test_pip_failure_graceful(2)
    project_with_pyproject(tmp_path)
    project_with_requirements(tmp_path)
    pip_outdated_json()
  tests/test_engine.py:
    e: project,TestEngine
    TestEngine: test_scan_only(1),test_full_pipeline_dry_run(1),test_full_pipeline_apply(1),test_run_single_file(1),test_backup_created(1),test_clean_project_no_issues(1)
    project(tmp_path)
  tests/test_integrations.py:
    e: test_ruff_integration,test_mypy_integration,test_isort_integration,test_autoflake_integration,test_string_transformations,test_full_pipeline,test_performance_comparison,run_integration_tests,IntegrationTestCase,IntegrationTestSuite
    IntegrationTestCase: __init__(3),run(1)  # Base class for integration test cases.
    IntegrationTestSuite: __init__(0),_create_test_cases(0),run_all_tests(1),_compare_results(2),_issues_match(2)  # Comprehensive test suite for all integrations.
    test_ruff_integration()
    test_mypy_integration()
    test_isort_integration()
    test_autoflake_integration()
    test_string_transformations()
    test_full_pipeline()
    test_performance_comparison()
    run_integration_tests()
  tests/test_refactoring.py:
    e: test_placeholder,test_import
    test_placeholder()
    test_import()
  tests/test_relative_imports.py:
    e: config,TestScan,TestFix,TestValidate
    TestScan: test_detects_relative_imports(1),test_ignores_absolute_imports(1),test_handles_syntax_error_gracefully(1)
    TestFix: test_converts_single_dot_import(1),test_converts_deep_relative_import(1),test_preserves_absolute_imports(1),test_no_fix_without_package_name(1)
    TestValidate: test_valid_after_fix(1),test_invalid_if_relative_remains(1)
    config(tmp_path)
  tests/test_rules.py:
    e: config,TestDuplicateImports,TestWildcardImports,TestStringConcat,TestPrintStatements,TestMissingReturnType,TestSortedImports
    TestDuplicateImports: test_detects_duplicate(1),test_no_duplicates(1),test_fix_removes_duplicate_line(1)
    TestWildcardImports: test_detects_wildcard(1),test_no_autofix(1)
    TestStringConcat: test_detects_concat(1),test_ignores_pure_string_concat(1),test_ignores_numeric_add(1)
    TestPrintStatements: test_detects_print(1),test_no_print_no_issue(1)
    TestMissingReturnType: test_detects_missing(1),test_has_return_type(1),test_skips_private(1)
    TestSortedImports: test_detects_unsorted(1),test_sorted_ok(1)
    config(tmp_path)
  tests/test_testql_manager.py:
    e: planfile_stub,test_run_testql_creates_and_syncs_tickets,test_run_testql_respects_no_create_tickets,test_discover_scenarios_returns_sorted_glob,test_run_testql_all_skips_when_no_scenarios,test_run_testql_all_aggregates_results,_stub_pipeline_steps,test_run_autonomous_with_testql_invokes_run_all,test_run_autonomous_default_skips_testql
    planfile_stub(monkeypatch)
    test_run_testql_creates_and_syncs_tickets(tmp_path;planfile_stub)
    test_run_testql_respects_no_create_tickets(tmp_path;planfile_stub)
    test_discover_scenarios_returns_sorted_glob(tmp_path)
    test_run_testql_all_skips_when_no_scenarios(tmp_path;planfile_stub)
    test_run_testql_all_aggregates_results(tmp_path;planfile_stub)
    _stub_pipeline_steps(auto;monkeypatch)
    test_run_autonomous_with_testql_invokes_run_all(tmp_path;monkeypatch)
    test_run_autonomous_default_skips_testql(tmp_path;monkeypatch)
  tests/test_unused_imports.py:
    e: config,TestScanUnused,TestFixUnused
    TestScanUnused: test_detects_unused(1),test_used_import_not_flagged(1),test_respects_all_exports(1),test_skips_underscore_imports(1),test_attribute_access_counts_as_used(1)
    TestFixUnused: test_removes_unused_line(1)
    config(tmp_path)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('prefact', '0.0.0', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.css', 74, 'css').
project_file('app.doql.less', 424, 'less').
project_file('benchmark_ram_optimization.py', 236, 'python').
project_file('examples/01-individual-rules/duplicate-imports/after.py', 9, 'python').
project_file('examples/01-individual-rules/duplicate-imports/before.py', 9, 'python').
project_file('examples/01-individual-rules/missing-return-type/after.py', 20, 'python').
project_file('examples/01-individual-rules/missing-return-type/before.py', 20, 'python').
project_file('examples/01-individual-rules/print-statements/after.py', 16, 'python').
project_file('examples/01-individual-rules/print-statements/before.py', 16, 'python').
project_file('examples/01-individual-rules/relative-imports/after.py', 27, 'python').
project_file('examples/01-individual-rules/relative-imports/before.py', 27, 'python').
project_file('examples/01-individual-rules/sorted-imports/after.py', 7, 'python').
project_file('examples/01-individual-rules/sorted-imports/before.py', 7, 'python').
project_file('examples/01-individual-rules/string-concat/after.py', 14, 'python').
project_file('examples/01-individual-rules/string-concat/before.py', 14, 'python').
project_file('examples/01-individual-rules/unused-imports/after.py', 42, 'python').
project_file('examples/01-individual-rules/unused-imports/before.py', 42, 'python').
project_file('examples/01-individual-rules/wildcard-imports/after.py', 14, 'python').
project_file('examples/01-individual-rules/wildcard-imports/before.py', 14, 'python').
project_file('examples/02-multiple-rules/messy_module.py', 55, 'python').
project_file('examples/03-output-formats/sample_code.py', 18, 'python').
project_file('examples/04-custom-rules/custom_rules/__init__.py', 7, 'python').
project_file('examples/04-custom-rules/custom_rules/no_todo_rule.py', 113, 'python').
project_file('examples/06-api-usage/example.py', 199, 'python').
project_file('examples/generate_examples.py', 233, 'python').
project_file('examples/run_all.sh', 144, 'shell').
project_file('examples/run_examples.py', 138, 'python').
project_file('examples/sample-project/cli.py', 63, 'python').
project_file('examples/sample-project/core.py', 37, 'python').
project_file('examples/sample-project/models.py', 60, 'python').
project_file('examples/sample-project/utils.py', 41, 'python').
project_file('examples/tests/test_examples.py', 7, 'python').
project_file('project.sh', 47, 'shell').
project_file('src/prefact/__init__.py', 4, 'python').
project_file('src/prefact/_base.py', 7, 'python').
project_file('src/prefact/autonomous/__init__.py', 313, 'python').
project_file('src/prefact/autonomous/_base.py', 74, 'python').
project_file('src/prefact/autonomous/dependency_checker.py', 238, 'python').
project_file('src/prefact/autonomous/docs_manager.py', 286, 'python').
project_file('src/prefact/autonomous/project_scanner.py', 297, 'python').
project_file('src/prefact/autonomous/setup_manager.py', 143, 'python').
project_file('src/prefact/autonomous/testql_manager.py', 219, 'python').
project_file('src/prefact/autonomous/todo_manager.py', 431, 'python').
project_file('src/prefact/autonomous.py', 18, 'python').
project_file('src/prefact/benchmark.py', 312, 'python').
project_file('src/prefact/cli.py', 425, 'python').
project_file('src/prefact/config.py', 178, 'python').
project_file('src/prefact/config_extended/__init__.py', 13, 'python').
project_file('src/prefact/config_extended/config.py', 143, 'python').
project_file('src/prefact/config_extended/constants.py', 16, 'python').
project_file('src/prefact/config_extended/generator.py', 162, 'python').
project_file('src/prefact/config_extended/models.py', 84, 'python').
project_file('src/prefact/config_extended/utils.py', 12, 'python').
project_file('src/prefact/config_extended/validation.py', 71, 'python').
project_file('src/prefact/config_extended/validators.py', 53, 'python').
project_file('src/prefact/defaults.py', 22, 'python').
project_file('src/prefact/engine.py', 171, 'python').
project_file('src/prefact/fixer.py', 59, 'python').
project_file('src/prefact/git_hooks.py', 384, 'python').
project_file('src/prefact/logging/__init__.py', 14, 'python').
project_file('src/prefact/logging/exceptions.py', 36, 'python').
project_file('src/prefact/logging/formatters.py', 27, 'python').
project_file('src/prefact/logging/levels.py', 14, 'python').
project_file('src/prefact/logging/logger.py', 154, 'python').
project_file('src/prefact/models.py', 91, 'python').
project_file('src/prefact/performance/__init__.py', 42, 'python').
project_file('src/prefact/performance/cache/__init__.py', 31, 'python').
project_file('src/prefact/performance/cache/base.py', 103, 'python').
project_file('src/prefact/performance/cache/config.py', 33, 'python').
project_file('src/prefact/performance/cache/globals.py', 52, 'python').
project_file('src/prefact/performance/cache/hash.py', 32, 'python').
project_file('src/prefact/performance/cache/rule.py', 40, 'python').
project_file('src/prefact/performance/cache/scan.py', 54, 'python').
project_file('src/prefact/performance/cache.py', 441, 'python').
project_file('src/prefact/performance/cache_adapters.py', 131, 'python').
project_file('src/prefact/performance/cache_state.py', 73, 'python').
project_file('src/prefact/performance/parallel.py', 358, 'python').
project_file('src/prefact/plugins/__init__.py', 331, 'python').
project_file('src/prefact/plugins/builtin.py', 14, 'python').
project_file('src/prefact/reporters/__init__.py', 2, 'python').
project_file('src/prefact/reporters/console.py', 71, 'python').
project_file('src/prefact/reporters/json_reporter.py', 58, 'python').
project_file('src/prefact/rules/__init__.py', 257, 'python').
project_file('src/prefact/rules/_ast_cache.py', 50, 'python').
project_file('src/prefact/rules/ai_boilerplate.py', 79, 'python').
project_file('src/prefact/rules/autoflake_based.py', 298, 'python').
project_file('src/prefact/rules/benchmark.py', 162, 'python').
project_file('src/prefact/rules/composite_factory.py', 122, 'python').
project_file('src/prefact/rules/composite_rules.py', 293, 'python').
project_file('src/prefact/rules/duplicate_imports.py', 103, 'python').
project_file('src/prefact/rules/import_linter_based.py', 481, 'python').
project_file('src/prefact/rules/importchecker_based.py', 500, 'python').
project_file('src/prefact/rules/isort_based.py', 520, 'python').
project_file('src/prefact/rules/llm_generated_code.py', 197, 'python').
project_file('src/prefact/rules/llm_hallucinations.py', 221, 'python').
project_file('src/prefact/rules/magic_numbers.py', 139, 'python').
project_file('src/prefact/rules/migration.py', 235, 'python').
project_file('src/prefact/rules/mypy_based.py', 417, 'python').
project_file('src/prefact/rules/print_statements.py', 63, 'python').
project_file('src/prefact/rules/pylint_based.py', 425, 'python').
project_file('src/prefact/rules/registry.py', 274, 'python').
project_file('src/prefact/rules/relative_imports.py', 236, 'python').
project_file('src/prefact/rules/ruff_based.py', 360, 'python').
project_file('src/prefact/rules/sorted_imports.py', 72, 'python').
project_file('src/prefact/rules/strategies.py', 159, 'python').
project_file('src/prefact/rules/string_concat.py', 73, 'python').
project_file('src/prefact/rules/string_transformations.py', 502, 'python').
project_file('src/prefact/rules/type_hints.py', 51, 'python').
project_file('src/prefact/rules/unimport_based.py', 460, 'python').
project_file('src/prefact/rules/unused_imports.py', 278, 'python').
project_file('src/prefact/rules/wildcard_imports.py', 50, 'python').
project_file('src/prefact/scanner.py', 168, 'python').
project_file('src/prefact/validator.py', 33, 'python').
project_file('test_large_files.py', 50, 'python').
project_file('test_ram_implementation.py', 54, 'python').
project_file('tests/test_autonomous_limits.py', 350, 'python').
project_file('tests/test_config.py', 96, 'python').
project_file('tests/test_dependency_checker.py', 153, 'python').
project_file('tests/test_engine.py', 102, 'python').
project_file('tests/test_integrations.py', 550, 'python').
project_file('tests/test_refactoring.py', 12, 'python').
project_file('tests/test_relative_imports.py', 134, 'python').
project_file('tests/test_rules.py', 162, 'python').
project_file('tests/test_testql_manager.py', 243, 'python').
project_file('tests/test_unused_imports.py', 66, 'python').
project_file('tree.sh', 2, 'shell').
project_file('vscode-extension/out/extension.js', 355, 'javascript').
project_file('vscode-extension/src/extension.ts', 438, 'typescript').
project_file('vscode-extension/test/prefact.test.js', 6, 'javascript').

% ── Python Functions ─────────────────────────────────────
python_function('benchmark_ram_optimization.py', 'create_test_files', 3, 3, 5).
python_function('benchmark_ram_optimization.py', 'benchmark_without_rampreload', 1, 1, 12).
python_function('benchmark_ram_optimization.py', 'benchmark_with_rampreload', 1, 1, 3).
python_function('benchmark_ram_optimization.py', 'run_benchmark', 2, 1, 7).
python_function('benchmark_ram_optimization.py', 'main', 0, 7, 6).
python_function('examples/01-individual-rules/duplicate-imports/after.py', 'process_data', 0, 1, 1).
python_function('examples/01-individual-rules/duplicate-imports/before.py', 'process_data', 0, 1, 1).
python_function('examples/01-individual-rules/missing-return-type/after.py', 'add', 2, 1, 0).
python_function('examples/01-individual-rules/missing-return-type/after.py', 'get_user', 1, 1, 0).
python_function('examples/01-individual-rules/missing-return-type/before.py', 'add', 2, 1, 0).
python_function('examples/01-individual-rules/missing-return-type/before.py', 'get_user', 1, 1, 0).
python_function('examples/01-individual-rules/print-statements/after.py', 'process_data', 1, 1, 1).
python_function('examples/01-individual-rules/print-statements/after.py', 'calculate', 2, 1, 1).
python_function('examples/01-individual-rules/print-statements/before.py', 'process_data', 1, 1, 1).
python_function('examples/01-individual-rules/print-statements/before.py', 'calculate', 2, 1, 1).
python_function('examples/01-individual-rules/relative-imports/after.py', 'process_user', 1, 1, 2).
python_function('examples/01-individual-rules/relative-imports/before.py', 'process_user', 1, 1, 2).
python_function('examples/01-individual-rules/sorted-imports/after.py', 'process', 0, 1, 0).
python_function('examples/01-individual-rules/sorted-imports/before.py', 'process', 0, 1, 0).
python_function('examples/01-individual-rules/string-concat/after.py', 'greet', 2, 1, 0).
python_function('examples/01-individual-rules/string-concat/after.py', 'format_data', 1, 1, 0).
python_function('examples/01-individual-rules/string-concat/before.py', 'greet', 2, 1, 1).
python_function('examples/01-individual-rules/string-concat/before.py', 'format_data', 1, 1, 1).
python_function('examples/01-individual-rules/unused-imports/after.py', 'process_data', 1, 2, 2).
python_function('examples/01-individual-rules/unused-imports/after.py', 'format_timestamp', 1, 1, 1).
python_function('examples/01-individual-rules/unused-imports/after.py', 'read_file', 1, 1, 2).
python_function('examples/01-individual-rules/unused-imports/before.py', 'process_data', 1, 2, 2).
python_function('examples/01-individual-rules/unused-imports/before.py', 'format_timestamp', 1, 1, 1).
python_function('examples/01-individual-rules/unused-imports/before.py', 'read_file', 1, 1, 2).
python_function('examples/01-individual-rules/wildcard-imports/after.py', 'process', 0, 1, 1).
python_function('examples/01-individual-rules/wildcard-imports/before.py', 'process', 0, 1, 1).
python_function('examples/02-multiple-rules/messy_module.py', 'process_users', 1, 2, 2).
python_function('examples/02-multiple-rules/messy_module.py', 'generate_report', 1, 1, 4).
python_function('examples/03-output-formats/sample_code.py', 'process_data', 1, 1, 2).
python_function('examples/03-output-formats/sample_code.py', 'calculate_sum', 1, 2, 2).
python_function('examples/06-api-usage/example.py', 'run_prefact_example', 3, 11, 9).
python_function('examples/06-api-usage/example.py', 'custom_rule_example', 0, 4, 10).
python_function('examples/06-api-usage/example.py', 'batch_processing_example', 0, 6, 9).
python_function('examples/06-api-usage/example.py', 'main', 0, 4, 7).
python_function('examples/run_examples.py', 'run_example', 1, 6, 3).
python_function('examples/run_examples.py', 'find_examples', 1, 4, 5).
python_function('examples/run_examples.py', 'main', 0, 8, 13).
python_function('examples/sample-project/cli.py', 'main', 2, 2, 12).
python_function('examples/sample-project/cli.py', 'admin', 0, 1, 2).
python_function('examples/sample-project/cli.py', 'users', 0, 2, 4).
python_function('examples/sample-project/core.py', 'process_data', 1, 1, 2).
python_function('examples/sample-project/core.py', 'calculate_sum', 1, 2, 2).
python_function('examples/sample-project/models.py', 'create_user', 2, 1, 2).
python_function('examples/sample-project/models.py', 'load_users_from_file', 1, 2, 4).
python_function('examples/sample-project/utils.py', 'format_name', 2, 1, 1).
python_function('examples/sample-project/utils.py', 'validate_email', 1, 2, 2).
python_function('examples/sample-project/utils.py', 'helper_function', 1, 1, 1).
python_function('examples/tests/test_examples.py', 'test_placeholder', 0, 2, 0).
python_function('src/prefact/benchmark.py', '_make_inprocess_probe', 0, 1, 10).
python_function('src/prefact/benchmark.py', 'build_prefact_suite', 0, 3, 10).
python_function('src/prefact/benchmark.py', 'benchmark_library', 6, 5, 6).
python_function('src/prefact/benchmark.py', 'main', 0, 7, 9).
python_function('src/prefact/cli.py', 'main', 8, 6, 6).
python_function('src/prefact/cli.py', '_common_options', 1, 1, 2).
python_function('src/prefact/cli.py', '_build_config', 5, 7, 6).
python_function('src/prefact/cli.py', 'scan', 0, 1, 5).
python_function('src/prefact/cli.py', 'fix', 2, 2, 7).
python_function('src/prefact/cli.py', 'check', 1, 1, 7).
python_function('src/prefact/cli.py', 'init', 1, 4, 9).
python_function('src/prefact/cli.py', 'autonomous_cmd', 7, 5, 11).
python_function('src/prefact/cli.py', 'testql_cmd', 10, 2, 8).
python_function('src/prefact/cli.py', 'rules', 0, 3, 9).
python_function('src/prefact/cli.py', '_output', 2, 4, 5).
python_function('src/prefact/config_extended/utils.py', 'deep_merge', 2, 5, 4).
python_function('src/prefact/git_hooks.py', 'install_git_hooks', 1, 4, 6).
python_function('src/prefact/git_hooks.py', 'uninstall_git_hooks', 1, 2, 4).
python_function('src/prefact/git_hooks.py', 'list_git_hooks', 1, 4, 5).
python_function('src/prefact/git_hooks.py', 'main', 0, 8, 10).
python_function('src/prefact/performance/cache/globals.py', 'initialize_cache', 1, 2, 6).
python_function('src/prefact/performance/cache/globals.py', 'get_cache', 0, 2, 1).
python_function('src/prefact/performance/cache/globals.py', 'get_scan_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'initialize_cache', 1, 2, 6).
python_function('src/prefact/performance/cache.py', 'get_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'get_scan_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'get_config_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'get_rule_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'get_hash_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'cleanup_cache', 0, 2, 1).
python_function('src/prefact/performance/cache.py', 'cached_result', 2, 1, 9).
python_function('src/prefact/performance/cache.py', 'cached_file_operation', 1, 1, 13).
python_function('src/prefact/performance/cache.py', 'clear_cache', 1, 5, 5).
python_function('src/prefact/performance/cache.py', 'get_cache_info', 0, 4, 7).
python_function('src/prefact/performance/cache_state.py', 'initialize_cache', 1, 2, 6).
python_function('src/prefact/performance/cache_state.py', 'get_cache', 0, 2, 1).
python_function('src/prefact/performance/cache_state.py', 'get_scan_cache', 0, 2, 1).
python_function('src/prefact/performance/cache_state.py', 'get_config_cache', 0, 2, 1).
python_function('src/prefact/performance/cache_state.py', 'get_rule_cache', 0, 2, 1).
python_function('src/prefact/performance/cache_state.py', 'get_hash_cache', 0, 2, 1).
python_function('src/prefact/performance/cache_state.py', 'close_cache', 0, 2, 1).
python_function('src/prefact/performance/parallel.py', 'init_worker', 0, 1, 0).
python_function('src/prefact/performance/parallel.py', 'scan_file_worker', 1, 1, 3).
python_function('src/prefact/performance/parallel.py', 'get_performance_monitor', 0, 2, 1).
python_function('src/prefact/plugins/__init__.py', 'get_plugin_manager', 1, 3, 3).
python_function('src/prefact/plugins/__init__.py', 'register_plugin_rule', 2, 1, 0).
python_function('src/prefact/reporters/console.py', 'print_report', 1, 14, 8).
python_function('src/prefact/reporters/json_reporter.py', 'to_dict', 1, 4, 1).
python_function('src/prefact/reporters/json_reporter.py', 'dump', 1, 2, 3).
python_function('src/prefact/rules/__init__.py', 'register', 1, 1, 1).
python_function('src/prefact/rules/__init__.py', 'get_all_rules', 0, 1, 1).
python_function('src/prefact/rules/__init__.py', 'get_rule', 1, 1, 1).
python_function('src/prefact/rules/_ast_cache.py', 'parse_cached', 1, 4, 5).
python_function('src/prefact/rules/_ast_cache.py', 'clear', 0, 1, 1).
python_function('src/prefact/rules/autoflake_based.py', 'build_autoflake_check_command', 2, 3, 3).
python_function('src/prefact/rules/autoflake_based.py', 'parse_autoflake_output', 1, 7, 2).
python_function('src/prefact/rules/autoflake_based.py', 'run_autoflake_command', 1, 1, 1).
python_function('src/prefact/rules/autoflake_based.py', 'create_temp_file_with_source', 1, 1, 3).
python_function('src/prefact/rules/autoflake_based.py', 'build_autoflake_fix_command', 2, 5, 3).
python_function('src/prefact/rules/autoflake_based.py', 'create_issues_from_results', 3, 3, 3).
python_function('src/prefact/rules/autoflake_based.py', 'extract_import_name', 1, 6, 3).
python_function('src/prefact/rules/autoflake_based.py', 'create_fixes_from_issues', 2, 2, 2).
python_function('src/prefact/rules/autoflake_based.py', 'validate_unused_imports', 3, 5, 3).
python_function('src/prefact/rules/benchmark.py', 'benchmark_file', 2, 6, 12).
python_function('src/prefact/rules/benchmark.py', 'benchmark_project', 2, 7, 7).
python_function('src/prefact/rules/benchmark.py', 'print_benchmark_results', 1, 4, 3).
python_function('src/prefact/rules/benchmark.py', 'main', 0, 1, 10).
python_function('src/prefact/rules/composite_factory.py', 'register_composite_rules', 1, 4, 4).
python_function('src/prefact/rules/import_linter_based.py', 'generate_import_linter_config', 2, 7, 4).
python_function('src/prefact/rules/migration.py', 'add_ruff_config_to_prefact_yaml', 1, 3, 3).
python_function('src/prefact/rules/pylint_based.py', 'generate_pylint_rc', 2, 4, 3).
python_function('src/prefact/rules/registry.py', 'get_lazy_registry', 0, 2, 1).
python_function('src/prefact/rules/registry.py', 'get_all_rules', 0, 3, 2).
python_function('src/prefact/rules/registry.py', 'get_rule', 1, 5, 2).
python_function('src/prefact/rules/registry.py', 'register', 1, 2, 3).
python_function('src/prefact/rules/registry.py', '_initialize_built_in_rules', 0, 1, 2).
python_function('src/prefact/rules/relative_imports.py', '_module_to_str', 1, 4, 2).
python_function('src/prefact/rules/relative_imports.py', '_str_to_module', 1, 2, 3).
python_function('src/prefact/rules/sorted_imports.py', '_sort_key', 1, 6, 4).
python_function('src/prefact/rules/string_concat.py', '_is_str_concat', 1, 6, 3).
python_function('src/prefact/rules/string_concat.py', '_flatten_add', 1, 3, 2).
python_function('src/prefact/rules/unused_imports.py', '_collect_imported_names', 1, 8, 3).
python_function('src/prefact/rules/unused_imports.py', '_collect_used_names', 1, 5, 4).
python_function('src/prefact/rules/unused_imports.py', '_collect_all_exports', 1, 10, 4).
python_function('src/prefact/scanner.py', '_load_gitignore', 1, 6, 5).
python_function('src/prefact/scanner.py', '_match_gitignore_pattern', 2, 12, 9).
python_function('test_large_files.py', 'test_large_file_handling', 0, 7, 8).
python_function('tests/test_autonomous_limits.py', '_write_prefact_config', 2, 1, 2).
python_function('tests/test_autonomous_limits.py', '_issue_group', 3, 2, 2).
python_function('tests/test_autonomous_limits.py', 'test_config_generator_includes_autonomous_limits', 1, 6, 2).
python_function('tests/test_autonomous_limits.py', 'test_config_validator_rejects_invalid_autonomous_limits', 1, 3, 2).
python_function('tests/test_autonomous_limits.py', 'test_project_scanner_respects_configured_example_limit', 1, 5, 5).
python_function('tests/test_autonomous_limits.py', 'test_project_scanner_caps_files_to_scan', 1, 3, 8).
python_function('tests/test_autonomous_limits.py', 'test_project_scanner_caps_issues_per_file', 1, 4, 5).
python_function('tests/test_autonomous_limits.py', 'test_autonomous_refact_caps_grouped_issues_before_distribution', 1, 4, 5).
python_function('tests/test_autonomous_limits.py', 'test_autonomous_refact_stops_before_docs_when_time_limit_exceeded', 1, 3, 5).
python_function('tests/test_autonomous_limits.py', 'test_autonomous_refact_prints_final_summary', 2, 3, 4).
python_function('tests/test_autonomous_limits.py', 'test_docs_manager_respects_total_ticket_limit', 1, 4, 9).
python_function('tests/test_autonomous_limits.py', 'test_docs_manager_reports_skipped_ticket_count', 2, 3, 5).
python_function('tests/test_autonomous_limits.py', 'test_todo_manager_reports_skipped_todo_counts', 2, 3, 7).
python_function('tests/test_autonomous_limits.py', 'test_todo_manager_limits_output_and_normalizes_existing_paths', 1, 6, 8).
python_function('tests/test_autonomous_limits.py', 'test_todo_manager_execute_todos_respects_execution_limit', 1, 4, 6).
python_function('tests/test_config.py', 'project_with_pyproject', 1, 1, 2).
python_function('tests/test_dependency_checker.py', 'project_with_pyproject', 1, 1, 1).
python_function('tests/test_dependency_checker.py', 'project_with_requirements', 1, 1, 1).
python_function('tests/test_dependency_checker.py', 'pip_outdated_json', 0, 1, 1).
python_function('tests/test_engine.py', 'project', 1, 1, 3).
python_function('tests/test_integrations.py', 'test_ruff_integration', 0, 4, 13).
python_function('tests/test_integrations.py', 'test_mypy_integration', 0, 2, 9).
python_function('tests/test_integrations.py', 'test_isort_integration', 0, 5, 11).
python_function('tests/test_integrations.py', 'test_autoflake_integration', 0, 2, 9).
python_function('tests/test_integrations.py', 'test_string_transformations', 0, 4, 10).
python_function('tests/test_integrations.py', 'test_full_pipeline', 0, 5, 11).
python_function('tests/test_integrations.py', 'test_performance_comparison', 0, 3, 13).
python_function('tests/test_integrations.py', 'run_integration_tests', 0, 5, 16).
python_function('tests/test_refactoring.py', 'test_placeholder', 0, 2, 0).
python_function('tests/test_refactoring.py', 'test_import', 0, 1, 0).
python_function('tests/test_relative_imports.py', 'config', 1, 1, 3).
python_function('tests/test_rules.py', 'config', 1, 1, 1).
python_function('tests/test_testql_manager.py', 'planfile_stub', 1, 1, 6).
python_function('tests/test_testql_manager.py', 'test_run_testql_creates_and_syncs_tickets', 2, 11, 4).
python_function('tests/test_testql_manager.py', 'test_run_testql_respects_no_create_tickets', 2, 7, 3).
python_function('tests/test_testql_manager.py', 'test_discover_scenarios_returns_sorted_glob', 1, 2, 4).
python_function('tests/test_testql_manager.py', 'test_run_testql_all_skips_when_no_scenarios', 2, 4, 2).
python_function('tests/test_testql_manager.py', 'test_run_testql_all_aggregates_results', 2, 6, 5).
python_function('tests/test_testql_manager.py', '_stub_pipeline_steps', 2, 1, 1).
python_function('tests/test_testql_manager.py', 'test_run_autonomous_with_testql_invokes_run_all', 2, 4, 6).
python_function('tests/test_testql_manager.py', 'test_run_autonomous_default_skips_testql', 2, 3, 5).
python_function('tests/test_unused_imports.py', 'config', 1, 1, 1).

% ── Python Classes ───────────────────────────────────────
python_class('examples/01-individual-rules/missing-return-type/after.py', 'Processor').
python_method('Processor', 'process', 1, 1, 1).
python_class('examples/01-individual-rules/missing-return-type/before.py', 'Processor').
python_method('Processor', 'process', 1, 1, 1).
python_class('examples/01-individual-rules/relative-imports/after.py', 'Processor').
python_method('Processor', '__init__', 0, 1, 1).
python_method('Processor', 'process', 0, 1, 1).
python_class('examples/01-individual-rules/relative-imports/before.py', 'Processor').
python_method('Processor', '__init__', 0, 1, 1).
python_method('Processor', 'process', 0, 1, 1).
python_class('examples/01-individual-rules/unused-imports/after.py', 'DataProcessor').
python_method('DataProcessor', '__init__', 0, 1, 1).
python_method('DataProcessor', 'add_data', 2, 1, 0).
python_method('DataProcessor', 'get_data', 1, 1, 1).
python_class('examples/01-individual-rules/unused-imports/before.py', 'DataProcessor').
python_method('DataProcessor', '__init__', 0, 1, 1).
python_method('DataProcessor', 'add_data', 2, 1, 0).
python_method('DataProcessor', 'get_data', 1, 1, 1).
python_class('examples/02-multiple-rules/messy_module.py', 'DataProcessor').
python_method('DataProcessor', '__init__', 0, 1, 1).
python_method('DataProcessor', 'process', 1, 1, 3).
python_class('examples/04-custom-rules/custom_rules/no_todo_rule.py', 'NoTodoRule').
python_method('NoTodoRule', '__init__', 1, 1, 3).
python_method('NoTodoRule', 'scan_file', 2, 6, 8).
python_method('NoTodoRule', 'fix', 3, 1, 0).
python_method('NoTodoRule', 'validate', 3, 2, 2).
python_class('examples/04-custom-rules/custom_rules/no_todo_rule.py', 'NoPrintRule').
python_method('NoPrintRule', 'scan_file', 2, 6, 5).
python_method('NoPrintRule', 'fix', 3, 1, 0).
python_method('NoPrintRule', 'validate', 3, 2, 2).
python_class('examples/sample-project/core.py', 'DataProcessor').
python_method('DataProcessor', '__init__', 0, 1, 1).
python_method('DataProcessor', 'add_item', 1, 1, 1).
python_method('DataProcessor', 'get_summary', 0, 1, 2).
python_class('examples/sample-project/models.py', 'User').
python_method('User', '__post_init__', 0, 2, 3).
python_class('examples/sample-project/models.py', 'Post').
python_method('Post', '__post_init__', 0, 2, 3).
python_method('Post', 'get_summary', 0, 1, 0).
python_class('examples/sample-project/utils.py', 'UtilClass').
python_method('UtilClass', '__init__', 0, 1, 1).
python_method('UtilClass', 'get_cached', 1, 2, 0).
python_class('src/prefact/autonomous/__init__.py', 'AutonomousRefact').
python_method('AutonomousRefact', '__init__', 2, 3, 6).
python_method('AutonomousRefact', 'run_autonomous', 1, 7, 13).
python_method('AutonomousRefact', 'create_refact_config', 0, 1, 1).
python_method('AutonomousRefact', 'detect_project_info', 0, 1, 1).
python_method('AutonomousRefact', 'run_examples', 0, 1, 1).
python_method('AutonomousRefact', 'scan_project', 0, 2, 5).
python_method('AutonomousRefact', 'group_issues', 1, 1, 1).
python_method('AutonomousRefact', 'update_planfile', 0, 1, 1).
python_method('AutonomousRefact', 'create_default_planfile', 0, 1, 1).
python_method('AutonomousRefact', 'create_ticket_from_issue', 1, 1, 1).
python_method('AutonomousRefact', 'ticket_exists', 2, 1, 1).
python_method('AutonomousRefact', 'manage_documentation', 0, 1, 2).
python_method('AutonomousRefact', 'update_todo_md', 0, 1, 1).
python_method('AutonomousRefact', 'execute_todos', 0, 1, 1).
python_method('AutonomousRefact', 'update_changelog_md', 0, 1, 1).
python_method('AutonomousRefact', 'run_testql', 1, 1, 1).
python_method('AutonomousRefact', 'run_testql_all', 0, 1, 1).
python_method('AutonomousRefact', '_print_autonomous_summary', 0, 1, 2).
python_method('AutonomousRefact', 'run_tests', 0, 7, 4).
python_class('src/prefact/autonomous/_base.py', 'BaseManager').
python_method('BaseManager', '__init__', 1, 1, 0).
python_method('BaseManager', 'get_autonomous_limit', 1, 1, 1).
python_method('BaseManager', '_load_autonomous_limits', 0, 10, 7).
python_class('src/prefact/autonomous/dependency_checker.py', 'DependencyChecker').
python_method('DependencyChecker', '__init__', 1, 1, 2).
python_method('DependencyChecker', 'check_dependencies', 0, 4, 5).
python_method('DependencyChecker', '_collect_declared_deps', 0, 1, 2).
python_method('DependencyChecker', '_parse_pyproject_toml', 0, 6, 7).
python_method('DependencyChecker', '_parse_requirements_files', 0, 10, 10).
python_method('DependencyChecker', '_query_pip_outdated', 0, 6, 8).
python_method('DependencyChecker', '_build_issue_groups', 0, 3, 5).
python_method('DependencyChecker', '_find_dep_source_file', 0, 3, 3).
python_method('DependencyChecker', '_find_dep_line', 2, 5, 5).
python_method('DependencyChecker', '_normalize', 1, 1, 2).
python_method('DependencyChecker', '_parse_dep_string', 1, 4, 4).
python_class('src/prefact/autonomous/docs_manager.py', 'DocsManager').
python_method('DocsManager', '__init__', 1, 1, 2).
python_method('DocsManager', 'update_planfile', 0, 27, 21).
python_method('DocsManager', '_count_existing_tickets', 1, 2, 2).
python_method('DocsManager', '_should_remove_obsolete_ticket', 2, 3, 4).
python_method('DocsManager', '_is_autonomous_ticket', 1, 5, 3).
python_method('DocsManager', 'create_default_planfile', 0, 1, 0).
python_method('DocsManager', 'create_ticket_from_issue', 1, 8, 8).
python_method('DocsManager', 'ticket_exists', 2, 6, 1).
python_method('DocsManager', 'update_changelog_md', 0, 6, 11).
python_method('DocsManager', '_get_relative_file_path', 1, 3, 5).
python_class('src/prefact/autonomous/project_scanner.py', 'ProjectScanner').
python_method('ProjectScanner', '__init__', 2, 2, 2).
python_method('ProjectScanner', 'scan_project', 0, 11, 17).
python_method('ProjectScanner', '_scan_files_with_progress', 3, 3, 9).
python_method('ProjectScanner', '_scan_files_parallel', 6, 3, 14).
python_method('ProjectScanner', '_scan_files_sequential', 5, 5, 8).
python_method('ProjectScanner', '_scan_single_file', 2, 5, 7).
python_method('ProjectScanner', 'group_issues', 1, 7, 9).
python_class('src/prefact/autonomous/setup_manager.py', 'SetupManager').
python_method('SetupManager', 'create_refact_config', 0, 2, 7).
python_method('SetupManager', 'detect_project_info', 0, 9, 5).
python_method('SetupManager', 'run_examples', 0, 6, 10).
python_class('src/prefact/autonomous/testql_manager.py', 'TestQLManager').
python_method('TestQLManager', 'run', 1, 15, 11).
python_method('TestQLManager', 'discover_scenarios', 1, 5, 7).
python_method('TestQLManager', 'run_all', 0, 8, 8).
python_class('src/prefact/autonomous/todo_manager.py', 'TodoManager').
python_method('TodoManager', '__init__', 1, 1, 2).
python_method('TodoManager', 'update_todo_md', 0, 1, 4).
python_method('TodoManager', '_parse_existing_todos', 0, 13, 9).
python_method('TodoManager', '_generate_current_todos', 1, 8, 8).
python_method('TodoManager', '_find_completed_tasks', 2, 6, 6).
python_method('TodoManager', '_write_todo_md', 4, 5, 6).
python_method('TodoManager', '_get_relative_file_path', 1, 3, 5).
python_method('TodoManager', 'execute_todos', 0, 4, 8).
python_method('TodoManager', '_parse_todo_tasks', 0, 9, 7).
python_method('TodoManager', '_get_refactoring_config', 0, 3, 3).
python_method('TodoManager', '_limit_todo_execution_tasks', 1, 2, 3).
python_method('TodoManager', '_execute_todo_tasks', 1, 6, 10).
python_method('TodoManager', '_group_tasks_by_file', 1, 3, 1).
python_method('TodoManager', '_process_file_tasks', 4, 6, 6).
python_method('TodoManager', '_update_todo_with_execution_results', 4, 2, 5).
python_class('src/prefact/benchmark.py', 'ScanProbe').
python_method('ScanProbe', '__init__', 4, 2, 0).
python_method('ScanProbe', 'run', 0, 5, 13).
python_class('src/prefact/config.py', 'RuleConfig').
python_class('src/prefact/config.py', 'Config').
python_method('Config', 'from_yaml', 2, 4, 9).
python_method('Config', '_parse_rules', 2, 4, 3).
python_method('Config', '_get_default_patterns', 1, 1, 1).
python_method('Config', 'rule_enabled', 1, 2, 1).
python_method('Config', 'is_rule_enabled', 1, 1, 1).
python_method('Config', 'rule_options', 1, 2, 1).
python_method('Config', 'get_rule_option', 3, 1, 2).
python_method('Config', 'set_rule_option', 3, 2, 1).
python_method('Config', 'detect_package_name', 0, 4, 1).
python_method('Config', '_detect_from_pyproject', 0, 5, 6).
python_method('Config', '_get_tomllib', 0, 2, 0).
python_method('Config', '_detect_from_src_layout', 0, 5, 3).
python_method('Config', '_detect_from_root_layout', 0, 5, 3).
python_class('src/prefact/config_extended/config.py', 'ExtendedConfig').
python_method('ExtendedConfig', '__init__', 9, 10, 5).
python_method('ExtendedConfig', 'from_yaml', 3, 7, 11).
python_method('ExtendedConfig', '_parse_rules', 1, 9, 5).
python_method('ExtendedConfig', '_deep_merge', 2, 5, 4).
python_method('ExtendedConfig', 'get_tool_config', 1, 1, 1).
python_method('ExtendedConfig', 'get_performance_setting', 2, 1, 1).
python_method('ExtendedConfig', 'get_plugin_config', 1, 1, 1).
python_method('ExtendedConfig', 'to_dict', 0, 1, 3).
python_class('src/prefact/config_extended/generator.py', 'ConfigGenerator').
python_method('ConfigGenerator', 'generate_extended_config', 3, 12, 3).
python_method('ConfigGenerator', 'generate_composite_rule_config', 4, 2, 1).
python_method('ConfigGenerator', 'save_config', 2, 1, 2).
python_class('src/prefact/config_extended/models.py', 'ExtendedConfig').
python_method('ExtendedConfig', '__init__', 9, 6, 4).
python_method('ExtendedConfig', 'from_yaml', 3, 13, 13).
python_method('ExtendedConfig', 'to_dict', 0, 1, 3).
python_class('src/prefact/config_extended/validation.py', 'ConfigValidator').
python_method('ConfigValidator', 'validate', 1, 6, 7).
python_method('ConfigValidator', '_validate_ruff_config', 1, 6, 2).
python_method('ConfigValidator', '_validate_mypy_config', 1, 3, 2).
python_method('ConfigValidator', '_validate_isort_config', 1, 3, 2).
python_method('ConfigValidator', '_validate_performance_config', 1, 4, 2).
python_method('ConfigValidator', '_validate_rule_config', 2, 2, 1).
python_class('src/prefact/config_extended/validators.py', 'ConfigValidator').
python_method('ConfigValidator', 'validate', 1, 4, 5).
python_method('ConfigValidator', '_validate_ruff_config', 1, 4, 2).
python_method('ConfigValidator', '_validate_mypy_config', 1, 3, 1).
python_method('ConfigValidator', '_validate_performance_config', 1, 5, 2).
python_class('src/prefact/engine.py', 'RefactoringEngine').
python_method('RefactoringEngine', '__init__', 1, 1, 3).
python_method('RefactoringEngine', 'run', 0, 13, 14).
python_method('RefactoringEngine', 'scan_only', 0, 7, 8).
python_method('RefactoringEngine', 'run_file', 1, 5, 8).
python_method('RefactoringEngine', '_preload_sources', 1, 9, 7).
python_class('src/prefact/fixer.py', 'Fixer').
python_method('Fixer', '__init__', 1, 3, 4).
python_method('Fixer', 'fix_file', 2, 2, 2).
python_method('Fixer', 'fix_file_with_source', 3, 7, 9).
python_class('src/prefact/git_hooks.py', 'GitHooks').
python_method('GitHooks', '__init__', 2, 2, 3).
python_method('GitHooks', '_find_git_dir', 0, 2, 5).
python_method('GitHooks', 'install_hooks', 1, 3, 2).
python_method('GitHooks', '_install_hook', 2, 2, 8).
python_method('GitHooks', '_generate_hook_script', 1, 4, 4).
python_method('GitHooks', '_pre_commit_hook', 0, 1, 0).
python_method('GitHooks', '_pre_push_hook', 0, 1, 0).
python_method('GitHooks', '_commit_msg_hook', 0, 1, 0).
python_method('GitHooks', 'uninstall_hooks', 1, 6, 6).
python_method('GitHooks', 'list_hooks', 0, 3, 2).
python_method('GitHooks', 'test_hook', 1, 3, 3).
python_class('src/prefact/git_hooks.py', 'PreCommitConfig').
python_method('PreCommitConfig', 'generate_config', 1, 1, 0).
python_method('PreCommitConfig', 'install', 1, 3, 7).
python_class('src/prefact/logging/exceptions.py', 'PprefactException').
python_method('PprefactException', '__init__', 3, 1, 3).
python_class('src/prefact/logging/exceptions.py', 'ConfigurationError').
python_class('src/prefact/logging/exceptions.py', 'RuleError').
python_method('RuleError', '__init__', 3, 1, 2).
python_class('src/prefact/logging/exceptions.py', 'PluginError').
python_method('PluginError', '__init__', 2, 1, 2).
python_class('src/prefact/logging/formatters.py', 'JsonFormatter').
python_method('JsonFormatter', 'format', 1, 2, 6).
python_class('src/prefact/logging/levels.py', 'LogLevel').
python_class('src/prefact/logging/logger.py', 'LogLevel').
python_class('src/prefact/logging/logger.py', 'PprefactLogger').
python_method('PprefactLogger', '__init__', 5, 1, 6).
python_method('PprefactLogger', '_setup_handlers', 0, 3, 7).
python_method('PprefactLogger', 'debug', 1, 1, 1).
python_method('PprefactLogger', 'info', 1, 1, 1).
python_method('PprefactLogger', 'warning', 1, 1, 1).
python_method('PprefactLogger', 'error', 2, 2, 5).
python_method('PprefactLogger', 'critical', 2, 2, 5).
python_method('PprefactLogger', '_log', 2, 2, 6).
python_method('PprefactLogger', '_send_telemetry', 1, 3, 1).
python_method('PprefactLogger', 'add_telemetry_callback', 1, 1, 1).
python_method('PprefactLogger', 'log_scan_start', 2, 1, 1).
python_method('PprefactLogger', 'log_scan_complete', 3, 1, 1).
python_method('PprefactLogger', 'log_rule_execution', 4, 1, 2).
python_method('PprefactLogger', 'log_plugin_loaded', 2, 1, 1).
python_method('PprefactLogger', 'log_performance_metrics', 1, 1, 1).
python_class('src/prefact/models.py', 'Severity').
python_class('src/prefact/models.py', 'Phase').
python_class('src/prefact/models.py', 'Issue').
python_method('Issue', 'location', 0, 1, 0).
python_class('src/prefact/models.py', 'Fix').
python_class('src/prefact/models.py', 'ValidationResult').
python_class('src/prefact/models.py', 'PipelineResult').
python_method('PipelineResult', 'total_issues', 0, 1, 1).
python_method('PipelineResult', 'total_fixed', 0, 1, 1).
python_method('PipelineResult', 'total_failed', 0, 1, 1).
python_method('PipelineResult', 'all_valid', 0, 2, 1).
python_class('src/prefact/performance/cache/base.py', 'Cache').
python_method('Cache', '__init__', 2, 3, 6).
python_method('Cache', 'get', 2, 2, 1).
python_method('Cache', 'set', 3, 1, 1).
python_method('Cache', 'delete', 1, 2, 1).
python_method('Cache', 'clear', 0, 1, 1).
python_method('Cache', 'get_stats', 0, 2, 2).
python_method('Cache', 'close', 0, 1, 1).
python_class('src/prefact/performance/cache/config.py', 'ConfigCache').
python_method('ConfigCache', '__init__', 1, 1, 0).
python_method('ConfigCache', 'get_key', 1, 1, 5).
python_method('ConfigCache', 'get', 1, 1, 2).
python_method('ConfigCache', 'set', 2, 1, 2).
python_class('src/prefact/performance/cache/hash.py', 'FileHashCache').
python_method('FileHashCache', '__init__', 1, 1, 0).
python_method('FileHashCache', 'get_hash', 1, 3, 2).
python_method('FileHashCache', 'set_hash', 2, 1, 2).
python_class('src/prefact/performance/cache/rule.py', 'RuleResultCache').
python_method('RuleResultCache', '__init__', 1, 1, 0).
python_method('RuleResultCache', 'get_key', 4, 1, 0).
python_method('RuleResultCache', 'get', 4, 1, 2).
python_method('RuleResultCache', 'set', 6, 1, 2).
python_class('src/prefact/performance/cache/scan.py', 'ScanResultCache').
python_method('ScanResultCache', '__init__', 1, 1, 0).
python_method('ScanResultCache', 'get_key', 4, 1, 2).
python_method('ScanResultCache', 'get', 4, 1, 2).
python_method('ScanResultCache', 'set', 6, 1, 2).
python_method('ScanResultCache', 'invalidate_file', 1, 1, 0).
python_class('src/prefact/performance/cache.py', 'Cache').
python_method('Cache', '__init__', 2, 1, 6).
python_method('Cache', 'get', 2, 1, 1).
python_method('Cache', 'set', 3, 1, 1).
python_method('Cache', 'delete', 1, 2, 1).
python_method('Cache', 'clear', 0, 1, 1).
python_method('Cache', 'get_stats', 0, 2, 2).
python_method('Cache', 'close', 0, 1, 1).
python_class('src/prefact/performance/cache.py', 'ScanResultCache').
python_method('ScanResultCache', '__init__', 1, 1, 0).
python_method('ScanResultCache', 'get_key', 4, 1, 2).
python_method('ScanResultCache', 'get', 4, 1, 2).
python_method('ScanResultCache', 'set', 6, 1, 2).
python_method('ScanResultCache', 'invalidate_file', 1, 1, 0).
python_class('src/prefact/performance/cache.py', 'ConfigCache').
python_method('ConfigCache', '__init__', 1, 1, 0).
python_method('ConfigCache', 'get_key', 1, 1, 5).
python_method('ConfigCache', 'get', 1, 1, 2).
python_method('ConfigCache', 'set', 2, 1, 2).
python_class('src/prefact/performance/cache.py', 'RuleResultCache').
python_method('RuleResultCache', '__init__', 1, 1, 0).
python_method('RuleResultCache', 'get_key', 4, 1, 0).
python_method('RuleResultCache', 'get', 4, 1, 2).
python_method('RuleResultCache', 'set', 6, 1, 2).
python_class('src/prefact/performance/cache.py', 'FileHashCache').
python_method('FileHashCache', '__init__', 1, 1, 0).
python_method('FileHashCache', 'get_hash', 1, 3, 2).
python_method('FileHashCache', 'set_hash', 2, 1, 2).
python_class('src/prefact/performance/cache.py', 'CacheContext').
python_method('CacheContext', '__init__', 1, 1, 0).
python_method('CacheContext', '__enter__', 0, 1, 1).
python_method('CacheContext', '__exit__', 3, 1, 1).
python_class('src/prefact/performance/cache_adapters.py', 'ScanResultCache').
python_method('ScanResultCache', '__init__', 1, 1, 0).
python_method('ScanResultCache', 'get_key', 4, 1, 2).
python_method('ScanResultCache', 'get', 4, 1, 2).
python_method('ScanResultCache', 'set', 6, 1, 2).
python_method('ScanResultCache', 'invalidate_file', 1, 1, 0).
python_class('src/prefact/performance/cache_adapters.py', 'ConfigCache').
python_method('ConfigCache', '__init__', 1, 1, 0).
python_method('ConfigCache', 'get_key', 1, 1, 5).
python_method('ConfigCache', 'get', 1, 1, 2).
python_method('ConfigCache', 'set', 2, 1, 2).
python_class('src/prefact/performance/cache_adapters.py', 'RuleResultCache').
python_method('RuleResultCache', '__init__', 1, 1, 0).
python_method('RuleResultCache', 'get_key', 4, 1, 0).
python_method('RuleResultCache', 'get', 4, 1, 2).
python_method('RuleResultCache', 'set', 6, 1, 2).
python_class('src/prefact/performance/cache_adapters.py', 'FileHashCache').
python_method('FileHashCache', '__init__', 1, 1, 0).
python_method('FileHashCache', 'get_hash', 1, 3, 2).
python_method('FileHashCache', 'set_hash', 2, 1, 2).
python_class('src/prefact/performance/parallel.py', 'ParallelScanTask').
python_method('ParallelScanTask', '__init__', 4, 1, 1).
python_method('ParallelScanTask', '_calculate_file_hash', 0, 2, 4).
python_method('ParallelScanTask', 'execute', 0, 4, 10).
python_class('src/prefact/performance/parallel.py', 'ParallelEngine').
python_method('ParallelEngine', '__init__', 1, 1, 4).
python_method('ParallelEngine', 'scan_files', 2, 6, 7).
python_method('ParallelEngine', '_scan_with_thread_pool', 1, 4, 8).
python_method('ParallelEngine', '_scan_with_process_pool', 1, 5, 8).
python_method('ParallelEngine', '_execute_task_wrapper', 1, 1, 1).
python_method('ParallelEngine', '_get_enabled_rule_ids', 0, 3, 4).
python_method('ParallelEngine', 'fix_files', 2, 3, 6).
python_class('src/prefact/performance/parallel.py', 'ParallelScanner').
python_method('ParallelScanner', '__init__', 1, 1, 1).
python_method('ParallelScanner', 'scan_directory', 4, 7, 6).
python_method('ParallelScanner', 'scan_workspace', 1, 1, 1).
python_method('ParallelScanner', 'get_performance_stats', 0, 1, 1).
python_class('src/prefact/performance/parallel.py', 'PerformanceMonitor').
python_method('PerformanceMonitor', '__init__', 0, 1, 0).
python_method('PerformanceMonitor', 'start_timing', 0, 1, 1).
python_method('PerformanceMonitor', 'end_timing', 1, 1, 1).
python_method('PerformanceMonitor', 'record_cache_hit', 0, 1, 0).
python_method('PerformanceMonitor', 'record_cache_miss', 0, 1, 0).
python_method('PerformanceMonitor', 'get_stats', 0, 4, 1).
python_class('src/prefact/plugins/__init__.py', 'PluginMetadata').
python_method('PluginMetadata', '__init__', 6, 1, 1).
python_method('PluginMetadata', '_check_compatibility', 0, 1, 0).
python_class('src/prefact/plugins/__init__.py', 'PluginValidator').
python_method('PluginValidator', 'validate_plugin_module', 1, 7, 3).
python_method('PluginValidator', 'validate_plugin_path', 1, 3, 2).
python_class('src/prefact/plugins/__init__.py', 'PluginManager').
python_method('PluginManager', '__init__', 1, 1, 4).
python_method('PluginManager', 'discover_plugins', 0, 3, 4).
python_method('PluginManager', '_discover_entry_point_plugins', 0, 6, 6).
python_method('PluginManager', '_discover_local_plugins', 1, 4, 10).
python_method('PluginManager', 'load_plugin', 1, 10, 12).
python_method('PluginManager', 'load_all_plugins', 0, 4, 3).
python_method('PluginManager', 'get_rule', 1, 2, 2).
python_method('PluginManager', '_load_plugin_for_rule', 1, 5, 2).
python_method('PluginManager', 'list_plugins', 0, 4, 3).
python_method('PluginManager', '_is_rule_from_plugin', 2, 1, 0).
python_method('PluginManager', 'unload_plugin', 1, 2, 1).
python_class('src/prefact/rules/__init__.py', 'BaseRule').
python_method('BaseRule', '__init__', 1, 1, 0).
python_method('BaseRule', 'scan_file', 2, 1, 0).
python_method('BaseRule', 'fix', 3, 1, 0).
python_method('BaseRule', 'validate', 3, 1, 0).
python_method('BaseRule', '_validate_by_rescan', 5, 3, 4).
python_class('src/prefact/rules/ai_boilerplate.py', 'AIBoilerplateRule').
python_method('AIBoilerplateRule', '_get_boilerplate_patterns', 0, 1, 0).
python_method('AIBoilerplateRule', '_check_line', 3, 3, 4).
python_method('AIBoilerplateRule', 'scan_file', 2, 3, 5).
python_method('AIBoilerplateRule', 'fix', 3, 1, 0).
python_method('AIBoilerplateRule', 'validate', 3, 1, 1).
python_class('src/prefact/rules/autoflake_based.py', 'AutoflakeHelper').
python_method('AutoflakeHelper', 'check_file', 2, 3, 4).
python_method('AutoflakeHelper', 'check_source', 2, 1, 4).
python_method('AutoflakeHelper', 'fix_file', 2, 2, 2).
python_method('AutoflakeHelper', 'fix_source', 2, 2, 6).
python_class('src/prefact/rules/autoflake_based.py', 'AutoflakeUnusedImports').
python_method('AutoflakeUnusedImports', '__init__', 1, 1, 3).
python_method('AutoflakeUnusedImports', '_load_autoflake_config', 0, 1, 1).
python_method('AutoflakeUnusedImports', 'scan_file', 2, 1, 2).
python_method('AutoflakeUnusedImports', 'fix', 3, 3, 2).
python_method('AutoflakeUnusedImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/autoflake_based.py', 'AutoflakeUnusedVariables').
python_method('AutoflakeUnusedVariables', '__init__', 1, 1, 2).
python_class('src/prefact/rules/composite_factory.py', 'CompositeRuleFactory').
python_method('CompositeRuleFactory', 'create_composite_rule', 5, 1, 17).
python_class('src/prefact/rules/composite_rules.py', 'CompositeUnusedImports').
python_method('CompositeUnusedImports', '__init__', 1, 1, 4).
python_method('CompositeUnusedImports', '_create_strategy', 0, 3, 4).
python_method('CompositeUnusedImports', '_load_tools', 0, 4, 5).
python_method('CompositeUnusedImports', 'scan_file', 2, 2, 1).
python_method('CompositeUnusedImports', 'fix', 3, 5, 1).
python_method('CompositeUnusedImports', 'validate', 3, 2, 2).
python_class('src/prefact/rules/composite_rules.py', 'CompositeImportRules').
python_method('CompositeImportRules', '__init__', 1, 1, 4).
python_method('CompositeImportRules', '_load_tools', 0, 4, 10).
python_method('CompositeImportRules', 'scan_file', 2, 2, 1).
python_method('CompositeImportRules', 'fix', 3, 5, 1).
python_method('CompositeImportRules', 'validate', 3, 2, 4).
python_class('src/prefact/rules/composite_rules.py', 'CompositeTypeChecking').
python_method('CompositeTypeChecking', '__init__', 1, 1, 3).
python_method('CompositeTypeChecking', '_load_tools', 0, 4, 4).
python_method('CompositeTypeChecking', 'scan_file', 2, 2, 2).
python_method('CompositeTypeChecking', 'fix', 3, 5, 3).
python_method('CompositeTypeChecking', 'validate', 3, 2, 4).
python_class('src/prefact/rules/duplicate_imports.py', 'DuplicateImports').
python_method('DuplicateImports', 'scan_file', 2, 2, 8).
python_method('DuplicateImports', 'fix', 3, 7, 6).
python_method('DuplicateImports', 'validate', 3, 2, 3).
python_class('src/prefact/rules/import_linter_based.py', 'ImportLinterHelper').
python_method('ImportLinterHelper', 'create_config', 2, 5, 3).
python_method('ImportLinterHelper', 'run_linter', 1, 8, 8).
python_method('ImportLinterHelper', 'check_file', 2, 3, 7).
python_class('src/prefact/rules/import_linter_based.py', 'ImportLinterLayers').
python_method('ImportLinterLayers', '__init__', 1, 1, 3).
python_method('ImportLinterLayers', '_load_linter_config', 0, 2, 1).
python_method('ImportLinterLayers', 'scan_file', 2, 4, 4).
python_method('ImportLinterLayers', 'fix', 3, 4, 0).
python_method('ImportLinterLayers', 'validate', 3, 3, 3).
python_class('src/prefact/rules/import_linter_based.py', 'ImportLinterNoRelative').
python_method('ImportLinterNoRelative', '__init__', 1, 1, 3).
python_method('ImportLinterNoRelative', '_load_linter_config', 0, 2, 1).
python_method('ImportLinterNoRelative', 'scan_file', 2, 4, 8).
python_method('ImportLinterNoRelative', 'fix', 3, 4, 2).
python_method('ImportLinterNoRelative', 'validate', 3, 3, 3).
python_class('src/prefact/rules/import_linter_based.py', 'ImportLinterIndependence').
python_method('ImportLinterIndependence', '__init__', 1, 1, 3).
python_method('ImportLinterIndependence', '_load_linter_config', 0, 2, 1).
python_method('ImportLinterIndependence', 'scan_file', 2, 4, 4).
python_method('ImportLinterIndependence', 'fix', 3, 4, 0).
python_method('ImportLinterIndependence', 'validate', 3, 3, 3).
python_class('src/prefact/rules/import_linter_based.py', 'ImportLinterCustomArchitecture').
python_method('ImportLinterCustomArchitecture', '__init__', 1, 1, 3).
python_method('ImportLinterCustomArchitecture', '_load_custom_config', 0, 6, 1).
python_method('ImportLinterCustomArchitecture', 'scan_file', 2, 4, 5).
python_method('ImportLinterCustomArchitecture', 'fix', 3, 4, 3).
python_method('ImportLinterCustomArchitecture', 'validate', 3, 3, 3).
python_class('src/prefact/rules/importchecker_based.py', 'ImportCheckerHelper').
python_method('ImportCheckerHelper', 'check_file', 1, 5, 5).
python_method('ImportCheckerHelper', '_get_module_name', 1, 3, 3).
python_method('ImportCheckerHelper', 'check_source', 2, 1, 6).
python_class('src/prefact/rules/importchecker_based.py', 'ImportCheckerUnusedImports').
python_method('ImportCheckerUnusedImports', '__init__', 1, 1, 3).
python_method('ImportCheckerUnusedImports', '_load_checker_config', 0, 1, 1).
python_method('ImportCheckerUnusedImports', 'scan_file', 2, 6, 5).
python_method('ImportCheckerUnusedImports', '_find_import_lines', 1, 8, 7).
python_method('ImportCheckerUnusedImports', 'fix', 3, 1, 2).
python_method('ImportCheckerUnusedImports', 'validate', 3, 1, 3).
python_class('src/prefact/rules/importchecker_based.py', 'ImportCheckerDuplicateImports').
python_method('ImportCheckerDuplicateImports', 'scan_file', 2, 6, 6).
python_method('ImportCheckerDuplicateImports', 'fix', 3, 1, 2).
python_method('ImportCheckerDuplicateImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/importchecker_based.py', 'ImportDependencyAnalysis').
python_method('ImportDependencyAnalysis', '__init__', 1, 1, 3).
python_method('ImportDependencyAnalysis', '_load_checker_config', 0, 1, 1).
python_method('ImportDependencyAnalysis', 'scan_file', 2, 6, 6).
python_method('ImportDependencyAnalysis', '_extract_imports', 1, 6, 7).
python_method('ImportDependencyAnalysis', '_detect_circular_imports', 2, 5, 3).
python_method('ImportDependencyAnalysis', 'fix', 3, 1, 0).
python_method('ImportDependencyAnalysis', 'validate', 3, 1, 3).
python_class('src/prefact/rules/importchecker_based.py', 'ImportOptimizer').
python_method('ImportOptimizer', 'scan_file', 2, 6, 6).
python_method('ImportOptimizer', '_extract_all_imports', 1, 7, 7).
python_method('ImportOptimizer', '_count_usage', 2, 5, 7).
python_method('ImportOptimizer', 'fix', 3, 1, 0).
python_method('ImportOptimizer', 'validate', 3, 1, 1).
python_class('src/prefact/rules/isort_based.py', 'ISortHelper').
python_method('ISortHelper', 'check_file', 2, 2, 2).
python_method('ISortHelper', 'check_source', 2, 6, 8).
python_method('ISortHelper', '_find_import_blocks', 1, 9, 8).
python_method('ISortHelper', '_is_block_sorted', 2, 1, 2).
python_method('ISortHelper', '_needs_section_separators', 2, 1, 3).
python_method('ISortHelper', 'fix_file', 2, 3, 3).
python_method('ISortHelper', 'fix_source', 2, 2, 2).
python_class('src/prefact/rules/isort_based.py', 'ISortedImports').
python_method('ISortedImports', '__init__', 1, 1, 3).
python_method('ISortedImports', '_load_isort_config', 0, 2, 2).
python_method('ISortedImports', 'scan_file', 2, 13, 4).
python_method('ISortedImports', 'fix', 3, 4, 3).
python_method('ISortedImports', 'validate', 3, 4, 3).
python_class('src/prefact/rules/isort_based.py', 'ImportSectionSeparator').
python_method('ImportSectionSeparator', '__init__', 1, 1, 3).
python_method('ImportSectionSeparator', 'scan_file', 2, 13, 3).
python_method('ImportSectionSeparator', 'fix', 3, 4, 3).
python_method('ImportSectionSeparator', 'validate', 3, 4, 2).
python_class('src/prefact/rules/isort_based.py', 'CustomImportOrganization').
python_method('CustomImportOrganization', '__init__', 1, 1, 3).
python_method('CustomImportOrganization', '_load_custom_rules', 0, 1, 1).
python_method('CustomImportOrganization', 'scan_file', 2, 13, 7).
python_method('CustomImportOrganization', '_check_grouping', 2, 5, 1).
python_method('CustomImportOrganization', '_check_alphabetical', 2, 6, 4).
python_method('CustomImportOrganization', 'fix', 3, 4, 3).
python_method('CustomImportOrganization', 'validate', 3, 4, 3).
python_class('src/prefact/rules/llm_generated_code.py', 'LLMGeneratedCodeRule').
python_method('LLMGeneratedCodeRule', '__init__', 1, 1, 3).
python_method('LLMGeneratedCodeRule', '_load_indicators', 0, 1, 0).
python_method('LLMGeneratedCodeRule', 'scan_file', 2, 4, 11).
python_method('LLMGeneratedCodeRule', '_check_comment_ratio', 2, 7, 5).
python_method('LLMGeneratedCodeRule', '_check_docstring_patterns', 2, 7, 7).
python_method('LLMGeneratedCodeRule', '_has_llm_docstring_pattern', 1, 2, 2).
python_method('LLMGeneratedCodeRule', '_map_severity', 1, 1, 1).
python_method('LLMGeneratedCodeRule', 'fix', 3, 1, 0).
python_method('LLMGeneratedCodeRule', 'validate', 3, 1, 1).
python_class('src/prefact/rules/llm_hallucinations.py', 'LLMHallucinationRule').
python_method('LLMHallucinationRule', '__init__', 1, 1, 3).
python_method('LLMHallucinationRule', '_load_patterns', 0, 1, 1).
python_method('LLMHallucinationRule', 'scan_file', 2, 4, 10).
python_method('LLMHallucinationRule', '_check_ast_patterns', 2, 8, 7).
python_method('LLMHallucinationRule', '_is_suspicious_function_name', 1, 2, 2).
python_method('LLMHallucinationRule', '_is_suspicious_import', 1, 3, 1).
python_method('LLMHallucinationRule', '_map_severity', 1, 1, 1).
python_method('LLMHallucinationRule', 'fix', 3, 1, 0).
python_method('LLMHallucinationRule', 'validate', 3, 3, 3).
python_class('src/prefact/rules/magic_numbers.py', 'MagicNumberRule').
python_method('MagicNumberRule', '__init__', 1, 1, 4).
python_method('MagicNumberRule', '_load_allowed_numbers', 0, 1, 3).
python_method('MagicNumberRule', 'scan_file', 2, 5, 7).
python_method('MagicNumberRule', '_extract_literal_issues', 2, 6, 4).
python_method('MagicNumberRule', '_extract_comparison_issues', 2, 6, 5).
python_method('MagicNumberRule', '_is_magic_number', 1, 7, 2).
python_method('MagicNumberRule', 'fix', 3, 1, 0).
python_method('MagicNumberRule', 'validate', 3, 1, 1).
python_class('src/prefact/rules/migration.py', 'RuleMigrationManager').
python_method('RuleMigrationManager', '__init__', 1, 1, 0).
python_method('RuleMigrationManager', 'get_migrated_rule', 1, 3, 0).
python_method('RuleMigrationManager', 'should_use_ruff', 1, 3, 1).
python_method('RuleMigrationManager', 'create_hybrid_rule', 1, 2, 9).
python_class('src/prefact/rules/migration.py', 'HybridScanner').
python_method('HybridScanner', '__init__', 1, 1, 2).
python_method('HybridScanner', '_load_rules', 0, 5, 6).
python_method('HybridScanner', 'scan_file', 2, 3, 4).
python_class('src/prefact/rules/migration.py', 'PerformanceProfiler').
python_method('PerformanceProfiler', 'profile_rule', 3, 1, 3).
python_method('PerformanceProfiler', 'compare_implementations', 3, 5, 7).
python_class('src/prefact/rules/mypy_based.py', 'MyPyHelper').
python_method('MyPyHelper', 'check_file', 2, 9, 9).
python_method('MyPyHelper', 'check_source', 2, 1, 5).
python_class('src/prefact/rules/mypy_based.py', 'MyPyMissingReturnType').
python_method('MyPyMissingReturnType', '__init__', 1, 2, 3).
python_method('MyPyMissingReturnType', '_load_mypy_config', 0, 1, 1).
python_method('MyPyMissingReturnType', 'scan_file', 2, 9, 5).
python_method('MyPyMissingReturnType', '_is_public_function', 2, 3, 3).
python_method('MyPyMissingReturnType', 'fix', 3, 3, 0).
python_method('MyPyMissingReturnType', 'validate', 3, 2, 4).
python_class('src/prefact/rules/mypy_based.py', 'MyPyTypeChecking').
python_method('MyPyTypeChecking', '__init__', 1, 2, 3).
python_method('MyPyTypeChecking', '_load_mypy_config', 0, 1, 1).
python_method('MyPyTypeChecking', 'scan_file', 2, 9, 4).
python_method('MyPyTypeChecking', 'fix', 3, 3, 0).
python_method('MyPyTypeChecking', 'validate', 3, 2, 4).
python_class('src/prefact/rules/mypy_based.py', 'ReturnTypeInferrer').
python_method('ReturnTypeInferrer', 'infer_return_type', 2, 5, 5).
python_method('ReturnTypeInferrer', '_analyze_return_types', 1, 4, 5).
python_method('ReturnTypeInferrer', '_get_return_value_type', 1, 4, 4).
python_method('ReturnTypeInferrer', '_unify_types', 1, 5, 4).
python_class('src/prefact/rules/mypy_based.py', 'ReturnTypeAdder').
python_method('ReturnTypeAdder', '__init__', 2, 2, 0).
python_method('ReturnTypeAdder', 'leave_FunctionDef', 2, 3, 6).
python_class('src/prefact/rules/mypy_based.py', 'SmartReturnTypeRule').
python_method('SmartReturnTypeRule', 'scan_file', 2, 9, 7).
python_method('SmartReturnTypeRule', 'fix', 3, 3, 3).
python_method('SmartReturnTypeRule', 'validate', 3, 2, 2).
python_class('src/prefact/rules/print_statements.py', 'PrintStatements').
python_method('PrintStatements', 'scan_file', 2, 9, 8).
python_method('PrintStatements', 'fix', 3, 1, 0).
python_method('PrintStatements', 'validate', 3, 1, 1).
python_class('src/prefact/rules/pylint_based.py', 'PylintHelper').
python_method('PylintHelper', 'check_file', 2, 6, 6).
python_method('PylintHelper', 'check_source', 2, 1, 5).
python_method('PylintHelper', 'fix_file', 2, 1, 0).
python_class('src/prefact/rules/pylint_based.py', 'PylintPrintStatements').
python_method('PylintPrintStatements', '__init__', 1, 1, 3).
python_method('PylintPrintStatements', '_load_pylint_config', 0, 1, 1).
python_method('PylintPrintStatements', 'scan_file', 2, 3, 7).
python_method('PylintPrintStatements', 'fix', 3, 6, 7).
python_method('PylintPrintStatements', 'validate', 3, 3, 5).
python_class('src/prefact/rules/pylint_based.py', 'PylintStringConcat').
python_method('PylintStringConcat', '__init__', 1, 1, 3).
python_method('PylintStringConcat', '_load_pylint_config', 0, 1, 1).
python_method('PylintStringConcat', 'scan_file', 2, 3, 5).
python_method('PylintStringConcat', 'fix', 3, 6, 2).
python_method('PylintStringConcat', 'validate', 3, 3, 5).
python_class('src/prefact/rules/pylint_based.py', 'PprefactPylintPlugin').
python_method('PprefactPylintPlugin', 'register', 1, 1, 0).
python_class('src/prefact/rules/pylint_based.py', 'PylintComprehensive').
python_method('PylintComprehensive', '__init__', 1, 1, 3).
python_method('PylintComprehensive', '_load_pylint_config', 0, 1, 1).
python_method('PylintComprehensive', 'scan_file', 2, 3, 6).
python_method('PylintComprehensive', '_map_pylint_to_prefact', 1, 1, 1).
python_method('PylintComprehensive', '_map_pylint_severity', 1, 1, 2).
python_method('PylintComprehensive', 'fix', 3, 6, 6).
python_method('PylintComprehensive', 'validate', 3, 3, 4).
python_class('src/prefact/rules/registry.py', 'LazyRuleRegistry').
python_method('LazyRuleRegistry', '__init__', 0, 1, 0).
python_method('LazyRuleRegistry', 'get_rule', 1, 5, 2).
python_method('LazyRuleRegistry', '_load_module', 1, 3, 2).
python_method('LazyRuleRegistry', '_find_rule_class', 2, 8, 5).
python_method('LazyRuleRegistry', 'get_all_rules', 0, 3, 1).
python_method('LazyRuleRegistry', 'list_available_rules', 0, 1, 2).
python_method('LazyRuleRegistry', 'register_rule', 2, 1, 0).
python_method('LazyRuleRegistry', 'register_rule_module', 2, 1, 0).
python_class('src/prefact/rules/relative_imports.py', '_RelativeImportFixer').
python_method('_RelativeImportFixer', '__init__', 3, 1, 0).
python_method('_RelativeImportFixer', 'leave_ImportFrom', 2, 6, 8).
python_method('_RelativeImportFixer', '_resolve', 2, 9, 6).
python_class('src/prefact/rules/relative_imports.py', 'RelativeToAbsoluteImports').
python_method('RelativeToAbsoluteImports', '__init__', 1, 1, 3).
python_method('RelativeToAbsoluteImports', 'scan_file', 2, 8, 6).
python_method('RelativeToAbsoluteImports', 'fix', 3, 5, 6).
python_method('RelativeToAbsoluteImports', 'validate', 3, 14, 7).
python_class('src/prefact/rules/ruff_based.py', 'RuffHelper').
python_method('RuffHelper', 'check_file', 2, 3, 5).
python_method('RuffHelper', 'fix_file', 2, 2, 3).
python_method('RuffHelper', 'fix_source', 2, 2, 7).
python_class('src/prefact/rules/ruff_based.py', 'RuffWildcardImports').
python_method('RuffWildcardImports', 'scan_file', 2, 4, 3).
python_method('RuffWildcardImports', 'fix', 3, 1, 0).
python_method('RuffWildcardImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/ruff_based.py', 'RuffPrintStatements').
python_method('RuffPrintStatements', 'scan_file', 2, 4, 4).
python_method('RuffPrintStatements', '_should_ignore_file', 1, 2, 3).
python_method('RuffPrintStatements', 'fix', 3, 1, 4).
python_method('RuffPrintStatements', 'validate', 3, 1, 1).
python_class('src/prefact/rules/ruff_based.py', 'RuffUnusedImports').
python_method('RuffUnusedImports', 'scan_file', 2, 4, 4).
python_method('RuffUnusedImports', 'fix', 3, 1, 4).
python_method('RuffUnusedImports', 'validate', 3, 1, 3).
python_class('src/prefact/rules/ruff_based.py', 'RuffSortedImports').
python_method('RuffSortedImports', 'scan_file', 2, 4, 3).
python_method('RuffSortedImports', 'fix', 3, 1, 4).
python_method('RuffSortedImports', 'validate', 3, 1, 3).
python_class('src/prefact/rules/ruff_based.py', 'RuffDuplicateImports').
python_method('RuffDuplicateImports', 'scan_file', 2, 4, 4).
python_method('RuffDuplicateImports', 'fix', 3, 1, 0).
python_method('RuffDuplicateImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/sorted_imports.py', 'SortedImports').
python_method('SortedImports', 'scan_file', 2, 7, 8).
python_method('SortedImports', 'fix', 3, 1, 0).
python_method('SortedImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/strategies.py', 'ToolStrategy').
python_method('ToolStrategy', 'scan', 3, 5, 0).
python_method('ToolStrategy', 'fix', 4, 1, 0).
python_class('src/prefact/rules/strategies.py', 'ParallelScanStrategy').
python_method('ParallelScanStrategy', '__init__', 1, 1, 0).
python_method('ParallelScanStrategy', 'scan', 3, 5, 6).
python_method('ParallelScanStrategy', 'fix', 4, 1, 5).
python_class('src/prefact/rules/strategies.py', 'SequentialScanStrategy').
python_method('SequentialScanStrategy', 'scan', 3, 5, 4).
python_method('SequentialScanStrategy', 'fix', 4, 1, 2).
python_class('src/prefact/rules/strategies.py', 'PriorityBasedStrategy').
python_method('PriorityBasedStrategy', '__init__', 1, 1, 0).
python_method('PriorityBasedStrategy', 'scan', 3, 5, 7).
python_method('PriorityBasedStrategy', 'fix', 4, 1, 4).
python_class('src/prefact/rules/string_concat.py', 'StringConcatToFstring').
python_method('StringConcatToFstring', 'scan_file', 2, 5, 6).
python_method('StringConcatToFstring', 'fix', 3, 1, 0).
python_method('StringConcatToFstring', 'validate', 3, 1, 1).
python_class('src/prefact/rules/string_transformations.py', 'StringConcatTransformer').
python_method('StringConcatTransformer', '__init__', 0, 1, 0).
python_method('StringConcatTransformer', '_get_line_number', 1, 6, 1).
python_method('StringConcatTransformer', 'leave_BinaryOperation', 2, 4, 8).
python_method('StringConcatTransformer', '_collect_string_parts', 1, 1, 4).
python_method('StringConcatTransformer', '_eval_string', 1, 5, 2).
python_method('StringConcatTransformer', '_should_transform', 1, 5, 3).
python_method('StringConcatTransformer', '_create_fstring', 1, 4, 4).
python_class('src/prefact/rules/string_transformations.py', 'StringConcatToFString').
python_method('StringConcatToFString', 'scan_file', 2, 1, 6).
python_method('StringConcatToFString', '_is_string_concat', 1, 2, 2).
python_method('StringConcatToFString', 'fix', 3, 4, 6).
python_method('StringConcatToFString', 'validate', 3, 1, 7).
python_class('src/prefact/rules/string_transformations.py', 'FlyntHelper').
python_method('FlyntHelper', 'fix_source', 1, 3, 1).
python_class('src/prefact/rules/string_transformations.py', 'FlyntStringFormatting').
python_method('FlyntStringFormatting', 'scan_file', 2, 1, 2).
python_method('FlyntStringFormatting', 'fix', 3, 4, 3).
python_method('FlyntStringFormatting', 'validate', 3, 1, 2).
python_class('src/prefact/rules/string_transformations.py', 'ContextAwareStringTransformer').
python_method('ContextAwareStringTransformer', '__init__', 1, 1, 0).
python_method('ContextAwareStringTransformer', 'visit_FunctionDef', 1, 1, 0).
python_method('ContextAwareStringTransformer', 'leave_FunctionDef', 1, 1, 0).
python_method('ContextAwareStringTransformer', 'visit_ClassDef', 1, 1, 0).
python_method('ContextAwareStringTransformer', 'leave_ClassDef', 1, 1, 0).
python_method('ContextAwareStringTransformer', 'leave_BinaryOperation', 2, 4, 5).
python_method('ContextAwareStringTransformer', '_should_skip_context', 1, 4, 2).
python_method('ContextAwareStringTransformer', '_is_in_logging_statement', 1, 1, 0).
python_class('src/prefact/rules/string_transformations.py', 'ContextAwareStringConcat').
python_method('ContextAwareStringConcat', '__init__', 1, 1, 2).
python_method('ContextAwareStringConcat', 'scan_file', 2, 1, 2).
python_method('ContextAwareStringConcat', 'fix', 3, 4, 6).
python_method('ContextAwareStringConcat', 'validate', 3, 1, 2).
python_class('src/prefact/rules/type_hints.py', 'MissingReturnType').
python_method('MissingReturnType', 'scan_file', 2, 6, 6).
python_method('MissingReturnType', 'fix', 3, 1, 0).
python_method('MissingReturnType', 'validate', 3, 1, 1).
python_class('src/prefact/rules/unimport_based.py', 'UnimportHelper').
python_method('UnimportHelper', 'check_file', 2, 9, 7).
python_method('UnimportHelper', 'check_source', 2, 1, 5).
python_method('UnimportHelper', '_extract_import_name', 1, 3, 2).
python_method('UnimportHelper', 'fix_file', 2, 5, 4).
python_method('UnimportHelper', 'fix_source', 2, 2, 7).
python_class('src/prefact/rules/unimport_based.py', 'UnimportUnusedImports').
python_method('UnimportUnusedImports', '__init__', 1, 1, 3).
python_method('UnimportUnusedImports', '_load_unimport_config', 0, 1, 1).
python_method('UnimportUnusedImports', 'scan_file', 2, 1, 10).
python_method('UnimportUnusedImports', 'fix', 3, 4, 3).
python_method('UnimportUnusedImports', 'validate', 3, 1, 3).
python_class('src/prefact/rules/unimport_based.py', 'UnimportDuplicateImports').
python_method('UnimportDuplicateImports', '__init__', 1, 1, 2).
python_method('UnimportDuplicateImports', 'scan_file', 2, 1, 5).
python_method('UnimportDuplicateImports', 'fix', 3, 4, 3).
python_method('UnimportDuplicateImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/unimport_based.py', 'UnimportStarImports').
python_method('UnimportStarImports', '__init__', 1, 1, 2).
python_method('UnimportStarImports', 'scan_file', 2, 1, 6).
python_method('UnimportStarImports', 'fix', 3, 4, 3).
python_method('UnimportStarImports', 'validate', 3, 1, 1).
python_class('src/prefact/rules/unimport_based.py', 'UnimportAll').
python_method('UnimportAll', '__init__', 1, 1, 3).
python_method('UnimportAll', 'scan_file', 2, 1, 5).
python_method('UnimportAll', 'fix', 3, 4, 3).
python_method('UnimportAll', 'validate', 3, 1, 7).
python_class('src/prefact/rules/unused_imports.py', 'UnusedImports').
python_method('UnusedImports', 'scan_file', 2, 6, 8).
python_method('UnusedImports', 'validate', 3, 2, 3).
python_method('UnusedImports', 'fix', 3, 7, 9).
python_method('UnusedImports', 'remove_lines', 2, 3, 1).
python_method('UnusedImports', 'process_import_from', 7, 8, 5).
python_method('UnusedImports', 'process_import', 7, 8, 6).
python_method('UnusedImports', '_remove_unused_from_line', 2, 7, 6).
python_method('UnusedImports', '_remove_unused_from_import_line', 2, 7, 6).
python_class('src/prefact/rules/wildcard_imports.py', 'WildcardImports').
python_method('WildcardImports', 'scan_file', 2, 7, 5).
python_method('WildcardImports', 'fix', 3, 1, 0).
python_method('WildcardImports', 'validate', 3, 1, 1).
python_class('src/prefact/scanner.py', 'Scanner').
python_method('Scanner', '__init__', 1, 4, 6).
python_method('Scanner', 'collect_files', 0, 6, 7).
python_method('Scanner', 'scan', 1, 4, 3).
python_method('Scanner', 'scan_sources', 1, 4, 3).
python_method('Scanner', '_excluded', 1, 14, 6).
python_class('src/prefact/validator.py', 'Validator').
python_method('Validator', '__init__', 1, 3, 4).
python_method('Validator', 'validate_file', 4, 4, 3).
python_class('tests/test_config.py', 'TestConfig').
python_method('TestConfig', 'test_detect_from_pyproject', 1, 2, 2).
python_method('TestConfig', 'test_detect_from_src_layout', 1, 2, 4).
python_method('TestConfig', 'test_detect_top_level_package', 1, 2, 4).
python_method('TestConfig', 'test_from_yaml', 1, 4, 3).
python_method('TestConfig', 'test_rule_defaults', 0, 4, 3).
python_method('TestConfig', 'test_config_uses_defaults_include', 0, 2, 1).
python_method('TestConfig', 'test_config_uses_defaults_exclude', 0, 2, 1).
python_method('TestConfig', 'test_venv_variants_in_defaults', 0, 3, 0).
python_method('TestConfig', 'test_scanner_excludes_venv_test', 1, 4, 5).
python_method('TestConfig', 'test_config_extended_constants_reexport', 0, 3, 0).
python_class('tests/test_dependency_checker.py', 'TestDependencyChecker').
python_method('TestDependencyChecker', 'test_parse_pyproject_toml', 1, 4, 2).
python_method('TestDependencyChecker', 'test_parse_requirements_txt', 1, 5, 2).
python_method('TestDependencyChecker', 'test_no_dep_files', 1, 2, 2).
python_method('TestDependencyChecker', 'test_outdated_filtering', 3, 5, 5).
python_method('TestDependencyChecker', 'test_all_up_to_date', 2, 2, 4).
python_method('TestDependencyChecker', 'test_issue_group_shape', 3, 8, 5).
python_method('TestDependencyChecker', 'test_line_number_detection', 3, 5, 4).
python_method('TestDependencyChecker', 'test_normalize', 0, 4, 1).
python_method('TestDependencyChecker', 'test_pip_failure_graceful', 2, 2, 4).
python_class('tests/test_engine.py', 'TestEngine').
python_method('TestEngine', 'test_scan_only', 1, 4, 3).
python_method('TestEngine', 'test_full_pipeline_dry_run', 1, 4, 4).
python_method('TestEngine', 'test_full_pipeline_apply', 1, 4, 4).
python_method('TestEngine', 'test_run_single_file', 1, 2, 3).
python_method('TestEngine', 'test_backup_created', 1, 2, 5).
python_method('TestEngine', 'test_clean_project_no_issues', 1, 4, 7).
python_class('tests/test_integrations.py', 'IntegrationTestCase').
python_method('IntegrationTestCase', '__init__', 3, 1, 0).
python_method('IntegrationTestCase', 'run', 1, 3, 9).
python_class('tests/test_integrations.py', 'IntegrationTestSuite').
python_method('IntegrationTestSuite', '__init__', 0, 1, 1).
python_method('IntegrationTestSuite', '_create_test_cases', 0, 1, 1).
python_method('IntegrationTestSuite', 'run_all_tests', 1, 4, 6).
python_method('IntegrationTestSuite', '_compare_results', 2, 8, 3).
python_method('IntegrationTestSuite', '_issues_match', 2, 7, 1).
python_class('tests/test_relative_imports.py', 'TestScan').
python_method('TestScan', 'test_detects_relative_imports', 1, 5, 7).
python_method('TestScan', 'test_ignores_absolute_imports', 1, 2, 4).
python_method('TestScan', 'test_handles_syntax_error_gracefully', 1, 2, 2).
python_class('tests/test_relative_imports.py', 'TestFix').
python_method('TestFix', 'test_converts_single_dot_import', 1, 3, 6).
python_method('TestFix', 'test_converts_deep_relative_import', 1, 2, 5).
python_method('TestFix', 'test_preserves_absolute_imports', 1, 3, 6).
python_method('TestFix', 'test_no_fix_without_package_name', 1, 3, 4).
python_class('tests/test_relative_imports.py', 'TestValidate').
python_method('TestValidate', 'test_valid_after_fix', 1, 5, 2).
python_method('TestValidate', 'test_invalid_if_relative_remains', 1, 2, 2).
python_class('tests/test_rules.py', 'TestDuplicateImports').
python_method('TestDuplicateImports', 'test_detects_duplicate', 1, 3, 4).
python_method('TestDuplicateImports', 'test_no_duplicates', 1, 2, 2).
python_method('TestDuplicateImports', 'test_fix_removes_duplicate_line', 1, 3, 5).
python_class('tests/test_rules.py', 'TestWildcardImports').
python_method('TestWildcardImports', 'test_detects_wildcard', 1, 3, 3).
python_method('TestWildcardImports', 'test_no_autofix', 1, 3, 3).
python_class('tests/test_rules.py', 'TestStringConcat').
python_method('TestStringConcat', 'test_detects_concat', 1, 3, 4).
python_method('TestStringConcat', 'test_ignores_pure_string_concat', 1, 2, 3).
python_method('TestStringConcat', 'test_ignores_numeric_add', 1, 2, 3).
python_class('tests/test_rules.py', 'TestPrintStatements').
python_method('TestPrintStatements', 'test_detects_print', 1, 3, 4).
python_method('TestPrintStatements', 'test_no_print_no_issue', 1, 2, 2).
python_class('tests/test_rules.py', 'TestMissingReturnType').
python_method('TestMissingReturnType', 'test_detects_missing', 1, 3, 4).
python_method('TestMissingReturnType', 'test_has_return_type', 1, 2, 2).
python_method('TestMissingReturnType', 'test_skips_private', 1, 2, 2).
python_class('tests/test_rules.py', 'TestSortedImports').
python_method('TestSortedImports', 'test_detects_unsorted', 1, 3, 4).
python_method('TestSortedImports', 'test_sorted_ok', 1, 2, 2).
python_class('tests/test_unused_imports.py', 'TestScanUnused').
python_method('TestScanUnused', 'test_detects_unused', 1, 4, 3).
python_method('TestScanUnused', 'test_used_import_not_flagged', 1, 2, 2).
python_method('TestScanUnused', 'test_respects_all_exports', 1, 2, 2).
python_method('TestScanUnused', 'test_skips_underscore_imports', 1, 2, 2).
python_method('TestScanUnused', 'test_attribute_access_counts_as_used', 1, 2, 2).
python_class('tests/test_unused_imports.py', 'TestFixUnused').
python_method('TestFixUnused', 'test_removes_unused_line', 1, 4, 5).

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('VENV', '').
makefile_target('PYTHON', '').
makefile_target('PIP', '').
makefile_target('help', 'Default target').
makefile_target('venv', '').
makefile_target('VENV_TARGETS', '').
makefile_target('install', '').
makefile_target('dev-install', '').
makefile_target('test', '').
makefile_target('test-fast', 'Fast tests - exclude slow and integration tests').
makefile_target('test-slow', 'Slow tests only').
makefile_target('test-integration', 'Integration tests only').
makefile_target('test-unit', 'Unit tests only').
makefile_target('test-cov', '').
makefile_target('test-toon', '').
makefile_target('validate-toon', '').
makefile_target('test-all-formats', '').
makefile_target('test-comprehensive', '').
makefile_target('lint', '').
makefile_target('format', '').
makefile_target('typecheck', '').
makefile_target('check', '').
makefile_target('run', '').
makefile_target('analyze', '').
makefile_target('analyze-all', '').
makefile_target('toon-demo', '').
makefile_target('toon-compare', '').
makefile_target('toon-validate', '').
makefile_target('build', '').
makefile_target('publish-test', '').
makefile_target('bump-patch', '').
makefile_target('bump-minor', '').
makefile_target('bump-major', '').
makefile_target('publish', '').
makefile_target('mermaid-png', '').
makefile_target('install-mermaid', '').
makefile_target('check-mermaid', '').
makefile_target('clean', '').
makefile_target('clean-png', '').
makefile_target('quickstart', '').

% ── Taskfile Tasks ───────────────────────────────────────
taskfile_task('', 'Install Python dependencies (editable)').
taskfile_task('', 'Run pytest suite').
taskfile_task('', 'Run ruff lint check').
taskfile_task('', 'Auto-format with ruff').
taskfile_task('', 'Build wheel + sdist').
taskfile_task('', 'Remove build artefacts').
taskfile_task('', '[from doql] workflow: health').
taskfile_task('', 'Run install, lint, test').
taskfile_task('', 'Show available tasks').
taskfile_task('', 'Auto-format with ruff (alias of fmt)').
taskfile_task('', 'Generate SUMD (Structured Unified Markdown Descriptor) for AI-aware project description').
taskfile_task('', 'Generate SUMR (Summary Report) with project metrics and health status').

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('PFIX_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-cli-tests.testql.toon.yaml', 'cli').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-cli-tests.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('Taskfile.yml', 'taskfile').
sumd_declared_file('pyqual.yaml', 'pyqual').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('cli', 'click').
sumd_interface('cli', '').
sumd_workflow('venv', 'manual').
sumd_workflow_step('venv', 1, 'if [ ! -x "$(PYTHON)" ]').
sumd_workflow_step('venv', 2, 'echo "Creating virtual environment in $(VENV)..."').
sumd_workflow_step('venv', 3, 'python3 -m venv "$(VENV)"').
sumd_workflow_step('venv', 4, 'fi').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, '$(PIP) install -e .').
sumd_workflow_step('install', 2, 'echo "✓ code2llm installed with TOON format support"').
sumd_workflow('dev-install', 'manual').
sumd_workflow_step('dev-install', 1, '$(PIP) install -e ".[dev]"').
sumd_workflow_step('dev-install', 2, 'echo "✓ code2llm installed with dev dependencies"').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, '$(PYTHON) -m pytest tests/ -v --tb=short').
sumd_workflow('test-fast', 'manual').
sumd_workflow_step('test-fast', 1, '$(PYTHON) -m pytest -m "not slow and not integration" -v --tb=short -n auto').
sumd_workflow('test-slow', 'manual').
sumd_workflow_step('test-slow', 1, '$(PYTHON) -m pytest -m "slow" -v --tb=short').
sumd_workflow('test-integration', 'manual').
sumd_workflow_step('test-integration', 1, '$(PYTHON) -m pytest -m "integration" -v --tb=short').
sumd_workflow('test-unit', 'manual').
sumd_workflow_step('test-unit', 1, '$(PYTHON) -m pytest -m "unit" -v --tb=short').
sumd_workflow('test-cov', 'manual').
sumd_workflow_step('test-cov', 1, '$(PYTHON) -m pytest tests/ --cov=code2llm --cov-report=html --cov-report=term 2>/dev/null || echo "No tests yet"').
sumd_workflow('test-toon', 'manual').
sumd_workflow_step('test-toon', 1, 'echo "🎯 Testing TOON format..."').
sumd_workflow_step('test-toon', 2, '$(PYTHON) -m code2llm ./ -v -o ./test_toon -m hybrid -f toon').
sumd_workflow_step('test-toon', 3, '$(PYTHON) validate_toon.py test_toon/analysis.toon').
sumd_workflow_step('test-toon', 4, 'echo "✓ TOON format test complete"').
sumd_workflow('validate-toon', 'manual').
sumd_workflow('test-all-formats', 'manual').
sumd_workflow_step('test-all-formats', 1, 'echo "📊 Testing all output formats..."').
sumd_workflow_step('test-all-formats', 2, '$(PYTHON) -m code2llm ./ -v -o ./test_all -m hybrid -f all').
sumd_workflow_step('test-all-formats', 3, '$(PYTHON) validate_toon.py test_all/analysis.toon').
sumd_workflow_step('test-all-formats', 4, 'echo "✓ All formats test complete"').
sumd_workflow('test-comprehensive', 'manual').
sumd_workflow_step('test-comprehensive', 1, 'echo "🚀 Running comprehensive test suite..."').
sumd_workflow_step('test-comprehensive', 2, 'bash project.sh').
sumd_workflow_step('test-comprehensive', 3, 'echo "✓ Comprehensive tests complete"').
sumd_workflow('lint', 'manual').
sumd_workflow_step('lint', 1, '$(PYTHON) -m flake8 code2llm/ --max-line-length=100 --ignore=E203,W503 2>/dev/null || echo "flake8 not installed"').
sumd_workflow_step('lint', 2, '$(PYTHON) -m black --check code2llm/ 2>/dev/null || echo "black not installed"').
sumd_workflow_step('lint', 3, 'echo "✓ Linting complete"').
sumd_workflow('format', 'manual').
sumd_workflow_step('format', 1, '$(PYTHON) -m black code2llm/ --line-length=100 2>/dev/null || echo "black not installed, run: pip install black"').
sumd_workflow_step('format', 2, 'echo "✓ Code formatted"').
sumd_workflow('typecheck', 'manual').
sumd_workflow_step('typecheck', 1, '$(PYTHON) -m mypy code2llm/ --ignore-missing-imports 2>/dev/null || echo "mypy not installed"').
sumd_workflow('check', 'manual').
sumd_workflow_step('check', 1, 'echo "✓ All checks passed"').
sumd_workflow('run', 'manual').
sumd_workflow_step('run', 1, '$(PYTHON) -m code2llm ../python/stts_core -v -o ./output').
sumd_workflow('analyze', 'manual').
sumd_workflow_step('analyze', 1, 'echo "🎯 Running TOON format analysis on current project..."').
sumd_workflow_step('analyze', 2, '$(PYTHON) -m code2llm ./ -v -o ./analysis -m hybrid -f toon').
sumd_workflow_step('analyze', 3, '$(PYTHON) validate_toon.py analysis/analysis.toon').
sumd_workflow_step('analyze', 4, 'echo "✓ TOON analysis complete - check analysis/analysis.toon"').
sumd_workflow('analyze-all', 'manual').
sumd_workflow_step('analyze-all', 1, 'echo "📊 Running analysis with all formats..."').
sumd_workflow_step('analyze-all', 2, '$(PYTHON) -m code2llm ./ -v -o ./analysis_all -m hybrid -f all').
sumd_workflow_step('analyze-all', 3, '$(PYTHON) validate_toon.py analysis_all/analysis.toon').
sumd_workflow_step('analyze-all', 4, 'echo "✓ All formats analysis complete - check analysis_all/"').
sumd_workflow('toon-demo', 'manual').
sumd_workflow_step('toon-demo', 1, 'echo "🎯 Quick TOON format demo..."').
sumd_workflow_step('toon-demo', 2, '$(PYTHON) -m code2llm ./ -v -o ./demo -m hybrid -f toon').
sumd_workflow_step('toon-demo', 3, 'echo "📁 Generated: demo/analysis.toon"').
sumd_workflow_step('toon-demo', 4, 'echo "📊 Size: $$(du -h demo/analysis.toon | cut -f1)"').
sumd_workflow_step('toon-demo', 5, 'echo "🔍 Preview:"').
sumd_workflow_step('toon-demo', 6, 'head -20 demo/analysis.toon').
sumd_workflow('toon-compare', 'manual').
sumd_workflow_step('toon-compare', 1, 'echo "📊 Comparing TOON vs YAML formats..."').
sumd_workflow_step('toon-compare', 2, '$(PYTHON) -m code2llm ./ -v -o ./compare -m hybrid -f toon,yaml').
sumd_workflow_step('toon-compare', 3, 'echo "📁 Files generated:"').
sumd_workflow_step('toon-compare', 4, 'echo "  - TOON:  compare/analysis.toon  ($$(du -h compare/analysis.toon | cut -f1))"').
sumd_workflow_step('toon-compare', 5, 'echo "  - YAML:  compare/analysis.yaml  ($$(du -h compare/analysis.yaml | cut -f1))"').
sumd_workflow_step('toon-compare', 6, 'echo "  - Ratio: $$(echo "scale=1').
sumd_workflow_step('toon-compare', 7, '$(PYTHON) validate_toon.py compare/analysis.yaml compare/analysis.toon').
sumd_workflow('toon-validate', 'manual').
sumd_workflow_step('toon-validate', 1, 'echo "🔍 Validating TOON format structure..."').
sumd_workflow_step('toon-validate', 2, '$(PYTHON) validate_toon.py analysis/analysis.toon 2>/dev/null || $(PYTHON) validate_toon.py test_toon/analysis.toon 2>/dev/null || echo "Run \'make test-toon\' first"').
sumd_workflow('build', 'manual').
sumd_workflow_step('build', 1, 'rm -rf build/ dist/ *.egg-info').
sumd_workflow_step('build', 2, '$(PYTHON) -m build').
sumd_workflow_step('build', 3, 'echo "✓ Build complete - check dist/"').
sumd_workflow('publish-test', 'manual').
sumd_workflow_step('publish-test', 1, 'echo "🚀 Publishing to TestPyPI..."').
sumd_workflow('bump-patch', 'manual').
sumd_workflow_step('bump-patch', 1, 'echo "🔢 Bumping patch version..."').
sumd_workflow_step('bump-patch', 2, '$(PYTHON) scripts/bump_version.py patch 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually"').
sumd_workflow('bump-minor', 'manual').
sumd_workflow_step('bump-minor', 1, 'echo "🔢 Bumping minor version..."').
sumd_workflow_step('bump-minor', 2, '$(PYTHON) scripts/bump_version.py minor 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually"').
sumd_workflow('bump-major', 'manual').
sumd_workflow_step('bump-major', 1, 'echo "🔢 Bumping major version..."').
sumd_workflow_step('bump-major', 2, '$(PYTHON) scripts/bump_version.py major 2>/dev/null || echo "Create scripts/bump_version.py or edit pyproject.toml manually"').
sumd_workflow('publish', 'manual').
sumd_workflow_step('publish', 1, 'echo "🚀 Publishing to PyPI..."').
sumd_workflow('mermaid-png', 'manual').
sumd_workflow_step('mermaid-png', 1, '$(PYTHON) mermaid_to_png.py --batch output output').
sumd_workflow('install-mermaid', 'manual').
sumd_workflow_step('install-mermaid', 1, 'npm install -g @mermaid-js/mermaid-cli').
sumd_workflow('check-mermaid', 'manual').
sumd_workflow_step('check-mermaid', 1, 'echo "Checking available Mermaid renderers..."').
sumd_workflow_step('check-mermaid', 2, 'which mmdc > /dev/null && echo "✓ mmdc (mermaid-cli)" || echo "✗ mmdc (run: npm install -g @mermaid-js/mermaid-cli)"').
sumd_workflow_step('check-mermaid', 3, 'which npx > /dev/null && echo "✓ npx (for @mermaid-js/mermaid-cli)" || echo "✗ npx (install Node.js)"').
sumd_workflow_step('check-mermaid', 4, 'which puppeteer > /dev/null && echo "✓ puppeteer" || echo "✗ puppeteer (run: npm install -g puppeteer)"').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'rm -rf build/ dist/ *.egg-info').
sumd_workflow_step('clean', 2, 'rm -rf .pytest_cache .coverage htmlcov/').
sumd_workflow_step('clean', 3, 'rm -rf code2llm/__pycache__ code2llm/*/__pycache__').
sumd_workflow_step('clean', 4, 'rm -rf test_* demo compare analysis analysis_all output_* 2>/dev/null || true').
sumd_workflow_step('clean', 5, 'find . -name "*.pyc" -delete 2>/dev/null || true').
sumd_workflow('clean-png', 'manual').
sumd_workflow_step('clean-png', 1, 'rm -f output/*.png').
sumd_workflow_step('clean-png', 2, 'echo "✓ Cleaned PNG files"').
sumd_workflow('quickstart', 'manual').
sumd_workflow_step('quickstart', 1, 'echo "🚀 Quick Start with code2llm TOON format:"').
sumd_workflow_step('quickstart', 2, 'echo ""').
sumd_workflow_step('quickstart', 3, 'echo "1. Install:        make install"').
sumd_workflow_step('quickstart', 4, 'echo "2. Test TOON:      make test-toon"').
sumd_workflow_step('quickstart', 5, 'echo "3. Analyze:        make analyze"').
sumd_workflow_step('quickstart', 6, 'echo "4. Compare:        make toon-compare"').
sumd_workflow_step('quickstart', 7, 'echo "5. All formats:    make test-all-formats"').
sumd_workflow_step('quickstart', 8, 'echo ""').
sumd_workflow_step('quickstart', 9, 'echo "📖 For more: make help"').
sumd_workflow('fmt', 'manual').
sumd_workflow_step('fmt', 1, 'ruff format .').
sumd_workflow('health', 'manual').
sumd_workflow_step('health', 1, 'docker compose ps').
sumd_workflow_step('health', 2, 'docker compose exec app echo "Health check passed"').
sumd_workflow('all', 'manual').
sumd_workflow_step('all', 1, 'taskfile run install').
sumd_workflow_step('all', 2, 'taskfile run lint').
sumd_workflow_step('all', 3, 'taskfile run test').
sumd_workflow('help', 'manual').
sumd_workflow_step('help', 1, 'echo "prefact — available tasks:"').
sumd_workflow_step('help', 2, 'echo ""').
sumd_workflow_step('help', 3, 'taskfile list').
sumd_workflow('sumd', 'manual').
sumd_workflow('sumr', 'manual').
```

## Call Graph

*183 nodes · 169 edges · 51 modules · CC̄=3.0*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `super` *(in vscode-extension.src.extension.PrefactTreeItem)* | 1 | 42 | 0 | **42** |
| `update_planfile` *(in src.prefact.autonomous.docs_manager.DocsManager)* | 27 ⚠ | 0 | 41 | **41** |
| `_initialize_built_in_rules` *(in src.prefact.rules.registry)* | 1 | 0 | 31 | **31** |
| `run_prefact_example` *(in examples.06-api-usage.example)* | 11 ⚠ | 1 | 28 | **29** |
| `from_yaml` *(in src.prefact.config_extended.models.ExtendedConfig)* | 13 ⚠ | 0 | 27 | **27** |
| `build_prefact_suite` *(in src.prefact.benchmark)* | 3 | 1 | 26 | **27** |
| `main` *(in examples.run_examples)* | 8 | 0 | 25 | **25** |
| `benchmark_file` *(in src.prefact.rules.benchmark)* | 6 | 1 | 20 | **21** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/prefact
# generated in 0.10s
# nodes: 183 | edges: 169 | modules: 51
# CC̄=3.0

HUBS[20]:
  vscode-extension.src.extension.PrefactTreeItem.super
    CC=1  in:42  out:0  total:42
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile
    CC=27  in:0  out:41  total:41
  src.prefact.rules.registry._initialize_built_in_rules
    CC=1  in:0  out:31  total:31
  examples.06-api-usage.example.run_prefact_example
    CC=11  in:1  out:28  total:29
  src.prefact.config_extended.models.ExtendedConfig.from_yaml
    CC=13  in:0  out:27  total:27
  src.prefact.benchmark.build_prefact_suite
    CC=3  in:1  out:26  total:27
  examples.run_examples.main
    CC=8  in:0  out:25  total:25
  src.prefact.rules.benchmark.benchmark_file
    CC=6  in:1  out:20  total:21
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule
    CC=1  in:0  out:20  total:20
  vscode-extension.src.extension.PrefactTreeProvider.activate
    CC=14  in:0  out:20  total:20
  examples.06-api-usage.example.batch_processing_example
    CC=6  in:1  out:19  total:20
  src.prefact.scanner._match_gitignore_pattern
    CC=12  in:0  out:18  total:18
  examples.sample-project.cli.main
    CC=2  in:0  out:18  total:18
  examples.06-api-usage.example.custom_rule_example
    CC=4  in:1  out:16  total:17
  src.prefact.rules.benchmark.print_benchmark_results
    CC=4  in:1  out:16  total:17
  benchmark_ram_optimization.run_benchmark
    CC=1  in:1  out:16  total:17
  src.prefact.benchmark.ScanProbe.run
    CC=5  in:0  out:17  total:17
  src.prefact.cli._build_config
    CC=7  in:3  out:14  total:17
  src.prefact.rules.migration.RuleMigrationManager.create_hybrid_rule
    CC=2  in:0  out:16  total:16
  src.prefact.performance.cache.cached_file_operation
    CC=1  in:0  out:16  total:16

MODULES:
  benchmark_ram_optimization  [4 funcs]
    benchmark_with_rampreload  CC=1  out:4
    benchmark_without_rampreload  CC=1  out:14
    create_test_files  CC=3  out:5
    run_benchmark  CC=1  out:16
  examples.01-individual-rules.relative-imports.after  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.relative-imports.before  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.string-concat.after  [1 funcs]
    format_data  CC=1  out:0
  examples.01-individual-rules.unused-imports.before  [1 funcs]
    process_data  CC=2  out:2
  examples.04-custom-rules.custom_rules.no_todo_rule  [1 funcs]
    __init__  CC=1  out:3
  examples.06-api-usage.example  [4 funcs]
    batch_processing_example  CC=6  out:19
    custom_rule_example  CC=4  out:16
    main  CC=4  out:11
    run_prefact_example  CC=11  out:28
  examples.run_examples  [2 funcs]
    find_examples  CC=4  out:5
    main  CC=8  out:25
  examples.sample-project.cli  [1 funcs]
    main  CC=2  out:18
  examples.sample-project.utils  [1 funcs]
    helper_function  CC=1  out:1
  src.prefact.autonomous.dependency_checker  [2 funcs]
    __init__  CC=1  out:2
    _query_pip_outdated  CC=6  out:10
  src.prefact.autonomous.docs_manager  [2 funcs]
    __init__  CC=1  out:2
    update_planfile  CC=27  out:41
  src.prefact.autonomous.project_scanner  [1 funcs]
    __init__  CC=2  out:2
  src.prefact.autonomous.todo_manager  [2 funcs]
    __init__  CC=1  out:2
    _generate_current_todos  CC=8  out:11
  src.prefact.benchmark  [4 funcs]
    run  CC=5  out:17
    _make_inprocess_probe  CC=1  out:10
    build_prefact_suite  CC=3  out:26
    main  CC=7  out:12
  src.prefact.cli  [5 funcs]
    _build_config  CC=7  out:14
    _output  CC=4  out:8
    check  CC=1  out:7
    fix  CC=2  out:8
    scan  CC=1  out:5
  src.prefact.config_extended.config  [2 funcs]
    __init__  CC=10  out:5
    to_dict  CC=1  out:3
  src.prefact.config_extended.models  [3 funcs]
    __init__  CC=6  out:4
    from_yaml  CC=13  out:27
    to_dict  CC=1  out:3
  src.prefact.config_extended.utils  [1 funcs]
    deep_merge  CC=5  out:5
  src.prefact.fixer  [1 funcs]
    __init__  CC=3  out:4
  src.prefact.git_hooks  [4 funcs]
    install_git_hooks  CC=4  out:9
    list_git_hooks  CC=4  out:6
    main  CC=8  out:12
    uninstall_git_hooks  CC=2  out:4
  src.prefact.logging.exceptions  [3 funcs]
    __init__  CC=1  out:2
    __init__  CC=2  out:3
    __init__  CC=1  out:2
  src.prefact.performance.cache  [9 funcs]
    __enter__  CC=1  out:1
    __exit__  CC=1  out:1
    cached_file_operation  CC=1  out:16
    cached_result  CC=1  out:14
    cleanup_cache  CC=2  out:1
    clear_cache  CC=5  out:5
    get_cache  CC=2  out:1
    get_cache_info  CC=4  out:7
    get_hash_cache  CC=2  out:1
  src.prefact.performance.cache_adapters  [1 funcs]
    set  CC=1  out:2
  src.prefact.performance.cache_state  [2 funcs]
    get_cache  CC=2  out:1
    initialize_cache  CC=2  out:8
  src.prefact.performance.parallel  [3 funcs]
    _get_enabled_rule_ids  CC=3  out:4
    _scan_with_process_pool  CC=5  out:9
    execute  CC=4  out:10
  src.prefact.plugins  [1 funcs]
    __init__  CC=1  out:4
  src.prefact.reporters.json_reporter  [2 funcs]
    dump  CC=2  out:3
    to_dict  CC=4  out:3
  src.prefact.rules.autoflake_based  [18 funcs]
    check_file  CC=3  out:4
    check_source  CC=1  out:4
    fix_file  CC=2  out:2
    fix_source  CC=2  out:6
    __init__  CC=1  out:3
    fix  CC=3  out:2
    scan_file  CC=1  out:2
    validate  CC=1  out:1
    __init__  CC=1  out:2
    build_autoflake_check_command  CC=3  out:3
  src.prefact.rules.benchmark  [4 funcs]
    benchmark_file  CC=6  out:20
    benchmark_project  CC=7  out:10
    main  CC=1  out:12
    print_benchmark_results  CC=4  out:16
  src.prefact.rules.composite_factory  [2 funcs]
    create_composite_rule  CC=1  out:20
    register_composite_rules  CC=4  out:7
  src.prefact.rules.composite_rules  [3 funcs]
    __init__  CC=1  out:4
    __init__  CC=1  out:3
    __init__  CC=1  out:4
  src.prefact.rules.import_linter_based  [4 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
  src.prefact.rules.importchecker_based  [3 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    _count_usage  CC=5  out:8
  src.prefact.rules.isort_based  [4 funcs]
    __init__  CC=1  out:3
    _find_import_blocks  CC=9  out:12
    __init__  CC=1  out:3
    __init__  CC=2  out:3
  src.prefact.rules.llm_generated_code  [1 funcs]
    __init__  CC=1  out:3
  src.prefact.rules.llm_hallucinations  [1 funcs]
    __init__  CC=1  out:3
  src.prefact.rules.magic_numbers  [2 funcs]
    __init__  CC=1  out:5
    _load_allowed_numbers  CC=1  out:3
  src.prefact.rules.migration  [3 funcs]
    _load_rules  CC=5  out:6
    compare_implementations  CC=5  out:8
    create_hybrid_rule  CC=2  out:16
  src.prefact.rules.mypy_based  [3 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    _analyze_return_types  CC=4  out:5
  src.prefact.rules.pylint_based  [3 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
  src.prefact.rules.registry  [6 funcs]
    get_all_rules  CC=3  out:1
    _initialize_built_in_rules  CC=1  out:31
    get_all_rules  CC=1  out:2
    get_lazy_registry  CC=2  out:1
    get_rule  CC=1  out:2
    register  CC=2  out:3
  src.prefact.rules.relative_imports  [5 funcs]
    __init__  CC=1  out:3
    _resolve  CC=9  out:9
    leave_ImportFrom  CC=6  out:9
    _module_to_str  CC=4  out:3
    _str_to_module  CC=2  out:4
  src.prefact.rules.sorted_imports  [2 funcs]
    scan_file  CC=7  out:8
    _sort_key  CC=6  out:5
  src.prefact.rules.string_concat  [3 funcs]
    scan_file  CC=5  out:6
    _flatten_add  CC=3  out:4
    _is_str_concat  CC=6  out:7
  src.prefact.rules.string_transformations  [2 funcs]
    __init__  CC=1  out:2
    _is_string_concat  CC=2  out:9
  src.prefact.rules.unimport_based  [4 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:2
    __init__  CC=1  out:2
    __init__  CC=1  out:3
  src.prefact.rules.unused_imports  [5 funcs]
    fix  CC=7  out:10
    scan_file  CC=6  out:8
    _collect_all_exports  CC=10  out:8
    _collect_imported_names  CC=8  out:4
    _collect_used_names  CC=5  out:7
  src.prefact.scanner  [4 funcs]
    __init__  CC=4  out:6
    collect_files  CC=6  out:7
    _load_gitignore  CC=6  out:5
    _match_gitignore_pattern  CC=12  out:18
  src.prefact.validator  [1 funcs]
    __init__  CC=3  out:4
  vscode-extension.src.extension  [33 funcs]
    config  CC=9  out:8
    diagnostic  CC=1  out:1
    diagnostics  CC=1  out:1
    diagnosticsByFile  CC=3  out:7
    entries  CC=1  out:1
    executablePath  CC=9  out:8
    fixFile  CC=3  out:7
    fixWorkspace  CC=3  out:5
    getSeverity  CC=5  out:0
    range  CC=1  out:1

EDGES:
  benchmark_ram_optimization.create_test_files → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.create_test_files
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_without_rampreload
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_with_rampreload
  examples.sample-project.cli.main → examples.01-individual-rules.unused-imports.before.process_data
  examples.run_examples.main → examples.run_examples.find_examples
  src.prefact.validator.Validator.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.fixer.Fixer.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  examples.01-individual-rules.relative-imports.before.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.before.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.04-custom-rules.custom_rules.no_todo_rule.NoTodoRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  examples.01-individual-rules.relative-imports.after.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.after.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  src.prefact.scanner._match_gitignore_pattern → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.scanner.Scanner.__init__ → src.prefact.scanner._load_gitignore
  src.prefact.scanner.Scanner.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.scanner.Scanner.collect_files → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.git_hooks.main → src.prefact.git_hooks.install_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.uninstall_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.list_git_hooks
  src.prefact.logging.exceptions.PprefactException.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.RuleError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.PluginError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.plugins.PluginManager.__init__ → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.performance.parallel.ParallelScanTask.execute → src.prefact.performance.cache_state.get_cache
  src.prefact.performance.parallel.ParallelEngine._scan_with_process_pool → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.performance.parallel.ParallelEngine._get_enabled_rule_ids → src.prefact.rules.registry.get_lazy_registry
  src.prefact.performance.cache.cached_result → src.prefact.performance.cache.get_cache
  src.prefact.performance.cache.cached_file_operation → src.prefact.performance.cache.get_hash_cache
  src.prefact.performance.cache.cached_file_operation → src.prefact.performance.cache.get_cache
  src.prefact.performance.cache.clear_cache → src.prefact.performance.cache.get_cache
  src.prefact.performance.cache.get_cache_info → src.prefact.performance.cache.get_cache
  src.prefact.performance.cache.CacheContext.__enter__ → src.prefact.performance.cache_state.initialize_cache
  src.prefact.performance.cache.CacheContext.__exit__ → src.prefact.performance.cache.cleanup_cache
  src.prefact.reporters.json_reporter.dump → src.prefact.reporters.json_reporter.to_dict
  src.prefact.autonomous.dependency_checker.DependencyChecker.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.autonomous.dependency_checker.DependencyChecker._query_pip_outdated → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.autonomous.docs_manager.DocsManager.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.rules.magic_numbers.MagicNumberRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.rules.magic_numbers.MagicNumberRule._load_allowed_numbers → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.rules.composite_factory.register_composite_rules → src.prefact.rules.registry.register
  src.prefact.rules.unused_imports.UnusedImports.scan_file → src.prefact.rules.unused_imports._collect_imported_names
  src.prefact.rules.unused_imports.UnusedImports.scan_file → src.prefact.rules.unused_imports._collect_used_names
  src.prefact.rules.unused_imports.UnusedImports.scan_file → src.prefact.rules.unused_imports._collect_all_exports
  src.prefact.rules.unused_imports.UnusedImports.fix → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.rules.unused_imports._collect_used_names → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.rules.unused_imports._collect_all_exports → src.prefact.performance.cache_adapters.ScanResultCache.set
  src.prefact.rules.registry.get_all_rules → src.prefact.rules.registry.get_lazy_registry
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Intent

Python code quality tool with LLM-aware rules, plugin system, and enterprise features
