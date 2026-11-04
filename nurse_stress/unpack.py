"""Conservatively unpack the official nested dataset archives without a network request."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import shutil
import stat
from zipfile import ZipFile, BadZipFile

MAX_UNCOMPRESSED = 15 * 1024**3
MAX_FILES = 300_000
MAX_ARCHIVES = 2_000


def extract_zip(archive: Path, destination: Path) -> int:
    archive = Path(archive)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    count = 0
    total_bytes = 0
    with ZipFile(archive) as zf:
        entries = zf.infolist()
        if len(entries) > MAX_FILES:
            raise ValueError('Archive exceeds safe member-count limit')
        for info in entries:
            name = info.filename.replace('\\', '/')
            rel = PurePosixPath(name)
            if not rel.parts or rel.is_absolute() or any(part in ('..', '.') for part in rel.parts) or ':' in rel.parts[0]:
                raise ValueError('Unsafe archive path rejected')
            kind = (info.external_attr >> 16) & 0o170000
            if kind == stat.S_IFLNK:
                raise ValueError('Symlink entry rejected')
            total_bytes += info.file_size
            if total_bytes > MAX_UNCOMPRESSED:
                raise ValueError('Archive exceeds uncompressed-size limit')
            path = destination.joinpath(*rel.parts)
            if not path.resolve().is_relative_to(root):
                raise ValueError('Unsafe archive path rejected')
            if info.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, 'r') as src, path.open('xb') as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            count += 1
    return count


def unpack_dataset(archive: Path, destination: Path) -> dict[str, int]:
    """Expand nested .zip packages from the official Dryad download."""
    if not Path(archive).is_file():
        raise FileNotFoundError(archive)
    destination = Path(destination)
    count = extract_zip(archive, destination)
    inspected = {Path(archive).resolve()}
    archives = 1
    # E4 data is packaged in nested recording ZIP files; extract each into its stem folder.
    while True:
        candidates = sorted(p for p in destination.rglob('*.zip') if p.resolve() not in inspected)
        if not candidates:
            break
        for zip_file in candidates:
            if archives >= MAX_ARCHIVES:
                raise ValueError('Too many nested archives')
            inspected.add(zip_file.resolve())
            folder = zip_file.with_suffix('')
            count += extract_zip(zip_file, folder)
            archives += 1
    return {'archives_extracted': archives, 'files_extracted': count}
