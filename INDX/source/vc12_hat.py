"""The owner's top hat at 500 size, built from their 400 model (run with FreeCAD's Python).

  VC12_HAT400=<Rat Rig Vcore 4 Idex 400 Top Hat.step>
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_hat.py <hat500_out.brep>

The owner's hat is the one in "Rat Rig Vcore 4 Idex 400 Top Hat.step", which they scaled down from their 500 for a
friend: the wall sections are the same, only the straight runs are shorter (700 x 635 frame instead of 800 x 735). This
cuts the 400 hat on X = 0 and Y = 0, moves each quarter out (50 mm in X, 50.5 mm in Y, so the lid pocket takes the
500's 800 x 736 top panel) and fills each gap with a copy of the 400's middle 100 mm. Module joints, the display
cut-out and the fan openings may sit elsewhere on the real 500 hat; the rim, lid pocket, corners and wall sections are
the owner's.

In both sizes the hat stands on the frame top with 5 mm tongues in the top 3030 slots. The stock top panel sits in
its pocket 130 mm above the frame top (P.HAT_LID_Z), 2 mm below the rim (P.HAT_RIM_Z).
"""
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import FreeCAD as App  # noqa: E402
import Import  # noqa: E402
import Part  # noqa: E402
from FreeCAD import Vector as V  # noqa: E402

import vc12_params as P  # noqa: E402

FRAME_TOP_400 = 881.14              # frame top in the owner's 400 file
GROW = (50.0, 50.5)                 # per side, X and Y
MODULES = ("Corner", "Middle", "Center")
BIG = 3000.0


def _box(x0, x1, y0, y1):
    return Part.makeBox(x1 - x0, y1 - y0, BIG, V(x0, y0, -BIG / 2))


def hat400(path):
    """The 400 hat's eight printed modules, in the 400 file's own frame."""
    doc = App.newDocument("hat400")
    Import.insert(path, doc.Name)
    out = []
    for o in doc.Objects:
        if o.TypeId == "Part::Feature" and o.Shape.Solids and any(k in o.Label for k in MODULES):
            s = o.Shape.copy()
            s.Placement = o.getGlobalPlacement()
            out.append(s)
    App.closeDocument(doc.Name)
    return Part.makeCompound(out)


def hat500(path=None):
    """The owner's hat stretched to the 500 frame and standing on its top 3030s."""
    src = hat400(path or os.environ["VC12_HAT400"])
    gx, gy = GROW
    dz = P.TOP_FRONT_Z[1] - FRAME_TOP_400
    pieces = []
    for sx in (-1, 1):
        for sy in (-1, 1):                                   # quarters, moved out
            q = src.common(_box(*sorted((0.0, sx * BIG)), *sorted((0.0, sy * BIG))))
            q.translate(V(sx * gx, sy * gy, dz))
            pieces.append(q)
        f = src.common(_box(*sorted((0.0, sx * BIG)), -gy, gy))   # side wall gap: the 400's middle 101 mm in Y
        f.translate(V(sx * gx, 0.0, dz))
        pieces.append(f)
    for sy in (-1, 1):                                       # front and back wall gaps: the 400's middle 100 mm in X
        f = src.common(_box(-gx, gx, *sorted((0.0, sy * BIG))))
        f.translate(V(0.0, sy * gy, dz))
        pieces.append(f)
    return Part.makeCompound([s for p in pieces for s in p.Solids])


if __name__ == "__main__":
    h = hat500()
    h.exportBrep(sys.argv[1])
    b = h.BoundBox
    print("hat500", len(h.Solids), "solids, bbox", [round(v, 1) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
