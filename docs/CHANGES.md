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


## 2026-09-13 — local polish 0.2

- Keyboard shortcuts, keyboard studio cursor, controls guide, revised home/settings/
  play/results/credits/records screens, original ambient audio with separate volumes.
- Correct multiline and long-word text layout, title/input clipping, three tutorial
  hints adapted to current bindings, one-press fully displayed dialogue.
- Distinct procedural movement poses, smoother 16-phase cycle, essential interpolation
  retained with reduced effects. Original assets and collision dimensions unchanged.
- Isolate preview/session fade, randomness and settings; clear stale menu actions;
  freeze current run categories on retry; handle failed saves/autosaves gracefully.
- Comparable local PBs and per-PB replay files, local replay verifier, simulated gamer
  profile tests, native/visual review tooling and community release proposal.
- Modified code: refresh/app.py, art.py, display.py, editor.py, runtime.py, storage.py,
  ui.py; lib/game.py (refresh-only dialogue), lib/sound.py (volume multiplier).
  New code: refresh/audio.py, desktop.py, runs.py; tools/verify_replay.py and review tooling.
- Mohtab Arabiat credited for refresh direction and Linux origin story; original
  creator and all upstream license notices retained in Credits, not the home footer.
