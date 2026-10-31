"""Write the full conversion assembly as two STEP files for SolidCraft.

  VC12_STOCK=<owner's V-Core FCStd> VC12_INDX=<INDX FCStd>
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_assembly.py <stock_out.step> <new_out.step>

stock_out: the owner's V-Core 4.1 500 IDEX model with every part this conversion removes taken
out, the bed raised 20 mm on new spacers and shown 50 mm below its top, and the door moved 13 mm
forward when P.DOOR_SPACER is set (it is 0: the docks sit 5 mm further back instead). new_out: the PPS-CF parts, purchased motion parts, belts and the INDX head, docks and
rail, at carriage X 0 with the gantry where the stock model has it (beam centre Y -21.2).
"""
import os
import re
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Import  # noqa: E402
import Mesh  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_check as K  # noqa: E402
import vc12_params as P  # noqa: E402

XC, YG = 0.0, -21.2          # carriage centred; gantry where the stock model has it
BED_DROP = 50.0              # show the bed below its (raised) top
STOCK_T0_XC = -309.8

REMOVE = re.compile(
    r"Motor Assembly - Hybrid|Tensioner - |Belts - 500 - IDEX|Toolhead - IDEX|PTFE Guide \(Upper\)|"
    r"PTFE Filament Guide - 500 - IDEX|_Umbilical - 500 - IDEX|Y-Axis Bumper|Y-Axis Endstop")
GANTRY_KEEP = re.compile(r"vc41_x-gantry_500|Linear Rail - MGN12 675mm|_MGN12C Carriage v017")


def path_of(o):
    p, cur = [], o
    while cur is not None:
        p.append(cur.Label)
        cur = cur.getParentGeoFeatureGroup()
    return "/".join(reversed(p))


def stock_groups(fc):
    doc = App.openDocument(fc)
    groups = {}
    moved = {"bed spacers removed": 0}
    for o in doc.Objects:
        if o.TypeId != "Part::Feature":
            continue
        pth = path_of(o)
        parts = pth.split("/")
        top = parts[1] if len(parts) > 1 else parts[0]
        if REMOVE.search(pth):
            continue
        if top.startswith("X-Gantry Assembly") and not GANTRY_KEEP.search(pth):
            continue
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        if not s.Solids:
            continue
        if "_MGN12C Carriage v017" in pth:                   # keep one X block, under the new carriage
            s.translate(V(XC - STOCK_T0_XC, 0, 0))
            top = "X block (stock MGN12C)"
        elif top.startswith("X-Gantry Assembly"):
            top = "X gantry (stock steel beam + MGN12 rail)"
        elif top.startswith("Bed Assembly"):
            if "Aluminium Spacer - 6mm" in pth:
                moved["bed spacers removed"] += 1
                continue                                      # replaced by the 32 mm spacers
            if "Steel Ball" in pth:
                s.translate(V(0, 0, -BED_DROP))
            else:
                s.translate(V(0, 0, P.BED_RAISE - BED_DROP))
            top = "Bed (raised 20 mm, shown 50 mm down)"
        elif top.startswith("Arm Assembly") or "_SRH15 Carriage" in pth:
            s.translate(V(0, 0, -BED_DROP))
            top = "Bed arms and Z carriages (shown 50 mm down)"
        elif top.startswith("Panel Assembly - Door") and P.DOOR_SPACER > 0:
            s.translate(V(0, -P.DOOR_SPACER, 0))
            top = f"Door ({P.DOOR_SPACER:.0f} mm forward)"
        groups.setdefault(top, []).append(s)
    App.closeDocument(doc.Name)
    print("stock groups", len(groups), "bodies", sum(len(v) for v in groups.values()), moved)
    return groups


def new_items():
    indx = K.indx_shapes()
    head, held, dock, parked = indx
    # real duct meshes for display (the checks use their boxes)
    heads = [s for s in head.Solids if not (abs(s.BoundBox.XLength - 27.2) < 0.3 and s.BoundBox.YLength > 100)]
    for f in ("INDX_4010_Duct_Left.stl", "INDX_4010_Duct_Right.stl"):
        m = Mesh.Mesh(os.path.join(K.INDX_DIR, f))
        sh = Part.Shape()
        sh.makeShapeFromMesh(m.Topology, 0.05)
        heads.append(Part.makeSolid(sh))
    head = Part.makeCompound(heads)
    fixed = K.fixed_parts((head, held, dock, parked))
    moving = K.moving_parts(XC, YG, (head, held, dock, parked))
    out = {}
    printed = ("joint_L", "joint_R", "carriage", "front_idler_L", "front_idler_R", "rear_corner_L_base",
               "rear_corner_L_top", "rear_corner_R_base", "rear_corner_R_top", "dock_bracket_L", "dock_bracket_R",
               "station_bracket_L", "station_bracket_R",
               *(f"station_cradle_T{i}" for i in range(P.INDX_TOOLS)), *(f"purge_bucket_T{i}" for i in range(P.INDX_TOOLS)))
    labels = {
        "F_L": "IDLER smooth F_L (front left, belt A)", "F_R": "IDLER smooth F_R (front right, belt B)",
        "R1_L": "IDLER smooth R1_L", "R2_L": "IDLER smooth R2_L", "C_LB": "IDLER smooth C_LB (belt B corner)",
        "R1_R": "IDLER smooth R1_R", "R2_R": "IDLER smooth R2_R", "C_RA": "IDLER smooth C_RA (belt A corner)",
        "J_LF": "IDLER toothed J_LF", "J_RF": "IDLER toothed J_RF", "J_LR": "IDLER smooth J_LR", "J_RR": "IDLER smooth J_RR",
        "M_L": "PULLEY 20T 12mm motor A", "M_R": "PULLEY 20T 12mm motor B",
        "motor_L": "MOTOR A (stock NEMA17, under left rear corner)", "motor_R": "MOTOR B (stock NEMA17, on right rear corner)",
        "bearing_L": "BEARING 625ZZ motor A", "bearing_R": "BEARING 625ZZ motor B",
        "dock_bar_1515": "INDX dock rail 1515 x 739",
        "station_rail_1515": "STATION rail 1515 x 739 (purge and wipe)",
        "indx_head": "INDX Smart Head + radial cooling", "indx_held_tool": "INDX tool T0 (on head)",
    }
    for n, s in list(fixed.items()) + list(moving.items()):
        if n in ("door_moved", "bed_at_tip", "beam", "x_rail", "x_block", "y_block_L", "y_block_R", "y_rail_L", "y_rail_R"):
            continue                       # the stock model carries the real ones
        if n.startswith("belt_"):
            continue
        if n in printed:
            out["PPS-CF " + n] = s
        elif n.startswith("cap_"):
            out["PPS-CF carriage clamp cap " + n[-1]] = s
        elif n.startswith("dock_T"):
            out[f"INDX dock {n[-2:]}"] = s
        elif n.startswith("wiper_pad_T"):
            out[f"WIPER Qidi pad {n[-2:]}"] = s
        elif n.startswith("parked_T"):
            out[f"INDX tool {n[-2:]} (parked)"] = s
        else:
            out[labels.get(n, n)] = s
    for plane in ("A", "B"):
        out[f"BELT {plane} 12mm ({'lower' if plane == 'A' else 'upper'})"] = Part.makeCompound(
            [s for n, s in moving.items() if n.startswith(f"belt_{plane}_")])
    # new bed spacers: one 32 mm spacer per kinematic ball, ball top to plate underside
    for i, (bx, by) in enumerate(((0.0, 206.5), (-254.5, -302.5), (254.5, -302.5))):
        z0 = 649.9 - BED_DROP
        out[f"NEW bed spacer 32mm {i + 1}"] = Part.makeCylinder(5.0, 12.0 + P.BED_RAISE, V(bx, by, z0))
    return out


def export(named, path):
    doc = App.newDocument("vc12export")
    objs = []
    for name, shp in named.items():
        o = doc.addObject("Part::Feature", re.sub(r"[^A-Za-z0-9_]+", "_", name)[:60])
        o.Label = name
        o.Shape = shp
        objs.append(o)
    Import.export(objs, path)
    App.closeDocument(doc.Name)
    print("wrote", path, len(objs))


if __name__ == "__main__":
    stock_out, new_out = sys.argv[1], sys.argv[2]
    new = new_items()
    export(new, new_out)
    groups = stock_groups(os.environ["VC12_STOCK"])
    export({"STOCK " + k: Part.makeCompound(v) for k, v in groups.items()}, stock_out)
