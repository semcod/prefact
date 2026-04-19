# prefact

Python code quality tool with LLM-aware rules, plugin system, and enterprise features

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Intent](#intent)

## Metadata

- **name**: `prefact`
- **version**: `unknown`
- **python_requires**: `>=3.13`
- **license**: MIT
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Taskfile.yml, Makefile, src/

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

## Source Map

- test_large_files.py
- examples/01-individual-rules/relative-imports/after.py
- examples/01-individual-rules/relative-imports/before.py
- examples/01-individual-rules/wildcard-imports/after.py
- examples/01-individual-rules/wildcard-imports/before.py
- examples/01-individual-rules/missing-return-type/after.py
- examples/01-individual-rules/missing-return-type/before.py
- examples/01-individual-rules/duplicate-imports/after.py
- examples/01-individual-rules/duplicate-imports/before.py
- examples/01-individual-rules/unused-imports/after.py
- examples/01-individual-rules/unused-imports/before.py
- examples/01-individual-rules/string-concat/after.py
- examples/01-individual-rules/string-concat/before.py
- examples/01-individual-rules/sorted-imports/after.py
- examples/01-individual-rules/sorted-imports/before.py
- examples/01-individual-rules/print-statements/after.py
- examples/01-individual-rules/print-statements/before.py
- examples/tests/test_examples.py
- examples/02-multiple-rules/messy_module.py
- examples/sample-project/cli.py
- examples/sample-project/utils.py
- examples/sample-project/models.py
- examples/sample-project/core.py
- examples/03-output-formats/sample_code.py
- examples/generate_examples.py
- examples/06-api-usage/example.py
- examples/run_examples.py
- examples/.venv/lib/python3.13/site-packages/dotenv/version.py
- examples/.venv/lib/python3.13/site-packages/dotenv/cli.py
- examples/.venv/lib/python3.13/site-packages/dotenv/__init__.py
- examples/.venv/lib/python3.13/site-packages/dotenv/__main__.py
- examples/.venv/lib/python3.13/site-packages/dotenv/parser.py
- examples/.venv/lib/python3.13/site-packages/dotenv/main.py
- examples/.venv/lib/python3.13/site-packages/dotenv/variables.py
- examples/.venv/lib/python3.13/site-packages/dotenv/ipython.py
- examples/.venv/lib/python3.13/site-packages/referencing/exceptions.py
- examples/.venv/lib/python3.13/site-packages/referencing/retrieval.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/test_exceptions.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/test_core.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/test_referencing_suite.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/__init__.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/test_retrieval.py
- examples/.venv/lib/python3.13/site-packages/referencing/tests/test_jsonschema.py
- examples/.venv/lib/python3.13/site-packages/referencing/_core.py
- examples/.venv/lib/python3.13/site-packages/referencing/__init__.py
- examples/.venv/lib/python3.13/site-packages/referencing/jsonschema.py
- examples/.venv/lib/python3.13/site-packages/referencing/_attrs.py
- examples/.venv/lib/python3.13/site-packages/referencing/typing.py
- examples/.venv/lib/python3.13/site-packages/httpcore/_api.py
- examples/.venv/lib/python3.13/site-packages/httpcore/_sync/http2.py
