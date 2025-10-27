# Poker Bankroll Decision System

Turn messy live poker logs into win rate and variance estimates, run risk of ruin and drawdown simulations, and output a clear stake recommendation for the current bankroll and conditions.

---


## Aims

**Aim 1 - Data regularization and enrichment**  
- Ingest two years of session logs in mixed formats.  
- Normalize into a canonical schema.  
- Derive features that matter for variance: straddle exposure, stack depth buckets, and side game flags.
- How can Karl Browman help? [Karl Broman, "Data Cleaning Principles" ](https://kbroman.org/Talk_DataCleaning2023/data_cleaning.pdf)
  - Draft a data dictionary that matches the schema above.
  - Build a small mapping table that normalizes stake_text to numeric blinds.
  - Import a sample of 30–50 sessions and prove the whole pipeline runs end to end.
D

**Aim 2 - Parameter estimation**  
- Estimate per hand win rate mu and variance sigma^2 by stake and conditions.  
- Show confidence intervals and sample sizes so decisions are grounded.

**Aim 3 - Simulation, decision, and reporting**  
- Run vectorized Monte Carlo to compute risk of ruin and D buy-in drawdowns over N hands.  
- Produce a stake recommendation table and a one page decision memo you can paste into Evernote.
- Given a bankroll B, an estimated win rate mu, an estimated variance sigma^2, an expected volume of play, and a willingness to move up or down in stakes, choose the stake that maximizes expected utility while keeping drawdowns tolerable.


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

## To do

Data cleanup sprint
- Write quick regex taggers for straddle and side games.
- Add a helper to assign stack_depth_class from your typical buy-in at each room, with a notes override.
- Produce the first summary.csv with μ and σ by condition and include N_hours.
First analysis pass
- Generate a stake recommendation table for 2/5, 2/5/10, and 5/10/25 using your current bankroll.
- Export ror_monthly.png and paste the table and image into Evernote with a short memo.
Going forward
- After each session, log: stake_text, hours, buyins_usd, cashouts_usd, straddle_exposure, stack_depth_class, side game counts, one-line note.
- Weekly Habitify tick: reconcile results and append a row.
- Monthly: rerun the notebook and update the Evernote snaps
  