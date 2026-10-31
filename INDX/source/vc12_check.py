"""Assemble the conversion at many poses and report every overlap.

  VC12_CONTEXT=<stock_context.brep> VC12_INDX=<INDX FCStd> [VC12_ARMS=<arms_bed.brep>] [VC12_INDX_DIR=<Bondtech INDX files>]
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_check.py [--station | --export-pose xc,yg]

The stock context is the owner's V-Core 4.1 500 IDEX model with every assembly this
conversion removes taken out (motor stacks, tensioners, X gantry parts, IDEX belts and
toolheads, top panel, door, bed and Y blocks; the moving ones are rebuilt here).
"""
import json
import math
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Mesh  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_params as P  # noqa: E402
from vc12_build import box, cyl_z  # noqa: E402

PARTS = os.path.join(HERE, "..", "parts")
INDX_DIR = os.environ.get(                  # Bondtech's INDX STEP and duct STLs
    "VC12_INDX_DIR", os.path.expanduser("~/Library/CloudStorage/Dropbox/3D Printing/Prusa/INDX"))
MIN_VOL = 0.5          # mm3 counted as a clash


def load(name):
    s = Part.Shape()
    s.read(os.path.join(PARTS, name + ".brep"))
    return s


def moved(s, dx=0.0, dy=0.0, dz=0.0):
    c = s.copy()
    c.translate(V(dx, dy, dz))
    return c


# ------------------------------------------------------------------ purchased parts
def smooth_idler(x, y, z):
    h = P.SMOOTH_IDLER["length"] / 2
    return cyl_z(x, y, 15.0, z - 8, z + 8).fuse(cyl_z(x, y, 19.0, z - h, z - 8)).fuse(cyl_z(x, y, 19.0, z + 8, z + h))


def toothed_idler(x, y, z):
    return cyl_z(x, y, 12.22, z - 6.5, z + 6.5).fuse(cyl_z(x, y, 15.0, z - 8, z - 6.5)).fuse(cyl_z(x, y, 15.0, z + 6.5, z + 8))


def drive_pulley(x, y, z, hub_down):
    p = cyl_z(x, y, 12.22, z - 6.5, z + 6.5).fuse(cyl_z(x, y, 15.0, z - 7.5, z - 6.5)).fuse(cyl_z(x, y, 15.0, z + 6.5, z + 7.5))
    return p.fuse(cyl_z(x, y, 14.0, z - 14.5, z - 7.5) if hub_down else cyl_z(x, y, 14.0, z + 7.5, z + 14.5))


def nema17(x, y, face_z, up):
    """Motor whose mounting face is at face_z; up=True means the shaft points up."""
    if up:
        return box(x - 21.15, x + 21.15, y - 21.15, y + 21.15, face_z - 48, face_z).fuse(
            cyl_z(x, y, 22.0, face_z, face_z + 2)).fuse(cyl_z(x, y, 5.0, face_z, face_z + 35))
    return box(x - 21.15, x + 21.15, y - 21.15, y + 21.15, face_z, face_z + 48).fuse(
        cyl_z(x, y, 22.0, face_z - 2, face_z)).fuse(cyl_z(x, y, 5.0, face_z - 35, face_z))


# ------------------------------------------------------------------ belts
def belt_solids(xc, yg):
    out = {}
    for plane, zc in (("A", P.PLANE_A), ("B", P.PLANE_B)):
        items, _ = P.belt_path(plane, xc, yg)
        z0 = zc - P.BELT_W / 2
        tooth, back = P.BELT_T - P.BELT_PITCH_FROM_BACK, P.BELT_PITCH_FROM_BACK
        pieces = []
        for it in items:
            if it[0] == "line":
                (x1, y1), (x2, y2) = it[1], it[2]
                L = math.hypot(x2 - x1, y2 - y1)
                if L < 1e-6:
                    continue
                nx, ny = -(y2 - y1) / L, (x2 - x1) / L      # left normal = tooth side
                pts = [V(x1 + nx * tooth, y1 + ny * tooth, z0), V(x2 + nx * tooth, y2 + ny * tooth, z0),
                       V(x2 - nx * back, y2 - ny * back, z0), V(x1 - nx * back, y1 - ny * back, z0)]
                pts.append(pts[0])
                pieces.append(Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, P.BELT_W)))
            else:
                _, name, c, r, s, a0, sweep = it
                rin, rout = (r - tooth, r + back) if s > 0 else (r - back, r + tooth)
                n = max(4, int(math.degrees(sweep) / 6))
                angs = [a0 + s * sweep * i / n for i in range(n + 1)]
                pts = [V(c[0] + rout * math.cos(a), c[1] + rout * math.sin(a), z0) for a in angs]
                pts += [V(c[0] + rin * math.cos(a), c[1] + rin * math.sin(a), z0) for a in reversed(angs)]
                pts.append(pts[0])
                pieces.append(Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, P.BELT_W)))
        for k, pc in enumerate(pieces):
            out[f"belt_{plane}_{k:02d}"] = pc
    return out


OWN = {  # a belt legitimately touches its own wraps and its own carriage clamp entry
    "belt_A": {"J_LF", "F_L", "R1_L", "M_L", "R2_L", "C_RA", "J_RR"},
    "belt_B": {"J_LR", "C_LB", "R2_R", "M_R", "R1_R", "F_R", "J_RF"},
}


# ------------------------------------------------------------------ INDX
def indx_shapes():
    doc = App.openDocument(os.environ["VC12_INDX"])
    def path(o):
        p, cur = [], o
        while cur is not None:
            p.append(cur.Label)
            cur = cur.getParentGeoFeatureGroup()
        return "/".join(reversed(p))
    head, held, dock, parked = [], [], [], []
    for o in doc.Objects:
        if o.TypeId != "Part::Feature":
            continue
        pth = path(o)
        s = o.Shape.copy()
        s.Placement = o.getGlobalPlacement()
        if not s.Solids:
            continue
        if any(k in pth for k in ("INDX Toolhead/SOLID", "PCB Cover", "Strain relief", "Front cover", "X-carriage 02PRT00364 (1)/SOLID")):
            head.append(s)
        elif "Nozzle tool closed" in pth:
            held.append(s)
        elif "Tool Dock 1515 Makerbeam" in pth:
            dock.append(s)
        elif "Nozzle tool open" in pth:
            parked.append(s)
    for f in ("INDX_4010_Duct_Left.stl", "INDX_4010_Duct_Right.stl"):
        b = Mesh.Mesh(os.path.join(INDX_DIR, f)).BoundBox      # duct envelope: fast and conservative
        head.append(Part.makeBox(b.XLength, b.YLength, b.ZLength, V(b.XMin, b.YMin, b.ZMin)))
    return [Part.makeCompound(x) for x in (head, held, dock, parked)]


def place_indx(s, xc, yg):
    c = s.copy()
    c.rotate(V(0, 0, 0), V(1, 0, 0), 90)           # INDX Y up -> printer Z up, INDX +Z -> printer -Y
    c.translate(V(xc, yg + P.INDX_NOZZLE_DY, P.TIP_Z + 31.5))
    return c


# ------------------------------------------------------------------ the machine
def fixed_parts(indx, pull=0.0, pulled=None):
    f = {}
    for tag in ("L", "R"):
        for n in ("front_idler", "rear_corner_{}_base", "rear_corner_{}_top", "dock_bracket"):
            name = n.format(tag) if "{}" in n else f"{n}_{tag}"
            f[name] = load(name)
    zA, zB = P.PLANE_A, P.PLANE_B
    f["F_L"] = smooth_idler(-P.CORNER_X, P.FRONT_IDLER_Y, zA)
    f["F_R"] = smooth_idler(P.CORNER_X, P.FRONT_IDLER_Y, zB)
    f["R1_L"] = smooth_idler(-P.CORNER_X, P.R1_Y, zA)
    f["R2_L"] = smooth_idler(-P.CORNER_X, P.CORNER_Y, zA)
    f["C_LB"] = smooth_idler(-P.CORNER_X, P.CORNER_Y, zB)
    f["R1_R"] = smooth_idler(P.CORNER_X, P.R1_Y, zB)
    f["R2_R"] = smooth_idler(P.CORNER_X, P.CORNER_Y, zB)
    f["C_RA"] = smooth_idler(P.CORNER_X, P.CORNER_Y, zA)
    f["M_L"] = drive_pulley(-P.MOTOR_X, P.MOTOR_Y, zA, hub_down=True)
    f["M_R"] = drive_pulley(P.MOTOR_X, P.MOTOR_Y, zB, hub_down=False)
    f["motor_L"] = nema17(-P.MOTOR_X, P.MOTOR_Y, 684.0, up=True)
    f["motor_R"] = nema17(P.MOTOR_X, P.MOTOR_Y, zB + 9 + 10.5 + 0.5, up=False)
    f["bearing_L"] = cyl_z(-P.MOTOR_X, P.MOTOR_Y, 16.0, 713.5, 718.5)
    f["bearing_R"] = cyl_z(P.MOTOR_X, P.MOTOR_Y, 16.0, 710.0, 715.0)
    for tag, sx in (("L", -1), ("R", 1)):
        f[f"y_rail_{tag}"] = box(sx * P.Y_RAIL_X - 6, sx * P.Y_RAIL_X + 6, P.Y_RAIL_Y[0], P.Y_RAIL_Y[1], *P.Y_RAIL_Z)
    f["station_rail_1515"] = box(-369.5, 369.5, P.STATION_RAIL_Y - 7.5, P.STATION_RAIL_Y + 7.5,
                                 P.STATION_RAIL_Z - 7.5, P.STATION_RAIL_Z + 7.5)
    for tag in ("L", "R"):
        f[f"station_bracket_{tag}"] = load(f"station_bracket_{tag}")
    for k in range(P.INDX_TOOLS):
        f[f"station_cradle_T{k}"] = load(f"station_cradle_T{k}")
        bucket = load(f"purge_bucket_T{k}")
        f[f"purge_bucket_T{k}"] = moved(bucket, dy=-pull) if pull and pulled in (None, k) else bucket
        f[f"wiper_pad_T{k}"] = box(P.PAD_X[k], P.PAD_X[k] + P.PAD[0], P.PAD_REAR_Y - P.PAD[1], P.PAD_REAR_Y,
                                   P.WIPER_TOP - P.PAD[2], P.WIPER_TOP)
    f["dock_bar_1515"] = box(-369.5, 369.5, P.DOCK_BAR_Y - 7.5, P.DOCK_BAR_Y + 7.5, P.DOCK_BAR_Z - 7.5, P.DOCK_BAR_Z + 7.5)
    head, held, dock, parked = indx
    for i, x in enumerate(P.DOCK_X):
        f[f"dock_T{i}"] = place_indx(dock, x, P.YG_DOCK)
        f[f"parked_T{i}"] = place_indx(parked, x, P.YG_DOCK)
    if P.DOOR_SPACER > 0:                     # otherwise the stock door (in the context) stays where it is
        door = P.DOOR_IN_Y - P.DOOR_SPACER
        f["door_moved"] = box(-400, 400, door - 4, door, 31.1, 981.1)
    f["bed_at_tip"] = box(-P.BED_X, P.BED_X, P.BED_Y[0], P.BED_Y[1], P.TIP_Z - 9.5, P.TIP_Z)
    return f


def moving_parts(xc, yg, indx):
    m = {}
    m["joint_L"] = moved(load("joint_L"), dy=yg)
    m["joint_R"] = moved(load("joint_R"), dy=yg)
    m["J_LF"] = toothed_idler(-P.J_F_X, yg + P.J_F_DY, P.PLANE_A)
    m["J_LR"] = smooth_idler(-P.J_R_X, yg + P.J_R_DY, P.PLANE_B)
    m["J_RF"] = toothed_idler(P.J_F_X, yg + P.J_F_DY, P.PLANE_B)
    m["J_RR"] = smooth_idler(P.J_R_X, yg + P.J_R_DY, P.PLANE_A)
    m["beam"] = box(-P.BEAM_HALF_L, P.BEAM_HALF_L, yg - P.BEAM_HALF_W, yg + P.BEAM_HALF_W, *P.BEAM_Z)
    m["x_rail"] = box(-P.X_RAIL_HALF_L, P.X_RAIL_HALF_L, yg - 6, yg + 6, *P.X_RAIL_Z)
    m["x_block"] = box(xc - 17.35, xc + 17.35, yg - P.X_BLOCK_HALF_W, yg + P.X_BLOCK_HALF_W, *P.X_BLOCK_Z)
    for tag, sx in (("L", -1), ("R", 1)):
        m[f"y_block_{tag}"] = box(sx * P.Y_RAIL_X - 13.5, sx * P.Y_RAIL_X + 13.5, yg - 17.25, yg + 17.25, *P.Y_BLOCK_Z)
    m["carriage"] = moved(load("carriage"), dx=xc, dy=yg)
    for i in range(1, 5):
        m[f"cap_{i}"] = moved(load(f"carriage_clamp_cap_{i}"), dx=xc, dy=yg)
    head, held, dock, parked = indx
    m["indx_head"] = place_indx(head, xc, yg)
    m["indx_held_tool"] = place_indx(held, xc, yg)
    m.update(belt_solids(xc, yg))
    return m


def ok_pair(a, b):
    """Pairs whose contact is by design."""
    pair = {a[:6] if a.startswith("belt_") else a, b[:6] if b.startswith("belt_") else b}
    if len(pair) == 1:
        return True
    for belt, own in OWN.items():
        if belt in pair:
            other = (pair - {belt}).pop()
            if other in own or other in ("carriage",) or other.startswith("cap_"):
                return True
    designed = [{"carriage", "x_block"}, {"x_block", "x_rail"}, {"x_rail", "beam"}, {"carriage", "indx_head"},
                {"indx_head", "indx_held_tool"}, {"joint_L", "beam"}, {"joint_R", "beam"},
                {"joint_L", "y_block_L"}, {"joint_R", "y_block_R"}, {"joint_L", "J_LF"}, {"joint_L", "J_LR"},
                {"joint_R", "J_RF"}, {"joint_R", "J_RR"}, {"y_block_L", "y_rail_L"}, {"y_block_R", "y_rail_R"},
                {"M_L", "motor_L"}, {"M_R", "motor_R"}, {"motor_L", "bearing_L"}, {"motor_R", "bearing_R"},
                {"dock_bar_1515", "dock_T0"}, {"dock_bar_1515", "dock_T1"}, {"dock_bar_1515", "dock_T2"},
                {"dock_bar_1515", "dock_T3"}, {"dock_bar_1515", "dock_T4"},
                {"station_rail_1515", "station_bracket_L"}, {"station_rail_1515", "station_bracket_R"},
                *[{"station_rail_1515", f"station_cradle_T{k}"} for k in range(P.INDX_TOOLS)],
                *[{f"station_cradle_T{k}", f"purge_bucket_T{k}"} for k in range(P.INDX_TOOLS)],
                *[{f"station_cradle_T{k}", f"wiper_pad_T{k}"} for k in range(P.INDX_TOOLS)]]
    if pair in designed or (pair & {"carriage"} and any(x.startswith("cap_") for x in pair)):
        return True
    return False


def common_vol(a, b):
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0
    try:
        return a.common(b).Volume
    except Exception:
        return -1.0


def check(poses, ctx, indx):
    fixed = fixed_parts(indx)
    report = {"fixed_vs_context": [], "poses": []}
    for n, s in fixed.items():
        for k, cs in enumerate(ctx):
            v = common_vol(s, cs)
            if v > MIN_VOL or v < 0:
                report["fixed_vs_context"].append([n, CTX_NAMES[k], round(v, 2)])
    fixed_names = list(fixed)
    for i, a in enumerate(fixed_names):
        for b in fixed_names[i + 1:]:
            if ok_pair(a, b) or ({a, b} & {"dock_bar_1515"} and any(x.startswith("dock_") for x in {a, b})):
                continue
            if any(x.startswith("dock_T") for x in (a, b)) and any(x.startswith("parked_T") for x in (a, b)):
                continue
            v = common_vol(fixed[a], fixed[b])
            if v > MIN_VOL or v < 0:
                report["fixed_vs_context"].append([a, b, round(v, 2)])
    for xc, yg, tag in poses:
        mov = moving_parts(xc, yg, indx)
        hits = []
        names = list(mov)
        for a in names:
            for b, fs in fixed.items():
                if ok_pair(a, b):
                    continue
                if tag in ("pickup", "front_stop") and a.startswith("indx_") and abs(P.DOCK_X[tag_dock(xc)] - xc) < 1 and b in (f"dock_T{tag_dock(xc)}", f"parked_T{tag_dock(xc)}"):
                    continue
                if tag in ("pickup", "front_stop") and a == "indx_head" and b == "dock_bar_1515":
                    continue    # the rail sits in the head's slot at pickup; checked with the real duct meshes
                if tag in ("clearance", "clear_move") and a == "indx_head" and b.startswith(("dock_T", "parked_T")):
                    continue    # the boxed ducts are too coarse here; checks/clearance_sweep.txt uses the real ducts
                v = common_vol(mov[a], fs)
                if v > MIN_VOL or v < 0:
                    hits.append([a, b, round(v, 2)])
            for k, cs in enumerate(ctx):
                if CTX_NAMES[k].startswith("Electronics Enclosure"):
                    continue                      # behind the rear 3030; nothing moving gets within 60 mm
                v = common_vol(mov[a], cs)
                if v > MIN_VOL or v < 0:
                    hits.append([a, CTX_NAMES[k], round(v, 2)])
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if ok_pair(a, b):
                    continue
                v = common_vol(mov[a], mov[b])
                if v > MIN_VOL or v < 0:
                    hits.append([a, b, round(v, 2)])
        report["poses"].append({"xc": xc, "yg": yg, "tag": tag, "hits": hits})
        print(f"pose xc {xc:7.1f} yg {yg:7.1f} {tag:9s} hits {len(hits)}" + ("" if not hits else ": " + "; ".join(f"{a}~{b} {v}" for a, b, v in hits[:6])), flush=True)
    return report


def tag_dock(xc):
    return min(range(len(P.DOCK_X)), key=lambda i: abs(P.DOCK_X[i] - xc))


CTX_NAMES = []


def load_context():
    global CTX_NAMES
    c = Part.Shape()
    c.read(os.environ["VC12_CONTEXT"])
    names = json.load(open(os.environ["VC12_CONTEXT"].replace(".brep", "_names.json")))
    solids = [x for x in c.childShapes()]
    region = Part.makeBox(820, 760, 200, V(-410, -380, 630)).BoundBox
    keep, CTX_NAMES = [], []
    for n, x in zip(names, solids):
        if REMOVED.search(n) or not x.BoundBox.intersect(region):
            continue
        keep.append(x)
        CTX_NAMES.append(n)
    return keep


import re  # noqa: E402
REMOVED = re.compile(r"Y-Axis Bumper|Y-Axis Endstop|PTFE Filament Guide - 500 - IDEX")  # come off in the conversion


def poses():
    out = []
    for xc in (-P.XC_STOP, P.DOCK_X[0], P.DOCK_X[2], P.DOCK_X[-1], P.XC_STOP):
        for yg, tag in ((P.YG_FRONT_STOP, "front_stop"), (P.YG_DOCK + P.INDX_CLEARANCE, "clearance"), (0.0, "mid"),
                        (P.YG_REAR_STOP, "rear_stop")):
            if tag == "front_stop" and xc not in P.DOCK_X:
                continue        # the head only comes forward of the clearance line at a dock or a purge spot
            out.append((xc, yg, tag))
    for i in range(len(P.DOCK_X) - 1):                                        # X moves along the clearance line
        for f in (0.25, 0.5):
            out.append((P.DOCK_X[i] + f * P.INDX_DOCK_PITCH, P.YG_DOCK + P.INDX_CLEARANCE, "clear_move"))
    for x in P.DOCK_X:
        out.append((x, P.YG_DOCK, "pickup"))
    return out


def real_duct_head(indx):
    """The head with Bondtech's real 4010 duct meshes instead of their boxes (the stations sit 47 / 49 mm from
    the docks, inside the boxes' reach but clear of the real ducts)."""
    head, held, dock, parked = indx
    core = [s for s in head.Solids if not (abs(s.BoundBox.XLength - 27.2) < 0.3 and s.BoundBox.YLength > 100)]
    for f in ("INDX_4010_Duct_Left.stl", "INDX_4010_Duct_Right.stl"):
        sh = Part.Shape()
        sh.makeShapeFromMesh(Mesh.Mesh(os.path.join(INDX_DIR, f)).Topology, 0.05)
        core.append(Part.makeSolid(sh).removeSplitter())
    return (Part.makeCompound(core), held, dock, parked)


MARGIN = 4.0      # station poses are also checked with the head this much closer to the dock beside it


def station_poses():
    """Per tool: purge spot, both ends of the wipe stroke, 15 mm back on the way in and out, the front stop, and
    the two poses nearest a dock again with the head MARGIN closer to that dock."""
    out = []
    for k, px in enumerate(P.PURGE_X):
        a, b = px + P.WIPE_X[0], px + P.WIPE_X[1]
        out += [(px, 15.0, f"T{k}_approach"), (px, 0.0, f"T{k}_purge"), (px, -1.0, f"T{k}_front_stop"),
                (a, 0.0, f"T{k}_wipe_left"), (b, 0.0, f"T{k}_wipe_right"), (a, 15.0, f"T{k}_leave"),
                (px - MARGIN, 0.0, f"T{k}_purge_-{MARGIN:.0f}mm"), (b + MARGIN, 0.0, f"T{k}_wipe_right_+{MARGIN:.0f}mm")]
    return out


def station_check(ctx, indx, arms):
    """Purge and wipe poses, the bed arms at the top of their travel, and each bucket slid out."""
    rep = {"fixed_vs_context": [], "poses": [], "bucket_pull": []}
    fixed = fixed_parts(indx)
    new = [n for n in fixed if n.startswith(("station_", "purge_", "wiper_"))]
    for n in new:
        for k, cs in enumerate(ctx + arms):
            v = common_vol(fixed[n], cs)
            if v > MIN_VOL or v < 0:
                rep["fixed_vs_context"].append([n, (CTX_NAMES + ARM_NAMES)[k], round(v, 2)])
        for m, fs in fixed.items():
            if m == n or ok_pair(n, m) or (m in new and new.index(m) < new.index(n)):
                continue
            v = common_vol(fixed[n], fs)
            if v > MIN_VOL or v < 0:
                rep["fixed_vs_context"].append([n, m, round(v, 2)])
    gaps = {}
    for n in new:                              # closest approach of each station part to the arms (at the top)
        gaps[n] = round(min(fixed[n].distToShape(a)[0] for a in arms), 2)
    rep["station_to_bed_arms_mm"] = gaps
    print("station parts to bed arms (mm):", min(gaps.values()), flush=True)
    real = real_duct_head(indx)
    for xc, back, tag in station_poses():
        mov = moving_parts(xc, P.YG_DOCK + back, real)
        own = f"wiper_pad_{tag[:2]}"
        hits = []
        for a in ("indx_head", "indx_held_tool", "carriage"):
            for b, fs in fixed.items():
                if ok_pair(a, b) or (a == "indx_head" and b == "dock_bar_1515"):
                    continue
                if a == "indx_held_tool" and "wipe" in tag and b == own:
                    continue                   # the nozzle drags across its own pad
                v = sum(common_vol(x, fs) for x in mov[a].Solids)   # solid by solid: skips far duct meshes
                if v > MIN_VOL or v < 0:
                    hits.append([a, b, round(v, 2)])
        touches = [b for b in fixed if b.startswith("wiper_pad_") and common_vol(mov["indx_held_tool"], fixed[b]) > 0.01]
        rep["poses"].append({"xc": xc, "back": back, "tag": tag, "hits": hits, "nozzle_touches": touches})
        print(f"{tag:22s} xc {xc:6.1f} back {back:4.1f}: hits {hits}  nozzle touches {touches}", flush=True)
    for k in range(P.INDX_TOOLS):
        for pull in (0.0, 20.0, 40.0, P.BUCKET_PULL):
            fx = fixed_parts(indx, pull, pulled=k)
            me = f"purge_bucket_T{k}"
            hits = []
            for b, fs in fx.items():
                if b in (me, "door_moved") or (b == f"station_cradle_T{k}" and 0 < pull < 20):
                    continue                   # 0-17 mm: the bucket rides 0.5 mm up over the detent ridge
                v = common_vol(fx[me], fs)
                if v > MIN_VOL or v < 0:
                    hits.append([b, round(v, 2)])
            for j, cs in enumerate(ctx):
                if "Panel Assembly - Door" in CTX_NAMES[j]:
                    continue                   # the door is open while the bucket comes out
                v = common_vol(fx[me], cs)
                if v > MIN_VOL or v < 0:
                    hits.append([CTX_NAMES[j], round(v, 2)])
            rep["bucket_pull"].append({"tool": k, "pull": pull, "hits": hits})
            print(f"bucket T{k} pulled {pull:4.0f} mm: hits {hits}", flush=True)
    return rep


ARM_NAMES = []


def load_arms():
    """Front bed arms, Z carriages and bed plate at the top of their travel (stock model pose), raised bed."""
    global ARM_NAMES
    c = Part.Shape()
    c.read(os.environ["VC12_ARMS"])
    names = json.load(open(os.environ["VC12_ARMS"].replace(".brep", "_names.json")))
    out = []
    for n, x in zip(names, c.childShapes()):
        if "Bed Plate" in n or "FlexPlate" in n:
            x = moved(x, dz=P.TIP_Z - 671.4)             # bed raised; its top at the nozzle tip
        out.append(x)
        ARM_NAMES.append(n)
    return out


if __name__ == "__main__":
    indx = indx_shapes()
    if "--station" in sys.argv:
        ctx = load_context()
        rep = station_check(ctx, indx, load_arms())
        outdir = os.path.join(HERE, "..", "checks")
        json.dump(rep, open(os.path.join(outdir, "station_report.json"), "w"), indent=1)
        print("fixed:", rep["fixed_vs_context"])
        sys.exit(0)
    if "--export-pose" in sys.argv:
        xc, yg = (float(v) for v in sys.argv[sys.argv.index("--export-pose") + 1].split(","))
        allp = dict(fixed_parts(indx))
        allp.update(moving_parts(xc, yg, indx))
        outdir = os.path.join(HERE, "..", "checks")
        os.makedirs(outdir, exist_ok=True)
        Part.makeCompound(list(allp.values())).exportStep(os.path.join(outdir, f"assembly_xc{xc:+.0f}_yg{yg:+.0f}.step"))
        print("exported", len(allp))
        sys.exit(0)
    ctx = load_context()
    print("context solids", len(ctx), flush=True)
    rep = check(poses(), ctx, indx)
    outdir = os.path.join(HERE, "..", "checks")
    os.makedirs(outdir, exist_ok=True)
    json.dump(rep, open(os.path.join(outdir, "interference_report.json"), "w"), indent=1)
    print("fixed vs context/fixed:", rep["fixed_vs_context"])
    print("poses with hits:", sum(1 for p in rep["poses"] if p["hits"]), "of", len(rep["poses"]))
