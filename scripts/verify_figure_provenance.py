from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT /
    "publication/figures/manifest_v1_1.json"
)

RESEARCH_FREEZE = (
    ROOT /
    "research/freeze_v1_1.json"
)

RAW_FREEZE = (
    ROOT /
    "research/raw_freeze_v1_1.json"
)


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


if not MANIFEST.exists():
    print("FIGURE PROVENANCE: PASS — no registered figures yet")
    sys.exit(0)

manifest = json.loads(MANIFEST.read_text())

errors = []

for fig in manifest["figures"]:

    checks = [
        (
            fig["figure"]["path"],
            fig["figure"]["sha256"]
        ),
        (
            fig["generator"]["path"],
            fig["generator"]["sha256"]
        )
    ]

    checks += [
        (x["path"], x["sha256"])
        for x in fig["inputs"]
    ]

    for rel, expected in checks:
        path = ROOT / rel

        if not path.exists():
            errors.append(
                f"{fig['id']}: missing {rel}"
            )
            continue

        if sha256(path) != expected:
            errors.append(
                f"{fig['id']}: hash drift {rel}"
            )

    if (
        fig["research_freeze_sha256"]
        != sha256(RESEARCH_FREEZE)
    ):
        errors.append(
            f"{fig['id']}: research freeze drift"
        )

    if (
        fig["raw_freeze_sha256"]
        != sha256(RAW_FREEZE)
    ):
        errors.append(
            f"{fig['id']}: raw freeze drift"
        )

if errors:
    print("FIGURE PROVENANCE: FAIL")

    for error in errors:
        print(" -", error)

    sys.exit(1)

print(
    "FIGURE PROVENANCE: PASS —",
    len(manifest["figures"]),
    "registered figure(s)"
)
