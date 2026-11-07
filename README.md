# England's comeback: a miracle or the right coaching decisions?

**Sweden 2-2 England (England win 3-2 on penalties) — UEFA Women's EURO 2025 quarter-final, 17 July 2025**

## Short answer

> TODO

## Match context

- **Competition:** UEFA Women's EURO 2025, quarter-final, Stadion Letzigrund, Zürich.
- **Score:** Sweden 2-2 England after extra time; England won the shootout 3-2.
- **Goals:** Asllani 2', Blackstenius 25' (Sweden); Bronze 79', Agyemang 81' (England).
- **Key decisions:** England's triple substitution (Mead, Agyemang, Morgan) in the 70th minute and Kelly
  on for Hemp at 77:33 on the StatsBomb clock.
- **Shootout:** 14 kicks, only 5 scored.

TODO: add a short narrative of the match.

## H1 — Sweden's press broke England's build-up in the first half

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## H2 — Substitutions after 70' improved England's chances

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## H3 — England switched to a 3-4-3

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## H4 — England's crossing strategy worked

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## H5 — Hampton kept England alive

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## H6 — The shootout was mostly luck

- **Claim:** TODO
- **Chart:** `figures/TODO.png`
- **What it shows:** TODO
- **Verdict:** TODO

## Conclusion

TODO

## Limitations

- **Single match.** Everything here describes one game; small samples (e.g. 18 England shots, 14 penalties)
  make before/after comparisons fragile and none of the differences are statistically robust.
- **xG model.** StatsBomb's xG model differs from Opta's (and others), so numbers will not match figures
  quoted on broadcasts or in other publications. StatsBomb Open Data has no post-shot xG, so goalkeeper
  performance is approximated with pre-shot xG.
- **Shootouts are noisy.** 14 kicks are far too few to separate skill from luck; any baseline comparison is
  only a rough benchmark.
- **Event definitions.** Ball losses, pressures and shots on target depend on definitions documented in
  `notebooks/02_analysis_prep.ipynb`; different choices give different counts.
- **360 coverage.** Freeze frames only include players inside the broadcast camera's view, so counts of
  nearby players are lower bounds.
- **Timing conventions.** StatsBomb minutes are the elapsed clock; broadcast minutes are one higher
  (a goal at 1:44 is "2'"). Substitution minutes can differ by one from official match reports.

## Data & tools

- **Data:** [StatsBomb Open Data](https://github.com/statsbomb/open-data) — Women's EURO 2025
  (competition 53, season 315), event data and 360 freeze frames, accessed with
  [`statsbombpy`](https://github.com/statsbomb/statsbombpy).
- **Tools:** Python, pandas, pyarrow, mplsoccer, matplotlib, Jupyter.

### Project structure

```
euro2025-sweden-england/
├── README.md
├── requirements.txt
├── data/raw/            # cached StatsBomb downloads (parquet, not tracked)
├── data/processed/      # prepared tables per hypothesis (parquet, not tracked)
├── notebooks/
│   ├── 01_data_loading.ipynb    # load + validate against known match facts
│   └── 02_analysis_prep.ipynb   # one prepared table per hypothesis (H1–H6)
├── src/
│   ├── data.py          # loading, caching, substitutions, lineup windows, filters
│   └── plots.py         # visualization functions
└── figures/             # exported charts
```

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_loading.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/02_analysis_prep.ipynb
```

The first run downloads the data (the H6 baseline loads all 31 Euro 2025 matches) and caches it in
`data/raw/`; later runs read from the cache. Prepared tables are written to `data/processed/` and can be
loaded with `src.data.load_processed("<table name>")`.

## Attribution

**Data: StatsBomb Open Data.**

> TODO: add the StatsBomb logo from the StatsBomb Media Pack (linked from the
> [open-data repository](https://github.com/statsbomb/open-data)) to this README and to every published
> chart, as required by the StatsBomb Open Data terms.
