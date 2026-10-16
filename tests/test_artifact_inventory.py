import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'artifact_inventory', Path(__file__).resolve().parents[1] / 'windows/artifact_inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class ArtifactInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'payload'
        self.root.mkdir()
        (self.root / 'timer.exe').write_bytes(b'not an executable; never executed')
        self.manifest = self.base / 'hashes.json'
        self.original = inventory.inventory(self.root)
        self.manifest.write_text(json.dumps(self.original))

    def test_verify_unchanged(self):
        self.assertEqual(inventory.verify(self.root, self.manifest), self.original)

    def test_reject_changed_same_size(self):
        path = self.root / 'timer.exe'
        path.write_bytes(b'x' * path.stat().st_size)
        with self.assertRaises(ValueError):
            inventory.verify(self.root, self.manifest)

    def test_reject_extra_or_missing_file(self):
        extra = self.root / 'unexpected.dll'
        extra.write_bytes(b'extra')
        with self.assertRaises(ValueError):
            inventory.verify(self.root, self.manifest)
        extra.unlink()
        (self.root / 'timer.exe').unlink()
        with self.assertRaises(ValueError):
            inventory.verify(self.root, self.manifest)

    def test_reject_symlink(self):
        try:
            (self.root / 'link').symlink_to(self.root / 'timer.exe')
        except OSError:
            self.skipTest('symlink creation not permitted on this host')
        with self.assertRaises(ValueError):
            inventory.inventory(self.root)

    def test_reject_unsafe_and_duplicate_paths(self):
        for name in ['../escape', '/absolute', 'C:/windows', 'a\\b', 'a/./b', 'a//b']:
            with self.subTest(name=name):
                manifest = json.loads(json.dumps(self.original))
                manifest['files'][0]['path'] = name
                self.manifest.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    inventory.read_manifest(self.manifest)
        manifest = json.loads(json.dumps(self.original))
        duplicate = dict(manifest['files'][0], path='TIMER.EXE')
        manifest['files'].append(duplicate)
        self.manifest.write_text(json.dumps(manifest))
        with self.assertRaises(ValueError):
            inventory.read_manifest(self.manifest)

    def test_compare_reports_changes(self):
        (self.root / 'timer.exe').write_bytes(b'different')
        (self.root / 'extra.dll').write_bytes(b'extra')
        other = self.base / 'other.json'
        other.write_text(json.dumps(inventory.inventory(self.root)))
        result = inventory.compare(self.manifest, other)
        self.assertEqual(result['changed'], ['timer.exe'])
        self.assertEqual(result['only_right'], ['extra.dll'])
        self.assertEqual(result['left_count'], 1)
        self.assertEqual(result['right_count'], 2)


if __name__ == '__main__':
    unittest.main()
