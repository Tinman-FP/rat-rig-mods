# V-Core 4.1 500: 12 mm CoreXY + Bondtech INDX (5 tools)

An unofficial conversion for the Rat Rig V-Core 4.1 500 IDEX: a single carriage with a Bondtech INDX five-tool changer on true 12 mm-belt CoreXY, each tool with its own purge bucket and wiper. Not affiliated with or endorsed by Rat Rig, Bondtech or Qidi.

Status (2026-10-31): **development design, checked in CAD only.** Nothing is printed, bought or fitted. The Klipper file is a draft that has not been run.

- **Build documents:** [INSTALL.md](INSTALL.md) is the installation guide, and [BOM.md](BOM.md) (or `BOM.csv`) is the bill of materials.
- **Print file:** `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf` holds every printed part.
- **Where the files live:**
  - The working copy, where the scripts run, is `cad/2026-10-30-vc41-corexy12-indx/` in the Rat Rig record.
  - The published copies are Dropbox `3D Printing/Rat Rig/Mods/INDX` and the `INDX/` folder of GitHub `Tinman-FP/rat-rig-mods`.

## Owner decisions this design follows
- One carriage carrying a Bondtech INDX Smart Head, using Bondtech's MGN-12 X-carriage and Tool Dock 1515s. Five 0.6 mm Steel CHT tools, radial part cooling.
- True CoreXY with two 12 mm, 2 mm-pitch belts, one per A/B path. The 9 mm belts and doubled 9 mm belts were rejected.
- Keep the 3030 frame. New parts in PPS-CF.
- Bed raised 20 mm: approved by the owner.
- No door change. The owner chose option 1: the docks sit 5 mm further back.
- Print area **510 × 484.5 mm**.
  - The 496 mm figure given earlier assumed Bondtech's 26 mm dock clearance. Re-checked with Bondtech's real radial-cooling ducts, the head needs 40 mm to pass the parked tools between docks; see Travel below.
- Tools spread 116 mm apart, each with its own purge bucket and wiper right beside its dock (owner, 2026-10-31). Every bucket keeps the earlier bucket's size, and slides out through the open front door with no fasteners.
- Wipers: the owner's Qidi nozzle wiper pads, 15 × 27 × 4.7 mm, one per tool. The 15 mm side runs along X, so all five stations fit between the docks with clearance to spare (owner confirmed, 2026-10-31).

## What changes on the printer
**Removed:**
- both IDEX toolheads, with their Beacons and EBB42s;
- the stock XY joiners, motor stacks and front tensioners;
- all four stock belts;
- the second X-rail MGN12C block;
- the stock front Y bumpers and Y endstop;
- the IDEX PTFE guides;
- two of the four motors, which become spares.

**Kept:**
- the frame, Y rails and blocks;
- the steel X gantry and its MGN12 rail, with one MGN12C block;
- the Z system, panels and electronics;
- two motors: the left lower one drives belt A, and the right upper one drives belt B.

**Added:**

| Item | Detail |
|---|---|
| Printed parts | the PPS-CF parts below |
| Motion hardware | 12 mm belts, pulleys, idlers, two 625 bearings |
| Docks | a 1515 dock rail with five INDX docks, 116 mm apart |
| INDX | head and Link board |
| Bed | 20 mm higher (see below) |
| Purge and wipe | a second 1515 rail and, for each tool, a cradle, a slide-out bucket and a Qidi wiper pad |

### Changes outside the motion system
- **Bed up 20 mm.**
  - The INDX head's PCB cover reaches 28 mm behind its mounting face, starting 55 mm above the nozzle tip. With the V-Core rail and block on top of the beam, that cover has to clear the carriage's top plate, which puts the tip at Z 688.
  - The stock bed tops out at Z 671.4. At each of the three kinematic balls, replace the two 6 mm spacers with one 32 mm spacer, and check the threaded balls still have enough engagement.
  - Z travel is still about 535 mm.
  - The other ways to fit the head were worse. Moving the X rail to the beam's front face means drilling the steel tube. Hanging the head 77 mm in front of the beam is less stiff, and loses the rear 25 mm of the bed.
- **The door is unchanged.**
  - The closed door panel's inner face is the frame front, at Y −367.5. The magnet holders reach further in, to −360.3, but only at |x| 356–369, well clear of the docks.
  - The dock fronts sit 2.0 mm behind the closed door, and the head at pickup sits 14.6 mm behind it. Both were measured against the real door, panel, magnet holders and handles.
  - The purge buckets' front flanges sit 3.0 mm behind the closed door.
  - An earlier draft asked for a 13 mm door spacer. That was a measuring error: it used the magnet holders as the door face.

## Assembly file (open in SolidCraft)
`assembly/Rat Rig Vcore 4.1 INDX Core XY.solidcraft` is the owner's V-Core 4.1 500 IDEX model with the conversion applied: docks 116 mm apart and one purge station per tool.
- **Removed** (deleted, not hidden):
  - both IDEX toolheads;
  - the hybrid motor stacks and the front tensioners;
  - the stock XY joiners and their idlers, spacers, trims and Y-belt clamps;
  - all four stock belts;
  - the second X-rail block;
  - the front Y bumpers and Y endstop;
  - the IDEX PTFE guides and cable model.
- **Moved:**
  - The X-rail block now sits under the new carriage at X 0.
  - The bed is raised 20 mm on three new 32 mm spacers, which replace the six 6 mm ones. It is shown 50 mm below its top so the head and tools are visible.
- **Added:**
  - the PPS-CF parts;
  - idlers, pulleys, bearings and the two motors in their new places;
  - both 12 mm belts, routed for this pose;
  - the INDX head with tool T0 and radial cooling;
  - the 1515 dock rail with five docks and parked tools;
  - the purge stations: the second 1515 rail, and for each tool a cradle, a bucket and a red Qidi wiper pad.
- **Pose:** the carriage is centred and the gantry is where the stock model has it (beam centre Y −21.2).

Colours: orange is new PPS-CF, yellow the new bed spacers, steel the idlers, pulleys and bearings, black the belts and motors, and blue the INDX head. The panels and the unchanged door are 15 % opaque so you can see inside. Eight saved views go straight to the overview, the carriage, each rear corner, a joint, the dock rail, the five purge stations, and a close-up of T2's dock, bucket and wiper.

`assembly/conversion_new.step` holds only the new and moved items, so it can be laid over the original model in any CAD program. `source/vc12_assembly.py` regenerates it and the stock-parts STEP the SolidCraft file is built from.

Pictures are in `images/`: the whole machine (`assembly_overview.png`), the row of stations, two stations close up, a bucket slid out, and each main printed part.

## Layout (source of truth: `source/vc12_params.py`)

**Belts**
- **Planes:** belt A (lower) has its centre at Z 704.5; belt B (upper) at Z 723.5. They are 19 mm apart, so two 18 mm smooth idlers can stack on one axle.
- **X runs:** they pass 16 mm in front of and 16 mm behind the beam centre line, like the stock V-Core routing.
- **Teeth:** they face the front on both runs.

**Side columns**
- The inner column is at |x| 351.05 and the outer at |x| 366.8.
- The outer column's teeth are 2.2 mm from the 3030 face.

**Idlers**
- The front idlers sit at Y −321 and can move 3.5 mm either way.
- The rear crossing is at Y 334.5.

**Motors**
- Both motor axes are at (|x| 333, 318.5).
- Each pulley gets 198° of wrap, which is 11 teeth in mesh.

**Belt path**
- Pitch length is 2727.09 mm for each belt, constant at every carriage position.
- Motor A tracks X+Y and motor B tracks X−Y, both exact to within 1e-12 mm.
- Cut each belt to 2797 mm, which leaves a 20 mm clamp and a 15 mm tail at each end.
- The owner's spare 2400 mm 12 mm loops are too short.

**Travel**
- **Nozzle offset:** the nozzle is 51.7 mm in front of the beam centre line.
- **Stops:**
  - Y stops are at gantry −266.8 (1 mm past tool pickup) and +263 (rear).
  - X stops are at ±290.
- **Printable area:** X 0..510, the full PEI sheet. Y 0..484.5, from the clearance line to the PEI rear edge.
- **Clearance line:** 40 mm behind the docked nozzles. Sideways moves past the docks and all printing happen behind this line.
  - Bondtech's 26 mm clears the head body and tool, but the radial-cooling ducts clip a parked tool beside the head, by up to 191 mm³.
  - 38 mm and 40 mm clear on both sides of a dock (`checks/clearance_sweep.txt`).
  - Without the radial ducts, 26 mm would give back about 14 mm of depth.

**Docks**
- Five docks 116 mm apart, tools at CAD X −263, −147, −31, 85 and 201 (printer X −8, 108, 224, 340, 456). Each tool's purge station sits between it and the next dock.
- They hang on a 1515 rail at Y −349, Z 734.4, bolted to the front uprights' inner T-slots through slotted brackets that give ±5 mm of height adjustment.
- The docked nozzles sit at Y −317.5.
- **How close the head can get to a dock.** Measured with Bondtech's real radial-cooling duct meshes, the head and tool clear a dock and its parked tool once the nozzle is 41.4 mm to the dock's right, or 44.5 mm to its left. That holds at every point on the way in from the clearance line, and it matches Bondtech's stated 41 mm minimum pitch.
  - The earlier 62 mm pitch came from treating the ducts as solid boxes. Measured that way, the head needs 47 mm on one side and 59.5 mm on the other, which is far too pessimistic.
  - The stations use these real-duct numbers with 5.6 mm and 4.5 mm to spare. Fit-check the real head before the first purge (open item 4).
- **Bed clearance:** parked tools sit 2 mm above the nozzle plane. Their tips are 4.5 mm ahead of the PEI's front edge (−313), and the tool bodies overhang the sheet by about 10 mm.


## Purge buckets and wipers, one per tool
Built on the SV08 purge/wipe work: wiper top 1.2 mm above the nozzle tip, and slide-out buckets. The wipers are the owner's Qidi nozzle wiper pads (15 × 27 × 4.7 mm).

**Why they sit here.** The dock rail runs the full width at the head's slot height, so the nozzle never gets further forward than the tool pickup (Y −317.5). That is only 4.5 mm past the PEI's front edge. Everything below Z 690 is under the head's lowest part, the radial duct, which sits 3.2 mm above the tip. So the stations sit in front of the bed, below the head:
- the buckets stay 2 mm ahead of the bed plate, and the pads 1.5 mm ahead of the PEI sheet;
- below Z 646 nothing reaches further back than Y −323.5, so the front bed arms pass underneath even at the top of their travel;
- the bed's height never matters, because nothing here is over the bed.

**One station per tool, just right of its dock.** Each station has its own purge spot, its own wiper pad and its own bucket, so materials never mix. The bucket also sits under that tool's parked nozzle, so it catches the tool's drips while it is docked.

Pictures: `images/stations_all_T0_T4.png` shows the whole row in the printer; `images/stations_T1_T2_front.png` shows T1 and T2 from the door side; `images/station_T2_bucket_pulled.png` shows T2's bucket slid out.

| Tool | Dock X | Purge X | Pad (left edge) | Wipe stroke |
|---|---|---|---|---|
| T0 | −263 / −8 | −216 / 39 | −210 / 45 | 43 → 59 |
| T1 | −147 / 108 | −100 / 155 | −94 / 161 | 159 → 175 |
| T2 | −31 / 224 | 16 / 271 | 22 / 277 | 275 → 291 |
| T3 | 85 / 340 | 132 / 387 | 138 / 393 | 391 → 407 |
| T4 | 201 / 456 | 248 / 503 | 254 / 509 | 507 → 523 |

Positions are CAD X / printer X, all at Y −317.5 (printer Y −40.0). Wipe strokes are in printer X.

**Parts (PPS-CF).** The five cradles are identical, and so are the five buckets apart from the tool number engraved on the front.

| Part | Size (mm) | Mass | What it does |
|---|---|---|---|
| station_rail brackets L/R | 31 × 22 × 50 | 12 g each | Same design as the dock-rail brackets, 129 mm lower. They hold a second 1515 rail on the front uprights' inner T-slots at Y −352.5, Z 605.5. |
| station_cradle_T0–T4 | 88 × 47.5 × 74 | 52 g each | Sits on that rail (2 × M3 countersunk into T-nuts). A floor the bucket slides on, two side walls, and a crossbar carrying the wiper pad on a shelf. A low ridge on the floor is the bucket's detent. "T0"–"T4" on the crossbar. |
| purge_bucket_T0–T4 | 88 × 49.5 × 51 | 49 g each | Same width, height and top opening as the earlier bucket: body 81 × 47 × 51. Below the rim the back slopes forward to clear the bed arms, so each holds about 132 cm³ (the earlier one held 159). Purge strands and drips that land at the back slide in off the slope and a 45° chamfer on the back rim. The front flange is the finger pull and the stop. A groove underneath takes the detent ridge. "T0"–"T4" on the flange. |
| Qidi wiper pad (owner's) | 15 × 27 × 4.7 | — | Glued with high-temperature RTV into the shelf behind the crossbar, against its front lip and right wall. The rear edge is 1.5 mm ahead of the PEI sheet. |

**Emptying a bucket, no tools or fasteners.**
1. Open the door.
2. Pull the bucket's front flange. It lifts 0.5 mm over the detent ridge, then slides out on the cradle floor.
3. After 60 mm it is clear of the frame; lift it out.
4. To refit, push it in until the flange meets the cradle; it drops into the detent.

The closed door also holds the buckets in, 3 mm in front of the flanges. Each bucket fits any cradle, but the engraved numbers keep each tool's purge in its own bucket.

**How it is used.**
1. `klipper/purge_wipe.cfg` (draft) adds `PURGE_AND_WIPE TOOL=n`.
2. From the clearance line, the macro moves to that tool's purge X, comes forward to Y −40, purges into the bucket and retracts.
3. It wipes three times across the pad, 4 → 20 mm right of the purge spot, starting and ending just off the pad's left end so the wipings drop into the bucket. Then it goes back to the clearance line.
4. Call it after the INDX tool change has heated the new tool.

**Wiper depth.** The nozzle can't come further forward than the tool pickup, and the pad must stay ahead of the PEI sheet. So the nozzle wipes 3 mm in from the pad's rear edge, across the pad's 15 mm width, and the rest of the 27 mm length is support.

## Printed parts (PPS-CF, density 1.30; STEP and STL in `parts/`)

| Part | Size (mm) | Mass | Notes |
|---|---|---|---|
| joint_L / joint_R | 61.5 × 63 × 61.6 | 80 g each | Sit on the Y-rail MGN12C (4 × M3) and grip the beam end with the stock M5 screws and T-nuts. One toothed and one smooth idler each. Each carries a hard-stop face front and rear. |
| carriage | 92 × 46 × 49 | 83 g | Sits on the X-rail MGN12C (4 × M3, countersunk under the INDX PCB cover). The INDX X-carriage bolts to its front on the 20 × 20 grid (4 × M3 heat-set inserts). Four 12 mm belt clamps with toothed racks. |
| carriage_clamp_cap_1–4 | — | 2–4 g | Each held by 2 × M3 + nut. |
| front_idler_L / front_idler_R | 53.5 × 43 × 67 / 48 | 30 g | Sit on the side 3030 top (2 × M6). Slotted axle with two M3 push screws; lock after tensioning. Front Y hard stop for the joint. |
| rear_corner_L_base / _top | 88.5 × 70.5 × 36.5 / 59.5 × 72 × 40 | 83 / 33 g | Motor A underneath. The base bolts under the side and rear 3030s; the top sits on them. 625 bearing bridge over the pulley. Rear Y hard stop. |
| rear_corner_R_base / _top | 88.5 × 70.5 × 27 / 88.5 × 72 × 23 | 62 / 65 g | Motor B on top; 625 bearing bridge under the pulley. |
| dock_bracket_L / _R | 31 × 25 × 50 | 14 g | 1515 rail ends; slotted M6 into the front uprights. |

The purge-station parts (two rail brackets, five cradles, five buckets) are listed under the stations above.

**Print file.** `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf` is a Tinman project holding all 27 parts on four plates: one of each motion part, and the five cradles and five buckets labelled T0–T4. Open it in Tinman as a project. It is saved unsliced.
- **Presets.** These are the owner's saved Qidi Plus 4 PPS-CF settings:
  - machine "Qidi X-Plus 4 0.6 nozzle - TinMan Codex";
  - process "0.24mm Tank @Qidi X-Plus 4 0.6 nozzle - TinMan Codex - Copy": 6 walls, 45 % gyroid, 8 top and bottom layers;
  - filament "PPS-CF Codex-Bambu - Qidi X-Plus 4": 320 °C nozzle, 110 °C bed, 65 °C chamber;
  - Textured PEI plate.
- **Plates.** Times and weights come from Tinman's own test slice on 2026-10-31.

| Plate | Parts | Time | PPS-CF |
|---|---|---|---|
| 1 Carriage, joints, front idlers | carriage, 4 clamp caps, joint L/R, front idler L/R | 15.5 h | 299 g |
| 2 Rear corners | base L/R, top L/R | 11.6 h | 225 g |
| 3 Purge cradles and rail brackets | station cradles T0–T4, dock brackets L/R, station brackets L/R | 18.0 h | 344 g |
| 4 Purge buckets | purge buckets T0–T4 | 12.4 h | 225 g |
| **Total** | 27 parts | **57.5 h** | **1,092 g** |

- **Test slice.** No warnings and no path conflicts. Every plate starts with `PRINT_START BED=110 HOTEND=320 CHAMBER=65`.
- **Orientation.** Each part lies on the face listed in `print/orientation.json`.
  - **Carriage:** top plate down, so the face that bolts to the X block prints as a clean top surface. The INDX lip stands 1.4 mm above the plate, so the lip touches the bed first and support fills the gap under the plate.
  - **Joints:** top plate down.
  - **Front idler blocks:** front wall down.
  - **Rear-corner bases:** plate down.
  - **Rear-corner tops:** as fitted, feet down.
    - Right top: the motor face prints clean, with support under the plate.
    - Left top: it stands on its idler spacer, with support under the plate and the 1.4 mm feet. Clean up the feet before they sit on the 3030.
  - **Dock and station brackets:** upright plate down.
  - **Station cradles and purge buckets:** floor down. The buckets' flange and sloped back print without support.
- **Supports.** Tree supports are on only for the 14 parts that need them: the carriage, both joints, both front idlers, all four rear-corner parts, and the five station cradles (under the crossbar and the pad shelf). The clamp caps, brackets and buckets print without support.
- **Spacing.** Parts are at least 20 mm apart. When Tinman's auto-arrange packed them closer, the tree supports of a joint and the carriage ran into each other. Don't auto-arrange this project; if you move parts, keep the gaps.
- **Rebuilding the file.**
  1. `vc12_print.py` (FreeCAD) writes print-ready STLs to `print/stl/`.
  2. `python3 vc12_tinman.py` imports them with Tinman's command line in a throwaway data folder, so the owner's Tinman settings are untouched. It saves the project, then slices a copy to check it.
  3. The results are in `checks/tinman_slice.json`.
  4. `python3 vc12_bom.py` writes `BOM.md` and `BOM.csv` from the same part list.

Bosses are sized for M3 heat-set inserts (Ø4.0) and M5/M6 clearance.

## Hardware
The full purchase list, with screw lengths worked out from each part's clamping thickness, is in [BOM.md](BOM.md). Nothing has been ordered.

## Checks done (scripts in `source/`, results in `checks/`)
- `vc12_params.py` is a pure-Python belt solver: tangent and wrap geometry, constant length, CoreXY linearity, motor wrap.
- `vc12_check.py` assembles the conversion in FreeCAD 1.1.4 at 31 poses and checks every pair for overlap above 0.5 mm³:
  - the poses are 5 carriage X positions × dock clearance, mid and rear stop, the front stop at the three docks among them, each of the 5 tool pickups, and 8 positions between docks on the clearance line;
  - the head only comes forward of the clearance line at a dock or a purge spot, so there is no front-stop pose at X ±290 (T0's dock is 27 mm from the left stop);
  - the parts checked are the printed parts, purchased idlers, pulleys, motors and bearings, belts, the INDX head and tool, the docks, parked tools and the 1515 rail;
  - the context is the owner's stock V-Core 4.1 500 model, minus everything this conversion removes. The real door is included: panel, magnet holders and handles.
- **SolidCraft 0.27.1** cross-check:
  - `inspect.clearance` with a 1 mm threshold;
  - `inspect.measure`, which confirmed every body is closed and printable.
- `vc12_check.py --station` checks the five purge stations (`checks/station_report.json`), using Bondtech's real duct meshes for the head:
  - per tool: on the way in, at the purge spot, at the front stop, at both ends of the wipe stroke, and on the way out;
  - the purge spot again with the head 4 mm closer to its own dock, and the end of the stroke 4 mm closer to the next dock;
  - each bucket pulled 0, 20, 40 and 60 mm with the door open;
  - every station part against the stock frame, door, panels, the other stations, and the front bed arms, Z carriages and raised bed at the top of their travel.
- Results, 2026-10-31, docks 116 mm apart with one station per tool:
  - **FreeCAD motion check: no overlaps at any of the 31 poses, and none between the fixed parts and the stock frame, door, panels and electronics** (`checks/interference_report.json`).
  - **Station check: no overlaps at any of the 40 purge and wipe poses, the 4 mm shifted ones included.** Each nozzle touches only its own pad, and only during the wipe. All five buckets slide out clear. No station part touches the frame, door, bed arms or another station.
  - **Station clearances to the bed:** 4.0 mm to the front bed arms at the top of their travel. As the bed moves past, the pads and pad shelves are 1.5 mm from the PEI sheet's front edge and the buckets' back rims 2.0 mm. Nothing on the bed reaches further forward than the PEI sheet.
  - **SolidCraft** (2026-10-30 run, before the station change) at the rear-right and front-left stops:
    - no unexpected overlaps;
    - the only gaps under 0.5 mm are the designed fits: the 625 pocket at 0.05 mm, the 1515 in its brackets at 0.15 mm, and the motor boss at 0.25 mm;
    - every body is closed.
  - **STL export:** all 27 meshes are solid and manifold, in both the assembly and the print orientation.
- Fixes made during checking:
  - The rear-corner plates are notched around the rear corner uprights.
  - The front stop pads clear the Y-rail ends.
  - The dock-bracket cheek was moved ahead of the rail, because it hit the front idler block.
  - The stock Y bumpers, Y endstop and IDEX PTFE guide are removed.
- What the check allows by design:
  - **The head reaching the dock rail at pickup.** The rail sits in the head's slot. Measured with Bondtech's real 4010 duct meshes, the overlap at pickup is 0; one millimetre further on, at the front stop, the head reaches the slot's end.
  - **The duct models.** The motion check models the ducts as their bounding boxes, which is conservative. The station check and the dock-clearance measurement use Bondtech's real duct meshes.

## Open items and risks
1. **PPS-CF stiffness.** The carriage and joints carry the head and beam that were aluminium and steel in stock. Both are prismatic, so they can be machined in 6061 if ringing or tool-change pushes show it.
2. **X block.** INDX expects an MGN12H. This carriage sits on the stock MGN12C. An MGN12H, needing a matched rail and preload, would stiffen yaw.
3. **Belt clamps.** These are a new design: a toothed rack plus a screw cap. Pull-test them before trusting them.
4. **Head beside the docks.** At its purge spot the head is 5.6 mm further from its own dock than it needs to be, and at the end of the wipe it is 4.5 mm further from the next dock. Both figures come from Bondtech's duct model. Before the first purge, jog the real head slowly to each purge spot and the end of each wipe stroke and look at the gaps. The ducts must be mounted as in Bondtech's model.
5. **Homing.** Y must home to the rear. The front stop is 1 mm past pickup, where the head already sits in the dock rail's slot.
6. **Firmware.** INDX needs `indx_klipper` (mainline) or Kalico. The printer runs a custom Klipper line around 54c7b65d with modified Beacon and PLR files, so check compatibility before installing.
7. **Electronics and filament.**
   - The INDX Link cable (178 cm) plus the host USB must total 2 m or less, so the USB can be at most 22 cm and the Link board has to sit near the Pi.
   - Five PTFE tubes need routing; the 120 mm top hat is the natural place.
8. **Tension and current.** Belt tension targets and motor current (draft 1.4 A) still need setting against the motor rating. No FEA was done.
9. **Wiper height and depth.** Set the pad top 1.2 mm above the nozzle tip with the station-rail brackets' ±5 mm slots. The nozzle wipes only 3 mm in from the pad's rear edge (see the stations section); if that proves too shallow, the pad can't move back without hitting the bed.
