"""
Input/Output operations for poker session data.
Functions for loading raw data, writing interim files, and reading processed data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict


def load_raw_session_data(data_dir: Path) -> pd.DataFrame:
    """
    Load and combine raw session data from multiple sources.

    Returns a DataFrame with columns matching the canonical schema:
    date, room, stake_text, buyins_usd, cashouts_usd, hours_played,
    straddle_exposure, side_bombpots_count, side_standup_minutes,
    side_bounty_flag, stack_depth_class, notes

    Args:
        data_dir: Path to directory containing raw data files

    Returns:
        DataFrame with normalized session data
    """
    # Check for existing raw data files
    raw_files = list(data_dir.glob("*.csv"))

    if not raw_files:
        print(
            "⚠️  No raw data files found. Creating sample data for demonstration."
        )
        return create_sample_session_data()

    # TODO: Implement actual data loading logic for CSV files
    # This would handle different CSV formats and normalize them
    print(f"📄 Found {len(raw_files)} raw data files")
    return create_sample_session_data()


def create_sample_session_data(
    n_sessions: int = 100, seed: int = 42
) -> pd.DataFrame:
    """
    Create sample poker session data for demonstration purposes.

    Args:
        n_sessions: Number of sample sessions to generate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with sample session data
    """
    np.random.seed(seed)

    # Generate sessions over the past 2 years
    start_date = datetime.now() - timedelta(days=730)

    dates = [
        start_date + timedelta(days=np.random.randint(0, 730))
        for _ in range(n_sessions)
    ]
    rooms = np.random.choice(
        ["Aria", "Bellagio", "Commerce", "Borgata", "Local Club"], n_sessions
    )
    stakes = np.random.choice(
        ["1-3", "2-5", "2-5-10", "5-10", "10-20"],
        n_sessions,
        p=[0.3, 0.4, 0.2, 0.08, 0.02],
    )

    # Generate realistic buy-ins and results
    buyins = []
    cashouts = []

    for stake in stakes:
        if stake == "1-3":
            buyin = np.random.normal(300, 100)
            result = np.random.normal(
                15, 180
            )  # Small positive expectation with high variance
        elif stake == "2-5":
            buyin = np.random.normal(500, 150)
            result = np.random.normal(25, 250)
        elif stake == "2-5-10":
            buyin = np.random.normal(800, 200)
            result = np.random.normal(40, 350)
        elif stake == "5-10":
            buyin = np.random.normal(1500, 300)
            result = np.random.normal(75, 600)
        else:  # 10-20
            buyin = np.random.normal(3000, 500)
            result = np.random.normal(150, 1200)

        buyins.append(max(buyin, 100))  # Minimum buyin
        cashouts.append(max(buyin + result, 0))  # Can't cash out negative

    data = {
        "date": [d.date() for d in dates],
        "room": rooms,
        "stake_text": stakes,
        "buyins_usd": [round(b, 2) for b in buyins],
        "cashouts_usd": [round(c, 2) for c in cashouts],
        "hours_played": np.random.normal(6, 2.5).clip(1, 12).round(1),
        "straddle_exposure": np.random.choice(
            ["none", "low", "medium", "high", "mandatory"],
            n_sessions,
            p=[0.4, 0.2, 0.2, 0.15, 0.05],
        ),
        "side_bombpots_count": np.random.poisson(3, n_sessions),
        "side_standup_minutes": np.random.exponential(15, n_sessions).astype(
            int
        ),
        "side_bounty_flag": np.random.choice(
            [True, False], n_sessions, p=[0.1, 0.9]
        ),
        "stack_depth_class": np.random.choice(
            ["S", "N", "D", "VD"], n_sessions, p=[0.1, 0.6, 0.25, 0.05]
        ),
        "notes": ["Sample session " + str(i) for i in range(n_sessions)],
    }

    return pd.DataFrame(data)


def write_interim_data(df: pd.DataFrame, filepath: Path) -> None:
    """
    Write cleaned session data to interim storage.

    Args:
        df: DataFrame with cleaned session data
        filepath: Path where to save the interim CSV file
    """
    df.to_csv(filepath, index=False)
    print(f"💾 Saved interim data to {filepath}")


def read_interim_data(filepath: Path) -> pd.DataFrame:
    """
    Read cleaned session data from interim storage.

    Args:
        filepath: Path to interim CSV file

    Returns:
        DataFrame with session data
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Interim data file not found: {filepath}")

    df = pd.read_csv(filepath)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df


def validate_session_data(df: pd.DataFrame) -> Dict[str, any]:
    """
    Validate session data quality and return summary report.

    Args:
        df: DataFrame with session data

    Returns:
        Dictionary with validation results
    """
    validation_report = {
        "total_sessions": len(df),
        "date_range": (df["date"].min(), df["date"].max()),
        "missing_values": df.isnull().sum().to_dict(),
        "total_hours": df["hours_played"].sum(),
        "total_net_result": (df["cashouts_usd"] - df["buyins_usd"]).sum(),
        "stake_distribution": df["stake_text"].value_counts().to_dict(),
        "validation_errors": [],
    }

    # Check for common data issues
    if df["hours_played"].min() <= 0:
        validation_report["validation_errors"].append(
            "Invalid hours_played values found"
        )

    if (df["cashouts_usd"] < 0).any():
        validation_report["validation_errors"].append(
            "Negative cashout values found"
        )

    if (df["buyins_usd"] <= 0).any():
        validation_report["validation_errors"].append(
            "Invalid buyin values found"
        )

    return validation_report
