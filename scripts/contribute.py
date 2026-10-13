#!/usr/bin/env python3
"""Import a reviewed contribution and prepare an ordinary pull request."""
from pathlib import Path
import argparse
import datetime
import json
import re
import shutil
import subprocess
from archive_files import file_record

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.md', '.mp3', '.m4a', '.wav', '.mp4', '.mov', '.mkv', '.webm', '.docx'}


def validate_metadata(data):
    for key in ('title', 'name'):
        if not isinstance(data.get(key), str) or not data[key].strip() or len(data[key]) > 200:
            raise ValueError(f'{key} is required (at most 200 characters).')
    if data.get('consent') is not True:
        raise ValueError('Permission to publish is required.')
    for key, maximum in [('context', 4000), ('source', 2000), ('date', 10)]:
        if not isinstance(data.get(key, ''), str) or len(data.get(key, '')) > maximum:
            raise ValueError(f'Invalid {key}.')
    if data.get('source') and not re.match(r'^https?://', data['source']):
        raise ValueError('Source must be an HTTP or HTTPS URL.')
    if data.get('date'):
        datetime.date.fromisoformat(data['date'])


def add(source, metadata, slug, root=ROOT):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug) or len(slug) > 100:
        raise ValueError('Use a short lowercase slug, such as family-photo-2024.')
    validate_metadata(metadata)
    if not source.is_file() or source.is_symlink() or source.suffix.lower() not in EXTENSIONS:
        raise ValueError('Choose a regular photo, document, text, audio, or video file.')
    record, pointer = file_record(source)
    if pointer:
        raise ValueError('Download the actual file before importing it.')
    folder = root / 'collection/contributions' / slug
    if folder.exists():
        raise ValueError(f'Contribution already exists: {slug}')
    filename = re.sub(r'[^A-Za-z0-9._-]', '-', source.name).lstrip('.-')
    if not filename or len(filename) > 151:
        raise ValueError('Use a filename of at most 151 characters.')
    public = {key: metadata.get(key, '') for key in ('title', 'name', 'context', 'source', 'date')}
    public.update({'consent': True, 'file': filename, **record})
    (folder / 'files').mkdir(parents=True)
    shutil.copyfile(source, folder / 'files' / filename)
    (folder / 'metadata.json').write_text(json.dumps(public, ensure_ascii=False, indent=2) + '\n')
    return folder


def check(root=ROOT):
    expected = set()
    for path in (root / 'collection/contributions').glob('*/metadata.json'):
        if path.is_symlink() or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', path.parent.name):
            raise ValueError(f'Invalid contribution directory or metadata: {path}')
        data = json.loads(path.read_text())
        validate_metadata(data)
        filename = data.get('file', '')
        if Path(filename).name != filename or not filename or Path(filename).suffix.lower() not in EXTENSIONS:
            raise ValueError(f'Invalid filename in {path}')
        source = path.parent / 'files' / filename
        expected.update([path, source])
        if source.is_symlink():
            raise ValueError(f'Symlinks are not allowed: {source}')
        record, _ = file_record(source)
        if any(record[key] != data.get(key) for key in ('size', 'sha256')):
            raise ValueError(f'Checksum or size mismatch: {source}')
        tracked = subprocess.check_output(['git', 'check-attr', 'filter', '--', str(source)], cwd=root, text=True)
        if not tracked.rstrip().endswith(': lfs'):
            raise ValueError(f'File is not tracked by LFS: {source}')
    actual = {p for p in (root / 'collection/contributions').rglob('*') if p.is_file()}
    if actual != expected:
        raise ValueError('Each contribution must contain only metadata.json and its declared original file.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    new = sub.add_parser('add')
    new.add_argument('file', type=Path)
    new.add_argument('--metadata', required=True, type=Path)
    new.add_argument('--slug', required=True)
    sub.add_parser('check')
    pr = sub.add_parser('pr')
    pr.add_argument('--slug', required=True)
    args = parser.parse_args()
    if args.command == 'add':
        folder = add(args.file, json.loads(args.metadata.read_text()), args.slug)
        print('Added', folder.relative_to(ROOT), '\nReview it, then run: npm run contribute -- pr --slug', args.slug)
    elif args.command == 'check':
        check()
        print('Contribution metadata, checksums, and LFS tracking verified.')
    else:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.slug):
            raise ValueError('Invalid slug.')
        folder = ROOT / 'collection/contributions' / args.slug
        metadata = json.loads((folder / 'metadata.json').read_text())
        check()
        def git(*values):
            return subprocess.run(['git', *values], cwd=ROOT, check=True)
        git('fetch', 'origin', 'main')
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT)
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT)
        if head != base:
            raise ValueError('Start from the latest origin/main before preparing a contribution PR.')
        changes = subprocess.check_output(['git', 'status', '--porcelain', '-z', '--untracked-files=all'], cwd=ROOT).decode().split('\0')
        prefix = f'collection/contributions/{args.slug}/'
        if any(line and (not line[3:].startswith(prefix) or line[:2] != '??') for line in changes):
            raise ValueError('Only the new, untracked contribution folder may be changed when creating its PR.')
        git('switch', '-c', 'contribution/' + args.slug)
        subprocess.run(['python3', 'scripts/collection_manifest.py'], cwd=ROOT, check=True)
        git('add', '--', prefix, 'collection-manifest.json')
        git('commit', '-m', 'Preserve ' + metadata['title'], '-m', 'Add a reviewed contribution with attribution and original-file checksums.')
        git('push', '-u', 'origin', 'HEAD')
        subprocess.run(['gh', 'pr', 'create', '--base', 'main', '--title', 'Preserve ' + metadata['title'], '--body', 'Adds a contribution with public attribution and verified original-file checksums. Please review the files and Vercel preview before merging.'], cwd=ROOT, check=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
