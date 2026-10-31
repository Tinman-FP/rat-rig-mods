"""Lay every printed part on its print face and write print-ready STLs to print/stl/.

Each part is turned so the face named in ORIENT points down (assembly frame), then moved to
X, Y, Z >= 0. SUPPORT lists the parts that need supports; vc12_tinman.py turns them on per part.
"""
import json
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD  # noqa: E402,F401
import MeshPart  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "..", "parts")
OUT = os.path.join(HERE, "..", "print", "stl")

# assembly face that goes on the bed, and why
ORIENT = {
    "carriage": ("+Z", "top plate down: the X-block face prints as a clean top surface; the 1.4 mm INDX lip touches first, so support fills under the plate"),
    "carriage_clamp_cap_1": ("-Y", "flat face down"),
    "carriage_clamp_cap_2": ("-Y", "flat face down"),
    "carriage_clamp_cap_3": ("-Y", "flat face down"),
    "carriage_clamp_cap_4": ("-Y", "flat face down"),
    "joint_L": ("+Z", "top plate down; supports under the lower deck"),
    "joint_R": ("+Z", "top plate down; supports under the lower deck"),
    "front_idler_L": ("-Y", "front wall down"),
    "front_idler_R": ("-Y", "front wall down"),
    "rear_corner_L_base": ("-Z", "plate down; supports under the bearing bridge"),
    "rear_corner_R_base": ("-Z", "plate down; supports under the bearing bridge"),
    "rear_corner_L_top": ("-Z", "as fitted: layers in the plate; supports under the plate and feet"),
    "rear_corner_R_top": ("-Z", "as fitted: the motor face prints as a clean top surface; supports under the plate"),
    "dock_bracket_L": ("-X", "upright plate down"),
    "dock_bracket_R": ("+X", "upright plate down"),
    "station_bracket_L": ("-X", "upright plate down"),
    "station_bracket_R": ("+X", "upright plate down"),
    **{f"station_cradle_T{i}": ("-Z", "floor down; supports under the crossbar and the pad shelf") for i in range(5)},
    **{f"purge_bucket_T{i}": ("-Z", "floor down, open top up; the flange and back overhangs print unsupported")
       for i in range(5)},
}
SUPPORT = {"carriage", "joint_L", "joint_R", "front_idler_L", "front_idler_R", "rear_corner_L_base",
           "rear_corner_R_base", "rear_corner_L_top", "rear_corner_R_top",
           *(f"station_cradle_T{i}" for i in range(5))}

# rotation (axis, degrees) that takes the named direction to -Z
TURN = {"-Z": None, "+Z": (V(1, 0, 0), 180), "-Y": (V(1, 0, 0), 90), "+Y": (V(1, 0, 0), -90),
        "-X": (V(0, 1, 0), -90), "+X": (V(0, 1, 0), 90)}


def main():
    os.makedirs(OUT, exist_ok=True)
    report = []
    for name, (down, why) in ORIENT.items():
        s = Part.Shape()
        s.read(os.path.join(PARTS, name + ".brep"))
        if TURN[down]:
            s.rotate(V(0, 0, 0), *TURN[down])
        bb = s.BoundBox
        s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
        bb = s.BoundBox
        contact = sum(f.Area for f in s.Faces if f.Surface.TypeId == "Part::GeomPlane"
                      and f.BoundBox.ZMax < 1e-3 and f.normalAt(0, 0).z < -0.999)
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.3, Relative=False)
        m.write(os.path.join(OUT, name + ".stl"))
        rec = {"part": name, "down": down, "why": why, "support": name in SUPPORT,
               "size_mm": [round(bb.XLength, 1), round(bb.YLength, 1), round(bb.ZLength, 1)],
               "bed_contact_mm2": round(contact), "volume_cm3": round(s.Volume / 1000, 2),
               "solid": m.isSolid(), "non_manifold": m.hasNonManifolds()}
        report.append(rec)
        print(f"{name:22s} {down}  {rec['size_mm']}  contact {rec['bed_contact_mm2']:5d} mm2  "
              f"support {rec['support']!s:5s} solid {rec['solid']} non-manifold {rec['non_manifold']}")
    with open(os.path.join(OUT, "..", "orientation.json"), "w") as f:
        json.dump(report, f, indent=1)


main()
