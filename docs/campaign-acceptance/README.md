# Original campaign acceptance

Verified original-content completions: **15/15**. Completion gate: **PASS**.

Human playtesting remains pending for every stage. A load check or exploratory failure does not prove a stage can or cannot be completed.

| Stage | Original load | Completion replay | Human acceptance | Route note |
| --- | --- | --- | --- | --- |
| Quest For The Keys · Stage 1 (`w0-l0`) | PASS | [Verified](replays/w0-l0.json) | Pending | Collect key; 4 available levers. |
| Quest For The Keys · Stage 2 (`w0-l1`) | PASS | [Verified](replays/w0-l1.json) | Pending | Collect key; 3 available levers. |
| Quest For The Keys · Stage 3 (`w0-l2`) | PASS | [Verified](replays/w0-l2.json) | Pending | Collect key; 3 available levers. |
| Quest For The Keys · Stage 4 (`w0-l3`) | PASS | [Verified](replays/w0-l3.json) | Pending | Collect key; 6 available levers. |
| Quest For The Keys · Stage 5 (`w0-l4`) | PASS | [Verified](replays/w0-l4.json) | Pending | Collect key; 3 available levers. |
| Quest For The Keys · Stage 6 (`w0-l5`) | PASS | [Verified](replays/w0-l5.json) | Pending | Collect key; 3 available levers. |
| Quest For The Keys · Stage 7 (`w0-l6`) | PASS | [Verified](replays/w0-l6.json) | Pending | Collect other pants; 3 available levers. |
| The Other Side · Stage 1 (`w1-l0`) | PASS | [Verified](replays/w1-l0.json) | Pending | Collect power crystal; 3 available levers. The first visible lever is high on the right; the crystal starts beyond the left viewport. Watch the floor spikes and blobs. |
| The Other Side · Stage 2 (`w1-l1`) | PASS | [Verified](replays/w1-l1.json) | Pending | Collect power crystal; 4 available levers. |
| The Other Side · Stage 3 (`w1-l2`) | PASS | [Verified](replays/w1-l2.json) | Pending | Collect power crystal; 7 available levers. |
| The Other Side · Stage 4 (`w1-l3`) | PASS | [Verified](replays/w1-l3.json) | Pending | Collect power crystal; 4 available levers. |
| The Other Side · Stage 5 (`w1-l4`) | PASS | [Verified](replays/w1-l4.json) | Pending | Collect power crystal; 10 available levers. |
| The Other Side · Stage 6 (`w1-l5`) | PASS | [Verified](replays/w1-l5.json) | Pending | Collect power crystal; 5 available levers. Two repeatable levers sit beside the central partition; three single-use levers and several spiders guard the remaining layout. |
| The Other Side · Stage 7 (`w1-l6`) | PASS | [Verified](replays/w1-l6.json) | Pending | Collect power crystal; 4 available levers. Four repeatable levers connect the chambers; the crystal begins beyond the left viewport. |
| A Piece of Cake · Stage 1 (`w2-l0`) | PASS | [Verified](replays/w2-l0.json) | Pending | Collect cake; 3 available levers. The cake begins beyond the left viewport beside a spider; three repeatable levers change the visible portion of the board. |

## Reproduce

```sh
python tools/campaign_acceptance.py --require-complete
```

This replays retained evidence against the current original documents in isolated temporary saves. A nonzero exit code means at least one original completion remains unproven. To import further recordings, add `--replay-dir /path/to/replays`. To run the bounded normal-input exploration, add `--attempts 16 --frames 3600`.

Only recordings that pass the independent replay verifier are written to `replays/`. Hash checks bind them to original documents. Tempo and dialogue categories are preserved; this is a completion gate, not a same-category leaderboard. No debug flips, forced item collection, health changes, coordinate edits, or forced completion results are used.

## Remaining human release gates

- A novice and an experienced player should complete each campaign and report unclear objectives, difficulty spikes, readability issues and retry friction.
- Test real controllers, suspend/resume, monitor/fullscreen changes, smallest supported window and a sustained session on release packages.
- Review final campaign ending, progression persistence and clean-install/upgrade behavior.
