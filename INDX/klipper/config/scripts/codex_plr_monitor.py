#!/usr/bin/env python3
"""Host-side PLR snapshot monitor for Klipper/Moonraker printers.

This does not try to move or resume the printer. It records enough state during
virtual_sdcard prints to make a later recovery decision possible.

DRAFT, not run on the printer. INDX version: one carriage and one [extruder], so
the IDEX dual_carriage/extruder1 objects are gone. It also records INDX's
TOOL_POSITIONS and _TOOLCHANGE_VARS macros, PLR's _PLR_STATE and the load cell;
the tool on the head is in save_variables (active_tool), captured as before.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA = "codex.ratrig.indx.plr.snapshot.v1"

BASE_OBJECTS = [
    "webhooks",
    "print_stats",
    "virtual_sdcard",
    "toolhead",
    "gcode_move",
    "pause_resume",
    "display_status",
    "idle_timeout",
    "heater_bed",
    "extruder",
    "fan",
    "bed_mesh",
    "save_variables",
    "gcode_macro TOOL_POSITIONS",
    "gcode_macro _TOOLCHANGE_VARS",
    "gcode_macro _PLR_STATE",
    "load_cell_probe",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def moonraker_get_json(base_url: str, path: str, timeout: float) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=timeout) as response:
        body = response.read()
    return json.loads(body.decode())


def moonraker_object_list(base_url: str, timeout: float) -> list[str]:
    data = moonraker_get_json(base_url, "/printer/objects/list", timeout)
    return list(data.get("result", {}).get("objects", []))


def build_object_query_list(base_url: str, timeout: float) -> list[str]:
    """Prefer live object discovery so renamed fans/heaters are captured."""
    try:
        available = set(moonraker_object_list(base_url, timeout))
    except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError):
        return BASE_OBJECTS

    dynamic_prefixes = (
        "extruder",
        "heater_generic ",
        "fan_generic ",
        "temperature_sensor ",
        "beacon",
        "load_cell",
        "indx",
    )
    objects: list[str] = []
    for name in BASE_OBJECTS:
        if name in available and name not in objects:
            objects.append(name)
    for name in sorted(available):
        if name.startswith(dynamic_prefixes) and name not in objects:
            objects.append(name)
    return objects


def moonraker_query(base_url: str, objects: list[str], timeout: float) -> dict[str, Any]:
    payload = json.dumps({"objects": {name: None for name in objects}}).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/printer/objects/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    data = json.loads(body.decode())
    if "result" not in data:
        raise RuntimeError(f"unexpected Moonraker response: {data!r}")
    return data["result"].get("status", {})


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def append_jsonl(path: Path, data: dict[str, Any], max_bytes: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > max_bytes:
        rotated = path.with_suffix(path.suffix + ".1")
        if rotated.exists():
            rotated.unlink()
        path.replace(rotated)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True))
        handle.write("\n")


def resolve_gcode_path(status: dict[str, Any], gcodes_dir: Path) -> Path | None:
    vsd = status.get("virtual_sdcard") or {}
    p = vsd.get("file_path")
    if p:
        return Path(p)
    filename = (status.get("print_stats") or {}).get("filename")
    if filename:
        return gcodes_dir / filename
    return None


def digest_file_window(path: Path, start: int, length: int) -> str | None:
    try:
        with path.open("rb") as handle:
            handle.seek(max(start, 0))
            return hashlib.sha256(handle.read(max(length, 0))).hexdigest()
    except OSError:
        return None


def file_fingerprint(path: Path, position: int) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    try:
        st = path.stat()
    except OSError as exc:
        info["error"] = str(exc)
        return info
    size = st.st_size
    info.update(
        {
            "size": size,
            "mtime": int(st.st_mtime),
            "sha256_head_64k": digest_file_window(path, 0, min(size, 65536)),
            "sha256_near_position_64k": digest_file_window(
                path, max(position - 32768, 0), min(size, 65536)
            ),
            "sha256_tail_64k": digest_file_window(path, max(size - 65536, 0), min(size, 65536)),
        }
    )
    return info


def gcode_context(path: Path, position: int, span: int = 4096) -> dict[str, Any]:
    context: dict[str, Any] = {"position": position}
    if not path.exists():
        return context
    try:
        start = max(position - span, 0)
        with path.open("rb") as handle:
            handle.seek(start)
            chunk = handle.read(span * 2)
    except OSError as exc:
        context["error"] = str(exc)
        return context

    rel = max(position - start, 0)
    before = chunk[:rel].decode("utf-8", errors="replace").splitlines()
    after = chunk[rel:].decode("utf-8", errors="replace").splitlines()
    context["previous_lines"] = before[-5:]
    context["next_lines"] = after[:5]
    prev_newline = chunk.rfind(b"\n", 0, rel)
    next_newline = chunk.find(b"\n", rel)
    context["window_start"] = start
    context["window_end"] = start + len(chunk)
    context["line_start_before_or_at_position"] = start + prev_newline + 1 if prev_newline >= 0 else 0
    context["next_line_start_after_position"] = (
        start + next_newline + 1 if next_newline >= 0 else None
    )
    return context


def compact_status(
    status: dict[str, Any],
    gcodes_dir: Path,
    interval: float,
    queried_objects: list[str],
) -> dict[str, Any]:
    ps = status.get("print_stats") or {}
    vsd = status.get("virtual_sdcard") or {}
    position = int(vsd.get("file_position") or 0)
    gcode_path = resolve_gcode_path(status, gcodes_dir)
    snapshot: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "created_at": utc_now(),
        "hostname": socket.gethostname(),
        "capture": {
            "poll_interval_seconds": interval,
            "queried_objects": queried_objects,
            "note": "Host-side snapshot only; Rat Rig has no MCU-flashed power-loss stepper state.",
        },
        "recoverable": False,
        "reason": "",
        "print_stats": ps,
        "virtual_sdcard": vsd,
        "toolhead": status.get("toolhead"),
        # Single carriage + INDX: the tool on the head is save_variables.active_tool
        "indx": {
            "tool_positions": status.get("gcode_macro TOOL_POSITIONS"),
            "toolchange_vars": status.get("gcode_macro _TOOLCHANGE_VARS"),
            "plr_state": status.get("gcode_macro _PLR_STATE"),
            "load_cell_probe": status.get("load_cell_probe"),
        },
        "gcode_move": status.get("gcode_move"),
        "pause_resume": status.get("pause_resume"),
        "heaters": {},
        "fans": {},
        "temperature_sensors": {},
        "bed_mesh": status.get("bed_mesh"),
        "save_variables": status.get("save_variables"),
        "display_status": status.get("display_status"),
        "idle_timeout": status.get("idle_timeout"),
        "webhooks": status.get("webhooks"),
        "warnings": [],
    }
    for name, value in status.items():
        if value is None:
            continue
        if name == "heater_bed" or name.startswith("extruder") or name.startswith("heater_generic "):
            snapshot["heaters"][name] = value
        elif name == "fan" or name.startswith("fan_generic "):
            snapshot["fans"][name] = value
        elif name.startswith("temperature_sensor "):
            snapshot["temperature_sensors"][name] = value

    state = str(ps.get("state") or "")
    filename = str(ps.get("filename") or "")
    is_active = bool(vsd.get("is_active"))
    if gcode_path is not None:
        snapshot["file"] = file_fingerprint(gcode_path, position)
        snapshot["file"]["context"] = gcode_context(gcode_path, position)

    if state in {"printing", "paused"} and filename and position > 0:
        snapshot["recoverable"] = True
        snapshot["reason"] = "active virtual_sdcard print snapshot"
    elif state in {"complete", "cancelled", "error"} and filename:
        snapshot["reason"] = f"terminal print state: {state}"
    elif is_active and filename and position > 0:
        snapshot["recoverable"] = True
        snapshot["reason"] = "virtual_sdcard active even though print_stats is not printing"
        snapshot["warnings"].append(f"unexpected print_stats.state={state!r}")
    else:
        snapshot["reason"] = f"not an active print: state={state!r}"
    return snapshot


def write_snapshot(state_dir: Path, snapshot: dict[str, Any], history_max_bytes: int) -> None:
    latest = state_dir / "codex_plr_latest.json"
    last_recoverable = state_dir / "codex_plr_last_recoverable.json"
    heartbeat = state_dir / "codex_plr_heartbeat.json"
    history = state_dir / "codex_plr_history.jsonl"
    terminal = state_dir / "codex_plr_last_terminal.json"

    atomic_write_json(heartbeat, {"schema": "codex.ratrig.indx.plr.heartbeat.v1", "last_poll": utc_now()})

    reason = str(snapshot.get("reason") or "")
    ps = snapshot.get("print_stats") or {}
    state = str(ps.get("state") or "")
    filename = str(ps.get("filename") or "")

    if snapshot.get("recoverable"):
        atomic_write_json(latest, snapshot)
        atomic_write_json(last_recoverable, snapshot)
        append_jsonl(history, snapshot, history_max_bytes)
    elif state in {"complete", "cancelled"} and filename:
        atomic_write_json(latest, snapshot)
        atomic_write_json(terminal, snapshot)
        append_jsonl(history, snapshot, history_max_bytes)
    elif state == "error" and filename:
        atomic_write_json(terminal, snapshot)
        append_jsonl(history, snapshot, history_max_bytes)
        if not latest.exists():
            atomic_write_json(latest, snapshot)
    else:
        idle_snapshot = dict(snapshot)
        idle_snapshot["schema"] = "codex.ratrig.indx.plr.non_printing.v1"
        atomic_write_json(state_dir / "codex_plr_last_non_printing.json", idle_snapshot)


def run(args: argparse.Namespace) -> int:
    state_dir = Path(args.state_dir).expanduser()
    gcodes_dir = Path(args.gcodes_dir).expanduser()
    consecutive_errors = 0
    objects = build_object_query_list(args.moonraker, args.timeout)
    while True:
        try:
            status = moonraker_query(args.moonraker, objects, args.timeout)
            snapshot = compact_status(status, gcodes_dir, args.interval, objects)
            write_snapshot(state_dir, snapshot, args.history_max_bytes)
            remove_file_if_exists(state_dir / "codex_plr_error.json")
            if args.once:
                print(json.dumps(snapshot, indent=2, sort_keys=True))
                return 0
            consecutive_errors = 0
        except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError) as exc:
            consecutive_errors += 1
            error_doc = {
                "schema": "codex.ratrig.indx.plr.error.v1",
                "created_at": utc_now(),
                "error": str(exc),
                "consecutive_errors": consecutive_errors,
            }
            atomic_write_json(state_dir / "codex_plr_error.json", error_doc)
            if args.once:
                print(json.dumps(error_doc, indent=2, sort_keys=True), file=sys.stderr)
                return 1
        time.sleep(args.interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--moonraker", default="http://127.0.0.1:7125")
    parser.add_argument("--state-dir", default="~/printer_data/config/codex_plr")
    parser.add_argument("--gcodes-dir", default="~/printer_data/gcodes")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument("--history-max-bytes", type=int, default=20_000_000)
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
