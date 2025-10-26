"""
Parameter estimation functions for poker bankroll analysis.
Estimate per hand win rate mu and variance sigma^2 by stake and conditions.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple


def estimate_mu_sigma_by_stake(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate win rate (mu) and variance (sigma^2) per hand by stake level.

    Returns estimates with confidence intervals and sample sizes.

    Args:
        df: DataFrame with enriched session data

    Returns:
        DataFrame with parameter estimates by stake
    """
    estimates = []

    for stake in df["stake_text"].unique():
        stake_data = df[df["stake_text"] == stake].copy()

        if len(stake_data) < 3:  # Minimum sample size
            continue

        # Basic statistics
        n_sessions = len(stake_data)
        total_hands = stake_data["hands_played"].sum()

        # Per-hand win rate (mu)
        mu_bb_per_hand = stake_data["bb_per_hand"].mean()
        mu_usd_per_hand = stake_data["usd_per_hand"].mean()

        # Per-hand variance (sigma^2)
        session_bb_variance = stake_data["bb_per_hand"].var()
        session_usd_variance = stake_data["usd_per_hand"].var()

        # Confidence intervals
        confidence_level = 0.95
        t_critical = stats.t.ppf((1 + confidence_level) / 2, df=n_sessions - 1)

        mu_bb_se = stake_data["bb_per_hand"].std() / np.sqrt(n_sessions)
        mu_bb_ci_lower = mu_bb_per_hand - t_critical * mu_bb_se
        mu_bb_ci_upper = mu_bb_per_hand + t_critical * mu_bb_se

        mu_usd_se = stake_data["usd_per_hand"].std() / np.sqrt(n_sessions)
        mu_usd_ci_lower = mu_usd_per_hand - t_critical * mu_usd_se
        mu_usd_ci_upper = mu_usd_per_hand + t_critical * mu_usd_se

        # Aggregate session data
        total_bb_won = stake_data["bb_per_session"].sum()
        total_usd_won = stake_data["net_result"].sum()
        avg_hours = stake_data["hours_played"].mean()

        estimates.append(
            {
                "stake_text": stake,
                "n_sessions": n_sessions,
                "total_hands": total_hands,
                "total_hours": stake_data["hours_played"].sum(),
                "avg_session_hours": avg_hours,
                # Win rate estimates (mu)
                "mu_bb_per_hand": mu_bb_per_hand,
                "mu_bb_ci_lower": mu_bb_ci_lower,
                "mu_bb_ci_upper": mu_bb_ci_upper,
                "mu_usd_per_hand": mu_usd_per_hand,
                "mu_usd_ci_lower": mu_usd_ci_lower,
                "mu_usd_ci_upper": mu_usd_ci_upper,
                # Variance estimates (sigma^2)
                "sigma2_bb_per_hand": session_bb_variance,
                "sigma2_usd_per_hand": session_usd_variance,
                # Derived metrics
                "bb_per_hour": mu_bb_per_hand
                * stake_data["hands_per_hour"].mean(),
                "hourly_rate_usd": mu_usd_per_hand
                * stake_data["hands_per_hour"].mean(),
                # Totals
                "total_bb_won": total_bb_won,
                "total_usd_won": total_usd_won,
            }
        )

    return pd.DataFrame(estimates)


def bootstrap_confidence_intervals(
    df: pd.DataFrame, n_bootstrap: int = 1000
) -> Dict:
    """
    Generate bootstrap confidence intervals for win rate estimates.

    This provides more robust confidence intervals, especially for smaller samples.

    Args:
        df: DataFrame with session data
        n_bootstrap: Number of bootstrap samples

    Returns:
        Dictionary with bootstrap results by stake
    """
    np.random.seed(42)

    bootstrap_results = {}

    for stake in df["stake_text"].unique():
        stake_data = df[df["stake_text"] == stake]["bb_per_hand"].values

        if len(stake_data) < 5:  # Skip if too few samples
            continue

        bootstrap_means = []

        for _ in range(n_bootstrap):
            bootstrap_sample = np.random.choice(
                stake_data, size=len(stake_data), replace=True
            )
            bootstrap_means.append(np.mean(bootstrap_sample))

        bootstrap_means = np.array(bootstrap_means)

        bootstrap_results[stake] = {
            "mean": np.mean(bootstrap_means),
            "std": np.std(bootstrap_means),
            "ci_lower": np.percentile(bootstrap_means, 2.5),
            "ci_upper": np.percentile(bootstrap_means, 97.5),
            "ci_10_90": (
                np.percentile(bootstrap_means, 10),
                np.percentile(bootstrap_means, 90),
            ),
        }

    return bootstrap_results


def calculate_sharpe_ratios(estimates_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Sharpe-like ratios for each stake level.

    Args:
        estimates_df: DataFrame with mu and sigma estimates

    Returns:
        DataFrame with added sharpe_ratio column
    """
    df = estimates_df.copy()

    # Calculate Sharpe ratio (return / volatility)
    df["sigma_bb_per_hand"] = np.sqrt(df["sigma2_bb_per_hand"])
    df["sharpe_ratio"] = df["mu_bb_per_hand"] / df["sigma_bb_per_hand"]

    # Handle division by zero
    df["sharpe_ratio"] = df["sharpe_ratio"].replace([np.inf, -np.inf], np.nan)

    return df


def estimate_kelly_criterion(
    mu: float, sigma: float, bankroll: float
) -> Tuple[float, float]:
    """
    Calculate Kelly criterion for optimal bet sizing.

    Args:
        mu: Expected return per hand
        sigma: Standard deviation per hand
        bankroll: Current bankroll size

    Returns:
        Tuple of (kelly_fraction, optimal_bet_size)
    """
    if sigma == 0:
        return 0.0, 0.0

    # Kelly fraction = mu / sigma^2 (simplified for normally distributed returns)
    kelly_fraction = mu / (sigma**2)

    # Cap at reasonable maximum (25% of bankroll)
    kelly_fraction = min(kelly_fraction, 0.25)
    kelly_fraction = max(kelly_fraction, 0.0)  # No negative betting

    optimal_bet_size = kelly_fraction * bankroll

    return kelly_fraction, optimal_bet_size
