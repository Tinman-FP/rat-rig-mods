"""Build the PPS-CF parts for the V-Core 4.1 500 12 mm CoreXY + INDX conversion.

Run with FreeCAD's own Python (not freecadcmd, whose exec breaks __file__):
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_build.py

Every part is built in the printer frame (see vc12_params) at Yg = 0, xc = 0 and
written to ../parts as <name>.brep (for the checks) and <name>.step. Each body's edges are rounded
(soften) before its holes are cut; ../checks/rounding_report.json lists what was rounded per part.
"""
import math
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
import numpy as np  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_params as P  # noqa: E402

OUT = os.path.join(HERE, "..", "parts")

# fastener holes
M3, M3_INSERT, M3_CB, M3_NUT = 3.4, 4.0, 6.5, 6.4      # clearance, heat-set, head, nut across corners
M4, M4_INSERT = 4.5, 5.6
M5, M5_CB, M5_NUT = 5.5, 9.5, 9.3
M6, M6_CB = 6.5, 11.0


def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_z(x, y, d, z0, z1):
    z0, z1 = sorted((z0, z1))
    return Part.makeCylinder(d / 2, z1 - z0, V(x, y, z0), V(0, 0, 1))


def cyl_y(x, z, d, y0, y1):
    y0, y1 = sorted((y0, y1))
    return Part.makeCylinder(d / 2, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_x(y, z, d, x0, x1):
    x0, x1 = sorted((x0, x1))
    return Part.makeCylinder(d / 2, x1 - x0, V(x0, y, z), V(1, 0, 0))


def hex_z(x, y, across_corners, z0, z1):
    r = across_corners / 2
    pts = [V(x + r * math.cos(math.radians(60 * i + 30)), y + r * math.sin(math.radians(60 * i + 30)), min(z0, z1))
           for i in range(7)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, abs(z1 - z0)))


def hex_y(x, z, across_corners, y0, y1):
    r = across_corners / 2
    pts = [V(x + r * math.cos(math.radians(60 * i)), min(y0, y1), z + r * math.sin(math.radians(60 * i))) for i in range(7)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, abs(y1 - y0), 0))


def csk_z(x, y, z_top, d=M3, d_head=6.6):
    """Countersunk M3 from the top face down."""
    return cyl_z(x, y, d, z_top - 40, z_top + 1).fuse(
        Part.makeCone(d / 2, d_head / 2, (d_head - d) / 2, V(x, y, z_top - (d_head - d) / 2), V(0, 0, 1))).fuse(
        cyl_z(x, y, d_head, z_top, z_top + 5))


def union(shapes):
    s = shapes[0].multiFuse(shapes[1:]) if len(shapes) > 1 else shapes[0]
    return s.removeSplitter()


def minus(shape, tools):
    return shape.cut(Part.makeCompound(tools)).removeSplitter()


# ------------------------------------------------------------------ rounded edges
# Owner, 2026-11-05: round the parts like Bondtech's. Each body is rounded before its holes, slots and pockets are cut,
# so those keep their exact sizes. Vertical corners first (R_CORNER), then the other edges (R_EDGE); the face that goes
# on the print bed gets a BED_CHAMFER 45 deg chamfer instead, so nothing overhangs at the first layer.
R_CORNER, R_EDGE, BED_CHAMFER = 5.0, 2.5, 1.0


def _usable(f):
    """A valid single solid that booleans still work on (a bad round can pass isValid and then cut to nothing)."""
    if not f.isValid() or len(f.Solids) != 1 or f.Volume <= 0:
        return False
    bb = f.BoundBox
    probes = Part.makeCompound([Part.makeCylinder(0.6, bb.ZLength + 2.0, V(bb.XMin + bb.XLength * (i + 0.5) / 3,
                                                                          bb.YMin + bb.YLength * (j + 0.5) / 3,
                                                                          bb.ZMin - 1.0))
                                for i in range(3) for j in range(3)])
    try:
        cut, common = f.cut(probes), f.common(probes)
        return len(cut.Solids) >= 1 and abs(cut.Volume + common.Volume - f.Volume) < 1e-4 * f.Volume
    except Exception:
        return False


def _fillet(s, r, edges, chamfer=False):
    try:
        f = s.makeChamfer(r, edges) if chamfer else s.makeFillet(r, edges)
    except Exception:
        return None
    return f if _usable(f) else None


def _greedy(s, r, cand, chamfer=False):
    """Round (or chamfer) as many of cand as will take r: all at once if they can, otherwise one by one."""
    if not cand:
        return s, 0, 0
    f = _fillet(s, r, cand, chamfer)
    if f is not None:
        return f, len(cand), 0
    good = []
    for e in cand:
        if _fillet(s, r, good + [e], chamfer) is not None:
            good.append(e)
    if not good:
        return s, 0, len(cand)
    return _fillet(s, r, good, chamfer), len(good), len(cand) - len(good)


STATS = {}
FALLBACK = {}       # part name -> 1: no vertical-corner pass, 2: not rounded (set by build_all when a part's cuts fail)


def _concave(s, e):
    """True for an inside corner (a fillet there adds material), or when it can't tell."""
    try:
        faces = s.ancestorsOfType(e, Part.Face)
    except Exception:
        return True
    if len(faces) != 2:
        return True
    u = (e.FirstParameter + e.LastParameter) / 2
    p, t = e.valueAt(u), e.tangentAt(u)
    pts = []
    for f in faces:
        try:
            n = f.normalAt(*f.Surface.parameter(p))
        except Exception:
            return True
        d = n.cross(t)
        if d.Length < 1e-9:
            return True
        d.normalize()
        for sgn in (1.0, -1.0):
            q = p + d * (0.4 * sgn)
            if f.isInside(q, 0.05, True):
                pts.append(q)
                break
        else:
            return True
    return not s.isInside((pts[0] + pts[1]) * 0.5, 1e-4, False)


def soften(s, name=None, r_v=R_CORNER, r_h=R_EDGE, planes=(), boxes=(), hold=()):
    """Round a body made of boxes before its holes are cut: vertical corners with r_v, then the other straight edges
    and the arcs that pass made with r_h. Edges stay square where they lie in one of `planes` ((axis 0/1/2, value):
    a face against an extrusion, rail, block or motor). Inside corners stay square where they reach into
    one of `boxes` (a mating part's space, grown by r_v + 0.5): a fillet there would add material into it; outside
    corners can only lose material, so they are rounded anyway. Every edge stays square in a `hold` box. The body's
    own bosses and posts (cylinders up to 8 mm radius) keep their edges and the edges near them. With `name`, the part's print-bed face (vc12_print.ORIENT)
    gets a BED_CHAMFER chamfer instead of rounds."""
    level = FALLBACK.get(name, 0)
    if level >= 2:
        STATS[name] = {"rounded": 0, "chamfered": 0, "left_square": "all (its cuts failed on the rounded body)"}
        return s
    planes = list(planes)
    bed = None
    if name is not None:
        from vc12_print import ORIENT
        d = ORIENT[name][0]
        i = "XYZ".index(d[1])
        bb = s.BoundBox
        bed = (i, (bb.XMax, bb.YMax, bb.ZMax)[i] if d[0] == "+" else (bb.XMin, bb.YMin, bb.ZMin)[i])
    g = r_v + 0.5
    grow = lambda b: App.BoundBox(b.XMin - g, b.YMin - g, b.ZMin - g, b.XMax + g, b.YMax + g, b.ZMax + g)  # noqa: E731
    near, held = [grow(b) for b in boxes], [grow(b) for b in hold]
    # the body's own bosses and posts: a round running into one breaks the later cuts, so edges near them stay square
    held += [grow(f.BoundBox) for f in s.Faces if f.Surface.__class__.__name__ == "Cylinder" and f.Surface.Radius <= 8.0]

    def in_plane(e, pl):
        a, b = e.Vertexes[0].Point, e.Vertexes[-1].Point
        bb = e.BoundBox
        lo, hi = (bb.XMin, bb.YMin, bb.ZMin), (bb.XMax, bb.YMax, bb.ZMax)
        return any(abs(a[i] - v) < 1e-6 and abs(b[i] - v) < 1e-6 and hi[i] - lo[i] < 1e-6 for i, v in pl)

    def kept(sh, e, with_bed=True):
        if in_plane(e, planes + ([bed] if bed and with_bed else [])):
            return True
        if any(e.BoundBox.intersect(k) for k in held):
            return True
        return any(e.BoundBox.intersect(k) for k in near) and _concave(sh, e)

    def line(e):                                         # a straight edge between two flat faces (no seams)
        if e.Curve.TypeId != "Part::GeomLine":
            return False
        try:
            fs = current[0].ancestorsOfType(e, Part.Face)
        except Exception:
            return False
        return len(fs) == 2 and all(f.Surface.__class__.__name__ == "Plane" for f in fs)

    def vertical(e):
        d = e.Vertexes[-1].Point - e.Vertexes[0].Point
        return line(e) and abs(d.x) < 1e-6 and abs(d.y) < 1e-6

    def key(e):
        c = e.Curve
        return (round(c.Center.x, 3), round(c.Center.y, 3), round(c.Center.z, 3), round(c.Radius, 3))

    def new_arc(e):
        return (e.Curve.TypeId == "Part::GeomCircle" and abs(abs(e.Curve.Axis.z) - 1.0) < 1e-6
                and key(e) not in own)

    own = {key(e) for e in s.Edges if e.Curve.TypeId == "Part::GeomCircle"}
    current = [s]
    s1, n1, k1 = (s, 0, 0) if level >= 1 else _greedy(s, r_v, [e for e in s.Edges if vertical(e) and not kept(s, e)])
    current[0] = s1
    s2, n2, k2 = _greedy(s1, r_h, [e for e in s1.Edges if ((line(e) and not vertical(e)) or new_arc(e))
                                   and not kept(s1, e)])
    current[0] = s2
    n3 = k3 = 0
    if bed:
        on_bed = [e for e in s2.Edges if in_plane(e, [bed]) and not kept(s2, e, with_bed=False)
                  and (line(e) or (e.Curve.TypeId == "Part::GeomCircle" and key(e) not in own))]
        s2, n3, k3 = _greedy(s2, BED_CHAMFER, on_bed, chamfer=True)
    if name is not None:
        STATS[name] = {"rounded": n1 + n2, "chamfered": n3, "left_square": k1 + k2 + k3,
                       "volume_change_mm3": round(s2.Volume - s.Volume, 1)}
    return s2


def bbox(x0, x1, y0, y1, z0, z1):
    """A mating part's space, for soften(boxes=...)."""
    return App.BoundBox(min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1))


def idler_box(x, y, z, idler):
    r = idler.get("od_flange", idler.get("od")) / 2
    h = idler["length"] / 2
    return bbox(x - r, x + r, y - r, y + r, z - h, z + h)


def lower_upper(side):
    """(front-going plane, rear-going plane) at this joint: left A/B, right B/A."""
    return (P.PLANE_A, P.PLANE_B) if side < 0 else (P.PLANE_B, P.PLANE_A)


# ------------------------------------------------------------------ XY joints
def joint(side):
    s = side
    X = lambda a: s * a  # noqa: E731  (|x| to world x)
    zF, zR = lower_upper(side)
    jf = (X(P.J_F_X), P.J_F_DY)
    jr = (X(P.J_R_X), P.J_R_DY)
    tooth_half, smooth_half = P.TOOTHED_IDLER["length"] / 2, P.SMOOTH_IDLER["length"] / 2
    top0, top1 = P.Y_BLOCK_Z[1], P.Y_BLOCK_Z[1] + 7.0
    deck0, deck1 = 689.5, 695.0
    body = [
        box(X(337.0), X(398.5), P.JOINT_Y[0], P.JOINT_Y[1], top0, top1),          # top plate on the Y block
        box(X(339.0), X(365.0), -12.5, 12.5, deck0, top0),                         # beam column
        box(X(337.0), X(365.0), P.JOINT_Y[0], 31.0, deck0, deck1),                 # lower deck
    ]
    # idler bosses: under each idler down to the deck, over each idler up to the top plate
    for (x, y), z, half in ((jf, zF, tooth_half), (jr, zR, smooth_half)):
        lo, hi = z - half - 0.5, z + half + 0.5
        if lo > deck1:
            body.append(cyl_z(x, y, 11.0, deck1, lo))
        body.append(cyl_z(x, y, 11.0, hi, top0))
    j = union(body)
    # square: the top plate over the Y block, and the column round the beam end
    j = soften(j, f"joint_{'L' if side < 0 else 'R'}",
               boxes=[idler_box(*jf, zF, P.TOOTHED_IDLER), idler_box(*jr, zR, P.SMOOTH_IDLER)],
               hold=[bbox(X(P.Y_RAIL_X) - 13.5, X(P.Y_RAIL_X) + 13.5, -17.25, 17.25, *P.Y_BLOCK_Z),
                     bbox(X(338.9), X(362.7), -P.BEAM_HALF_W, P.BEAM_HALF_W, *P.BEAM_Z)])
    tools = [
        box(X(338.9), X(362.7), -P.BEAM_HALF_W - 0.15, P.BEAM_HALF_W + 0.15, P.BEAM_Z[0] - 0.1, P.BEAM_Z[1] + 0.15),
        box(X(330.0), X(339.0), -15, 15, deck0 - 1, top0),                         # keep the inner face clean
    ]
    for (x, y) in (jf, jr):                                                         # M5 axles, head on top, nut below
        tools += [cyl_z(x, y, M5, deck0 - 1, top1 + 1), cyl_z(x, y, M5_CB, top1 - 5.0, top1 + 1),
                  hex_z(x, y, M5_NUT, deck0 - 1, deck0 + 5.0)]
    for dx, dy in P.Y_BLOCK_HOLES:                                                 # MGN12C on the Y rail
        x = X(P.Y_RAIL_X) + dx
        tools += [cyl_z(x, dy, M3, top0 - 1, top1 + 1), cyl_z(x, dy, M3_CB, top1 - 3.5, top1 + 1)]
    for ax in P.BEAM_TNUT_X:                                                       # M5 into the beam's T-nuts
        tools += [cyl_z(X(ax), 0, M5, deck0 - 1, P.BEAM_Z[0]), cyl_z(X(ax), 0, M5_CB, deck0 - 1, deck0 + 5.0)]
    return minus(j, tools)


# ------------------------------------------------------------------ carriage
def carriage():
    """One printed carriage on the X rail's MGN12C; INDX X-carriage bolts to its front."""
    grid_z = P.TIP_Z + P.INDX_GRID_DZ                    # 728
    top0, top1 = P.X_BLOCK_Z[1], P.X_BLOCK_Z[1] + 6.0      # 734.1 .. 740.1
    face = P.INDX_FACE_DY                                 # -18
    lip_top = P.TIP_Z + P.INDX_GRID_DZ + 13.5             # 741.5, like an MGN12H block's edge
    leg_bot = 692.5
    body = [
        box(-46, 46, -22, 24, top0, top1),                                  # top plate
        box(-26.0, 26.0, face, -10.6, 704.0, 723.5),                        # INDX mount wall, below the block,
        box(-26.0, 26.0, face, -14.0, 723.5, top0),                         # beside the block (meets the front legs)
        box(-25.5, 25.5, face, -14.0, top1, lip_top),                       # lip up to the INDX grid's top row
    ]
    for e in (-1, 1):
        body += [box(e * 26, e * 46, -22, -10.5, leg_bot, top0),            # front leg
                 box(e * 26, e * 46, 10.5, 24, leg_bot, top0)]              # rear leg
    c = union(body)
    # square: the INDX X-carriage face, and the inside corners round the MGN12 block under the top plate
    c = soften(c, "carriage", planes=[(1, face)],
               boxes=[bbox(-17.35, 17.35, -P.X_BLOCK_HALF_W, P.X_BLOCK_HALF_W, *P.X_BLOCK_Z)])
    env = c
    tools = []
    for dx, dy in P.X_BLOCK_HOLES:                                          # countersunk: the PCB cover is above
        tools.append(csk_z(dx, dy, top1))
    for x in CHAIN_HEAD_SCREWS:                                             # chain head bracket: M3 inserts over the
        tools.append(cyl_z(x, 16.5, M3_INSERT, top1 - 5.0, top1 + 1.0))     # rear-right leg
    for gx in (-10, 10):                                                    # INDX 20 x 20 grid, M3 inserts
        for gz in (grid_z - 10, grid_z + 10):
            tools.append(cyl_y(gx, gz, M3_INSERT, face - 1, face + 6.0))
    for hx in (-19, 19):                                                    # head-screw heads behind the plate
        tools.append(cyl_y(hx, P.TIP_Z + 23.5, 7.0, face - 1, face + 1.0))
    for px in (-11.5, 11.5):                                                # dowel holes behind the plate
        tools.append(cyl_y(px, P.TIP_Z + 31.0, 5.0, face - 1, face + 3.0))
    caps = []
    # belt clamps: (side, lane, plane). Left front A, left rear B, right front B, right rear A.
    for e, lane, plane in ((-1, "F", P.PLANE_A), (-1, "R", P.PLANE_B), (1, "F", P.PLANE_B), (1, "R", P.PLANE_A)):
        lower = plane == P.PLANE_A
        x_out, x_in = e * 46.0, e * 26.0
        if lane == "F":
            slot = (-17.2, -15.45)
            cap_y = (-15.45, -10.5)
            ridge_y = (-17.2, -16.5)
            screw_from, screw_to, nut_y = -22.0, -10.5, (-13.0, -10.4)
        else:
            slot = (14.8, 16.55)
            cap_y = (16.55, 24.0)
            ridge_y = (14.8, 15.5)
            screw_from, screw_to, nut_y = 24.0, 10.5, (10.4, 13.0)
        win_z = (plane - 8.0, plane + 12.5) if lower else (plane - 11.5, plane + 8.0)
        screw_z = plane + 8.5 if lower else plane - 8.5
        tools.append(box(x_in, x_out + e * 0.1, slot[0], slot[1], plane - 6.5, plane + 6.5))   # belt channel
        tools.append(box(x_in + e * 0.01, x_out + e * 0.1, cap_y[0], cap_y[1], win_z[0], win_z[1]))  # cap window
        for sx in (e * 30.0, e * 42.0):
            tools.append(cyl_y(sx, screw_z, M3, screw_from - 1, screw_to + 1))
        cap = box(x_in + e * 0.2, x_out, cap_y[0], cap_y[1], win_z[0] + 0.2, win_z[1] - 0.2)
        cap = cap.common(env).removeSplitter()                             # follows the leg's rounded edges
        cap_tools = [cyl_y(sx, screw_z, M3, cap_y[0] - 1, cap_y[1] + 1) for sx in (e * 30.0, e * 42.0)]
        if lane == "F":                       # nuts in the cap's beam-side face
            cap_tools += [hex_y(sx, screw_z, M3_NUT, nut_y[0], nut_y[1]) for sx in (e * 30.0, e * 42.0)]
        else:                                 # nuts in the leg's beam-side face
            tools += [hex_y(sx, screw_z, M3_NUT, nut_y[0], nut_y[1]) for sx in (e * 30.0, e * 42.0)]
        caps.append(minus(cap, cap_tools))
        # rack: ridges that sit between the belt's teeth (2 mm pitch, teeth face the front)
        rack = []
        n = 0
        while True:
            rx = x_in + e * (1.5 + 2.0 * n)
            if abs(rx) > abs(x_out) - 1.0:
                break
            rack.append(box(rx - 0.5, rx + 0.5, ridge_y[0], ridge_y[1], plane - 6.5, plane + 6.5))
            n += 1
        tools_after = rack
        c = minus(c, tools)
        c = union([c] + tools_after)
        tools = []
    return c, caps


# ------------------------------------------------------------------ front idler blocks
def front_idler(side):
    s = side
    X = lambda a: s * a  # noqa: E731
    z = P.PLANE_A if side < 0 else P.PLANE_B
    half = P.SMOOTH_IDLER["length"] / 2
    y0 = P.FRONT_IDLER_Y
    ax = X(P.CORNER_X)
    lo_top = z - half - 0.5
    hi_bot = z + half + 0.5
    deck_t = 8.0
    front = (y0 - P.FRONT_IDLER_SLOT - 9.5 - 4.8, y0 - P.FRONT_IDLER_SLOT - 9.5 - 1.8)   # 1.8 mm ahead of the flange
    rear = -313.0
    ext_top = P.SIDE_Z[1]
    body = [box(X(346.0), X(369.0), front[0], rear, lo_top - deck_t, lo_top),       # lower deck
            box(X(346.0), X(369.0), front[0], rear, hi_bot, hi_bot + deck_t),       # upper deck
            box(X(346.0), X(369.0), front[0], front[1], lo_top - deck_t, hi_bot + deck_t)]  # front wall
    if hi_bot + deck_t < ext_top:            # left: riser up to the 3030 top, then an arm onto it
        body += [box(X(362.0), X(369.5), front[0], rear, hi_bot + deck_t, ext_top + 6.0),
                 box(X(362.0), X(399.5), P.FRONT_VERT_Y[1] + 0.1, rear, ext_top, ext_top + 6.0)]
        arm_top = ext_top + 6.0
    else:                                    # right: the upper deck already clears the 3030 top
        body += [box(X(369.0), X(399.5), P.FRONT_VERT_Y[1] + 0.1, rear, ext_top, hi_bot + deck_t)]
        arm_top = hi_bot + deck_t
    # front hard stop for the joint's top plate (sensorless homing)
    stop_face = P.YG_FRONT_STOP + P.JOINT_Y[0]
    rail_front = P.Y_RAIL_Y[0] - 0.5
    body.append(box(X(372.0), X(397.0), rear - 1.0, rail_front, arm_top - 0.1, P.Y_BLOCK_Z[1] + 10.0))
    body.append(box(X(372.0), X(397.0), rail_front - 0.1, stop_face, P.Y_RAIL_Z[1] + 0.6, P.Y_BLOCK_Z[1] + 10.0))
    f = union(body)
    # square: the arm on the side 3030's top, and its face against the front upright
    idl = idler_box(ax, y0, z, P.SMOOTH_IDLER)
    f = soften(f, f"front_idler_{'L' if side < 0 else 'R'}",
               planes=[(2, ext_top), (1, P.FRONT_VERT_Y[1] + 0.1)],
               boxes=[bbox(idl.XMin, idl.XMax, idl.YMin - P.FRONT_IDLER_SLOT, idl.YMax + P.FRONT_IDLER_SLOT,
                           idl.ZMin, idl.ZMax),
                      bbox(X(P.Y_RAIL_X) - 6.0, X(P.Y_RAIL_X) + 6.0, P.Y_RAIL_Y[0], P.Y_RAIL_Y[1], *P.Y_RAIL_Z),
                      bbox(X(369.6), X(399.6), -400.0, 400.0, *P.SIDE_Z)])
    tools = []
    # axle slot in both decks, push screws from the rear into the axle
    for zz in ((lo_top - deck_t - 1, lo_top + 1), (hi_bot - 1, hi_bot + deck_t + 1)):
        tools.append(cyl_z(ax, y0 - P.FRONT_IDLER_SLOT, M5, *zz).fuse(cyl_z(ax, y0 + P.FRONT_IDLER_SLOT, M5, *zz)).fuse(
            box(ax - M5 / 2, ax + M5 / 2, y0 - P.FRONT_IDLER_SLOT, y0 + P.FRONT_IDLER_SLOT, *zz)))
    for zc in (lo_top - deck_t / 2, hi_bot + deck_t / 2):
        tools += [cyl_y(ax, zc, M3_INSERT, rear - 6.0, rear + 1), cyl_y(ax, zc, M3, y0, rear)]
    # M6 down into the side 3030's top slot
    for yy in (-332.0, -320.0):
        tools.append(cyl_z(X(P.Y_RAIL_X), yy, M6, ext_top - 1, arm_top + 30))
        tools.append(cyl_z(X(P.Y_RAIL_X), yy, M6_CB, arm_top - 0.01 if arm_top > ext_top + 6 else ext_top + 6.0 - 0.01, arm_top + 30))
    return minus(f, tools)


# ------------------------------------------------------------------ rear corners
NEMA_HOLES = [(-15.5, -15.5), (-15.5, 15.5), (15.5, -15.5), (15.5, 15.5)]


def rear_corner(side):
    """Left (side -1): motor A below, drives the lower belt. Right (+1): motor B above, upper belt."""
    s = side
    X = lambda a: s * a  # noqa: E731
    mx, my = X(P.MOTOR_X), P.MOTOR_Y
    r1 = (X(P.CORNER_X), P.R1_Y)
    r2 = (X(P.CORNER_X), P.CORNER_Y)
    zA, zB = P.PLANE_A, P.PLANE_B
    half = P.SMOOTH_IDLER["length"] / 2
    ybot, yrear = 296.5, 367.0
    xin, xout = 311.0, 399.5
    ext_bot, ext_top = P.SIDE_Z
    parts = {}
    if side < 0:
        base0, base1 = 684.0, 695.0                  # motor face on the underside
        top0, top1 = zB + half + 0.5, zB + half + 7.5
        bridge = (712.5, 720.5)
        bearing_z = (713.5, 718.6)
        posts = [(X(316.0), 309.0), (X(316.0), 328.0)]
    else:
        base0, base1 = 688.0, 695.0
        top0, top1 = zB + half + 0.5, zB + half + 10.5  # motor on top
        bridge = (706.5, 715.0)
        bearing_z = (709.9, 715.1)
        posts = [(X(316.0), 307.0), (X(316.0), 325.0)]
    # base (under the 3030s), bosses up into their bottom slots, posts and the shaft bearing bridge
    base = [box(X(xin), X(xout), ybot, yrear, base0, base1)]
    bolt_pts_bottom = [(X(385.0), 305.0), (X(385.0), 326.0), (X(355.0), 352.5), (X(325.0), 352.5)]
    for x, y in bolt_pts_bottom:
        base.append(cyl_z(x, y, 14.0, base1, ext_bot))
    for x, y in posts:
        base.append(cyl_z(x, y, 10.0, base1, bridge[1]))
    base.append(box(X(311.0), X(345.0), 304.0, 331.0, bridge[0], bridge[1]))
    # idler pedestals so each idler sits at its plane
    if side < 0:
        pass                                          # R1 and R2 are on the lower plane: sit on the base
    else:
        base.append(cyl_z(*r1, 11.0, base1, zB - half - 0.5))   # R1_R is on the upper plane
    b = union(base)
    tag = "L" if side < 0 else "R"
    idlers = [idler_box(*r1, zA if side < 0 else zB, P.SMOOTH_IDLER), idler_box(*r2, zA, P.SMOOTH_IDLER),
              idler_box(*r2, zB, P.SMOOTH_IDLER), bbox(mx - 8, mx + 8, my - 8, my + 8, zA - 10, zB + 10)]  # + pulley
    motor = bbox(mx - 21, mx + 21, my - 21, my + 21, base0 - 48, base0) if side < 0 else \
        bbox(mx - 21, mx + 21, my - 21, my + 21, top1, top1 + 48)
    frame = [bbox(X(369.6), X(399.6), 296.0, 368.0, *P.SIDE_Z), bbox(X(300.0), X(399.6), 337.5, 367.5, *P.SIDE_Z)]
    b = soften(b, f"rear_corner_{tag}_base", boxes=idlers + [motor] + frame,
               hold=[bbox(x - 5.0, x + 5.0, y - 5.0, y + 5.0, base1, bridge[1]) for x, y in posts])  # bridge on its posts
    tools = []
    for x, y in bolt_pts_bottom:
        tools += [cyl_z(x, y, M6, base0 - 1, ext_bot + 1), cyl_z(x, y, M6_CB, base0 - 1, base0 + 5.0)]
    for (x, y) in (r1, r2):
        tools += [cyl_z(x, y, M5, base0 - 1, base1 + 30), hex_z(x, y, M5_NUT, base0 - 1, base0 + 5.0)]
    if side < 0:
        tools += [cyl_z(mx, my, 16.5, base0 - 1, base1 + 1), cyl_z(mx, my, 22.5, base0 - 1, base0 + 2.5)]
        for dx, dy in NEMA_HOLES:
            tools += [cyl_z(mx + dx, my + dy, M3, base0 - 1, base1 + 1), cyl_z(mx + dx, my + dy, M3_CB, base1 - 3.5, base1 + 1)]
        tools += [cyl_z(mx, my, 16.1, bridge[0] - 1, bearing_z[1]), cyl_z(mx, my, 7.0, bridge[0] - 1, bridge[1] + 1)]
    else:
        tools += [cyl_z(mx, my, 16.1, bearing_z[0], bridge[1] + 1), cyl_z(mx, my, 7.0, bridge[0] - 1, bridge[1] + 1)]
    post = box(X(369.6), X(401.0), P.REAR_POST_Y[0] - 0.4, 400.0, 600.0, 800.0)   # the corner upright
    tools.append(post)
    parts["base"] = minus(b, tools)
    # top plate on the 3030 tops, feet down to them, rear hard stop for the joint's top plate
    top = [box(X(xin if side > 0 else 340.0), X(xout), ybot, yrear, top0, top1)]
    bolt_pts_top = [(X(385.0), 305.0), (X(385.0), 330.0), (X(355.0), 352.5)]
    for x, y in bolt_pts_top:
        top.append(cyl_z(x, y, 14.0, ext_top, top0 + 0.1))
    stop_face = P.YG_REAR_STOP + P.JOINT_Y[1]
    top.append(box(X(372.0), X(397.0), stop_face, stop_face + 8.0, top1 - 0.1, P.Y_BLOCK_Z[1] + 10.0))
    if side < 0:
        top.append(cyl_z(*r1, 11.0, zA + half + 0.5, top0 + 0.1))   # spacer over R1_L down to its idler
    t = union(top)
    # square: the right one's motor face on top, the joint's stop face
    t = soften(t, f"rear_corner_{tag}_top", planes=([(2, top1)] if side > 0 else []) + [(1, stop_face)],
               boxes=idlers + [motor] + frame)
    tools = []
    for x, y in bolt_pts_top:
        tools += [cyl_z(x, y, M6, ext_top - 1, top1 + 1), cyl_z(x, y, M6_CB, top1 - 5.0, top1 + 1)]
    for (x, y) in (r1, r2):
        tools += [cyl_z(x, y, M5, zA, top1 + 1), cyl_z(x, y, M5_CB, top1 - 5.0, top1 + 1)]
    if side > 0:
        tools += [cyl_z(mx, my, 16.5, top0 - 1, top1 + 1), cyl_z(mx, my, 22.5, top1 - 2.5, top1 + 1)]
        for dx, dy in NEMA_HOLES:
            tools += [cyl_z(mx + dx, my + dy, M3, top0 - 1, top1 + 1), cyl_z(mx + dx, my + dy, M3_CB, top0 - 1, top0 + 3.5)]
    tools.append(post)
    parts["top"] = minus(t, tools)
    return parts


# ------------------------------------------------------------------ dock bar brackets
def dock_bracket(side, yb=None, zb=None, name=None):
    s = side
    X = lambda a: s * a  # noqa: E731
    yb = P.DOCK_BAR_Y if yb is None else yb
    zb = P.DOCK_BAR_Z if zb is None else zb
    half = 7.5
    plate = box(X(361.0), X(369.8), P.FRONT_VERT_Y[0] + 2.0, yb + half + 1.3, zb - 25.0, zb + 25.0)   # on the upright's inner face
    shelf = box(X(339.0), X(361.0), yb - half - 4.0, yb + half - 0.2, zb - half - 5.0, zb - half)  # under the bar end
    cheek = box(X(339.0), X(361.0), yb - half - 4.0, yb - half, zb - half - 5.0, zb + half)   # ahead of the bar end:
    # the docks cover the bar's front face only where they hang, and the front idler block sits behind
    b = union([plate, shelf, cheek])
    # square: the plate's face on the upright; every edge round the bar end
    b = soften(b, name or f"dock_bracket_{'L' if side < 0 else 'R'}", planes=[(0, X(369.8))],
               hold=[bbox(X(338.0), X(369.9), yb - half, yb + half, zb - half, zb + half)])
    tools = [box(X(338.0), X(369.9), yb - half - 0.15, yb + half + 0.15, zb - half - 0.15, zb + half + 0.15)]
    # vertical slots into the upright's inner T-slot (Y -352.5): +/-5 mm height adjustment, per Bondtech
    for dz in (-17.0, 17.0):
        for k in (-5.0, 0.0, 5.0):
            tools.append(cyl_x(-352.5, zb + dz + k, M6, X(360.0), X(370.5)))
    tools.append(cyl_z(X(350.0), yb, M3, zb - half - 6, zb - half + 0.1))      # M3 into the bar's T-nut
    return minus(b, tools)


# ------------------------------------------------------------------ purge and wipe stations (one per tool)
FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FLOOR_Z = (P.STATION_RAIL_Z + 7.5, P.STATION_RAIL_Z + 12.5)          # cradle floor on the rail top
CROSSBAR_Y = (P.PAD_REAR_Y - P.PAD[1] - 7.5, P.PAD_REAR_Y - P.PAD[1])  # just ahead of the pad
CROSSBAR_Z = (678.0, P.WIPER_TOP - P.PAD[2] + 2.5)                   # top holds the pad's lower 2.5 mm
POCKET_Z = (P.WIPER_TOP - P.PAD[2] - 3.0, P.WIPER_TOP - P.PAD[2])


def yz_prism(pts, x0, x1):
    """Polygon in the YZ plane, extruded along X."""
    w = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def engrave_front(text, x_mid, y_face, z_mid, height, depth=0.6):
    """Text cutter for a face looking toward -Y (readable from the door)."""
    chars = Part.makeWireString(text, FONT, height, 0.0)
    faces = [Part.makeFace(ws, "Part::FaceMakerBullseye") for ws in chars if ws]
    t = Part.makeCompound(faces)
    bb = t.BoundBox
    t.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, 0))
    t.rotate(V(0, 0, 0), V(1, 0, 0), 90)                    # text Y -> printer Z, face normal -> -Y
    t.translate(V(x_mid, y_face - 0.01, z_mid))
    return Part.makeCompound([f.extrude(V(0, depth + 0.01, 0)) for f in t.Faces])


def station_cradle(i):
    """Sits on the station rail (2 x M3 into T-nuts); the bucket slides on its floor between its walls, and a
    crossbar carries the Qidi wiper pad. Below Z 646 nothing reaches behind Y -323.5 (front bed arms)."""
    x0 = P.STATION_X0[i]
    x1 = x0 + P.STATION_W
    w = P.CRADLE_WALL
    y0, y1 = P.BUCKET_FRONT_Y, P.BUCKET_LOW_REAR_Y
    pad = P.PAD_X[i]
    body = [box(x0, x1, y0, y1, *FLOOR_Z),                                                  # floor
            box(x0, x0 + w, y0, y1, FLOOR_Z[1], CROSSBAR_Z[1]),                             # walls
            box(x1 - w, x1, y0, y1, FLOOR_Z[1], CROSSBAR_Z[1]),
            box(x0 + w - 0.1, x1 - w + 0.1, *CROSSBAR_Y, *CROSSBAR_Z),                      # crossbar
            box(pad - 0.2, x1 - w + 0.1, CROSSBAR_Y[1] - 0.1, P.PAD_REAR_Y, *POCKET_Z),     # pad shelf
            box(pad + P.PAD[0] + 0.2, x1 - w + 0.1, CROSSBAR_Y[1] - 0.1, P.PAD_REAR_Y, POCKET_Z[1], CROSSBAR_Z[1]),
            yz_prism([(P.DETENT_Y - 1.5, FLOOR_Z[1] - 0.1), (P.DETENT_Y + 1.5, FLOOR_Z[1] - 0.1),     # detent ridge
                      (P.DETENT_Y + 0.7, FLOOR_Z[1] + 0.8), (P.DETENT_Y - 0.7, FLOOR_Z[1] + 0.8)], x0 + w, x1 - w)]
    c = union(body)
    # square: the floor's top and the walls' inner faces (the bucket slides on them), the pad pocket, the detent
    c = soften(c, f"station_cradle_T{i}", planes=[(2, FLOOR_Z[1]), (0, x0 + w), (0, x1 - w)],
               boxes=[bbox(x0 + w, x1 - w, y0, y1, FLOOR_Z[1], P.BUCKET_RIM_Z)],
               hold=[bbox(pad, pad + P.PAD[0], P.PAD_REAR_Y - P.PAD[1], P.PAD_REAR_Y, P.WIPER_TOP - P.PAD[2], P.WIPER_TOP),
                     bbox(x0 + w, x1 - w, P.DETENT_Y - 1.5, P.DETENT_Y + 1.5, FLOOR_Z[1], FLOOR_Z[1] + 0.8)])
    tools = [csk_z(bx, P.STATION_RAIL_Y, FLOOR_Z[1]) for bx in (x0 + 18.0, x1 - 18.0)]   # into the rail's T-nuts
    tools.append(engrave_front(f"T{i}", (x0 + pad) / 2 + 2, CROSSBAR_Y[0], sum(CROSSBAR_Z) / 2, 5.5))
    return minus(c, tools)


def purge_bucket(i):
    """Open-top bucket. Door open, pull the front flange: it rides over the detent and slides out, no fasteners.
    The back slopes, so purge and drips landing at the rear slide in; the low back keeps clear of the bed arms."""
    x0 = P.STATION_X0[i] + P.CRADLE_WALL + P.BUCKET_GAP
    x1 = P.STATION_X0[i] + P.STATION_W - P.CRADLE_WALL - P.BUCKET_GAP
    t = P.BUCKET_WALL
    z0, z1 = FLOOR_Z[1] + 0.3, P.BUCKET_RIM_Z
    yf, yr, ylo, zs = P.BUCKET_FRONT_Y, P.BUCKET_REAR_Y, P.BUCKET_LOW_REAR_Y, P.BUCKET_SLOPE_Z
    outer = yz_prism([(yf, z0), (ylo, z0), (ylo, zs), (yr, z1), (yf, z1)], x0, x1)
    d = (yr - ylo, z1 - zs)
    L = math.hypot(*d)
    n = (-d[1] / L, d[0] / L)                                   # inward normal of the sloped back
    a = (ylo + t * n[0], zs + t * n[1])                         # inner slope passes through a, direction d
    k = (yr - ylo) / (z1 - zs)
    y_at = lambda z: a[0] + (z - a[1]) * k  # noqa: E731
    yi = ylo - t
    zc = a[1] + (yi - a[0]) / k                                 # inner back corner
    inner = yz_prism([(yf + t, z0 + t), (yi, z0 + t), (yi, zc), (y_at(z1 + 5), z1 + 5), (yf + t, z1 + 5)],
                     x0 + t, x1 - t)
    # outside and inside rounded to match, so the walls keep their thickness; the low back's inside corner stays
    # square (a fillet there would reach toward the bed arms)
    outer = soften(outer, f"purge_bucket_T{i}", r_v=4.0, r_h=2.0, planes=[(1, ylo)])
    inner = soften(inner, r_v=4.0 - t, r_h=1.5)
    b = minus(outer, [inner])
    flange = soften(box(P.STATION_X0[i], P.STATION_X0[i] + P.STATION_W, yf - P.BUCKET_FLANGE, yf, z1 - 14.0, z1),
                    r_v=1.2, r_h=1.0)
    b = union([b, flange])
    h = (yr - 0.6) - (y_at(z1) - 1.0)                           # back rim: 45 deg chamfer down into the bucket,
    tools = [yz_prism([(yr - 0.6, z1 + 0.1), (yr - 0.6 - h, z1 + 0.1), (yr - 0.6 - h, z1 + 0.1 - h)],   # 0.6 mm land
                      x0 + t, x1 - t),
             yz_prism([(P.DETENT_Y - 1.8, z0 - 0.1), (P.DETENT_Y + 1.8, z0 - 0.1),              # detent groove underneath
                       (P.DETENT_Y + 0.8, z0 + 1.0), (P.DETENT_Y - 0.8, z0 + 1.0)], x0 - 1, x1 + 1),
             engrave_front(f"T{i}", (x0 + x1) / 2, yf - P.BUCKET_FLANGE, z1 - 7.0, 7.0)]
    return minus(b, tools)


# ------------------------------------------------------------------ PTFE coupler blocks and the cable chain brackets
def rod(points, d):
    """Round bar along a polyline (cylinders and ball joints)."""
    out = []
    for a, b in zip(points[:-1], points[1:]):
        a, b = V(*a), V(*b)
        if (b - a).Length > 1e-6:
            out.append(Part.makeCylinder(d / 2, (b - a).Length, a, b - a))
    out += [Part.makeSphere(d / 2, V(*p)) for p in points[1:-1]]
    return union(out)


def ptfe_coupler_block(i):
    """On the front top 3030's inner T-slot (2 x M6), directly above dock i. The tube comes down from the top hat into
    the channel, bends 60 deg (R 40) and leaves through a PC4-M10 coupler pointing 30 deg down and back. Above the
    frame top its front is cut back to clear the hat's front centre wall by 2 mm."""
    import vc12_tubes as T
    x = P.DOCK_X[i]
    path = T.channel_points(x)
    face = P.TOP_FRONT_IN_Y
    z_slot = sum(P.TOP_FRONT_Z) / 2
    plate = box(x - 19.0, x + 19.0, face, face + 6.0, P.TOP_FRONT_Z[0] + 1.0, P.TOP_FRONT_Z[1] - 1.0)
    housing = box(x - 8.0, x + 8.0, face + 5.9, P.TUBE_IN_Y + 7.0, P.TUBE_BEND[0] - 22.0, path[0][2])
    web = box(min(x, path[-3][0]) - 4.0, max(x, path[-3][0]) + 4.0, face + 5.9, path[-3][1], path[-3][2] - 6.0,
              P.TUBE_BEND[0] - 21.9)
    body = union([plate, housing, web, rod(path[1:], 16.0)])
    # square: the plate's face on the 3030, and its top, which sits 1 mm under the hat's front wall
    body = soften(body, f"ptfe_coupler_block_T{i}", r_v=3.0, r_h=2.0, planes=[(1, face), (2, P.TOP_FRONT_Z[1] - 1.0)])
    axis = V(*T.tube_dir(x))
    end = V(*path[-1])
    tools = [rod(np.vstack([path[0] + np.array([0.0, 0.0, 5.0]), path]), 5.0),       # tube channel
             Part.makeCylinder(9.2 / 2, 11.0, end - axis * 10.0, axis)]               # PC4-M10 bore (self-threading)
    tools.append(box(x - 30.0, x + 30.0, P.HAT_FRONT_IN_Y - 30.0, P.HAT_FRONT_IN_Y + 2.0, P.TOP_FRONT_Z[1],
                     P.TOP_FRONT_Z[1] + 60.0))                                    # 2 mm clear of the hat's front wall
    tools.append(box(x - 30.0, x + 30.0, face + 5.8, P.HAT_FRONT_IN_Y + 2.0, P.TOP_FRONT_Z[1] - 3.0,
                     P.TOP_FRONT_Z[1] + 1.0))                                     # and of its inner edge on the 3030
    for dx in (-13.0, 13.0):                                                         # M6 into the slot's T-nuts
        tools += [cyl_y(x + dx, z_slot, M6, face - 1.0, face + 7.0), cyl_y(x + dx, z_slot, M6_CB, face + 3.0, face + 20.0)]
    return minus(body, tools)


CHAIN_FACE_GAP = 4.0          # room for the igus end bracket between the chain's side and the printed face


def chain_head_bracket():
    """Bolted to the carriage's rear-right corner (2 x M3 into inserts over the rear leg), beside the INDX PCB cover. It
    rises to a face behind the chain's moving end, where the igus end bracket screws on (2 x M3 inserts, 29 mm apart
    up and down). Printed lying on that face: base, upright and face share the plane Y = face0."""
    top1 = P.X_BLOCK_Z[1] + 6.0                              # carriage top plate
    bx, by = P.CHAIN_HEAD_D[0], P.INDX_NOZZLE_DY + P.CHAIN_HEAD_D[1]   # chain end over the head pose xc 0, yg 0
    face0 = by + P.CHAIN["thick"] / 2 + CHAIN_FACE_GAP       # the face the igus bracket screws onto
    z0, z1 = P.CHAIN_Z - P.CHAIN["tall"] / 2 - 2.0, P.CHAIN_Z + P.CHAIN["tall"] / 2 + 3.3
    base = box(27.0, 45.0, face0, 22.0, top1, top1 + 6.0)
    upright = box(33.0, 45.0, face0, 22.0, top1 + 5.9, z1)
    face = box(bx, bx + 28.0, face0, face0 + 7.0, z0, z1)
    b = union([base, upright, face])
    b = soften(b, "chain_head_bracket", r_v=3.0, r_h=1.5, planes=[(2, top1)])
    tools = []
    for x in CHAIN_HEAD_SCREWS:                              # down into the carriage's inserts
        tools += [cyl_z(x, 16.5, M3, top1 - 1.0, top1 + 7.0), cyl_z(x, 16.5, M3_CB, top1 + 3.0, top1 + 7.0)]
    for dz in (-P.CHAIN_BRACKET_HOLES / 2, P.CHAIN_BRACKET_HOLES / 2):
        tools.append(cyl_y(bx + 12.0, P.CHAIN_Z + dz, M3_INSERT, face0 - 1.0, face0 + 6.0))
    return minus(b, tools)


CHAIN_HEAD_SCREWS = (30.5, 41.5)  # X of the 2 x M3 into the carriage top plate, both at Y 16.5 over the rear-right leg


def chain_mount():
    """On the left top 3030's inner face (2 x M6 into its T-slot), mid-depth. A web drops to the chain's height and a face
    behind the chain's fixed end takes the igus end bracket (2 x M3 inserts, 29 mm apart up and down). The cable comes
    along the top 3030, down beside the web and into the chain's open end. Printed lying on its 3030 face."""
    ax, ay = P.CHAIN_MOUNT
    wall = -370.0                                            # left top 3030's inner face
    zt0, zt1 = P.TOP_FRONT_Z
    slot = (zt0 + zt1) / 2
    face0 = ay + P.CHAIN["thick"] / 2 + CHAIN_FACE_GAP
    z0, z1 = P.CHAIN_Z - P.CHAIN["tall"] / 2 - 2.0, P.CHAIN_Z + P.CHAIN["tall"] / 2 + 3.3
    plate = box(wall, wall + 6.0, ay - 25.0, ay + 45.0, zt0 + 2.0, zt1 - 2.0)
    web = box(wall, wall + 8.0, face0, ay + 38.0, z0, zt0 + 2.1)
    face = box(wall + 6.0, ax + 24.5, face0, face0 + 7.0, z0, z1)
    m = union([plate, web, face])
    m = soften(m, "chain_mount", r_v=3.0, r_h=1.5)
    tools = []
    for y in (ay - 15.0, ay + 35.0):                         # M6 into the slot's T-nuts
        tools += [cyl_x(y, slot, M6, wall - 1.0, wall + 7.0), cyl_x(y, slot, M6_CB, wall + 3.0, wall + 7.0)]
    for dz in (-P.CHAIN_BRACKET_HOLES / 2, P.CHAIN_BRACKET_HOLES / 2):
        tools.append(cyl_y(ax + 12.0, P.CHAIN_Z + dz, M3_INSERT, face0 - 1.0, face0 + 6.0))
    return minus(m, tools)


def _rounded_l(x0, x1, y0, y1, cx, cy, r, z0, z1):
    """Plan x0..x1 by y0..y1 (x1, y0 the outer corner), that corner rounded r about (cx, cy)."""
    return union([box(x0, cx, y0, y1, z0, z1), box(x0, x1, cy, y1, z0, z1),
                  Part.makeCylinder(r, z1 - z0, V(cx, cy, z0))]).common(box(x0, x1, y0, y1, z0, z1))


def deck_foot(corner):
    """Under each corner of the spool deck. Its legs stand on the hat's rim right over the frame's corner upright,
    2 mm outside the lid's pocket, its skirt hugs the hat's rounded corner, and two wood screws hold the deck to its
    top plate. It arches over the lid and its handles. Symmetric about its corner's diagonal, so all four are the same
    part, turned; built at the front right corner."""
    ox, oy, r = P.HAT_OUTER
    px, py = P.HAT_POCKET
    gap, wall, depth = P.FOOT_SKIRT
    cx, cy = ox - r, -(oy - r)                                   # centre of the hat corner's rounding
    xi, yi = ox - P.FOOT_SPAN, -(oy - P.FOOT_SPAN)               # inner edges
    zr, zt = P.HAT_RIM_Z, P.DECK_Z
    plate = 6.0
    body = _rounded_l(xi, ox + gap + wall, -(oy + gap + wall), yi, cx, cy, r + gap + wall, zr - depth, zt)
    body = soften(body, "deck_foot_FR", r_v=4.0, r_h=1.5)                 # all four are this part, turned
    hat = _rounded_l(xi - 50.0, ox + gap, -(oy + gap), yi + 50.0, cx, cy, r + gap, zr - depth - 1.0, zr)
    g = P.FOOT_LID_GAP
    hollow = box(xi - 1.0, px + g, -(py + g), yi + 1.0, zr - depth - 1.0, zt - plate)         # over the lid: open
    tools = [hat, hollow]
    for a, b in ((16.0, 28.0), (28.0, 16.0)):                                            # 4 mm wood screws
        tools.append(cyl_z(ox - a, -(oy - b), 4.5, zt - plate - 1.0, zt + 1.0))
    f = minus(body, tools)
    sx, sy = {"FR": (1, -1), "FL": (-1, -1), "RR": (1, 1), "RL": (-1, 1)}[corner]
    if sx < 0:
        f = f.mirror(V(0, 0, 0), V(1, 0, 0))
    if sy > 0:
        f = f.mirror(V(0, 0, 0), V(0, 1, 0))
    return f


def build_all():
    os.makedirs(OUT, exist_ok=True)
    while True:
        out = _build_parts()
        bad = [n for n, shp in out.items() if len(shp.Solids) != 1]
        if not bad:
            break
        for n in bad:
            if FALLBACK.get(n, 0) >= 2:
                raise RuntimeError(f"{n}: {len(out[n].Solids)} solids even unrounded")
            FALLBACK[n] = FALLBACK.get(n, 0) + 1
            print(f"{n}: its cuts failed on the rounded body; rebuilding at fallback level {FALLBACK[n]}", flush=True)
    _write(out)
    return out


def _build_parts():
    out = {}
    for side, tag in ((-1, "L"), (1, "R")):
        out[f"joint_{tag}"] = joint(side)
        out[f"front_idler_{tag}"] = front_idler(side)
        rc = rear_corner(side)
        out[f"rear_corner_{tag}_base"] = rc["base"]
        out[f"rear_corner_{tag}_top"] = rc["top"]
        out[f"dock_bracket_{tag}"] = dock_bracket(side)
        out[f"station_bracket_{tag}"] = dock_bracket(side, P.STATION_RAIL_Y, P.STATION_RAIL_Z, f"station_bracket_{tag}")
    for i in range(P.INDX_TOOLS):
        out[f"station_cradle_T{i}"] = station_cradle(i)
        out[f"purge_bucket_T{i}"] = purge_bucket(i)
        out[f"ptfe_coupler_block_T{i}"] = ptfe_coupler_block(i)
    out["chain_head_bracket"] = chain_head_bracket()
    out["chain_mount"] = chain_mount()
    for c in ("FR", "FL", "RR", "RL"):
        out[f"deck_foot_{c}"] = deck_foot(c)
    car, caps = carriage()
    out["carriage"] = car
    for i, cp in enumerate(caps):
        out[f"carriage_clamp_cap_{i + 1}"] = cp
    return out


def _write(out):
    for name, shp in out.items():
        if not shp.isValid():
            shp.fix(1e-6, 1e-6, 1e-6)
        shp.exportBrep(os.path.join(OUT, name + ".brep"))
        shp.exportStep(os.path.join(OUT, name + ".step"))
        print(f"{name:26s} solids {len(shp.Solids)} valid {shp.isValid()} volume {shp.Volume / 1000:8.2f} cm3 "
              f"mass {shp.Volume * 1.30e-3:6.1f} g (PPS-CF 1.30)  {STATS.get(name, '')}")
    import json
    rep = {n: dict(STATS.get(n, {}), fallback=FALLBACK.get(n, 0), valid=out[n].isValid(), solids=len(out[n].Solids),
                   mass_g=round(out[n].Volume * 1.30e-3, 1)) for n in out}
    json.dump(rep, open(os.path.join(HERE, "..", "checks", "rounding_report.json"), "w"), indent=1)


if __name__ == "__main__":
    build_all()
