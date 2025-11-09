"""
Goal A - Unified September Log

Merge September sessions from two sources:
- Results_Sept25_26 (new format)
- 2025_Results (old format, Sept rows only)

Output: Combined September P&L with hours, net, hourly, win rate
"""

import os
import pandas as pd
import requests
from io import StringIO
from typing import Optional
from dotenv import load_dotenv
import re


def extract_sheet_id_from_url(url: str) -> str:
    """
    Extract the sheet ID from a Google Sheets URL.

    Args:
        url: Full Google Sheets URL

    Returns:
        The sheet ID

    Examples:
        >>> extract_sheet_id_from_url(
        ...     "https://docs.google.com/spreadsheets/d/ABC123/edit"
        ... )
        'ABC123'
    """
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    raise ValueError(f"Could not extract sheet ID from URL: {url}")


def load_google_sheet_csv(sheet_id: str, gid: str = "0") -> pd.DataFrame:
    """
    Load a Google Sheet as CSV using the export URL.

    Args:
        sheet_id: The Google Sheet ID from the URL
        gid: The specific sheet/tab ID (default "0" for first sheet)

    Returns:
        DataFrame with the sheet data

    Note:
        Sheet must be set to "Anyone with link can view" for this to work
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    response = requests.get(url)
    response.raise_for_status()

    return pd.read_csv(StringIO(response.text))


def load_results_sept25_26(
    sheet_id: str, gid: Optional[str] = None
) -> pd.DataFrame:
    """
    Load the Results_Sept25_26 sheet (new format).

    Expected columns: date, room, stake_text, buyins_usd, cashouts_usd,
                      hours_played, straddle_exposure, etc.
    """
    df = load_google_sheet_csv(sheet_id, gid or "0")

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Calculate net for each session
    df["net_usd"] = df["cashouts_usd"] - df["buyins_usd"]

    return df


def load_2025_results_sept_only(
    sheet_id: str, gid: Optional[str] = None
) -> pd.DataFrame:
    """
    Load the 2025_Results sheet and filter for September rows only.

    This likely has different column names, so we'll need to map them
    to the canonical schema.
    """
    df = load_google_sheet_csv(sheet_id, gid or "0")

    # Convert date column (adjust column name as needed)
    date_col = "date" if "date" in df.columns else df.columns[0]
    df["date"] = pd.to_datetime(df[date_col])

    # Filter for September 2025
    sept_mask = (df["date"].dt.year == 2025) & (df["date"].dt.month == 9)
    df_sept = df[sept_mask].copy()

    return df_sept


def normalize_to_canonical_schema(
    df: pd.DataFrame, source: str = "unknown"
) -> pd.DataFrame:
    """
    Normalize any source dataframe to canonical schema.

    Required columns in output:
    - date, room, stake_text, buyins_usd, cashouts_usd, hours_played, net_usd
    """
    # TODO: Map column names based on source
    # This will depend on what the actual columns look like

    canonical = pd.DataFrame()
    canonical["date"] = df["date"]
    canonical["source"] = source

    # Add other columns with fallbacks
    # canonical['room'] = df.get('room', df.get('location', 'Unknown'))
    # etc.

    return canonical


def merge_september_sessions(
    new_format_df: pd.DataFrame, old_format_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Combine September sessions from both sources.

    Returns:
        DataFrame with all September sessions, sorted by date
    """
    # Ensure both have the same schema
    new_normalized = normalize_to_canonical_schema(
        new_format_df, source="Sept25_26"
    )
    old_normalized = normalize_to_canonical_schema(
        old_format_df, source="2025_Results"
    )

    # Combine
    combined = pd.concat([new_normalized, old_normalized], ignore_index=True)

    # Sort by date
    combined = combined.sort_values("date").reset_index(drop=True)

    return combined


def compute_september_summary(df: pd.DataFrame) -> dict:
    """
    Calculate key September metrics.

    Returns:
        Dict with total_hours, total_net, hourly_rate, etc.
    """
    summary = {
        "total_sessions": len(df),
        "total_hours": df["hours_played"].sum(),
        "total_net": df["net_usd"].sum(),
        "total_buyins": df["buyins_usd"].sum(),
        "total_cashouts": df["cashouts_usd"].sum(),
    }

    summary["hourly_rate"] = (
        summary["total_net"] / summary["total_hours"]
        if summary["total_hours"] > 0
        else 0
    )
    summary["roi"] = (
        (summary["total_net"] / summary["total_buyins"] * 100)
        if summary["total_buyins"] > 0
        else 0
    )

    return summary


def main():
    """
    Main workflow for Goal A.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get the Google Sheets URL from environment variable
    sheets_url = os.getenv("POKER_SHEETS_URL")
    if not sheets_url:
        raise ValueError(
            "POKER_SHEETS_URL not found in .env file. "
            "Please add it to your .env file."
        )

    # Extract sheet ID from URL
    sheet_id = extract_sheet_id_from_url(sheets_url)
    print(f"Using sheet ID: {sheet_id}")

    # GID values for different tabs (update these based on your actual tabs)
    # You can find GID in the URL when you click on a tab: ...#gid=123456
    RESULTS_SEPT25_26_GID = "0"  # Update with actual GID
    RESULTS_2025_GID = "0"  # Update with actual GID for the 2025_Results tab

    print("Loading Results_Sept25_26...")
    new_format = load_results_sept25_26(sheet_id, RESULTS_SEPT25_26_GID)
    print(f"  Loaded {len(new_format)} rows")

    print("Loading 2025_Results (September only)...")
    old_format = load_2025_results_sept_only(sheet_id, RESULTS_2025_GID)
    print(f"  Loaded {len(old_format)} September rows")

    print("Merging September sessions...")
    combined = merge_september_sessions(new_format, old_format)
    print(f"  Combined total: {len(combined)} sessions")

    print("\nSeptember Summary:")
    summary = compute_september_summary(combined)
    for key, value in summary.items():
        if isinstance(value, float):
            print(
                f"  {key}: ${value:,.2f}"
                if "usd" in key or "net" in key
                else f"  {key}: {value:.2f}"
            )
        else:
            print(f"  {key}: {value}")

    # Save combined data
    output_path = "../data/interim/september_combined.csv"
    combined.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
