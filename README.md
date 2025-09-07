# Poker Bankroll Decision System

Turn messy live poker logs into win rate and variance estimates, run risk of ruin and drawdown simulations, and output a clear stake recommendation for the current bankroll and conditions.

This repo is written to be Copilot friendly in VS Code. It uses short, explicit function names, consistent data types, and inline TODOs so Copilot can propose useful completions.

---

## What problem this solves

Given a bankroll B, an estimated win rate mu, an estimated variance sigma^2, an expected volume of play, and a willingness to move up or down in stakes, choose the stake that maximizes expected utility while keeping drawdowns tolerable.

---

## Aims

**Aim 1 - Data regularization and enrichment**  
- Ingest two years of session logs in mixed formats.  
- Normalize into a canonical schema.  
- Derive features that matter for variance: straddle exposure, stack depth buckets, and side game flags.

**Aim 2 - Parameter estimation**  
- Estimate per hand win rate mu and variance sigma^2 by stake and conditions.  
- Show confidence intervals and sample sizes so decisions are grounded.

**Aim 3 - Simulation, decision, and reporting**  
- Run vectorized Monte Carlo to compute risk of ruin and D buy-in drawdowns over N hands.  
- Produce a stake recommendation table and a one page decision memo you can paste into Evernote.

---

## Repository layout


├─ data/
│ ├─ raw/ # unmodified exports or notes
│ ├─ interim/ # cleaned CSVs with consistent columns
│ └─ processed/ # summary.csv, features.parquet
├─ notebooks/
│ └─ bankroll_decision_system.ipynb
├─ src/
│ ├─ io_ops.py # load_raw, write_interim, read_interim
│ ├─ enrich.py # derive_effective_bb, tag_straddle, tag_side_games, bucket_stack_depth
│ ├─ estimate.py # estimate_mu_sigma, bootstrap_ci
│ ├─ simulate.py # simulate_paths, risk_of_ruin, drawdown_prob
│ ├─ recommend.py # stake_table, step_up_rules, step_down_rules
│ └─ report.py # render_table, save_ror_chart, write_decision_memo
├─ config/
│ └─ settings.yaml # hands_per_hour, stake_map, drawdown thresholds, horizons
├─ tests/
│ └─ test_estimate_simulate.py
├─ README.md
└─ requirements.txt


Copilot hint: keep functions small, pure when possible, and typed.

---

## Canonical data schema

One row per session.

| column               | type     | description                                    |
| -------------------- | -------- | ---------------------------------------------- |
| date                 | date     | session date                                   |
| room                 | string   | cardroom name                                  |
| stake_text           | string   | "1-3", "2-5", "2-5-10"                         |
| buyins_usd           | float    | total bought in for the session                |
| cashouts_usd         | float    | total cashed out for the session               |
| hours_played         | float    | total hours this session                       |
| straddle_exposure    | category | none, low, medium, high, mandatory             |
| side_bombpots_count  | int      | number of bomb pots (0 if none)                |
| side_standup_minutes | int      | estimated minutes the stand up game ran        |
| side_bounty_flag     | bool     | true if a bounty or 7-2 style prop was active  |
| stack_depth_class    | category | S <=120bb, N 120-200bb, D 200-320bb, VD >320bb |
| notes                | string   | free text                                      |

Why buckets for stack depth: recording a continuous effective stack is impractical during live play. A typical depth bucket plus optional counts for deep conditions is a useful and realistic proxy.
