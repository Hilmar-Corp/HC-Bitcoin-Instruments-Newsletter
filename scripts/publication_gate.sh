#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "HILMARCORP PUBLICATION GATE"
echo "========================================"

python -m pytest -q

python scripts/verify_figure_provenance.py

if [ -f PUBLICATION_MANIFEST.json ]; then
    python scripts/build_publication_manifest.py --verify
fi

if [ "$#" -gt 0 ]; then
    python scripts/lint_publication_claims.py "$@"
fi

echo
echo "========================================"
echo "PUBLICATION GATE: PASS"
echo "========================================"
