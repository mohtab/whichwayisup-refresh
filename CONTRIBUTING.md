# Contributing to the homage

The original game is by Olli “Hectigo” Etuaho. Preserve that credit, the original
license notices, and attribution for every contribution you build upon.

## Submit a stage

Export a stage JSON from the studio and propose it in a GitHub pull request.
Include:

1. Stage title, author name and explicit content license.
2. The exported JSON, tested in the current refresh version.
3. Difficulty, expected completion time and whether rotation is required.
4. A completion replay or a clear playtest route, plus a screenshot.
5. Attribution for adapted content and confirmation that you can share the contribution.

New independently created stages may use CC BY 4.0. A remix of an original stage must
retain its CC BY 3.0 material attribution; do not replace its license with a blanket
claim that you created everything. Submitting a stage does not transfer its authorship.

Run `python run_game.py --import-stage path/to/stage.json` to validate and import.
Unknown entity types, malformed tile maps and executable actions will be rejected.
Maintainer review is still needed for solvability, quality and attribution. Nothing is
automatically uploaded from your machine.

## Report a problem or share an idea

Use the repository’s issue forms for bugs and suggestions. Include your version,
Linux distribution, and steps to reproduce a bug. For setup help, start with the
[install guide](docs/INSTALL.md).

## Code and visual design

Code and code-drawn artwork in this repository use GPL version 2. Keep a source form
that can be edited and rebuilt, note changes and preserve existing notices. Add focused
behavior tests for physics, save migration, stage parsing or input changes. Run:

```sh
python -m unittest discover -s tests -v
```

The Original theme is a maintained compatibility option. Theme changes must not alter
collision dimensions, stage geometry, scoring or physics. Keep projectiles distinguishable
from collectibles and ensure hazard readability in low-effects and light-palette modes.

Public release preparation must include full source, installation scripts, original
asset/font notices and a review of new artwork/branding permissions. Do not imply
endorsement by the original author, DHH or Omarchy.
