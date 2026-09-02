# Reproducibility

## Two distinct levels

This repository distinguishes:

1. exact offline verification of the frozen publication package;
2. methodological reproduction from external providers.

These two concepts are not equivalent.

## Exact offline verification

The committed research package contains frozen processed data,
research contracts, reports, tables, tests and manifests.

Run:

    python -m pytest -q
    python scripts/verify_figure_provenance.py
    python scripts/build_publication_manifest.py --verify

Or run the full assurance layer:

    bash scripts/run_research_assurance.sh

Expected final line:

    RESEARCH_ASSURANCE_PASS

## Local verification of raw inputs

Third-party raw provider caches are not redistributed publicly.

On the research machine where they are present, run:

    python scripts/verify_raw_inputs.py --require-present

The command verifies those files against:

    research/raw_freeze_v1_1.json

## Methodological reproduction

The canonical empirical workflow is implemented primarily in:

    rerun_etf_synced.py
    normalize_blackrock_download.py
    final_ibit_nav_decomposition.py

A new run can query external providers again.

It reproduces the methodology, temporal conventions and calculations.

It is not guaranteed to produce byte-identical upstream data if providers
revise history, metadata, files or interfaces.

## Acceptance criteria

The assurance layer checks, among other controls:

- frozen-artifact SHA-256 integrity;
- 661 synchronized XNAS observations;
- 660 return observations;
- unique and ordered dates;
- strictly positive BTC, IBIT and NAV prices;
- identical certified calendars;
- independent recomputation of IBIT tracking metrics;
- exact NAV log-return decomposition identity;
- frozen premium/discount statistics;
- explicit structural-only futures scope;
- rejection of unvalidated futures proxies;
- publication claim governance;
- figure provenance;
- global publication-manifest integrity;
- zero Pytest failures.

## Limitation

Reproducibility is not an independent audit, regulatory certification,
investment recommendation or validation of future performance.
