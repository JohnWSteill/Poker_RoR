"""
Recommendation and reporting functions for poker bankroll decisions.
Generate stake recommendations and decision memos.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict


def generate_stake_recommendations(
    simulation_df: pd.DataFrame,
    current_bankroll_bb: float,
    risk_tolerance: float = 0.05,
) -> pd.DataFrame:
    """
    Generate stake recommendations based on simulation results.

    Considers risk of ruin, expected return, and bankroll requirements.

    Args:
        simulation_df: DataFrame with simulation results
        current_bankroll_bb: Current bankroll in big blinds
        risk_tolerance: Acceptable risk of ruin level

    Returns:
        DataFrame with recommendations for each stake
    """
    recommendations = []

    for _, row in simulation_df.iterrows():
        stake = row["stake_text"]

        # Get risk metrics for 10,000 hand horizon (long-term)
        ror_10k = row.get("ror_10000h", float("inf"))
        expected_final = row.get("final_mean_10000h", current_bankroll_bb)

        # Calculate bankroll requirements (conservative estimates)
        min_bankroll_buyins = 25  # Conservative minimum
        min_bankroll_bb = min_bankroll_buyins * 100  # 100BB per buyin

        # Recommendation logic
        if ror_10k <= risk_tolerance and current_bankroll_bb >= min_bankroll_bb:
            if row["mu"] > 0:
                recommendation = "RECOMMENDED"
                reason = f"Low risk ({ror_10k:.1%}), positive expectation (+{row['mu']:.4f} BB/hand)"
            else:
                recommendation = "MARGINAL"
                reason = f"Low risk but negative expectation ({row['mu']:.4f} BB/hand)"
        elif ror_10k <= risk_tolerance * 2:  # Slightly higher risk tolerance
            recommendation = "ACCEPTABLE"
            reason = f"Moderate risk ({ror_10k:.1%}), monitor closely"
        else:
            recommendation = "NOT RECOMMENDED"
            reason = f"High risk of ruin ({ror_10k:.1%})"

        if current_bankroll_bb < min_bankroll_bb:
            recommendation = "UNDERFUNDED"
            reason = f"Insufficient bankroll (need {min_bankroll_bb:.0f}BB, have {current_bankroll_bb:.0f}BB)"

        recommendations.append(
            {
                "stake_text": stake,
                "recommendation": recommendation,
                "reason": reason,
                "ror_10k_hands": ror_10k,
                "expected_return_bb_per_hand": row["mu"],
                "min_bankroll_bb": min_bankroll_bb,
                "current_bankroll_sufficient": current_bankroll_bb
                >= min_bankroll_bb,
                "expected_bb_after_10k": expected_final,
            }
        )

    return pd.DataFrame(recommendations).sort_values("ror_10k_hands")


def create_decision_memo(
    recommendations_df: pd.DataFrame,
    enriched_sessions: pd.DataFrame,
    current_bankroll_bb: float,
    config: Dict,
) -> str:
    """
    Generate a one-page decision memo suitable for saving or sharing.

    Args:
        recommendations_df: DataFrame with stake recommendations
        enriched_sessions: DataFrame with session data
        current_bankroll_bb: Current bankroll size
        config: Simulation configuration

    Returns:
        Formatted decision memo as string
    """
    memo = f"""
# POKER BANKROLL DECISION MEMO
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Current Bankroll: {current_bankroll_bb:,.0f} BB

## EXECUTIVE SUMMARY
Based on {len(enriched_sessions)} sessions and {enriched_sessions['hours_played'].sum():.0f} hours of data:

"""

    # Find best recommendation
    recommended = recommendations_df[
        recommendations_df["recommendation"] == "RECOMMENDED"
    ]
    if len(recommended) > 0:
        best_stake = recommended.iloc[0]
        memo += f"""
**PRIMARY RECOMMENDATION: {best_stake['stake_text']}**
- Risk of Ruin (10K hands): {best_stake['ror_10k_hands']:.1%}
- Expected Return: {best_stake['expected_return_bb_per_hand']:.4f} BB/hand
- Reason: {best_stake['reason']}

"""
    else:
        memo += """
**NO STAKES CURRENTLY RECOMMENDED**
All analyzed stakes exceed acceptable risk thresholds or show negative expectation.
Consider building bankroll at lower stakes or improving play.

"""

    memo += "## STAKE ANALYSIS\n\n"

    for _, row in recommendations_df.iterrows():
        status_emoji = {
            "RECOMMENDED": "✅",
            "ACCEPTABLE": "⚠️",
            "MARGINAL": "🔸",
            "NOT RECOMMENDED": "❌",
            "UNDERFUNDED": "💰",
        }.get(row["recommendation"], "❓")

        memo += f"""
**{status_emoji} {row['stake_text']} - {row['recommendation']}**
- Risk of Ruin: {row['ror_10k_hands']:.1%}
- Expected Return: {row['expected_return_bb_per_hand']:.4f} BB/hand
- Min Bankroll: {row['min_bankroll_bb']:.0f} BB
- Assessment: {row['reason']}

"""

    memo += f"""
## RISK PARAMETERS
- Risk Tolerance: {config['risk_tolerance']:.1%}
- Simulation Runs: {config['n_simulations']:,}
- Time Horizon: {max(config['time_horizons']):,} hands

## DATA QUALITY
- Total Sessions: {len(enriched_sessions)}
- Date Range: {enriched_sessions['date'].min()} to {enriched_sessions['date'].max()}
- Total Hours: {enriched_sessions['hours_played'].sum():.0f}
- Net Result: ${enriched_sessions['net_result'].sum():.2f}

---
*This analysis is based on historical performance and Monte Carlo simulation. 
Past results do not guarantee future performance. 
Always play within your means and maintain proper bankroll management.*
"""

    return memo


def create_summary_table(recommendations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a clean summary table for display.

    Args:
        recommendations_df: DataFrame with recommendations

    Returns:
        Formatted summary DataFrame
    """
    summary_cols = [
        "stake_text",
        "recommendation",
        "ror_10k_hands",
        "expected_return_bb_per_hand",
        "min_bankroll_bb",
    ]

    summary = recommendations_df[summary_cols].copy()
    summary["ror_10k_hands"] = summary["ror_10k_hands"].apply(
        lambda x: f"{x:.1%}"
    )
    summary["expected_return_bb_per_hand"] = summary[
        "expected_return_bb_per_hand"
    ].round(4)
    summary["min_bankroll_bb"] = summary["min_bankroll_bb"].astype(int)

    summary.columns = [
        "Stake",
        "Recommendation",
        "Risk of Ruin",
        "BB/Hand",
        "Min Bankroll BB",
    ]

    return summary
