from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "publication/claims_registry_v1_1.json"

TOKEN = re.compile(
    r"\{\{(metric|fact):([A-Za-z0-9_.-]+)\}\}"
)


def format_value(obj):
    value = obj["value"]
    fmt = obj["format"]

    if fmt == "integer":
        return f"{int(value)}"

    if fmt == "decimal6":
        return f"{float(value):.6f}"

    if fmt == "percent2":
        return f"{100 * float(value):.2f} %"

    if fmt == "percent4":
        return f"{100 * float(value):.4f} %"

    raise ValueError(f"Unknown format: {fmt}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    registry = json.loads(REGISTRY.read_text())

    source = Path(args.input)
    output = Path(args.output)

    text = source.read_text()

    def replace(match):
        kind = match.group(1)
        key = match.group(2)

        collection = (
            registry["metrics"]
            if kind == "metric"
            else registry["facts"]
        )

        if key not in collection:
            raise RuntimeError(
                f"Unknown publication token: {kind}:{key}"
            )

        return format_value(collection[key])

    rendered = TOKEN.sub(replace, text)

    unresolved = TOKEN.findall(rendered)

    if unresolved:
        raise RuntimeError(
            f"Unresolved publication tokens: {unresolved}"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered)

    print("PUBLICATION RENDER: PASS")
    print("Input :", source)
    print("Output:", output)


if __name__ == "__main__":
    main()
