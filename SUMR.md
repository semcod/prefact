# prefact

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Quality Pipeline (`pyqual.yaml`)](#quality-pipeline-pyqualyaml)
- [Dependencies](#dependencies)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `prefact`
- **version**: `0.0.0`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, testql(2), app.doql.less, pyqual.yaml, goal.yaml, .env.example, project/(6 analysis files)

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

## Call Graph

*184 nodes · 169 edges · 50 modules · CC̄=3.0*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `super` *(in vscode-extension.src.extension.PrefactTreeItem)* | 1 | 42 | 0 | **42** |
| `update_planfile` *(in src.prefact.autonomous.docs_manager.DocsManager)* | 27 ⚠ | 0 | 41 | **41** |
| `_initialize_built_in_rules` *(in src.prefact.rules.registry)* | 1 | 0 | 31 | **31** |
| `run_prefact_example` *(in examples.06-api-usage.example)* | 11 ⚠ | 1 | 28 | **29** |
| `build_prefact_suite` *(in src.prefact.benchmark)* | 3 | 1 | 26 | **27** |
| `from_yaml` *(in src.prefact.config_extended.models.ExtendedConfig)* | 13 ⚠ | 0 | 27 | **27** |
| `main` *(in examples.run_examples)* | 8 | 0 | 25 | **25** |
| `benchmark_file` *(in src.prefact.rules.benchmark)* | 6 | 1 | 20 | **21** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/prefact
# generated in 0.11s
# nodes: 184 | edges: 169 | modules: 50
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
  src.prefact.benchmark.build_prefact_suite
    CC=3  in:1  out:26  total:27
  src.prefact.config_extended.models.ExtendedConfig.from_yaml
    CC=13  in:0  out:27  total:27
  examples.run_examples.main
    CC=8  in:0  out:25  total:25
  src.prefact.rules.benchmark.benchmark_file
    CC=6  in:1  out:20  total:21
  vscode-extension.src.extension.PrefactTreeProvider.activate
    CC=14  in:0  out:20  total:20
  examples.06-api-usage.example.batch_processing_example
    CC=6  in:1  out:19  total:20
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule
    CC=1  in:0  out:20  total:20
  examples.sample-project.cli.main
    CC=2  in:0  out:18  total:18
  src.prefact.scanner._match_gitignore_pattern
    CC=12  in:0  out:18  total:18
  benchmark_ram_optimization.run_benchmark
    CC=1  in:1  out:16  total:17
  src.prefact.rules.benchmark.print_benchmark_results
    CC=4  in:1  out:16  total:17
  examples.06-api-usage.example.custom_rule_example
    CC=4  in:1  out:16  total:17
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
  examples.01-individual-rules.duplicate-imports.after  [1 funcs]
    process_data  CC=1  out:1
  examples.01-individual-rules.relative-imports.after  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.relative-imports.before  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.string-concat.after  [1 funcs]
    format_data  CC=1  out:0
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
  src.prefact.performance.cache  [10 funcs]
    set  CC=1  out:1
    __enter__  CC=1  out:1
    __exit__  CC=1  out:1
    cached_file_operation  CC=1  out:16
    cached_result  CC=1  out:14
    cleanup_cache  CC=2  out:1
    clear_cache  CC=5  out:5
    get_cache  CC=2  out:1
    get_cache_info  CC=4  out:7
    get_hash_cache  CC=2  out:1
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
  src.prefact.rules.pylint_based  [4 funcs]
    register  CC=1  out:0
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
  examples.run_examples.main → examples.run_examples.find_examples
  examples.01-individual-rules.relative-imports.after.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.after.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.relative-imports.before.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.before.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.sample-project.cli.main → examples.01-individual-rules.duplicate-imports.after.process_data
  examples.06-api-usage.example.main → examples.06-api-usage.example.run_prefact_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.custom_rule_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.batch_processing_example
  examples.04-custom-rules.custom_rules.no_todo_rule.NoTodoRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.validator.Validator.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.git_hooks.main → src.prefact.git_hooks.install_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.uninstall_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.list_git_hooks
  src.prefact.cli.scan → src.prefact.cli._build_config
  src.prefact.cli.scan → src.prefact.cli._output
  src.prefact.cli.fix → src.prefact.cli._build_config
  src.prefact.cli.fix → src.prefact.cli._output
  src.prefact.cli.check → src.prefact.cli._build_config
  src.prefact.cli.check → src.prefact.cli._output
  src.prefact.fixer.Fixer.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.scanner._match_gitignore_pattern → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.scanner.Scanner.__init__ → src.prefact.scanner._load_gitignore
  src.prefact.scanner.Scanner.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.scanner.Scanner.collect_files → src.prefact.performance.cache.Cache.set
  src.prefact.benchmark.ScanProbe.run → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.benchmark._make_inprocess_probe → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.benchmark.main → src.prefact.benchmark.build_prefact_suite
  src.prefact.logging.exceptions.PprefactException.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.RuleError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.PluginError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.plugins.PluginManager.__init__ → src.prefact.performance.cache.Cache.set
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
  src.prefact.autonomous.docs_manager.DocsManager.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile → src.prefact.performance.cache.Cache.set
  src.prefact.autonomous.todo_manager.TodoManager.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Cli (1)

**`CLI Command Tests`**

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/prefact
# generated in 0.11s
# nodes: 184 | edges: 169 | modules: 50
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
  src.prefact.benchmark.build_prefact_suite
    CC=3  in:1  out:26  total:27
  src.prefact.config_extended.models.ExtendedConfig.from_yaml
    CC=13  in:0  out:27  total:27
  examples.run_examples.main
    CC=8  in:0  out:25  total:25
  src.prefact.rules.benchmark.benchmark_file
    CC=6  in:1  out:20  total:21
  vscode-extension.src.extension.PrefactTreeProvider.activate
    CC=14  in:0  out:20  total:20
  examples.06-api-usage.example.batch_processing_example
    CC=6  in:1  out:19  total:20
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule
    CC=1  in:0  out:20  total:20
  examples.sample-project.cli.main
    CC=2  in:0  out:18  total:18
  src.prefact.scanner._match_gitignore_pattern
    CC=12  in:0  out:18  total:18
  benchmark_ram_optimization.run_benchmark
    CC=1  in:1  out:16  total:17
  src.prefact.rules.benchmark.print_benchmark_results
    CC=4  in:1  out:16  total:17
  examples.06-api-usage.example.custom_rule_example
    CC=4  in:1  out:16  total:17
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
  examples.01-individual-rules.duplicate-imports.after  [1 funcs]
    process_data  CC=1  out:1
  examples.01-individual-rules.relative-imports.after  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.relative-imports.before  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.string-concat.after  [1 funcs]
    format_data  CC=1  out:0
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
  src.prefact.performance.cache  [10 funcs]
    set  CC=1  out:1
    __enter__  CC=1  out:1
    __exit__  CC=1  out:1
    cached_file_operation  CC=1  out:16
    cached_result  CC=1  out:14
    cleanup_cache  CC=2  out:1
    clear_cache  CC=5  out:5
    get_cache  CC=2  out:1
    get_cache_info  CC=4  out:7
    get_hash_cache  CC=2  out:1
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
  src.prefact.rules.pylint_based  [4 funcs]
    register  CC=1  out:0
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
  examples.run_examples.main → examples.run_examples.find_examples
  examples.01-individual-rules.relative-imports.after.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.after.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.relative-imports.before.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.before.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.sample-project.cli.main → examples.01-individual-rules.duplicate-imports.after.process_data
  examples.06-api-usage.example.main → examples.06-api-usage.example.run_prefact_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.custom_rule_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.batch_processing_example
  examples.04-custom-rules.custom_rules.no_todo_rule.NoTodoRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.validator.Validator.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.git_hooks.main → src.prefact.git_hooks.install_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.uninstall_git_hooks
  src.prefact.git_hooks.main → src.prefact.git_hooks.list_git_hooks
  src.prefact.cli.scan → src.prefact.cli._build_config
  src.prefact.cli.scan → src.prefact.cli._output
  src.prefact.cli.fix → src.prefact.cli._build_config
  src.prefact.cli.fix → src.prefact.cli._output
  src.prefact.cli.check → src.prefact.cli._build_config
  src.prefact.cli.check → src.prefact.cli._output
  src.prefact.fixer.Fixer.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.scanner._match_gitignore_pattern → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.scanner.Scanner.__init__ → src.prefact.scanner._load_gitignore
  src.prefact.scanner.Scanner.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.scanner.Scanner.collect_files → src.prefact.performance.cache.Cache.set
  src.prefact.benchmark.ScanProbe.run → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.benchmark._make_inprocess_probe → vscode-extension.src.extension.PrefactDiagnosticsProvider.range
  src.prefact.benchmark.main → src.prefact.benchmark.build_prefact_suite
  src.prefact.logging.exceptions.PprefactException.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.RuleError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.logging.exceptions.PluginError.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.plugins.PluginManager.__init__ → src.prefact.performance.cache.Cache.set
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
  src.prefact.autonomous.docs_manager.DocsManager.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile → src.prefact.performance.cache.Cache.set
  src.prefact.autonomous.todo_manager.TodoManager.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 148f 21014L | python:106,yaml:28,shell:3,json:3,yml:2,cfg:1,toml:1,txt:1,typescript:1 | 2026-06-02
# generated in 0.04s
# CC̅=3.0 | critical:2/779 | dups:15 | cycles:0

HEALTH[5]:
  🔴 DUP   15 classes duplicated
  🔴 GOD   src/prefact/rules/isort_based.py = 519L, 4 classes, 23m, max CC=13
  🔴 GOD   src/prefact/rules/string_transformations.py = 501L, 6 classes, 27m, max CC=8
  🟡 CC    update_planfile CC=27 (limit:15)
  🟡 CC    run CC=15 (limit:15)

REFACTOR[4]:
  1. rm duplicates  (-15 dup classes)
  2. split src/prefact/rules/isort_based.py  (god module)
  3. split src/prefact/rules/string_transformations.py  (god module)
  4. split 2 high-CC methods  (CC>15)

PIPELINES[610]:
  [1] Src [main]: main → run_benchmark → create_test_files → range → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main → find_examples
      PURITY: 100% pure
  [3] Src [process_user]: process_user → helper_function
      PURITY: 100% pure
  [4] Src [__init__]: __init__
      PURITY: 100% pure
  [5] Src [process]: process → format_data
      PURITY: 100% pure
  [6] Src [process_user]: process_user → helper_function
      PURITY: 100% pure
  [7] Src [__init__]: __init__
      PURITY: 100% pure
  [8] Src [process]: process → format_data
      PURITY: 100% pure
  [9] Src [process]: process
      PURITY: 100% pure
  [10] Src [process]: process
      PURITY: 100% pure
  [11] Src [process]: process
      PURITY: 100% pure
  [12] Src [process]: process
      PURITY: 100% pure
  [13] Src [process_data]: process_data
      PURITY: 100% pure
  [14] Src [process_data]: process_data
      PURITY: 100% pure
  [15] Src [format_timestamp]: format_timestamp
      PURITY: 100% pure
  [16] Src [read_file]: read_file
      PURITY: 100% pure
  [17] Src [__init__]: __init__
      PURITY: 100% pure
  [18] Src [get_data]: get_data
      PURITY: 100% pure
  [19] Src [process_data]: process_data
      PURITY: 100% pure
  [20] Src [format_timestamp]: format_timestamp
      PURITY: 100% pure
  [21] Src [read_file]: read_file
      PURITY: 100% pure
  [22] Src [__init__]: __init__
      PURITY: 100% pure
  [23] Src [get_data]: get_data
      PURITY: 100% pure
  [24] Src [greet]: greet
      PURITY: 100% pure
  [25] Src [format_data]: format_data
      PURITY: 100% pure
  [26] Src [process_data]: process_data
      PURITY: 100% pure
  [27] Src [calculate]: calculate
      PURITY: 100% pure
  [28] Src [process_data]: process_data
      PURITY: 100% pure
  [29] Src [calculate]: calculate
      PURITY: 100% pure
  [30] Src [process_users]: process_users
      PURITY: 100% pure
  [31] Src [generate_report]: generate_report
      PURITY: 100% pure
  [32] Src [__init__]: __init__
      PURITY: 100% pure
  [33] Src [process]: process
      PURITY: 100% pure
  [34] Src [main]: main → process_data
      PURITY: 100% pure
  [35] Src [admin]: admin
      PURITY: 100% pure
  [36] Src [users]: users
      PURITY: 100% pure
  [37] Src [format_name]: format_name
      PURITY: 100% pure
  [38] Src [__init__]: __init__
      PURITY: 100% pure
  [39] Src [__post_init__]: __post_init__
      PURITY: 100% pure
  [40] Src [__post_init__]: __post_init__
      PURITY: 100% pure
  [41] Src [create_user]: create_user
      PURITY: 100% pure
  [42] Src [load_users_from_file]: load_users_from_file
      PURITY: 100% pure
  [43] Src [process_data]: process_data
      PURITY: 100% pure
  [44] Src [calculate_sum]: calculate_sum
      PURITY: 100% pure
  [45] Src [__init__]: __init__
      PURITY: 100% pure
  [46] Src [add_item]: add_item
      PURITY: 100% pure
  [47] Src [get_summary]: get_summary
      PURITY: 100% pure
  [48] Src [process_data]: process_data
      PURITY: 100% pure
  [49] Src [calculate_sum]: calculate_sum
      PURITY: 100% pure
  [50] Src [main]: main → run_prefact_example
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=3.1    ←in:0  →out:0  ×DUP
  │ !! isort_based                519L  4C   23m  CC=13     ←0
  │ !! string_transformations     501L  6C   27m  CC=8      ←0
  │ importchecker_based        499L  5C   24m  CC=14     ←0
  │ import_linter_based        480L  5C   24m  CC=8      ←0
  │ unimport_based             459L  5C   22m  CC=14     ←0
  │ todo_manager               430L  1C   15m  CC=13     ←0
  │ cli                        424L  0C   11m  CC=7      ←1
  │ pylint_based               424L  5C   22m  CC=6      ←1
  │ mypy_based                 416L  6C   22m  CC=9      ←0
  │ git_hooks                  383L  2C   17m  CC=8      ←0
  │ ruff_based                 359L  6C   19m  CC=4      ←0
  │ parallel                   357L  4C   23m  CC=7      ←0
  │ __init__                   330L  3C   17m  CC=10     ←0
  │ __init__                   312L  1C   19m  CC=7      ←0
  │ benchmark                  311L  1C    6m  CC=7      ←0
  │ autoflake_based            297L  3C   19m  CC=7      ←0
  │ project_scanner            296L  1C    7m  CC=11     ←0
  │ composite_rules            292L  3C   16m  CC=12     ←0
  │ !! docs_manager               285L  1C   10m  CC=27     ←0
  │ unused_imports             277L  1C   11m  CC=10     ←0
  │ registry                   273L  1C   13m  CC=8      ←8
  │ __init__                   256L  1C    8m  CC=3      ←0
  │ dependency_checker         237L  1C   11m  CC=10     ←0
  │ relative_imports           235L  2C    9m  CC=14     ←0
  │ migration                  234L  3C   10m  CC=5      ←0
  │ llm_hallucinations         220L  1C    9m  CC=8      ←0
  │ !! testql_manager             218L  1C    3m  CC=15     ←0
  │ llm_generated_code         196L  1C    9m  CC=7      ←0
  │ config                     177L  2C   13m  CC=5      ←0
  │ engine                     170L  1C    5m  CC=13     ←0
  │ scanner                    167L  1C    7m  CC=14     ←0
  │ generator                  161L  1C    3m  CC=12     ←0
  │ benchmark                  161L  0C    4m  CC=7      ←0
  │ strategies                 158L  4C   10m  CC=5      ←0
  │ logger                     153L  2C   15m  CC=3      ←0
  │ setup_manager              142L  1C    3m  CC=9      ←0
  │ config                     142L  1C    8m  CC=10     ←0
  │ magic_numbers              138L  1C    8m  CC=7      ←0
  │ cache_adapters             130L  4C   16m  CC=3      ←0  ×DUP
  │ composite_factory          121L  1C    2m  CC=4      ←0
  │ base                       102L  1C    7m  CC=3      ←0  ×DUP
  │ duplicate_imports          102L  1C    3m  CC=7      ←0
  │ models                      90L  6C    0m  CC=0.0    ←0
  │ models                      83L  1C    3m  CC=13     ←0
  │ ai_boilerplate              78L  1C    5m  CC=3      ←0
  │ _base                       73L  1C    3m  CC=10     ←0
  │ cache_state                 72L  0C    7m  CC=2      ←2
  │ string_concat               72L  1C    5m  CC=6      ←0
  │ sorted_imports              71L  1C    4m  CC=7      ←0
  │ console                     70L  0C    1m  CC=14     ←0
  │ validation                  70L  1C    6m  CC=6      ←0  ×DUP
  │ print_statements            62L  1C    3m  CC=9      ←0
  │ fixer                       58L  1C    3m  CC=7      ←0
  │ json_reporter               57L  0C    2m  CC=4      ←0
  │ scan                        53L  1C    5m  CC=1      ←0  ×DUP
  │ validators                  52L  1C    4m  CC=5      ←0  ×DUP
  │ globals                     51L  0C    3m  CC=2      ←0
  │ type_hints                  50L  1C    3m  CC=6      ←0
  │ wildcard_imports            49L  1C    3m  CC=7      ←0
  │ _ast_cache                  49L  0C    2m  CC=4      ←0
  │ __init__                    41L  0C    0m  CC=0.0    ←0
  │ rule                        39L  1C    4m  CC=1      ←0  ×DUP
  │ exceptions                  35L  4C    3m  CC=2      ←0
  │ validator                   32L  1C    2m  CC=4      ←0
  │ config                      32L  1C    4m  CC=1      ←0  ×DUP
  │ hash                        31L  1C    3m  CC=3      ←0  ×DUP
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ formatters                  26L  1C    1m  CC=2      ←0
  │ defaults                    21L  0C    0m  CC=0.0    ←0
  │ constants                   15L  0C    0m  CC=0.0    ←0
  │ levels                      13L  1C    0m  CC=0.0    ←0
  │ __init__                    13L  0C    0m  CC=0.0    ←0
  │ builtin                     13L  0C    0m  CC=0.0    ←0
  │ __init__                    12L  0C    0m  CC=0.0    ←0
  │ utils                       11L  0C    1m  CC=5      ←1
  │ _base                        6L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ cache                        0L  6C   37m  CC=5      ←9  ×DUP
  │
  vscode-extension/               CC̄=2.9    ←in:0  →out:0
  │ extension.ts               437L  5C   48m  CC=14     ←27
  │ package.json               187L  0C    0m  CC=0.0    ←0
  │ .eslintrc.json              19L  0C    0m  CC=0.0    ←0
  │ tsconfig.json               16L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=2.6    ←in:0  →out:0
  │ !! planfile.yaml             2048L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  512L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             337L  0C    0m  CC=0.0    ←0
  │ Makefile                   293L  0C    0m  CC=0.0    ←0
  │ benchmark_ram_optimization   235L  0C    5m  CC=7      ←0
  │ Taskfile.yml               186L  0C    0m  CC=0.0    ←0
  │ koru.yaml                  133L  0C    0m  CC=0.0    ←0
  │ pyqual.yaml                124L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                87L  0C    0m  CC=0.0    ←0
  │ redsl.yaml                  72L  0C    0m  CC=0.0    ←0
  │ project.sh                  47L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_report.toon.yaml    25L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_plan.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ setup.cfg                    4L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.7    ←in:0  →out:0  ×DUP
  │ prefact.yaml               344L  0C    0m  CC=0.0    ←0
  │ prefact.yaml               281L  0C    0m  CC=0.0    ←0
  │ generate_examples          232L  0C    0m  CC=0.0    ←0
  │ example                    198L  0C    4m  CC=11     ←0
  │ run_all.sh                 143L  0C    3m  CC=0.0    ←0
  │ run_examples               137L  0C    3m  CC=8      ←0
  │ prefact.yaml               129L  0C    0m  CC=0.0    ←0
  │ prefact.yaml               123L  0C    0m  CC=0.0    ←0
  │ no_todo_rule               112L  2C    7m  CC=6      ←0
  │ .gitlab-ci.yml             108L  0C    0m  CC=0.0    ←0
  │ prefact.yaml               101L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                87L  0C    0m  CC=0.0    ←0
  │ cli                         62L  0C    3m  CC=2      ←0
  │ models                      59L  2C    5m  CC=2      ←0
  │ messy_module                54L  1C    4m  CC=2      ←0
  │ after                       41L  1C    6m  CC=2      ←0  ×DUP
  │ before                      41L  1C    6m  CC=2      ←0  ×DUP
  │ utils                       40L  1C    5m  CC=2      ←3
  │ core                        36L  1C    5m  CC=2      ←0
  │ prefact.yaml                35L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                35L  0C    0m  CC=0.0    ←0
  │ after                       26L  1C    3m  CC=1      ←0
  │ before                      26L  1C    3m  CC=1      ←0
  │ prefact.yaml                26L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                26L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ after                       19L  1C    3m  CC=1      ←0
  │ before                      19L  1C    3m  CC=1      ←0
  │ prefact.yaml                18L  0C    0m  CC=0.0    ←0
  │ sample_code                 17L  0C    2m  CC=2      ←0
  │ after                       15L  0C    2m  CC=1      ←0
  │ before                      15L  0C    2m  CC=1      ←0
  │ after                       13L  0C    1m  CC=1      ←0
  │ before                      13L  0C    1m  CC=1      ←0
  │ after                       13L  0C    2m  CC=1      ←2
  │ before                      13L  0C    2m  CC=1      ←0
  │ requirements.txt            13L  0C    0m  CC=0.0    ←0
  │ after                        8L  0C    1m  CC=1      ←1
  │ before                       8L  0C    1m  CC=1      ←0
  │ after                        6L  0C    1m  CC=1      ←0
  │ before                       6L  0C    1m  CC=1      ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=0.0    ←in:0  →out:0
  │ koru-interface-registry.yaml   270L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     src/prefact/performance/cache.py          0L

COUPLING:
                                        vscode-extension.src                   src.prefact  examples.01-individual-rules       examples.sample-project    benchmark_ram_optimization      examples.04-custom-rules
          vscode-extension.src                            ──                           ←46                                                                                        ←1                            ←1  hub
                   src.prefact                            46                            ──                                                                                                                          !! fan-out
  examples.01-individual-rules                                                                                        ──                             2                                                            
       examples.sample-project                                                                                         1                            ──                                                            
    benchmark_ram_optimization                             1                                                                                                                      ──                              
      examples.04-custom-rules                             1                                                                                                                                                    ──
  CYCLES: none
  HUB: vscode-extension.src/ (fan-in=48)
  SMELL: src.prefact/ fan-out=46 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 46 groups | 100f 14449L | 2026-06-02

SUMMARY:
  files_scanned: 100
  total_lines:   14449
  dup_groups:    46
  dup_fragments: 120
  saved_lines:   434
  scan_ms:       2293

HOTSPOTS[7] (files with most duplication):
  src/prefact/rules/unimport_based.py  dup=84L  groups=4  frags=7  (0.6%)
  src/prefact/rules/import_linter_based.py  dup=62L  groups=4  frags=9  (0.4%)
  src/prefact/rules/composite_rules.py  dup=54L  groups=3  frags=6  (0.4%)
  src/prefact/performance/cache.py  dup=46L  groups=4  frags=8  (0.3%)
  src/prefact/rules/pylint_based.py  dup=45L  groups=2  frags=5  (0.3%)
  src/prefact/rules/mypy_based.py  dup=44L  groups=4  frags=7  (0.3%)
  examples/04-custom-rules/custom_rules/no_todo_rule.py  dup=28L  groups=2  frags=4  (0.2%)

DUPLICATES[46] (ranked by impact):
  [2f0b5f60dff6d87a] ! EXAC  fix  L=5 N=14 saved=65 sim=1.00
      examples/04-custom-rules/custom_rules/no_todo_rule.py:46-50  (fix)
      examples/04-custom-rules/custom_rules/no_todo_rule.py:98-102  (fix)
      src/prefact/rules/ai_boilerplate.py:69-73  (fix)
      src/prefact/rules/import_linter_based.py:172-177  (fix)
      src/prefact/rules/import_linter_based.py:327-331  (fix)
      src/prefact/rules/importchecker_based.py:378-382  (fix)
      src/prefact/rules/importchecker_based.py:490-494  (fix)
      src/prefact/rules/llm_generated_code.py:187-191  (fix)
      src/prefact/rules/llm_hallucinations.py:203-207  (fix)
      src/prefact/rules/magic_numbers.py:129-133  (fix)
      src/prefact/rules/mypy_based.py:155-160  (fix)
      src/prefact/rules/mypy_based.py:225-229  (fix)
      src/prefact/rules/ruff_based.py:112-116  (fix)
      src/prefact/rules/ruff_based.py:351-356  (fix)
  [b65e5e76ebaa28e7] ! STRU  fix  L=22 N=3 saved=44 sim=1.00
      src/prefact/rules/unimport_based.py:181-202  (fix)
      src/prefact/rules/unimport_based.py:278-299  (fix)
      src/prefact/rules/unimport_based.py:411-432  (fix)
  [61838ef52572f18b]   STRU  get_cache  L=5 N=5 saved=20 sim=1.00
      src/prefact/performance/cache.py:268-272  (get_cache)
      src/prefact/performance/cache.py:275-279  (get_scan_cache)
      src/prefact/performance/cache.py:282-286  (get_config_cache)
      src/prefact/performance/cache.py:289-293  (get_rule_cache)
      src/prefact/performance/cache.py:296-300  (get_hash_cache)
  [8a88275822553ad5]   STRU  validate  L=18 N=2 saved=18 sim=1.00
      src/prefact/rules/pylint_based.py:162-179  (validate)
      src/prefact/rules/pylint_based.py:234-251  (validate)
  [02b90c71278bdfe9]   EXAC  fix  L=4 N=5 saved=16 sim=1.00
      src/prefact/rules/print_statements.py:56-59  (fix)
      src/prefact/rules/sorted_imports.py:65-68  (fix)
      src/prefact/rules/string_concat.py:66-69  (fix)
      src/prefact/rules/type_hints.py:44-47  (fix)
      src/prefact/rules/wildcard_imports.py:43-46  (fix)
  [00e3ba6791c8b05d]   STRU  get_cache  L=4 N=5 saved=16 sim=1.00
      src/prefact/performance/cache_state.py:34-37  (get_cache)
      src/prefact/performance/cache_state.py:40-43  (get_scan_cache)
      src/prefact/performance/cache_state.py:46-49  (get_config_cache)
      src/prefact/performance/cache_state.py:52-55  (get_rule_cache)
      src/prefact/performance/cache_state.py:58-61  (get_hash_cache)
  [c9d89c232e41d853]   EXAC  validate  L=13 N=2 saved=13 sim=1.00
      src/prefact/rules/composite_rules.py:203-215  (validate)
      src/prefact/rules/composite_rules.py:280-292  (validate)
  [a613d4975a07742c]   EXAC  fix  L=6 N=3 saved=12 sim=1.00
      src/prefact/rules/composite_factory.py:74-79  (fix)
      src/prefact/rules/composite_rules.py:101-108  (fix)
      src/prefact/rules/composite_rules.py:194-201  (fix)
  [90331f4920e98fd7]   STRU  validate  L=4 N=4 saved=12 sim=1.00
      src/prefact/rules/ai_boilerplate.py:75-78  (validate)
      src/prefact/rules/llm_generated_code.py:193-196  (validate)
      src/prefact/rules/magic_numbers.py:135-138  (validate)
      src/prefact/rules/unimport_based.py:370-373  (validate)
  [02b48514187ed5cf]   EXAC  to_dict  L=11 N=2 saved=11 sim=1.00
      src/prefact/config_extended/config.py:132-142  (to_dict)
      src/prefact/config_extended/models.py:73-83  (to_dict)
  [414281b035028eb5]   EXAC  validate  L=11 N=2 saved=11 sim=1.00
      src/prefact/rules/mypy_based.py:406-416  (validate)
      src/prefact/rules/string_transformations.py:361-371  (validate)
  [07201fe17c618549]   STRU  validate  L=11 N=2 saved=11 sim=1.00
      src/prefact/rules/import_linter_based.py:333-343  (validate)
      src/prefact/rules/import_linter_based.py:424-434  (validate)
  [0012aae792aa3fda]   EXAC  get_hash  L=10 N=2 saved=10 sim=1.00
      src/prefact/performance/cache.py:222-231  (get_hash)
      src/prefact/performance/cache_adapters.py:119-125  (get_hash)
  [3229e7f5682165ed]   EXAC  validate  L=10 N=2 saved=10 sim=1.00
      src/prefact/rules/duplicate_imports.py:93-102  (validate)
      src/prefact/rules/unused_imports.py:48-57  (validate)
  [45b23d72e656b184]   STRU  validate  L=10 N=2 saved=10 sim=1.00
      src/prefact/rules/import_linter_based.py:179-188  (validate)
      src/prefact/rules/import_linter_based.py:271-280  (validate)
  [637c7e586b5ac6f6]   EXAC  validate  L=9 N=2 saved=9 sim=1.00
      examples/04-custom-rules/custom_rules/no_todo_rule.py:52-60  (validate)
      examples/04-custom-rules/custom_rules/no_todo_rule.py:104-112  (validate)
  [ea7177ce519c189d]   EXAC  _get_relative_file_path  L=9 N=2 saved=9 sim=1.00
      src/prefact/autonomous/docs_manager.py:277-285  (_get_relative_file_path)
      src/prefact/autonomous/todo_manager.py:224-232  (_get_relative_file_path)
  [8edfe22670ef44e1]   EXAC  process_data  L=8 N=2 saved=8 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:7-14  (process_data)
      examples/01-individual-rules/unused-imports/before.py:7-14  (process_data)
  [7db25b6baa69639e]   EXAC  scan_file  L=4 N=3 saved=8 sim=1.00
      src/prefact/rules/composite_factory.py:69-72  (scan_file)
      src/prefact/rules/composite_rules.py:94-99  (scan_file)
      src/prefact/rules/composite_rules.py:187-192  (scan_file)
  [cb356507d857797f]   EXAC  validate  L=8 N=2 saved=8 sim=1.00
      src/prefact/rules/importchecker_based.py:263-270  (validate)
      src/prefact/rules/unimport_based.py:301-308  (validate)
  [618cd0669047c527]   EXAC  _load_mypy_config  L=8 N=2 saved=8 sim=1.00
      src/prefact/rules/mypy_based.py:108-115  (_load_mypy_config)
      src/prefact/rules/mypy_based.py:192-199  (_load_mypy_config)
  [94f4bfa96465f169]   EXAC  calculate_sum  L=7 N=2 saved=7 sim=1.00
      examples/03-output-formats/sample_code.py:11-17  (calculate_sum)
      examples/sample-project/core.py:13-19  (calculate_sum)
  [53efaf6dde1d343f]   EXAC  process_data  L=6 N=2 saved=6 sim=1.00
      examples/01-individual-rules/print-statements/after.py:4-9  (process_data)
      examples/01-individual-rules/print-statements/before.py:4-9  (process_data)
  [52878821d84977d2]   EXAC  __init__  L=6 N=2 saved=6 sim=1.00
      src/prefact/fixer.py:12-17  (__init__)
      src/prefact/validator.py:11-16  (__init__)
  [55804bb29d6c13a1]   EXAC  set_hash  L=6 N=2 saved=6 sim=1.00
      src/prefact/performance/cache.py:233-238  (set_hash)
      src/prefact/performance/cache_adapters.py:127-130  (set_hash)
  [50fd28cabdf165f6]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      src/prefact/rules/import_linter_based.py:126-128  (__init__)
      src/prefact/rules/import_linter_based.py:198-200  (__init__)
      src/prefact/rules/import_linter_based.py:290-292  (__init__)
  [17783b0f3fb50cdb]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      src/prefact/rules/pylint_based.py:88-90  (__init__)
      src/prefact/rules/pylint_based.py:189-191  (__init__)
      src/prefact/rules/pylint_based.py:273-275  (__init__)
  [16897491a14d9018]   STRU  get_performance_monitor  L=6 N=2 saved=6 sim=1.00
      src/prefact/performance/parallel.py:352-357  (get_performance_monitor)
      src/prefact/rules/registry.py:169-174  (get_lazy_registry)
  [772c77ab0afca55b]   EXAC  process_user  L=5 N=2 saved=5 sim=1.00
      examples/01-individual-rules/relative-imports/after.py:8-12  (process_user)
      examples/01-individual-rules/relative-imports/before.py:8-12  (process_user)
  [a6697fd3227f7e47]   EXAC  get_key  L=5 N=2 saved=5 sim=1.00
      src/prefact/performance/cache.py:189-193  (get_key)
      src/prefact/performance/cache_adapters.py:87-90  (get_key)
  [8c3b4878cda6c2a9]   EXAC  calculate  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/print-statements/after.py:12-15  (calculate)
      examples/01-individual-rules/print-statements/before.py:12-15  (calculate)
  [d783de7edd92287c]   EXAC  read_file  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:22-25  (read_file)
      examples/01-individual-rules/unused-imports/before.py:22-25  (read_file)
  [641667a4d5a7609f]   EXAC  process  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/wildcard-imports/after.py:10-13  (process)
      examples/01-individual-rules/wildcard-imports/before.py:10-13  (process)
  [c522b15451457d34]   STRU  format_data  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/string-concat/before.py:10-13  (format_data)
      examples/sample-project/utils.py:23-26  (helper_function)
  [ced691da4eea9c77]   EXAC  process_data  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/duplicate-imports/after.py:6-8  (process_data)
      examples/01-individual-rules/duplicate-imports/before.py:6-8  (process_data)
  [d45b7d0f286fc4fd]   EXAC  add  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:4-6  (add)
      examples/01-individual-rules/missing-return-type/before.py:4-6  (add)
  [9baec9052aef7a75]   EXAC  get_user  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:9-11  (get_user)
      examples/01-individual-rules/missing-return-type/before.py:9-11  (get_user)
  [47c667d00e4443d6]   EXAC  process  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:17-19  (process)
      examples/01-individual-rules/missing-return-type/before.py:17-19  (process)
  [6979933d3c997c8c]   EXAC  process  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/sorted-imports/after.py:4-6  (process)
      examples/01-individual-rules/sorted-imports/before.py:4-6  (process)
  [95b3fc542348f5d0]   EXAC  format_timestamp  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:17-19  (format_timestamp)
      examples/01-individual-rules/unused-imports/before.py:17-19  (format_timestamp)
  [bd51f88e17729153]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:31-33  (__init__)
      examples/01-individual-rules/unused-imports/before.py:31-33  (__init__)
  [77829e64b838d82d]   EXAC  add_data  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:35-37  (add_data)
      examples/01-individual-rules/unused-imports/before.py:35-37  (add_data)
  [8793c3565817b439]   EXAC  get_data  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:39-41  (get_data)
      examples/01-individual-rules/unused-imports/before.py:39-41  (get_data)
  [89f4308d864bd180]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      src/prefact/rules/importchecker_based.py:100-102  (__init__)
      src/prefact/rules/importchecker_based.py:281-283  (__init__)
  [53e9ef8f2a396333]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      src/prefact/rules/mypy_based.py:104-106  (__init__)
      src/prefact/rules/mypy_based.py:188-190  (__init__)
  [abd7b44abf133457]   STRU  __init__  L=3 N=2 saved=3 sim=1.00
      src/prefact/rules/unimport_based.py:223-225  (__init__)
      src/prefact/rules/unimport_based.py:319-321  (__init__)

REFACTOR[46] (ranked by priority):
  [1] ○ extract_function   → utils/fix.py
      WHY: 14 occurrences of 5-line block across 9 files — saves 65 lines
      FILES: examples/04-custom-rules/custom_rules/no_todo_rule.py, src/prefact/rules/ai_boilerplate.py, src/prefact/rules/import_linter_based.py, src/prefact/rules/importchecker_based.py, src/prefact/rules/llm_generated_code.py +4 more
  [2] ○ extract_function   → src/prefact/rules/utils/fix.py
      WHY: 3 occurrences of 22-line block across 1 files — saves 44 lines
      FILES: src/prefact/rules/unimport_based.py
  [3] ○ extract_function   → src/prefact/performance/utils/get_cache.py
      WHY: 5 occurrences of 5-line block across 1 files — saves 20 lines
      FILES: src/prefact/performance/cache.py
  [4] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 18-line block across 1 files — saves 18 lines
      FILES: src/prefact/rules/pylint_based.py
  [5] ○ extract_function   → src/prefact/rules/utils/fix.py
      WHY: 5 occurrences of 4-line block across 5 files — saves 16 lines
      FILES: src/prefact/rules/print_statements.py, src/prefact/rules/sorted_imports.py, src/prefact/rules/string_concat.py, src/prefact/rules/type_hints.py, src/prefact/rules/wildcard_imports.py
  [6] ○ extract_function   → src/prefact/performance/utils/get_cache.py
      WHY: 5 occurrences of 4-line block across 1 files — saves 16 lines
      FILES: src/prefact/performance/cache_state.py
  [7] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 13-line block across 1 files — saves 13 lines
      FILES: src/prefact/rules/composite_rules.py
  [8] ○ extract_function   → src/prefact/rules/utils/fix.py
      WHY: 3 occurrences of 6-line block across 2 files — saves 12 lines
      FILES: src/prefact/rules/composite_factory.py, src/prefact/rules/composite_rules.py
  [9] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 4 occurrences of 4-line block across 4 files — saves 12 lines
      FILES: src/prefact/rules/ai_boilerplate.py, src/prefact/rules/llm_generated_code.py, src/prefact/rules/magic_numbers.py, src/prefact/rules/unimport_based.py
  [10] ○ extract_class      → src/prefact/config_extended/utils/to_dict.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: src/prefact/config_extended/config.py, src/prefact/config_extended/models.py
  [11] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: src/prefact/rules/mypy_based.py, src/prefact/rules/string_transformations.py
  [12] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: src/prefact/rules/import_linter_based.py
  [13] ○ extract_class      → src/prefact/performance/utils/get_hash.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: src/prefact/performance/cache.py, src/prefact/performance/cache_adapters.py
  [14] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: src/prefact/rules/duplicate_imports.py, src/prefact/rules/unused_imports.py
  [15] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: src/prefact/rules/import_linter_based.py
  [16] ○ extract_function   → examples/04-custom-rules/custom_rules/utils/validate.py
      WHY: 2 occurrences of 9-line block across 1 files — saves 9 lines
      FILES: examples/04-custom-rules/custom_rules/no_todo_rule.py
  [17] ○ extract_function   → src/prefact/autonomous/utils/_get_relative_file_path.py
      WHY: 2 occurrences of 9-line block across 2 files — saves 9 lines
      FILES: src/prefact/autonomous/docs_manager.py, src/prefact/autonomous/todo_manager.py
  [18] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/process_data.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [19] ○ extract_function   → src/prefact/rules/utils/scan_file.py
      WHY: 3 occurrences of 4-line block across 2 files — saves 8 lines
      FILES: src/prefact/rules/composite_factory.py, src/prefact/rules/composite_rules.py
  [20] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: src/prefact/rules/importchecker_based.py, src/prefact/rules/unimport_based.py
  [21] ○ extract_function   → src/prefact/rules/utils/_load_mypy_config.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: src/prefact/rules/mypy_based.py
  [22] ○ extract_function   → examples/utils/calculate_sum.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: examples/03-output-formats/sample_code.py, examples/sample-project/core.py
  [23] ○ extract_function   → examples/01-individual-rules/print-statements/utils/process_data.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: examples/01-individual-rules/print-statements/after.py, examples/01-individual-rules/print-statements/before.py
  [24] ○ extract_function   → src/prefact/utils/__init__.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/fixer.py, src/prefact/validator.py
  [25] ○ extract_class      → src/prefact/performance/utils/set_hash.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/performance/cache.py, src/prefact/performance/cache_adapters.py
  [26] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/prefact/rules/import_linter_based.py
  [27] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/prefact/rules/pylint_based.py
  [28] ○ extract_function   → src/prefact/utils/get_performance_monitor.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/performance/parallel.py, src/prefact/rules/registry.py
  [29] ○ extract_function   → examples/01-individual-rules/relative-imports/utils/process_user.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: examples/01-individual-rules/relative-imports/after.py, examples/01-individual-rules/relative-imports/before.py
  [30] ○ extract_class      → src/prefact/performance/utils/get_key.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: src/prefact/performance/cache.py, src/prefact/performance/cache_adapters.py
  [31] ○ extract_function   → examples/01-individual-rules/print-statements/utils/calculate.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/print-statements/after.py, examples/01-individual-rules/print-statements/before.py
  [32] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/read_file.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [33] ○ extract_function   → examples/01-individual-rules/wildcard-imports/utils/process.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/wildcard-imports/after.py, examples/01-individual-rules/wildcard-imports/before.py
  [34] ○ extract_function   → examples/utils/format_data.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/string-concat/before.py, examples/sample-project/utils.py
  [35] ○ extract_function   → examples/01-individual-rules/duplicate-imports/utils/process_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/duplicate-imports/after.py, examples/01-individual-rules/duplicate-imports/before.py
  [36] ○ extract_function   → examples/01-individual-rules/missing-return-type/utils/add.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [37] ○ extract_function   → examples/01-individual-rules/missing-return-type/utils/get_user.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [38] ○ extract_class      → examples/01-individual-rules/missing-return-type/utils/process.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [39] ○ extract_function   → examples/01-individual-rules/sorted-imports/utils/process.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/sorted-imports/after.py, examples/01-individual-rules/sorted-imports/before.py
  [40] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/format_timestamp.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [41] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [42] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/add_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [43] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/get_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [44] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/prefact/rules/importchecker_based.py
  [45] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/prefact/rules/mypy_based.py
  [46] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/prefact/rules/unimport_based.py

QUICK_WINS[28] (low risk, high savings — do first):
  [1] extract_function   saved=65L  → utils/fix.py
      FILES: no_todo_rule.py, ai_boilerplate.py, import_linter_based.py +6
  [2] extract_function   saved=44L  → src/prefact/rules/utils/fix.py
      FILES: unimport_based.py
  [3] extract_function   saved=20L  → src/prefact/performance/utils/get_cache.py
      FILES: cache.py
  [4] extract_function   saved=18L  → src/prefact/rules/utils/validate.py
      FILES: pylint_based.py
  [5] extract_function   saved=16L  → src/prefact/rules/utils/fix.py
      FILES: print_statements.py, sorted_imports.py, string_concat.py +2
  [6] extract_function   saved=16L  → src/prefact/performance/utils/get_cache.py
      FILES: cache_state.py
  [7] extract_function   saved=13L  → src/prefact/rules/utils/validate.py
      FILES: composite_rules.py
  [8] extract_function   saved=12L  → src/prefact/rules/utils/fix.py
      FILES: composite_factory.py, composite_rules.py
  [9] extract_function   saved=12L  → src/prefact/rules/utils/validate.py
      FILES: ai_boilerplate.py, llm_generated_code.py, magic_numbers.py +1
  [10] extract_class      saved=11L  → src/prefact/config_extended/utils/to_dict.py
      FILES: config.py, models.py

DEPENDENCY_RISK[1] (duplicates spanning multiple packages):
  fix  packages=2  files=9
      examples/04-custom-rules/custom_rules/no_todo_rule.py
      src/prefact/rules/ai_boilerplate.py
      src/prefact/rules/import_linter_based.py
      src/prefact/rules/importchecker_based.py
      +5 more

EFFORT_ESTIMATE (total ≈ 16.6h):
  hard   fix                                 saved=65L  ~260min
  medium fix                                 saved=44L  ~88min
  medium get_cache                           saved=20L  ~40min
  medium validate                            saved=18L  ~36min
  medium fix                                 saved=16L  ~32min
  medium get_cache                           saved=16L  ~32min
  easy   validate                            saved=13L  ~26min
  easy   fix                                 saved=12L  ~24min
  easy   validate                            saved=12L  ~24min
  easy   to_dict                             saved=11L  ~22min
  ... +36 more (~414min)

METRICS-TARGET:
  dup_groups:  46 → 0
  saved_lines: 434 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 700 func | 69f | 2026-06-02
# generated in 0.00s

NEXT[5] (ranked by impact):
  [1] !! SPLIT           src/prefact/rules/isort_based.py
      WHY: 519L, 4 classes, max CC=13
      EFFORT: ~4h  IMPACT: 6747

  [2] !! SPLIT-FUNC      DocsManager.update_planfile  CC=27  fan=23
      WHY: CC=27 exceeds 15
      EFFORT: ~1h  IMPACT: 621

  [3] !  SPLIT-FUNC      TestQLManager.run  CC=15  fan=12
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 180

  [4] !! SPLIT           planfile.yaml
      WHY: 2048L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0

  [5] !! SPLIT           goal.yaml
      WHY: 512L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting planfile.yaml may break 0 import paths
  ⚠ Splitting src/prefact/rules/isort_based.py may break 23 import paths
  ⚠ Splitting goal.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          3.1 → ≤2.2
  max-CC:      27 → ≤13
  god-modules: 4 → 0
  high-CC(≥15): 2 → ≤1
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=3.1 → now CC̄=3.1
```

### Validation (`project/validation.toon.yaml`)

```toon markpact:analysis path=project/validation.toon.yaml
# vallm batch | 192f | 122✓ 2⚠ 21✗ | 2026-04-09

SUMMARY:
  scanned: 192  passed: 122 (63.5%)  warnings: 2  errors: 21  unsupported: 49

WARNINGS[2]{path,score}:
  vscode-extension/src/extension.ts,0.83
    issues[1]{rule,severity,message,line}:
      js.import.resolvable,warning,Module 'vscode' not found,1
  src/prefact/config_extended/generator.py,0.97
    issues[1]{rule,severity,message,line}:
      complexity.lizard_length,warning,generate_extended_config: 111 lines exceeds limit 100,17

ERRORS[21]{path,score}:
  .pyqual/benchmark.json,0.00
    issues[1]{rule,severity,message,line}:
      syntax.tree_sitter,error,tree-sitter found 34 parse error(s) in json,
  examples/01-individual-rules/relative-imports/after.py,0.57
    issues[8]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'mypackage.models' not found,3
      python.import.resolvable,error,Module 'mypackage.utils' not found,4
      python.import.resolvable,error,Module 'mypackage.config' not found,5
      python.import.resolvable,error,Module 'mypackage.models' not found,6
      python.import.resolvable,error,Module 'mypackage.utils' not found,7
      python.import.resolvable,error,Module 'mypackage' not found,8
      python.import.resolvable,error,Module 'mypackage.core' not found,22
      python.import.resolvable,error,Module 'mypackage.utils' not found,26
  examples/01-individual-rules/relative-imports/before.py,0.57
    issues[7]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'models' not found,3
      python.import.relative.resolvable,error,Relative import 'utils' not found,4
      python.import.relative.resolvable,error,Relative import 'config' not found,5
      python.import.relative.resolvable,error,Relative import 'models' not found,6
      python.import.relative.resolvable,error,Relative import 'utils' not found,7
      python.import.relative.resolvable,error,Relative import 'core' not found,22
      python.import.relative.resolvable,error,Relative import 'utils' not found,26
  examples/sample-project/core.py,0.57
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'utils' not found,3
  examples/sample-project/cli.py,0.74
    issues[3]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'core' not found,5
      python.import.resolvable,error,Module 'models' not found,6
      python.import.resolvable,error,Module 'utils' not found,7
  examples/01-individual-rules/wildcard-imports/after.py,0.79
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'utils' not found,4
      python.import.relative.resolvable,error,Relative import 'models' not found,5
  examples/01-individual-rules/wildcard-imports/before.py,0.79
    issues[2]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'utils' not found,4
      python.import.relative.resolvable,error,Relative import 'models' not found,5
  examples/02-multiple-rules/messy_module.py,0.82
    issues[5]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'utils' not found,7
      python.import.relative.resolvable,error,Relative import 'models' not found,8
      python.import.relative.resolvable,error,Relative import 'utils' not found,11
      python.import.relative.resolvable,error,Relative import 'models' not found,12
      python.import.relative.resolvable,error,Relative import 'config' not found,58
  examples/03-output-formats/sample_code.py,0.83
    issues[2]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'utils' not found,6
      python.import.relative.resolvable,error,Relative import 'models' not found,7
  tests/test_config.py,0.89
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,7
  src/prefact/performance/cache_state.py,0.91
    issues[1]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'cache_core' not found,10
  tests/test_dependency_checker.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,9
  tests/test_engine.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,8
  tests/test_unused_imports.py,0.93
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,8
  examples/01-individual-rules/sorted-imports/after.py,0.94
    issues[1]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'local_module' not found,3
  examples/01-individual-rules/sorted-imports/before.py,0.94
    issues[1]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'local_module' not found,3
  src/prefact/performance/cache_adapters.py,0.94
    issues[1]{rule,severity,message,line}:
      python.import.relative.resolvable,error,Relative import 'cache_core' not found,12
  tests/test_relative_imports.py,0.94
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,8
  src/prefact/autonomous/dependency_checker.py,0.95
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'tomli' not found,89
  tests/test_rules.py,0.96
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,8
  tests/test_integrations.py,0.97
    issues[1]{rule,severity,message,line}:
      python.import.resolvable,error,Module 'pytest' not found,17

UNSUPPORTED[4]{bucket,count}:
  *.md,24
  *.txt,3
  *.yml,1
  other,21
```

## Intent

Python code quality tool with LLM-aware rules, plugin system, and enterprise features
