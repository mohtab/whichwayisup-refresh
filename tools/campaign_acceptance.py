#!/usr/bin/env python3
"""Verify original campaign completions and write an honest release gate.

Only normal Session.step inputs are used. Simulation state and original stage
content are never modified. Saved files are retained only after independent
runs.verify succeeds against the current original stage fingerprint.
"""
import argparse
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MAX_REPLAY_BYTES = 8 * 1024 * 1024
LAYOUT_NOTES = {
    'w1-l0': 'The first visible lever is high on the right; the crystal starts beyond the left viewport. Watch the floor spikes and blobs.',
    'w1-l5': 'Two repeatable levers sit beside the central partition; three single-use levers and several spiders guard the remaining layout.',
    'w1-l6': 'Four repeatable levers connect the chambers; the crystal begins beyond the left viewport.',
    'w2-l0': 'The cake begins beyond the left viewport beside a spider; three repeatable levers change the visible portion of the board.',
}


def originals():
    from refresh import stages
    for world in stages.WORLD_NAMES:
        listing = ROOT / 'data/levels' / (world + '.txt')
        for index, row in enumerate(listing.read_text().splitlines()):
            ident = row.split()[1]
            path = listing.parent / (ident + '.txt')
            yield stages.Stage(ident, f'{index + 1:02d} / {world}', world, path, stages.parse_legacy(path))


def explore(stage, attempt, frame_limit, settings):
    """Bounded exploratory input policy; failure is not evidence of an impossible stage."""
    from refresh.runtime import Session
    session = Session(stage.engine_path, settings, seed=attempt)
    rng = random.Random(attempt)
    direction = 'LEFT'
    hold_jump = 0
    target = None
    for tick in range(frame_limit):
        player = session.scene['player']
        level = session.scene['level']
        if tick % 36 == 0:
            targets = [o for o in level.objects if 0 < o.x < 520 and -40 < o.y < 520
                       and (o.itemclass in ('key', 'power_crystal', 'cake', 'other_pants')
                            or (o.itemclass == 'lever' and (o.max_activations == -1 or o.activated_times < o.max_activations)))]
            target = min(targets, key=lambda o: abs(o.x-player.x) + abs(o.y-player.y), default=None)
            direction = rng.choice(('LEFT', 'RIGHT', ''))
            if target is not None and rng.random() < .65:
                direction = 'RIGHT' if target.x > player.x else 'LEFT'
        frame = {}
        if direction:
            frame[direction] = True
        # Press/release edges, as produced by physical jump/interact controls.
        if player.on_ground and tick % 3 == 0:
            frame['JUMP'] = True
            hold_jump = rng.randrange(22, 39)
        if hold_jump > 0:
            frame['UP'] = True
            hold_jump -= 1
        if tick % 2 == 0:
            frame['DOWN'] = True
        session.step(frame)
        if session.result is not None:
            break
    return session


def collect(args):
    os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', PYGAME_HIDE_SUPPORT_PROMPT='1')
    import pygame
    from refresh import runs, stages
    from refresh.runtime import Session
    from refresh.storage import DEFAULTS
    settings = dict(DEFAULTS, sound=False, dialogue=False)
    pygame.display.init()
    pygame.font.init()
    pygame.display.set_mode((520, 520))
    args.output.mkdir(parents=True, exist_ok=True)
    replay_output = args.output / 'replays'
    replay_output.mkdir(exist_ok=True)
    candidates = []
    for folder in [replay_output, *args.replay_dir]:
        for path in sorted(folder.glob('*.json')):
            try:
                if path.stat().st_size > MAX_REPLAY_BYTES:
                    raise ValueError('Replay exceeds 8 MiB')
                payload = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(payload, dict):
                    raise ValueError('Replay must be an object')
                candidates.append((path, payload))
            except (ValueError, OSError) as error:
                print(f'Cannot read {path.name}: {error}', file=sys.stderr)
    rows = []
    rejected = []
    for stage in originals():
        fingerprint = stages.fingerprint(stage.document)
        row = dict(id=stage.id, name=stages.display_name(stage), world=stage.world,
                   stage_hash=fingerprint, original_load=False, verified_completion=False,
                   completion_replay=None, attempts=0, human_playtest='pending')
        try:
            session = Session(stage.engine_path, settings)
            for _ in range(48):
                session.step({})
                if session.result is not None:
                    break
            player = session.scene['player']
            row['original_load'] = math.isfinite(player.x) and math.isfinite(player.y)
        except Exception as error:
            row['load_error'] = f'{type(error).__name__}: {error}'
        matches = [(path, payload) for path, payload in candidates if payload.get('stage_hash') == fingerprint]
        # Prefer fewer recorded frames, independent of tempo/category.
        matches.sort(key=lambda pair: len(pair[1].get('inputs', [])) if isinstance(pair[1].get('inputs'), list) else runs.MAX_INPUTS+1)
        for source, payload in matches:
            try:
                result = runs.verify(payload, stage.document, settings)
            except (ValueError, OSError) as error:
                rejected.append(dict(stage=stage.id, source=source.name, reason=str(error)))
                continue
            target = replay_output / (stage.id + '.json')
            target.write_text(json.dumps(payload, separators=(',', ':')) + '\n')
            row.update(verified_completion=True, completion_replay=str(target.relative_to(args.output)),
                       verification=result, provenance='Existing input recording; independently resimulated',
                       source_name=source.name)
            break
        if not row['verified_completion'] and row['original_load']:
            for attempt in range(args.attempts):
                row['attempts'] += 1
                session = explore(stage, attempt, args.frames, settings)
                if session.result == 3:
                    payload = runs.replay(stage.document, session, 1., False, 0, True)
                    result = runs.verify(payload, stage.document, settings)
                    target = replay_output / (stage.id + '.json')
                    target.write_text(json.dumps(payload, separators=(',', ':')) + '\n')
                    row.update(verified_completion=True, completion_replay=str(target.relative_to(args.output)),
                               verification=result, provenance='Deterministic normal-input exploration', seed=attempt)
                    break
        goals = [e['type'].replace('_', ' ') for e in stage.document['entities']
                 if e['type'] in ('key', 'power_crystal', 'cake', 'other_pants')]
        levers = sum(e['type'] == 'lever' for e in stage.document['entities'])
        row['route_note'] = f"Collect {', '.join(goals)}; {levers} available levers."
        if stage.id in LAYOUT_NOTES:
            row['route_note'] += ' ' + LAYOUT_NOTES[stage.id]
        if not row['verified_completion']:
            row['route_note'] += ' Route remains unproven; record a normal playthrough.'
        rows.append(row)
        print(f"{stage.id}: load={'PASS' if row['original_load'] else 'FAIL'}, completion={'VERIFIED' if row['verified_completion'] else 'UNPROVEN'}", flush=True)
    pygame.quit()
    verified = sum(row['verified_completion'] for row in rows)
    report = dict(schema=1, rules=runs.RULES, stage_count=len(rows), verified_completions=verified,
                  completion_gate_passed=verified == len(rows) and all(row['original_load'] for row in rows),
                  human_acceptance_passed=False, exploration=dict(attempts_per_unverified_stage=args.attempts, frames_per_attempt=args.frames),
                  stages=rows, rejected_replays=rejected)
    (args.output / 'matrix.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# Original campaign acceptance', '',
             f"Verified original-content completions: **{verified}/{len(rows)}**. Completion gate: **{'PASS' if report['completion_gate_passed'] else 'INCOMPLETE'}**.", '',
             'Human playtesting remains pending for every stage. A load check or exploratory failure does not prove a stage can or cannot be completed.', '',
             '| Stage | Original load | Completion replay | Human acceptance | Route note |',
             '| --- | --- | --- | --- | --- |']
    for row in rows:
        replay = f"[Verified]({row['completion_replay']})" if row['verified_completion'] else '**Unproven**'
        lines.append(f"| {row['name']} (`{row['id']}`) | {'PASS' if row['original_load'] else 'FAIL'} | {replay} | Pending | {row['route_note']} |")
    lines += ['', '## Reproduce', '', '```sh',
              'python tools/campaign_acceptance.py --require-complete',
              '```', '',
              'This replays retained evidence against the current original documents in isolated temporary saves. A nonzero exit code means at least one original completion remains unproven. To import further recordings, add `--replay-dir /path/to/replays`. To run the bounded normal-input exploration, add `--attempts 16 --frames 3600`.', '',
              'Only recordings that pass the independent replay verifier are written to `replays/`. Hash checks bind them to original documents. Tempo and dialogue categories are preserved; this is a completion gate, not a same-category leaderboard. No debug flips, forced item collection, health changes, coordinate edits, or forced completion results are used.', '',
              '## Remaining human release gates', '',
              '- A novice and an experienced player should complete each campaign and report unclear objectives, difficulty spikes, readability issues and retry friction.',
              '- Test real controllers, suspend/resume, monitor/fullscreen changes, smallest supported window and a sustained session on release packages.',
              '- Review final campaign ending, progression persistence and clean-install/upgrade behavior.', '']
    (args.output / 'README.md').write_text('\n'.join(lines))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-dir', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/campaign-acceptance')
    parser.add_argument('--attempts', type=int, default=0)
    parser.add_argument('--frames', type=int, default=3600)
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.attempts <= 100 or not 1 <= args.frames <= 86400:
        parser.error('Expected 0–100 attempts and 1–86400 frames')
    with tempfile.TemporaryDirectory(prefix='wwisup-campaign-') as scratch:
        os.environ['WWISUP_USER_DIR'] = scratch
        report = collect(args)
    return 1 if args.require_complete and not report['completion_gate_passed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
