# PLR on the INDX conversion: notes

DRAFT, not run. Nothing here has been loaded on the printer. Source: the IDEX
config repo at commit 277d85e (Gcode_Macro.cfg PLR block, PLR_Shell.cfg,
scripts/codex_plr_tool.py, codex_plr_monitor.py, docs/plr).

## Files

- `PLR.cfg`: all PLR macros, moved out of Gcode_Macro.cfg.
- `PLR_Shell.cfg`: host-tool bridge. Kalico has `[gcode_shell_command]` built in, so it can be included directly.
- `scripts/codex_plr_monitor.py`, `scripts/codex_plr_tool.py`: host side.
- `scripts/test_plr_indx.py`: offline test with made-up fixtures (`python3 test_plr_indx.py`, 21 tests).

## What changed

- One carriage, one `[extruder]`. The tool is INDX's saved `active_tool`, not `toolhead.extruder`.
- A checkpoint records the tool, the latch state, head XYZ (machine), G-code XYZ/E, the G-code offset in effect (the tool's offsets), layer, byte position, file and targets.
- A checkpoint is one saved variable, `plr_snapshot` (a dict), not about 30 `SAVE_VARIABLE` writes. `variables.cfg` now also holds INDX's tool state, and every write rewrites the whole file.
- Recovery refuses unless the tool on the head now (`active_tool`, latch locked, `seat_suspect` unset) matches the checkpoint. This is `PLR_VERIFY_TOOL TOOL=<n>` in Kalico, and the same checks run in the host precheck.
- New refusals: checkpoint before layer 1, head not homed at the checkpoint, head at the docks (Y below `clearance_y`, so a tool change was running), latch open, Z + lift above Z max, and an old IDEX snapshot (wrong schema).
- The staged plan restores Z from the snapshot (`SET_KINEMATIC_POSITION Z=.. SET_HOMED=Z`) and lifts 10 mm (`_PLR_STATE resume_lift`). It then runs `G28 X Y` only, puts the tool offsets back with `MOVE=0`, runs the tool check again, and heats with M104/M109. Next it moves over the saved point, stops 1 mm above the saved Z for a hand gap check, lowers, and runs `G92 E`. M23/M26/M24 stay commented as before. The only live lines are the tool check and the bed target. The plan never homes Z and never changes tools.
- The IDEX version did not restore Z at all: it left Z to be re-established by hand. The Z restore is new and is the part to test first.
- `make-plan` now runs the precheck and writes nothing if it fails. A failed `precheck` writes a "REFUSED" plan with no steps.
- The M23 filename is no longer quoted. Klipper's M23 takes the raw text, so the quotes would become part of the name.
- File names saved by `PLR_SNAPSHOT` are reduced to plain characters. A `;`, `#` or quote in a name used to break `SAVE_VARIABLE` at the layer change and stop the print.

## Removed

- `_PLR_IDEX_POSITION_STATE`, `PLR_CAPTURE_ACTIVE_TOOL_POSITION`, `PLR_IDEX_POSITION_STATUS`, `PLR_IDEX_SET_SYNC_MODE`. Their callers are all IDEX macros: PARK_T0/T1_SAFE, CLEAN_NOZZLE, PARK_BEFORE_WIPE_PAD and the tool-select macros in Gcode_Macro.cfg, plus T0/T1/copy/mirror in macros.cfg. Delete those lines when the macros are ported.
- These variables are no longer written: the per-field `plr_last_*`, `plr_t0_*`/`plr_t1_*`, `plr_idex_*`, `plr_dual_carriage_*`, and the duplicate names `last_file`, `filepath`, `power_resume_z`, `print_temp`, `bed_temp`, `hot_temp`. Nothing in the IDEX repo reads them. A carried-over `variables.cfg` keeps the old keys, which are ignored, because SAVE_VARIABLE cannot delete them.
- The monitor no longer queries `dual_carriage`, `extruder1` or `part_fan_t0/t1`. It now also records `TOOL_POSITIONS`, `_TOOLCHANGE_VARS`, `_PLR_STATE` and `load_cell_probe`.

## The rest of the config must provide

- `[save_variables]` in `~/printer_data/config/variables.cfg` (System.cfg), `[respond]`, and `[force_move] enable_force_move: True` for SET_KINEMATIC_POSITION (Test_Macros.cfg).
- INDX's `TOOL_POSITIONS` (`tool_count`, `clearance_y`) and its saved `active_tool`, `toolhead_state`, `seat_suspect`, `tN_offset_x/y/z`, `global_z_offset`.
- These callers, as before: START_PRINT calls `PLR_BEGIN_PRINT`, PRINT_END calls `PLR_END_PRINT`, the cancel path calls `PLR_CANCEL_PRINT`, the layer hook calls `PLR_SNAPSHOT LAYER=<n>` (reading `_PLR_STATE.enabled/interval`), and startup calls `DETECT_INTERRUPTION`.
- New: `PLR_SNAPSHOT QUIET=1` after each tool change, in the slicer's change-filament G-code after `T<next>`. Without it, the Kalico-side precheck falsely refuses a layer that changed tools. The host monitor still catches it within 2 s.

## Check on the machine before trusting PLR

1. Dry run with no filament and nothing on the bed (or a foam stand-in). Print a test file to layer 3 or more, then cut power at the wall.
2. After boot: Kalico starts, `variables.cfg` is intact, `DETECT_INTERRUPTION` reports the checkpoint, and `PLR_STATUS` shows the right tool and Z.
3. Measure that the bed did not move while unpowered. Mark it before the cut.
4. `CODEX_PLR_PRECHECK` passes. Then `MANUAL_TOOLHEAD_RESET` and confirm it refuses, then `MANUAL_TOOL_SEAT TOOL=<n>` to restore.
5. `codex_plr_tool.py precheck` (or `CODEX_PLR_PRECHECK_HOST`, which also proves RUN_SHELL_COMMAND works). Read the report and the plan.
6. Walk the staged plan from the console one line at a time. Check each of these:
   - the lift lowers the bed;
   - `G28 X Y` does not touch Z homing or the docks;
   - the 1 mm gap matches a feeler gauge;
   - M23/M26/M24 load the file and continue.
7. Cut power during a tool change and confirm the precheck refuses.
8. Install the monitor service. The IDEX `systemd/codex-plr-monitor.service.example` works unchanged; the paths are the same.

## Open questions (left out rather than guessed)

- **Z source.** The snapshot Z is the commanded position (it runs ahead of the motion) and is up to 2 s old. A snapshot taken during a Z hop reads high, so the nozzle would end up low. The 1 mm gap check is the only guard. Is slicer Z hop on?
- **Bed mesh.** An adaptive mesh is gone after the restart. Loading `default` may load an old mesh. No mesh line is staged, so Z at the resume point is off by the mesh value. Should each print save its mesh as a named profile?
- **Heater filament model.** Bondtech's `_APPLY_TOOL_FILAMENT` (an inner macro) runs at pickup, not at restart. Does Kalico's INDX heater need it before M109 after a power cut? It is not in the plan.
- **variables.cfg on power loss.** Mainline `SAVE_VARIABLE` rewrites the file in place. A cut mid-write can leave it empty, Kalico won't start, and the INDX tool state is lost. Does Kalico write it atomically? The monitor snapshot and the precheck archive hold copies.
- **Priming.** The plan says prime by hand at the rear. Is the wipe station path clear of a part?
- **Chamber.** The chamber targets are printed in the plan, but the chamber macros are not called.
- **Z steppers.** They snap up to a full step (about 0.02 mm), each motor separately, when they energise. Is that acceptable?
