# Installation: V-Core 4.1 500 12 mm CoreXY + Bondtech INDX

**Status:** this is the planned procedure for a design that has been checked in CAD only. Nobody has built it yet. Read the open items in `README.md` before you start, and go slowly the first time the machine moves.

Parts and hardware are in `BOM.md`. The printed parts are all in the Tinman project `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf`. CAD for every part is in `parts/`, and the whole machine is in `assembly/Rat Rig Vcore 4.1 INDX Core XY.solidcraft`. Its saved views show each area this guide refers to.

## Before you start
- Back up the current Klipper configuration.
- Have Bondtech's INDX instructions to hand. This guide covers fitting the conversion to the V-Core; the head, tools, docks and Link board are assembled and wired the way Bondtech describes.
- **Positions:** X positions below are measured from the inner face of the left front upright. That face is 370 mm left of the frame centre.
- **Tools:** 2.5 / 3 / 4 / 5 mm hex keys, a soldering iron with an M3 insert tip, calipers, a long straightedge.

## 1. Print and prepare the parts
1. Print the six plates in the Tinman project. Don't auto-arrange them: the tree supports need the gaps.

   | Plate | Parts | Time | PPS-CF |
   |---|---|---|---|
   | 1 | carriage, 4 clamp caps, joints, front idlers | 14.7 h | 287 g |
   | 2 | rear corner bases and tops | 11.1 h | 219 g |
   | 3 | five cradles, dock and station rail brackets | 15.8 h | 311 g |
   | 4 | five buckets | 13.6 h | 236 g |
   | 5 | five PTFE coupler blocks and the two chain brackets | 9.2 h | 192 g |
   | 6 | four spool deck feet | 6.6 h | 150 g |

   Times and weights are from Tinman's slice.
2. Remove the supports. On the left rear-corner top, clean up the feet before they sit on the 3030s.
3. Fit the M3 heat-set inserts:
   - four in the carriage's front face, on the INDX 20 × 20 grid;
   - two in the back of each front idler block, for the tension screws.
4. Glue a Qidi wiper pad into each cradle's shelf with high-temperature RTV. Push it against the crossbar lip and the right wall. Its back edge lines up with the back of the shelf. Let the RTV cure fully.

## 2. Strip the IDEX parts
Power off and unplug the printer.

1. Remove both IDEX toolheads with their Beacons, EBB42s and umbilicals, the stock umbilical frame at the back middle, and the IDEX PTFE guides.
2. Release and remove all four belts.
3. Remove the hybrid motor stacks and the front tensioners. Keep the **left lower** motor (it becomes motor A) and the **right upper** motor (motor B), with their cables.
4. Remove the stock XY joiners from the beam ends. Keep the four M5 × 12 screws and square T-nuts in the beam.
5. Slide the second MGN12C block off the X rail. Use a rail retainer or a spare rail end so its balls don't fall out.
6. Remove the front Y bumpers and the Y endstop.

## 3. Raise the bed 20 mm
1. At each of the three kinematic balls, replace the two 6 mm spacers with one 32 mm spacer.
2. Check that each threaded ball still has at least 6 mm of thread engaged. Use a longer M5 if it doesn't.
3. Leave levelling and Z for commissioning (section 13).

## 4. Rear corners and motors
Each rear corner is a base under the side and rear 3030s and a top on them. The saved views "3 Left rear corner" and "4 Right rear corner" show both.

1. **Left base.** Press a 625ZZ bearing into the bridge from below, then bolt the base up under the side and rear 3030s with 4 × M6 × 18 into drop-in T-nuts.
2. **Motor A.**
   - Set a 20T pulley in the gap under the bridge, hub down.
   - Push motor A up from below, its shaft through the base, the pulley and into the bearing.
   - Fix it with 4 × M3 × 12 from above.
   - Line the pulley's teeth up with belt plane A and tighten its grub screws.
3. **Right base.** Bolt it up under the 3030s with 4 × M6 × 14. Press the second 625ZZ into its bridge from above.
4. **Corner idlers.** Each corner has two axles: one through the R1 idler, and one through a stacked pair of corner idlers.
   - Left corner: the R1 idler and the lower corner idler are on plane A; the upper corner idler is on plane B.
   - Right corner: the R1 idler and the upper corner idler are on plane B; the lower corner idler is on plane A.
   - Stand the idlers in place, with a washer between stacked idlers.
5. **Tops.**
   - Fit both tops over the idlers onto the 3030s: left 3 × M6 × 10, right 3 × M6 × 12.
   - Push the M5 × 55 axles down through each top, the idlers and the base. The nyloc nuts sit in the traps under the bases.
   - The tops' front faces are the rear Y hard stops.
6. **Motor B.**
   - Set the second pulley in the gap above the right bridge, hub up.
   - Lower motor B onto the right top, its shaft down through the top, the pulley and into the bearing.
   - Fix it with 4 × M3 × 10 from below.
   - Line the pulley up with belt plane B and tighten its grub screws.

## 5. Front idler blocks
1. Sit each block on top of its side 3030 at the front: left 2 × M6 × 12, right 2 × M6 × 16.
2. Fit the smooth idler on an M5 × 40 axle through the slot. It is on plane A on the left and plane B on the right.
3. Screw 2 × M3 × 20 tension screws into the inserts from the rear, until they just touch the axle.

Each block's rear face is the front Y hard stop for its joint.

## 6. XY joints
1. Bolt each joint onto its Y-rail block with 4 × M3 × 6. Don't use longer screws: the block's threads are only 3.5 mm deep.
2. Clamp the beam ends with the stock M5 × 12 screws into the beam's T-nuts, from below.
3. Fit the joint idlers on M5 × 60 axles:
   - left joint: toothed idler on plane A (front), smooth idler on plane B (rear);
   - right joint: toothed idler on plane B (front), smooth idler on plane A (rear).
4. Slide the gantry along Y by hand. It should run freely, and each joint should touch only the hard-stop faces at the ends of its travel.

## 7. Carriage and INDX head
1. Bolt the carriage onto the X-rail block with 4 × M3 × 8 countersunk. Again, no longer: 3.5 mm of thread.
2. Bolt Bondtech's MGN-12 X-carriage to the carriage's front grid with 4 × M3 × 10 into the inserts.
3. Assemble the INDX head, radial ducts and fans onto it per Bondtech's instructions. The ducts must sit as in Bondtech's model: the head's clearances to the docks depend on it.

## 8. Belts
Cut two belts to 2797 mm each. Belt A runs on the lower plane and belt B on the upper plane. Their teeth face the front on both X runs.

| Belt A (lower) | Belt B (upper) |
|---|---|
| carriage left clamp, front | carriage left clamp, rear |
| left joint, toothed idler | left joint, smooth idler |
| left front idler | left rear corner, upper idler |
| left rear R1 idler | across the back to the right rear corner, upper idler |
| motor A pulley | motor B pulley |
| left rear corner, lower idler | right rear R1 idler |
| across the back to the right rear corner, lower idler | right front idler |
| right joint, smooth idler | right joint, toothed idler |
| carriage right clamp, rear | carriage right clamp, front |

Toothed idlers and pulleys run on the teeth; smooth idlers run on the back of the belt.

1. Clamp the first end of each belt: lay its teeth on the rack in the clamp channel, then fit the cap with 2 × M3 × 16 and nuts. Leave about 15 mm of tail.
2. Push the gantry back until both joints touch the rear hard stops, so the gantry is square.
3. Pull each belt snug by hand and clamp its second end.
4. Tension each belt with its front idler: belt A on the left, belt B on the right.
   - Loosen the axle nut.
   - Turn both tension screws evenly.
   - Re-tighten the axle.
   - Tension targets are still an open item. Set both belts the same and check the gantry stays square.
5. Move the carriage by hand over the whole bed. Watch that every belt stays centred on every idler.

## 9. Dock rail, purge stations and buckets
1. **Dock rail.** Bolt both dock-rail brackets into the inner T-slots of the front uprights, 2 × M6 × 14 each, in the middle of their slots.
   - Drop in the 1515 × 739 bar. Fix each end with M3 × 8 into a T-nut in the bar.
   - The bar's centre sits 3.3 mm above the top face of the side 3030s. The slots give ±5 mm for the INDX dock height.
2. **Docks.** Hang the five INDX docks on the bar with their own screws. Each dock's tool centre goes at:

   | Tool | T0 | T1 | T2 | T3 | T4 |
   |---|---|---|---|---|---|
   | From the left upright (mm) | 95 | 217 | 339 | 461 | 583 |
   | Klipper X | −20 | 102 | 224 | 346 | 468 |

   These are the tool centres, not the dock bodies: the dock body sits mostly to the left of its tool. Klipper's dock calibration fine-tunes them.
3. **Station rail.** Bolt the station-rail brackets into the same slots, 129 mm lower than the dock-rail brackets. Fit the second 1515 × 739 bar the same way.
4. **Cradles.** Put two M3 T-nuts per cradle in the top slot of the station rail. Fit the five cradles with 2 × M3 × 8 countersunk each, left edges at:

   | Cradle | T0 | T1 | T2 | T3 | T4 |
   |---|---|---|---|---|---|
   | Left edge from the left upright (mm) | 82 | 204 | 326 | 448 | 570 |

   Each cradle sits under its own tool, with the wiper pad to the tool's right.
5. **Buckets.** Slide each bucket in from the front until its flange meets the cradle. It drops onto the detent ridge. Use the matching T number.
   - To empty one: open the door, pull the flange, slide it out 60 mm and lift it out. No fasteners.
6. Close the door. It should clear the bucket flanges by 3 mm and the dock fronts by 2 mm.

## 10. PTFE tubes and the cable chain
The tubes come in at the top front, directly above the docks, and hang free to the tools. The head's cable runs in a cable chain lying on its side, from a mount on the left top 3030 to a bracket on the carriage beside the head. The chain only bends sideways, so it folds into a U across the machine as the head moves.

1. **Coupler blocks.**
   - Bolt one block to the inner T-slot of the front top 3030 over each dock, with 2 × M6 × 10 into drop-in T-nuts. Centre each block on its dock's tool position, the same distances from the left upright as in the dock table.
   - The top of each block stands 24 mm above the frame top, inside the top hat. Its front is cut back to clear the hat's front wall, and the wall's edge where it overhangs the 3030, by 1–2 mm.
   - T1–T3's blocks send the tube straight back. T0's turns it 20° toward the middle and T4's 15°, so their long tubes don't bow out through the side frame. Fit each block over its own dock.
   - Thread a PC4-M10 coupler into each block's boss. Tap it M10 × 1, or let the coupler cut its own thread.
2. **Tubes.** Use one continuous 4 × 2 mm PTFE tube per tool.
   - Run it from its dryer on the deck down through its hole in the lid (section 11), down the block's channel, through the coupler and into the tool's push-fit.
   - Leave this much free between the coupler and the tool:

   | Tool | T0 | T1 | T2 | T3 | T4 |
   |---|---|---|---|---|---|
   | Free length (mm) | 791 | 717 | 649 | 680 | 750 |

   - Tape a 1.0 mm piano wire along each free length, from the coupler to about 20 mm above the tool.
   - A parked tube then holds an arch above the front of the chamber, and the active tube swings clear above the head.
3. **Chain brackets.**
   - Fit 2 M3 heat-set inserts in the carriage's top plate at its rear-right corner (they are modelled in), and 2 in each bracket's face.
   - Bolt the head bracket to the carriage with 2 × M3 × 8. Its face stands behind and above the head's right side.
   - Bolt the chain mount to the inner slot of the left top 3030 with 2 × M6 × 10 into drop-in T-nuts, 50 mm behind the 3030's middle (Y 25 to 95 from the frame centre).
4. **Cable chain.**
   - Take the igus E2.10.16.018.0 to 41 links (819 mm). Fit an igus end bracket on each end and screw them to the two brackets' faces (2 × M3 each), the chain lying on its side.
   - Open the chain along its outer side and lay the INDX toolhead cable in, from the head end. The cable comes up out of Bondtech's strain relief clip and curves about 30 mm sideways into the chain's end.
   - From the mount, run the cable up beside the mount, along the left top 3030 with slot clips to the left rear corner, and across the back to the electronics box.
5. **Hand check.** Move the head by hand to each front corner, each dock and the back corners.
   - The chain should fold flat into its U without dragging on the head or the frame, and stay under the parked tubes' arches.
   - No tube should touch the head.
   - Every tube top should stay below the top hat's lid.

## 11. Spool deck and dryers
The dryers sit on a plywood deck above the top hat, on four printed feet. Each foot stands on the hat's rim at one corner, straight over a frame upright, so the weight goes into the frame and nothing rests on the lid. The deck's underside sits 29 mm above the lid's top. That keeps the chamber's heat off the dryers and clears the lid's 22 mm handles by 7 mm. The tubes rise straight out of their blocks, through five holes in the lid and up through a notch in the deck's front edge.

1. **Lid holes.** Take the lid out of the hat.
   - Mark five holes 43 mm from its front edge, at 125, 247, 369, 491 and 613 mm from its left edge (seen from the front).
   - Drill them 3 mm first. Put the lid back in its pocket and look down through each hole: it should sit straight above its block's channel. Then open the holes to 6 mm and deburr them. Use a bit suited to the panel and back it with scrap.
2. **Deck.** Cut 820 × 756 mm from 15 mm birch plywood.
   - Cut a notch in one long edge, which becomes the front: 538 mm wide and 72 mm deep, starting 110 mm from the left end (so 172 mm from the right end).
   - Round the notch's back edge, where the tubes bend over it. Seal or paint the deck.
3. **Feet.** All four are the same part.
   - Set one on each corner of the hat. Its skirt drops over the hat's corner and its legs stand on the rim, just outside the lid.
   - Put a strip of double-sided tape on top of each foot. Lower the deck onto them, notch at the front, its edges in line with the hat's corners. Press down.
   - Lift the deck off with the feet stuck to it and turn it over. Drill 2.5 mm pilots through each foot's two holes and fix it with two 4 × 16 mm pan-head wood screws.
4. **Deck on.** Lower the deck onto the hat so the feet's skirts drop over the corners. With the S4 and S2 and five full spools, each foot carries about 45 N, and the deck sags about 2 mm in the middle.
5. **Dryers.** Stand the Sunlu S4 (T0–T3) and the single-spool dryer (T4) on the deck behind the notch, wherever suits their outlets. The S4 lengthways and an S2 side-on use about 634 of the deck's 820 mm width.
   - Each tube needs to bend at a 60 mm radius or more on its way from the notch to its outlet.
6. **Tubes.** Take each tube from its block straight up through its lid hole and the notch, over the notch's back edge and to its outlet. Label each outlet with its tool. Cut each tube to length once its free length below the block is set (section 10).
7. **Taking the lid off.** Unplug the five tubes at the dryers and lift the dryers off. Lift the deck off with its feet; it comes away from the tubes through the notch. Then lift the lid straight up over the tube ends. The tubes stay in their blocks.

The stock side spool holders are no longer needed. You can leave them on or take them off.

## 12. Electronics and Klipper
1. **Motors.** Motor A goes to MOTOR0 (the old `stepper_x` socket) and motor B to MOTOR1 (the old `stepper_y` socket). MOTOR3 and MOTOR4 become free.
2. **INDX electronics.** Fit the INDX Link board near the Pi. The Link cable (178 cm) plus the host USB must total 2 m or less.
3. **Snapshot first.** Copy the live printer's whole config folder, `variables.cfg` and its Klipper version somewhere safe. The draft is built on the GitHub copy of the config, and the live one may differ.
4. **Firmware: Kalico.** Its INDX support and the INDX head's firmware are built in.
   - Switch the Klipper folder to Kalico and reflash the Octopus from it, with the same board settings as before.
   - Flash the INDX head from the Kalico tree: `KCONFIG_CONFIG=board_configs/bondtech_indx_usb.config make`, then `make flash FLASH_DEVICE=04d8:e483`, with the head in bootloader mode (Bondtech's guide).
5. **Config.** The draft is in `klipper/config/`; `klipper/README.md` lists every file.
   - Copy the new and changed files over the old ones.
   - Move the retired files out of the config folder (the list is in `klipper/README.md` and at the end of the new `printer.cfg`).
   - Get Bondtech's macros, pinned to the version the draft was checked against:
     `git clone https://github.com/BondtechAB/INDX.git ~/printer_data/config/INDX`, then `git -C ~/printer_data/config/INDX checkout ae64179`.
   - In `MCU.cfg`, put back the Octopus serial line from the old file. Add the INDX head's line from `ls /dev/serial/by-id/` (the one starting `usb-Bondtech_INDX`).
   - In the slicer (Orca), set the change-filament G-code to `CHANGE_TOOL TOOL={next_extruder} TEMP={new_filament_temp}`, then `AFTER_TOOL_CHANGE TOOL={next_extruder}`, then `M400`. Add `TOOLS=` to the `START_PRINT` line (see `klipper/README.md`).
6. **Filament sensors.** Fit one runout switch per tool at the spool side and wire T0–T4 to the Octopus inputs PG10–PG14. Check each with `QUERY_FILAMENT_SENSOR SENSOR=Tn_runout`, with filament in and out.

## 13. Commissioning
Keep a hand on the power switch for every first move.

1. **Directions.** Run `STEPPER_BUZZ` on each motor. Check the CoreXY directions: motor A moves the head along X+Y, and motor B along X−Y.
2. **Homing.** Y homes to the **rear** stop, never toward the docks. `klipper/config/homing_indx.cfg` homes Y then X twice each, ending 4 mm off the rear and left stops.
   - Start with the head in the middle of the bed. Run `G28 Y` alone, then `G28 X`, each with a hand on the power switch. If an axis stops before reaching its stop, lower that motor's `driver_SGTHRS`. If it hits the stop and keeps pushing, raise it. Then try again.
   - Then run `G28`. Check the head goes to Y 388.8 before homing X, and never comes forward of Y 0 except to fetch T0.
   - Repeatability: run `G28` five times. After each, send `G0 X250 Y250 F6000`, `M400`, then `GET_POSITION`, and note the `mcu:` numbers for `stepper_x` and `stepper_y`. They should agree within 16 (0.05 mm; one microstep is 0.003 mm).
3. **Limits.** Check the stops and soft limits: X −35 to 545, Y −41 to 488.8.
4. **INDX head, in Bondtech's order.**
   - Calibrate the load cell with the head empty (`CALIBRATE_LOAD_CELL`, then `SAVE_CONFIG`) before the first Z home. Z homes on it.
   - Heater model: `INDX_CALIBRATE` with T0 seated by hand.
   - Until the docks are measured INDX refuses to drive into them. Seat T0 by hand and run `MANUAL_TOOL_SEAT TOOL=0`, then `G28`.
5. **Z.** With the bed 20 mm higher, re-measure Z max (`position_max` 480 in `Motion_Z.cfg` is a placeholder). Then run `Z_TILT_ADJUST` and a mesh, both on the load cell with T0.
6. **Docks.** Measure them with Bondtech's procedure (`CAL_SET_DOCK_Y`, `CALIBRATE_DOCK_X TOOL=n`). Paste the results into `INDX_Tools.cfg`, set `docks_calibrated: True` and `RESTART`. Then set the tool offsets (`CAL_Z`, and `CAL_ONE`/`TWO`/`THREE` or a test print for X/Y).
7. **Purge stations.** Before the first purge, fit-check them with no filament, cold:
   - On the clearance line, jog to each tool's purge X (27, 149, 271, 393, 515).
   - Step forward in Y to −40 a few millimetres at a time, watching the gaps to the docks on both sides.
   - Then jog right 20 mm across the pad. The head should clear the next dock with room to spare.
8. **Wiper height.** Adjust the station-rail brackets so each pad's top is 1.2 mm above the nozzle tip.
9. **Purge test.** With each tool heated, run `PURGE_AND_WIPE TOOL=n`. Check the strand drops into that tool's bucket and the wipe crosses the pad.
10. **Power-loss recovery.** Before trusting it, do the dry run in `klipper/config/PLR_INDX_NOTES.md`: no filament, cut power at layer 3, then walk the staged plan one line at a time. The Z restore is new.
11. **First print.** Run a small single-tool print, then a tool-change test across all five tools. Watch the tubes and the cable chain during the first tool changes and at the front corners.
