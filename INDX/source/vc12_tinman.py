"""Import the print-ready STLs into Tinman and save one project 3MF (no printer contact).

Runs Tinman's command line in a throwaway data folder, so the owner's Tinman settings and any
open Tinman window are untouched. Presets are the owner's Qidi Plus 4 PPS-CF combination:
  machine  Qidi X-Plus 4 0.6 nozzle - TinMan Codex
  process  0.24mm Tank @Qidi X-Plus 4 0.6 nozzle - TinMan Codex - Copy
  filament PPS-CF Codex-Bambu - Qidi X-Plus 4
Steps: Tinman imports the parts onto four plates (positions below, supports per part) -> object
and plate names -> Tinman re-saves the project -> Tinman slices a copy to check it. The delivered
3MF is not sliced.
Run with system python3 after vc12_print.py.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STL = ROOT / "print" / "stl"
FINAL = ROOT / "print" / "VC41_CoreXY12_INDX_PPSCF_QidiPlus4_06.3mf"
CHECK = ROOT / "checks" / "tinman_slice.json"
APP = Path("/Applications/Tinman.app/Contents/MacOS/Tinman")
LIVE = Path.home() / "Library/Application Support/Tinman"
PRESETS = {
    "machine": LIVE / "system/Qidi/machine/TinMan Codex/Qidi X-Plus 4 0.6 nozzle - TinMan Codex.json",
    "process": LIVE / "user/default/process/0.24mm Tank @Qidi X-Plus 4 0.6 nozzle - TinMan Codex - Copy.json",
    "filament": LIVE / "user/default/filament/PPS-CF Codex-Bambu - Qidi X-Plus 4.json",
}
BED = "Textured PEI Plate"

# 305 x 305 bed. Part centres (mm); at least 20 mm between parts so tree supports don't meet
PLATES = ["Carriage, joints, front idlers", "Rear corners", "Purge cradles and rail brackets", "Purge buckets"]
LAYOUT = {
    "joint_L": (1, 50, 80), "joint_R": (1, 140, 80), "carriage": (1, 240, 80),
    "front_idler_L": (1, 50, 195), "front_idler_R": (1, 140, 195),
    "carriage_clamp_cap_1": (1, 215, 175), "carriage_clamp_cap_2": (1, 255, 175),
    "carriage_clamp_cap_3": (1, 215, 215), "carriage_clamp_cap_4": (1, 255, 215),
    "rear_corner_L_base": (2, 95, 95), "rear_corner_R_base": (2, 210, 95),
    "rear_corner_L_top": (2, 95, 210), "rear_corner_R_top": (2, 210, 210),
    "station_cradle_T0": (3, 70, 45), "station_cradle_T1": (3, 185, 45), "station_cradle_T2": (3, 70, 115),
    "station_cradle_T3": (3, 185, 115), "station_cradle_T4": (3, 70, 185),
    "dock_bracket_L": (3, 45, 255), "dock_bracket_R": (3, 115, 255),
    "station_bracket_L": (3, 185, 255), "station_bracket_R": (3, 255, 255),
    "purge_bucket_T0": (4, 70, 50), "purge_bucket_T1": (4, 185, 50), "purge_bucket_T2": (4, 70, 125),
    "purge_bucket_T3": (4, 185, 125), "purge_bucket_T4": (4, 127.5, 200),
}


def tinman(datadir, log, *args):
    cmd = [str(APP), "--datadir", str(datadir), *map(str, args)]
    with open(log, "w") as f:
        rc = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=Path(datadir).parent).returncode   # its 00000.log lands there
    if rc:
        sys.exit(f"Tinman exit {rc}; see {log}")


def flatten(src):
    """The command line does not follow a system preset's 'inherits'; merge the chain here."""
    vendor = next(p for p in src.parents if p.parent == LIVE / "system")
    index = {}
    for p in (vendor / src.parent.relative_to(vendor).parts[0]).rglob("*.json"):
        index.setdefault(json.loads(p.read_text()).get("name"), p)
    chain, d = [], json.loads(src.read_text())
    while d:
        chain.append(d)
        parent = d.get("inherits")
        d = json.loads(index[parent].read_text()) if parent else None
    merged = {}
    for d in reversed(chain):
        merged.update(d)
    return merged


def setup():
    work = Path(tempfile.mkdtemp(prefix="vc12-tinman-"))
    data = work / "data"
    shutil.copytree(LIVE / "system", data / "system")
    files = {}
    for kind, src in PRESETS.items():
        d = flatten(src) if src.is_relative_to(LIVE / "system") else json.loads(src.read_text())
        d.setdefault("type", kind)
        if kind == "process":
            d["curr_bed_type"] = BED
        assert not any(d.get(k) for k in d if re.search(r"host|apikey|password|access_code", k, re.I)), kind
        dst = data / "user/default" / kind / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(d, indent=4))
        files[kind] = dst
    return work, data, files


def assemble_list(orient):
    """Tinman places each STL's origin (its bounding-box corner) at pos, relative to its plate."""
    plates = [{"plate_name": n, "need_arrange": False, "objects": []} for n in PLATES]
    for r in orient:
        plate, cx, cy = LAYOUT[r["part"]]
        sx, sy, _ = r["size_mm"]
        objects = plates[plate - 1]["objects"]
        obj = {"path": str(STL / f"{r['part']}.stl"), "count": 1, "filaments": [1],
               "assemble_index": [len(objects)], "pos_x": [cx - sx / 2], "pos_y": [cy - sy / 2], "pos_z": [0]}
        if r["support"]:
            obj["print_params"] = {"enable_support": "1"}
        objects.append(obj)
    return {"plates": plates}


def md(el, key, value):
    e = el.find(f"metadata[@key='{key}']")
    if e is None:
        e = E.SubElement(el, "metadata", key=key)
    e.set("value", value)


def name_objects(src, dst):
    """Name each object after its part (Tinman calls them 'assemble_n') and name the plates."""
    with zipfile.ZipFile(src) as z:
        files = {n: z.read(n) for n in z.namelist()}
    meta = E.fromstring(files["Metadata/model_settings.config"])
    names = []
    for ob in meta.findall("object"):
        part = ob.find("part/metadata[@key='name']").get("value").removesuffix("_1")
        md(ob, "name", part)
        md(ob.find("part"), "name", part)
        names.append(part)
    for i, plate in enumerate(meta.findall("plate")):
        md(plate, "plater_name", f"{i + 1} {PLATES[i]}")
    files["Metadata/model_settings.config"] = E.tostring(meta, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in files.items():
            z.writestr(n, b)
    return names


def slice_summary(sliced, result):
    with zipfile.ZipFile(sliced) as z:
        info = E.fromstring(z.read("Metadata/slice_info.config"))
    plates = []
    for p in info.findall("plate"):
        m = {e.get("key"): e.get("value") for e in p.findall("metadata")}
        plates.append({"plate": int(m["index"]), "name": PLATES[int(m["index"]) - 1],
                       "hours": round(float(m["prediction"]) / 3600, 1), "grams": round(float(m["weight"]), 1),
                       "objects": [o.get("name") for o in p.findall("object")],
                       "warnings": [w.get("msg") for w in p.findall("warning")]})
    return {"tinman_result": json.loads(result.read_text()), "plates": plates,
            "total_hours": round(sum(p["hours"] for p in plates), 1),
            "total_grams": round(sum(p["grams"] for p in plates), 1)}


def main():
    orient = json.loads((ROOT / "print/orientation.json").read_text())
    work, data, files = setup()
    (work / "assemble_list.json").write_text(json.dumps(assemble_list(orient), indent=1))
    tinman(data, work / "1_import.log", "--load-settings", f"{files['machine']};{files['process']}",
           "--load-filaments", files["filament"], "--load-assemble-list", work / "assemble_list.json",
           "--outputdir", work, "--export-3mf", "imported.3mf")
    names = name_objects(work / "imported.3mf", work / "named.3mf")
    assert sorted(names) == sorted(LAYOUT), names
    tinman(data, work / "2_save.log", "--arrange", "0", "--orient", "0", "--outputdir", work / "saved",
           "--export-3mf", FINAL.name, work / "named.3mf")
    shutil.copy2(work / "saved" / FINAL.name, FINAL)
    tinman(data, work / "3_slice.log", "--arrange", "0", "--orient", "0", "--slice", "0",
           "--outputdir", work / "sliced", "--export-3mf", "sliced.3mf", FINAL)
    summary = slice_summary(work / "sliced/sliced.3mf", work / "sliced/result.json")
    CHECK.write_text(json.dumps(summary, indent=1) + "\n")
    print("Tinman work folder (logs, sliced copy):", work)
    print(json.dumps({k: summary[k] for k in ["total_hours", "total_grams"]}),
          *[f"\n plate {p['plate']} {p['name']}: {p['hours']} h, {p['grams']} g, {len(p['objects'])} parts {p['warnings']}"
            for p in summary["plates"]])


main()
