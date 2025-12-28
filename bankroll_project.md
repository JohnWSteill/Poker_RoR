# Poker Bankroll Decision System - Project Formulation

## Purpose
Turn messy live poker logs into trusted estimates of win rate (mu) and variance (sigma), then use those estimates to choose stakes that maximize expected utility while keeping drawdowns tolerable. The system is practical for live play, uses your own data, and outputs an actionable stake recommendation before each session.

## Principles
- Data before opinion: estimates come from your log, not generic numbers.
- One place to run it: a single notebook that ingests, estimates, simulates, and reports.
- Actionable outputs only: each run ends with a recommendation and clear guardrails.
- Show uncertainty: include sample sizes and confidence bands so you see when estimates are thin.
- Keep it light: weekly quick updates, monthly deeper recalibration, minimal manual inputs.
- Use hyphens in prose and keep formatting simple for portability.

## Scope and Aims
Single project with three aims.

### Aim 1 - Data regularization and enrichment
Clean two years of historical logs, normalize into a canonical schema, and derive the features that matter for variance.

**Canonical schema - one row per session**
- date, room, stake_text ("1-3", "2-5", "2-5-10", "5-10-25")
- buyins_usd, cashouts_usd, hours_played
- straddle_exposure: none, low (<20%), medium (20-60%), high (>60%), mandatory
- side games: bombpots_count, standup_minutes, bounty_flag
- stack_depth_class: S <= 120 bb, N 120-200 bb, D 200-320 bb, VD > 320 bb
- notes: short free text

**Why depth buckets, not continuous stacks**
Continuous effective stacks are impractical to capture live. A typical depth bucket plus optional rough deep-hours percent is a realistic proxy that tracks variance well enough for decisioning.

**Backfill plan**
- Parse stake_text into numeric blinds and effective big blind (BB_eff).
- Infer straddle_exposure and side games from notes via simple keyword rules.
- Assign stack_depth_class from your usual buy-in pattern at each room, with manual overrides when notes indicate deep play.

### Aim 2 - Parameter estimation
Estimate per hand mu and sigma by stake and conditions, with confidence intervals.

**Units and transforms**
- bb_result = (cashouts_usd - buyins_usd) / BB_eff
- bb_per_hour = bb_result / hours_played
- bb_per_hand = bb_per_hour / hands_per_hour(stake_text)

**Grouping keys**
- [stake_text, straddle_exposure, stack_depth_class, side game flags]

**Outputs**
- mu_hand, sigma_hand (or sigma2_hand), mu_hour, sample size in hours, date range, and 95 percent CI for mu (bootstrap or normal approximation).

### Aim 3 - Simulation, decision, and reporting
Turn estimates into risk metrics and a stake choice.

**Risk metrics**
- Risk of ruin within N hands.
- Probability of a D buy-in drawdown within N hands.
- Sensitivity runs: mu minus 2 bb per hour, sigma plus 20 percent.

**Recommendation**
- A table per stake with bankroll in bb, mu_hand, sigma_hand, Kelly fraction mu/sigma2, risk metrics at configured horizons, and a final recommendation.
- A one-page decision memo you can paste into Evernote: context, mu and sigma snapshot, risk metrics, recommendation, and triggers to step up or step down.

## Decision rules
- Step up: only if lineup looks soft, current stake mu_hour exceeds threshold X, and simulated probability of a Z buy-in drawdown within N hands is under Y percent.
- Step down: after a Z buy-in downswing or if trailing 100 hour mu falls below threshold.
- Re-estimate monthly or after 40 to 60 hours at a given stake.
- Shot taking at 2-5-10 is allowed when edge looks strong and guardrails are met. Default daily game is 2-5 with light straddling under 20 percent.

## Deliverables and Milestones
- Notebook: bankroll_decision_system.ipynb with four sections - Import, Enrich, Estimate, Simulate and Report.
- Data artifacts: data/interim cleaned tables and data/processed/summary.csv with grouped estimates.
- Reporting artifacts: ror_monthly.png chart and reports/decision_memo.md.
- Config: config/settings.yaml for hands_per_hour, stake_map, and thresholds.
- README.md that orients Copilot and documents function signatures and layout.

**Milestone 1 - End to end on a sample (1-2 days)**
- Import 30-50 sessions and run the pipeline to produce a first summary.csv and one chart.
- Draft a decision memo for 2-5 vs 2-5-10.

**Milestone 2 - Full archive cleaned (3-5 days of focused work)**
- Confidence intervals added, sensitivity runs saved, first monthly snapshot published.

**Milestone 3 - Stable routine (ongoing)**
- Weekly bankroll update and session capture habit in place.
- Monthly risk snapshot pasted to Evernote with the stake table.

## Workflow and Habits
- After each session: capture stake_text, hours, buyins_usd, cashouts_usd, straddle_exposure, stack_depth_class, side-game counts, and one-line note.
- Weekly: reconcile results and append a row to your log.
- Monthly: rerun the notebook, update Evernote, and review decision rules.
- Before a session: open the notebook, refresh the recommendation, skim the memo, and set step-up and step-down triggers.

## Risks and Assumptions
- Estimates are only as good as the log. Thin groups will have wide intervals.
- Hands per hour and BB_eff are approximations for live play and should be revisited when conditions change.
- The normal approximation for hand outcomes is a convenience. If heavy tails are large, consider robust variance or a t-like generator in simulation.
- Utility-based stake choice is the long term target. The current version optimizes expected utility under simple CRRA-like utility or uses drawdown thresholds as a proxy.

## Next actions
- Create the notebook and data dictionary.
- Build the stake_map and hands_per_hour tables.
- Import a 50-session sample and prove the full loop.
- Generate the first recommendation table for 2-5, 2-5-10, and 5-10-25 using your current bankroll.
- Export ror_monthly.png and paste the table and image into Evernote with a short memo.
