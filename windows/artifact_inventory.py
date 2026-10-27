"""Inventory/verify/compare build files without executing any payload."""
import argparse
import hashlib
import json
from pathlib import Path


def inventory(root):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError("payload must be a real directory")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed: {path}")
        if not path.is_file():
            continue
        sha256 = hashlib.sha256()
        sha1 = hashlib.sha1()  # Legacy identification only; not a security check.
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha256.update(chunk)
                sha1.update(chunk)
        files.append({"path": path.relative_to(root).as_posix(),
                      "size": path.stat().st_size,
                      "sha256": sha256.hexdigest(), "sha1": sha1.hexdigest()})
    if not files:
        raise ValueError("empty payload")
    return {"schema": 1, "files": sorted(files, key=lambda x: x["path"])}


def read_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schema") != 1 or not manifest.get("files"):
        raise ValueError("invalid or empty manifest")
    names = set()
    for entry in manifest["files"]:
        name = entry["path"]
        if (not name or "\\" in name or ":" in name or name.startswith("/")
                or any(part in ("", ".", "..") for part in name.split("/"))
                or name.casefold() in names):
            raise ValueError(f"unsafe or duplicate path: {name}")
        names.add(name.casefold())
        if (not isinstance(entry["size"], int) or entry["size"] < 0
                or any(len(entry[key]) != length
                       or any(c not in "0123456789abcdef" for c in entry[key])
                       for key, length in [("sha256", 64), ("sha1", 40)])):
            raise ValueError(f"invalid size/hash: {name}")
    return manifest


def verify(root, manifest_path):
    expected = read_manifest(manifest_path)
    actual = inventory(root)
    if sorted(expected["files"], key=lambda x: x["path"]) != actual["files"]:
        raise ValueError("payload differs: missing, extra, renamed or modified files")
    return actual


def compare(left, right):
    a = {x["path"]: x for x in read_manifest(left)["files"]}
    b = {x["path"]: x for x in read_manifest(right)["files"]}
    return {"left_count": len(a), "right_count": len(b),
            "left_bytes": sum(x["size"] for x in a.values()),
            "right_bytes": sum(x["size"] for x in b.values()),
            "only_left": sorted(a.keys() - b.keys()),
            "only_right": sorted(b.keys() - a.keys()),
            "changed": sorted(k for k in a.keys() & b.keys()
                              if a[k]["sha256"] != b[k]["sha256"]),
            "identical": sorted(k for k in a.keys() & b.keys()
                                if a[k]["sha256"] == b[k]["sha256"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("create", "verify"):
        sub = commands.add_parser(command)
        sub.add_argument("root", type=Path)
        sub.add_argument("manifest", type=Path)
    sub = commands.add_parser("compare")
    sub.add_argument("left", type=Path)
    sub.add_argument("right", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "create":
            if args.manifest.resolve().is_relative_to(args.root.resolve()):
                raise ValueError("manifest must be outside payload directory")
            args.manifest.write_text(json.dumps(inventory(args.root), indent=2) + "\n",
                                     encoding="utf-8")
            print("Inventory created; this does not establish safety.")
        elif args.command == "verify":
            result = verify(args.root, args.manifest)
            print(f"Verified {len(result['files'])} files; this does not establish safety.")
        else:
            print(json.dumps(compare(args.left, args.right), indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Inventory error: {error}\n")


if __name__ == "__main__":
    main()
