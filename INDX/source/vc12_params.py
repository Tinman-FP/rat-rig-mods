"""Rat Rig V-Core 4.1 500: 12 mm CoreXY + Bondtech INDX conversion, shared geometry.

All coordinates are the owner's V-Core 4.1 500 IDEX CAD frame, in mm:
X to the right, Y to the rear, Z up. Yg is the Y of the X-beam centre line,
xc the X of the carriage (nozzle) centre line.

Pure Python (no FreeCAD), so the belt solver can be run and tested anywhere.
"""
import math

# ---------------------------------------------------------------- stock frame
SIDE_IN_X = 370.0              # inner faces of the gantry-level side 3030s
SIDE_Z = (701.14, 731.14)        # gantry-level side and rear 3030s
REAR_IN_Y = 337.5              # inner face of the gantry-level rear 3030
REAR_POST_Y = (337.5, 367.5)   # rear corner uprights, X +/-(370..400), full height
FRONT_VERT_Y = (-367.5, -337.5)
DOOR_IN_Y = -367.5              # door panel's inner face = frame front (magnet holders sit at |x| 356-369)
Y_RAIL_X = 385.0               # MGN12 Y rails on top of the side 3030s
Y_RAIL_Y = (-305.5, 294.5)
Y_RAIL_Z = (731.14, 739.14)
Y_BLOCK_Z = (734.14, 744.14)     # MGN12C, 27 wide, 34.5 long incl. seals
Y_BLOCK_HOLES = [(-10.0, -7.5), (-10.0, 7.5), (10.0, -7.5), (10.0, 7.5)]
BEAM_HALF_L = 362.5            # V-Core 4.1 steel gantry, 18 x 18
BEAM_HALF_W = 9.0
BEAM_Z = (703.14, 721.14)
BEAM_TNUT_X = (358.5, 348.5)   # M5 square T-nuts in the tube, from below
X_RAIL_Z = (721.14, 729.14)
X_RAIL_HALF_L = 337.5          # MGN12 675 mm
X_BLOCK_Z = (724.14, 734.14)     # MGN12C, 27 wide, 34.7 long incl. seals
X_BLOCK_HALF_W = 13.5
X_BLOCK_HOLES = [(-7.5, -10.0), (-7.5, 10.0), (7.5, -10.0), (7.5, 10.0)]
BED_X = 264.5
BED_Y = (-312.5, 216.5)
PEI_Y = (-313.0, 207.0)
BED_TOP_MAX_STOCK = 671.4      # bed carriages at the top of the HG15 rails
BED_RAISE = 20.0               # longer spacers at the three kinematic balls

# ---------------------------------------------------------------- INDX head
# From Bondtech's INDX_simplified_1.19.step (RG frame: tip at Y -31.5 on the
# nozzle axis, block face at Z -33.7, 20 x 20 grid centre 40 mm above the tip).
TIP_Z = 688.0                  # seated nozzle tip; bed max becomes 691.4
INDX_FACE_DY = -18.0           # INDX X-carriage block face, relative to Yg
INDX_NOZZLE_DY = INDX_FACE_DY - 33.7
INDX_GRID_DZ = 40.0            # 20 x 20 grid centre above the tip
INDX_PCB_DZ = 55.0             # PCB cover starts this far above the tip
INDX_PCB_BACK = 28.3           # and reaches this far behind the block face
INDX_DOCK_PITCH = 116.0        # owner's choice: tools well apart, each with its own purge bucket and wiper
                               # between it and the next dock (see the station section below)
HEAD_CLEAR_RIGHT = 41.4        # measured, Bondtech's real 4010 duct meshes: least nozzle X offset at which the
HEAD_CLEAR_LEFT = 44.5         # head + tool clears a dock and its parked tool on the head's left / right,
                               # anywhere on the way in from the clearance line (Bondtech states 41). The
                               # earlier 62 mm pitch came from treating the ducts as solid boxes (47 / 59.5).
INDX_TOOLS = 5
INDX_Y_LOST = 28.5             # README: Y travel lost to the dock bank (with the bare head)
INDX_CLEARANCE = 40.0          # nozzle Y behind the docked nozzle for X moves and printing. Bondtech's 26 mm
                               # clears the head body and tool, but with the radial-cooling ducts fitted the
                               # ducts clip a parked tool beside the head up to about 38 mm (measured, real STLs)
INDX_DOCK_FRONT = 48.0         # dock front face ahead of the docked nozzle
INDX_BAR_DY = -31.5            # 1515 bar centre ahead of the docked nozzle
INDX_BAR_DZ = 46.4             # and above the seated tip

# ---------------------------------------------------------------- belt hardware
BELT_W = 12.0
BELT_T = 1.38
BELT_PITCH_FROM_BACK = 0.376   # pitch line to the belt back (2 mm GT, PLD 0.254)
R_TOOTH = 40.0 / math.pi / 2   # 20T pitch radius, 6.366
R_SMOOTH = 7.5 + BELT_PITCH_FROM_BACK   # 15 mm smooth idler, belt back on it
TOOTHED_IDLER = dict(od_flange=15.0, length=16.0)       # McMaster 3693N13 class
SMOOTH_IDLER = dict(od=15.0, od_flange=19.0, length=18.0)  # MISUMI HBGA15-16
DRIVE_PULLEY = dict(od_flange=15.0, flange_len=15.0, hub_len=7.0, hub_od=14.0)  # 3684N14

PLANE_A = 704.5                # lower belt centre: left motor, left front idler
PLANE_B = 723.5                # upper belt centre: right motor, right front idler

# ---------------------------------------------------------------- belt layout
LANE_F = -16.0                 # front X-run pitch line, relative to Yg
LANE_R = 16.0                  # rear X-run pitch line, relative to Yg
X_OUT = 366.8                  # outer Y column (|x|), teeth face the 3030
X_IN = X_OUT - 2 * R_SMOOTH    # inner Y column of each front-going end
J_F_X = X_IN - R_TOOTH         # joint idler, front-going end (toothed)
J_F_DY = LANE_F - R_TOOTH
J_R_X = X_OUT - R_SMOOTH       # joint idler, rear-going end (smooth)
J_R_DY = LANE_R + R_SMOOTH
FRONT_IDLER_Y = -321.0         # front idlers (smooth, 180 degree wrap)
CROSS_Y = 334.5                # rear crossing pitch line
CORNER_X = X_OUT - R_SMOOTH    # R2 and the other plane's corner idler
CORNER_Y = CROSS_Y - R_SMOOTH
R1_Y = 306.0                   # first idler of the motor wrap
MOTOR_X = 333.0                # |x| of both motor axes
MOTOR_Y = 318.5
CLAMP_DX = 46.0                # belt ends enter the carriage this far from xc

# ---------------------------------------------------------------- travel
DOCK_NOZZLE_Y = -317.5         # docked nozzle Y: dock fronts 2 mm behind the closed door
DOCK_BAR_Y = DOCK_NOZZLE_Y + INDX_BAR_DY     # -349.0
DOCK_BAR_Z = TIP_Z + INDX_BAR_DZ
DOCK_X0 = -263.0               # T0; the row is placed so the five stations sit symmetric about X 0
DOCK_X = [DOCK_X0 + INDX_DOCK_PITCH * i for i in range(INDX_TOOLS)]   # -263, -147, -31, 85, 201
YG_DOCK = DOCK_NOZZLE_Y - INDX_NOZZLE_DY                 # -265.8 at pickup
YG_FRONT_STOP = YG_DOCK - 1.0  # crash stop just past pickup; Y homes to the rear
YG_REAR_STOP = 263.0           # hard stop; nozzle reaches the PEI rear edge at 258.7
YG_REAR_SOFT = 260.5
# ---------------------------------------------------------------- purge and wipe stations (one per tool)
# The dock rail runs the full width at the head's slot height, so the nozzle never gets further forward than
# the tool pickup (Y -317.5): only 4.5 mm past the PEI's front edge. Everything below Z 690 is under the head's
# lowest part (the radial duct, 3.2 mm above the tip), so the stations sit there, in front of the bed.
# Each tool has its own station just right of its dock: purge spot, then a Qidi silicone wiper pad, over its
# own bucket. The bucket also sits under its own parked tool, so it catches that tool's drips.
STATION_RAIL_Y = -352.5        # second 1515, same front-upright T-slot as the dock rail
STATION_RAIL_Z = 605.5         # centre
PURGE_Y = DOCK_NOZZLE_Y        # -317.5: as far forward as the nozzle goes
PURGE_DX = 47.0                # purge spot right of its own dock (HEAD_CLEAR_RIGHT + 5.6)
PAD = (15.0, 27.0, 4.7)        # Qidi nozzle wiper pad (owner's part): X, Y, height
PAD_DX = 6.0                   # pad's left edge, right of the purge spot: the strand drops clear of it
PAD_REAR_Y = -314.5            # 1.5 mm ahead of the PEI sheet; the nozzle wipes 3 mm in from this edge
WIPER_TOP = TIP_Z + 1.2        # SV08 rule: wiper top 1.2 mm above the nozzle tip
WIPE_X = (PAD_DX - 2.0, PAD_DX + 14.0)   # nozzle stroke across the pad, relative to the purge spot; it starts
                                         # and ends 2 mm off the pad's left end, so wipings drop in the bucket
PURGE_X = [d + PURGE_DX for d in DOCK_X]             # -216, -100, 16, 132, 248 (Klipper X = CAD X + 255)
PAD_X = [p + PAD_DX for p in PURGE_X]                # pad left edges
# right end of each stroke to the next dock: INDX_DOCK_PITCH - PURGE_DX - WIPE_X[1] = 49 (HEAD_CLEAR_LEFT + 4.5)
STATION_DX = -13.0             # station's left edge relative to its dock
STATION_W = 88.0               # cradle outside width; the five cradles and five buckets are identical
STATION_X0 = [d + STATION_DX for d in DOCK_X]        # -276 .. 276
CRADLE_WALL = 3.0
BUCKET_GAP = 0.4               # each side, bucket to cradle wall
BUCKET_WALL = 2.4
BUCKET_RIM_Z = 669.0           # purge falls 19 mm
BUCKET_REAR_Y = -315.0         # 2 mm ahead of the bed plate, 2.5 mm ahead of the PEI sheet
BUCKET_FRONT_Y = -362.0        # body; its front flange reaches -364.5, 3 mm behind the closed door
BUCKET_FLANGE = 2.5            # the flange is the finger pull and the stop against the cradle fronts
ARM_TOP_Z = 643.9              # front bed arms at the top of their travel; their front edge reaches Y -319.5
                               # (X 240..280), so below this every station part stays at Y -323.5 or ahead
BUCKET_LOW_REAR_Y = -323.5
BUCKET_SLOPE_Z = 646.0         # the bucket's back slopes from (-323.5, 646) up to (-315, 669)
BUCKET_PULL = 60.0             # slide-out travel through the open door; then it lifts out
DETENT_Y = -340.0              # ridge on the cradle floor, groove under the bucket: holds it home, no fasteners
DOOR_SPACER = 0.0              # owner chose no door change (option 1): docks and head reach Y -365.5
FRONT_IDLER_SLOT = 3.5         # front idler axle travel either side of nominal
JOINT_Y = (-31.0, 32.0)        # joint top plate front/rear faces, relative to Yg (the stop faces)
XC_STOP = 290.0                # |xc|; joints' inner faces at about 339


def plane_wraps(plane, xc, yg):
    """Ordered wraps for one belt, from its left carriage clamp to its right one.

    Each wrap is (name, cx, cy, r, s) with s = +1 for a left (CCW) turn and -1 for
    a right (CW) turn, seen from above while walking the belt left clamp to right
    clamp. Plane A is front-going at the left joint, plane B at the right joint.
    """
    s = 1 if plane == "A" else -1     # plane B is plane A mirrored in X
    w = []
    if plane == "A":
        start = (xc - CLAMP_DX, yg + LANE_F)
        end = (xc + CLAMP_DX, yg + LANE_R)
        w.append(("J_LF", -J_F_X, yg + J_F_DY, R_TOOTH, +1))
        w.append(("F_L", -CORNER_X, FRONT_IDLER_Y, R_SMOOTH, -1))
        w.append(("R1_L", -CORNER_X, R1_Y, R_SMOOTH, -1))
        w.append(("M_L", -MOTOR_X, MOTOR_Y, R_TOOTH, +1))
        w.append(("R2_L", -CORNER_X, CORNER_Y, R_SMOOTH, -1))
        w.append(("C_RA", CORNER_X, CORNER_Y, R_SMOOTH, -1))
        w.append(("J_RR", J_R_X, yg + J_R_DY, R_SMOOTH, -1))
    else:
        start = (xc - CLAMP_DX, yg + LANE_R)
        end = (xc + CLAMP_DX, yg + LANE_F)
        w.append(("J_LR", -J_R_X, yg + J_R_DY, R_SMOOTH, -1))
        w.append(("C_LB", -CORNER_X, CORNER_Y, R_SMOOTH, -1))
        w.append(("R2_R", CORNER_X, CORNER_Y, R_SMOOTH, -1))
        w.append(("M_R", MOTOR_X, MOTOR_Y, R_TOOTH, +1))
        w.append(("R1_R", CORNER_X, R1_Y, R_SMOOTH, -1))
        w.append(("F_R", CORNER_X, FRONT_IDLER_Y, R_SMOOTH, -1))
        w.append(("J_RF", J_F_X, yg + J_F_DY, R_TOOTH, +1))
    del s
    # Walking left clamp to right clamp, both belts have their teeth on the left:
    # every +1 wrap meets the teeth (toothed idler or pulley), every -1 the back.
    return start, end, w


def _tangent(c1, r1, s1, c2, r2, s2):
    """Belt line leaving circle 1 and arriving on circle 2 (r = 0 for a point)."""
    dx, dy = c2[0] - c1[0], c2[1] - c1[1]
    L = math.hypot(dx, dy)
    rho1, rho2 = s1 * r1, s2 * r2
    a = math.atan2(dy, dx)
    th = a - math.asin((rho2 - rho1) / L)
    ux, uy = math.cos(th), math.sin(th)
    nx, ny = -uy, ux                      # left normal; centre = point + rho * n
    p1 = (c1[0] - rho1 * nx, c1[1] - rho1 * ny)
    p2 = (c2[0] - rho2 * nx, c2[1] - rho2 * ny)
    return p1, p2


def belt_path(plane, xc, yg):
    """Segments and arcs of one belt's pitch line, left clamp to right clamp.

    Returns (items, total): items are ("line", p1, p2) and
    ("arc", name, centre, r, s, angle_from, sweep) in walking order.
    """
    start, end, wraps = plane_wraps(plane, xc, yg)
    nodes = [("start", start[0], start[1], 0.0, 1)] + wraps + [("end", end[0], end[1], 0.0, 1)]
    lines = []
    for a, b in zip(nodes[:-1], nodes[1:]):
        lines.append(_tangent((a[1], a[2]), a[3], a[4], (b[1], b[2]), b[3], b[4]))
    items, total = [], 0.0
    for i, (p1, p2) in enumerate(lines):
        if i > 0:
            n = nodes[i]
            c = (n[1], n[2])
            ain = math.atan2(lines[i - 1][1][1] - c[1], lines[i - 1][1][0] - c[0])
            aout = math.atan2(p1[1] - c[1], p1[0] - c[0])
            sweep = (aout - ain) * n[4] % (2 * math.pi)
            items.append(("arc", n[0], c, n[3], n[4], ain, sweep))
            total += n[3] * sweep
        items.append(("line", p1, p2))
        total += math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    return items, total


def wrap_deg(plane, name, xc=0.0, yg=0.0):
    for it in belt_path(plane, xc, yg)[0]:
        if it[0] == "arc" and it[1] == name:
            return math.degrees(it[6])
    raise KeyError(name)


def side_length(plane, xc, yg, motor):
    """Belt from the left clamp to where it first touches the motor pulley."""
    items, _ = belt_path(plane, xc, yg)
    total = 0.0
    for it in items:
        if it[0] == "arc":
            if it[1] == motor:
                return total
            total += it[3] * it[6]
        else:
            total += math.hypot(it[2][0] - it[1][0], it[2][1] - it[1][1])
    raise KeyError(motor)


def straightness(plane, xc, yg, tol=1e-6):
    """Every free span should run along X or Y; returns the worst angle in degrees."""
    worst = 0.0
    items, _ = belt_path(plane, xc, yg)
    for it in items:
        if it[0] != "line":
            continue
        dx, dy = it[2][0] - it[1][0], it[2][1] - it[1][1]
        ang = math.degrees(math.atan2(abs(dy), abs(dx)))
        worst = max(worst, min(ang, 90 - ang)) if (abs(dx) > 30 and abs(dy) > 30) is False else worst
    return worst


if __name__ == "__main__":
    poses = [(xc, yg) for xc in (-XC_STOP, 0.0, XC_STOP) for yg in (YG_FRONT_STOP, YG_DOCK, 0.0, YG_REAR_STOP)]
    for plane, motor in (("A", "M_L"), ("B", "M_R")):
        lens = [belt_path(plane, xc, yg)[1] for xc, yg in poses]
        base = side_length(plane, 0.0, 0.0, motor)
        coef = [(side_length(plane, xc, yg, motor) - base, xc, yg) for xc, yg in poses]
        dev = max(abs(d - (xc + (yg if plane == "A" else -yg))) for d, xc, yg in coef)
        print(f"plane {plane}: pitch length {min(lens):.3f}..{max(lens):.3f} mm, "
              f"CoreXY linearity error {dev:.2e} mm, motor wrap {wrap_deg(plane, motor):.1f} deg "
              f"({wrap_deg(plane, motor) / 18:.1f} teeth)")
        for name in ("J_LF", "F_L", "R1_L", "R2_L", "C_RA", "J_RR") if plane == "A" else ("J_LR", "C_LB", "R2_R", "R1_R", "F_R", "J_RF"):
            print(f"   {name:5s} wrap {wrap_deg(plane, name):6.1f} deg")
    print(f"X_IN {X_IN:.3f}  J_F_X {J_F_X:.3f}  J_R_X {J_R_X:.3f}  CORNER {CORNER_X:.3f},{CORNER_Y:.3f}")
    print(f"nozzle Y = Yg {INDX_NOZZLE_DY:+.1f}; printable Y {DOCK_NOZZLE_Y + INDX_CLEARANCE:.1f}..{min(PEI_Y[1], YG_REAR_SOFT + INDX_NOZZLE_DY):.1f}"
          f" (PEI {PEI_Y[0]}..{PEI_Y[1]}); docks at X {DOCK_X}, bar Y {DOCK_BAR_Y} Z {DOCK_BAR_Z}")
    gaps = [(DOCK_X[i + 1] if i + 1 < INDX_TOOLS else XC_STOP + 1e9) - (p + WIPE_X[1]) for i, p in enumerate(PURGE_X)]
    print(f"purge X {PURGE_X}, pads {PAD_X}; head clears its own dock by {PURGE_DX - HEAD_CLEAR_RIGHT:.1f} and the next by "
          f"{min(gaps) - HEAD_CLEAR_LEFT:.1f} mm; stations X {STATION_X0[0]:.0f}..{STATION_X0[-1] + STATION_W:.0f}; "
          f"last stroke ends at X {PURGE_X[-1] + WIPE_X[1]:.0f} (stop {XC_STOP:.0f})")
    print(f"belt cut length each: pitch {belt_path('A', 0, 0)[1]:.0f} + 2 x (clamp 20 + tail 15) = {belt_path('A', 0, 0)[1] + 70:.0f} mm")
