"""Record original bytes; safe in both hydrated and pointer-only checkouts."""
from pathlib import Path
import json
import subprocess
from archive_files import file_record

ROOT = Path(__file__).resolve().parents[1]


def collect(root=ROOT):
    paths = sorted(p for p in (root / 'collection').rglob('*') if p.is_file() and p.name != '.DS_Store')
    if any(p.is_symlink() for p in paths):
        raise ValueError('Collection files must not be symbolic links.')
    names = [p.relative_to(root).as_posix() for p in paths]
    result = subprocess.run(['git', 'check-attr', '-z', '--stdin', 'filter'], input='\0'.join(names) + '\0', cwd=root, text=True, capture_output=True, check=True)
    fields = result.stdout.split('\0')
    filters = {fields[i]: fields[i + 2] for i in range(0, len(fields) - 1, 3)}
    files = []
    for path, name in zip(paths, names):
        record, pointer = file_record(path)
        lfs = filters[name] == 'lfs'
        if pointer and not lfs:
            raise ValueError(f'LFS pointer without tracking: {name}')
        files.append({'path': path.relative_to(root / 'collection').as_posix(), **record, 'lfs': lfs})
    return files


if __name__ == '__main__':
    manifest_path = ROOT / 'collection-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files'] = collect()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(len(manifest['files']), 'files;', sum(f['size'] for f in manifest['files']), 'bytes')
