# Data provenance

## Research object

HilmarCorp Research — Newsletter #11

**Le même Bitcoin, trois produits différents**

*Détention directe, produit coté ou futures : l'actif est le même,
l'exposition ne l'est pas.*

## Empirical sample

The primary synchronized sample covers:

- start: 2024-01-11;
- end: 2026-08-31;
- XNAS sessions: 661;
- return observations: 660.

## Bitcoin spot reference

Primary source:

`Coinbase BTC-USD`

Bitcoin is sampled at the exact XNAS closing boundary used for the
IBIT comparison.

The synchronization protocol uses the actual XNAS trading calendar,
including holidays, daylight-saving changes and early closes.

No interpolation is permitted.

No future observation may be substituted for a missing close-boundary value.

## IBIT market price

Instrument:

`iShares Bitcoin Trust ETF (IBIT)`

The empirical listed-product analysis applies specifically to IBIT.

It must not be generalized mechanically to every Bitcoin ETF or ETP.

## IBIT NAV

Source:

Official BlackRock/iShares fund download.

The normalized workbook is a deterministic local representation of the
provider's SpreadsheetML download.

The final empirical merge contains NAV for all 661 certified IBIT/BTC
observations.

The exact log-return identity is:

    market vs BTC
    =
    NAV vs BTC
    +
    market vs NAV

## Canonical research contracts

Publication-level empirical values are controlled by:

    research/contract_v1_1.json
    publication/claims_registry_v1_1.json

## CME Bitcoin Futures

Instrument:

`CME Bitcoin Futures`, root `BTC`.

The futures publication block is structural only.

It documents:

- contract notional;
- contract size;
- collateral and margin;
- variation margin;
- clearing;
- expiry;
- basis;
- roll;
- trading availability;
- absence of physical Bitcoin custody by the futures holder.

The empirical contract-by-contract futures backtest is:

    EXCLUDED_BY_DESIGN

The following are explicitly rejected as publication-grade historical
futures evidence:

- Yahoo `BTC=F` continuous proxy;
- incomplete Yahoo histories of expired CME contracts;
- unauthenticated CME settlement requests returning HTTP 403.

No historical futures tracking statistic from these rejected sources may
be published.

## Raw-data policy

Raw third-party caches are retained locally where available.

Their SHA-256 fingerprints are recorded in:

    research/raw_freeze_v1_1.json

Raw provider files are intentionally excluded from the public repository.

See also:

    DATA_NOTICE.md
    REPRODUCIBILITY.md
    RESEARCH_ASSURANCE.md
