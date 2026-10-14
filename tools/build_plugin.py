#!/usr/bin/env python3
"""Build a deterministic skills-only plugin ZIP from the reviewed source folder."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


def inspect_source_archive(path, root):
    """Allow only frozen source ZIPs whose contents have been checked separately."""
    skill = root / "skills" / "eskd-electrical-cabinets"
    source_dir = skill / "assets" / "x2002-reference" / "sources"
    if path.parent != source_dir or path.suffix != ".zip":
        raise SystemExit(f"Archive requires separate inspection: {path.relative_to(root)}")
    reference = skill / "assets/x2002-reference"
    manifest = json.loads((reference / "file-manifest.json").read_text(encoding="utf-8"))
    expected = {row["path"]: row["sha256"] for row in manifest["files"]}
    rel = path.relative_to(reference).as_posix()
    if expected.get(rel) != hashlib.sha256(path.read_bytes()).hexdigest():
        raise SystemExit(f"Archive is missing from manifest or changed: {rel}")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise SystemExit(f"Corrupt source archive: {rel}")
        for member in archive.infolist():
            name = member.filename.replace("\\", "/")
            parts = PurePosixPath(name)
            mode = member.external_attr >> 16
            if (parts.is_absolute() or ".." in parts.parts or ":" in name
                    or stat.S_ISLNK(mode) or member.flag_bits & 1):
                raise SystemExit(f"Unsafe or encrypted source entry: {rel}: {name}")
            if any(p in {".git", "__pycache__", ".venv"} for p in parts.parts):
                raise SystemExit(f"History/cache in source archive: {rel}: {name}")
            if parts.suffix.lower() in {".zip", ".7z", ".pyc", ".pyo"}:
                raise SystemExit(f"Nested archive/cache requires inspection: {rel}: {name}")


def main():
    repo = Path(__file__).resolve().parents[1]
    root = repo / "plugins" / "eskd-electrical-cabinets"
    manifest = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=repo / "dist")
    args = parser.parse_args()
    required = ["plugin.json", "requirements.txt",
                "skills/eskd-electrical-cabinets/SKILL.md"]
    for name in required:
        if not (root / name).is_file():
            raise SystemExit(f"Missing required file: {name}")
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in {".git", "__pycache__", ".venv"} for part in rel.parts):
            continue
        if path.is_symlink():
            raise SystemExit(f"Refusing symlink: {rel}")
        if not path.is_file() or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.suffix in {".zip", ".7z"}:
            inspect_source_archive(path, root)
        files.append(path)
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{manifest['name']}-{manifest['version']}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(root).as_posix(), (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(target) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"ZIP integrity error: {bad}")
    print(json.dumps({"archive": str(target), "files": len(files),
                      "bytes": target.stat().st_size,
                      "sha256": hashlib.sha256(target.read_bytes()).hexdigest()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
