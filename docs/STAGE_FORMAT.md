# Stage format v1

A stage is a UTF-8 JSON object, at most 128 KiB. Importing never executes scripts.
The canonical validator is `refresh/stages.py`; it is also used by the studio and
command-line importer. Legacy `.txt` stages can be converted with the same importer.

Required fields:

| Field | Meaning |
| --- | --- |
| `schema` | Exactly `1` |
| `id` | 1–60 ASCII letters, digits, underscores or hyphens |
| `title`, `author`, `license` | Nonempty strings of at most 100 characters, no control characters |
| `tileset` | `brown`, `green` or `grey`, for the Original presentation |
| `tiles` | Exactly 20 strings, each exactly 20 characters: W wall, S spikes, B bars, space or dot empty |
| `entities` | 1–128 entities, exactly one player |
| `events` | Up to 64 built-in event groups |

Every entity has `type`, `x`, and `y`. Coordinates are finite numbers in `[0, 20)`;
cell centers are usually `.5`. Types: player, key, lever, spider, blob, other_pants,
power_crystal, cake. Spiders also have `attached`: LEFT, RIGHT, UP or DOWN. Levers
have `uses`: -1 for unlimited, or 1–100. Levers rotate the board.

An event group contains `trigger`, `times`, and an array of `actions` (max 100).
Triggers: level_begin, flipped, key, other_pants, power_crystal, cake.
Repeat count is -1 (unlimited) or 0–100. Actions are built-in strings:

- `dialogue Your message here` (the whole action is at most 500 characters)
- `change_level` (complete this stage)
- `wait`
- `player orientation LEFT` (or RIGHT, UP, DOWN)
- `player animation default` (other accepted legacy values are listed in the validator)

The original game only partially interprets the animation action. Do not rely on it
for arbitrary cutscenes. For a standalone creator stage, a goal-item trigger containing
`change_level` is the normal way to finish. Validation establishes structural safety,
not solvability; playtest every orientation and route to the goal.

Generate a complete editable example:

```sh
python -c 'from refresh.stages import blank; from refresh.storage import atomic_json; atomic_json("my-stage.json", blank())'
```

The studio's initial viewport outlines the bottom-right 13 × 13 part of the board.
Rotations expose different parts of the same board. Larger window sizes do not reveal
additional tiles. Keep this constraint in mind when designing routes.

Import filenames are generated from the validated ID and a content hash. Imported
stages and derived legacy cache files never overwrite the built-in content. Zip files,
external asset dependencies and arbitrary code are intentionally unsupported in v1.
