#!/usr/bin/env python3
"""Build a deterministic skills-only plugin ZIP from the reviewed source folder."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


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
            raise SystemExit(f"Nested archive requires separate inspection: {rel}")
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
