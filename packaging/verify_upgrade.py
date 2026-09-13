"""Check profile compatibility using a trusted prior source release in isolation.

Runs both releases with temporary saves, creating a real campaign completion,
user stage and draft in the prior version. This is a save-format compatibility
check, not a clean operating-system package installation test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import tomllib

PROGRAM = r'''
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from refresh.app import App
from refresh.editor import Editor
from refresh import stages
from refresh.storage import user_path
app=App(argparse.Namespace(theme=None,safe_window=True,play=False,stage=None,screen=None,smoke=None,screenshot=None))
mode=sys.argv[2]
payload=json.loads(Path(sys.argv[3]).read_text())
if mode=='seed':
    app.s.update(theme='cyberpunk',sound=False,music=False,key_left='j',key_right='k',dialogue=False,tempo=1.)
    app.start_stage(app.catalog.stages[0])
    for frame in payload['inputs']:
        app.session.step(frame)
    assert app.session.result==3, 'Prior release must actually complete the campaign stage'
    app.finish()
    editor=Editor()
    editor.document['id']='upgrade-user-stage'
    editor.document['title']='Upgrade compatibility stage'
    editor.save()
    editor.document['title']='Unfinished upgrade draft'
    editor.document['entities']=[entity for entity in editor.document['entities'] if entity['type']!='player']
    editor.save(draft=True)
    app.store.save()
else:
    assert app.s['theme']=='cyberpunk' and app.s['key_left']=='j' and app.s['key_right']=='k'
    assert app.s['sound'] is False and app.s['dialogue'] is False and app.s['tempo']==1.
    assert app.completed(app.catalog.stages[0]), 'Existing completion must count toward progression'
    assert app.stage_best(app.catalog.stages[0])==payload['ticks']/24
    assert any(stage.title=='Upgrade compatibility stage' for stage in app.catalog.stages)
    app.resume_draft()
    assert app.screen=='editor' and app.editor.document['title']=='Unfinished upgrade draft'
    assert not any(entity['type']=='player' for entity in app.editor.document['entities'])
    app.draw()
    app.route('home')
    app.start_stage(app.catalog.stages[0])
    for frame in payload['inputs']:
        app.session.step(frame)
    assert app.session.result==3
    app.finish()
    assert not app.new_best, 'An equal replay must preserve the existing PB'
    app.store.save()
print('PROFILE_OK')
'''


def extract_prior(archive, destination):
    roots = set()
    with tarfile.open(archive, 'r:gz') as source:
        members = source.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or not (member.isfile() or member.isdir()):
                raise ValueError(f'Unsafe archive member: {member.name}')
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError('Expected a single prior release root')
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as incoming, target.open('wb') as outgoing:
                    outgoing.write(incoming.read())
    return destination / roots.pop()


def verify_upgrade(prior_archive, root):
    root = Path(root).resolve()
    replay = root / 'docs/campaign-acceptance/replays/w0-l0.json'
    with tempfile.TemporaryDirectory(prefix='wwisup-upgrade-check-') as scratch:
        scratch = Path(scratch)
        old = extract_prior(prior_archive, scratch / 'old')
        profile = scratch / 'profile'
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   WWISUP_USER_DIR=str(profile), XDG_CONFIG_HOME=str(scratch / 'config'),
                   PYTHONDONTWRITEBYTECODE='1', PYGAME_HIDE_SUPPORT_PROMPT='1')
        def run(directory, mode):
            result = subprocess.run([sys.executable, '-B', '-c', PROGRAM, str(directory), mode, str(replay)],
                                    cwd=scratch, env=env, capture_output=True, text=True, timeout=60)
            if result.returncode or 'PROFILE_OK' not in result.stdout:
                raise RuntimeError(f'{mode} failed:\n{result.stdout}\n{result.stderr}')
        run(old, 'seed')
        records = json.loads((profile / 'data/records.json').read_text())
        protected = {}
        for folder in ('data/replays', 'data/stages', 'data/drafts'):
            for path in (profile / folder).glob('*.json'):
                protected[path.relative_to(profile).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        if len(protected) != 3:
            raise ValueError('Expected prior PB replay, user stage, and unfinished draft')
        run(root, 'upgrade')
        if json.loads((profile / 'data/records.json').read_text()) != records:
            raise ValueError('An equal run changed existing PB records')
        for name, checksum in protected.items():
            if hashlib.sha256((profile / name).read_bytes()).hexdigest() != checksum:
                raise ValueError(f'Upgrade changed prior user data: {name}')
        version = lambda directory: tomllib.loads((directory / 'pyproject.toml').read_text())['project']['version']
        return {'from_version': version(old), 'to_version': version(root), 'verified': True,
                'checks': ['settings and custom bindings retained', 'existing PB recognized as completed',
                           'user stage loaded', 'unfinished draft restored without adding a spawn',
                           'equal campaign replay completed after upgrade', 'PB records retained',
                           'prior replay, stage and draft bytes unchanged'],
                'protected_files_sha256': protected, 'headless': True, 'clean_os_install': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--from-archive', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = json.dumps(verify_upgrade(args.from_archive, args.root), indent=2)
    if args.report:
        args.report.write_text(report + '\n')
    print(report)


if __name__ == '__main__':
    main()
