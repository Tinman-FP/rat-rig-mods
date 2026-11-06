"""Offline check of klipper/config/homing_indx.cfg: parse the configs as Klipper does, render the macros with
Klipper's Jinja settings, and replay every move for several G28 cases. Bondtech's helper macros are stubs.

  python3 vc12_homingcheck.py ../klipper/config <Bondtech's INDX/macros folder (homing.cfg)> ../checks/homing_report.json
"""
import configparser, sys, json, re
import jinja2

KL, BT = sys.argv[1], sys.argv[2]           # our klipper/config folder, Bondtech's macros folder
fc = configparser.RawConfigParser(strict=False, inline_comment_prefixes=(';', '#'))
fc.read([f"{KL}/INDX_Tools.cfg", f"{BT}/homing.cfg", f"{KL}/Motion_XY.cfg", f"{KL}/homing_indx.cfg"])
ho = fc.get("homing_override", "gcode")
assert "_HOME_XY_TWICE" in ho, "our [homing_override] did not replace Bondtech's"
assert fc.get("homing_override", "axes").strip() == "xyz"
sx, sy = dict(fc.items("stepper_x")), dict(fc.items("stepper_y"))
for s in (sx, sy):
    assert float(s["homing_retract_dist"]) == 0 and "second_homing_speed" not in s
LIM = {"x": (float(sx["position_min"]), float(sx["position_max"])), "y": (float(sy["position_min"]), float(sy["position_max"]))}
END = {"x": float(sx["position_endstop"]), "y": float(sy["position_endstop"])}
CLEARANCE_Y = 0.0                            # TOOL_POSITIONS clearance_y for this machine (docks at Y -40)
settings = {"stepper_x": {"position_endstop": END["x"], "homing_positive_dir": sx["homing_positive_dir"].strip().lower() == "true"},
            "stepper_y": {"position_endstop": END["y"], "homing_positive_dir": sy["homing_positive_dir"].strip().lower() == "true"}}
env = jinja2.Environment('{%', '%}', '{', '}', extensions=['jinja2.ext.do'])
T_HO = env.from_string(ho)
T_TW = env.from_string(fc.get("gcode_macro _HOME_XY_TWICE", "gcode"))
tw_vars = {k[len("variable_"):]: float(v) for k, v in fc.items("gcode_macro _HOME_XY_TWICE") if k.startswith("variable_")}

def run(case, start, homed, offset=(0.0, 0.0), tool=0):
    st = {"pos": dict(start), "homed": set(homed), "log": [], "err": None}
    def printer():
        return {"toolhead": {"homed_axes": "".join(a for a in "xyz" if a in st["homed"]), "position": {"y": st["pos"]["y"]}},
                "gcode_macro TOOL_POSITIONS": {"tools": [0, 1, 2, 3, 4], "clearance_y": CLEARANCE_Y, "dock_dir": -1},
                "gcode_macro _HOME_XY_TWICE": tw_vars, "configfile": {"settings": settings},
                "gcode_move": {"homing_origin": {"x": offset[0], "y": offset[1]}},
                "save_variables": {"variables": {"active_tool": tool}}, "bed_mesh": {"mesh_matrix": [[]]}}
    def execute(text):
        for line in text.splitlines():
            line = line.strip()
            if not line or st["err"]:
                continue
            w = line.split()
            cmd = w[0].upper()
            if cmd == "_HOME_XY_TWICE":
                p = dict(a.split("=") for a in w[1:])
                execute(T_TW.render(printer=printer(), params=p))
            elif cmd == "G28":
                for a in w[1:]:
                    a = a.lower()
                    if a in "xy":
                        st["pos"][a] = END[a]; st["homed"].add(a)
                        st["log"].append(f"home {a.upper()} at Y {st['pos']['y']:.1f}" if a == "x" else "home Y")
                        if a == "x" and st["pos"]["y"] < CLEARANCE_Y:
                            st["err"] = f"X homed at Y {st['pos']['y']} in front of the clearance line"
            elif cmd in ("G0", "G1"):
                for a in w[1:]:
                    ax = a[0].lower()
                    if ax in "xy":
                        m = float(a[1:]) + offset["xy".index(ax)]
                        if ax not in st["homed"]:
                            st["err"] = f"{a}: {ax.upper()} not homed"
                        elif not LIM[ax][0] <= m <= LIM[ax][1]:
                            st["err"] = f"{a}: machine {m:.3f} outside {LIM[ax]}"
                        else:
                            st["pos"][ax] = m
                            st["log"].append(f"move {ax.upper()} {m:.1f}")
            elif cmd.startswith("_INDX") or cmd in ("G90", "G4", "M400", "RESPOND", "BED_MESH_CLEAR"):
                if cmd in ("_INDX_SAFE_Z_HOP", "_INDX_HOME_Z"):
                    st["log"].append(cmd)
            else:
                st["err"] = f"unexpected command {line}"
    params = {k: "" for k in case.split()[1:]}
    execute(T_HO.render(printer=printer(), params=params))
    return st

cases = [
    ("G28", {"x": 300, "y": 200}, "", (0, 0)),
    ("G28 X Y", {"x": 102, "y": -40}, "xyz", (0, 0)),           # head at T1's dock
    ("G28 X", {"x": 149, "y": -40}, "xyz", (0, 0)),             # head at T1's purge spot, Y homed
    ("G28 X", {"x": 200, "y": 100}, "", (0, 0)),               # Y unknown: homes Y first
    ("G28 Y", {"x": 250, "y": 300}, "xyz", (0, 0)),
    ("G28 Z", {"x": 250, "y": 250}, "xy", (0, 0)),
    ("G28", {"x": 250, "y": 250}, "xyz", (1.8, -2.5)),          # a tool offset active
]
ok = True
out = []
for case, start, homed, off in cases:
    st = run(case, start, homed, off)
    seq = st["log"]
    if case in ("G28", "G28 X Y") or (case == "G28 X" and homed == ""):
        ok &= [s for s in seq if s.startswith("home")] == ["home Y", "home X at Y 388.8", "home Y", "home X at Y 484.8"]
    if case == "G28 X" and homed:
        ok &= [s for s in seq if s.startswith("home")] == ["home X at Y 388.8", "home X at Y 388.8"]
    if case == "G28 Y":
        ok &= [s for s in seq if s.startswith("home")] == ["home Y", "home Y"]
    if case == "G28 Z":
        ok &= not any(s.startswith(("home", "move")) for s in seq) and "_INDX_HOME_Z" in seq
    ok &= st["err"] is None and seq[0] == "_INDX_SAFE_Z_HOP"
    out.append({"case": case, "start": start, "homed": homed, "offset": off, "error": st["err"], "sequence": seq,
                "end": {k: round(v, 3) for k, v in st["pos"].items()}})
    print(f"{case:8s} from {start} homed '{homed}' offset {off}: {'OK' if st['err'] is None else st['err']}")
    print("   ", "; ".join(seq))
print("ALL PASS" if ok else "FAIL")
json.dump({"pass": bool(ok), "limits": LIM, "endstops": END, "clearance_y": CLEARANCE_Y, "cases": out}, open(sys.argv[3], "w"), indent=1)
sys.exit(0 if ok else 1)
