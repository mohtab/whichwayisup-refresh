# Build status — 0.2.1 sprite polish, 2026-09-13

Local review build; not a public release.

- Illustrated explorer with scarf, goggles, six-frame stride, jump stretch, apex,
  falling/gliding poses, landing compression, damage recoil and collapse.
- Armored spiders with articulated scuttle poses and feet anchored to all four
  supporting directions, interpolated through room turns. Studio previews match.
- Ornate compass key with glint/sway animation; restrained pickup, landing and hit effects.
- World art rendered at 1040×1040, preserving more sprite detail when enlarged.
- Original theme and original physics remain available. DHH retains its existing art.
- Four intact generated PNG sheets, exact prompts and provenance in assets/sprites/.
  Arch packaging now includes these required assets.

32 automated tests pass. New checks cover actual jump/landing/damage events, four-way
spider contact, continuous rotation, uncut run strides, grounded crouches, frozen pause
poses and presentation that leaves physics and replay inputs unchanged.

Native Wayland scripted review observed takeoff, rising, apex, falling, gliding,
landing and hurt. Short diagnostic: median frame work 12.78 ms, p95 19.30 ms with
rendering/presentation; not a sustained FPS promise. Preview movie, screenshots and
native/headless reports are in docs/sprite-review-v2/.

Human art approval, sustained play and campaign completion remain release gates.
Online scores and uploads remain proposed, not implemented. Local replay validation
cannot establish that a human performed a run. The prior release gates below still apply.

---

# Build status — 0.2.0 local polish, 2026-09-13

A tested local review build. Not yet approved for a public release.

## Delivered in this pass

- F1 keyboard guide, F2 window sizes, F6/Shift+F6 themes, F10 in-game settings,
  F11 fullscreen, M music, Ctrl+S context-aware saving, F5 playtest and keyboard
  studio cursor/painting/tools/rotation. Shortcuts and custom binding hints visible.
- Redesigned home, settings, run HUD, results, records and Credits. Timer, ticks,
  attempts, health and category-specific PBs; Story/Speedrun presets; retry retains
  current rules. New procedural walking/rising/falling/gliding poses.
- Independent original SFX and synthesized ambient music with volume controls.
- Correct multiline/long-word wrapping, bounded titles and modal text, long-dialogue
  pages, single-press dialogue advance and adaptive tutorial control hints.
- Isolated preview/session globals, recoverable malformed records, save-error
  notifications and cleared stale menu callbacks.
- Mohtab Arabiat's credits and first-Linux-game story. Original creator/content/
  license notices retained in Credits; main-screen creator footer removed.
- Bounded local replay validator/re-simulator and per-PB replay files. Proposed
  public stage hub/leaderboard design and release gates in POLISH_PLAN.md.

## Verification

25 automated tests pass, including simulated novice, runner, creator, reduced-effects/
silent player, returning-player content and malformed-input workflows. All 15 original
stages load; original collision sampling, tempo and display-rate independence pass.
Actual stage completion and replay verification pass for a controlled user stage.
These are simulated profiles, not external playtester feedback or full playthroughs.

Native Wayland on a 2560×1600 desktop: four window presets verified at 800×532,
1000×668, 1200×800 and 1440×960 (HiDPI rounding), three fullscreen round trips,
rollback, and settings pause/resume. F2 uses a process/address-scoped Hyprland
adapter because tiled windows ignore ordinary SDL size requests. No desktop config
or global keyboard binding was changed. Other desktops retain SDL-only behavior.

180 scripted native frames: median work 8.45 ms, p95 11.01 ms. Includes rendering/
presentation, not a sustained FPS benchmark or hardware-independent guarantee.
Native window tests used dummy audio; music synthesis/mute was exercised in tests,
not assessed by a human listening session. Gallery and reports: `polish-review/`.

## Remaining release gates

- Mohtab's approval of art/music and human novice/speedrunner playtesting.
- Full completion of all 15 stages, real controller hardware, sustained sessions,
  suspend/resume, multiple monitors and broader platform/package install testing.
- A separately approved community architecture: authentication, moderation, hosting,
  costs, backups, privacy/terms and a hardened server replay worker. No global
  scoreboard, online upload or browsing service is currently connected.
- Hardened RTA/anti-cheat rules if desired; current records are local IGT, and replay
  determinism does not prove human play. Stage ZIP/asset packs remain future work.

Original files and Git history are retained, with a separate rollback backup made
before applying this pass. See POLISH_PLAN.md for sequencing and acceptance gates.

---

## Previous build record (historical)

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
