"""Build the PPS-CF parts for the V-Core 4.1 500 12 mm CoreXY + INDX conversion.

Run with FreeCAD's own Python (not freecadcmd, whose exec breaks __file__):
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_build.py

Every part is built in the printer frame (see vc12_params) at Yg = 0, xc = 0 and
written to ../parts as <name>.brep (for the checks) and <name>.step.
"""
import math
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402
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
        box(-25.5, 25.5, face, -10.6, 704.0, 723.5),                        # INDX mount wall, below the block
        box(-25.5, 25.5, face, -14.0, 723.5, top0),                         # beside the block
        box(-25.5, 25.5, face, -14.0, top1, lip_top),                       # lip up to the INDX grid's top row
    ]
    for e in (-1, 1):
        body += [box(e * 26, e * 46, -22, -10.5, leg_bot, top0),            # front leg
                 box(e * 26, e * 46, 10.5, 24, leg_bot, top0)]              # rear leg
    c = union(body)
    tools = []
    for dx, dy in P.X_BLOCK_HOLES:                                          # countersunk: the PCB cover is above
        tools.append(csk_z(dx, dy, top1))
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
        cap = box(x_in + e * 0.2, x_out, cap_y[0] + (0.0 if lane == "F" else 0.0), cap_y[1], win_z[0] + 0.2, win_z[1] - 0.2)
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
    tools = []
    for d in (0.0,):
        pass
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
def dock_bracket(side, yb=None, zb=None):
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
    b = minus(outer, [inner])
    flange = box(P.STATION_X0[i], P.STATION_X0[i] + P.STATION_W, yf - P.BUCKET_FLANGE, yf, z1 - 14.0, z1)
    b = union([b, flange])
    h = (yr - 0.6) - (y_at(z1) - 1.0)                           # back rim: 45 deg chamfer down into the bucket,
    tools = [yz_prism([(yr - 0.6, z1 + 0.1), (yr - 0.6 - h, z1 + 0.1), (yr - 0.6 - h, z1 + 0.1 - h)],   # 0.6 mm land
                      x0 + t, x1 - t),
             yz_prism([(P.DETENT_Y - 1.8, z0 - 0.1), (P.DETENT_Y + 1.8, z0 - 0.1),              # detent groove underneath
                       (P.DETENT_Y + 0.8, z0 + 1.0), (P.DETENT_Y - 0.8, z0 + 1.0)], x0 - 1, x1 + 1),
             engrave_front(f"T{i}", (x0 + x1) / 2, yf - P.BUCKET_FLANGE, z1 - 7.0, 7.0)]
    return minus(b, tools)


def build_all():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for side, tag in ((-1, "L"), (1, "R")):
        out[f"joint_{tag}"] = joint(side)
        out[f"front_idler_{tag}"] = front_idler(side)
        rc = rear_corner(side)
        out[f"rear_corner_{tag}_base"] = rc["base"]
        out[f"rear_corner_{tag}_top"] = rc["top"]
        out[f"dock_bracket_{tag}"] = dock_bracket(side)
        out[f"station_bracket_{tag}"] = dock_bracket(side, P.STATION_RAIL_Y, P.STATION_RAIL_Z)
    for i in range(P.INDX_TOOLS):
        out[f"station_cradle_T{i}"] = station_cradle(i)
        out[f"purge_bucket_T{i}"] = purge_bucket(i)
    car, caps = carriage()
    out["carriage"] = car
    for i, cp in enumerate(caps):
        out[f"carriage_clamp_cap_{i + 1}"] = cp
    for name, shp in out.items():
        if not shp.isValid():
            shp.fix(1e-6, 1e-6, 1e-6)
        shp.exportBrep(os.path.join(OUT, name + ".brep"))
        shp.exportStep(os.path.join(OUT, name + ".step"))
        print(f"{name:26s} solids {len(shp.Solids)} valid {shp.isValid()} volume {shp.Volume / 1000:8.2f} cm3 "
              f"mass {shp.Volume * 1.30e-3:6.1f} g (PPS-CF 1.30)")
    return out


if __name__ == "__main__":
    build_all()
