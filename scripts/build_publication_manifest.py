from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "PUBLICATION_MANIFEST.json"

SELF_PATH = "PUBLICATION_MANIFEST.json"


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def tracked_public_files():
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
        )
    except Exception as exc:
        raise RuntimeError(
            "PUBLICATION MANIFEST requires a Git working tree."
        ) from exc

    paths = []

    for item in raw.decode().split("\0"):
        if not item:
            continue

        if item == SELF_PATH:
            continue

        path = ROOT / item

        if not path.is_file():
            raise RuntimeError(
                f"Git-tracked artifact missing from working tree: {item}"
            )

        paths.append(Path(item))

    return sorted(
        paths,
        key=lambda p: p.as_posix()
    )


def snapshot():
    return {
        rel.as_posix(): sha256(ROOT / rel)
        for rel in tracked_public_files()
    }


parser = argparse.ArgumentParser()

parser.add_argument(
    "--verify",
    action="store_true"
)

args = parser.parse_args()

current = snapshot()


if args.verify:

    if not MANIFEST.exists():
        print("PUBLICATION MANIFEST: FAIL — missing")
        sys.exit(1)

    manifest = json.loads(
        MANIFEST.read_text()
    )

    expected = {
        item["path"]: item["sha256"]
        for item in manifest["files"]
    }

    errors = []

    missing = sorted(
        set(expected) - set(current)
    )

    extra = sorted(
        set(current) - set(expected)
    )

    for path in missing:
        errors.append(
            f"missing tracked artifact: {path}"
        )

    for path in extra:
        errors.append(
            f"unregistered tracked artifact: {path}"
        )

    for path in sorted(
        set(current) & set(expected)
    ):
        if current[path] != expected[path]:
            errors.append(
                f"hash drift: {path}"
            )

    if errors:

        print("PUBLICATION MANIFEST: FAIL")

        for error in errors:
            print(" -", error)

        sys.exit(1)

    print(
        "PUBLICATION MANIFEST: PASS —",
        len(current),
        "Git-tracked artifact(s)"
    )

    sys.exit(0)


manifest = {
    "research_id":
        "newsletter-11-bitcoin-direct-etp-futures",

    "protocol_version":
        "1.1",

    "manifest_scope":
        "GIT_TRACKED_PUBLIC_ARTIFACTS",

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
    json.dumps(
        manifest,
        indent=2
    )
)

print(
    "PUBLICATION MANIFEST BUILT —",
    len(current),
    "Git-tracked artifact(s)"
)
