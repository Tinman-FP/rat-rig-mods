"""The owner's top hat, as it sits on their 500 (run with FreeCAD's Python).

  VC12_HAT=<Rat Rig Top Hat Modular.step>
  /Applications/FreeCAD.app/Contents/Resources/bin/python vc12_hat.py <hat_out.brep>

The owner's file (exported 2026-11-03) holds the eight printed modules where they sit on the machine: four corners (the
front right one with the display window), a centre module front and back, and a middle module each side. In the file
the front is +Y and the frame's top sits at Z 110.8. This turns it 180 deg about Z and moves it onto the frame: the
modules' 5 mm tongues land in the top 3030 slots (slot centres X +/-385, Y +/-352.5) and their undersides on the frame
top (P.TOP_FRONT_Z[1]).

The hat is a 141 mm ring: 40 mm corner walls, 50 mm centre walls standing 5 mm proud of the corners, and hollow side
middles. The lid sits in a 6 mm pocket whose floor is 130 mm above the frame top (P.HAT_LID_Z); the 10 mm rim round it
is 136 above (P.HAT_RIM_Z). The display window goes through the front right corner's wall, behind tool 4's tube.
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

FILE_CENTRE = (264.78, -51.0)       # frame centre in the owner's file (midway between the tongues)
FILE_FRAME_TOP = 110.8              # frame top in the owner's file (the tongues reach 5 mm below it)


def hat(path=None):
    """The owner's eight hat modules on the frame, in machine coordinates."""
    doc = App.newDocument("hat")
    Import.insert(path or os.environ["VC12_HAT"], doc.Name)
    cx, cy = FILE_CENTRE
    out = []
    for o in doc.Objects:
        if o.TypeId == "Part::Feature" and o.Shape.Solids:
            s = o.Shape.copy()
            s.Placement = o.getGlobalPlacement()
            s.rotate(V(cx, cy, 0.0), V(0, 0, 1), 180.0)
            s.translate(V(-cx, -cy, P.TOP_FRONT_Z[1] - FILE_FRAME_TOP))
            out.extend(s.Solids)
    App.closeDocument(doc.Name)
    return Part.makeCompound(out)


if __name__ == "__main__":
    h = hat()
    h.exportBrep(sys.argv[1])
    b = h.BoundBox
    print("hat", len(h.Solids), "solids, bbox", [round(v, 1) for v in (b.XMin, b.XMax, b.YMin, b.YMax, b.ZMin, b.ZMax)])
