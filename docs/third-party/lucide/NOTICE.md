# Third-Party Notices

`radar/icons/*.svg` are icons from **Lucide** (`lucide-static`), copied byte for byte and used under its licence (`LICENSE` in this folder: ISC, with the MIT terms of the Feather project for the icons derived from it).

**Original work:** https://github.com/lucide-icons/lucide
**Version:** see `radar/icons/index.json` (`version`)
**Used for:** the pictogram on each component card of the draw.io diagram (`radar/drawio.py`). Each file's sha256 is in `radar/icons/index.json`; `tests/test_icons.py` fails when a file differs, is missing or is not listed.

To update: copy the new `<name>.svg` files from the package over the old ones, copy its `LICENSE` here, then fix `version` and the `sha256` values in `index.json` (keep each `gloss`). A name is added by adding its file and an `index.json` entry with a short meaning for the writer prompt.
