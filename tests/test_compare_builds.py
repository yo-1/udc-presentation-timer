import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location(
    'compare_builds', Path(__file__).resolve().parents[1] / 'windows/compare_builds.py')
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


def make_zip(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, data in entries:
            archive.writestr(zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0)), data)
    return stream.getvalue()


class Reader:
    def __init__(self, entries):
        self.toc = entries

    def extract(self, name):
        return self.toc[name]


class CompareBuildTests(unittest.TestCase):
    def test_zip_order_does_not_imply_changed_member_code(self):
        a = make_zip([('a.pyc', b'first'), ('b.pyc', b'second')])
        b = make_zip([('b.pyc', b'second'), ('a.pyc', b'first')])
        result = compare.compare_zip(a, b)
        self.assertFalse(result['entry_order_equal'])
        self.assertEqual(result['different_member_bytes'], [])
        self.assertEqual(result['different_metadata'], [])
        c = make_zip([('a.pyc', b'altered'), ('b.pyc', b'second')])
        self.assertEqual(compare.compare_zip(a, c)['different_member_bytes'], ['a.pyc'])

    def test_windows_paths_and_missing_extra_modified_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'assets').mkdir()
            (root / 'assets/bell.mp3').write_bytes(b'audio')
            (root / 'python.dll').write_bytes(b'expected')
            (root / 'missing.dll').write_bytes(b'missing')
            one = Reader({'assets\\bell.mp3': b'audio', 'python.dll': b'modified',
                          'extra.dll': b'extra', 'udc_timer': b'code'})
            oned = Reader({'udc_timer': b'code'})
            result = compare.compare_contents(one, oned, root)
            self.assertEqual(result['external_byte_identical'], 1)
            self.assertEqual(result['external_different'], ['python.dll'])
            self.assertEqual(result['external_missing_from_onefile'], ['missing.dll'])
            self.assertEqual(result['unexpected_onefile_entries'], ['extra.dll'])
            self.assertEqual(result['embedded_different'], [])
            one.toc['udc_timer'] = b'altered-code'
            self.assertEqual(compare.compare_contents(one, oned, root)['embedded_different'], ['udc_timer'])

    def test_reject_path_aliases_and_traversal(self):
        for names in [['a/b', 'a\\b'], ['../escape'], ['/absolute'], ['C:\\file']]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                compare.normalized_index(names)


if __name__ == '__main__':
    unittest.main()
