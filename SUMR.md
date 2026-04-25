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
- **python_requires**: `>=3.8`
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
  runtime: "ast-decompiler>=0.7.0, click>=8.0.0, libcst>=0.4.0, pyyaml>=6.0, rich>=12.0.0, tomli>=2.0.0; python_version<'3.11', goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
  dev: "pytest>=7.0.0, pytest-cov>=4.0.0, pytest-asyncio>=0.21.0, black>=23.0.0, isort>=5.10.0, mypy>=1.0.0, ruff>=0.5.0, pre-commit>=3.0.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
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
  python_version: >=3.8;
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
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
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
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Call Graph

*229 nodes · 229 edges · 65 modules · CC̄=0.7*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in Taskfile)* | 0 | 133 | 0 | **133** |
| `super` *(in vscode-extension.src.extension.PrefactTreeItem)* | 1 | 42 | 0 | **42** |
| `_initialize_built_in_rules` *(in src.prefact.rules.registry)* | 1 | 0 | 31 | **31** |
| `run_prefact_example` *(in examples.06-api-usage.example)* | 11 ⚠ | 1 | 28 | **29** |
| `build_prefact_suite` *(in src.prefact.benchmark)* | 3 | 1 | 26 | **27** |
| `update_planfile` *(in src.prefact.autonomous.docs_manager.DocsManager)* | 11 ⚠ | 0 | 25 | **25** |
| `main` *(in examples.run_examples)* | 8 | 0 | 25 | **25** |
| `from_yaml` *(in src.prefact.config_extended.models.ExtendedConfig)* | 13 ⚠ | 0 | 24 | **24** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/prefact
# nodes: 229 | edges: 229 | modules: 65
# CC̄=0.7

HUBS[20]:
  Taskfile.print
    CC=0  in:133  out:0  total:133
  vscode-extension.src.extension.PrefactTreeItem.super
    CC=1  in:42  out:0  total:42
  src.prefact.rules.registry._initialize_built_in_rules
    CC=1  in:0  out:31  total:31
  examples.06-api-usage.example.run_prefact_example
    CC=11  in:1  out:28  total:29
  src.prefact.benchmark.build_prefact_suite
    CC=3  in:1  out:26  total:27
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile
    CC=11  in:0  out:25  total:25
  examples.run_examples.main
    CC=8  in:0  out:25  total:25
  src.prefact.config_extended.models.ExtendedConfig.from_yaml
    CC=13  in:0  out:24  total:24
  project.map.toon.open
    CC=0  in:22  out:0  total:22
  benchmark_ram_optimization.main
    CC=7  in:0  out:22  total:22
  src.prefact.rules.benchmark.benchmark_file
    CC=6  in:1  out:21  total:22
  examples.06-api-usage.example.batch_processing_example
    CC=6  in:1  out:19  total:20
  src.prefact.scanner._match_gitignore_pattern
    CC=12  in:2  out:18  total:20
  vscode-extension.src.extension.PrefactTreeProvider.activate
    CC=14  in:0  out:20  total:20
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule
    CC=1  in:0  out:20  total:20
  examples.sample-project.cli.main
    CC=2  in:0  out:18  total:18
  src.prefact.benchmark.ScanProbe.run
    CC=5  in:0  out:17  total:17
  src.prefact.cli._build_config
    CC=7  in:3  out:14  total:17
  examples.06-api-usage.example.custom_rule_example
    CC=4  in:1  out:16  total:17
  benchmark_ram_optimization.run_benchmark
    CC=1  in:1  out:16  total:17

MODULES:
  Taskfile  [1 funcs]
    print  CC=0  out:0
  benchmark_ram_optimization  [5 funcs]
    benchmark_with_rampreload  CC=1  out:4
    benchmark_without_rampreload  CC=1  out:14
    create_test_files  CC=3  out:5
    main  CC=7  out:22
    run_benchmark  CC=1  out:16
  examples.01-individual-rules.duplicate-imports.after  [1 funcs]
    process_data  CC=1  out:1
  examples.01-individual-rules.print-statements.after  [2 funcs]
    calculate  CC=1  out:1
    process_data  CC=1  out:2
  examples.01-individual-rules.print-statements.before  [2 funcs]
    calculate  CC=1  out:1
    process_data  CC=1  out:2
  examples.01-individual-rules.relative-imports.after  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.relative-imports.before  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.string-concat.after  [1 funcs]
    format_data  CC=1  out:0
  examples.01-individual-rules.unused-imports.after  [1 funcs]
    read_file  CC=1  out:2
  examples.01-individual-rules.unused-imports.before  [1 funcs]
    read_file  CC=1  out:2
  examples.02-multiple-rules.messy_module  [4 funcs]
    __init__  CC=1  out:1
    process  CC=1  out:4
    generate_report  CC=1  out:6
    process_users  CC=2  out:3
  examples.03-output-formats.sample_code  [2 funcs]
    calculate_sum  CC=2  out:2
    process_data  CC=1  out:2
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
  examples.sample-project.cli  [3 funcs]
    admin  CC=1  out:2
    main  CC=2  out:18
    users  CC=2  out:7
  examples.sample-project.core  [3 funcs]
    __init__  CC=1  out:1
    calculate_sum  CC=2  out:2
    process_data  CC=1  out:2
  examples.sample-project.models  [3 funcs]
    __post_init__  CC=2  out:3
    __post_init__  CC=2  out:3
    load_users_from_file  CC=2  out:4
  examples.sample-project.utils  [4 funcs]
    __init__  CC=1  out:1
    format_name  CC=1  out:1
    helper_function  CC=1  out:1
    validate_email  CC=2  out:3
  project.map.toon  [1 funcs]
    open  CC=0  out:0
  src.prefact.autonomous.dependency_checker  [2 funcs]
    __init__  CC=1  out:2
    _query_pip_outdated  CC=6  out:10
  src.prefact.autonomous.docs_manager  [2 funcs]
    __init__  CC=1  out:2
    update_planfile  CC=11  out:25
  src.prefact.autonomous.project_scanner  [1 funcs]
    __init__  CC=2  out:2
  src.prefact.autonomous.setup_manager  [1 funcs]
    create_refact_config  CC=2  out:7
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
  src.prefact.config_extended.generator  [1 funcs]
    save_config  CC=1  out:2
  src.prefact.config_extended.models  [3 funcs]
    __init__  CC=6  out:4
    from_yaml  CC=13  out:24
    to_dict  CC=1  out:3
  src.prefact.config_extended.utils  [1 funcs]
    deep_merge  CC=5  out:5
  src.prefact.engine  [1 funcs]
    _preload_sources  CC=9  out:10
  src.prefact.fixer  [1 funcs]
    __init__  CC=3  out:4
  src.prefact.git_hooks  [8 funcs]
    _find_git_dir  CC=2  out:5
    _install_hook  CC=2  out:9
    uninstall_hooks  CC=6  out:8
    install  CC=3  out:11
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
  src.prefact.performance.parallel  [4 funcs]
    _get_enabled_rule_ids  CC=3  out:4
    _scan_with_process_pool  CC=5  out:9
    _calculate_file_hash  CC=2  out:4
    execute  CC=4  out:10
  src.prefact.plugins  [4 funcs]
    __init__  CC=1  out:4
    _discover_entry_point_plugins  CC=6  out:7
    _discover_local_plugins  CC=4  out:14
    load_plugin  CC=10  out:15
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
    benchmark_file  CC=6  out:21
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
  src.prefact.rules.import_linter_based  [6 funcs]
    __init__  CC=1  out:3
    create_config  CC=5  out:4
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    generate_import_linter_config  CC=7  out:7
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
  src.prefact.rules.migration  [4 funcs]
    _load_rules  CC=5  out:6
    compare_implementations  CC=5  out:8
    create_hybrid_rule  CC=2  out:16
    add_ruff_config_to_prefact_yaml  CC=3  out:4
  src.prefact.rules.mypy_based  [3 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    _analyze_return_types  CC=4  out:5
  src.prefact.rules.pylint_based  [4 funcs]
    register  CC=1  out:0
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
  src.prefact.rules.registry  [7 funcs]
    _load_module  CC=3  out:2
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
  src.prefact.rules.ruff_based  [1 funcs]
    fix_source  CC=2  out:7
  src.prefact.rules.sorted_imports  [2 funcs]
    scan_file  CC=7  out:8
    _sort_key  CC=6  out:5
  src.prefact.rules.strategies  [1 funcs]
    scan  CC=4  out:6
  src.prefact.rules.string_concat  [3 funcs]
    scan_file  CC=5  out:6
    _flatten_add  CC=3  out:4
    _is_str_concat  CC=6  out:7
  src.prefact.rules.string_transformations  [2 funcs]
    __init__  CC=1  out:2
    _is_string_concat  CC=2  out:9
  src.prefact.rules.unimport_based  [5 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:2
    fix_source  CC=2  out:7
    __init__  CC=1  out:2
    __init__  CC=1  out:3
  src.prefact.rules.unused_imports  [5 funcs]
    fix  CC=7  out:10
    scan_file  CC=6  out:8
    _collect_all_exports  CC=10  out:8
    _collect_imported_names  CC=8  out:4
    _collect_used_names  CC=5  out:7
  src.prefact.scanner  [5 funcs]
    __init__  CC=4  out:6
    _excluded  CC=12  out:5
    collect_files  CC=6  out:6
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
  benchmark_ram_optimization.run_benchmark → Taskfile.print
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.create_test_files
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_without_rampreload
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_with_rampreload
  benchmark_ram_optimization.main → Taskfile.print
  examples.run_examples.main → examples.run_examples.find_examples
  examples.01-individual-rules.relative-imports.after.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.after.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.relative-imports.before.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.before.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.unused-imports.after.read_file → project.map.toon.open
  examples.01-individual-rules.unused-imports.before.read_file → project.map.toon.open
  examples.01-individual-rules.print-statements.after.process_data → Taskfile.print
  examples.01-individual-rules.print-statements.after.calculate → Taskfile.print
  examples.01-individual-rules.print-statements.before.process_data → Taskfile.print
  examples.01-individual-rules.print-statements.before.calculate → Taskfile.print
  examples.02-multiple-rules.messy_module.process_users → Taskfile.print
  examples.02-multiple-rules.messy_module.generate_report → Taskfile.print
  examples.02-multiple-rules.messy_module.DataProcessor.__init__ → Taskfile.print
  examples.02-multiple-rules.messy_module.DataProcessor.process → Taskfile.print
  examples.sample-project.cli.main → Taskfile.print
  examples.sample-project.cli.main → examples.01-individual-rules.duplicate-imports.after.process_data
  examples.sample-project.cli.admin → Taskfile.print
  examples.sample-project.cli.users → Taskfile.print
  examples.sample-project.utils.format_name → Taskfile.print
  examples.sample-project.utils.validate_email → Taskfile.print
  examples.sample-project.utils.UtilClass.__init__ → Taskfile.print
  examples.sample-project.models.User.__post_init__ → Taskfile.print
  examples.sample-project.models.Post.__post_init__ → Taskfile.print
  examples.sample-project.models.load_users_from_file → project.map.toon.open
  examples.sample-project.core.process_data → Taskfile.print
  examples.sample-project.core.calculate_sum → Taskfile.print
  examples.sample-project.core.DataProcessor.__init__ → Taskfile.print
  examples.03-output-formats.sample_code.process_data → Taskfile.print
  examples.03-output-formats.sample_code.calculate_sum → Taskfile.print
  examples.06-api-usage.example.run_prefact_example → Taskfile.print
  examples.06-api-usage.example.custom_rule_example → Taskfile.print
  examples.06-api-usage.example.batch_processing_example → Taskfile.print
  examples.06-api-usage.example.main → examples.06-api-usage.example.run_prefact_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.custom_rule_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.batch_processing_example
  examples.04-custom-rules.custom_rules.no_todo_rule.NoTodoRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.engine.RefactoringEngine._preload_sources → Taskfile.print
  src.prefact.validator.Validator.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.git_hooks.GitHooks._find_git_dir → project.map.toon.open
  src.prefact.git_hooks.GitHooks._install_hook → Taskfile.print
  src.prefact.git_hooks.GitHooks.uninstall_hooks → Taskfile.print
  src.prefact.git_hooks.PreCommitConfig.install → Taskfile.print
  src.prefact.git_hooks.install_git_hooks → Taskfile.print
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
# nodes: 229 | edges: 229 | modules: 65
# CC̄=0.7

HUBS[20]:
  Taskfile.print
    CC=0  in:133  out:0  total:133
  vscode-extension.src.extension.PrefactTreeItem.super
    CC=1  in:42  out:0  total:42
  src.prefact.rules.registry._initialize_built_in_rules
    CC=1  in:0  out:31  total:31
  examples.06-api-usage.example.run_prefact_example
    CC=11  in:1  out:28  total:29
  src.prefact.benchmark.build_prefact_suite
    CC=3  in:1  out:26  total:27
  src.prefact.autonomous.docs_manager.DocsManager.update_planfile
    CC=11  in:0  out:25  total:25
  examples.run_examples.main
    CC=8  in:0  out:25  total:25
  src.prefact.config_extended.models.ExtendedConfig.from_yaml
    CC=13  in:0  out:24  total:24
  project.map.toon.open
    CC=0  in:22  out:0  total:22
  benchmark_ram_optimization.main
    CC=7  in:0  out:22  total:22
  src.prefact.rules.benchmark.benchmark_file
    CC=6  in:1  out:21  total:22
  examples.06-api-usage.example.batch_processing_example
    CC=6  in:1  out:19  total:20
  src.prefact.scanner._match_gitignore_pattern
    CC=12  in:2  out:18  total:20
  vscode-extension.src.extension.PrefactTreeProvider.activate
    CC=14  in:0  out:20  total:20
  src.prefact.rules.composite_factory.CompositeRuleFactory.create_composite_rule
    CC=1  in:0  out:20  total:20
  examples.sample-project.cli.main
    CC=2  in:0  out:18  total:18
  src.prefact.benchmark.ScanProbe.run
    CC=5  in:0  out:17  total:17
  src.prefact.cli._build_config
    CC=7  in:3  out:14  total:17
  examples.06-api-usage.example.custom_rule_example
    CC=4  in:1  out:16  total:17
  benchmark_ram_optimization.run_benchmark
    CC=1  in:1  out:16  total:17

MODULES:
  Taskfile  [1 funcs]
    print  CC=0  out:0
  benchmark_ram_optimization  [5 funcs]
    benchmark_with_rampreload  CC=1  out:4
    benchmark_without_rampreload  CC=1  out:14
    create_test_files  CC=3  out:5
    main  CC=7  out:22
    run_benchmark  CC=1  out:16
  examples.01-individual-rules.duplicate-imports.after  [1 funcs]
    process_data  CC=1  out:1
  examples.01-individual-rules.print-statements.after  [2 funcs]
    calculate  CC=1  out:1
    process_data  CC=1  out:2
  examples.01-individual-rules.print-statements.before  [2 funcs]
    calculate  CC=1  out:1
    process_data  CC=1  out:2
  examples.01-individual-rules.relative-imports.after  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.relative-imports.before  [2 funcs]
    process  CC=1  out:1
    process_user  CC=1  out:2
  examples.01-individual-rules.string-concat.after  [1 funcs]
    format_data  CC=1  out:0
  examples.01-individual-rules.unused-imports.after  [1 funcs]
    read_file  CC=1  out:2
  examples.01-individual-rules.unused-imports.before  [1 funcs]
    read_file  CC=1  out:2
  examples.02-multiple-rules.messy_module  [4 funcs]
    __init__  CC=1  out:1
    process  CC=1  out:4
    generate_report  CC=1  out:6
    process_users  CC=2  out:3
  examples.03-output-formats.sample_code  [2 funcs]
    calculate_sum  CC=2  out:2
    process_data  CC=1  out:2
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
  examples.sample-project.cli  [3 funcs]
    admin  CC=1  out:2
    main  CC=2  out:18
    users  CC=2  out:7
  examples.sample-project.core  [3 funcs]
    __init__  CC=1  out:1
    calculate_sum  CC=2  out:2
    process_data  CC=1  out:2
  examples.sample-project.models  [3 funcs]
    __post_init__  CC=2  out:3
    __post_init__  CC=2  out:3
    load_users_from_file  CC=2  out:4
  examples.sample-project.utils  [4 funcs]
    __init__  CC=1  out:1
    format_name  CC=1  out:1
    helper_function  CC=1  out:1
    validate_email  CC=2  out:3
  project.map.toon  [1 funcs]
    open  CC=0  out:0
  src.prefact.autonomous.dependency_checker  [2 funcs]
    __init__  CC=1  out:2
    _query_pip_outdated  CC=6  out:10
  src.prefact.autonomous.docs_manager  [2 funcs]
    __init__  CC=1  out:2
    update_planfile  CC=11  out:25
  src.prefact.autonomous.project_scanner  [1 funcs]
    __init__  CC=2  out:2
  src.prefact.autonomous.setup_manager  [1 funcs]
    create_refact_config  CC=2  out:7
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
  src.prefact.config_extended.generator  [1 funcs]
    save_config  CC=1  out:2
  src.prefact.config_extended.models  [3 funcs]
    __init__  CC=6  out:4
    from_yaml  CC=13  out:24
    to_dict  CC=1  out:3
  src.prefact.config_extended.utils  [1 funcs]
    deep_merge  CC=5  out:5
  src.prefact.engine  [1 funcs]
    _preload_sources  CC=9  out:10
  src.prefact.fixer  [1 funcs]
    __init__  CC=3  out:4
  src.prefact.git_hooks  [8 funcs]
    _find_git_dir  CC=2  out:5
    _install_hook  CC=2  out:9
    uninstall_hooks  CC=6  out:8
    install  CC=3  out:11
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
  src.prefact.performance.parallel  [4 funcs]
    _get_enabled_rule_ids  CC=3  out:4
    _scan_with_process_pool  CC=5  out:9
    _calculate_file_hash  CC=2  out:4
    execute  CC=4  out:10
  src.prefact.plugins  [4 funcs]
    __init__  CC=1  out:4
    _discover_entry_point_plugins  CC=6  out:7
    _discover_local_plugins  CC=4  out:14
    load_plugin  CC=10  out:15
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
    benchmark_file  CC=6  out:21
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
  src.prefact.rules.import_linter_based  [6 funcs]
    __init__  CC=1  out:3
    create_config  CC=5  out:4
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    generate_import_linter_config  CC=7  out:7
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
  src.prefact.rules.migration  [4 funcs]
    _load_rules  CC=5  out:6
    compare_implementations  CC=5  out:8
    create_hybrid_rule  CC=2  out:16
    add_ruff_config_to_prefact_yaml  CC=3  out:4
  src.prefact.rules.mypy_based  [3 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    _analyze_return_types  CC=4  out:5
  src.prefact.rules.pylint_based  [4 funcs]
    register  CC=1  out:0
    __init__  CC=1  out:3
    __init__  CC=1  out:3
    __init__  CC=1  out:3
  src.prefact.rules.registry  [7 funcs]
    _load_module  CC=3  out:2
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
  src.prefact.rules.ruff_based  [1 funcs]
    fix_source  CC=2  out:7
  src.prefact.rules.sorted_imports  [2 funcs]
    scan_file  CC=7  out:8
    _sort_key  CC=6  out:5
  src.prefact.rules.strategies  [1 funcs]
    scan  CC=4  out:6
  src.prefact.rules.string_concat  [3 funcs]
    scan_file  CC=5  out:6
    _flatten_add  CC=3  out:4
    _is_str_concat  CC=6  out:7
  src.prefact.rules.string_transformations  [2 funcs]
    __init__  CC=1  out:2
    _is_string_concat  CC=2  out:9
  src.prefact.rules.unimport_based  [5 funcs]
    __init__  CC=1  out:3
    __init__  CC=1  out:2
    fix_source  CC=2  out:7
    __init__  CC=1  out:2
    __init__  CC=1  out:3
  src.prefact.rules.unused_imports  [5 funcs]
    fix  CC=7  out:10
    scan_file  CC=6  out:8
    _collect_all_exports  CC=10  out:8
    _collect_imported_names  CC=8  out:4
    _collect_used_names  CC=5  out:7
  src.prefact.scanner  [5 funcs]
    __init__  CC=4  out:6
    _excluded  CC=12  out:5
    collect_files  CC=6  out:6
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
  benchmark_ram_optimization.run_benchmark → Taskfile.print
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.create_test_files
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_without_rampreload
  benchmark_ram_optimization.run_benchmark → benchmark_ram_optimization.benchmark_with_rampreload
  benchmark_ram_optimization.main → Taskfile.print
  examples.run_examples.main → examples.run_examples.find_examples
  examples.01-individual-rules.relative-imports.after.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.after.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.relative-imports.before.process_user → examples.sample-project.utils.helper_function
  examples.01-individual-rules.relative-imports.before.Processor.process → examples.01-individual-rules.string-concat.after.format_data
  examples.01-individual-rules.unused-imports.after.read_file → project.map.toon.open
  examples.01-individual-rules.unused-imports.before.read_file → project.map.toon.open
  examples.01-individual-rules.print-statements.after.process_data → Taskfile.print
  examples.01-individual-rules.print-statements.after.calculate → Taskfile.print
  examples.01-individual-rules.print-statements.before.process_data → Taskfile.print
  examples.01-individual-rules.print-statements.before.calculate → Taskfile.print
  examples.02-multiple-rules.messy_module.process_users → Taskfile.print
  examples.02-multiple-rules.messy_module.generate_report → Taskfile.print
  examples.02-multiple-rules.messy_module.DataProcessor.__init__ → Taskfile.print
  examples.02-multiple-rules.messy_module.DataProcessor.process → Taskfile.print
  examples.sample-project.cli.main → Taskfile.print
  examples.sample-project.cli.main → examples.01-individual-rules.duplicate-imports.after.process_data
  examples.sample-project.cli.admin → Taskfile.print
  examples.sample-project.cli.users → Taskfile.print
  examples.sample-project.utils.format_name → Taskfile.print
  examples.sample-project.utils.validate_email → Taskfile.print
  examples.sample-project.utils.UtilClass.__init__ → Taskfile.print
  examples.sample-project.models.User.__post_init__ → Taskfile.print
  examples.sample-project.models.Post.__post_init__ → Taskfile.print
  examples.sample-project.models.load_users_from_file → project.map.toon.open
  examples.sample-project.core.process_data → Taskfile.print
  examples.sample-project.core.calculate_sum → Taskfile.print
  examples.sample-project.core.DataProcessor.__init__ → Taskfile.print
  examples.03-output-formats.sample_code.process_data → Taskfile.print
  examples.03-output-formats.sample_code.calculate_sum → Taskfile.print
  examples.06-api-usage.example.run_prefact_example → Taskfile.print
  examples.06-api-usage.example.custom_rule_example → Taskfile.print
  examples.06-api-usage.example.batch_processing_example → Taskfile.print
  examples.06-api-usage.example.main → examples.06-api-usage.example.run_prefact_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.custom_rule_example
  examples.06-api-usage.example.main → examples.06-api-usage.example.batch_processing_example
  examples.04-custom-rules.custom_rules.no_todo_rule.NoTodoRule.__init__ → vscode-extension.src.extension.PrefactTreeItem.super
  src.prefact.engine.RefactoringEngine._preload_sources → Taskfile.print
  src.prefact.validator.Validator.__init__ → src.prefact.rules.registry.LazyRuleRegistry.get_all_rules
  src.prefact.git_hooks.GitHooks._find_git_dir → project.map.toon.open
  src.prefact.git_hooks.GitHooks._install_hook → Taskfile.print
  src.prefact.git_hooks.GitHooks.uninstall_hooks → Taskfile.print
  src.prefact.git_hooks.PreCommitConfig.install → Taskfile.print
  src.prefact.git_hooks.install_git_hooks → Taskfile.print
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 154f 120629L | python:104,yaml:37,json:3,shell:2,txt:2,cfg:1,toml:1,yml:1,typescript:1 | 2026-04-25
# CC̄=0.7 | critical:1/3484 | dups:15 | cycles:0

HEALTH[2]:
  🔴 DUP   15 classes duplicated
  🟡 CC    scan_file CC=15 (limit:15)

REFACTOR[2]:
  1. rm duplicates  (-15 dup classes)
  2. split 1 high-CC methods  (CC>15)

PIPELINES[596]:
  [1] Src [main]: main → print
      PURITY: 100% pure
  [2] Src [main]: main → find_examples
      PURITY: 100% pure
  [3] Src [process_user]: process_user → helper_function
      PURITY: 100% pure
  [4] Src [__init__]: __init__
      PURITY: 100% pure
  [5] Src [process]: process → format_data
      PURITY: 100% pure

LAYERS:
  src/                            CC̄=3.1    ←in:0  →out:0  ×DUP
  │ string_transformations     495L  6C   27m  CC=8      ←0
  │ importchecker_based        490L  5C   24m  CC=14     ←0
  │ isort_based                470L  4C   23m  CC=13     ←0
  │ unimport_based             456L  5C   22m  CC=14     ←0
  │ import_linter_based        451L  5C   24m  CC=8      ←0
  │ cache                      439L  6C   37m  CC=5      ←9  ×DUP
  │ mypy_based                 398L  6C   22m  CC=9      ←0
  │ pylint_based               396L  5C   22m  CC=6      ←1
  │ git_hooks                  383L  2C   17m  CC=8      ←0
  │ todo_manager               368L  1C   15m  CC=13     ←0
  │ parallel                   353L  4C   23m  CC=7      ←0
  │ __init__                   320L  3C   17m  CC=10     ←0
  │ ruff_based                 311L  6C   19m  CC=4      ←0
  │ benchmark                  293L  1C    6m  CC=7      ←0
  │ autoflake_based            277L  3C   19m  CC=7      ←0
  │ composite_rules            276L  3C   16m  CC=12     ←0
  │ registry                   255L  1C   13m  CC=8      ←8
  │ cli                        247L  0C   10m  CC=7      ←1
  │ project_scanner            244L  1C    7m  CC=11     ←0
  │ dependency_checker         237L  1C   11m  CC=10     ←0
  │ __init__                   236L  1C    7m  CC=1      ←0
  │ unused_imports             232L  1C   11m  CC=10     ←0
  │ migration                  232L  3C   10m  CC=5      ←0
  │ relative_imports           219L  2C    9m  CC=14     ←0
  │ __init__                   218L  1C   17m  CC=7      ←0
  │ llm_hallucinations         214L  1C    9m  CC=8      ←0
  │ config                     192L  2C   13m  CC=5      ←3
  │ llm_generated_code         191L  1C    9m  CC=7      ←0
  │ docs_manager               189L  1C    7m  CC=11     ←0
  │ generator                  171L  1C    3m  CC=12     ←1
  │ benchmark                  161L  0C    4m  CC=7      ←0
  │ engine                     158L  1C    5m  CC=13     ←0
  │ scanner                    153L  1C    7m  CC=12     ←0
  │ strategies                 152L  4C   10m  CC=5      ←0
  │ !! magic_numbers              138L  1C    6m  CC=15     ←0
  │ config                     128L  1C    8m  CC=10     ←4
  │ setup_manager              120L  1C    3m  CC=9      ←0
  │ composite_factory          119L  1C    2m  CC=4      ←0
  │ cache_adapters             106L  4C   16m  CC=3      ←0  ×DUP
  │ base                        99L  1C    7m  CC=3      ←0  ×DUP
  │ models                      91L  6C    0m  CC=0.0    ←0
  │ duplicate_imports           80L  1C    3m  CC=11     ←0
  │ ai_boilerplate              77L  1C    5m  CC=3      ←0
  │ cache_state                 74L  0C    7m  CC=2      ←2
  │ _base                       66L  1C    3m  CC=10     ←0
  │ string_concat               66L  1C    5m  CC=6      ←0
  │ logger                      65L  2C   15m  CC=3      ←0
  │ validation                  65L  1C    6m  CC=6      ←1  ×DUP
  │ console                     64L  0C    1m  CC=14     ←0
  │ sorted_imports              63L  1C    4m  CC=7      ←0
  │ scan                        59L  1C    5m  CC=1      ←0  ×DUP
  │ print_statements            58L  1C    3m  CC=9      ←0
  │ json_reporter               57L  0C    2m  CC=4      ←1
  │ _ast_cache                  51L  0C    2m  CC=4      ←0
  │ globals                     50L  0C    3m  CC=2      ←0
  │ fixer                       49L  1C    3m  CC=7      ←0
  │ rule                        47L  1C    4m  CC=1      ←0  ×DUP
  │ type_hints                  46L  1C    3m  CC=6      ←0
  │ wildcard_imports            45L  1C    3m  CC=7      ←0
  │ validators                  44L  1C    4m  CC=5      ←1  ×DUP
  │ __init__                    41L  0C    0m  CC=0.0    ←0
  │ models                      38L  1C    3m  CC=13     ←0
  │ config                      31L  1C    4m  CC=1      ←0  ×DUP
  │ hash                        31L  1C    3m  CC=3      ←0  ×DUP
  │ validator                   29L  1C    2m  CC=4      ←0
  │ exceptions                  24L  4C    3m  CC=2      ←0
  │ formatters                  24L  1C    1m  CC=2      ←0
  │ constants                   24L  0C    0m  CC=0.0    ←0
  │ levels                      13L  1C    0m  CC=0.0    ←0
  │ builtin                     13L  0C    0m  CC=0.0    ←0
  │ __init__                    13L  0C    0m  CC=0.0    ←0
  │ utils                       10L  0C    1m  CC=5      ←1
  │ _base                        6L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  vscode-extension/               CC̄=2.9    ←in:0  →out:0
  │ extension.ts               437L  5C   48m  CC=14     ←27
  │ package.json               187L  0C    0m  CC=0.0    ←0
  │ .eslintrc.json              19L  0C    0m  CC=0.0    ←0
  │ tsconfig.json               16L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=2.2    ←in:0  →out:0
  │ !! planfile.yaml             2126L  0C    0m  CC=0.0    ←0
  │ goal.yaml                  480L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             337L  0C    0m  CC=0.0    ←0
  │ benchmark_ram_optimization   222L  0C    5m  CC=7      ←0
  │ Taskfile.yml               186L  0C    1m  CC=0.0    ←16
  │ pyqual.yaml                124L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                84L  0C    0m  CC=0.0    ←0
  │ redsl.yaml                  72L  0C    0m  CC=0.0    ←0
  │ project.sh                  46L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_report.toon.yaml    25L  0C    0m  CC=0.0    ←0
  │ redsl_refactor_plan.toon.yaml    23L  0C    0m  CC=0.0    ←0
  │ setup.cfg                    4L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=1.7    ←in:0  →out:0  ×DUP
  │ prefact.yaml               344L  0C    0m  CC=0.0    ←0
  │ prefact.yaml               281L  0C    0m  CC=0.0    ←0
  │ generate_examples          233L  0C    0m  CC=0.0    ←0
  │ example                    185L  0C    4m  CC=11     ←0
  │ run_all.sh                 143L  0C    3m  CC=0.0    ←0
  │ prefact.yaml               129L  0C    0m  CC=0.0    ←0
  │ prefact.yaml               123L  0C    0m  CC=0.0    ←0
  │ run_examples               119L  0C    3m  CC=8      ←0
  │ no_todo_rule               108L  2C    7m  CC=6      ←0
  │ prefact.yaml               101L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                87L  0C    0m  CC=0.0    ←0
  │ messy_module                67L  1C    4m  CC=2      ←0
  │ cli                         65L  0C    3m  CC=2      ←0
  │ models                      62L  2C    5m  CC=2      ←0
  │ after                       41L  1C    6m  CC=2      ←0  ×DUP
  │ before                      41L  1C    6m  CC=2      ←0  ×DUP
  │ utils                       40L  1C    5m  CC=2      ←3
  │ core                        36L  1C    5m  CC=2      ←0
  │ prefact.yaml                35L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                35L  0C    0m  CC=0.0    ←0
  │ after                       27L  1C    3m  CC=1      ←0
  │ before                      27L  1C    3m  CC=1      ←0
  │ prefact.yaml                26L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                26L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                25L  0C    0m  CC=0.0    ←0
  │ sample_code                 21L  0C    2m  CC=2      ←0
  │ prefact.yaml                18L  0C    0m  CC=0.0    ←0
  │ after                       16L  1C    3m  CC=1      ←0
  │ before                      16L  1C    3m  CC=1      ←0
  │ before                      14L  0C    1m  CC=1      ←0
  │ after                       13L  0C    1m  CC=1      ←0
  │ before                      13L  0C    1m  CC=1      ←0
  │ after                       13L  0C    2m  CC=1      ←0
  │ before                      13L  0C    2m  CC=1      ←0
  │ requirements.txt            13L  0C    0m  CC=0.0    ←0
  │ after                       11L  0C    1m  CC=1      ←0
  │ before                      11L  0C    1m  CC=1      ←0
  │ after                       11L  0C    1m  CC=1      ←1
  │ after                       11L  0C    2m  CC=1      ←2
  │ before                      11L  0C    2m  CC=1      ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │
  project/                        CC̄=0.0    ←in:0  →out:0
  │ !! map.toon.yaml            96742L  0C  2716m  CC=0.0    ←19
  │ !! calls.yaml                3201L  0C    0m  CC=0.0    ←0
  │ calls.toon.yaml            347L  0C    0m  CC=0.0    ←0
  │ duplication.toon.yaml      332L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         214L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         116L  0C    0m  CC=0.0    ←0
  │ analysis.toon.yaml         116L  0C    0m  CC=0.0    ←0
  │ validation.toon.yaml       105L  0C    0m  CC=0.0    ←0
  │ project.toon.yaml           51L  0C    0m  CC=0.0    ←0
  │ prompt.txt                  47L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         43L  0C    0m  CC=0.0    ←0
  │ evolution.toon.yaml         43L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │ generated-cli-tests.testql.toon.yaml    12L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     Makefile                                  0L

COUPLING:
                                                    Taskfile                   src.prefact          vscode-extension.src         examples.06-api-usage    benchmark_ram_optimization                   project.map       examples.sample-project  examples.01-individual-rules    examples.02-multiple-rules    examples.03-output-formats      examples.04-custom-rules
                      Taskfile                            ──                           ←43                                                         ←34                           ←25                                                         ←17                            ←6                            ←6                            ←2                                hub
                   src.prefact                            43                            ──                            46                            ←1                                                          19                                                                                                                                                        !! fan-out
          vscode-extension.src                                                         ←46                            ──                                                          ←1                                                                                                                                                                                  ←1  hub
         examples.06-api-usage                            34                             1                                                          ──                                                                                                                                                                                                                    !! fan-out
    benchmark_ram_optimization                            25                                                           1                                                          ──                                                                                                                                                                                      !! fan-out
                   project.map                                                         ←19                                                                                                                      ──                            ←1                            ←2                                                                                            hub
       examples.sample-project                            17                                                                                                                                                     1                            ──                             1                                                                                            !! fan-out
  examples.01-individual-rules                             6                                                                                                                                                     2                             2                            ──                                                                                            !! fan-out
    examples.02-multiple-rules                             6                                                                                                                                                                                                                                              ──                                                            
    examples.03-output-formats                             2                                                                                                                                                                                                                                                                            ──                              
      examples.04-custom-rules                                                                                         1                                                                                                                                                                                                                                              ──
  CYCLES: none
  HUB: Taskfile/ (fan-in=133)
  HUB: project.map/ (fan-in=22)
  HUB: vscode-extension.src/ (fan-in=48)
  SMELL: examples.06-api-usage/ fan-out=35 → split needed
  SMELL: examples.01-individual-rules/ fan-out=10 → split needed
  SMELL: src.prefact/ fan-out=108 → split needed
  SMELL: examples.sample-project/ fan-out=19 → split needed
  SMELL: benchmark_ram_optimization/ fan-out=26 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 39 groups | 99f 13256L | 2026-04-25

SUMMARY:
  files_scanned: 99
  total_lines:   13256
  dup_groups:    39
  dup_fragments: 107
  saved_lines:   379
  scan_ms:       30372

HOTSPOTS[7] (files with most duplication):
  src/prefact/rules/unimport_based.py  dup=84L  groups=3  frags=7  (0.6%)
  src/prefact/rules/composite_rules.py  dup=56L  groups=3  frags=6  (0.4%)
  src/prefact/rules/import_linter_based.py  dup=54L  groups=3  frags=9  (0.4%)
  src/prefact/performance/cache.py  dup=41L  groups=3  frags=7  (0.3%)
  src/prefact/rules/pylint_based.py  dup=37L  groups=2  frags=5  (0.3%)
  src/prefact/rules/mypy_based.py  dup=29L  groups=3  frags=6  (0.2%)
  examples/04-custom-rules/custom_rules/no_todo_rule.py  dup=28L  groups=2  frags=4  (0.2%)

DUPLICATES[39] (ranked by impact):
  [1343b32626b1ecd1] ! STRU  validate  L=9 N=6 saved=45 sim=1.00
      src/prefact/rules/ai_boilerplate.py:69-77  (validate)
      src/prefact/rules/importchecker_based.py:253-262  (validate)
      src/prefact/rules/llm_generated_code.py:183-191  (validate)
      src/prefact/rules/magic_numbers.py:130-138  (validate)
      src/prefact/rules/unimport_based.py:295-304  (validate)
      src/prefact/rules/unimport_based.py:362-371  (validate)
  [fb8a4c52c4513ef3] ! EXAC  fix  L=3 N=14 saved=39 sim=1.00
      examples/04-custom-rules/custom_rules/no_todo_rule.py:46-48  (fix)
      examples/04-custom-rules/custom_rules/no_todo_rule.py:94-96  (fix)
      src/prefact/rules/ai_boilerplate.py:65-67  (fix)
      src/prefact/rules/import_linter_based.py:168-171  (fix)
      src/prefact/rules/import_linter_based.py:307-309  (fix)
      src/prefact/rules/importchecker_based.py:372-374  (fix)
      src/prefact/rules/importchecker_based.py:480-482  (fix)
      src/prefact/rules/llm_generated_code.py:179-181  (fix)
      src/prefact/rules/llm_hallucinations.py:201-203  (fix)
      src/prefact/rules/magic_numbers.py:126-128  (fix)
      src/prefact/rules/mypy_based.py:146-149  (fix)
      src/prefact/rules/mypy_based.py:210-212  (fix)
      src/prefact/rules/ruff_based.py:93-95  (fix)
      src/prefact/rules/ruff_based.py:305-308  (fix)
  [fd9736dd4e8df736] ! STRU  fix  L=18 N=3 saved=36 sim=1.00
      src/prefact/rules/unimport_based.py:185-202  (fix)
      src/prefact/rules/unimport_based.py:276-293  (fix)
      src/prefact/rules/unimport_based.py:409-426  (fix)
  [fe7129d46d801afa]   STRU  validate  L=10 N=4 saved=30 sim=1.00
      src/prefact/rules/import_linter_based.py:173-182  (validate)
      src/prefact/rules/import_linter_based.py:255-264  (validate)
      src/prefact/rules/import_linter_based.py:311-319  (validate)
      src/prefact/rules/import_linter_based.py:397-405  (validate)
  [61838ef52572f18b]   STRU  get_cache  L=5 N=5 saved=20 sim=1.00
      src/prefact/performance/cache.py:273-277  (get_cache)
      src/prefact/performance/cache.py:280-284  (get_scan_cache)
      src/prefact/performance/cache.py:287-291  (get_config_cache)
      src/prefact/performance/cache.py:294-298  (get_rule_cache)
      src/prefact/performance/cache.py:301-305  (get_hash_cache)
  [9e61a0169b46b783]   EXAC  validate  L=16 N=2 saved=16 sim=1.00
      src/prefact/rules/composite_rules.py:185-200  (validate)
      src/prefact/rules/composite_rules.py:261-276  (validate)
  [00e3ba6791c8b05d]   STRU  get_cache  L=4 N=5 saved=16 sim=1.00
      src/prefact/performance/cache_state.py:36-39  (get_cache)
      src/prefact/performance/cache_state.py:42-45  (get_scan_cache)
      src/prefact/performance/cache_state.py:48-51  (get_config_cache)
      src/prefact/performance/cache_state.py:54-57  (get_rule_cache)
      src/prefact/performance/cache_state.py:60-63  (get_hash_cache)
  [9b03faadcb4a354b]   STRU  validate  L=14 N=2 saved=14 sim=1.00
      src/prefact/rules/pylint_based.py:150-163  (validate)
      src/prefact/rules/pylint_based.py:210-223  (validate)
  [ad988c8760eff899]   EXAC  validate  L=11 N=2 saved=11 sim=1.00
      examples/04-custom-rules/custom_rules/no_todo_rule.py:50-60  (validate)
      examples/04-custom-rules/custom_rules/no_todo_rule.py:98-108  (validate)
  [0012aae792aa3fda]   EXAC  get_hash  L=10 N=2 saved=10 sim=1.00
      src/prefact/performance/cache.py:229-238  (get_hash)
      src/prefact/performance/cache_adapters.py:95-101  (get_hash)
  [8edfe22670ef44e1]   EXAC  process_data  L=8 N=2 saved=8 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:7-14  (process_data)
      examples/01-individual-rules/unused-imports/before.py:7-14  (process_data)
  [7db25b6baa69639e]   EXAC  scan_file  L=4 N=3 saved=8 sim=1.00
      src/prefact/rules/composite_factory.py:73-76  (scan_file)
      src/prefact/rules/composite_rules.py:86-91  (scan_file)
      src/prefact/rules/composite_rules.py:171-176  (scan_file)
  [4a3cdf885b861207]   EXAC  fix  L=4 N=3 saved=8 sim=1.00
      src/prefact/rules/composite_factory.py:78-81  (fix)
      src/prefact/rules/composite_rules.py:93-98  (fix)
      src/prefact/rules/composite_rules.py:178-183  (fix)
  [c245c0aa11f8ea14]   EXAC  validate  L=8 N=2 saved=8 sim=1.00
      src/prefact/rules/duplicate_imports.py:73-80  (validate)
      src/prefact/rules/unused_imports.py:47-54  (validate)
  [06dc55e08866a299]   EXAC  _load_mypy_config  L=8 N=2 saved=8 sim=1.00
      src/prefact/rules/mypy_based.py:103-110  (_load_mypy_config)
      src/prefact/rules/mypy_based.py:178-185  (_load_mypy_config)
  [94f4bfa96465f169]   EXAC  calculate_sum  L=7 N=2 saved=7 sim=1.00
      examples/03-output-formats/sample_code.py:15-21  (calculate_sum)
      examples/sample-project/core.py:13-19  (calculate_sum)
  [53efaf6dde1d343f]   EXAC  process_data  L=6 N=2 saved=6 sim=1.00
      examples/01-individual-rules/print-statements/after.py:3-8  (process_data)
      examples/01-individual-rules/print-statements/before.py:3-8  (process_data)
  [52878821d84977d2]   EXAC  __init__  L=6 N=2 saved=6 sim=1.00
      src/prefact/fixer.py:12-17  (__init__)
      src/prefact/validator.py:12-17  (__init__)
  [55804bb29d6c13a1]   EXAC  set_hash  L=6 N=2 saved=6 sim=1.00
      src/prefact/performance/cache.py:240-245  (set_hash)
      src/prefact/performance/cache_adapters.py:103-106  (set_hash)
  [50fd28cabdf165f6]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      src/prefact/rules/import_linter_based.py:128-130  (__init__)
      src/prefact/rules/import_linter_based.py:192-194  (__init__)
      src/prefact/rules/import_linter_based.py:274-276  (__init__)
  [17783b0f3fb50cdb]   EXAC  __init__  L=3 N=3 saved=6 sim=1.00
      src/prefact/rules/pylint_based.py:87-89  (__init__)
      src/prefact/rules/pylint_based.py:173-175  (__init__)
      src/prefact/rules/pylint_based.py:245-247  (__init__)
  [16897491a14d9018]   STRU  get_performance_monitor  L=6 N=2 saved=6 sim=1.00
      src/prefact/performance/parallel.py:348-353  (get_performance_monitor)
      src/prefact/rules/registry.py:179-184  (get_lazy_registry)
  [772c77ab0afca55b]   EXAC  process_user  L=5 N=2 saved=5 sim=1.00
      examples/01-individual-rules/relative-imports/after.py:11-15  (process_user)
      examples/01-individual-rules/relative-imports/before.py:11-15  (process_user)
  [b2a3226830ad4536]   STRU  __init__  L=5 N=2 saved=5 sim=1.00
      src/prefact/rules/unimport_based.py:223-227  (__init__)
      src/prefact/rules/unimport_based.py:315-319  (__init__)
  [8c3b4878cda6c2a9]   EXAC  calculate  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/print-statements/after.py:10-13  (calculate)
      examples/01-individual-rules/print-statements/before.py:10-13  (calculate)
  [d25fff731ecfc648]   EXAC  read_file  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/unused-imports/after.py:22-25  (read_file)
      examples/01-individual-rules/unused-imports/before.py:22-25  (read_file)
  [641667a4d5a7609f]   EXAC  process  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/wildcard-imports/after.py:8-11  (process)
      examples/01-individual-rules/wildcard-imports/before.py:8-11  (process)
  [c522b15451457d34]   STRU  format_data  L=4 N=2 saved=4 sim=1.00
      examples/01-individual-rules/string-concat/before.py:8-11  (format_data)
      examples/sample-project/utils.py:23-26  (helper_function)
  [ced691da4eea9c77]   EXAC  process_data  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/duplicate-imports/after.py:9-11  (process_data)
      examples/01-individual-rules/duplicate-imports/before.py:12-14  (process_data)
  [d45b7d0f286fc4fd]   EXAC  add  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:3-5  (add)
      examples/01-individual-rules/missing-return-type/before.py:3-5  (add)
  [9baec9052aef7a75]   EXAC  get_user  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:7-9  (get_user)
      examples/01-individual-rules/missing-return-type/before.py:7-9  (get_user)
  [47c667d00e4443d6]   EXAC  process  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/missing-return-type/after.py:14-16  (process)
      examples/01-individual-rules/missing-return-type/before.py:14-16  (process)
  [6979933d3c997c8c]   EXAC  process  L=3 N=2 saved=3 sim=1.00
      examples/01-individual-rules/sorted-imports/after.py:11-13  (process)
      examples/01-individual-rules/sorted-imports/before.py:11-13  (process)
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
      src/prefact/rules/importchecker_based.py:102-104  (__init__)
      src/prefact/rules/importchecker_based.py:273-275  (__init__)
  [53e9ef8f2a396333]   EXAC  __init__  L=3 N=2 saved=3 sim=1.00
      src/prefact/rules/mypy_based.py:99-101  (__init__)
      src/prefact/rules/mypy_based.py:174-176  (__init__)

REFACTOR[39] (ranked by priority):
  [1] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 6 occurrences of 9-line block across 5 files — saves 45 lines
      FILES: src/prefact/rules/ai_boilerplate.py, src/prefact/rules/importchecker_based.py, src/prefact/rules/llm_generated_code.py, src/prefact/rules/magic_numbers.py, src/prefact/rules/unimport_based.py
  [2] ○ extract_function   → utils/fix.py
      WHY: 14 occurrences of 3-line block across 9 files — saves 39 lines
      FILES: examples/04-custom-rules/custom_rules/no_todo_rule.py, src/prefact/rules/ai_boilerplate.py, src/prefact/rules/import_linter_based.py, src/prefact/rules/importchecker_based.py, src/prefact/rules/llm_generated_code.py +4 more
  [3] ○ extract_function   → src/prefact/rules/utils/fix.py
      WHY: 3 occurrences of 18-line block across 1 files — saves 36 lines
      FILES: src/prefact/rules/unimport_based.py
  [4] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 4 occurrences of 10-line block across 1 files — saves 30 lines
      FILES: src/prefact/rules/import_linter_based.py
  [5] ○ extract_function   → src/prefact/performance/utils/get_cache.py
      WHY: 5 occurrences of 5-line block across 1 files — saves 20 lines
      FILES: src/prefact/performance/cache.py
  [6] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 16-line block across 1 files — saves 16 lines
      FILES: src/prefact/rules/composite_rules.py
  [7] ○ extract_function   → src/prefact/performance/utils/get_cache.py
      WHY: 5 occurrences of 4-line block across 1 files — saves 16 lines
      FILES: src/prefact/performance/cache_state.py
  [8] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 14-line block across 1 files — saves 14 lines
      FILES: src/prefact/rules/pylint_based.py
  [9] ○ extract_function   → examples/04-custom-rules/custom_rules/utils/validate.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: examples/04-custom-rules/custom_rules/no_todo_rule.py
  [10] ○ extract_class      → src/prefact/performance/utils/get_hash.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: src/prefact/performance/cache.py, src/prefact/performance/cache_adapters.py
  [11] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/process_data.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [12] ○ extract_function   → src/prefact/rules/utils/scan_file.py
      WHY: 3 occurrences of 4-line block across 2 files — saves 8 lines
      FILES: src/prefact/rules/composite_factory.py, src/prefact/rules/composite_rules.py
  [13] ○ extract_function   → src/prefact/rules/utils/fix.py
      WHY: 3 occurrences of 4-line block across 2 files — saves 8 lines
      FILES: src/prefact/rules/composite_factory.py, src/prefact/rules/composite_rules.py
  [14] ○ extract_function   → src/prefact/rules/utils/validate.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: src/prefact/rules/duplicate_imports.py, src/prefact/rules/unused_imports.py
  [15] ○ extract_function   → src/prefact/rules/utils/_load_mypy_config.py
      WHY: 2 occurrences of 8-line block across 1 files — saves 8 lines
      FILES: src/prefact/rules/mypy_based.py
  [16] ○ extract_function   → examples/utils/calculate_sum.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: examples/03-output-formats/sample_code.py, examples/sample-project/core.py
  [17] ○ extract_function   → examples/01-individual-rules/print-statements/utils/process_data.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: examples/01-individual-rules/print-statements/after.py, examples/01-individual-rules/print-statements/before.py
  [18] ○ extract_function   → src/prefact/utils/__init__.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/fixer.py, src/prefact/validator.py
  [19] ○ extract_class      → src/prefact/performance/utils/set_hash.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/performance/cache.py, src/prefact/performance/cache_adapters.py
  [20] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/prefact/rules/import_linter_based.py
  [21] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: src/prefact/rules/pylint_based.py
  [22] ○ extract_function   → src/prefact/utils/get_performance_monitor.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: src/prefact/performance/parallel.py, src/prefact/rules/registry.py
  [23] ○ extract_function   → examples/01-individual-rules/relative-imports/utils/process_user.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: examples/01-individual-rules/relative-imports/after.py, examples/01-individual-rules/relative-imports/before.py
  [24] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: src/prefact/rules/unimport_based.py
  [25] ○ extract_function   → examples/01-individual-rules/print-statements/utils/calculate.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/print-statements/after.py, examples/01-individual-rules/print-statements/before.py
  [26] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/read_file.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [27] ○ extract_function   → examples/01-individual-rules/wildcard-imports/utils/process.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/wildcard-imports/after.py, examples/01-individual-rules/wildcard-imports/before.py
  [28] ○ extract_function   → examples/utils/format_data.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: examples/01-individual-rules/string-concat/before.py, examples/sample-project/utils.py
  [29] ○ extract_function   → examples/01-individual-rules/duplicate-imports/utils/process_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/duplicate-imports/after.py, examples/01-individual-rules/duplicate-imports/before.py
  [30] ○ extract_function   → examples/01-individual-rules/missing-return-type/utils/add.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [31] ○ extract_function   → examples/01-individual-rules/missing-return-type/utils/get_user.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [32] ○ extract_class      → examples/01-individual-rules/missing-return-type/utils/process.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/missing-return-type/after.py, examples/01-individual-rules/missing-return-type/before.py
  [33] ○ extract_function   → examples/01-individual-rules/sorted-imports/utils/process.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/sorted-imports/after.py, examples/01-individual-rules/sorted-imports/before.py
  [34] ○ extract_function   → examples/01-individual-rules/unused-imports/utils/format_timestamp.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [35] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [36] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/add_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [37] ○ extract_class      → examples/01-individual-rules/unused-imports/utils/get_data.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: examples/01-individual-rules/unused-imports/after.py, examples/01-individual-rules/unused-imports/before.py
  [38] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/prefact/rules/importchecker_based.py
  [39] ○ extract_function   → src/prefact/rules/utils/__init__.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: src/prefact/rules/mypy_based.py

QUICK_WINS[22] (low risk, high savings — do first):
  [1] extract_function   saved=45L  → src/prefact/rules/utils/validate.py
      FILES: ai_boilerplate.py, importchecker_based.py, llm_generated_code.py +2
  [2] extract_function   saved=39L  → utils/fix.py
      FILES: no_todo_rule.py, ai_boilerplate.py, import_linter_based.py +6
  [3] extract_function   saved=36L  → src/prefact/rules/utils/fix.py
      FILES: unimport_based.py
  [4] extract_function   saved=30L  → src/prefact/rules/utils/validate.py
      FILES: import_linter_based.py
  [5] extract_function   saved=20L  → src/prefact/performance/utils/get_cache.py
      FILES: cache.py
  [6] extract_function   saved=16L  → src/prefact/rules/utils/validate.py
      FILES: composite_rules.py
  [7] extract_function   saved=16L  → src/prefact/performance/utils/get_cache.py
      FILES: cache_state.py
  [8] extract_function   saved=14L  → src/prefact/rules/utils/validate.py
      FILES: pylint_based.py
  [9] extract_function   saved=11L  → examples/04-custom-rules/custom_rules/utils/validate.py
      FILES: no_todo_rule.py
  [10] extract_class      saved=10L  → src/prefact/performance/utils/get_hash.py
      FILES: cache.py, cache_adapters.py

DEPENDENCY_RISK[1] (duplicates spanning multiple packages):
  fix  packages=2  files=9
      examples/04-custom-rules/custom_rules/no_todo_rule.py
      src/prefact/rules/ai_boilerplate.py
      src/prefact/rules/import_linter_based.py
      src/prefact/rules/importchecker_based.py
      +5 more

EFFORT_ESTIMATE (total ≈ 13.9h):
  hard   validate                            saved=45L  ~90min
  hard   fix                                 saved=39L  ~156min
  medium fix                                 saved=36L  ~72min
  medium validate                            saved=30L  ~60min
  medium get_cache                           saved=20L  ~40min
  medium validate                            saved=16L  ~32min
  medium get_cache                           saved=16L  ~32min
  easy   validate                            saved=14L  ~28min
  easy   validate                            saved=11L  ~22min
  easy   get_hash                            saved=10L  ~20min
  ... +29 more (~284min)

METRICS-TARGET:
  dup_groups:  39 → 0
  saved_lines: 379 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 3405 func | 70f | 2026-04-25

NEXT[1] (ranked by impact):
  [1] !  SPLIT-FUNC      MagicNumberRule.scan_file  CC=15  fan=9
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 135


RISKS[0]: none

METRICS-TARGET:
  CC̄:          0.6 → ≤0.4
  max-CC:      15 → ≤7
  god-modules: 0 → 0
  high-CC(≥15): 1 → ≤0
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
  prev CC̄=2.8 → now CC̄=0.6
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
