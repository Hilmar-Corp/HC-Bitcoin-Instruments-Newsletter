# Research assurance

## Objective

The assurance layer verifies traceability, numerical integrity,
temporal alignment, publication contracts and artifact integrity for:

**Le même Bitcoin, trois produits différents**

It does not certify future investment performance, constitute an
investment recommendation or represent independent external validation.

## Evidence levels

| Level | Meaning |
|---|---|
| `artifact-verified` | Frozen files match their recorded SHA-256 fingerprints |
| `raw-provenance-verified` | Locally available provider inputs can be checked against frozen hashes |
| `data-contract-verified` | Dates, uniqueness, sample size, positivity and completeness satisfy declared constraints |
| `temporal-alignment-verified` | Bitcoin observations correspond to the exact XNAS close boundary |
| `regression-verified` | Correlation, beta, R², tracking error and tracking difference are independently recomputed |
| `nav-decomposition-verified` | Market/BTC, NAV/BTC and market/NAV log-return identity is numerically verified |
| `scope-governance-verified` | Rejected futures proxies remain excluded from empirical publication claims |
| `claim-contract-verified` | Publication metrics originate from the controlled claims registry |
| `figure-provenance-verified` | Registered figures are linked to generator code and inputs by SHA-256 |
| `code-reproducible` | The documented methodology can be re-executed |

## Automated controls

The current test and assurance stack verifies:

- research-freeze integrity;
- synchronized sample size;
- unique and ordered dates;
- positive market values;
- BTC/IBIT/NAV calendar consistency;
- independent recomputation of tracking statistics;
- exact log-return decomposition;
- premium/discount statistics;
- futures scope marked `EXCLUDED_BY_DESIGN`;
- rejected continuous and incomplete futures proxies;
- explicitly forbidden publication claims;
- raw-source registry integrity;
- figure provenance;
- global publication-manifest integrity.

## Local execution

Create an isolated environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt -r requirements-dev.txt

Run:

    bash scripts/run_research_assurance.sh

Expected final line:

    RESEARCH_ASSURANCE_PASS

## Continuous integration

GitHub Actions executes the offline assurance under Python 3.11,
3.12 and 3.13.

Third-party GitHub actions used by the workflow are pinned to immutable
commit SHAs.

External provider calls are not required to verify the exact frozen
publication package.

## Limits

This is an internal automated assurance framework.

It verifies consistency of the research package against declared contracts.

It must not be represented as:

- an independent audit;
- regulatory certification;
- validation of future investment outcomes;
- investment advice.
