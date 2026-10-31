# Rat Rig Mods

Public Rat Rig mod and printed-part collection from William Tinney / Tinman-FP.

This repository keeps the printable Rat Rig work separate from the experimental RatOS Raspberry Pi 5 repository so friends and builders can download the parts without mixing them with firmware or OS experiments.

## Printed Parts

The public release bundle is in [printed-parts](printed-parts/).

Source copied from:

`/Users/williamtinney/Library/CloudStorage/Dropbox/3D Printing/Rat Rig/Printed Parts`

Published on July 15, 2026.

Current bundle size:

- 161 source files, plus repository README and manifest files
- about 297 MB
- STL, STEP/STP, 3MF, F3D, PDF, ZIP, README, and license files

The source folder contained one macOS `.DS_Store` metadata file; it was intentionally omitted.

## Repository Layout

- [INDX](INDX/) - V-Core 4.1 500 conversion from IDEX to a single carriage on true 12 mm-belt CoreXY with a Bondtech INDX five-tool changer, PPS-CF parts, and one purge bucket and wiper per tool. It includes the installation guide, bill of materials, Tinman print project, CAD and the parametric source. Design checked in CAD only; not yet built.
- [printed-parts/custom-mods](printed-parts/custom-mods/) - Tinman-FP Rat Rig custom parts, panels, toolhead pieces, wire covers, chamber heater parts, and full assembly references.
- [printed-parts/rat-rig-official](printed-parts/rat-rig-official/) - Rat Rig V-Core official printed-part sets and archived bundles preserved from the source folder.
- [printed-parts/community-mods](printed-parts/community-mods/) - Imported/community mod files such as lighting mounts and V-Core door hinge models.
- [printed-parts/reference-cad](printed-parts/reference-cad/) - Vendor and reference CAD used for fitment and mod design.

For a complete file list with SHA-256 checksums, see [MANIFEST.tsv](MANIFEST.tsv).

## Download

For casual download, open [printed-parts](printed-parts/) and download the files you need.

For a full command-line clone with all large CAD and mesh files:

```bash
git lfs install
git clone https://github.com/Tinman-FP/rat-rig-mods.git
cd rat-rig-mods
git lfs pull
```

Git LFS is used for CAD, mesh, archive, and PDF assets so the repository can include the full release payload, including the large Rat Rig V-Core 4.0 500 IDEX STEP assembly.

## Fitment

Review each part before printing or installing it. Match the part to your exact Rat Rig size, revision, toolhead, electronics, enclosure, probe, and material requirements.

This is an unofficial community mod repository and is not affiliated with, endorsed by, or maintained by Rat Rig.

## Credits

See [ATTRIBUTION.md](ATTRIBUTION.md).

## Licensing

There is no single blanket license applied to every model in this repository because this is a mixed-source mod collection. Included upstream README and LICENSE files are preserved in place. Custom Tinman-FP files are shared for community use, but every builder should verify the part source, fitment, and license before reuse or redistribution.
