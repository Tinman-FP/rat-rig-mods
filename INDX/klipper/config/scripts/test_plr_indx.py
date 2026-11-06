#!/usr/bin/env python3
"""Offline test for the INDX PLR draft. Python 3 stdlib only. DRAFT, not run on the printer.

Every fixture is made up: a fictional Moonraker status, G-code file and
variables.cfg in a temp dir. Nothing talks to a printer or the network.

    python3 test_plr_indx.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG_DIR = HERE.parent
TOOL = HERE / "codex_plr_tool.py"
MONITOR = HERE / "codex_plr_monitor.py"
PLR_CFG = CONFIG_DIR / "PLR.cfg"
PLR_SHELL_CFG = CONFIG_DIR / "PLR_Shell.cfg"
NOTES = CONFIG_DIR / "PLR_INDX_NOTES.md"

GCODE_NAME = "fixture_bracket_PPS-CF.gcode"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


monitor = load_module("codex_plr_monitor_under_test", MONITOR)
tool_module = load_module("codex_plr_tool_under_test", TOOL)
# Keep the real host name out of the fixtures
monitor.socket.gethostname = lambda: "fixture-host"


def write_gcode(path: Path) -> int:
    """Fictional print file. Returns a byte offset at a line start mid-file."""
    lines = ["; fictional fixture file", "G90", "M83"]
    for layer in range(1, 60):
        lines.append(f";LAYER:{layer}")
        lines.append(f"LAYER_CHANGE LAYER={layer}")
        for i in range(8):
            lines.append(f"G1 X{200 + i * 0.5:.3f} Y{188 + i * 0.25:.3f} E0.0312 F3600")
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    marker = "LAYER_CHANGE LAYER=42\n"
    return text.index(marker) + len(marker)


def variables_text(values: dict) -> str:
    """Same layout Klipper's save_variables writes: [Variables], name = repr(value), sorted."""
    lines = ["[Variables]"]
    for name, value in sorted(values.items()):
        lines.append(f"{name} = {value!r}")
    return "\n".join(lines) + "\n"


def base_variables(pos: int, size: int) -> dict:
    return {
        "active_tool": 2,
        "toolhead_state": 0,
        "seat_suspect": -1,
        "global_z_offset": 0.05,
        "t2_offset_x": 0.12,
        "t2_offset_y": -0.08,
        "t2_offset_z": 0.17,
        "t3_offset_x": -0.21,
        "t3_offset_y": 0.31,
        "t3_offset_z": -0.04,
        "tc_mode": "NORMAL",
        "toolchange_count": 41,
        "was_interrupted": True,
        "plr_completed_normally": False,
        "plr_snapshot": {
            "layer": 42, "tool": 2, "latch": 0, "known": 1,
            "x": 201.5, "y": 188.25, "z": 8.62,
            "gx": 201.38, "gy": 188.33, "gz": 8.4, "e": 1520.0,
            "ox": 0.12, "oy": -0.08, "oz": 0.22, "abs_e": 1,
            "bed": 100.0, "hotend": 310.0, "chamber": 60.0,
            "pos": pos - 400, "size": size,
            "file": GCODE_NAME, "path": "/home/pi/printer_data/gcodes/" + GCODE_NAME,
        },
    }


def base_status(gcode_path: Path, pos: int, size: int, variables: dict) -> dict:
    return {
        "print_stats": {"state": "printing", "filename": GCODE_NAME,
                        "info": {"current_layer": 42, "total_layer": 59}},
        "virtual_sdcard": {"file_path": str(gcode_path), "file_position": pos, "file_size": size,
                           "is_active": True, "progress": pos / size},
        "toolhead": {"position": [201.5, 188.25, 8.62, 1520.0], "homed_axes": "xyz",
                     "axis_maximum": [545.0, 488.8, 480.0, 0.0], "extruder": "extruder"},
        "gcode_move": {"gcode_position": [201.38, 188.33, 8.4, 1520.12345],
                       "homing_origin": [0.12, -0.08, 0.22, 0.0],
                       "speed_factor": 1.0, "extrude_factor": 0.98,
                       "absolute_coordinates": True, "absolute_extrude": True},
        "heater_bed": {"temperature": 99.8, "target": 100.0},
        "extruder": {"temperature": 309.6, "target": 310.0},
        "heater_generic chamber_heater1": {"temperature": 59.0, "target": 60.0},
        "fan": {"speed": 0.4},
        "bed_mesh": {"profile_name": "", "mesh_matrix": [[]]},
        "save_variables": {"variables": json.loads(json.dumps(variables))},
        "gcode_macro TOOL_POSITIONS": {"tool_count": 5, "clearance_y": 0.0, "no_heat_tools": []},
        "gcode_macro _TOOLCHANGE_VARS": {"toolhead_state": 0, "homing_busy": 0},
        "gcode_macro _PLR_STATE": {"enabled": 1, "interval": 1, "active": 1, "resume_lift": 10.0},
    }


class Fixture:
    """One temp printer_data tree: gcodes, variables.cfg, codex_plr state dir with a snapshot."""

    def __init__(self, tmp: Path, now_vars=None, snap_vars=None, status_edit=None, snapshot_edit=None):
        self.gcodes = tmp / "gcodes"
        self.state = tmp / "config" / "codex_plr"
        self.variables = tmp / "config" / "variables.cfg"
        self.gcodes.mkdir(parents=True)
        self.state.mkdir(parents=True)
        gcode_path = self.gcodes / GCODE_NAME
        self.pos = write_gcode(gcode_path)
        self.size = gcode_path.stat().st_size

        snap_values = base_variables(self.pos, self.size)
        if snap_vars:
            snap_values.update(snap_vars)
        status = base_status(gcode_path, self.pos, self.size, snap_values)
        if status_edit:
            status_edit(status)
        snapshot = monitor.compact_status(status, self.gcodes, 2.0, sorted(status))
        if snapshot_edit:
            snapshot_edit(snapshot)
        self.snapshot = snapshot
        (self.state / "codex_plr_latest.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

        values = base_variables(self.pos, self.size)
        for key, value in (now_vars or {}).items():
            if value is None:
                values.pop(key, None)
            else:
                values[key] = value
        self.variables.write_text(variables_text(values), encoding="utf-8")

    def run(self, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update({
            "CODEX_PLR_STATE_DIR": str(self.state),
            "CODEX_PLR_GCODE_ROOT": str(self.gcodes),
            "CODEX_PLR_VARIABLES_FILE": str(self.variables),
        })
        return subprocess.run(
            [sys.executable, str(TOOL), "--snapshot", str(self.state / "codex_plr_latest.json"), *args],
            env=env, capture_output=True, text=True, timeout=60,
        )

    @property
    def plan_path(self) -> Path:
        return self.gcodes / ".plr" / "codex_plr_plan.gcode"


# Anything that would home Z, change or park a tool, probe, or use IDEX commands
FORBIDDEN_TOKENS = re.compile(
    r"^(T\d+|CHANGE_TOOL|PARK_TOOL|_INDX_\w+|_PICKUP_\w+|BED_MESH_CALIBRATE|Z_TILT_ADJUST|PROBE\w*|"
    r"CAL_\w+|SET_DUAL_CARRIAGE|ACTIVATE_EXTRUDER|SDCARD_PRINT_FILE)$"
)
STAGED_RE = re.compile(r"^; ([A-Z][A-Z0-9_]*)(?:\s|$)")


def command_lines(plan: str) -> list[tuple[bool, str]]:
    """(live, command) for every live command and every staged ('; CMD ...') command."""
    out = []
    for raw in plan.splitlines():
        line = raw.strip()
        if not line:
            continue
        if not line.startswith(";"):
            out.append((True, line))
        elif STAGED_RE.match(line):
            out.append((False, line[2:].strip()))
    return out


def index_of(commands: list[str], prefix: str, start: int = 0) -> int:
    for i in range(start, len(commands)):
        if commands[i].startswith(prefix):
            return i
    raise AssertionError(f"plan has no command starting with {prefix!r} after index {start}: {commands}")


class PlanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def fixture(self, **kwargs) -> Fixture:
        sub = self.tmp / f"case{len(list(self.tmp.iterdir()))}"
        sub.mkdir()
        return Fixture(sub, **kwargs)

    # --- monitor ---------------------------------------------------------------

    def test_monitor_snapshot_is_indx(self):
        fx = self.fixture()
        snap = fx.snapshot
        self.assertTrue(snap["recoverable"], snap["reason"])
        self.assertEqual(snap["schema"], "codex.ratrig.indx.plr.snapshot.v1")
        self.assertNotIn("dual_carriage", snap)
        self.assertEqual(snap["indx"]["tool_positions"]["tool_count"], 5)
        self.assertEqual(snap["save_variables"]["variables"]["active_tool"], 2)
        self.assertNotIn("dual_carriage", monitor.BASE_OBJECTS)
        self.assertNotIn("extruder1", monitor.BASE_OBJECTS)

    # --- status ------------------------------------------------------------------

    def test_status(self):
        fx = self.fixture()
        res = fx.run("status")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("Recorded tool: T2", res.stdout)
        self.assertIn("latch locked", res.stdout)
        self.assertIn("Head position (machine): X=201.50 Y=188.25 Z=8.62", res.stdout)
        self.assertNotIn("IDEX", res.stdout)

    # --- precheck ----------------------------------------------------------------

    def test_precheck_pass_writes_report_runfile_and_plan(self):
        fx = self.fixture()
        res = fx.run("precheck")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("OK: True", res.stdout)
        self.assertIn("Tool on the head now: T2, latch locked, seat_suspect none", res.stdout)
        state = json.loads((fx.state / "codex_plr_precheck.json").read_text())
        self.assertTrue(state["ok"], state["errors"])
        self.assertEqual(state["recorded_tool"], 2)
        self.assertTrue(state["start_locked"])
        runfile = (fx.gcodes / ".plr" / "plr.gcode").read_text()
        live = [c for is_live, c in command_lines(runfile) if is_live]
        self.assertEqual(live, ["M118 Codex PLR locked: precheck recorded state, but motion is disabled."])
        self.assertTrue(fx.plan_path.exists())
        self.check_plan(fx.plan_path.read_text(), fx.pos)

    def expect_refusal(self, fx: Fixture, needle: str):
        res = fx.run("precheck")
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("OK: False", res.stdout)
        self.assertIn(needle, res.stdout)
        plan = fx.plan_path.read_text()
        self.assertIn("REFUSED", plan)
        self.assertNotIn("SET_KINEMATIC_POSITION", plan)
        self.assertNotIn("M109", plan)
        out = fx.state / "should_not_exist.gcode"
        res = fx.run("make-plan", "--output", str(out))
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertFalse(out.exists())

    def test_precheck_tool_mismatch(self):
        self.expect_refusal(self.fixture(now_vars={"active_tool": 3}), "tool mismatch")

    def test_precheck_seat_suspect_set(self):
        self.expect_refusal(self.fixture(now_vars={"seat_suspect": 2}), "seat_suspect is set")

    def test_precheck_empty_head(self):
        self.expect_refusal(self.fixture(now_vars={"active_tool": -1}), "no tool on the head now")

    def test_precheck_active_tool_missing(self):
        self.expect_refusal(self.fixture(now_vars={"active_tool": None}), "active_tool is missing")

    def test_precheck_snapshot_without_tool(self):
        fx = self.fixture(snap_vars={"active_tool": -1})
        self.expect_refusal(fx, "snapshot recorded no tool on the head")

    def test_precheck_latch_open_now(self):
        self.expect_refusal(self.fixture(now_vars={"toolhead_state": 2}), "latch is not recorded as locked")

    def test_precheck_head_at_docks(self):
        def at_dock(status):
            status["toolhead"]["position"][1] = -35.0
        self.expect_refusal(self.fixture(status_edit=at_dock), "the head was at the docks")

    def test_precheck_lift_above_z_max(self):
        def tall(status):
            status["toolhead"]["position"][2] = 475.0
        self.expect_refusal(self.fixture(status_edit=tall), "is above Z max")

    def test_precheck_not_interrupted(self):
        fx = self.fixture(now_vars={"was_interrupted": False}, snap_vars={"was_interrupted": False})
        self.expect_refusal(fx, "no interrupted print is recorded")

    def test_precheck_before_first_layer(self):
        def layer0(status):
            status["print_stats"]["info"]["current_layer"] = 0
        self.expect_refusal(self.fixture(status_edit=layer0), "before layer 1")

    def test_precheck_refuses_idex_snapshot(self):
        def idex(snapshot):
            snapshot["schema"] = "codex.ratrig.plr.snapshot.v1"
            snapshot["dual_carriage"] = {"carriage_0": "PRIMARY", "carriage_1": "INACTIVE"}
        self.expect_refusal(self.fixture(snapshot_edit=idex), "is not the INDX schema")

    # --- make-plan ---------------------------------------------------------------

    def test_make_plan(self):
        fx = self.fixture()
        out = fx.state / "plan_out.gcode"
        res = fx.run("make-plan", "--output", str(out))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.check_plan(out.read_text(), fx.pos)

    def check_plan(self, plan: str, pos: int):
        # Never a Z home: the only G28 anywhere in the file is the staged X/Y home
        for line in plan.splitlines():
            if re.search(r"\bG28\b", line):
                self.assertEqual(line.strip(), "; G28 X Y", line)
        self.assertNotIn("G28 Z", plan)
        self.assertEqual(plan.count("G28"), 1)

        cmds = command_lines(plan)
        live = [c for is_live, c in cmds if is_live]
        # Only the tool guard and the bed target run; no motion, no hotend heat
        self.assertEqual(live, ["PLR_VERIFY_TOOL TOOL=2", "M140 S100.0"])
        for _, c in cmds:
            self.assertIsNone(FORBIDDEN_TOKENS.match(c.split()[0]), c)

        seq = [c for _, c in cmds]
        i_guard = index_of(seq, "PLR_VERIFY_TOOL TOOL=2")
        i_zero = index_of(seq, "SET_GCODE_OFFSET X=0 Y=0 Z=0 MOVE=0")
        i_kin = index_of(seq, "SET_KINEMATIC_POSITION Z=8.620 SET_HOMED=Z")
        i_rel = index_of(seq, "G91", i_kin)
        i_lift = index_of(seq, "G1 Z10.000", i_rel)
        i_home = index_of(seq, "G28 X Y")
        i_off = index_of(seq, "SET_GCODE_OFFSET X=0.120 Y=-0.080 Z=0.220 MOVE=0")
        i_guard2 = index_of(seq, "PLR_VERIFY_TOOL TOOL=2", i_off)
        i_m104 = index_of(seq, "M104 S310.0")
        i_m109 = index_of(seq, "M109 S310.0")
        i_xy = index_of(seq, "G1 X201.380 Y188.330")
        i_check = index_of(seq, "G1 Z9.400", i_xy)
        i_down = index_of(seq, "G1 Z8.400", i_check)
        i_e = index_of(seq, "G92 E1520.12345")
        i_m23 = index_of(seq, f"M23 {GCODE_NAME}")
        i_m26 = index_of(seq, f"M26 S{pos}")
        i_m24 = index_of(seq, "M24")
        order = [i_guard, i_zero, i_kin, i_rel, i_lift, i_home, i_off, i_guard2, i_m104, i_m109,
                 i_xy, i_check, i_down, i_e, i_m23, i_m26, i_m24]
        self.assertEqual(order, sorted(order), dict(zip(
            ["guard", "zero", "kin", "rel", "lift", "home", "offset", "guard2", "m104", "m109",
             "xy", "check", "down", "e", "m23", "m26", "m24"], order)))
        # Z restore comes before X/Y homing, and only Z is marked homed by it
        self.assertLess(i_kin, i_home)
        self.assertLess(i_lift, i_home)
        self.assertNotIn('"', seq[i_m23])
        # Heat only after the second tool check
        heats = [i for i, c in enumerate(seq) if c.startswith(("M104", "M109"))]
        self.assertTrue(heats and min(heats) > i_guard2)

    # --- archive / clear ---------------------------------------------------------

    def test_archive_and_clear(self):
        fx = self.fixture()
        self.assertEqual(fx.run("precheck").returncode, 0)
        res = fx.run("archive")
        self.assertEqual(res.returncode, 0, res.stderr)
        archives = list((fx.state / "archive").iterdir())
        self.assertEqual(len(archives), 1)
        names = {p.name for p in archives[0].iterdir()}
        self.assertTrue({"codex_plr_latest.json", "variables.cfg", "codex_plr_plan.gcode"} <= names, names)
        self.assertEqual(fx.run("clear").returncode, 2)
        self.assertTrue((fx.state / "codex_plr_latest.json").exists())
        self.assertEqual(fx.run("clear", "--yes").returncode, 0)
        self.assertFalse((fx.state / "codex_plr_latest.json").exists())
        self.assertFalse(fx.plan_path.exists())
        self.assertTrue(fx.variables.exists())


class ConfigTests(unittest.TestCase):
    """Static checks on the draft cfg files (no Klipper here to load them)."""

    @staticmethod
    def macros(path: Path) -> dict[str, list[str]]:
        sections: dict[str, list[str]] = {}
        current = None
        for line in path.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\[(.+)\]\s*$", line)
            if m:
                current = m.group(1)
                sections[current] = []
            elif current is not None:
                sections[current].append(line)
        return sections

    def test_public_interface(self):
        sections = self.macros(PLR_CFG)
        names = {s.split(" ", 1)[1] for s in sections if s.startswith("gcode_macro ")}
        required = {
            "_PLR_STATE", "PLR_BEGIN_PRINT", "PLR_END_PRINT", "PLR_CANCEL_PRINT", "PLR_ENABLE", "PLR_DISABLE",
            "PLR_SNAPSHOT", "PLR_STATUS", "PLR_CLEAR", "CODEX_PLR_CLEAR", "RESUME_INTERRUPTED",
            "CODEX_PLR_PRECHECK", "CODEX_PLR_START", "DETECT_INTERRUPTION", "PLR_RECOVERY_HELP",
            "AUTO_RECOVER_WIZARD", "PLR_VERIFY_TOOL",
        }
        self.assertTrue(required <= names, required - names)
        for dropped in ("_PLR_IDEX_POSITION_STATE", "PLR_IDEX_POSITION_STATUS", "PLR_IDEX_SET_SYNC_MODE",
                        "PLR_CAPTURE_ACTIVE_TOOL_POSITION"):
            self.assertNotIn(dropped, names)
        shell = self.macros(PLR_SHELL_CFG)
        for name in ("codex_plr_precheck", "codex_plr_status", "codex_plr_archive", "codex_plr_clear"):
            self.assertIn(f"gcode_shell_command {name}", shell)

    def test_plr_cfg_never_moves_heats_or_homes(self):
        bad_cmd = re.compile(r"^(G0|G1|G28|G91|G92|M104|M109|M140|T\d+|CHANGE_TOOL|PARK_TOOL|"
                             r"SET_KINEMATIC_POSITION|SET_DUAL_CARRIAGE|ACTIVATE_EXTRUDER)\b")
        for section, body in self.macros(PLR_CFG).items():
            for line in body:
                s = line.strip()
                if not s or s.startswith(("#", ";")):
                    continue
                self.assertIsNone(bad_cmd.match(s), f"{section}: {s}")
                self.assertNotIn("extruder1", s, section)
                self.assertNotIn("dual_carriage", s, section)
                # Klipper's config reader cuts a line at ' #' or ' ;'
                self.assertNotRegex(s, r"\s[#;]", f"{section}: {s}")

    def test_jinja_blocks_balanced(self):
        for section, body in self.macros(PLR_CFG).items():
            text = "\n".join(body)
            for opener, closer in (("if", "endif"), ("for", "endfor")):
                n_open = len(re.findall(r"\{%%\s*%s\b" % opener, text))
                n_close = len(re.findall(r"\{%%\s*%s\b" % closer, text))
                self.assertEqual(n_open, n_close, f"{section}: {opener}/{closer}")

    def test_lift_matches_tool_default(self):
        m = re.search(r"^variable_resume_lift:\s*([0-9.]+)", PLR_CFG.read_text(), re.M)
        self.assertIsNotNone(m)
        self.assertEqual(float(m.group(1)), tool_module.DEFAULT_LIFT_MM)

    def test_no_private_data(self):
        ip = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        mac = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
        serial = "/dev/serial/" + "by-id/usb-"  # split so this file does not match itself
        files = [PLR_CFG, PLR_SHELL_CFG, TOOL, MONITOR, Path(__file__)]
        if NOTES.exists():
            files.append(NOTES)
        for path in files:
            text = path.read_text(encoding="utf-8")
            for hit in ip.findall(text):
                self.assertEqual(hit, "127.0.0.1", f"{path.name}: {hit}")
            self.assertIsNone(mac.search(text), path.name)
            self.assertFalse(serial in text, path.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
