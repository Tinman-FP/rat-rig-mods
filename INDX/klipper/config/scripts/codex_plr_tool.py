#!/usr/bin/env python3
"""Read Rat Rig INDX PLR snapshots and generate a conservative recovery plan.

DRAFT, not run on the printer. Adapted from the IDEX version (repo commit 277d85e):
one carriage and one [extruder], the tool on the head is INDX's saved active_tool,
and the staged plan restores Z from the snapshot, lifts, homes X/Y only and never
homes Z (Z homing fetches T0 and probes at the bed centre, into the part).
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = Path(os.environ.get("CODEX_PLR_STATE_DIR", "~/printer_data/config/codex_plr")).expanduser()
GCODE_ROOT = Path(os.environ.get("CODEX_PLR_GCODE_ROOT", "~/printer_data/gcodes")).expanduser()
VARIABLES_FILE = Path(
    os.environ.get("CODEX_PLR_VARIABLES_FILE", "~/printer_data/config/variables.cfg")
).expanduser()
PLR_DIR = GCODE_ROOT / ".plr"
LOCKED_RUNFILE = PLR_DIR / "plr.gcode"
PLAN_FILE = PLR_DIR / "codex_plr_plan.gcode"
REPORT_FILE = STATE_DIR / "codex_plr_precheck_report.txt"
PRECHECK_FILE = STATE_DIR / "codex_plr_precheck.json"

SNAPSHOT_SCHEMA = "codex.ratrig.indx.plr.snapshot.v1"
PRECHECK_SCHEMA = "codex.ratrig.indx.plr.precheck.v1"

# Fallbacks when the snapshot has no TOOL_POSITIONS / _PLR_STATE (INDX_Tools.cfg, PLR.cfg)
DEFAULT_TOOL_COUNT = 5
DEFAULT_CLEARANCE_Y = 0.0  # docks at the front (Y -40); the head is clear of them at Y >= 0
DEFAULT_LIFT_MM = 10.0
TRAVEL_FEEDRATE = 6000
Z_FEEDRATE = 600
GAP_CHECK_MM = 1.0  # stop this far above the saved Z and measure the gap by hand
OFFSET_TOLERANCE_MM = 0.05
Z_AGREE_MM = 1.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.monotonic_ns()}.tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def parse_value(raw: str) -> Any:
    raw = raw.strip()
    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError):
        pass
    if raw == "True":
        return True
    if raw == "False":
        return False
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw.strip("'\"")


def parse_saved_variables(path: Path | None = None) -> dict[str, Any]:
    path = VARIABLES_FILE if path is None else path
    values: dict[str, Any] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("[") or " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        values[key.strip()] = parse_value(value)
    return values


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def snapshot_variables(snapshot: dict[str, Any]) -> dict[str, Any]:
    save_variables = snapshot.get("save_variables") or {}
    values = save_variables.get("variables") or {}
    return values if isinstance(values, dict) else {}


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def coord(value: Any) -> list[float] | None:
    """Moonraker sends positions as [x, y, z, e]."""
    if isinstance(value, dict):
        return [as_float(value.get(axis)) for axis in "xyze"]
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        vals = [as_float(v) for v in value[:4]]
        while len(vals) < 4:
            vals.append(0.0)
        return vals
    return None


def tool_name(tool: int | None) -> str:
    return f"T{tool}" if tool is not None and tool >= 0 else "none"


def latch_name(state: int | None) -> str:
    return {0: "locked", 2: "open"}.get(state, "unknown") if state is not None else "not recorded"


def plr_record(values: dict[str, Any]) -> dict[str, Any]:
    """The layer checkpoint PLR_SNAPSHOT saves as one dict (save_variables plr_snapshot)."""
    record = values.get("plr_snapshot")
    return record if isinstance(record, dict) else {}


def head_tool_state(values: dict[str, Any]) -> dict[str, Any]:
    """INDX's saved tool state: active_tool (-1 empty), toolhead_state (0 locked, 2 open), seat_suspect."""
    return {
        "active_tool": as_int(values["active_tool"], -1) if "active_tool" in values else None,
        "toolhead_state": as_int(values["toolhead_state"], -1) if "toolhead_state" in values else None,
        "seat_suspect": as_int(values.get("seat_suspect", -1), -1),
    }


def tool_offsets_from_variables(values: dict[str, Any], tool: int | None) -> dict[str, float] | None:
    """What INDX applies at pickup: X/Y = tN_offset, Z = tN_offset_z + global_z_offset."""
    if tool is None or tool < 0:
        return None
    if not any(f"t{tool}_offset_{axis}" in values for axis in "xyz"):
        return None
    tool_z = as_float(values.get(f"t{tool}_offset_z"))
    global_z = as_float(values.get("global_z_offset"))
    return {
        "x": as_float(values.get(f"t{tool}_offset_x")),
        "y": as_float(values.get(f"t{tool}_offset_y")),
        "z": tool_z + global_z,
        "tool_z": tool_z,
        "global_z": global_z,
    }


def indx_snapshot_state(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Single head + active tool as recorded in one monitor snapshot."""
    values = snapshot_variables(snapshot)
    record = plr_record(values)
    toolhead = snapshot.get("toolhead") or {}
    gcode_move = snapshot.get("gcode_move") or {}
    ps = snapshot.get("print_stats") or {}
    indx = snapshot.get("indx") or {}
    tool_positions = indx.get("tool_positions") or {}
    plr_state = indx.get("plr_state") or {}

    homed = str(toolhead.get("homed_axes") or "")
    pos = coord(toolhead.get("position"))
    if pos is not None:
        head = {"x": pos[0], "y": pos[1], "z": pos[2], "known": all(a in homed for a in "xyz"),
                "source": "toolhead.position"}
    elif record:
        head = {"x": as_float(record.get("x")), "y": as_float(record.get("y")), "z": as_float(record.get("z")),
                "known": truthy(record.get("known")), "source": "save_variables.plr_snapshot"}
    else:
        head = {"x": 0.0, "y": 0.0, "z": 0.0, "known": False, "source": "missing"}

    gpos = coord(gcode_move.get("gcode_position"))
    if gpos is None and record:
        gpos = [as_float(record.get(k)) for k in ("gx", "gy", "gz", "e")]
    gcode = {"x": gpos[0], "y": gpos[1], "z": gpos[2], "e": gpos[3]} if gpos else None

    state = head_tool_state(values)
    tool = state["active_tool"]
    tool_source = "save_variables.active_tool"
    if tool is None and "tool" in record:
        tool = as_int(record.get("tool"), -1)
        tool_source = "save_variables.plr_snapshot"
    if tool is None:
        tool_source = "missing"
    latch = state["toolhead_state"]
    if latch is None and "latch" in record:
        latch = as_int(record.get("latch"), -1)

    tool_offsets = tool_offsets_from_variables(values, tool)
    origin = coord(gcode_move.get("homing_origin"))
    offset_source = "gcode_move.homing_origin"
    if origin is None and record and "oz" in record:
        origin = [as_float(record.get(k)) for k in ("ox", "oy", "oz")] + [0.0]
        offset_source = "save_variables.plr_snapshot"
    if origin is None and tool_offsets:
        origin = [tool_offsets["x"], tool_offsets["y"], tool_offsets["z"], 0.0]
        offset_source = "variables tN_offset + global_z_offset"
    offset = {"x": origin[0], "y": origin[1], "z": origin[2], "source": offset_source} if origin else None

    layer = (ps.get("info") or {}).get("current_layer")
    if layer is None and "layer" in record:
        layer = record.get("layer")
    axis_max = coord(toolhead.get("axis_maximum"))
    bed_mesh = snapshot.get("bed_mesh") or {}
    mesh_matrix = bed_mesh.get("mesh_matrix") or []
    return {
        "tool": tool if tool is not None else -1,
        "tool_known": tool is not None,
        "tool_source": tool_source,
        "toolhead_state": latch,
        "seat_suspect": state["seat_suspect"],
        "head": head,
        "gcode": gcode,
        "offset": offset,
        "tool_offsets": tool_offsets,
        "macro_record": record,
        "layer": as_int(layer, -1) if layer is not None else None,
        "z_max": axis_max[2] if axis_max else None,
        "tool_count": as_int(tool_positions.get("tool_count"), DEFAULT_TOOL_COUNT),
        "clearance_y": as_float(tool_positions.get("clearance_y"), DEFAULT_CLEARANCE_Y)
        if "clearance_y" in tool_positions else DEFAULT_CLEARANCE_Y,
        "no_heat_tools": list(tool_positions.get("no_heat_tools") or []),
        "resume_lift": as_float(plr_state.get("resume_lift"), DEFAULT_LIFT_MM)
        if "resume_lift" in plr_state else DEFAULT_LIFT_MM,
        "bed_mesh_profile": str(bed_mesh.get("profile_name") or ""),
        "bed_mesh_active": bool(mesh_matrix and isinstance(mesh_matrix, list) and mesh_matrix[0]),
    }


def tool_check_errors(recorded_tool: int, tool_count: int, now: dict[str, Any]) -> list[str]:
    """Same refusals as PLR_VERIFY_TOOL in PLR.cfg, against the variables file as it is now."""
    act = now.get("active_tool")
    latch = now.get("toolhead_state")
    suspect = now.get("seat_suspect", -1)
    if recorded_tool < 0:
        return ["the snapshot recorded no tool on the head (power lost during a tool change?): re-slice instead"]
    if tool_count > 0 and recorded_tool >= tool_count:
        return [f"recorded tool T{recorded_tool} is not configured ({tool_count} tools)"]
    errors = []
    if suspect is not None and suspect >= 0:
        errors.append(
            f"seat_suspect is set (T{suspect} may be half seated): check the head by hand, then "
            "MANUAL_TOOL_REMOVE or MANUAL_TOOL_SEAT TOOL=<n>"
        )
    if act is None:
        errors.append("active_tool is missing from the variables file: INDX does not know what is on the head")
    elif act < 0:
        errors.append(f"no tool on the head now (active_tool=-1); the snapshot needs T{recorded_tool}")
    elif act != recorded_tool:
        errors.append(f"tool mismatch: the snapshot was printed with T{recorded_tool}, active_tool says T{act} is on the head")
    if latch != 0:
        errors.append(f"the latch is not recorded as locked (toolhead_state={latch_name(latch)})")
    return errors


def load_snapshot(path: Path) -> dict[str, Any]:
    with path.expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_best_available_snapshot(path: Path) -> tuple[dict[str, Any] | None, Path | None]:
    expanded = path.expanduser()
    if expanded.exists():
        return load_snapshot(expanded), expanded
    state_dir = expanded.parent
    for fallback in [
        "codex_plr_last_terminal.json",
        "codex_plr_last_non_printing.json",
        "codex_plr_heartbeat.json",
    ]:
        candidate = state_dir / fallback
        if candidate.exists():
            return load_snapshot(candidate), candidate
    return None, None


def load_recoverable_snapshot(path: Path) -> tuple[dict[str, Any] | None, Path | None]:
    snapshot, source = load_best_available_snapshot(path)
    if snapshot and snapshot.get("recoverable"):
        return snapshot, source
    candidate = path.expanduser().parent / "codex_plr_last_recoverable.json"
    if candidate.exists():
        last = load_snapshot(candidate)
        if last.get("recoverable"):
            return last, candidate
    return snapshot, source


def fmt_temp(obj: dict[str, Any] | None) -> str:
    if not obj:
        return "n/a"
    return f"{float(obj.get('temperature', 0.0)):.1f}/{float(obj.get('target', 0.0)):.1f}C"


def fmt_xyz(obj: dict[str, Any] | None, digits: int = 2) -> str:
    if not obj:
        return "n/a"
    return " ".join(f"{axis.upper()}={as_float(obj.get(axis)):.{digits}f}" for axis in "xyz")


def status_text(snapshot: dict[str, Any]) -> str:
    ps = snapshot.get("print_stats") or {}
    vsd = snapshot.get("virtual_sdcard") or {}
    file_info = snapshot.get("file") or {}
    toolhead = snapshot.get("toolhead") or {}
    heaters = snapshot.get("heaters") or {}
    capture = snapshot.get("capture") or {}
    st = indx_snapshot_state(snapshot)
    gcode = st["gcode"]
    lines = [
        f"Snapshot: {snapshot.get('created_at', 'unknown')}",
        f"Recoverable: {bool(snapshot.get('recoverable'))} ({snapshot.get('reason', '')})",
        f"Capture interval: {capture.get('poll_interval_seconds', 'n/a')}s",
        f"File: {ps.get('filename') or file_info.get('path') or 'n/a'}",
        f"Byte position: {vsd.get('file_position', 0)} / {vsd.get('file_size', 0)}",
        f"Progress: {float(vsd.get('progress') or 0.0) * 100:.2f}%",
        f"Layer: {(ps.get('info') or {}).get('current_layer')} / {(ps.get('info') or {}).get('total_layer')}",
        f"Homed axes: {toolhead.get('homed_axes', '')}",
        (
            f"Recorded tool: {tool_name(st['tool'])} (from {st['tool_source']}), "
            f"latch {latch_name(st['toolhead_state'])}, seat_suspect {tool_name(st['seat_suspect'])}"
        ),
        f"Head position (machine): {fmt_xyz(st['head'])} known={st['head']['known']}",
        (
            f"G-code position: {fmt_xyz(gcode, 3)} E={as_float(gcode.get('e')):.4f}"
            if gcode else "G-code position: n/a"
        ),
        f"G-code offset in effect: {fmt_xyz(st['offset'], 3)}",
        f"Tool offsets from variables: {fmt_xyz(st['tool_offsets'], 3)}",
        f"Bed: {fmt_temp(heaters.get('heater_bed'))}",
        f"Hotend (extruder): {fmt_temp(heaters.get('extruder'))}",
    ]
    extra_heaters = [
        f"{name}: {fmt_temp(obj)}"
        for name, obj in sorted(heaters.items())
        if name not in {"heater_bed", "extruder"}
    ]
    if extra_heaters:
        lines.append("Additional heaters:")
        lines.extend(f"- {line}" for line in extra_heaters)
    warnings = snapshot.get("warnings") or []
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in warnings)
    context = (file_info.get("context") or {})
    previous_lines = context.get("previous_lines") or []
    next_lines = context.get("next_lines") or []
    if previous_lines or next_lines:
        lines.append("G-code context near saved byte:")
        for line in previous_lines[-3:]:
            lines.append(f"  before: {line}")
        for line in next_lines[:3]:
            lines.append(f"  next:   {line}")
    return "\n".join(lines)


def gcode_filename(snapshot: dict[str, Any]) -> str:
    ps = snapshot.get("print_stats") or {}
    return str(ps.get("filename") or "")


def build_refused_plan(snapshot: dict[str, Any], errors: list[str]) -> str:
    lines = [
        "; Codex Rat Rig INDX PLR recovery plan: REFUSED",
        "; DRAFT, not run on the printer.",
        f"; Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"; Source file: {gcode_filename(snapshot) or 'n/a'}",
        "; The precheck failed, so no recovery steps are written:",
        *[f"; - {error}" for error in errors],
        "M118 Codex PLR plan refused: precheck failed, see codex_plr_precheck_report.txt",
        "",
    ]
    return "\n".join(lines)


def build_plan(snapshot: dict[str, Any], lift: float | None = None) -> str:
    """Staged plan. Only the tool guard and the bed target are live; every move stays commented."""
    vsd = snapshot.get("virtual_sdcard") or {}
    gcode_move = snapshot.get("gcode_move") or {}
    heaters = snapshot.get("heaters") or {}
    fans = snapshot.get("fans") or {}
    file_info = snapshot.get("file") or {}
    context = file_info.get("context") or {}
    st = indx_snapshot_state(snapshot)
    lift = st["resume_lift"] if lift is None else lift
    filename = gcode_filename(snapshot)
    pos = int(vsd.get("file_position") or 0)
    tool = st["tool"]
    head = st["head"]
    gcode = st["gcode"] or {"x": head["x"], "y": head["y"], "z": head["z"], "e": 0.0}
    offset = st["offset"] or {"x": 0.0, "y": 0.0, "z": 0.0, "source": "none"}
    bed_target = float((heaters.get("heater_bed") or {}).get("target") or 0.0)
    hotend_target = float((heaters.get("extruder") or {}).get("target") or 0.0)
    chamber_targets = [
        f"{name.split(' ', 1)[1]}={float((obj or {}).get('target') or 0.0):.1f}C"
        for name, obj in sorted(heaters.items())
        if name.startswith("heater_generic ")
    ]
    speed_factor = float(gcode_move.get("speed_factor") or 1.0)
    extrude_factor = float(gcode_move.get("extrude_factor") or 1.0)
    absolute_coordinates = bool(gcode_move.get("absolute_coordinates", True))
    absolute_extrude = bool(gcode_move.get("absolute_extrude", True))
    kin_z = head["z"]
    lifted_z = kin_z + lift
    # The lifted height in G-code coordinates once the tool offset is back on
    lifted_gcode_z = lifted_z - offset["z"]
    check_z = gcode["z"] + GAP_CHECK_MM

    fan_lines = []
    for name, obj in fans.items():
        if not obj or "speed" not in obj:
            continue
        speed = float(obj.get("speed") or 0.0)
        if name == "fan":
            fan_lines.append(f"; M106 S{round(speed * 255)}")
        elif name.startswith("fan_generic "):
            fan = name.split(" ", 1)[1]
            fan_lines.append(f"; SET_FAN_SPEED FAN={fan} SPEED={speed:.3f}")

    validation_lines = [
        "; Validation snapshot:",
        f"; - File exists: {file_info.get('exists')}",
        f"; - Snapshot file size: {file_info.get('size', 'n/a')}",
        f"; - VSD file size: {vsd.get('file_size', 'n/a')}",
        f"; - Head hash: {file_info.get('sha256_head_64k', 'n/a')}",
        f"; - Near-position hash: {file_info.get('sha256_near_position_64k', 'n/a')}",
        f"; - Tail hash: {file_info.get('sha256_tail_64k', 'n/a')}",
        f"; - Line start before/at saved byte: {context.get('line_start_before_or_at_position')}",
        f"; - Next line start after saved byte: {context.get('next_line_start_after_position')}",
    ]
    previous_lines = context.get("previous_lines") or []
    next_lines = context.get("next_lines") or []
    if previous_lines or next_lines:
        validation_lines.append("; G-code context:")
        for line in previous_lines[-3:]:
            validation_lines.append(f";   before: {line}")
        for line in next_lines[:3]:
            validation_lines.append(f";   next:   {line}")

    if hotend_target > 0 and tool not in st["no_heat_tools"]:
        heat_lines = [f"; M104 S{hotend_target:.1f}", f"; M109 S{hotend_target:.1f}"]
    else:
        heat_lines = ["; - no hotend target recorded for this tool: nothing to heat"]

    lines = [
        "; Codex Rat Rig INDX PLR staged recovery plan",
        "; DRAFT, not run on the printer.",
        f"; Generated: {datetime.now().isoformat(timespec='seconds')}",
        "; This is intentionally not an automatic resume.",
        "; Host-side state only: Z comes from the last snapshot, not from MCU-flashed stepper state.",
        "",
        f"; Source file: {filename}",
        f"; Saved byte position: {pos}",
        f"; Saved layer: {st['layer']}",
        f"; Recorded tool: {tool_name(tool)} (latch {latch_name(st['toolhead_state'])})",
        f"; Head at snapshot (machine): {fmt_xyz(head, 3)}",
        f"; G-code position at snapshot: {fmt_xyz(gcode, 3)} E={as_float(gcode.get('e')):.5f}",
        f"; G-code offset in effect: {fmt_xyz(offset, 3)} (from {offset['source']})",
        f"; Saved offsets for {tool_name(tool)} (variables): {fmt_xyz(st['tool_offsets'], 3)}",
        f"; Lift before X/Y homing: {lift:.1f} mm, to machine Z {lifted_z:.3f} (Z max {st['z_max']})",
        f"; Bed mesh at snapshot: {st['bed_mesh_profile'] or ('active, no profile name' if st['bed_mesh_active'] else 'none')}",
        "",
        *validation_lines,
        "",
        f"; Stage 1 (runs): refuse unless {tool_name(tool)} is on the head. No motion, no hotend heat.",
        f"PLR_VERIFY_TOOL TOOL={tool}",
        f"M140 S{bed_target:.1f}",
        f"; - chamber targets were {', '.join(chamber_targets) or 'n/a'}: set them with the chamber macros if needed",
        "",
        "; ===== STOP. Everything below is commented out on purpose. =====",
        "; Physical checks first:",
        "; - the part is still bonded and nothing is loose on the bed",
        f"; - {tool_name(tool)} is the tool on the head and fully latched (TOOL_STATUS, and look at it)",
        "; - the head is over the print, not at the docks",
        "; - the nozzle is not fused into the part (if it is, heat it with the step 4 lines first)",
        "; - the path to the rear stop is clear at the lifted height",
        "; - the file hashes/context above still match the printed file",
        "; - do not home Z: Z homing fetches T0 and probes at the bed centre, into the part",
        "; - no tool change: T<n> / CHANGE_TOOL would park and fetch tools over the part",
        "",
        "; Step 1: restore Z from the snapshot (X and Y stay unhomed), then lift the nozzle off the part.",
        "; SET_GCODE_OFFSET X=0 Y=0 Z=0 MOVE=0",
        f"; SET_KINEMATIC_POSITION Z={kin_z:.3f} SET_HOMED=Z",
        "; G91",
        f"; G1 Z{lift:.3f} F{Z_FEEDRATE}",
        "; G90",
        "; Step 2: home X and Y only (Y to the rear stop, then X to the left, at the lifted height).",
        "; G28 X Y",
        f"; Step 3: put {tool_name(tool)}'s offsets back as they were at the snapshot (no tool change).",
        f"; SET_GCODE_OFFSET X={offset['x']:.3f} Y={offset['y']:.3f} Z={offset['z']:.3f} MOVE=0",
        f"; Step 4: heat {tool_name(tool)}. M104/M109 only heat a tool recorded on the head, so check again first.",
        f"; PLR_VERIFY_TOOL TOOL={tool}",
        *heat_lines,
        "; - prime by hand at the rear, clear of the part, and remove the string",
        "; Step 5: go over the saved point at the lifted height, stop 1 mm above the saved Z and measure.",
        "; G90",
        f"; G1 Z{lifted_gcode_z:.3f} F{Z_FEEDRATE}",
        f"; G1 X{gcode['x']:.3f} Y{gcode['y']:.3f} F{TRAVEL_FEEDRATE}",
        f"; G1 Z{check_z:.3f} F{Z_FEEDRATE}",
        f"; - the gap to the top layer must be about {GAP_CHECK_MM:.1f} mm. If not, stop, or correct it with",
        ";   SET_GCODE_OFFSET Z_ADJUST=<mm> before going lower",
        f"; G1 Z{gcode['z']:.3f} F{Z_FEEDRATE}",
        "; Step 6: restore the print state and resume at the saved byte.",
        "; G90" if absolute_coordinates else "; G91",
        "; M82" if absolute_extrude else "; M83",
        f"; G92 E{as_float(gcode.get('e')):.5f}",
        f"; M220 S{speed_factor * 100:.1f}",
        f"; M221 S{extrude_factor * 100:.1f}",
        *fan_lines,
        f"; M23 {filename}",
        f"; M26 S{pos}",
        "; M24",
    ]
    return "\n".join(lines) + "\n"


def resolve_existing_gcode_path(snapshot: dict[str, Any]) -> Path | None:
    ps = snapshot.get("print_stats") or {}
    file_info = snapshot.get("file") or {}
    candidates: list[Path] = []
    file_path = file_info.get("path")
    if file_path:
        candidates.append(Path(str(file_path)))
    filename = ps.get("filename")
    if filename:
        candidates.append(GCODE_ROOT / str(filename))
    for candidate in candidates:
        candidate = candidate.expanduser()
        if candidate.exists() and candidate.is_file():
            return candidate
    return candidates[0].expanduser() if candidates else None


def validate_precheck(snapshot: dict[str, Any], source_path: Path | None, lift: float | None = None) -> dict[str, Any]:
    snap_values = snapshot_variables(snapshot)
    now_values = parse_saved_variables()
    values = dict(snap_values)
    values.update(now_values)

    ps = snapshot.get("print_stats") or {}
    vsd = snapshot.get("virtual_sdcard") or {}
    file_info = snapshot.get("file") or {}
    filename = str(ps.get("filename") or Path(str(file_info.get("path") or "")).name)
    byte_position = int(vsd.get("file_position") or 0)
    file_size = int(vsd.get("file_size") or file_info.get("size") or 0)
    interrupted = truthy(values.get("was_interrupted"))
    gcode_path = resolve_existing_gcode_path(snapshot)
    st = indx_snapshot_state(snapshot)
    now = head_tool_state(now_values)
    lift = st["resume_lift"] if lift is None else lift
    head = st["head"]
    z = head["z"]

    errors: list[str] = []
    warnings: list[str] = [
        "Host-side PLR state does not prove physical nozzle, XY, or Z clearance.",
        "CODEX_PLR_START remains locked until a supervised recovery-start workflow is installed.",
        "active_tool is saved state, not a sensor: look at the head before trusting it.",
    ]
    if snapshot.get("schema") != SNAPSHOT_SCHEMA or snapshot.get("dual_carriage"):
        errors.append(
            f"snapshot schema {snapshot.get('schema')!r} is not the INDX schema (left over from the IDEX machine?)"
        )
    if not interrupted:
        errors.append("no interrupted print is recorded in save_variables.was_interrupted")
    if not snapshot.get("recoverable"):
        errors.append(f"snapshot is not recoverable: {snapshot.get('reason', 'no reason recorded')}")
    if not filename:
        errors.append("snapshot has no print filename")
    if byte_position <= 0:
        errors.append("snapshot has no positive virtual_sdcard byte position")
    if file_size > 0 and byte_position > file_size:
        errors.append(f"saved byte position {byte_position} exceeds file size {file_size}")
    if st["layer"] is not None and st["layer"] < 1:
        errors.append(f"snapshot is from before layer 1 (layer {st['layer']}): start the print again")
    if not head["known"]:
        errors.append("the head was not homed in X, Y and Z when the snapshot was taken")
    if z <= 0:
        errors.append("could not derive a positive saved Z height")
    if st["z_max"] is None:
        warnings.append("snapshot has no toolhead.axis_maximum: check saved Z + lift is below Z max by hand")
    elif z + lift > st["z_max"]:
        errors.append(f"saved Z {z:.3f} + lift {lift:.1f} is above Z max {st['z_max']:.1f}")
    if head["y"] < st["clearance_y"]:
        errors.append(
            f"the head was at the docks (Y {head['y']:.2f}, below clearance_y {st['clearance_y']:.2f}) "
            "when the snapshot was taken: a tool change was running"
        )
    if st["toolhead_state"] is not None and st["toolhead_state"] != 0:
        errors.append(f"the latch was {latch_name(st['toolhead_state'])} in the snapshot: a tool change was running")
    if not VARIABLES_FILE.exists():
        errors.append(f"variables file not found ({VARIABLES_FILE}): INDX tool state is unknown")
    errors.extend(tool_check_errors(st["tool"], st["tool_count"], now))
    if st["offset"] is None:
        errors.append("snapshot has no G-code offset and no saved tool offsets: cannot re-apply the tool offsets")
    if gcode_path is None:
        errors.append("could not identify a G-code source file")
    elif not gcode_path.exists():
        errors.append(f"G-code source file is not present: {gcode_path}")
    if file_info.get("exists") is False:
        warnings.append("the monitor snapshot recorded file.exists=false at capture time")

    record = st["macro_record"]
    if record and "tool" in record and as_int(record.get("tool"), -1) != st["tool"]:
        warnings.append(
            f"the last layer checkpoint has {tool_name(as_int(record.get('tool'), -1))}, the monitor snapshot "
            f"{tool_name(st['tool'])}: the plan uses the monitor value"
        )
    if record and "z" in record and abs(as_float(record.get("z")) - z) > Z_AGREE_MM:
        warnings.append(
            f"the last layer checkpoint Z {as_float(record.get('z')):.3f} and the monitor Z {z:.3f} differ by more "
            f"than {Z_AGREE_MM:.1f} mm: check for a Z hop at the snapshot"
        )
    offset = st["offset"]
    tool_offsets = st["tool_offsets"]
    if offset and tool_offsets and (
        abs(offset["x"] - tool_offsets["x"]) > OFFSET_TOLERANCE_MM
        or abs(offset["y"] - tool_offsets["y"]) > OFFSET_TOLERANCE_MM
    ):
        warnings.append(
            f"the X/Y offset in effect ({offset['x']:.3f}, {offset['y']:.3f}) differs from "
            f"{tool_name(st['tool'])}'s saved offsets ({tool_offsets['x']:.3f}, {tool_offsets['y']:.3f}): "
            "the plan uses the offset in effect"
        )
    if st["bed_mesh_profile"] or st["bed_mesh_active"]:
        warnings.append(
            f"a bed mesh was active ({st['bed_mesh_profile'] or 'no profile name'}) and is gone after the restart: "
            "Z at the resume point is off by the mesh value unless the same mesh is loaded"
        )

    return {
        "schema": PRECHECK_SCHEMA,
        "created_at": utc_now(),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "snapshot_source": str(source_path) if source_path else None,
        "snapshot_created_at": snapshot.get("created_at"),
        "snapshot_reason": snapshot.get("reason"),
        "source_file": str(gcode_path) if gcode_path else None,
        "filename": filename,
        "resume_byte": byte_position,
        "file_size": file_size,
        "resume_z": z,
        "lift_mm": lift,
        "z_max": st["z_max"],
        "recorded_tool": st["tool"],
        "recorded_tool_source": st["tool_source"],
        "recorded_latch": st["toolhead_state"],
        "tool_now": now,
        "head": head,
        "gcode_position": st["gcode"],
        "gcode_offset": st["offset"],
        "tool_offsets": st["tool_offsets"],
        "saved_was_interrupted": interrupted,
        "saved_layer": st["layer"],
        "context": (file_info.get("context") or {}),
        "fingerprint": {
            "sha256_head_64k": file_info.get("sha256_head_64k"),
            "sha256_near_position_64k": file_info.get("sha256_near_position_64k"),
            "sha256_tail_64k": file_info.get("sha256_tail_64k"),
        },
        "start_locked": True,
    }


def precheck_report_text(state: dict[str, Any], snapshot: dict[str, Any]) -> str:
    now = state.get("tool_now") or {}
    lines = [
        "Codex Rat Rig INDX PLR precheck",
        f"Created: {state['created_at']}",
        f"OK: {state['ok']}",
        f"Snapshot: {state.get('snapshot_source') or 'n/a'}",
        f"Snapshot reason: {state.get('snapshot_reason') or 'n/a'}",
        f"Source: {state.get('source_file') or 'n/a'}",
        f"Resume byte: {state['resume_byte']} / {state['file_size']}",
        f"Resume Z (machine): {state['resume_z']}",
        f"Lift: {state['lift_mm']} mm (Z max {state.get('z_max')})",
        f"Saved layer: {state.get('saved_layer')}",
        (
            f"Recorded tool: {tool_name(state.get('recorded_tool'))} "
            f"(from {state.get('recorded_tool_source')}, latch {latch_name(state.get('recorded_latch'))})"
        ),
        (
            f"Tool on the head now: {tool_name(now.get('active_tool'))}, latch {latch_name(now.get('toolhead_state'))}, "
            f"seat_suspect {tool_name(now.get('seat_suspect'))}"
        ),
        f"Head at snapshot (machine): {fmt_xyz(state.get('head'))}",
        f"G-code offset in effect: {fmt_xyz(state.get('gcode_offset'), 3)}",
        f"was_interrupted: {state['saved_was_interrupted']}",
        "",
    ]
    if state["errors"]:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in state["errors"])
        lines.append("")
    if state["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in state["warnings"])
        lines.append("")
    context = state.get("context") or {}
    previous_lines = context.get("previous_lines") or []
    next_lines = context.get("next_lines") or []
    if previous_lines or next_lines:
        lines.append("G-code context:")
        for line in previous_lines[-5:]:
            lines.append(f"  before: {line}")
        for line in next_lines[:5]:
            lines.append(f"  next:   {line}")
        lines.append("")
    lines.extend(
        [
            "Locked output:",
            f"- {LOCKED_RUNFILE}",
            f"- {PLAN_FILE}",
            "",
            "The locked runfile contains no movement. Review the plan, verify the part, the tool on",
            "the head and the travel corridor physically, then work through the staged steps by hand.",
            "Never home Z with the part on the bed.",
            "",
            "Snapshot summary:",
            status_text(snapshot),
        ]
    )
    return "\n".join(lines) + "\n"


def write_locked_runfile(state: dict[str, Any]) -> None:
    head = state.get("head") or {}
    text = "\n".join(
        [
            "; Codex Rat Rig INDX PLR locked runfile",
            f"; Generated: {state['created_at']}",
            "; This file intentionally contains no movement.",
            "; Run CODEX_PLR_PRECHECK and complete physical/Z validation before any resume.",
            f"; Source: {state.get('source_file') or 'n/a'}",
            f"; Resume byte: {state['resume_byte']}",
            f"; Resume Z: {state['resume_z']}",
            f"; Recorded tool: {tool_name(state.get('recorded_tool'))}",
            f"; Head: X={as_float(head.get('x')):.2f} Y={as_float(head.get('y')):.2f} "
            f"Z={as_float(head.get('z')):.2f} known={bool(head.get('known'))}",
            "M118 Codex PLR locked: precheck recorded state, but motion is disabled.",
            "",
        ]
    )
    atomic_write(LOCKED_RUNFILE, text)


def write_precheck_outputs(state: dict[str, Any], snapshot: dict[str, Any]) -> None:
    atomic_write_json(PRECHECK_FILE, state)
    atomic_write(REPORT_FILE, precheck_report_text(state, snapshot))
    write_locked_runfile(state)
    if state["ok"]:
        atomic_write(PLAN_FILE, build_plan(snapshot, state["lift_mm"]))
    else:
        atomic_write(PLAN_FILE, build_refused_plan(snapshot, state["errors"]))


def archive_state_files(state_dir: Path) -> Path:
    archive_dir = state_dir / "archive" / datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ("codex_plr_*.json*", "codex_plr_*.txt", "codex_plr_*.gcode"):
        for candidate in state_dir.glob(pattern):
            if candidate.is_file():
                shutil.copy2(candidate, archive_dir / candidate.name)
    for candidate in (PLAN_FILE, LOCKED_RUNFILE):
        if candidate.exists():
            shutil.copy2(candidate, archive_dir / candidate.name)
    if VARIABLES_FILE.exists():
        shutil.copy2(VARIABLES_FILE, archive_dir / VARIABLES_FILE.name)
    return archive_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        default=str(STATE_DIR / "codex_plr_latest.json"),
        help="Path to codex_plr_latest.json",
    )
    parser.add_argument(
        "--lift",
        type=float,
        default=None,
        help="Z lift in mm before X/Y homing (default: _PLR_STATE resume_lift, else 10)",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("precheck")
    plan = sub.add_parser("make-plan")
    plan.add_argument("--output", default=str(PLAN_FILE))
    sub.add_parser("archive")
    clear = sub.add_parser("clear")
    clear.add_argument("--yes", action="store_true", help="required confirmation")
    args = parser.parse_args()

    snapshot_path = Path(args.snapshot)
    if args.command == "archive":
        archive = archive_state_files(snapshot_path.expanduser().parent)
        print(f"Archived PLR state files to {archive}")
        return 0
    if args.command == "clear":
        if not args.yes:
            print("Refusing to clear PLR files without --yes.")
            return 2
        state_dir = snapshot_path.expanduser().parent
        archive = archive_state_files(state_dir)
        for candidate in state_dir.glob("codex_plr_*.json*"):
            candidate.unlink()
        for candidate in [REPORT_FILE, PRECHECK_FILE, PLAN_FILE, LOCKED_RUNFILE]:
            try:
                candidate.unlink()
            except FileNotFoundError:
                pass
        print(f"Archived PLR state to {archive}")
        print("Cleared PLR state files. Use CODEX_PLR_CLEAR in Klipper to clear save_variables.")
        return 0

    snapshot, source_path = (
        load_recoverable_snapshot(snapshot_path)
        if args.command in {"make-plan", "precheck"}
        else load_best_available_snapshot(snapshot_path)
    )
    if snapshot is None:
        print("No PLR snapshot files found yet. The monitor will create one during the next virtual SD print.")
        return 0
    if args.command == "status":
        if source_path is not None and source_path.name != "codex_plr_latest.json":
            print(f"No active recovery snapshot yet; showing {source_path.name}.\n")
        print(status_text(snapshot))
        return 0
    if args.command == "precheck":
        state = validate_precheck(snapshot, source_path, args.lift)
        write_precheck_outputs(state, snapshot)
        print(precheck_report_text(state, snapshot))
        return 0 if state["ok"] else 2
    if args.command == "make-plan":
        if not snapshot.get("recoverable"):
            print("Refusing to write a recovery plan because the latest available snapshot is not recoverable.")
            print(status_text(snapshot))
            return 2
        state = validate_precheck(snapshot, source_path, args.lift)
        if not state["ok"]:
            print("Refusing to write a recovery plan because the precheck failed:")
            for error in state["errors"]:
                print(f"- {error}")
            return 2
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(output, build_plan(snapshot, state["lift_mm"]))
        print(f"Wrote {output}")
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
