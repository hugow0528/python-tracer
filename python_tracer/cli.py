from __future__ import annotations

import argparse
from pathlib import Path

from .tracer import TraceCollector, build_trace_summary, write_trace_json
from .visualize import write_html_report


def run_trace(script_path: Path, output_dir: Path, script_args: list[str], include_stdlib: bool = False) -> dict[str, Path]:
    script_path = script_path.resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Script does not exist: {script_path}")

    root_dir = Path.cwd().resolve()
    collector = TraceCollector(root_dir=root_dir, include_stdlib=include_stdlib)
    events = collector.run_script(script_path=script_path, script_args=script_args)
    trace_data = build_trace_summary(events=events, target_script=script_path, root_dir=root_dir)
    trace_path = write_trace_json(trace_data=trace_data, output_dir=output_dir)
    html_path = write_html_report(trace_data=trace_data, output_dir=output_dir)
    return {"trace_json": trace_path, "html_report": html_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Python execution tracer with HTML visualization")
    subparsers = parser.add_subparsers(dest="command")

    trace_parser = subparsers.add_parser("trace", help="Trace a Python script and build visualization")
    trace_parser.add_argument("script_path", type=Path, help="Absolute or relative path to Python script")
    trace_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("build/trace_visualization"),
        help="Directory for trace.json and index.html",
    )
    trace_parser.add_argument(
        "--include-stdlib",
        action="store_true",
        help="Include traced events from outside repository root",
    )
    trace_parser.add_argument(
        "script_args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the traced script (prefix with --)",
    )

    args = parser.parse_args(argv)
    if args.command != "trace":
        parser.print_help()
        return 1

    script_args = args.script_args
    if script_args and script_args[0] == "--":
        script_args = script_args[1:]

    paths = run_trace(
        script_path=args.script_path,
        output_dir=args.output_dir,
        script_args=script_args,
        include_stdlib=args.include_stdlib,
    )
    print(f"Trace JSON: {paths['trace_json']}")
    print(f"HTML report: {paths['html_report']}")
    return 0
