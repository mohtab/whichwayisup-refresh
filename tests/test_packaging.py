"""Release contents, reproducibility, and independent runtime metadata checks."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'packaging' / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class PackagingTests(unittest.TestCase):
    def test_reproducible_archive_and_extracted_runtime_version(self):
        builder = module('build_release')
        smoke = module('smoke_release')
        version = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']['version']
        with tempfile.TemporaryDirectory(prefix='wwisup-package-test-') as scratch:
            scratch = Path(scratch)
            # Freeze inputs: this also permits running the test while a developer
            # edits the working tree, without confusing changes with nondeterminism.
            snapshot = scratch / 'source'
            for source in builder.release_files():
                target = snapshot / source.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            first = builder.build_release(root=snapshot, output=scratch / 'one', epoch=123)
            second = builder.build_release(root=snapshot, output=scratch / 'two', epoch=123)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(),
                             hashlib.sha256(second.read_bytes()).hexdigest())
            self.assertEqual(int.from_bytes(first.read_bytes()[4:8], 'little'), 123)
            recipe = (first.parent / 'PKGBUILD').read_text()
            self.assertIn('pkgver=' + version, recipe)
            self.assertIn(hashlib.sha256(first.read_bytes()).hexdigest(), recipe)
            self.assertIn('https://github.com/mohtab/whichwayisup-refresh', recipe)
            self.assertNotIn('@VERSION@', recipe)
            with tarfile.open(first) as archive:
                names = archive.getnames()
                self.assertTrue(any(name.endswith('/licenses/original-copyright') for name in names))
                self.assertFalse(any('/dist/' in name or '__pycache__' in name or '/.git/' in name for name in names))
                self.assertFalse(any(name.endswith(('.pyc', '.env')) for name in names))
                videos = [name.split('/', 1)[1] for name in names if name.endswith('.mp4')]
                self.assertEqual(sorted(videos), sorted((
                    'docs/visual-review-v3/visual-review.mp4',
                    'docs/cyberpunk-review-v4/visual-review.mp4')))
                self.assertTrue(all(member.mtime == 123 for member in archive.getmembers()))
            extracted = smoke.extract_source(first, scratch / 'extracted')
            result = subprocess.run([sys.executable, '-B', '-c',
                                     'from refresh import __version__; print(__version__)'],
                                    cwd=extracted, capture_output=True, text=True, check=True,
                                    env=dict(os.environ, PYTHONPATH=''))
            self.assertEqual(result.stdout.strip(), version)

    def test_manifest_rejects_missing_files_and_symlinks(self):
        builder = module('build_release')
        with tempfile.TemporaryDirectory(prefix='wwisup-manifest-test-') as scratch:
            root = Path(scratch)
            with self.assertRaisesRegex(ValueError, 'regular file'):
                list(builder.release_files(root))
            for name in builder.FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            (root / 'credentials.env').write_text('test')
            self.assertNotIn(root / 'credentials.env', list(builder.release_files(root)))
            (root / 'themes').mkdir()
            (root / 'themes/private.toml').symlink_to(root / 'credentials.env')
            with self.assertRaisesRegex(ValueError, 'regular file'):
                list(builder.release_files(root))

    def test_source_extraction_rejects_traversal_and_links(self):
        smoke = module('smoke_release')
        with tempfile.TemporaryDirectory(prefix='wwisup-extraction-test-') as scratch:
            root = Path(scratch)
            for name, kind in (('../outside', tarfile.REGTYPE), ('root/link', tarfile.SYMTYPE)):
                archive = root / 'bad.tar.gz'
                with tarfile.open(archive, 'w:gz') as target:
                    info = tarfile.TarInfo(name)
                    info.type = kind
                    target.addfile(info, io.BytesIO())
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    smoke.extract_source(archive, root / 'output')
            self.assertFalse((root / 'outside').exists())

    def test_manifest_rejects_symlinked_directories(self):
        builder = module('build_release')
        with tempfile.TemporaryDirectory(prefix='wwisup-manifest-test-') as scratch:
            root = Path(scratch) / 'source'
            for name in builder.FILES:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            external = Path(scratch) / 'external'
            external.mkdir()
            (external / 'private.toml').write_text('private data')
            (root / 'themes').symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'regular file'):
                list(builder.release_files(root))

    def test_local_installer_and_launcher_with_special_paths(self):
        with tempfile.TemporaryDirectory(prefix='wwisup-install-test-') as scratch:
            # Exercise both shell quoting and Desktop Entry value/field-code escaping.
            root = Path(scratch) / 'game with spaces $`"\\'
            home = Path(scratch) / 'home 100% complete'
            (root / 'packaging').mkdir(parents=True)
            for name in ('install_local.py', 'whichwayisup-refresh.desktop', 'icon.svg'):
                shutil.copyfile(ROOT / 'packaging' / name, root / 'packaging' / name)
            (root / 'run_game.py').write_text('import json, sys; print(json.dumps(sys.argv[1:]))\n')
            env = dict(os.environ, HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
            subprocess.run([sys.executable, str(root / 'packaging/install_local.py')],
                           cwd=scratch, env=env, capture_output=True, text=True, check=True)
            launcher = home / '.local/bin/whichwayisup-refresh'
            result = subprocess.run([str(launcher), 'argument with spaces', '--version'],
                                    cwd=scratch, env=env, capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), '["argument with spaces", "--version"]')
            desktop = (home / '.local/share/applications/whichwayisup-refresh.desktop').read_text()
            self.assertIn('Exec="' + scratch + '/home 100%% complete/.local/bin/whichwayisup-refresh"\n', desktop)


if __name__ == '__main__':
    unittest.main()
