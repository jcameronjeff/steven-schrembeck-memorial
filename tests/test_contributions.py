import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from archive_files import file_record, file_size
from contribute import add, check
from collection_manifest import collect
from contribution_pages import build_contributions
from explore import explore_library


class Contributions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', self.root], check=True)
        (self.root / '.gitattributes').write_text('collection/contributions/**/files/** filter=lfs diff=lfs merge=lfs -text\n')
        self.source = self.root / 'memory.txt'
        self.source.write_text('A memory of Steven.\n')
        self.metadata = {'title': 'A memory', 'name': 'Friend', 'consent': True, 'inviteId': 'must-not-be-published'}

    def test_import_and_pointer_checkout_have_identical_manifest(self):
        folder = add(self.source, self.metadata, 'a-memory', self.root)
        check(self.root)
        metadata = json.loads((folder / 'metadata.json').read_text())
        self.assertNotIn('inviteId', metadata)
        before = collect(self.root)
        original = folder / 'files/memory.txt'
        record, _ = file_record(original)
        original.write_text(f'version https://git-lfs.github.com/spec/v1\noid sha256:{record["sha256"]}\nsize {record["size"]}\n')
        self.assertEqual(file_size(original), record['size'])
        check(self.root)
        self.assertEqual(collect(self.root), before)
        self.assertTrue(next(x for x in before if x['path'].endswith('.txt'))['lfs'])

    def test_tampering_duplicate_paths_and_orphan_files_are_rejected(self):
        folder = add(self.source, self.metadata, 'a-memory', self.root)
        with self.assertRaises(ValueError):
            add(self.source, self.metadata, 'a-memory', self.root)
        with self.assertRaises(ValueError):
            add(self.source, self.metadata, '../escape', self.root)
        (folder / 'extra.txt').write_text('unreviewed')
        with self.assertRaises(ValueError):
            check(self.root)
        (folder / 'extra.txt').unlink()
        (folder / 'files/memory.txt').write_text('changed')
        with self.assertRaises(ValueError):
            check(self.root)

    def test_permission_and_source_validation(self):
        for values in [{'consent': False}, {'source': 'javascript:alert(1)'}, {'date': '2026-99-99'}]:
            with self.assertRaises(ValueError):
                add(self.source, {**self.metadata, **values}, 'a-memory', self.root)

    def test_malformed_pointer_is_not_hashed_as_an_original(self):
        self.source.write_text('version https://git-lfs.github.com/spec/v1\noid sha256:invalid\nsize 10\n')
        with self.assertRaises(ValueError):
            file_record(self.source)

    def test_reviewed_file_appears_in_catalogue_with_escaped_credit(self):
        add(self.source, {**self.metadata, 'name': '<script>test</script>'}, 'a-memory', self.root)
        pages = []
        items = build_contributions(self.root / 'collection', lambda *args: pages.append(args), lambda *args: '|'.join(args))
        self.assertEqual(items[0]['path'], 'contributions/a-memory/files/memory.txt')
        self.assertIn('&lt;script&gt;', pages[0][2])
        self.assertNotIn('<script>', pages[0][2])
        html = explore_library(items, [], lambda path: 'collection-files/' + path)
        self.assertIn('View contribution', html)
        self.assertIn('items/contribution-a-memory.html', html)


if __name__ == '__main__':
    unittest.main()
