# Build status — 0.1.0, 2026-09-12

This is a playable local build, not completion of every milestone in `REWORK_PLAN.md`.
No repository, public catalog or release has been published.

## Implemented

- Safe, resizable desktop application; native Wayland preference; fullscreen
  confirmation and 10-second rollback. New launches start in windowed mode.
- Five selectable visual treatments, independent character selection, editable accent,
  exportable TOML palette packs and live Omarchy palette reading at menu boundaries.
- Original assets and all 15 campaigns preserved and playable.
- New code-drawn Refresh / Omarchy / DHH / Cyberpunk art. These are revisable first
  designs, not an approved final art direction. Cyberpunk laser bolts preserve existing
  projectile rules.
- Independent display pacing and interpolation; selectable 0.75×–1.5× gameplay tempo.
- Shared asset/animation caches, indexed tile collision, bounded text caches, stable
  removal iteration, one-axis controller guard and audio fallback.
- Remappable primary keyboard bindings, generic controller input, mouse/menu controls,
  pause on focus loss, and controller-disconnect pause.
- Separate atomic XDG settings/records and a one-time preserved copy of old save metadata.
- Original and user-stage browser, validated JSON/TXT import, local authoring studio,
  undo/redo, board rotation, entity placement, goal/message editing, metadata, autosaved
  drafts, playtest, and JSON export. Resume the most recent draft from the library.
- Credits, full original notices, GPL text, source archive recipe, local application
  registration and a checksum-pinned Arch package recipe.

## Verification evidence

- Automated suite covers all original stage round-trips and simulation, 4,800 sampled
  collision comparisons across four rotations, timing independence at 30/60/120/144/240
  display rates, each supported tempo, stage-goal completion, stage authoring/import,
  malformed content, warm asset loading, non-mutating theme rendering and theme export.
- `desktop-verification.json` records actual **Wayland** tests on **2560 × 1600**:
  three fullscreen/windowed round-trips, rollback, play/pause, theme changes and editor
  playtest. Windowed size was ultimately managed by Hyprland at 1280 × 774.
- `legacy-comparison.json`: the first stage's scripted 221-frame trace matched the
  pre-refresh checkout for player position, health, gameplay timer and rotation.
  This is a sampled compatibility check, not a proof of exact whole-game equivalence.
- Comparable headless audit: image-load attempts **5,802 → 70**; profiled execution
  **3.779 s → 1.592 s**; cumulative tile collision **1.017 s → 0.051 s**. These are
  single-run diagnostic measurements, not promised end-user FPS improvements.
  See `legacy-profile.txt`, `refresh-profile.txt`, and their audit JSON files.
- Screenshots of the main themes and studio are in `docs/screenshots/`.

## Explicitly outstanding

- Collaborative final art direction and richer sprite animation, including refinement
  of the DHH cameo. Theme manifests currently customize palettes and built-in drawing
  styles; arbitrary image/sound replacement packs are not implemented yet.
- A distinct 120 Hz Modern physics profile, jump buffering/coyote time, true beam
  weapon variants and assist tuning. Current tempo uses the tested original 24 Hz
  rules, independent of render rate. This avoids claiming an unvalidated physics port.
- Successful full playthrough/completion replays of all 15 original stages. The audit
  exercises loading, movement and rotation; it does not establish campaign completion.
- Hardware controller testing, multiple monitors, suspend/resume, Windows/macOS/mobile,
  and sustained high-refresh performance/memory acceptance across devices.
- ZIP/asset packs, arbitrary event editing beyond the built-in goal controls, draft
  history browsing, public replay verification, hosted submissions/catalog, moderation
  and online leaderboards. Local JSON stages are the current community-content foundation.
- A publication review of final branding and all new asset provenance before distribution.

Original data and saves remain recoverable in the pre-build archive. The local launcher
points at this checkout, so moving/deleting it requires rerunning local installation.
