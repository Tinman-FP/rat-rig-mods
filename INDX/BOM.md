# Bill of materials: V-Core 4.1 500 12 mm CoreXY + INDX

Nothing on this list has been ordered or fitted yet. `BOM.csv` holds the same list for a spreadsheet.

## Printed parts (27 parts, PPS-CF, about 1,114 g modelled)

All of them are in the Tinman project `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf`.

| Part | Qty | Size as printed (mm) | Plate | What it is |
|---|---|---|---|---|
| carriage | 1 | 92 x 46 x 49 | 1 | Carries the INDX head on the X-rail block; four 12 mm belt clamps; 83 g; tree supports |
| carriage_clamp_cap_1 | 1 | 19.8 x 20.1 x 5 | 1 | Belt clamp caps, one of each; 2 g |
| carriage_clamp_cap_2 | 1 | 19.8 x 19.1 x 7.5 | 1 | Belt clamp caps, one of each; 3 g |
| carriage_clamp_cap_3 | 1 | 19.8 x 19.1 x 5 | 1 | Belt clamp caps, one of each; 2 g |
| carriage_clamp_cap_4 | 1 | 19.8 x 20.1 x 7.5 | 1 | Belt clamp caps, one of each; 4 g |
| joint_L | 1 | 61.5 x 63 x 61.6 | 1 | XY joints: Y-rail block to beam end, two idlers each; 80 g; tree supports |
| joint_R | 1 | 61.5 x 63 x 61.6 | 1 | XY joints: Y-rail block to beam end, two idlers each; 80 g; tree supports |
| front_idler_L | 1 | 53.5 x 67.1 x 41 | 1 | Front idler blocks with belt tensioners and front Y stops; 30 g; tree supports |
| front_idler_R | 1 | 53.5 x 48.1 x 41 | 1 | Front idler blocks with belt tensioners and front Y stops; 29 g; tree supports |
| rear_corner_L_base | 1 | 88.5 x 70.5 x 36.5 | 2 | Rear corner bases, under the 3030s; 83 g; tree supports |
| rear_corner_R_base | 1 | 88.5 x 70.5 x 27 | 2 | Rear corner bases, under the 3030s; 62 g; tree supports |
| rear_corner_L_top | 1 | 59.5 x 72 x 40.1 | 2 | Rear corner tops, on the 3030s; rear Y stops; 33 g; tree supports |
| rear_corner_R_top | 1 | 88.5 x 72 x 23 | 2 | Rear corner tops, on the 3030s; rear Y stops; 65 g; tree supports |
| dock_bracket_L | 1 | 50 x 25.3 x 30.8 | 3 | Dock rail end brackets; 14 g |
| dock_bracket_R | 1 | 50 x 25.3 x 30.8 | 3 | Dock rail end brackets; 14 g |
| station_bracket_L | 1 | 50 x 21.8 x 30.8 | 3 | Station rail end brackets; 12 g |
| station_bracket_R | 1 | 50 x 21.8 x 30.8 | 3 | Station rail end brackets; 12 g |
| station_cradle_T0 | 1 | 88 x 47.5 x 74 | 3 | Purge station cradles, one per tool (identical, engraved T0-T4); 52 g; tree supports |
| station_cradle_T1 | 1 | 88 x 47.5 x 74 | 3 | Purge station cradles, one per tool (identical, engraved T0-T4); 52 g; tree supports |
| station_cradle_T2 | 1 | 88 x 47.5 x 74 | 3 | Purge station cradles, one per tool (identical, engraved T0-T4); 52 g; tree supports |
| station_cradle_T3 | 1 | 88 x 47.5 x 74 | 3 | Purge station cradles, one per tool (identical, engraved T0-T4); 52 g; tree supports |
| station_cradle_T4 | 1 | 88 x 47.5 x 74 | 3 | Purge station cradles, one per tool (identical, engraved T0-T4); 52 g; tree supports |
| purge_bucket_T0 | 1 | 88 x 49.5 x 50.7 | 4 | Purge buckets, one per tool (identical, engraved T0-T4); 49 g |
| purge_bucket_T1 | 1 | 88 x 49.5 x 50.7 | 4 | Purge buckets, one per tool (identical, engraved T0-T4); 49 g |
| purge_bucket_T2 | 1 | 88 x 49.5 x 50.7 | 4 | Purge buckets, one per tool (identical, engraved T0-T4); 49 g |
| purge_bucket_T3 | 1 | 88 x 49.5 x 50.7 | 4 | Purge buckets, one per tool (identical, engraved T0-T4); 49 g |
| purge_bucket_T4 | 1 | 88 x 49.5 x 50.7 | 4 | Purge buckets, one per tool (identical, engraved T0-T4); 49 g |

## Motion

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 6 m | Belt, 12 mm GT2 | 2 mm pitch, 12 mm wide; cut 2 x 2797 mm | Gates 2MGT / GT3 | Belt A (lower) and belt B (upper) |
| 2 | Drive pulley, 20T 12 mm | 20 teeth, 12 mm belt, 5 mm bore | KB3D G2GT-20-5-12 or McMaster 3684N14 | Motors A and B |
| 2 | Toothed idler, 20T 12 mm | 20 teeth, 12 mm belt, 5 mm bore | KB3D G2GT-I-20-12 or McMaster 3693N13 | Joints, front-going side |
| 10 | Smooth idler | 15 mm running diameter, 19 mm flanges, 18 mm long, 5 mm bore | MISUMI HBGA15-16 | Joints 2, front idlers 2, rear corners 6 |
| 2 | 625ZZ bearing | 5 x 16 x 5 mm | Any | Motor shaft support bridges |
| 4 | M5 x 60 socket head screw | Idler axle | Any | Joint idlers |
| 4 | M5 x 55 socket head screw | Idler axle | Any | Rear corner idlers |
| 2 | M5 x 40 socket head screw | Idler axle | Any | Front idlers |
| 10 | M5 nyloc nut | — | Any | Idler axles |
| 20 | M5 washer | — | Any | Under axle heads and between stacked idlers |

## Fasteners

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 8 | M3 x 6 socket head screw | Max 3.5 mm into the block | Any | Joints to the Y-rail blocks |
| 4 | M3 x 8 countersunk screw | Max 3.5 mm into the block | Any | Carriage to the X-rail block |
| 10 | M3 x 8 countersunk screw | — | Any | Purge cradles to the station rail |
| 4 | M3 x 8 socket head screw | — | Any | Rail brackets into the 1515 bars |
| 4 | M3 x 10 socket head screw | — | Any | INDX X-carriage to the carriage |
| 4 | M3 x 10 socket head screw | — | Any | Motor B to the right rear top |
| 4 | M3 x 12 socket head screw | — | Any | Motor A under the left rear base |
| 8 | M3 x 16 socket head screw | — | Any | Belt clamp caps |
| 4 | M3 x 20 socket head screw | — | Any | Front idler tension (push) screws |
| 8 | M3 hex nut | — | Any | Belt clamp caps |
| 8 | M3 heat-set insert | For 4.0 mm holes, about 5.7 mm long | Any | Carriage INDX grid 4, front idler tension screws 4 |
| 14 | 1515 M3 T-nut | MakerBeam XL compatible | MakerBeam | Cradles 10, rail brackets 4 |
| 26 | 3030 M6 drop-in T-nut | — | Any | All M6 screws below |
| 4 | M6 x 18 socket head screw | — | Any | Left rear corner base, up into the 3030s |
| 4 | M6 x 14 socket head screw | — | Any | Right rear corner base, up into the 3030s |
| 3 | M6 x 10 socket head screw | — | Any | Left rear corner top |
| 3 | M6 x 12 socket head screw | — | Any | Right rear corner top |
| 2 | M6 x 12 socket head screw | — | Any | Left front idler block |
| 2 | M6 x 16 socket head screw | — | Any | Right front idler block |
| 8 | M6 x 14 socket head screw | — | Any | Dock and station rail brackets |

## Docks and stations

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 2 | 1515 aluminium extrusion, 739 mm | MakerBeam XL compatible | MakerBeam | Dock rail and station rail |
| 5 | Qidi nozzle wiper pad | 15 x 27 x 4.7 mm | Qidi (owner's part) | One wiper per tool |
| 1 | High-temperature RTV silicone | Rated 260 C or more | Any | Gluing the wiper pads |

## INDX (Bondtech)

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 1 | INDX Smart Head with MGN-12 X-carriage | — | Bondtech | Toolhead |
| 5 | INDX nozzle tool, 0.6 mm Steel CHT | — | Bondtech | Tools T0-T4 |
| 5 | INDX Tool Dock 1515 (MakerBeam) | With its M3 screw and square nut | Bondtech | Docks on the 1515 dock rail |
| 1 | INDX Link board and 178 cm cable | Link cable plus host USB 2 m or less | Bondtech | Head electronics |
| 1 | Radial part cooling, 4010 ducts and fans | Left and right | Bondtech | Part cooling |
| 1 | USB cable, host to Link board | 22 cm or shorter | Any | Link board |
| 5 | PTFE tube, 4 mm OD | Length to suit the top-hat routing | Any | Filament to each tool |

## Bed

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 3 | Bed spacer, 32 mm | 10 mm OD aluminium, M5 clearance | Any or turned | Replaces the two 6 mm spacers at each kinematic ball |
| 3 if needed | Longer M5 for the threaded balls | Keep at least 6 mm of thread engaged | Any | Bed balls |

## Filament

| Qty | Item | Specification | Source | Used for |
|---|---|---|---|---|
| 1.1 kg | PPS-CF | 1,092 g in Tinman's slice | Any | All printed parts |

## Reused from the printer

- Frame, panels, door and electronics
- Y rails and both Y-rail MGN12C blocks
- Steel X gantry, its MGN12 rail and one MGN12C block
- Beam-end M5 x 12 screws and square T-nuts (4)
- Two stock NEMA17 48 mm motors: left lower becomes A, right upper becomes B
- Z system and bed

## Removed (keep as spares)

- Both IDEX toolheads with their Beacons and EBB42s
- Stock XY joiners, hybrid motor stacks, front tensioners
- All four stock 9 mm belts
- The second X-rail MGN12C block
- Front Y bumpers and the Y endstop
- IDEX PTFE guides
- Two motors (spares)

## Notes

- Screw lengths come from each part's clamping thickness. Check them against your own T-nuts before ordering.
- The MGN12C blocks' threads are only 3.5 mm deep. Don't use longer screws there than listed.
- The INDX kit's own contents and part numbers follow Bondtech's documentation; this list names what the conversion needs from it.
