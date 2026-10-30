"""Release boundaries and archive integrity, using small disposable packages."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import package_release as release


class PackageReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='sdd-package-tests-')
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / 'companion'
        self.root.mkdir()
        self.output = self.directory / 'release.zip'
        self.write('README.md', '# Companion\n\n[Example](starter/example.py)\n')
        self.write('starter/example.py', 'print("example")\n')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return path

    def test_includes_dotfiles_and_final_evidence_but_excludes_only_ephemeral_inputs(self):
        included = ['starter/.gitignore', 'starter/.dockerignore',
                    'evidence/run/workspace-final/protected/config.txt',
                    'evidence/run/controller-final/state.json',
                    'evidence/distribution-history/SHA256SUMS-20261028.txt']
        for name in included:
            self.write(name, 'retained\n')
        for folder in ['.git', '.venv', '__pycache__', 'runs', 'test-results',
                       'validation-runs', 'validation-container']:
            self.write(f'{folder}/README.md', '[Ignored broken link](absent.md)\n')
        self.write('.DS_Store', 'local metadata')
        self.write('starter/cached.pyc', 'bytecode')
        result = release.build_release(self.output, root=self.root, refresh_manifest=True)
        with zipfile.ZipFile(self.output) as archive:
            names = archive.namelist()
            expected = ['README.md', 'starter/example.py', 'SHA256SUMS', *included]
            self.assertEqual(names, [f'{release.ARCHIVE_ROOT}/{name}' for name in sorted(expected)])
            self.assertTrue(all(info.date_time == release.FIXED_TIMESTAMP for info in archive.infolist()))
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual((self.root / included[-1]).read_text(), 'retained\n')
        checksum = hashlib.sha256(self.output.read_bytes()).hexdigest()
        self.assertEqual(Path(str(self.output) + '.sha256').read_text(), f'{checksum}  release.zip\n')

    def test_repeated_build_has_identical_bytes(self):
        release.build_release(self.output, root=self.root, refresh_manifest=True)
        second = self.directory / 'second.zip'
        release.build_release(second, root=self.root)
        self.assertEqual(self.output.read_bytes(), second.read_bytes())

    def test_symlink_input_is_rejected_before_manifest_refresh(self):
        link = self.root / 'linked.py'
        link.symlink_to(self.root / 'starter/example.py')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            release.build_release(self.output, root=self.root, refresh_manifest=True)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.root / 'SHA256SUMS').exists())

    def test_existing_archive_or_sidecar_is_preserved(self):
        for suffix in ('', '.sha256'):
            with self.subTest(suffix=suffix):
                retained = Path(str(self.output) + suffix)
                retained.write_bytes(b'previous release')
                with self.assertRaises(FileExistsError):
                    release.build_release(self.output, root=self.root, refresh_manifest=True)
                self.assertEqual(retained.read_bytes(), b'previous release')
                self.assertFalse((self.root / 'SHA256SUMS').exists())
                retained.unlink()

    def test_output_inside_package_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            release.build_release(self.root / 'release.zip', root=self.root, refresh_manifest=True)
        self.assertFalse((self.root / 'SHA256SUMS').exists())

    def test_missing_manifest_is_not_implicitly_created(self):
        with self.assertRaisesRegex(ValueError, 'verification failed'):
            release.build_release(self.output, root=self.root)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.root / 'SHA256SUMS').exists())

    def test_changed_bytes_fail_without_refresh(self):
        release.write_manifest(self.root)
        manifest = (self.root / 'SHA256SUMS').read_bytes()
        self.write('starter/example.py', 'print("changed")\n')
        with self.assertRaisesRegex(ValueError, 'hash_mismatch'):
            release.build_release(self.output, root=self.root)
        self.assertFalse(self.output.exists())
        self.assertEqual((self.root / 'SHA256SUMS').read_bytes(), manifest)

    def test_unlisted_deliverable_is_rejected(self):
        release.write_manifest(self.root)
        self.write('new-evidence.json', '{}\n')
        with self.assertRaisesRegex(ValueError, 'Manifest coverage'):
            release.build_release(self.output, root=self.root)
        self.assertFalse(self.output.exists())

    def test_broken_link_prevents_archive_even_with_refreshed_manifest(self):
        self.write('README.md', '[Missing evidence](absent.json)\n')
        with self.assertRaisesRegex(ValueError, 'missing_target'):
            release.build_release(self.output, root=self.root, refresh_manifest=True)
        self.assertFalse(self.output.exists())

    def test_archive_byte_corruption_is_rejected(self):
        snapshot = {'README.md': (b'expected bytes', 0o644)}
        with zipfile.ZipFile(self.output, 'w') as archive:
            archive.writestr(f'{release.ARCHIVE_ROOT}/README.md', b'corrupt bytes')
        with self.assertRaisesRegex(ValueError, 'Archive bytes differ'):
            release.verify_archive(self.output, snapshot)

    def test_source_mutation_during_packaging_leaves_no_release(self):
        original_verify = release.verify_archive

        def mutate_after_archive_check(path, snapshot):
            original_verify(path, snapshot)
            self.write('starter/example.py', 'print("edited during release")\n')

        with patch.object(release, 'verify_archive', side_effect=mutate_after_archive_check):
            with self.assertRaisesRegex(ValueError, 'changed while packaging'):
                release.build_release(self.output, root=self.root, refresh_manifest=True)
        self.assertFalse(self.output.exists())
        self.assertFalse(Path(str(self.output) + '.sha256').exists())


if __name__ == '__main__':
    unittest.main()
