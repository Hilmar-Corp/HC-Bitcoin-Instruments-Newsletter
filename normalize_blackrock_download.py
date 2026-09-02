from pathlib import Path
import re

import pandas as pd
from lxml import etree

RAW = Path("data/raw")

SRC = RAW / "ibit_blackrock_official_fund_download.xls"
DST = RAW / "ibit_blackrock_official_fund_download_normalized.xlsx"

if not SRC.exists():
    raise FileNotFoundError(SRC)

blob = SRC.read_bytes()

print("=" * 72)
print("BLACKROCK SPREADSHEETML — ROBUST RECOVERY")
print("=" * 72)

print("Bytes:", len(blob))
print("Magic:", repr(blob[:40]))

# ------------------------------------------------------------
# 1. Decode defensively
# ------------------------------------------------------------

text = blob.decode("utf-8", errors="replace")

# Remove XML-invalid control characters, preserving tab/newline/CR.
text = "".join(
    c for c in text
    if (
        c in "\t\n\r"
        or ord(c) >= 0x20
    )
)

# Repair naked ampersands while preserving valid entities.
text = re.sub(
    r'&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9A-Fa-f]+;)',
    '&amp;',
    text,
)

xml_bytes = text.encode("utf-8")

# ------------------------------------------------------------
# 2. Recover malformed SpreadsheetML with lxml
# ------------------------------------------------------------

parser = etree.XMLParser(
    recover=True,
    huge_tree=True,
    resolve_entities=False,
    no_network=True,
)

root = etree.fromstring(
    xml_bytes,
    parser=parser
)

if root is None:
    raise RuntimeError("lxml could not recover the BlackRock XML.")

print("\nXML RECOVERY: PASS")

if parser.error_log:
    print(f"Recovered XML issues: {len(parser.error_log)}")
    for err in list(parser.error_log)[:10]:
        print(
            f"  line={err.line} "
            f"column={err.column} "
            f"{err.message}"
        )


def lname(tag):
    if not isinstance(tag, str):
        return ""
    return tag.split("}")[-1]


def attr_local(element, target):
    for key, value in element.attrib.items():
        if key.split("}")[-1] == target:
            return value
    return None


# ------------------------------------------------------------
# 3. Extract every SpreadsheetML worksheet
# ------------------------------------------------------------

worksheets = [
    e for e in root.iter()
    if lname(e.tag) == "Worksheet"
]

print("\nWorksheets detected:", len(worksheets))

if not worksheets:
    raise RuntimeError(
        "Recovered XML contains no SpreadsheetML Worksheet."
    )

frames = {}

for ws_idx, ws in enumerate(worksheets, 1):

    sheet_name = (
        attr_local(ws, "Name")
        or f"sheet_{ws_idx:02d}"
    )

    table = next(
        (
            e for e in ws.iter()
            if lname(e.tag) == "Table"
        ),
        None
    )

    if table is None:
        print(f"  {sheet_name}: no table")
        continue

    rows_out = []

    for row in table:

        if lname(row.tag) != "Row":
            continue

        values = []
        current_col = 1

        for cell in row:

            if lname(cell.tag) != "Cell":
                continue

            # SpreadsheetML can skip empty columns via ss:Index.
            idx = attr_local(cell, "Index")

            if idx is not None:
                try:
                    idx = int(idx)

                    while current_col < idx:
                        values.append(None)
                        current_col += 1

                except Exception:
                    pass

            data_node = next(
                (
                    x for x in cell
                    if lname(x.tag) == "Data"
                ),
                None
            )

            if data_node is None:
                value = None
            else:
                # itertext() preserves content even if recovery
                # created nested fragments.
                value = "".join(
                    data_node.itertext()
                ).strip()

                if value == "":
                    value = None

            values.append(value)
            current_col += 1

        rows_out.append(values)

    if not rows_out:
        print(f"  {sheet_name}: 0 rows")
        continue

    max_cols = max(
        len(r) for r in rows_out
    )

    rows_out = [
        r + [None] * (max_cols - len(r))
        for r in rows_out
    ]

    df = pd.DataFrame(rows_out)

    frames[sheet_name] = df

    print(
        f"  {sheet_name}: "
        f"{df.shape[0]} rows × {df.shape[1]} cols"
    )


if not frames:
    raise RuntimeError(
        "Worksheets found but no recoverable tables."
    )

# ------------------------------------------------------------
# 4. Write a genuine XLSX
# ------------------------------------------------------------

used = set()

with pd.ExcelWriter(
    DST,
    engine="openpyxl"
) as writer:

    for i, (name, df) in enumerate(
        frames.items(),
        1
    ):

        safe = re.sub(
            r'[\\/*?:\[\]]',
            "_",
            str(name)
        )[:31]

        if not safe:
            safe = f"sheet_{i:02d}"

        base = safe
        j = 2

        while safe in used:
            suffix = f"_{j}"
            safe = base[:31-len(suffix)] + suffix
            j += 1

        used.add(safe)

        # Keep source rows untouched: the downstream
        # script detects the actual header itself.
        df.to_excel(
            writer,
            sheet_name=safe,
            index=False,
            header=False
        )

print("\n" + "=" * 72)
print("NORMALIZATION: PASS")
print("=" * 72)
print("Output:", DST)
print("Size:", DST.stat().st_size, "bytes")

# Sanity check that openpyxl can reopen it.
check = pd.ExcelFile(
    DST,
    engine="openpyxl"
)

print("XLSX REOPEN: PASS")
print("Sheets:")
for s in check.sheet_names:
    print(" -", s)
