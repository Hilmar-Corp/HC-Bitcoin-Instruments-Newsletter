#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "HILMARCORP RESEARCH ASSURANCE"
echo "========================================"

python -m compileall -q \
    rerun_etf_synced.py \
    normalize_blackrock_download.py \
    final_ibit_nav_decomposition.py \
    scripts \
    tests

python scripts/verify_raw_inputs.py

if [ -f publication/newsletter_11.template.md ]; then
    bash scripts/publication_gate.sh \
        publication/newsletter_11.template.md
else
    bash scripts/publication_gate.sh
fi

echo
echo "RESEARCH_ASSURANCE_PASS"
