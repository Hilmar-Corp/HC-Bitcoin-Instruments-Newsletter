from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PUBLICATION_MANIFEST.json"

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "reproduction",
}

EXCLUDED_FILES = {
    "PUBLICATION_MANIFEST.json",
    "finish_institutional_experiment.py",
    "finish_futures_vendor.py",
}

EXCLUDED_PREFIXES = (
    "data/raw/",
    "publication/rendered/",
    "newsletter-11-bitcoin-direct-etp-futures/",
    "newsletter-11-bitcoin-direct-etp-futures/",
)


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def public_files():
    out = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(ROOT)
        rels = rel.as_posix()

        if rel.name in EXCLUDED_FILES:
            continue

        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue

        if any(rels.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue

        out.append(rel)

    return sorted(out, key=lambda p: p.as_posix())


parser = argparse.ArgumentParser()
parser.add_argument("--verify", action="store_true")
args = parser.parse_args()

current = {
    rel.as_posix(): sha256(ROOT / rel)
    for rel in public_files()
}

if args.verify:
    if not MANIFEST.exists():
        print("PUBLICATION MANIFEST: FAIL — missing")
        sys.exit(1)

    manifest = json.loads(MANIFEST.read_text())

    expected = {
        item["path"]: item["sha256"]
        for item in manifest["files"]
    }

    errors = []

    if set(current) != set(expected):
        missing = sorted(set(expected) - set(current))
        extra = sorted(set(current) - set(expected))

        for x in missing:
            errors.append(f"missing public artifact: {x}")

        for x in extra:
            errors.append(f"unregistered public artifact: {x}")

    for path in sorted(set(current) & set(expected)):
        if current[path] != expected[path]:
            errors.append(f"hash drift: {path}")

    if errors:
        print("PUBLICATION MANIFEST: FAIL")
        for e in errors:
            print(" -", e)
        sys.exit(1)

    print(
        "PUBLICATION MANIFEST: PASS —",
        len(current),
        "artifact(s)"
    )
    sys.exit(0)


manifest = {
    "research_id":
        "newsletter-11-bitcoin-direct-etp-futures",
    "protocol_version":
        "1.1",
    "generated_at_utc":
        datetime.now(timezone.utc).isoformat(),
    "hash_algorithm":
        "SHA-256",
    "raw_provider_caches_included":
        False,
    "files": [
        {
            "path": path,
            "sha256": digest
        }
        for path, digest in current.items()
    ]
}

MANIFEST.write_text(
    json.dumps(manifest, indent=2)
)

print(
    "PUBLICATION MANIFEST BUILT —",
    len(current),
    "artifact(s)"
)
