# Third-party data notice

This repository contains derived analytical artifacts produced from
third-party market and product data.

The Apache-2.0 license applies only to original HilmarCorp code, tests,
automation and documentation.

It does not grant rights to third-party market data or provider content.

Raw provider caches are intentionally excluded from the public repository.

The research pipeline references, among others:

- Coinbase Exchange for BTC-USD observations;
- BlackRock/iShares for official IBIT fund and NAV information;
- Yahoo Finance / yfinance for listed-market observations where documented;
- exchange-calendar metadata supplied by `exchange_calendars`;
- public CME Group documentation for Bitcoin Futures contract mechanics.

Historical contract-by-contract CME futures data sufficient for a publication-
grade empirical futures backtest is not part of the frozen empirical package.

The futures section is therefore explicitly structural.

Use, storage and redistribution of provider data remain subject to the
applicable provider terms and rights.

The committed processed datasets, reports and tables are derived research
artifacts. Upstream reconstruction may differ if providers revise historical
records, interfaces or metadata.

See `DATA_PROVENANCE.md` and `research/raw_sources_v1_1.json`.
