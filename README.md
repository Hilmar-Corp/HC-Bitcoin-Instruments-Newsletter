# Bitcoin Instruments: Direct Holding, Listed Product and Futures

[![Research Assurance](https://github.com/Hilmar-Corp/HC-Bitcoin-Instruments-Newsletter/actions/workflows/research-ci.yml/badge.svg?branch=main)](https://github.com/Hilmar-Corp/HC-Bitcoin-Instruments-Newsletter/actions/workflows/research-ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB)
![Research](https://img.shields.io/badge/research-quantitative-2ea44f)
![Protocol](https://img.shields.io/badge/protocol-v1.1-2ea44f)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

**Reproducible quantitative-research package comparing direct Bitcoin exposure, a listed Bitcoin product and the structural mechanics of CME Bitcoin futures.**

This repository supports HilmarCorp Research Newsletter #11:

> **Le même Bitcoin, trois produits différents**
> *Détention directe, produit coté ou futures : l’actif est le même, l’exposition ne l’est pas.*

The repository contains the empirical pipeline, processed research data, controlled publication claims, robustness analysis, publication figures and assurance framework supporting the note.

It is designed as a reproducible quantitative-research package rather than as a standalone investment recommendation.

## Research question

Bitcoin exposure can enter a portfolio through different financial instruments.

The underlying economic direction may remain similar while the mechanism transmitting that exposure changes.

The study asks:

> Does holding Bitcoin directly, through a listed product, or through futures amount to holding the same portfolio exposure?

The research separates three objects:

1. **Direct Bitcoin** — the spot asset itself.
2. **Listed exposure** — empirically represented by BlackRock's iShares Bitcoin Trust ETF, IBIT.
3. **Futures exposure** — structurally represented by standard CME Bitcoin Futures, symbol `BTC`.

The objective is not to rank these instruments.

It is to identify which additional variables are introduced when the same underlying exposure is carried through different financial structures.

## Research scope

Frozen research period:

```text
2024-01-11 to 2026-08-31
```

Final synchronized sample:

| Item | Value |
|---|---:|
| XNAS sessions | 661 |
| Daily return observations | 660 |
| BTC/XNAS exact-boundary coverage | 100% |
| IBIT NAV coverage | 100% |

Primary Bitcoin reference:

```text
Coinbase BTC-USD
```

Listed product:

```text
IBIT — iShares Bitcoin Trust ETF
```

Futures instrument:

```text
CME Bitcoin Futures — BTC
Contract size: 5 BTC
```

The empirical comparison is limited to Bitcoin versus IBIT.

CME futures are treated **structurally only**.

No publication-grade historical CME futures backtest, futures tracking error or continuous-futures performance series is claimed.

## Temporal alignment

Bitcoin trades continuously.

IBIT trades on a listed-market calendar.

A daily comparison therefore requires an explicit common valuation boundary.

For each XNAS session \(t\), the primary Bitcoin price is defined at the exact effective XNAS close:

```math
P_t^{BTC}=P_t^{BTC}(\tau_t)
```

where:

```math
\tau_t=\text{effective XNAS close for session }t
```

The corresponding simple returns are:

```math
r_t^{BTC}
=
\frac{P_t^{BTC}}{P_{t-1}^{BTC}}-1
```

and:

```math
r_t^{IBIT}
=
\frac{P_t^{IBIT}}{P_{t-1}^{IBIT}}-1
```

The synchronization policy applies:

- exact session boundaries;
- daylight-saving-aware market times;
- holiday and early-close handling;
- no interpolation;
- no future observations;
- no silent market substitution.

All 661 primary session boundaries are matched.

## Main empirical result

Under the synchronized primary specification:

| Measure | Result |
|---|---:|
| Correlation | 0.999651 |
| Beta | 1.008744 |
| R² | 0.999302 |
| Annualized tracking error | 1.3705% |
| Annualized compounded tracking difference | -0.6064% |

The empirical conclusion is deliberately narrow:

> When Bitcoin and IBIT are measured over the same effective market intervals, their daily returns track extremely closely over the study sample.

This does not imply that Bitcoin and IBIT are economically or operationally identical instruments.

## Tracking error and tracking difference

Define the daily return difference:

```math
d_t=r_t^{IBIT}-r_t^{BTC}
```

Annualized tracking error is:

```math
TE_{ann}
=
\sqrt{252}
\sqrt{
\frac{1}{T-1}
\sum_{t=1}^{T}
(d_t-\bar d)^2
}
```

The primary estimate is:

```text
1.3705%
```

Tracking difference is a different object.

The annualized compounded relative drift is:

```math
TD_{ann}
=
\left[
\frac{
\prod_{t=1}^{T}(1+r_t^{IBIT})
}{
\prod_{t=1}^{T}(1+r_t^{BTC})
}
\right]^{252/T}
-1
```

The observed value is:

```text
-0.6064%
```

Tracking error measures dispersion.

Tracking difference measures accumulated relative drift.

The observed tracking difference must not be interpreted as equivalent to the management or sponsor fee.

## Market price and NAV

A listed product introduces another valuation layer.

Let \(NAV_t\) denote IBIT's net asset value per share and \(P_t^M\) its market price.

Define the market premium or discount:

```math
PD_t
=
\frac{P_t^M}{NAV_t}-1
```

Observed distribution:

| Measure | Result |
|---|---:|
| Median | +0.0469% |
| 5th percentile | -0.5166% |
| 95th percentile | +0.5569% |
| Maximum absolute value | 1.7731% |

The market-price identity is:

```math
P_t^M= NAV_t(1+PD_t)
```

Therefore:

```math
1+r_t^M
=
(1+r_t^{NAV})
\frac{1+PD_t}{1+PD_{t-1}}
```

A listed product can therefore track its underlying economic reference closely while still introducing a market-price layer that does not exist in direct spot holding.

## Tracking decomposition

Using log returns:

```math
g_t^{BTC}
=
\ln\left(\frac{P_t^{BTC}}{P_{t-1}^{BTC}}\right)
```

```math
g_t^{NAV}
=
\ln\left(\frac{NAV_t}{NAV_{t-1}}\right)
```

```math
g_t^M
=
\ln\left(\frac{P_t^M}{P_{t-1}^M}\right)
```

the total gap decomposes exactly as:

```math
G_t^{Total}
=
G_t^{NAV-BTC}
+
G_t^{M-NAV}
```

Published annualized drifts:

| Component | Annualized drift |
|---|---:|
| Market IBIT vs BTC | -0.6064% |
| NAV vs BTC | -0.4679% |
| Market IBIT vs NAV | -0.1391% |

The daily log-return decomposition is an accounting identity.

It localizes the observed tracking gap.

It does not by itself identify the economic cause of each component.

In particular, the NAV/BTC component must not be described as management fees because the official IBIT valuation benchmark and the Coinbase reference used in this experiment are not identical.

## Robustness analysis

The publication result is tested against alternative measurement conventions.

### Simple returns versus log returns

| Measure | Simple returns | Log returns |
|---|---:|---:|
| Correlation | 0.999651 | 0.999646 |
| Beta | 1.008744 | 1.008642 |
| R² | 0.999302 | 0.999292 |
| Tracking error | 1.3705% | 1.3767% |
| Tracking difference | -0.6064% | -0.6064% |

The conclusion is effectively invariant to the simple-return versus log-return convention.

### Temporal-boundary sensitivity

A deliberately non-synchronized sensitivity specification replaces the exact XNAS-close Bitcoin observation with a 00:00 UTC Bitcoin boundary at the start of the same session date.

This specification:

- retains 100% exact-boundary coverage;
- uses no future observation;
- is not presented as an alternative publication-grade tracking estimate.

Results:

| Measure | Exact XNAS close | 00:00 UTC sensitivity |
|---|---:|---:|
| Correlation | 0.999651 | 0.178192 |
| Beta | 1.008744 | 0.183105 |
| R² | 0.999302 | 0.031752 |
| Tracking error | 1.3705% | 62.3636% |
| Tracking difference | -0.6064% | +0.3012% |

The result is robust to the mathematical return convention but highly sensitive to temporal synchronization.

The valuation boundary is therefore part of the measurement.

### Premium/discount tail sensitivity

The center of the IBIT market/NAV distribution remains stable after removing the largest absolute observations:

| Sample | Median premium/discount | Maximum absolute value |
|---|---:|---:|
| Full sample | 0.0469% | 1.7731% |
| Excluding top 1% absolute observations | 0.0475% | 1.1564% |
| Excluding top 5% absolute observations | 0.0466% | 0.7144% |

Tail trimming reduces the observed extremes without materially shifting the median.

## CME Bitcoin Futures: structural analysis only

The futures section deliberately avoids an empirical continuous-contract backtest.

Let \(S_t\) be the Bitcoin spot price and \(F_{t,T}\) the futures price for maturity \(T\).

Define the relative basis:

```math
B_{t,T}
=
\frac{F_{t,T}}{S_t}-1
```

so that:

```math
F_{t,T}
=
S_t(1+B_{t,T})
```

For a fixed maturity:

```math
1+r_{t,T}^{F}
=
(1+r_t^S)
\frac{1+B_{t,T}}
{1+B_{t-1,T}}
```

The futures return therefore depends both on:

- the underlying Bitcoin return;
- the change in basis.

For the standard CME Bitcoin Futures contract:

```text
Contract size = 5 BTC
```

The corresponding notional is:

```math
N_{t,T}=5F_{t,T}
```

Notional exposure is not equivalent to posted collateral.

A futures position additionally introduces:

- margin;
- collateral management;
- mark-to-market cash flows;
- expiry;
- maturity selection;
- roll conventions.

A continuous futures history is therefore already a methodological construction.

The repository intentionally rejects unvalidated continuous proxies and incomplete historical individual-contract series as publication-grade evidence.

## Data provenance

The study uses several data layers.

### Bitcoin

Primary empirical reference:

```text
Coinbase BTC-USD
```

The retained hourly raw input is covered by the local raw-input freeze and SHA-256 verification framework.

### IBIT market price

IBIT daily market prices are acquired through Yahoo Finance using `yfinance` in the empirical workflow.

The synchronized processed panel used for publication is frozen and committed.

The complete upstream provider cache is not redistributed in the public repository.

### IBIT NAV

Official historical NAV data is sourced from the BlackRock/iShares fund download.

The original provider file is not redistributed publicly.

A normalized internal representation is used by the research workflow and covered by the raw-input provenance registry.

### Third-party rights

Raw third-party provider datasets are intentionally excluded from the public Git history.

See:

```text
DATA_NOTICE.md
DATA_PROVENANCE.md
```

for details.

## Publication figures

All publication figures are generated from controlled research artifacts.

Current figure pack:

```text
publication/figures/01_btc_ibit_indexed.png
publication/figures/02_ibit_btc_return_regression.png
publication/figures/03_ibit_tracking_difference.png
publication/figures/04_ibit_premium_discount.png
publication/figures/05_ibit_tracking_decomposition.png
publication/figures/06_measurement_robustness.png
```

The six figures correspond to:

1. synchronized BTC and IBIT indexed price paths;
2. synchronized daily-return regression;
3. daily IBIT/BTC tracking difference;
4. IBIT market-price premium or discount to NAV;
5. cumulative tracking-gap decomposition;
6. measurement and tail robustness.

Figure provenance is recorded in:

```text
publication/figures/manifest_v1_1.json
```

The manifest links each registered figure to its generator and controlled inputs through SHA-256 fingerprints.

## Research contract and publication claims

The frozen research contract is:

```text
research/contract_v1_1.json
```

Status:

```text
FROZEN
```

Publication status:

```text
QUANT_ASSET_MANAGEMENT_READY
```

Controlled publication metrics are stored in:

```text
publication/claims_registry_v1_1.json
```

The registry also contains forbidden claim patterns designed to prevent rejected or unsupported futures evidence from re-entering publication material.

## Research assurance

The repository uses a fail-closed assurance framework covering:

- frozen research-artifact integrity;
- raw-source registry integrity;
- synchronized sample size;
- unique and ordered dates;
- positive and finite market values;
- BTC / IBIT / NAV calendar consistency;
- exact XNAS temporal alignment;
- independent recomputation of tracking statistics;
- NAV premium/discount statistics;
- exact log-return decomposition;
- futures-scope governance;
- rejected-proxy enforcement;
- controlled publication claims;
- robustness outputs;
- figure provenance;
- global publication-manifest integrity.

The current publication package passes:

```text
23 tests
6 registered publication figures
PUBLICATION MANIFEST: PASS
PUBLICATION GATE: PASS
RESEARCH_ASSURANCE_PASS
```

This assurance framework verifies internal consistency, traceability and reproducibility.

It is not an independent audit, regulatory certification or validation of future investment outcomes.

Detailed documentation:

```text
RESEARCH_ASSURANCE.md
```

## Repository structure

```text
.
├── .github/
│   └── workflows/
│       └── research-ci.yml
├── data/
│   ├── raw/
│   └── processed/
├── outputs/
│   ├── reports/
│   └── tables/
├── publication/
│   ├── claims_registry_v1_1.json
│   └── figures/
├── research/
│   ├── contract_v1_1.json
│   ├── freeze_v1_1.json
│   ├── raw_freeze_v1_1.json
│   ├── raw_sources_v1_1.json
│   └── environment_v1_1.txt
├── scripts/
│   ├── build_publication_manifest.py
│   ├── make_publication_figures.py
│   ├── make_robustness_figure.py
│   ├── register_figure.py
│   ├── run_publication_robustness.py
│   ├── run_research_assurance.sh
│   ├── verify_figure_provenance.py
│   └── verify_raw_inputs.py
├── tests/
├── final_ibit_nav_decomposition.py
├── normalize_blackrock_download.py
├── rerun_etf_synced.py
├── DATA_NOTICE.md
├── DATA_PROVENANCE.md
├── REPRODUCIBILITY.md
├── RESEARCH_ASSURANCE.md
├── PUBLICATION_MANIFEST.json
├── CITATION.cff
├── LICENSE
├── NOTICE
├── Makefile
└── README.md
```

## Installation

Create an isolated Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## Tests

Run the deterministic test suite:

```bash
python -m pytest -q
```

Expected publication snapshot:

```text
23 passed
```

## Complete research assurance

Run:

```bash
bash scripts/run_research_assurance.sh
```

Expected final line:

```text
RESEARCH_ASSURANCE_PASS
```

Equivalent Make target:

```bash
make assurance
```

## Verify publication artifacts

Verify figure provenance:

```bash
python scripts/verify_figure_provenance.py
```

Expected result:

```text
FIGURE PROVENANCE: PASS — 6 registered figure(s)
```

Verify the Git-canonical publication manifest:

```bash
python scripts/build_publication_manifest.py --verify
```

## Verify local raw inputs

Third-party provider raw files are not redistributed publicly.

On the controlled research machine where they are available:

```bash
python scripts/verify_raw_inputs.py --require-present
```

This checks local provider files against:

```text
research/raw_freeze_v1_1.json
```

## Reproducibility model

The repository distinguishes two forms of reproducibility.

### Frozen-output verification

The committed package contains processed data, reports, tables, figures, contracts, tests and manifests sufficient to verify the frozen publication state offline.

### Methodological reconstruction

A new empirical run can reacquire external provider data and re-execute the documented methodology.

The principal empirical workflow is implemented in:

```text
rerun_etf_synced.py
normalize_blackrock_download.py
final_ibit_nav_decomposition.py
```

Upstream providers may revise historical data, metadata, file formats or interfaces.

A newly acquired dataset is therefore not guaranteed to be byte-identical to the frozen publication inputs.

See:

```text
REPRODUCIBILITY.md
```

## Interpretation limits

This repository does not establish:

- that direct Bitcoin, IBIT and CME futures are interchangeable;
- that IBIT's historical tracking statistics will persist;
- that tracking difference is equivalent to product fees;
- a historical CME futures tracking-error estimate;
- a publication-grade continuous CME futures return series;
- the optimal instrument for Bitcoin exposure;
- an investment strategy;
- predictive power;
- future investment performance.

The empirical results are conditional on:

- the study period;
- the selected Bitcoin reference;
- the selected listed product;
- the exact temporal-alignment convention;
- the available public and official data;
- the declared methodological controls.

The futures analysis is structural rather than an empirical performance comparison.

## Research interpretation

The research supports a narrower conclusion:

> The underlying economic exposure may be similar, while the instrument determines how that exposure enters the portfolio.

Direct holding, a listed product and a futures contract can all provide economic sensitivity to Bitcoin.

They do not create the same financial object.

The instrument can change:

- valuation;
- market microstructure;
- custody;
- collateral requirements;
- capital usage;
- basis exposure;
- expiry;
- roll mechanics;
- operational constraints.

The underlying describes what the portfolio seeks to be exposed to.

The instrument describes how that exposure is transmitted.

## About HilmarCorp

HilmarCorp develops quantitative research and infrastructure for systematic Bitcoin allocation and digital-asset exposure management.

Its research publications focus on making portfolio exposure, risk and implementation choices more explicit, measurable and auditable.

## Citation

Citation metadata is provided in:

```text
CITATION.cff
```

## License

Original HilmarCorp code, tests, research tooling and documentation are released under the Apache License 2.0 as described in:

```text
LICENSE
NOTICE
```

Third-party market data is outside the Apache-2.0 grant.

## Disclaimer

This repository is provided for quantitative research and educational purposes.

Nothing in this repository constitutes investment advice, a recommendation, a forecast, investment management, order execution, a solicitation, or an offer to buy or sell any financial instrument or digital asset.

Historical observations are not indicative of future outcomes.
