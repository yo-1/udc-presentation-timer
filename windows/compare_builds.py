"""Compare PyInstaller payloads statically. Never import or execute bundled code.

Use the build venv (PyInstaller and pefile are required for the CLI).
Archive hashes/provenance must be verified before parsing candidate files.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def normalized_index(names):
    result = {}
    for raw in names:
        name = raw.replace('\\', '/')
        if (name.startswith('/') or ':' in name
                or any(part in ('', '.', '..') for part in name.split('/'))
                or name in result):
            raise ValueError(f'unsafe or duplicate archive name: {raw}')
        result[name] = raw
    return result


def compare_zip(left, right):
    """Compare member bytes and metadata separately from ZIP entry order."""
    with zipfile.ZipFile(io.BytesIO(left)) as a, zipfile.ZipFile(io.BytesIO(right)) as b:
        x, y = a.namelist(), b.namelist()
        normalized_index(x)
        normalized_index(y)
        common = set(x) & set(y)
        attributes = ('date_time', 'compress_type', 'create_system', 'external_attr',
                      'internal_attr', 'extra', 'comment', 'flag_bits')
        return {'left_entries': len(x), 'right_entries': len(y),
                'only_left': sorted(set(x) - set(y)),
                'only_right': sorted(set(y) - set(x)),
                'different_member_bytes': sorted(n for n in common if a.read(n) != b.read(n)),
                'different_metadata': sorted(n for n in common if any(
                    getattr(a.getinfo(n), key) != getattr(b.getinfo(n), key)
                    for key in attributes)),
                'entry_order_equal': x == y}


def compare_contents(onefile, onedir, external_root):
    """Reader objects expose only toc and extract; no bundled module is loaded."""
    a, b = normalized_index(onefile.toc), normalized_index(onedir.toc)
    root = Path(external_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('expected real onedir _internal directory')
    files = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('symlinks are not supported')
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    if not files:
        raise ValueError('empty onedir _internal directory')
    different, zip_details = [], {}
    matched = set(a) & set(files)
    for name in sorted(matched):
        left, right = onefile.extract(a[name]), files[name].read_bytes()
        if left != right:
            different.append(name)
            if name == 'base_library.zip':
                zip_details[name] = compare_zip(left, right)
    embedded_common = set(a) & set(b)
    return {
        'external_count': len(files),
        'external_byte_identical': len(matched) - len(different),
        'external_different': different,
        'external_missing_from_onefile': sorted(set(files) - set(a)),
        'unexpected_onefile_entries': sorted(set(a) - set(files) - set(b)),
        'embedded_compared': len(embedded_common),
        'embedded_missing_from_onefile': sorted(set(b) - set(a)),
        'embedded_different': sorted(n for n in embedded_common
                                     if onefile.extract(a[n]) != onedir.extract(b[n])),
        'zip_details': zip_details,
    }


def pe_details(path):
    import pefile
    data = Path(path).read_bytes()
    with pefile.PE(data=data) as pe:
        return {'bytes': len(data), 'sha256': sha256(data),
                'sha1_identification_only': hashlib.sha1(data).hexdigest(),
                'machine': hex(pe.FILE_HEADER.Machine),
                'subsystem': pe.OPTIONAL_HEADER.Subsystem,
                'certificate_table_bytes': pe.OPTIONAL_HEADER.DATA_DIRECTORY[4].Size,
                'imports': [entry.dll.decode('ascii')
                            for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('onefile_exe', type=Path)
    parser.add_argument('onedir_directory', type=Path,
                        help='directory containing PresentationTimer.exe and _internal')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from PyInstaller.archive.readers import CArchiveReader
    other = args.onedir_directory / 'PresentationTimer.exe'
    result = {'schema': 1, 'method': 'static parsing; bundled code never executed',
              'onefile': pe_details(args.onefile_exe), 'onedir': pe_details(other),
              'comparison': compare_contents(CArchiveReader(str(args.onefile_exe)),
                                             CArchiveReader(str(other)),
                                             args.onedir_directory / '_internal')}
    # A difference is a reportable observation, not automatically an unsafe file.
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Comparison saved. This is not an antivirus scan or a safety verdict.')


if __name__ == '__main__':
    main()
