from __future__ import annotations

from pathlib import Path
import json
import tempfile
import textwrap
import unittest

from python_tracer.cli import run_trace
from python_tracer.tracer import TraceCollector, build_trace_summary


class TracerTests(unittest.TestCase):
    def test_trace_capture_includes_call_return_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "sample.py"
            script_path.write_text(
                textwrap.dedent(
                    """
                    def child():
                        raise RuntimeError("boom")

                    def parent():
                        try:
                            child()
                        except RuntimeError:
                            return "handled"

                    parent()
                    """
                ).strip(),
                encoding="utf-8",
            )

            collector = TraceCollector(root_dir=root)
            events = collector.run_script(script_path=script_path, script_args=[])
            event_types = {event.event for event in events}

            self.assertIn("call", event_types)
            self.assertIn("return", event_types)
            self.assertIn("exception", event_types)

            child_call = next(event for event in events if event.event == "call" and event.function == "child")
            parent_call = next(event for event in events if event.event == "call" and event.function == "parent")
            self.assertEqual(child_call.parent_call_id, parent_call.call_id)

    def test_trace_summary_has_graph_nodes_and_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "sample.py"
            script_path.write_text(
                "def a():\n    return 1\n\ndef b():\n    return a()\n\nb()\n",
                encoding="utf-8",
            )
            collector = TraceCollector(root_dir=root)
            events = collector.run_script(script_path=script_path, script_args=[])

            trace_data = build_trace_summary(events=events, target_script=script_path, root_dir=root)
            self.assertIn("metadata", trace_data)
            self.assertIn("events", trace_data)
            self.assertIn("graph", trace_data)
            self.assertGreater(len(trace_data["graph"]["nodes"]), 0)
            self.assertGreater(len(trace_data["graph"]["edges"]), 0)

    def test_run_trace_writes_json_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script_path = root / "sample.py"
            output_dir = root / "out"
            script_path.write_text("def f():\n    return 42\n\nf()\n", encoding="utf-8")

            paths = run_trace(script_path=script_path, output_dir=output_dir, script_args=[])
            self.assertTrue(paths["trace_json"].exists())
            self.assertTrue(paths["html_report"].exists())

            trace_data = json.loads(paths["trace_json"].read_text(encoding="utf-8"))
            self.assertIn("metadata", trace_data)
            self.assertIn("events", trace_data)
            self.assertIn("graph", trace_data)

            html = paths["html_report"].read_text(encoding="utf-8")
            self.assertIn("Python Trace Visualization", html)
            self.assertIn("TRACE_DATA", html)


if __name__ == "__main__":
    unittest.main()
