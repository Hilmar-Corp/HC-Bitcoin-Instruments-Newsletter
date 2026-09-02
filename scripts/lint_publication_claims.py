from pathlib import Path
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "publication/claims_registry_v1_1.json"

TOKEN = re.compile(
    r"\{\{(metric|fact):([A-Za-z0-9_.-]+)\}\}"
)

RAW_PERCENT = re.compile(
    r"(?<![\w}])[-+]?\d+(?:[.,]\d+)?\s*%"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text())

    errors = []

    for filename in args.files:
        path = Path(filename)

        if not path.exists():
            errors.append(f"Missing publication file: {path}")
            continue

        text = path.read_text()

        # ----------------------------------------------------
        # Validate controlled tokens
        # ----------------------------------------------------

        for kind, key in TOKEN.findall(text):
            collection = (
                registry["metrics"]
                if kind == "metric"
                else registry["facts"]
            )

            if key not in collection:
                errors.append(
                    f"{path}: unknown token {kind}:{key}"
                )

        # ----------------------------------------------------
        # Forbidden claims
        # ----------------------------------------------------

        lower = text.lower()

        for pattern in registry["forbidden_patterns"]:
            if pattern.lower() in lower:
                errors.append(
                    f"{path}: forbidden claim detected: {pattern}"
                )

        # ----------------------------------------------------
        # No manually typed percentages in source templates.
        # All quantitative publication percentages must come
        # from controlled registry tokens.
        # ----------------------------------------------------

        cleaned = TOKEN.sub("", text)

        for match in RAW_PERCENT.finditer(cleaned):
            errors.append(
                f"{path}: uncontrolled percentage literal: "
                f"{match.group(0)!r}"
            )

    if errors:
        print("=" * 72)
        print("CLAIM LINTER: FAIL")
        print("=" * 72)

        for err in errors:
            print(" -", err)

        sys.exit(1)

    print("CLAIM LINTER: PASS")


if __name__ == "__main__":
    main()
