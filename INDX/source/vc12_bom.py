"""Write the bill of materials as BOM.md and BOM.csv (run with python3 after vc12_print.py).

Printed-part sizes and masses come from print/orientation.json (PPS-CF, density 1.30); the plate numbers
match vc12_tinman.py. Screw lengths were worked out from each part's clamping thickness (README, BOM notes).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENSITY = 1.30

PRINTED = [  # (parts, qty, plate, what it is)
    (["carriage"], 1, 1, "Carries the INDX head on the X-rail block; four 12 mm belt clamps"),
    (["carriage_clamp_cap_1", "carriage_clamp_cap_2", "carriage_clamp_cap_3", "carriage_clamp_cap_4"], 1, 1,
     "Belt clamp caps, one of each"),
    (["joint_L", "joint_R"], 1, 1, "XY joints: Y-rail block to beam end, two idlers each"),
    (["front_idler_L", "front_idler_R"], 1, 1, "Front idler blocks with belt tensioners and front Y stops"),
    (["rear_corner_L_base", "rear_corner_R_base"], 1, 2, "Rear corner bases, under the 3030s"),
    (["rear_corner_L_top", "rear_corner_R_top"], 1, 2, "Rear corner tops, on the 3030s; rear Y stops"),
    (["dock_bracket_L", "dock_bracket_R"], 1, 3, "Dock rail end brackets"),
    (["station_bracket_L", "station_bracket_R"], 1, 3, "Station rail end brackets"),
    ([f"station_cradle_T{i}" for i in range(5)], 1, 3, "Purge station cradles, one per tool (identical, engraved T0-T4)"),
    ([f"purge_bucket_T{i}" for i in range(5)], 1, 4, "Purge buckets, one per tool (identical, engraved T0-T4)"),
]

# (category, item, qty, specification, source, used for)
HARDWARE = [
    ("Motion", "Belt, 12 mm GT2", "6 m", "2 mm pitch, 12 mm wide; cut 2 x 2797 mm", "Gates 2MGT / GT3",
     "Belt A (lower) and belt B (upper)"),
    ("Motion", "Drive pulley, 20T 12 mm", 2, "20 teeth, 12 mm belt, 5 mm bore", "KB3D G2GT-20-5-12 or McMaster 3684N14",
     "Motors A and B"),
    ("Motion", "Toothed idler, 20T 12 mm", 2, "20 teeth, 12 mm belt, 5 mm bore", "KB3D G2GT-I-20-12 or McMaster 3693N13",
     "Joints, front-going side"),
    ("Motion", "Smooth idler", 10, "15 mm running diameter, 19 mm flanges, 18 mm long, 5 mm bore", "MISUMI HBGA15-16",
     "Joints 2, front idlers 2, rear corners 6"),
    ("Motion", "625ZZ bearing", 2, "5 x 16 x 5 mm", "Any", "Motor shaft support bridges"),
    ("Motion", "M5 x 60 socket head screw", 4, "Idler axle", "Any", "Joint idlers"),
    ("Motion", "M5 x 55 socket head screw", 4, "Idler axle", "Any", "Rear corner idlers"),
    ("Motion", "M5 x 40 socket head screw", 2, "Idler axle", "Any", "Front idlers"),
    ("Motion", "M5 nyloc nut", 10, "", "Any", "Idler axles"),
    ("Motion", "M5 washer", 20, "", "Any", "Under axle heads and between stacked idlers"),
    ("Fasteners", "M3 x 6 socket head screw", 8, "Max 3.5 mm into the block", "Any", "Joints to the Y-rail blocks"),
    ("Fasteners", "M3 x 8 countersunk screw", 4, "Max 3.5 mm into the block", "Any", "Carriage to the X-rail block"),
    ("Fasteners", "M3 x 8 countersunk screw", 10, "", "Any", "Purge cradles to the station rail"),
    ("Fasteners", "M3 x 8 socket head screw", 4, "", "Any", "Rail brackets into the 1515 bars"),
    ("Fasteners", "M3 x 10 socket head screw", 4, "", "Any", "INDX X-carriage to the carriage"),
    ("Fasteners", "M3 x 10 socket head screw", 4, "", "Any", "Motor B to the right rear top"),
    ("Fasteners", "M3 x 12 socket head screw", 4, "", "Any", "Motor A under the left rear base"),
    ("Fasteners", "M3 x 16 socket head screw", 8, "", "Any", "Belt clamp caps"),
    ("Fasteners", "M3 x 20 socket head screw", 4, "", "Any", "Front idler tension (push) screws"),
    ("Fasteners", "M3 hex nut", 8, "", "Any", "Belt clamp caps"),
    ("Fasteners", "M3 heat-set insert", 8, "For 4.0 mm holes, about 5.7 mm long", "Any",
     "Carriage INDX grid 4, front idler tension screws 4"),
    ("Fasteners", "1515 M3 T-nut", 14, "MakerBeam XL compatible", "MakerBeam", "Cradles 10, rail brackets 4"),
    ("Fasteners", "3030 M6 drop-in T-nut", 26, "", "Any", "All M6 screws below"),
    ("Fasteners", "M6 x 18 socket head screw", 4, "", "Any", "Left rear corner base, up into the 3030s"),
    ("Fasteners", "M6 x 14 socket head screw", 4, "", "Any", "Right rear corner base, up into the 3030s"),
    ("Fasteners", "M6 x 10 socket head screw", 3, "", "Any", "Left rear corner top"),
    ("Fasteners", "M6 x 12 socket head screw", 3, "", "Any", "Right rear corner top"),
    ("Fasteners", "M6 x 12 socket head screw", 2, "", "Any", "Left front idler block"),
    ("Fasteners", "M6 x 16 socket head screw", 2, "", "Any", "Right front idler block"),
    ("Fasteners", "M6 x 14 socket head screw", 8, "", "Any", "Dock and station rail brackets"),
    ("Docks and stations", "1515 aluminium extrusion, 739 mm", 2, "MakerBeam XL compatible", "MakerBeam",
     "Dock rail and station rail"),
    ("Docks and stations", "Qidi nozzle wiper pad", 5, "15 x 27 x 4.7 mm", "Qidi (owner's part)", "One wiper per tool"),
    ("Docks and stations", "High-temperature RTV silicone", 1, "Rated 260 C or more", "Any", "Gluing the wiper pads"),
    ("INDX (Bondtech)", "INDX Smart Head with MGN-12 X-carriage", 1, "", "Bondtech", "Toolhead"),
    ("INDX (Bondtech)", "INDX nozzle tool, 0.6 mm Steel CHT", 5, "", "Bondtech", "Tools T0-T4"),
    ("INDX (Bondtech)", "INDX Tool Dock 1515 (MakerBeam)", 5, "With its M3 screw and square nut", "Bondtech",
     "Docks on the 1515 dock rail"),
    ("INDX (Bondtech)", "INDX Link board and 178 cm cable", 1, "Link cable plus host USB 2 m or less", "Bondtech",
     "Head electronics"),
    ("INDX (Bondtech)", "Radial part cooling, 4010 ducts and fans", 1, "Left and right", "Bondtech", "Part cooling"),
    ("INDX (Bondtech)", "USB cable, host to Link board", 1, "22 cm or shorter", "Any", "Link board"),
    ("INDX (Bondtech)", "PTFE tube, 4 mm OD", 5, "Length to suit the top-hat routing", "Any", "Filament to each tool"),
    ("Bed", "Bed spacer, 32 mm", 3, "10 mm OD aluminium, M5 clearance", "Any or turned",
     "Replaces the two 6 mm spacers at each kinematic ball"),
    ("Bed", "Longer M5 for the threaded balls", "3 if needed", "Keep at least 6 mm of thread engaged", "Any",
     "Bed balls"),
    ("Filament", "PPS-CF", "1.1 kg", "1,092 g in Tinman's slice", "Any", "All printed parts"),
]

REUSED = ["Frame, panels, door and electronics", "Y rails and both Y-rail MGN12C blocks",
          "Steel X gantry, its MGN12 rail and one MGN12C block",
          "Beam-end M5 x 12 screws and square T-nuts (4)",
          "Two stock NEMA17 48 mm motors: left lower becomes A, right upper becomes B", "Z system and bed"]
REMOVED = ["Both IDEX toolheads with their Beacons and EBB42s", "Stock XY joiners, hybrid motor stacks, front tensioners",
           "All four stock 9 mm belts", "The second X-rail MGN12C block", "Front Y bumpers and the Y endstop",
           "IDEX PTFE guides", "Two motors (spares)"]


def main():
    orient = {r["part"]: r for r in json.loads((ROOT / "print/orientation.json").read_text())}
    rows = []
    total_g = 0.0
    for parts, qty, plate, what in PRINTED:
        for p in parts:
            r = orient[p]
            g = r["volume_cm3"] * DENSITY
            total_g += g * qty
            rows.append(("Printed (PPS-CF)", p, qty, " x ".join(f"{v:g}" for v in r["size_mm"]) + " mm",
                         f"Plate {plate}", f"{what}; {g:.0f} g" + ("; tree supports" if r["support"] else "")))
    with open(ROOT / "BOM.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Category", "Item", "Qty", "Specification", "Source / plate", "Used for"])
        w.writerows(rows)
        w.writerows(HARDWARE)
        w.writerows(("Reused from the printer", x, "", "", "", "") for x in REUSED)
        w.writerows(("Removed (keep as spares)", x, "", "", "", "") for x in REMOVED)
    md = ["# Bill of materials: V-Core 4.1 500 12 mm CoreXY + INDX", "",
          "Nothing on this list has been ordered or fitted yet. `BOM.csv` holds the same list for a spreadsheet.", "",
          f"## Printed parts ({sum(q * len(p) for p, q, _, _ in PRINTED)} parts, PPS-CF, about {total_g:,.0f} g modelled)", "",
          "All of them are in the Tinman project `print/VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf`.", "",
          "| Part | Qty | Size as printed (mm) | Plate | What it is |", "|---|---|---|---|---|"]
    md += [f"| {r[1]} | {r[2]} | {r[3].removesuffix(' mm')} | {r[4].removeprefix('Plate ')} | {r[5]} |" for r in rows]
    cat = None
    for c, item, qty, spec, src, use in HARDWARE:
        if c != cat:
            md += ["", f"## {c}", "", "| Qty | Item | Specification | Source | Used for |", "|---|---|---|---|---|"]
            cat = c
        md.append(f"| {qty} | {item} | {spec or '—'} | {src} | {use} |")
    md += ["", "## Reused from the printer", ""] + [f"- {x}" for x in REUSED]
    md += ["", "## Removed (keep as spares)", ""] + [f"- {x}" for x in REMOVED]
    md += ["", "## Notes", "",
           "- Screw lengths come from each part's clamping thickness. Check them against your own T-nuts before ordering.",
           "- The MGN12C blocks' threads are only 3.5 mm deep. Don't use longer screws there than listed.",
           "- The INDX kit's own contents and part numbers follow Bondtech's documentation; this list names what the "
           "conversion needs from it.", ""]
    (ROOT / "BOM.md").write_text("\n".join(md))
    print(f"{len(rows)} printed rows, {len(HARDWARE)} hardware rows, {total_g:.0f} g modelled")


main()
