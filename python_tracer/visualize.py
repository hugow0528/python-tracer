from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def write_html_report(trace_data: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / "index.html"
    html_path.write_text(_build_html(trace_data), encoding="utf-8")
    return html_path


def _build_html(trace_data: dict[str, Any]) -> str:
    trace_json = json.dumps(trace_data, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Python Trace Visualization</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      color: #1f2937;
      background: #f8fafc;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .card {{
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .stat {{ font-size: 24px; font-weight: 700; }}
    .muted {{ color: #6b7280; }}
    input, select {{
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #d1d5db;
      border-radius: 6px;
      padding: 8px 10px;
      margin-top: 6px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
      padding: 8px 6px;
      vertical-align: top;
      font-size: 14px;
    }}
    code {{
      background: #f3f4f6;
      border-radius: 4px;
      padding: 2px 4px;
      word-break: break-word;
    }}
    details {{ margin-top: 8px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Python Trace Visualization</h1>
    <p class="muted">Interactive function call graph summary generated from runtime events.</p>
    <div class="card">
      <div class="grid">
        <div><div class="muted">Target Script</div><div id="targetScript"></div></div>
        <div><div class="muted">Generated At</div><div id="generatedAt"></div></div>
        <div><div class="muted">Total Events</div><div class="stat" id="totalEvents"></div></div>
        <div><div class="muted">Total Functions</div><div class="stat" id="totalFunctions"></div></div>
      </div>
    </div>

    <div class="card">
      <label for="search">Search function/module/file</label>
      <input id="search" placeholder="Type to filter nodes..." />
      <label for="moduleFilter">Module filter</label>
      <select id="moduleFilter"></select>
    </div>

    <div class="card">
      <h2>Function Nodes</h2>
      <table>
        <thead>
          <tr>
            <th>Function</th>
            <th>Module</th>
            <th>Call Count</th>
            <th>File</th>
          </tr>
        </thead>
        <tbody id="nodesBody"></tbody>
      </table>
    </div>

    <div class="card">
      <h2>Call Edges</h2>
      <details open>
        <summary>Expand/collapse edge list</summary>
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Target</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody id="edgesBody"></tbody>
        </table>
      </details>
    </div>
  </div>

  <script>
    const TRACE_DATA = {trace_json};

    const nodes = TRACE_DATA.graph.nodes;
    const edges = TRACE_DATA.graph.edges;

    const targetScriptEl = document.getElementById('targetScript');
    const generatedAtEl = document.getElementById('generatedAt');
    const totalEventsEl = document.getElementById('totalEvents');
    const totalFunctionsEl = document.getElementById('totalFunctions');
    const nodesBody = document.getElementById('nodesBody');
    const edgesBody = document.getElementById('edgesBody');
    const searchEl = document.getElementById('search');
    const moduleFilterEl = document.getElementById('moduleFilter');

    targetScriptEl.textContent = TRACE_DATA.metadata.target_script;
    generatedAtEl.textContent = TRACE_DATA.metadata.generated_at;
    totalEventsEl.textContent = String(TRACE_DATA.metadata.total_events);
    totalFunctionsEl.textContent = String(nodes.length);

    const modules = ['(all)', ...Array.from(new Set(nodes.map((n) => n.module))).sort()];
    for (const moduleName of modules) {{
      const option = document.createElement('option');
      option.value = moduleName;
      option.textContent = moduleName;
      moduleFilterEl.appendChild(option);
    }}

    function render() {{
      const query = searchEl.value.trim().toLowerCase();
      const moduleFilter = moduleFilterEl.value;

      const filteredNodes = nodes.filter((node) => {{
        const moduleMatch = moduleFilter === '(all)' || node.module === moduleFilter;
        if (!moduleMatch) return false;
        if (!query) return true;
        const haystack = `${{node.function}} ${{node.module}} ${{node.filename}}`.toLowerCase();
        return haystack.includes(query);
      }});

      const visibleNodeIds = new Set(filteredNodes.map((n) => n.id));
      const filteredEdges = edges.filter((edge) =>
        visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
      );

      nodesBody.innerHTML = '';
      for (const node of filteredNodes) {{
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><code>${{node.function}}</code></td>
          <td><code>${{node.module}}</code></td>
          <td>${{node.call_count}}</td>
          <td><code>${{node.filename}}</code></td>
        `;
        nodesBody.appendChild(row);
      }}

      edgesBody.innerHTML = '';
      for (const edge of filteredEdges) {{
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><code>${{edge.source}}</code></td>
          <td><code>${{edge.target}}</code></td>
          <td>${{edge.count}}</td>
        `;
        edgesBody.appendChild(row);
      }}
    }}

    searchEl.addEventListener('input', render);
    moduleFilterEl.addEventListener('change', render);
    render();
  </script>
</body>
</html>
"""
