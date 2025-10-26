"""
Monte Carlo simulation functions for bankroll analysis.
Risk of ruin and drawdown probability calculations.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple


def simulate_bankroll_paths(
    mu: float,
    sigma: float,
    initial_bankroll: float,
    n_hands: int,
    n_simulations: int = 10000,
) -> np.ndarray:
    """
    Simulate bankroll paths using random walk with drift.

    Args:
        mu: Expected return per hand (in BB)
        sigma: Standard deviation per hand (in BB)
        initial_bankroll: Starting bankroll (in BB)
        n_hands: Number of hands to simulate
        n_simulations: Number of simulation paths

    Returns:
        Array of shape (n_simulations, n_hands + 1) with bankroll paths
    """
    np.random.seed(42)  # For reproducible results

    # Generate random returns for each hand
    returns = np.random.normal(mu, sigma, (n_simulations, n_hands))

    # Calculate cumulative returns
    cumulative_returns = np.cumsum(returns, axis=1)

    # Add initial bankroll
    bankroll_paths = np.column_stack(
        [
            np.full(n_simulations, initial_bankroll),
            initial_bankroll + cumulative_returns,
        ]
    )

    return bankroll_paths


def calculate_risk_of_ruin(
    bankroll_paths: np.ndarray, ruin_threshold: float = 0
) -> float:
    """
    Calculate the probability of bankroll going below ruin threshold.

    Args:
        bankroll_paths: Array of bankroll simulation paths
        ruin_threshold: Bankroll level considered "ruin"

    Returns:
        Probability of ruin (0.0 to 1.0)
    """
    min_bankrolls = np.min(bankroll_paths, axis=1)
    ruin_count = np.sum(min_bankrolls <= ruin_threshold)
    return ruin_count / len(bankroll_paths)


def calculate_drawdown_probabilities(
    bankroll_paths: np.ndarray, drawdown_thresholds: List[float]
) -> Dict[float, float]:
    """
    Calculate probabilities of various drawdown levels.

    Args:
        bankroll_paths: Array of bankroll simulation paths
        drawdown_thresholds: List of drawdown levels to analyze

    Returns:
        Dictionary mapping drawdown threshold to probability
    """
    drawdown_probs = {}

    for threshold in drawdown_thresholds:
        # Calculate maximum drawdown for each path
        running_max = np.maximum.accumulate(bankroll_paths, axis=1)
        drawdowns = running_max - bankroll_paths
        max_drawdowns = np.max(drawdowns, axis=1)

        # Count paths with drawdown >= threshold
        drawdown_count = np.sum(max_drawdowns >= threshold)
        drawdown_probs[threshold] = drawdown_count / len(bankroll_paths)

    return drawdown_probs


def run_stake_simulations(
    estimates_df: pd.DataFrame, config: Dict
) -> pd.DataFrame:
    """
    Run Monte Carlo simulations for all stake levels.

    Args:
        estimates_df: DataFrame with mu/sigma estimates by stake
        config: Simulation configuration dictionary

    Returns:
        DataFrame with simulation results for each stake
    """
    simulation_results = []

    for _, stake_row in estimates_df.iterrows():
        stake = stake_row["stake_text"]
        mu = stake_row["mu_bb_per_hand"]
        sigma = np.sqrt(stake_row["sigma2_bb_per_hand"])

        stake_results = {
            "stake_text": stake,
            "mu": mu,
            "sigma": sigma,
            "sigma2": stake_row["sigma2_bb_per_hand"],
        }

        # Run simulations for different time horizons
        for n_hands in config["time_horizons"]:
            # Simulate bankroll paths
            paths = simulate_bankroll_paths(
                mu=mu,
                sigma=sigma,
                initial_bankroll=config["current_bankroll_bb"],
                n_hands=n_hands,
                n_simulations=config["n_simulations"],
            )

            # Calculate risk metrics
            ror = calculate_risk_of_ruin(paths, ruin_threshold=0)
            drawdown_probs = calculate_drawdown_probabilities(
                paths, config["drawdown_thresholds"]
            )

            # Final bankroll statistics
            final_bankrolls = paths[:, -1]

            stake_results[f"ror_{n_hands}h"] = ror
            stake_results[f"final_mean_{n_hands}h"] = np.mean(final_bankrolls)
            stake_results[f"final_std_{n_hands}h"] = np.std(final_bankrolls)
            stake_results[f"final_p10_{n_hands}h"] = np.percentile(
                final_bankrolls, 10
            )
            stake_results[f"final_p90_{n_hands}h"] = np.percentile(
                final_bankrolls, 90
            )

            # Store drawdown probabilities
            for dd_threshold, dd_prob in drawdown_probs.items():
                stake_results[f"dd_{dd_threshold}bb_{n_hands}h"] = dd_prob

        simulation_results.append(stake_results)

    return pd.DataFrame(simulation_results)


def calculate_bankroll_requirements(
    estimates_df: pd.DataFrame, risk_tolerance: float = 0.05
) -> pd.DataFrame:
    """
    Calculate recommended bankroll requirements for each stake.

    Args:
        estimates_df: DataFrame with estimates
        risk_tolerance: Acceptable risk of ruin level

    Returns:
        DataFrame with bankroll recommendations
    """
    requirements = []

    for _, row in estimates_df.iterrows():
        stake = row["stake_text"]
        mu = row["mu_bb_per_hand"]
        sigma = np.sqrt(row["sigma2_bb_per_hand"])

        # Conservative bankroll estimate using Kelly-derived formula
        if mu > 0 and sigma > 0:
            # Approximate bankroll requirement for given RoR
            z_score = abs(stats.norm.ppf(risk_tolerance))
            required_bb = (z_score * sigma / mu) ** 2

            # Cap at reasonable limits
            required_bb = min(required_bb, 10000)  # Max 10k BB
            required_bb = max(required_bb, 1000)  # Min 1k BB
        else:
            required_bb = 5000  # Default for break-even or losing players

        requirements.append(
            {
                "stake_text": stake,
                "required_bankroll_bb": required_bb,
                "required_buyins": required_bb / 100,  # Assuming 100BB buyins
                "mu": mu,
                "sigma": sigma,
            }
        )

    return pd.DataFrame(requirements)
