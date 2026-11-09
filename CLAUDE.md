# CLAUDE.md

## Project
Football analytics project on Sweden vs England, UEFA Women's EURO 2025 quarter-final (17 July 2025, Stadion Letzigrund, Zurich). Sweden led 2–0 (Asllani 2', Blackstenius 25'), England equalised (Bronze 79', Agyemang 81'), 2–2 after extra time, England won the shootout 3–2.

## The football question
"England's comeback: a miracle or the right coaching decisions?"
Every chart and every paragraph must serve this question. If something does not help answer it, leave it out.

## Hypotheses (status as of now)
- H1 England mostly lost the ball on their own, but both Sweden goals came from pressing and a tackle — chart done (figures/01_h1_turnovers.png).
- H2 England's big chances came after Kelly came on (xG per shot 0.06 → 0.31); the triple substitution added tempo, not quality — chart done (figures/02_h2_cumulative_xg.png).
- H3 Did England switch to a 3-4-3? Bronze pushed up, James dropped deeper; average positions show no back three — chart done (figures/03_h3_pass_networks.png).
- H4 Crossing strategy after Kelly came on — to do.
- H5 Hampton kept England alive — to do.
- H6 The shootout was mostly luck (Sweden's misses are the outlier) — to do.

## Data
- StatsBomb Open Data via statsbombpy: competition_id=53, season_id=315 (event and 360 data).
- Raw data is cached in data/raw/, prepared tables in data/processed/. Both are git-ignored.
- Notebook 01 = loading and validation, 02 = analysis tables per hypothesis, 03 = figures.
- Coordinates: each team's events are stored in that team's own attacking direction. When plotting both teams on one pitch, convert the opponent with x' = 120 − x, y' = 80 − y and check the result.
- Known data notes: StatsBomb's under_pressure flag is set only on the event where the ball is lost (lower bound of pressure). Key goal sequences were checked against video: the 2' goal started with Asllani's press on Carter, then Angeldal's block on Walsh's pass.

## Working rules
1. Explain the plan first, then write code. Before any non-trivial change, state in a few lines what you will do and which tables you will use.
2. Never invent numbers. Every number in a chart, title or text must be read from the data tables, not typed in. If a number is not available, say so instead of estimating.
3. Do not recompute analysis in notebook 03. If a figure needs data that is missing, report it; analysis belongs in notebook 02.
4. Claims must follow the evidence. Write chart titles only after checking what the data shows. If the data does not support a claim, do not make it, and say so.
5. If the data disagrees with facts given in a prompt, do not bend the code to match: report the mismatch.
6. All project content in English: code, comments, notebooks, README, commit messages.

## Charts
- Before creating or editing any chart, use the data-visualization skill and follow it.
- Reuse the style helpers and team colours in src/plots.py (England red #e34948, Sweden blue #2a78d6).
- Every chart has: a title that states the finding, a subtitle with sample sizes, a footer starting with "Data: StatsBomb Open Data" (plus "xG: StatsBomb model" where xG is shown), and an empty bottom-right corner for the StatsBomb logo.
- Every chart has built-in checks in the notebook (counts, totals, coordinates) that stop the run if they fail.
- Save to figures/ as numbered PNGs (01_, 02_, …), 300 dpi.

## Git
- After a change runs cleanly and all built-in checks pass, commit it with a clear message.
- Never push to GitHub unless explicitly asked.
