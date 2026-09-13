"""Build a reproducible source archive from an explicit distribution manifest."""
import argparse
import gzip
import hashlib
import os
from pathlib import Path
import re
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
# Only these files and patterns belong in a release. Local captures, caches,
# credentials, editor state, and previous artifacts are never swept into it.
FILES = (
    'run_game.py', 'pyproject.toml', 'README.md', 'README.txt', 'CONTRIBUTING.md',
    'CREDITS.md', 'CHANGELOG.md', 'LICENSE', 'changelog.txt',
    'licenses/omarchy-MIT.txt', 'licenses/original-copyright',
    'packaging/PKGBUILD.in', 'packaging/build_release.py',
    'packaging/install_local.py', 'packaging/smoke_release.py', 'packaging/verify_upgrade.py',
    'packaging/icon.svg', 'packaging/whichwayisup-refresh.desktop',
    'docs/visual-review-v3/visual-review.mp4',
    'docs/cyberpunk-review-v4/visual-review.mp4',
)
PATTERNS = (
    'refresh/*.py', 'lib/*.py', 'themes/*.toml', 'tests/test_*.py', 'tools/*.py',
    'data/levels/*.txt', 'data/misc/*.ttf', 'data/pictures/*.png',
    'data/pictures/*.txt', 'data/sounds/*.ogg', 'data/sounds/*.txt',
    'assets/sprites/*.png', 'assets/sprites/*.md',
    'assets/branding/*.png', 'assets/branding/*.md', 'docs/*.md',
    'docs/campaign-acceptance/*.md', 'docs/campaign-acceptance/*.json',
    'docs/campaign-acceptance/replays/*.json',
    'docs/release-review/*.json', 'docs/release-review/*.png', 'docs/release-review/tests.txt',
    '.github/workflows/*.yml', '.github/ISSUE_TEMPLATE/*.yml', '.github/*.md',
)


def release_files(root=ROOT):
    """Fail on missing required inputs and symlinks escaping the manifest."""
    root = Path(root).resolve()
    files = {root / name for name in FILES}
    for pattern in PATTERNS:
        files.update(root.glob(pattern))
    for path in sorted(files):
        if (not path.is_file() or path.is_symlink()
                or any(parent.is_symlink() for parent in path.parents if parent != root and root in parent.parents)):
            raise ValueError(f'Release input must be a regular file: {path}')
        yield path


def build_release(root=ROOT, output=None, epoch=None):
    root = Path(root).resolve()
    output = Path(output) if output is not None else root / 'dist'
    metadata = tomllib.loads((root / 'pyproject.toml').read_text())['project']
    version = metadata['version']
    if not re.fullmatch(r'[0-9][A-Za-z0-9.+]*', version):
        raise ValueError(f'Version is not safe for an Arch package: {version!r}')
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', '0')) if epoch is None else epoch
    if epoch < 0:
        raise ValueError('SOURCE_DATE_EPOCH must be nonnegative')
    name = metadata['name'] + '-' + version
    files = list(release_files(root))
    output.mkdir(parents=True, exist_ok=True)
    archive = output / (name + '.tar.gz')
    # Normalize the gzip header as well as tar metadata.
    with archive.open('wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=epoch) as compressed:
            with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as tar:
                for path in files:
                    info = tar.gettarinfo(str(path), arcname=f'{name}/{path.relative_to(root).as_posix()}')
                    info.uid = info.gid = 0
                    info.uname = info.gname = 'root'
                    info.mtime = epoch
                    info.mode = 0o644
                    info.pax_headers = {}
                    with path.open('rb') as source:
                        tar.addfile(info, source)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    recipe = (root / 'packaging/PKGBUILD.in').read_text()
    values = {'VERSION': version, 'HOMEPAGE': metadata['urls']['Homepage'], 'SHA256': checksum}
    for token, value in values.items():
        recipe = recipe.replace(f'@{token}@', value)
    (output / 'PKGBUILD').write_text(recipe)
    (output / 'SHA256SUMS').write_text(f'{checksum}  {archive.name}\n')
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Destination directory (default: dist/)')
    args = parser.parse_args()
    archive = build_release(output=args.output)
    print(archive)
    print(f'Verify: python packaging/smoke_release.py --archive {archive}')
    print(f'Build Arch package: cd {archive.parent} && makepkg')


if __name__ == '__main__':
    main()
