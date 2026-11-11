import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reality_book as book
import reality_book_build as builder


def check_text(text):
    """Errors for a one-off manuscript checked against the real transcripts."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / '99-test.txt'
        path.write_text('# Test\nsource: trailer\n\n' + text + '\n', encoding='utf-8')
        return book.run_check([path], quiet=True)[2]


class Fidelity(unittest.TestCase):
    def test_every_passage_matches_its_transcript(self):
        chapters, _sources, errors, _warnings, config = book.run_check(None, quiet=True)
        self.assertEqual(errors, [])
        self.assertEqual([c.slug for c in chapters], [slug for part in config['parts'] for slug in part['chapters']])
        self.assertTrue(all(passage.kept for chapter in chapters for passage in chapter.passages))

    def test_cutting_is_accepted(self):
        self.assertEqual(check_text('@B0006 Steven\nNothing is impossible, you are not going to die, and everything loves you.'), [])

    def test_added_word_is_rejected(self):
        errors = check_text('@B0006 Steven\nNothing is truly impossible.')
        self.assertTrue(any('"truly" is not in the source' in error for error in errors), errors)

    def test_replaced_word_is_rejected(self):
        errors = check_text('@B0006 Steven\nYou are not going to perish.')
        self.assertTrue(any('"perish"' in error for error in errors), errors)

    def test_reordered_words_are_rejected(self):
        self.assertTrue(check_text('@B0006 Steven\nEverything loves you, and nothing is impossible.'))

    def test_words_cannot_be_given_to_another_speaker(self):
        errors = check_text('@B0005 Steven\nI\'ll be holding space for this incredible exploration.')
        self.assertTrue(any('spoken by Joshua' in error for error in errors), errors)

    def test_passages_cannot_reuse_or_reorder_the_recording(self):
        errors = check_text('@B0006 Steven\nNothing is impossible.\n\n@B0003 Steven\nSo in 2022, a series of UFO sightings.')
        self.assertTrue(any('Keep recording order' in error for error in errors), errors)

    def test_transcript_misspelling_of_his_name_is_not_printed(self):
        errors = check_text('@B0001 Steven\nMy name is Stephen Schrembeck.')
        self.assertTrue(any('write "steven"' in error for error in errors), errors)


class Edition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edition = builder.Edition()
        cls.folder = book.BOOK

    def test_reading_edition_is_current(self):
        self.assertEqual((self.folder / 'reading.html').read_text(encoding='utf-8'), builder.standalone(self.edition),
                         'Run python3 scripts/reality_book.py build')

    def test_epub_is_current_and_well_formed(self):
        built = zipfile.ZipFile(io.BytesIO(builder.epub_bytes(self.edition)))
        saved = zipfile.ZipFile(self.folder / builder.EPUB_NAME)
        self.assertEqual(saved.namelist()[0], 'mimetype')
        self.assertEqual(saved.getinfo('mimetype').compress_type, zipfile.ZIP_STORED)
        self.assertEqual(saved.namelist(), built.namelist())
        for name in saved.namelist():
            self.assertEqual(saved.read(name), built.read(name), f'{name}: run python3 scripts/reality_book.py build')

    def test_passage_map_and_validation_are_current(self):
        passages, validation = builder.records(self.edition)
        saved = json.loads((self.folder / 'passage-map.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['passages'], passages)
        record = json.loads((self.folder / 'validation.json').read_text(encoding='utf-8'))
        record.pop('epub_sha256')
        self.assertEqual(record, json.loads(json.dumps(validation)))
        self.assertEqual(record['added_body_words'], 0)

    def test_every_internal_link_resolves(self):
        page = builder.standalone(self.edition)
        import re
        anchors = set(re.findall(r'id="([^"]+)"', page))
        for target in re.findall(r'href="#([^"]+)"', page):
            self.assertIn(target, anchors)


if __name__ == '__main__':
    unittest.main()
