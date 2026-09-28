# Unused Imports Rule Example

This example demonstrates the `unused-imports` rule which flags imports that are never used.

## What it detects

- Imports that are not referenced anywhere in the module
- Imports left behind after the code that used them was moved or deleted
- Symbols imported "just in case" that nothing consumes

## Files

- `before.py` — contains unused imports (`datetime`, `json`, `os`, `Path`).
- `after.py` — the same file with the unused imports removed.
- `data_helpers.py` — shared code (`DataProcessor` and helpers) used by both
  demo files.

`before.py` and `after.py` intentionally share the same body and differ only in
their import block, which is exactly what this rule examines. The shared class
lives in `data_helpers.py` so duplication detectors do not flag the pair as a
copy-pasted class (PLF-092).

## Run the scan

```bash
python -m prefact.cli scan --path examples/01-individual-rules/unused-imports \
  --config examples/01-individual-rules/unused-imports/prefact.yaml
```

The scan reports the unused imports in `before.py`; `after.py` and
`data_helpers.py` report no unused-import findings.
