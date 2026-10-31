# Installation: V-Core 4.1 500 12 mm CoreXY + Bondtech INDX

**Status:** this is the planned procedure for a design that has been checked in CAD only. Nobody has built it yet. Read the open items in `README.md` before you start, and go slowly the first time the machine moves.

Parts and hardware are in `BOM.md`. The printed parts are all in the Tinman project `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf`. CAD for every part is in `parts/`, and the whole machine is in `assembly/Rat Rig Vcore 4.1 INDX Core XY.solidcraft`. Its saved views show each area this guide refers to.

## Before you start
- Back up the current Klipper configuration.
- Have Bondtech's INDX instructions to hand. This guide covers fitting the conversion to the V-Core; the head, tools, docks and Link board are assembled and wired the way Bondtech describes.
- **Positions:** X positions below are measured from the inner face of the left front upright. That face is 370 mm left of the frame centre.
- **Tools:** 2.5 / 3 / 4 / 5 mm hex keys, a soldering iron with an M3 insert tip, calipers, a long straightedge.

## 1. Print and prepare the parts
1. Print the four plates in the Tinman project. Don't auto-arrange them: the tree supports need the gaps.

   | Plate | Parts | Time | PPS-CF |
   |---|---|---|---|
   | 1 | carriage, 4 clamp caps, joints, front idlers | 15.5 h | 299 g |
   | 2 | rear corner bases and tops | 11.6 h | 225 g |
   | 3 | five cradles, dock and station rail brackets | 18.0 h | 344 g |
   | 4 | five buckets | 12.4 h | 225 g |

   Times and weights are from Tinman's slice.
2. Remove the supports. On the left rear-corner top, clean up the feet before they sit on the 3030s.
3. Fit the M3 heat-set inserts:
   - four in the carriage's front face, on the INDX 20 × 20 grid;
   - two in the back of each front idler block, for the tension screws.
4. Glue a Qidi wiper pad into each cradle's shelf with high-temperature RTV. Push it against the crossbar lip and the right wall. Its back edge lines up with the back of the shelf. Let the RTV cure fully.

## 2. Strip the IDEX parts
Power off and unplug the printer.

1. Remove both IDEX toolheads with their Beacons, EBB42s and umbilicals, and the IDEX PTFE guides.
2. Release and remove all four belts.
3. Remove the hybrid motor stacks and the front tensioners. Keep the **left lower** motor (it becomes motor A) and the **right upper** motor (motor B), with their cables.
4. Remove the stock XY joiners from the beam ends. Keep the four M5 × 12 screws and square T-nuts in the beam.
5. Slide the second MGN12C block off the X rail. Use a rail retainer or a spare rail end so its balls don't fall out.
6. Remove the front Y bumpers and the Y endstop.

## 3. Raise the bed 20 mm
1. At each of the three kinematic balls, replace the two 6 mm spacers with one 32 mm spacer.
2. Check that each threaded ball still has at least 6 mm of thread engaged. Use a longer M5 if it doesn't.
3. Leave levelling and Z for commissioning (step 10).

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
   | From the left upright (mm) | 107 | 223 | 339 | 455 | 571 |
   | Klipper X | −8 | 108 | 224 | 340 | 456 |

   These are the tool centres, not the dock bodies: the dock body sits mostly to the left of its tool. Klipper's dock calibration fine-tunes them.
3. **Station rail.** Bolt the station-rail brackets into the same slots, 129 mm lower than the dock-rail brackets. Fit the second 1515 × 739 bar the same way.
4. **Cradles.** Put two M3 T-nuts per cradle in the top slot of the station rail. Fit the five cradles with 2 × M3 × 8 countersunk each, left edges at:

   | Cradle | T0 | T1 | T2 | T3 | T4 |
   |---|---|---|---|---|---|
   | Left edge from the left upright (mm) | 94 | 210 | 326 | 442 | 558 |

   Each cradle sits under its own tool, with the wiper pad to the tool's right.
5. **Buckets.** Slide each bucket in from the front until its flange meets the cradle. It drops onto the detent ridge. Use the matching T number.
   - To empty one: open the door, pull the flange, slide it out 60 mm and lift it out. No fasteners.
6. Close the door. It should clear the bucket flanges by 3 mm and the dock fronts by 2 mm.

## 10. Electronics and Klipper
1. **Motors.** Motor A goes to MOTOR0 (the old `stepper_x` socket) and motor B to MOTOR1 (the old `stepper_y` socket). MOTOR3 and MOTOR4 become free.
2. **INDX electronics.** Fit the INDX Link board near the Pi. The Link cable (178 cm) plus the host USB must total 2 m or less. Route the five PTFE tubes through the top hat.
3. **Firmware.** Install Bondtech's `indx_klipper` (mainline) or Kalico. The printer currently runs a custom Klipper line with modified Beacon and PLR files, so check compatibility first.
4. **Config.** Add `klipper/motion_corexy12_indx.cfg` in place of the old motion files and the hybrid CoreXY kinematics, and add `klipper/purge_wipe.cfg`. Both are drafts. Set the INDX values listed at the end of the motion file.

## 11. Commissioning
Keep a hand on the power switch for every first move.

1. **Directions.** Run `STEPPER_BUZZ` on each motor. Check the CoreXY directions: motor A moves the head along X+Y, and motor B along X−Y.
2. **Homing.** Home Y to the **rear** stop, then X on the clearance line (Klipper Y 0). Y must never home toward the docks.
3. **Limits.** Check the stops and soft limits: X −35 to 545, Y −41 to 488.8.
4. **Z.** With the bed 20 mm higher, re-home Z, re-measure Z max, then level and mesh with the INDX probe.
5. **Docks.** Calibrate them with Bondtech's procedure (`CAL_SET_DOCK_Y`, `CALIBRATE_DOCK_X TOOL=n`).
6. **Purge stations.** Before the first purge, fit-check them with no filament, cold:
   - On the clearance line, jog to each tool's purge X (39, 155, 271, 387, 503).
   - Step forward in Y to −40 a few millimetres at a time, watching the gaps to the docks on both sides.
   - Then jog right 20 mm across the pad. The head should clear the next dock with room to spare.
7. **Wiper height.** Adjust the station-rail brackets so each pad's top is 1.2 mm above the nozzle tip.
8. **Purge test.** With each tool heated, run `PURGE_AND_WIPE TOOL=n`. Check the strand drops into that tool's bucket and the wipe crosses the pad.
9. **First print.** Run a small single-tool print, then a tool-change test across all five tools.
