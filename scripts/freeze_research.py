from pathlib import Path
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "research/contract_v1_1.json",
    "data/processed/panel_ibit_btc_SYNCHRONIZED.csv",
    "data/processed/panel_ibit_btc_nav_FINAL.csv",
    "outputs/tables/btc_prices_at_xnas_close_audit.csv",
    "outputs/reports/ETF_SYNC_RESULTS.json",
    "outputs/reports/IBIT_NAV_FINAL_RESULTS.json",
    "rerun_etf_synced.py",
    "normalize_blackrock_download.py",
    "final_ibit_nav_decomposition.py",
    "tests/test_research_v1_1.py",
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

records = []

for rel in FILES:
    path = ROOT / rel

    if not path.exists():
        raise FileNotFoundError(
            f"Cannot freeze missing artifact: {rel}"
        )

    records.append({
        "path": rel,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    })

try:
    git_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()
except Exception:
    git_commit = None

freeze = {
    "research_id": "newsletter-11-bitcoin-direct-etp-futures",
    "protocol_version": "1.1",
    "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "git_commit": git_commit,
    "python": sys.version,
    "platform": platform.platform(),
    "files": records,
}

freeze_path = ROOT / "research/freeze_v1_1.json"

freeze_path.write_text(
    json.dumps(freeze, indent=2)
)

try:
    pip_freeze = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"],
        text=True,
    )
except Exception:
    pip_freeze = "pip freeze unavailable\n"

env_path = ROOT / "research/environment_v1_1.txt"

env_path.write_text(
    "RESEARCH ENVIRONMENT V1.1\n"
    "=========================\n\n"
    f"Python:\n{sys.version}\n\n"
    f"Platform:\n{platform.platform()}\n\n"
    f"Git commit:\n{git_commit}\n\n"
    f"Dependencies:\n{pip_freeze}"
)

print("=" * 72)
print("RESEARCH FREEZE V1.1")
print("=" * 72)

for r in records:
    print(r["sha256"][:16], r["path"])

print()
print("Freeze:", freeze_path)
print("Environment:", env_path)
print("STATUS: FROZEN")
