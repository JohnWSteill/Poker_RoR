"""
Data enrichment functions for poker session analysis.
Derive features that matter for variance: straddle exposure, stack depth buckets, and side game flags.
"""

import pandas as pd
import numpy as np
from typing import Dict


def derive_effective_bb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate effective big blind size from stake_text.

    Examples:
    '1-3' -> 3
    '2-5' -> 5
    '2-5-10' -> 5 (main game BB, straddle handled separately)

    Args:
        df: DataFrame with stake_text column

    Returns:
        DataFrame with added effective_bb column
    """
    df = df.copy()

    def extract_bb(stake_text: str) -> float:
        """Extract big blind from stake text."""
        parts = stake_text.split("-")
        if len(parts) >= 2:
            return float(parts[1])
        return 1.0  # fallback

    df["effective_bb"] = df["stake_text"].apply(extract_bb)
    return df


def tag_straddle_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert straddle exposure to numerical impact factor.

    This affects both variance and expected stack depth.

    Args:
        df: DataFrame with straddle_exposure column

    Returns:
        DataFrame with added straddle_multiplier and effective_bb_with_straddle columns
    """
    df = df.copy()

    straddle_multipliers = {
        "none": 1.0,
        "low": 1.1,  # Occasional straddle, small impact
        "medium": 1.25,  # Regular straddling, moderate impact
        "high": 1.5,  # Frequent straddling, high impact
        "mandatory": 2.0,  # Always straddled, double impact
    }

    df["straddle_multiplier"] = df["straddle_exposure"].map(
        straddle_multipliers
    )
    df["effective_bb_with_straddle"] = (
        df["effective_bb"] * df["straddle_multiplier"]
    )

    return df


def tag_side_games(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create composite side game exposure metric.

    Side games (bomb pots, stand-up games, bounties) increase variance
    and can significantly impact session results.

    Args:
        df: DataFrame with side game columns

    Returns:
        DataFrame with added side game intensity columns
    """
    df = df.copy()

    # Normalize side game exposure (0-1 scale)
    df["bombpot_intensity"] = (
        df["side_bombpots_count"] / df["hours_played"]
    ).clip(0, 5) / 5
    df["standup_intensity"] = (
        df["side_standup_minutes"] / (df["hours_played"] * 60)
    ).clip(0, 0.5) / 0.5
    df["bounty_intensity"] = df["side_bounty_flag"].astype(float)

    # Composite side game score (0-3 scale)
    df["side_game_intensity"] = (
        df["bombpot_intensity"]
        + df["standup_intensity"]
        + df["bounty_intensity"]
    )

    return df


def bucket_stack_depth_effect(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert stack depth class to numerical effective multipliers.

    Stack depth affects both win rate and variance:
    - Shallow (S): Lower variance, potentially higher win rate for skilled players
    - Normal (N): Baseline
    - Deep (D): Higher variance, skill edge amplified
    - Very Deep (VD): Highest variance, significant skill edge for competent players

    Args:
        df: DataFrame with stack_depth_class column

    Returns:
        DataFrame with added depth effect columns
    """
    df = df.copy()

    depth_effects = {
        "S": {"variance_mult": 0.7, "skill_mult": 1.1},  # S <=120bb
        "N": {"variance_mult": 1.0, "skill_mult": 1.0},  # N 120-200bb
        "D": {"variance_mult": 1.4, "skill_mult": 1.15},  # D 200-320bb
        "VD": {"variance_mult": 2.0, "skill_mult": 1.3},  # VD >320bb
    }

    df["depth_variance_mult"] = df["stack_depth_class"].map(
        lambda x: depth_effects[x]["variance_mult"]
    )
    df["depth_skill_mult"] = df["stack_depth_class"].map(
        lambda x: depth_effects[x]["skill_mult"]
    )

    return df


def calculate_session_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-session performance metrics in various normalizations.

    Args:
        df: DataFrame with basic session data

    Returns:
        DataFrame with added performance metrics
    """
    df = df.copy()

    # Basic results
    df["net_result"] = df["cashouts_usd"] - df["buyins_usd"]
    df["roi"] = df["net_result"] / df["buyins_usd"]  # Return on investment

    # Hourly rates
    df["hourly_rate"] = df["net_result"] / df["hours_played"]

    # Big blind rates (key poker metric)
    df["bb_per_hour"] = df["hourly_rate"] / df["effective_bb_with_straddle"]
    df["bb_per_session"] = df["net_result"] / df["effective_bb_with_straddle"]

    # Risk-adjusted metrics
    df["buyins_risked"] = df["buyins_usd"] / (
        100 * df["effective_bb_with_straddle"]
    )
    df["bb_per_buyin_risked"] = df["bb_per_session"] / df["buyins_risked"]

    return df


def estimate_hands_per_hour() -> Dict[str, float]:
    """
    Estimate hands per hour by game conditions.

    These are typical live poker rates adjusted for game conditions.

    Returns:
        Dictionary with hands per hour adjustments
    """
    return {
        "live_poker_base": 30,  # Standard live poker rate
        "straddle_adjustment": -2,  # Straddling slows the game
        "deep_stack_adjustment": -3,  # Deep play slows decisions
        "side_game_adjustment": -5,  # Side games slow main action
    }


def calculate_hands_played(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate hands played per session based on conditions.

    Args:
        df: DataFrame with session data and enrichment features

    Returns:
        DataFrame with added hands played metrics
    """
    df = df.copy()

    hands_config = estimate_hands_per_hour()
    base_rate = hands_config["live_poker_base"]

    # Adjust for game conditions
    straddle_adj = df["straddle_multiplier"].apply(
        lambda x: hands_config["straddle_adjustment"] if x > 1.1 else 0
    )
    depth_adj = df["stack_depth_class"].apply(
        lambda x: (
            hands_config["deep_stack_adjustment"] if x in ["D", "VD"] else 0
        )
    )
    side_adj = df["side_game_intensity"].apply(
        lambda x: hands_config["side_game_adjustment"] * min(x, 1)
    )

    df["hands_per_hour"] = base_rate + straddle_adj + depth_adj + side_adj
    df["hands_played"] = (
        (df["hands_per_hour"] * df["hours_played"]).round().astype(int)
    )

    # Calculate per-hand metrics
    df["bb_per_hand"] = df["bb_per_session"] / df["hands_played"]
    df["usd_per_hand"] = df["net_result"] / df["hands_played"]

    return df


def enrich_session_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all enrichment functions to session data.

    Args:
        df: Raw session DataFrame

    Returns:
        Fully enriched DataFrame with all derived features
    """
    return (
        df.pipe(derive_effective_bb)
        .pipe(tag_straddle_impact)
        .pipe(tag_side_games)
        .pipe(bucket_stack_depth_effect)
        .pipe(calculate_session_metrics)
        .pipe(calculate_hands_played)
    )
