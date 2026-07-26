from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import runpy
import sys
import time
from types import FrameType
from typing import Any


@dataclass
class TraceEvent:
    event: str
    timestamp: float
    call_id: int | None
    parent_call_id: int | None
    module: str
    function: str
    filename: str
    lineno: int
    depth: int


class TraceCollector:
    def __init__(self, root_dir: Path, include_stdlib: bool = False) -> None:
        self.root_dir = root_dir.resolve()
        self.include_stdlib = include_stdlib
        self.events: list[TraceEvent] = []
        self._next_call_id = 1
        self._frame_to_call_id: dict[int, int] = {}
        self._start_time = 0.0

    def _relative_time(self) -> float:
        return round(time.perf_counter() - self._start_time, 6)

    def _should_trace_file(self, filename: str) -> bool:
        if self.include_stdlib:
            return True
        if not filename:
            return False
        try:
            path = Path(filename).resolve()
        except (OSError, RuntimeError):
            return False
        return path.is_relative_to(self.root_dir)

    def _event_from_frame(
        self,
        frame: FrameType,
        event: str,
        call_id: int | None,
        parent_call_id: int | None,
    ) -> TraceEvent:
        module = str(frame.f_globals.get("__name__", "<unknown>"))
        filename = str(Path(frame.f_code.co_filename).resolve())
        depth = 0
        if call_id is not None:
            depth = len(self._frame_to_call_id)
        return TraceEvent(
            event=event,
            timestamp=self._relative_time(),
            call_id=call_id,
            parent_call_id=parent_call_id,
            module=module,
            function=frame.f_code.co_name,
            filename=filename,
            lineno=frame.f_lineno,
            depth=depth,
        )

    def _trace(self, frame: FrameType, event: str, arg: Any) -> Any:
        if not self._should_trace_file(frame.f_code.co_filename):
            return None

        frame_id = id(frame)
        parent_call_id = None
        if frame.f_back is not None:
            parent_call_id = self._frame_to_call_id.get(id(frame.f_back))

        if event == "call":
            call_id = self._next_call_id
            self._next_call_id += 1
            self._frame_to_call_id[frame_id] = call_id
            self.events.append(self._event_from_frame(frame, "call", call_id, parent_call_id))
            return self._trace

        call_id = self._frame_to_call_id.get(frame_id)
        if event == "return":
            self.events.append(self._event_from_frame(frame, "return", call_id, parent_call_id))
            self._frame_to_call_id.pop(frame_id, None)
        elif event == "exception":
            self.events.append(self._event_from_frame(frame, "exception", call_id, parent_call_id))
        return self._trace

    def run_script(self, script_path: Path, script_args: list[str]) -> list[TraceEvent]:
        script_path = script_path.resolve()
        old_argv = sys.argv[:]
        old_trace = sys.gettrace()
        self.events = []
        self._next_call_id = 1
        self._frame_to_call_id = {}
        self._start_time = time.perf_counter()

        try:
            sys.argv = [str(script_path), *script_args]
            sys.settrace(self._trace)
            runpy.run_path(str(script_path), run_name="__main__")
        finally:
            sys.settrace(old_trace)
            sys.argv = old_argv
        return self.events


def build_trace_summary(
    events: list[TraceEvent],
    target_script: Path,
    root_dir: Path,
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str], int] = {}
    call_id_to_node: dict[int, str] = {}

    for event in events:
        node_key = f"{event.module}:{event.function}:{event.filename}"
        if node_key not in nodes:
            nodes[node_key] = {
                "id": node_key,
                "module": event.module,
                "function": event.function,
                "filename": event.filename,
                "call_count": 0,
            }
        if event.event == "call":
            nodes[node_key]["call_count"] += 1
            if event.call_id is not None:
                call_id_to_node[event.call_id] = node_key
            if event.parent_call_id is not None:
                parent_node = call_id_to_node.get(event.parent_call_id)
                if parent_node is not None:
                    edge_key = (parent_node, node_key)
                    edges[edge_key] = edges.get(edge_key, 0) + 1

    graph_nodes = sorted(nodes.values(), key=lambda node: node["id"])
    graph_edges = [
        {"source": source, "target": target, "count": count}
        for (source, target), count in sorted(edges.items(), key=lambda item: (item[0][0], item[0][1]))
    ]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "root_dir": str(root_dir.resolve()),
            "target_script": str(target_script.resolve()),
            "total_events": len(events),
        },
        "events": [asdict(event) for event in events],
        "graph": {
            "nodes": graph_nodes,
            "edges": graph_edges,
        },
    }


def write_trace_json(trace_data: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    trace_path = output_dir / "trace.json"
    trace_path.write_text(json.dumps(trace_data, indent=2, sort_keys=True), encoding="utf-8")
    return trace_path
