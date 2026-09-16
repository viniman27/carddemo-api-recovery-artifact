#!/usr/bin/env python3
"""Verify fixture candidate manifest resource sizes and sha256 hashes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(manifest_path: Path) -> list[str]:
    root = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for section in ("resources", "layout_copies"):
        for resource in manifest.get(section, []):
            rel = resource["path"]
            path = root / rel
            if not path.exists():
                errors.append(f"missing {section}: {rel}")
                continue
            actual_bytes = path.stat().st_size
            actual_sha = sha256_file(path)
            if actual_bytes != resource["bytes"]:
                errors.append(f"bytes mismatch {rel}: {actual_bytes} != {resource['bytes']}")
            if actual_sha != resource["sha256"]:
                errors.append(f"sha256 mismatch {rel}: {actual_sha} != {resource['sha256']}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    errors = verify(args.manifest)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, "errors": []}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
