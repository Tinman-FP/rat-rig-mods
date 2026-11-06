# Kalico config for the INDX conversion (draft)

**Draft, not installed, not run on the printer.** It is the owner's working config
(`Tinman-FP/rat-rig-dual-beacon-500-idex-config`, commit 277d85e) changed for the single
carriage and the five-tool INDX. `config/` holds only the files that are new or changed. Every
other file in the printer's config folder stays as it is.

## What's in `config/`

| File | New or changed | What it does |
|---|---|---|
| `printer.cfg` | changed | Include order for Kalico and INDX. The saved settings block keeps only the bed and chamber PIDs |
| `MCU.cfg` | changed | Octopus plus the INDX head (`indxmcu`). The two EBB42s and the Beacons are gone. The serial paths are placeholders |
| `Core_Printer.cfg` | changed | `kinematics: corexy` (was `hybrid_corexy_ratrig`); bed unchanged |
| `Motion_XY.cfg` | changed | Two belts on MOTOR0 and MOTOR1, Y homes to the **rear**, 12 mm belt limits |
| `Motion_Z.cfg` | changed | Probe is the load cell; Z max 480 (bed 20 mm higher); 2 mm/s homing |
| `INDX_Head.cfg` | new | Bondtech's Smart Head sections: heater, extruder, TMC2240, fan, LEDs, accelerometer, encoder, load cell, head temperatures |
| `INDX_Tools.cfg` | new | Bondtech's `indx.cfg` with this machine's five docks, clearance line and probe point. T0–T4 run `AFTER_TOOL_CHANGE` (power-loss checkpoint, then runout check) |
| `homing_indx.cfg` | new | Bondtech's homing with X/Y homed twice each (FibreSeek style). Must come after their `homing.cfg` |
| `Stations.cfg` | new | Each tool's purge bucket and wiper pad: `PURGE_AND_WIPE`, `CLEAN_NOZZLE` |
| `Filament_Sensors.cfg` | new | One runout switch per tool on PG10–PG14, `FILAMENT_STATUS`, pause on an empty pickup |
| `Leveling.cfg` | changed | Z tilt and mesh on the load cell with T0, in the new coordinates |
| `Resonance.cfg` | changed | Accelerometer is the INDX head's LIS2DW |
| `System.cfg` | changed | Adds `[respond]`; INDX shares the existing `variables.cfg` |
| `Heated_Chamber.cfg` | changed | Sensors moved out. **Chamber target capped at 55 °C**, because the INDX head is rated for 60 °C ambient |
| `macros.cfg` | changed | One-carriage park; tool metadata for five tools. IDEX modes and offsets removed. `SET_TOOL_FILAMENT` is renamed `SET_TOOL_MATERIAL` |
| `Gcode_Macro.cfg` | changed | Print start levels on T0, then picks up the first tool, then heats. Prechecks cover every tool used. Load and unload work over each tool's bucket |
| `Adaptive_Heat_Soak.cfg` | changed | Beacon settle removed |
| `Test_Macros.cfg` | changed | Two-carriage jog tests removed |
| `PLR.cfg`, `PLR_Shell.cfg`, `scripts/` | changed | Power-loss recovery for one carriage plus the tool on the head. Recovery refuses unless the tool on the head matches the checkpoint, and it never homes Z. Not run yet; `PLR_INDX_NOTES.md` has the machine test and the open questions. `scripts/test_plr_indx.py` is an offline test (21 cases, made-up data) |

Macros you didn't need to change are kept byte for byte (the edits were made section by section).

**Retired** (take them out of the config folder): `Toolheads.cfg`, `EBB42_T0.cfg`,
`EBB42_T1.cfg`, `Compatibility.cfg`, every `Beacon*.cfg` and `beacon_active.cfg`,
`Dual_Beacon_Calibration.cfg`, `Adaptive_Heat_Soak_Beacon_Shell.cfg`, `scripts/ahs_beacon_wait.py`,
`Camera_XY.cfg` and `Toolchanger_Calibrate.cfg` (Bondtech's `CAL_ONE/TWO/THREE` replace them),
and the repo's `klipper-modified/` (custom IDEX kinematics).

**From Bondtech, used as shipped:** `indx-tc-macros.cfg`, `indx-cal.cfg` and `homing.cfg`, from
`github.com/BondtechAB/INDX` at commit ae64179. Clone that repo into the config folder as `INDX/`.

## Changes you will notice
- **Slicer (Orca), change filament G-code:** use Bondtech's version, then `AFTER_TOOL_CHANGE`. While printing, it saves the power-loss checkpoint with the new tool, and it pauses if that tool's runout switch reads empty:
  ```
  CHANGE_TOOL TOOL={next_extruder} TEMP={new_filament_temp}
  AFTER_TOOL_CHANGE TOOL={next_extruder}
  M400
  ```
- **Start G-code:** `START_PRINT` takes the same parameters as before, plus:
  - `TOOLS=`: a comma list of the tools used (`0,2,3`), or five true/false flags. For example `TOOLS={is_extruder_used[0]},{is_extruder_used[1]},{is_extruder_used[2]},{is_extruder_used[3]},{is_extruder_used[4]}`.
  - `PRIME=`: mm purged into the first tool's bucket after it heats (default 8).

  The probe count now defaults to 7,7: each load-cell touch takes about 5 s.
- **Loading filament:** `FILAMENT_LOAD TOOL=n TYPE=PLA|PETG|ABS|ASA|PA|PC|TPU [FILAMENT=name]` picks up the tool, moves it over its bucket and runs Bondtech's `LOAD_FILAMENT`. That step sets the heat model for the filament, heats, feeds and primes. Then the nozzle is wiped. Bondtech's `LOAD_FILAMENT` can also be called directly.
- **Temperature limits:** the INDX head is rated for 300 °C at the nozzle and 60 °C ambient. PPS-CF (320 °C nozzle, 65 °C chamber) is out of its range: keep printing these parts on the Qidi Plus 4.

## Checks run on this draft
1. **Kalico's offline batch mode.**
   - **Setup:** Kalico commit 648194e. The Octopus (STM32F446) and the INDX head (SAME51, Kalico's `bondtech_indx_usb.config`) data files were built locally. Nothing was flashed. The full config was assembled: the owner's repo, plus these files, minus the retired ones, plus Bondtech's macros and mainsail.cfg.
   - **Result:** it loads with no errors. Every section and option is accepted, every pin resolves on its board, and every macro compiles. The only warnings are for the owner's existing `off_below` on three fans, which Kalico marks as deprecated.
   - **Found and fixed:** Kalico requires `sense_resistor` on every TMC2209. Mainline Klipper defaulted it to 0.110, and the old X/Y sections relied on that default.
2. **A static check.**
   - **What it covers:** includes resolve, and no section is defined twice by accident. The only expected duplicates are the homing override and mainsail's own sections. It also checks that every command a macro calls exists, either as a macro or as a Kalico command.
   - **Result:** clean.
   - **Found and fixed:** leftover calls to the retired toolboard-fan macros.
   - **Proof it works:** it caught a planted missing macro and a planted Jinja error.

What the checks can't see: anything that only shows up when a macro runs, and anything that
needs the real machine (homing sensitivity, load-cell and heater calibration, dock positions).

## Before installing
1. Take a fresh snapshot of the live printer: the whole config folder, `variables.cfg` and the Klipper version. The live config may differ from the repo snapshot this draft is based on.
2. Follow INSTALL.md sections 12 and 13.
