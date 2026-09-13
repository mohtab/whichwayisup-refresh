"""Smoke-test a source archive or extracted installed game without touching saves.

This verifies startup, bundled campaigns, themes, and menu rendering. It does
not certify campaign completion or physical display/controller behavior.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import tomllib


def extract_source(archive, destination):
    """Extract only regular files under a single archive root."""
    destination = Path(destination)
    roots = set()
    with tarfile.open(archive, 'r:gz') as source:
        members = source.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or len(path.parts) < 2 or not member.isfile():
                raise ValueError(f'Unsafe source archive member: {member.name}')
            roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError('Expected exactly one source archive root')
        for member in members:
            target = destination / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.extractfile(member) as incoming, target.open('wb') as outgoing:
                outgoing.write(incoming.read())
    return destination / roots.pop()


def smoke(root):
    root = Path(root).resolve()
    version = tomllib.loads((root / 'pyproject.toml').read_text())['project']['version']
    required = ('run_game.py', 'LICENSE', 'CREDITS.md', 'licenses/original-copyright',
                'licenses/omarchy-MIT.txt', 'data/misc/Vera.ttf')
    for name in required:
        if not (root / name).is_file():
            raise ValueError(f'Missing packaged file: {name}')
    cases = [('screen-' + screen, ['--screen', screen])
             for screen in ('home', 'settings', 'stages', 'editor', 'credits')]
    cases += [('theme-' + theme.stem, ['--play', '--theme', theme.stem])
              for theme in sorted((root / 'themes').glob('*.toml'))]
    stage_ids = [f'w{world}-l{level}' for world, count in ((0, 7), (1, 7), (2, 1)) for level in range(count)]
    cases += [(stage, ['--play', '--stage', stage]) for stage in stage_ids]
    with tempfile.TemporaryDirectory(prefix='wwisup-release-smoke-') as scratch:
        env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                   WWISUP_USER_DIR=str(Path(scratch) / 'saves'),
                   XDG_CONFIG_HOME=str(Path(scratch) / 'config'),
                   PYGAME_HIDE_SUPPORT_PROMPT='1', PYTHONDONTWRITEBYTECODE='1')
        # Start from outside the checkout to catch implicit working-directory dependencies.
        result = subprocess.run([sys.executable, '-B', '-c',
                                 'import sys; sys.path.insert(0, sys.argv[1]); '
                                 'import json; from refresh import __version__; '
                                 'from refresh.stages import Catalog; catalog = Catalog(); '
                                 'print(json.dumps({"version": __version__, '
                                 '"stages": [stage.id for stage in catalog.stages], "errors": catalog.errors}))', str(root)],
                                cwd=scratch, env=env, capture_output=True, text=True, check=True)
        catalog = json.loads(result.stdout)
        if catalog['version'] != version:
            raise ValueError('Runtime and release metadata versions differ')
        if catalog['errors'] or set(stage_ids) != set(catalog['stages']):
            raise ValueError('Packaged campaign catalog is incomplete or invalid')
        passed = []
        for label, arguments in cases:
            result = subprocess.run([sys.executable, '-B', str(root / 'run_game.py'),
                                     '--safe-window', '--smoke', '0.05', *arguments],
                                    cwd=scratch, env=env, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise RuntimeError(f'{label} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}')
            passed.append(label)
    return {'version': version, 'cases_passed': len(passed), 'cases': passed, 'headless': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--root', type=Path, help='Checkout or extracted usr/share/whichwayisup-refresh')
    inputs.add_argument('--archive', type=Path, help='Release source .tar.gz')
    parser.add_argument('--report', type=Path, help='Write JSON verification report')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='wwisup-release-extract-') as scratch:
        root = extract_source(args.archive, scratch) if args.archive else args.root
        report = smoke(root)
    rendered = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(rendered + '\n')
    print(rendered)


if __name__ == '__main__':
    main()
