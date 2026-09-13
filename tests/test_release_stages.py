"""Stage import regressions and immutable campaign presentation names."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from refresh import stages


class LegacyImportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='wwisup-import-')
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'stage.txt'

    def assert_invalid(self, source, line=1):
        self.path.write_text(source, encoding='utf-8')
        with self.assertRaisesRegex(stages.StageError, f'Line {line}:'):
            stages.read(self.path)

    def test_truncated_and_extra_fields(self):
        for line in ('player', 'player 1', 'player 1 2 surplus', 'set',
                     'set brown surplus', 'trigger', 'trigger key',
                     'trigger key 1 surplus', 'spider 1 2', 'lever 1 2',
                     'lever 1 2 1 TRIGGER_FLIP surplus'):
            with self.subTest(line=line):
                self.assert_invalid('\n' + line, 2)

    def test_bad_numeric_values(self):
        for line in ('player nope 2', 'player 1 inf', 'player nan 1',
                     'player 1 20', 'player -1 1', 'lever 1 2 1.5',
                     'lever 1 2 0', 'lever 1 2 101', 'trigger key no',
                     'trigger key 101', 'trigger key ' + '9' * 5000):
            with self.subTest(line=line[:80]):
                self.assert_invalid(line)

    def test_bad_directives_and_actions(self):
        for line in ('set purple', 'spider 1 2 SIDEWAYS',
                     'lever 1 2 1 TRIGGER_EXEC', 'trigger unknown 1',
                     'end trigger'):
            with self.subTest(line=line):
                self.assert_invalid(line)
        self.assert_invalid('trigger key 1\npython print(1)\nend trigger', 2)
        self.assert_invalid('trigger key 1\ntrigger cake 1', 2)
        self.assert_invalid('trigger key 1\nwait', 1)

    def test_board_and_spawn_errors_have_source_locations(self):
        self.assert_invalid('tiles\nshort', 1)
        self.assert_invalid('tiles\n' + '\n'.join([' '*20, 'short'] + [' '*20]*18), 3)
        self.assert_invalid('player 1 2\nplayer 2 3', 2)

    def test_non_utf8_text_is_stage_error(self):
        for suffix in ('.txt', '.TXT', '.json'):
            path = self.path.with_suffix(suffix)
            path.write_bytes(b'\n\xff')
            with self.assertRaisesRegex(stages.StageError, 'Line 2: Stage must be UTF-8'):
                stages.read(path)

    def test_original_documents_and_fingerprints_unchanged(self):
        # Known content keys were in use before parser and presentation changes.
        expected = {
            'w0-l0': '13172b16d819eb82b1690d2cb8dfb0248fedd3498a4553a40c5c1e1bc56102ab',
            'w1-l0': 'c4076a064a23637715a8e8c7778911766a61b1152d03c08ed5fd25903c657e9d',
            'w2-l0': 'da4051e80a1aa1686eaa0f8e88b5f669d13ef4e7b7604d7a17e16c838f013c19',
        }
        for world in stages.WORLD_NAMES:
            listing = stages.ROOT / 'data/levels' / (world + '.txt')
            for row in listing.read_text().splitlines():
                ident = row.split()[1]
                source = listing.parent / (ident + '.txt')
                document = stages.parse_legacy(source)
                if ident in expected:
                    self.assertEqual(stages.fingerprint(document), expected[ident])
                target = Path(self.folder.name) / source.name
                target.write_text(stages.legacy(document))
                reparsed = stages.parse_legacy(target)
                self.assertEqual(reparsed['tiles'], document['tiles'])
                self.assertEqual(reparsed['events'], document['events'])
                self.assertEqual(sorted(reparsed['entities'], key=str), sorted(document['entities'], key=str))

    def test_friendly_name_preserves_identity_and_custom_titles(self):
        source = stages.ROOT / 'data/levels/w0-l0.txt'
        stage = stages.Stage('w0-l0', '01 / Quest For The Keys', stages.WORLD_NAMES[0], source, stages.parse_legacy(source))
        before = deepcopy(stage)
        self.assertEqual(stages.display_name(stage), 'Quest For The Keys · Stage 1')
        self.assertEqual(stage, before)
        stage.original = False
        stage.title = 'Custom adventure'
        self.assertEqual(stages.display_name(stage), 'Custom adventure')


if __name__ == '__main__':
    unittest.main()
