"""Original sizes/checksums from hydrated files or strict Git LFS pointers."""
import hashlib
import re

POINTER = re.compile(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n')


def file_record(path):
    with path.open('rb') as source:
        prefix = source.read(1024)
        pointer = POINTER.fullmatch(prefix)
        if pointer:
            return {'size': int(pointer[2]), 'sha256': pointer[1].decode()}, True
        if prefix.startswith(b'version https://git-lfs.github.com/spec/'):
            raise ValueError(f'Malformed LFS pointer: {path}')
        checksum = hashlib.sha256(prefix)
        for block in iter(lambda: source.read(1024 * 1024), b''):
            checksum.update(block)
    return {'size': path.stat().st_size, 'sha256': checksum.hexdigest()}, False


def file_size(path):
    if path.stat().st_size < 1024:
        pointer = POINTER.fullmatch(path.read_bytes())
        if pointer:
            return int(pointer[2])
    return path.stat().st_size
