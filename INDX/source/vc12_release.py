"""Write an STL for every printed part (assembly orientation; see README for print orientation)."""
import glob
import os
import sys

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD  # noqa: E402,F401
import MeshPart  # noqa: E402
import Part  # noqa: E402

PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "parts")
for path in sorted(glob.glob(os.path.join(PARTS, "*.brep"))):
    s = Part.Shape()
    s.read(path)
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.05, AngularDeflection=0.3, Relative=False)
    out = path[:-5] + ".stl"
    m.write(out)
    print(f"{os.path.basename(out):30s} facets {m.CountFacets:7d} solid {m.isSolid()} non-manifold {m.hasNonManifolds()}")
