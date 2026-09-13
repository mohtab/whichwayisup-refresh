# Which Way Is Up? — polish and release plan

Owner: Mohtab Arabiat. Review started 13 September 2026.
Development used a separate implementation/review checkout while preserving the
original checkout's Git history and in-progress refresh.

## Direction

A precise, playful gravity platformer: readable at a glance, immediate to retry,
and personal enough to remember. Refresh uses midnight blue, warm ivory, mint and
apricot, with angular framing, bold times and restrained decorative detail.
The room remains the visual center. Hazards have pointed silhouettes; collectibles
have open/bright silhouettes. Character poses communicate run, rise, fall and hurt.
Keep Original as an authentic art option. Physics and collision dimensions remain
stable across themes and display rates. No new engine or infrastructure migration.

## Local polish acceptance

- F1 controls; F2 window size; F6 / Shift+F6 cycle themes; F10 settings;
  F11 fullscreen; Ctrl+S save; Ctrl+Shift+S export stage; F5 editor playtest;
  R restart; Esc/P pause/resume; music and sound controls. All actions discoverable.
- In-run saves explicitly mean a practice replay plus settings, not a resumable
  checkpoint. Studio saves mean the stage. Completion records save automatically.
- Menus support keyboard focus, no mouse required for play/settings/records.
  Keyboard studio cursor supports placing/erasing, tools, rotation, undo and redo.
- Pause/settings freeze the simulation; focus loss clears input. Restart and menu
  navigation cannot accidentally invoke stale controls from the previous screen.
- Separate Story and Speedrun presets. Run metadata captures rules, tempo, dialogue
  setting and pauses. Local personal bests only compare like categories. Display
  exact simulation ticks, IGT and PB; do not claim real-time/global verification.
- New walking cycle and rising/falling poses without collision changes. Reduced
  effects does not disable essential character motion or smooth positioning.
- Independent original SFX and an original procedural ambient music loop.
- Correct multiline wrapping, unsupported font symbols, dynamic bindings,
  dialogue continuation, long titles/authors, modal clipping and credit placement.
- Credits: Mohtab as refresh creator; Olli “Hectigo” Etuaho as original creator;
  GPL-2.0 code/new procedural assets, CC BY 3.0 original content, Vera font notice.
  Story: this was the first game Mohtab tried when starting Linux.

## Community and global leaderboard — proposed next milestone

Prepare the contract and verifier locally; deploying a public service is a separate
architecture/public-exposure decision. No current global board or upload is implied.

A single small API with PostgreSQL and object storage is sufficient initially.
Keep it independent of Atlas Brain/GBrain. A desktop client fetches paginated stage
metadata and explicit downloads, caches previously downloaded stages for offline
play, and never downloads executable code. Authenticated creators upload a bounded
JSON stage, title, creator credit, content license and a completion replay. Uploaded
stages enter pending review; only approved versions appear publicly. Content-addressed
versions keep old replays valid. Report/takedown, per-account quotas, size limits,
rate limits and curator controls are launch requirements, not later polish.

Leaderboard key: stage SHA-256 + engine/rules version + tempo + category. Server
re-simulates bounded input replays in an isolated worker and calculates completion
and ticks itself. Client times are never authoritative. Rank eligible verified runs
by ticks, equal times share rank; one PB per account/category. Modified content,
practice runs and incomplete replays must not silently enter the main board.
IGT is the initial proposed category; an RTA category requires its own rules and
trusted timing design. Re-simulation alone does not prove a human played a run.

Proposed endpoints: GET /v1/stages (cursor, query, sort), GET /v1/stages/:hash,
POST /v1/stages, POST /v1/runs, GET /v1/runs/:id,
GET /v1/leaderboards/:hash (category, cursor), POST /v1/reports.
Responses include review/verification status. Handle timeouts without blocking
SDL, retry only safe requests, require explicit upload/share actions.

Approval packet before implementation of hosting: provider, region, monthly cap,
authentication provider, operator/moderation responsibilities, retention/deletion,
backup/restore, domain and privacy/terms copy. This document proposes those choices;
it does not authorize a public deployment or spending.

## Verification profiles and release gates

1. First-time keyboard player: home → controls → play → dialogue → pause → settings
   → resume; every hint matches actual keys; resize and fullscreen escape safely.
2. Speedrunner: select preset, quick retry, finish twice, compare PB, inspect replay;
   identical input traces produce identical outcomes at 30/60/120/144/240 FPS.
3. Stage creator: keyboard placement, undo/redo, save/export, invalid draft recovery,
   import and actual trigger completion; remix attribution preserved.
4. Reduced-motion / silent player: effects disabled, music/SFX off, clear focus and
   hazards, animation still explains movement; no audio device remains playable.
5. Returning player: all 15 original stages load, old settings/records survive;
   Original art and legacy entrypoint remain available.
6. Adversarial content: malformed fields, Unicode/long text, invalid replay actions,
   oversized inputs, false completion, file write failures and offline startup.

Automated profiles are simulated workflows, not actual external playtesters.
Native window checks and screenshots are separate from headless tests.
Before public release: human playthrough of all 15 stages; controller hardware;
long-session/multi-monitor/suspend tests; blind novice and experienced runner
sessions; approved final sprites/music;
source/license packaging and clean install/upgrade; Mohtab's visual acceptance.


## September 13 review result

The local acceptance items above are implemented in 0.2 and covered by 25 passing
regression tests plus native Wayland review. Local replay verification is implemented;
all remote endpoints above are still a proposal. Current rules ID is `refresh24-v2`
to distinguish the refresh dialogue/session fixes from earlier local records.
New movement poses are code-rendered within unchanged collision bounds. The atlas
in `polish-review/movement-atlas.png` shows the first-pass art for Mohtab's review.
A public launch still requires the release gates listed above.

Technical references checked during implementation:
- Pygame keyboard events and text input: https://www.pygame.org/docs/ref/key.html
- Pygame reserved audio channels: https://www.pygame.org/docs/ref/mixer.html
- Original-content attribution terms: https://creativecommons.org/licenses/by/3.0/
- Hyprland Lua dispatch patterns: https://wiki.hypr.land/Configuring/Basics/Binds/
  and installed `/usr/share/omarchy/bin/omarchy-hyprland-window-pop` /
  `omarchy-capture-webcam-resize`. Hyprland version tested: 0.56.2.

## 0.4.0rc1 implementation

The follow-up polish and release work is recorded in [RELEASE_ACCEPTANCE.md](RELEASE_ACCEPTANCE.md).
This offline release does not depend on the proposed hosted community service.
