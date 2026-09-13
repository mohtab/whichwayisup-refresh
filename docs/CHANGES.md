# Refresh changes — 2026-09-12

The pre-refresh working tree and legacy saves were archived before editing under
`~/whichwayisup-backups/`. Existing Python 3 conversion edits were retained.

New `refresh/` modules provide the application, display handling, independent timing,
read-only presentation renderer, theme manifests, settings, stage validation/import,
local records and stage editor. New `themes/`, `tests/` and `packaging/` directories
provide palette packs, behavior checks and local/Arch packaging. The original
`README.txt`, `data/` files and Debian notices are preserved.

Modified legacy source:

- `game.py`: expose yielded simulation steps; retain the legacy `run()` wrapper;
  snapshot lists during removal; stop accumulating walking dust while paused;
  guard one-axis joysticks. New projectiles are first updated on the following tick.
- `animation.py`, `frame.py`: share definitions and decoded sprite surfaces with
  bounded caches and explicit missing-file fallbacks.
- `visibleobject.py`: avoid changing the alpha of shared sprite surfaces.
- `level.py`: close input files, initialize editor state, add a tile-cell index,
  narrow collision candidates while preserving their ordering, replace unbounded
  coordinate-string caching, and rebuild indices after rotation/edit.
- `item.py`: avoid requesting nonexistent broken animations for collectibles.
- `menu.py`: load the menu backdrop once outside its frame loop.
- `util.py`: bound text-surface caching; preserve the earlier bundled-font repair.
- `run_game.py`: launch the refresh by default; preserve `--legacy`; select native
  Wayland automatically when available, respecting an explicit SDL backend override.

Additional existing modifications visible in git predate this build and are captured
in the backup patch. This refresh does not claim those changes as newly authored work.
