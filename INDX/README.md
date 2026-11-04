# V-Core 4.1 500: 12 mm CoreXY + Bondtech INDX (5 tools)

An unofficial conversion for the Rat Rig V-Core 4.1 500 IDEX: a single carriage with a Bondtech INDX five-tool changer on true 12 mm-belt CoreXY, each tool with its own purge bucket and wiper. Not affiliated with or endorsed by Rat Rig, Bondtech or Qidi.

Status (2026-11-03): **development design, checked in CAD only.** Nothing is printed, bought or fitted. The Klipper file is a draft that has not been run.

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
- Tools spread apart, each with its own purge bucket and wiper right beside its dock (owner, 2026-10-31). Every bucket keeps the earlier bucket's size, and slides out through the open front door with no fasteners.
- Docks stay at the front (owner, 2026-11-03). The tools are now 122 mm apart, as far as the X travel allows with every station clear of the bed arms.
  - Rear docks, as on the Snapmaker U1, were considered. On this frame they would mean reversing the INDX head, which loses about 50 mm of print depth, and the buckets could no longer slide out of the front door.
- PTFE tubes come in at the top front, above each dock, and are stiffened with 1.0 mm piano wire (owner, 2026-11-03). The head's umbilical stays at the back middle and must not interfere with the tubes.
- Spools on top of the machine rather than in dryers at the sides (owner, 2026-11-03: "Design top mount"). The tubes stay short and straight and all enter at the front, away from the umbilical.
  - Dryers: a Sunlu FilaDryer S4 for four spools, and a single-spool dryer beside it for the fifth (owner). A Sunlu S2 is suggested because it also reaches 70 °C.
  - The owner places the dryers and routes each tube's last run to them. The design brings each tube up through the lid and the deck's notch to just behind the notch (owner: "Just put the PTFE inlets where they need to be and I will work around the dryer").
- The top hat is the owner's own design, printed in PET-CF. `source/vc12_hat.py` places their file `Rat Rig Top Hat Modular.step` (exported 2026-11-03, "the complete top hat as it sits") on the frame.
- Firmware: Kalico (owner, 2026-11-03). Bondtech recommends it, and the load-cell probing and the optional INDX bed scanner work fully only on Kalico. See open item 6.
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
| Docks | a 1515 dock rail with five INDX docks, 122 mm apart |
| INDX | head and Link board |
| Bed | 20 mm higher (see below) |
| Purge and wipe | a second 1515 rail and, for each tool, a cradle, a slide-out bucket and a Qidi wiper pad |
| Tubes and umbilical | five PTFE coupler blocks on the front top 3030, piano wire on the tubes, and a saddle and swivel that carry the stock umbilical off the head |
| Spool deck | a plywood deck for the dryers on four printed feet, one on each top-hat corner, and five tube holes in the lid |

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
`assembly/Rat Rig Vcore 4.1 INDX Core XY.solidcraft` is the owner's V-Core 4.1 500 IDEX model with the conversion applied: docks 122 mm apart, one purge station per tool, the PTFE tubes and umbilical in their solved shapes (T0 on the head, the others parked), and the owner's top hat with the spool deck on it.
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
  - The stock top panel is left out. It is 800 × 736 mm, too big for the hat's 799.4 × 733.4 mm pocket. The owner's own lid is shown in its place, 5 mm thick with its top 5 mm above the hat's rim, with a 6 mm hole over each coupler block. Its two handles are drawn as stock-size blocks (33 mm tall).
- **Added:**
  - the PPS-CF parts;
  - idlers, pulleys, bearings and the two motors in their new places;
  - both 12 mm belts, routed for this pose;
  - the INDX head with tool T0 and radial cooling;
  - the 1515 dock rail with five docks and parked tools;
  - the purge stations: the second 1515 rail, and for each tool a cradle, a bucket and a red Qidi wiper pad;
  - the PTFE coupler blocks and tubes (light grey), and the umbilical (black) with its saddle and swivel;
  - the owner's top hat (dark grey, see-through) and lid, the spool deck (birch) on its four feet, each tube's run from its block up through the lid and the deck's notch, and see-through outlines of a Sunlu S4 and S2 on the deck (their placement is the owner's).
- **Pose:** the carriage is centred and the gantry is where the stock model has it (beam centre Y −21.2).

Colours: orange is new PPS-CF, yellow the new bed spacers, steel the idlers, pulleys and bearings, black the belts and motors, and blue the INDX head. The panels and the unchanged door are 15 % opaque so you can see inside. Twelve saved views go straight to the overview, the carriage, each rear corner, a joint, the dock rail, the five purge stations, a close-up of T2's dock, bucket and wiper, the tubes and umbilical, the spool deck, a deck foot on a hat corner, and the tubes rising through the lid and the deck's notch.

`assembly/conversion_new.step` holds only the new and moved items, so it can be laid over the original model in any CAD program. `source/vc12_assembly.py` regenerates it and the stock-parts STEP the SolidCraft file is built from.

Pictures are in `images/`: the whole machine (`assembly_overview.png`), the tubes and umbilical (`tubes_and_umbilical.png`), the spool deck (`spool_deck.png`, `deck_foot_on_hat.png`, `tubes_through_lid.png`), the row of stations, two stations close up, a bucket slid out, and each main printed part.

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
- Five docks 122 mm apart, tools at CAD X −275, −153, −31, 91 and 213 (printer X −20, 102, 224, 346, 468). Each tool's purge station sits between it and the next dock.
- They hang on a 1515 rail at Y −349, Z 734.4, bolted to the front uprights' inner T-slots through slotted brackets that give ±5 mm of height adjustment.
- The docked nozzles sit at Y −317.5.
- **How close the head can get to a dock.** Measured with Bondtech's real radial-cooling duct meshes, the head and tool clear a dock and its parked tool once the nozzle is 41.4 mm to the dock's right, or 44.5 mm to its left. That holds at every point on the way in from the clearance line, and it matches Bondtech's stated 41 mm minimum pitch.
  - The earlier 62 mm pitch came from treating the ducts as solid boxes. Measured that way, the head needs 47 mm on one side and 59.5 mm on the other, which is far too pessimistic.
  - The stations use these real-duct numbers with 5.6 mm and 10.5 mm to spare. Fit-check the real head before the first purge (open item 4).
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
| T0 | −275 / −20 | −228 / 27 | −222 / 33 | 31 → 47 |
| T1 | −153 / 102 | −106 / 149 | −100 / 155 | 153 → 169 |
| T2 | −31 / 224 | 16 / 271 | 22 / 277 | 275 → 291 |
| T3 | 91 / 346 | 138 / 393 | 144 / 399 | 397 → 413 |
| T4 | 213 / 468 | 260 / 515 | 266 / 521 | 519 → 535 |

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

## PTFE tubes and the umbilical
**Where the tubes come in.** Each tool's PTFE tube comes into the chamber from the top hat through a coupler block on the inner T-slot of the front top 3030, directly above its dock.
- **Coupler block.** The tube runs down the block's channel, bends 60° at a 40 mm radius, and leaves through a PC4-M10 coupler 30° below horizontal, pointing back into the chamber.
- **Free tube.** From the coupler the tube hangs free to its tool, with a 1.0 mm piano wire taped along it.
- **End tools.** T1–T3's blocks point straight back. T0's turns 20° toward the middle and T4's 15°. Straight back, those two longest tubes bow out through the side frame when the head is on their side.
- **Parked tubes.** A parked tube holds an arch over the front of the chamber, from Z 888 to 1091. That is 23 mm or more above the head's highest point, and under the lid's seat at Z 1111.
- **Active tube.** It never comes lower than Z 828, away from its last 15 mm at the tool.

| Tool | T0 | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| Free tube, coupler to tool (mm) | 791 | 717 | 649 | 680 | 750 |

**Umbilical.** The head's cables stay on the stock V-Core 4 umbilical: 1.2 mm piano wire from the back-middle mount, leaving it about 55° forward of vertical.
- **Saddle and swivel.** Its end is clamped in a swivel that turns on an M3 pin at the tail of a saddle stuck to the INDX PCB cover, 60 mm behind the cable strain relief. A stop on the saddle keeps the swivel between level-backward and straight up.
- **Why it swivels.** Near the front the umbilical lies back, under the parked tubes' arches. Near the back it stands up and stays inside the frame. Any fixed angle at the head fails one or the other:
  - straight down into the head, the stock way, it touches the parked tubes;
  - clamped level-backward, its spare length folds back into the rear panel.
- **Length.** Free length 687 mm, mount to swivel.

**Checks** (`source/vc12_routecheck.py`, `checks/route_report.json`). Every tube and the umbilical are solved as elastic rods with the method from the SV08 INDX project. They are checked with each tool on the head in turn, at every point of a 9 × 9 bed grid, its purge stroke and its dock. The check runs against the head, saddle, carriage, beam and joints, and the docks, rails, coupler blocks, frame, top 3030s and top hat.
- **No clashes for the tubes.** No tube, parked or active, touches the head, saddle, carriage, gantry, docks, rails, coupler blocks, frame, top 3030s or top hat at any position.
- **Umbilical to parked tubes:** 10.2 mm at the closest. That is with the head near the front at X 191, beside T4's parked tube.
- **What the check reports but doesn't count:**
  - The umbilical and the active tube both ride on the head and touch at a few front positions (up to 6.6 mm).
  - Active and parked tubes cross and rub in 39 of the checked cases (up to 4.5 mm), as on any multi-tool printer.
  - With the head at the back centre, the umbilical's spare length rests on the top of the INDX head. The stock V-Core 4 umbilical has the same length and mount.
- **Heights:** the umbilical stays between Z 784 and 1092, under the lid and inside the frame at the back. Every tube stays under the lid.
- **The tubes' runs up to the lid** (each straight up from its block): the umbilical stays at least 182 mm from them, an active tube at least 31 mm from the other tools' runs, and a parked tube at least 123 mm.

## Spool deck on the top hat
The dryers sit on a deck above the top hat. Pictures: `images/spool_deck.png`, `images/deck_foot_on_hat.png`, `images/tubes_through_lid.png`.

**The top hat.** It is the owner's, printed in PET-CF, from their file `Rat Rig Top Hat Modular.step` (`source/vc12_hat.py` places it on the frame).
- **Modules:** eight printed modules, 141 mm tall, standing on the top 3030s with 5 mm tongues in their slots.
- **Walls:** 40 mm thick at the four corners. The centre modules front and back are 50 mm thick and stand 5 mm proud of the corners. The side middles are hollow.
- **Display:** the front right corner carries the display. Its window goes through the wall, and the display's cables run through the hollow at that corner's right end.
- **Lid:** the pocket for the lid is 799.4 × 733.4 mm with its floor 130 mm above the frame top, and a 10 mm rim runs round it at 136 mm. The owner's lid sits in the pocket on a foam gasket, its top about 5 mm above the rim.

**Why it stands on the hat's corners.** The deck needs to be carried by the frame, not the lid. The hat's corners stand right on the corner uprights, so the deck's feet stand on them. A separate frame would mean cutting 30 mm holes through all four hat corners, or bolting posts through the side panels outside the hat.

- **Feet** (`deck_foot_FR`/`FL`/`RR`/`RL`, all the same part, 61 g each).
  - Each stands on the rim at one corner, with a skirt that drops 8 mm over the hat's rounded corner (1 mm gap) to locate it.
  - Its legs stand 2 mm outside the lid's pocket and it is open over the lid, so it touches only the rim even though the lid stands above it.
  - Two 4 × 16 mm wood screws hold the deck to its top plate.
  - At the front right corner, the hat is hollow at the top for the display cables. The foot's legs stand right over that corner's 6 and 7.5 mm outer walls, which carry the load down to the solid part below.
- **Deck.** 15 mm birch plywood, 820 × 756 mm, flush with the hat's corners. Its underside is 40 mm above the lid's top, an air gap that keeps the chamber's heat (65 °C for PPS-CF) off the dryers. It clears the lid's two handles by 6.9 mm if they are stock height (33 mm); taller handles would need taller feet.
- **Notch.** A 538 × 72 mm notch in the front edge lets the tubes rise past the deck. So the deck lifts off without unthreading them, and taking the lid off means lifting the dryers and deck, then the lid over the tube ends.
- **Tubes.** Each one rises straight from its block's channel (Z 1005) through a 6 mm hole in the lid, 42.7 mm behind the pocket's front edge, to 20 mm above the deck. It then bends back over the notch's edge at 60 mm radius or more and ends just behind the notch. That is one continuous tube from the tool to the dryer; the only bend below the deck is the block's own 60° turn.
- **Dryers.** A Sunlu S4 (four spools) and a single-spool dryer beside it, shown as outlines of a Sunlu S4 lengthways for T0–T3 and an S2 side-on at the right end for T4. They use about 634 of the deck's 820 mm width. Where they stand and how each tube reaches its outlet is the owner's call; keep each bend at 60 mm radius or more.

| Lid hole | T0 | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| From the lid's left edge (mm) | 125 | 247 | 369 | 491 | 613 |

**Checks** (`source/vc12_topcheck.py`, `checks/top_report.json`), against the owner's hat file:
- The feet sit on the rim with no overlap, 2.0 mm clear of the lid, 631 mm² of bearing each.
- The deck clears the handles by 6.9 mm (stock height), the lid by 39.9 mm and the hat by 44.9 mm.
- Each tube's run clears the hat by 5.7 mm (T2, T3, behind the front centre), 6.5 mm (T1) and 10.7 mm (T0, T4). It clears its lid hole by 1 mm all round, the deck's notch by 16 mm and the other blocks by 109 mm.
- The coupler blocks are cut back above the frame top to clear the hat's front centre wall by 2 mm, and its lower inner edge where it overhangs the top 3030. The closest point is the mounting plate, 1.0 mm under that overhang.
- **Load:** with the S4 and S2 and five full 1 kg spools (12.25 kg), the deck (5.9 kg) and feet put about 45 N on each corner, 0.07 MPa on the rim. A 15 mm birch deck on four corners sags about 2 mm in the middle.

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

**Print file.** `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf` is a Tinman project holding all 38 parts on six plates: one of each motion part, the five cradles and five buckets labelled T0–T4, the five PTFE coupler blocks, the umbilical saddle and swivel, and the four spool deck feet. Open it in Tinman as a project. It is saved unsliced.
- **Presets.** These are the owner's saved Qidi Plus 4 PPS-CF settings:
  - machine "Qidi X-Plus 4 0.6 nozzle - TinMan Codex";
  - process "0.24mm Tank @Qidi X-Plus 4 0.6 nozzle - TinMan Codex - Copy": 6 walls, 45 % gyroid, 8 top and bottom layers;
  - filament "PPS-CF Codex-Bambu - Qidi X-Plus 4": 320 °C nozzle, 110 °C bed, 65 °C chamber;
  - Textured PEI plate.
- **Plates.** Times and weights come from Tinman's own test slice on 2026-11-03, after the coupler blocks and deck feet were refitted to the owner's real top hat.

| Plate | Parts | Time | PPS-CF |
|---|---|---|---|
| 1 Carriage, joints, front idlers | carriage, 4 clamp caps, joint L/R, front idler L/R | 15.2 h | 295 g |
| 2 Rear corners | base L/R, top L/R | 11.4 h | 223 g |
| 3 Purge cradles and rail brackets | station cradles T0–T4, dock brackets L/R, station brackets L/R | 16.3 h | 322 g |
| 4 Purge buckets | purge buckets T0–T4 | 13.7 h | 241 g |
| 5 PTFE coupler blocks and umbilical saddle | coupler blocks T0–T4, saddle, swivel | 7.1 h | 138 g |
| 6 Spool deck feet | deck feet ×4 | 8.3 h | 190 g |
| **Total** | 38 parts | **72.0 h** | **1,408 g** |

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
  - **Coupler blocks:** mounting plate down. **Saddle:** front face down, arm standing up. **Swivel:** flat side down.
  - **Deck feet:** top plate down; the legs and skirt stand up.
- **Supports.** Tree supports are on only for the 19 parts that need them: the carriage, both joints, both front idlers, all four rear-corner parts, the five station cradles (under the crossbar and the pad shelf) and the five coupler blocks (under the bend). The clamp caps, brackets, buckets, saddle, swivel and deck feet print without support.
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
  - **FreeCAD motion check: no overlaps at any of the 31 poses, and none between the fixed parts and the stock frame, door, panels and electronics** (`checks/interference_report.json`; re-run 2026-11-03 with the coupler blocks refitted to the real top hat, same result).
  - **Station check: no overlaps at any of the 40 purge and wipe poses, the 4 mm shifted ones included.** Each nozzle touches only its own pad, and only during the wipe. All five buckets slide out clear. No station part touches the frame, door, bed arms or another station.
  - **Tubes and umbilical** (`checks/route_report.json`): no tube clashes; the umbilical stays at least 10.2 mm from every parked tube. See "PTFE tubes and the umbilical".
  - **Station clearances to the bed:** 4.0 mm to the front bed arms at the top of their travel. As the bed moves past, the pads and pad shelves are 1.5 mm from the PEI sheet's front edge and the buckets' back rims 2.0 mm. Nothing on the bed reaches further forward than the PEI sheet.
  - **SolidCraft** (2026-10-30 run, before the station change) at the rear-right and front-left stops:
    - no unexpected overlaps;
    - the only gaps under 0.5 mm are the designed fits: the 625 pocket at 0.05 mm, the 1515 in its brackets at 0.15 mm, and the motor boss at 0.25 mm;
    - every body is closed.
  - **Spool deck** (`checks/top_report.json`): the feet, deck and tube runs clear the owner's hat, the lid and its handles. See "Spool deck on the top hat".
  - **STL export:** all 38 meshes are solid and manifold, in both the assembly and the print orientation.
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
4. **Head beside the docks.** At its purge spot the head is 5.6 mm further from its own dock than it needs to be, and at the end of the wipe it is 10.5 mm further from the next dock. Both figures come from Bondtech's duct model. Before the first purge, jog the real head slowly to each purge spot and the end of each wipe stroke and look at the gaps. The ducts must be mounted as in Bondtech's model.
5. **Homing.** Y must home to the rear. The front stop is 1 mm past pickup, where the head already sits in the dock rail's slot.
6. **Firmware: Kalico** (owner, 2026-11-03).
   - Bondtech calls Kalico its reference INDX firmware; `indx_klipper` follows it for mainline Klipper.
   - The INDX head's load cell is the Z probe. Bondtech's load-cell settings use Kalico's pullback tap analysis, which mainline Klipper lacks. The optional INDX bed scanner needs Kalico from 2026-10-08 on.
   - Kalico also has `gcode_shell_command` built in, which the printer's power-loss-recovery and heat-soak shell helpers wait on.
   - The custom kinematics and dual-Beacon code in the owner's config (`Tinman-FP/rat-rig-dual-beacon-500-idex-config`) are for IDEX and are retired by this conversion.
   - The chamber, heat-soak, precheck, counter, RGB and camera macros carry over.
   - These need redoing for the INDX:
     - the toolboard and extruder sections;
     - the filament sensors and prechecks, for five tools;
     - homing, using Bondtech's macro with sensorless XY;
     - power-loss recovery.
   - INDX's saved state goes in the existing `variables.cfg`, since Klipper allows only one `[save_variables]`.
   - Take a fresh snapshot of the live printer before changing anything.
7. **Electronics and filament.**
   - The INDX Link cable (178 cm) plus the host USB must total 2 m or less, so the USB can be at most 22 cm and the Link board has to sit near the Pi.
   - The five PTFE tubes run up to the dryers on the spool deck (see "Spool deck on the top hat"). The owner routes each tube's last run to its outlet.
8. **Tension and current.** Belt tension targets and motor current (draft 1.4 A) still need setting against the motor rating. No FEA was done.
9. **Wiper height and depth.** Set the pad top 1.2 mm above the nozzle tip with the station-rail brackets' ±5 mm slots. The nozzle wipes only 3 mm in from the pad's rear edge (see the stations section); if that proves too shallow, the pad can't move back without hitting the bed.
10. **Tubes and umbilical.** Their shapes are modelled: a free tube settles where its stiffness and weight put it. Set them by hand on the machine as the stock umbilical is, and watch the first tool changes.
    - The top hat is the owner's own file. On the machine, check the coupler blocks' 1–2 mm to the hat's front wall and its overhang on the top 3030. Also check that the back of the display doesn't reach more than about 10 mm into the chamber past the wall's inside face; T4's tube rises 12.7 mm behind that face.
    - The umbilical rests on the head when the head is at the back centre. If it rubs, trim its spare length a little.
11. **Spool deck on the hat.**
    - **Load on the corners:** the printed hat corners carry the deck and dryers, about 45 N each. The hat is PET-CF, which stays stiff at the chamber's 65 °C.
    - **Front right corner:** it is hollow at the top for the display cables. The foot's legs stand over its outer walls.
    - **Handles:** the lid's handles are assumed to be stock height (33 mm). If they stand taller, the deck needs taller feet.
    - **Loading spools:** the deck's top is about 1.17 m above whatever the printer stands on, so loading spools needs a step stool.
