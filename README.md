# python-tracer

Visualize Python execution as a call graph with JSON trace output and a static HTML report.

## What this project does

- Traces Python runtime events: `call`, `return`, and `exception`
- Records structured trace metadata (file, line, function, module, timestamps, parent call)
- Produces:
  - `trace.json` (raw trace + computed graph)
  - `index.html` (interactive visualization)

## Quick start

Run the example program and generate visualization output:

```bash
python -m python_tracer trace /home/runner/work/python-tracer/python-tracer/examples/target_program.py --output-dir /home/runner/work/python-tracer/python-tracer/build/trace_visualization
```

Generated files:

- `/home/runner/work/python-tracer/python-tracer/build/trace_visualization/trace.json`
- `/home/runner/work/python-tracer/python-tracer/build/trace_visualization/index.html`

## CLI usage

```bash
python -m python_tracer trace SCRIPT_PATH [--output-dir OUTPUT_DIR] [--include-stdlib] [-- SCRIPT_ARGS...]
```

Options:

- `--output-dir`: Destination for `trace.json` and `index.html` (default: `build/trace_visualization`)
- `--include-stdlib`: Include events from outside the repository root
- `--`: Pass remaining arguments to the traced script

## Tests

```bash
python -m unittest discover -s /home/runner/work/python-tracer/python-tracer/tests
```

## GitHub Actions deployment

The repository includes a workflow that:

1. Runs tests
2. Generates visualization artifacts from the example script
3. Uploads artifacts
4. Deploys `index.html` + `trace.json` to GitHub Pages

Workflow file:

- `/home/runner/work/python-tracer/python-tracer/.github/workflows/visualize-trace.yml`