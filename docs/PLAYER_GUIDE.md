# Your first game

Choose **Story**, then **Play** on the home screen. Story keeps the dialogue and
starts at normal speed. Follow each stage's goal, collect what you need, and use
levers to turn the room. Hold jump to slow your fall.

You can also use **Choose a stage** to explore any of the 15 original stages.
Completed stages are marked, and **Continue** points you toward the next adventure.
It starts a stage; it does not resume partway through an unfinished run.

## Essential controls

| Action | Keyboard |
| --- | --- |
| Move | Left / Right or A / D |
| Jump; hold to slow your fall | Z, Up or Space |
| Interact / pull a lever | Down, S or E |
| Advance dialogue | Jump or interact |
| Pause / resume | Esc or P |
| Retry the stage | R |
| Open the controls guide | F1 |
| Open settings | F10 |
| Fullscreen | F11, then Enter to keep it or Esc to revert |

Use the mouse for menus, or move the focus with Tab / Shift+Tab and activate with
Enter. Remap the main movement keys in **Customize → Controls**.

Generic controller support is included: use the stick or D-pad to move, button 1
to jump or confirm, button 2 to interact or go back, and buttons 7 or 8 to pause.
Button numbering depends on the controller. Hardware controller testing is still
pending for this release candidate.

## Make it comfortable

Choose a visual theme on the home screen or press **F6** to cycle themes. **Original**
uses the classic artwork; **Refresh**, **Omarchy** and **Cyberpunk** offer new looks.
**Follow Omarchy** follows your desktop palette when available and uses a fallback
palette on other desktops. Characters can be selected separately in Customize.

In **Customize → Display**, choose **Full interface**, **Compact HUD** or **Board
only** under **Play layout**. Compact HUD keeps the goal, time and health visible
above the board. **F9** toggles board-only play; **Esc** opens the pause menu and
**F10** opens settings even when the interface is hidden.

Modern sprites use subtle dark edges by default. Turn on **High-contrast sprites**
in Display settings if you prefer bright outlines. The Gameplay settings also
offer reduced effects and a scene-depth toggle. Audio settings have separate
controls for music and sound effects; music starts off by default.

## Progress and personal bests

Stage completions, personal bests and settings save automatically. **Personal bests**
on the home screen shows your records. **Speedrun** skips dialogue and uses normal
speed for the next stage. Changing presets or tempo applies to your next run;
retrying keeps the current run's rules.

Times use the game's own clock, which excludes pauses and some scripted sequences.
Records are compared within matching stage and rule settings. There are no online
rankings or uploads.

**Ctrl+S** during play saves settings and a practice replay, and retries a failed
completion save. Replays are input recordings, not checkpoints you can resume.

## Build or try a stage

Open **Stage studio** to make a stage, or choose **Remix** beside an existing stage
to start from a copy. Paint with the mouse; right-click erases. Use **F5** to playtest,
**Ctrl+S** to save, and **Ctrl+Shift+S** to export a JSON stage. **Resume draft** in the
stage library restores an autosaved draft.

To try a shared JSON or TXT stage, use **Import file** in the stage library or drop
the file into the game window. See the [stage format](STAGE_FORMAT.md) for details.

## Where your saves live

With the default Linux settings:

| Contents | Location |
| --- | --- |
| Settings | `~/.config/whichwayisup-refresh/settings.json` |
| Records, replays, stages, drafts, exports and themes | `~/.local/share/whichwayisup-refresh/` |
| Log file | `~/.local/state/whichwayisup-refresh/refresh.log` |

These paths follow your XDG directory settings if you have customized them.
To back up your progress and creations, close the game and copy the config and data
folders. Updating the game does not require deleting either folder. The original
game's `~/.wwisup/config.txt` is preserved separately.

Need help getting started? See [installation and troubleshooting](INSTALL.md).
