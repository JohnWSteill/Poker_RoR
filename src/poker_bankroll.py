"""
Main module for Poker Bankroll Decision System.
Coordinates the workflow: Import -> Enrich -> Estimate -> Simulate -> Report
"""

import yaml
from pathlib import Path
import pandas as pd

from .io_ops import load_raw_session_data, validate_session_data
from .enrich import enrich_session_data
from .estimate import estimate_mu_sigma_by_stake, bootstrap_confidence_intervals
from .simulate import run_stake_simulations
from .recommend import generate_stake_recommendations, create_decision_memo


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class PokerBankrollAnalyzer:
    """Main class for poker bankroll analysis."""

    def __init__(self, project_root: Path):
        """
        Initialize the analyzer.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root)
        self.data_raw = self.project_root / "data" / "raw"
        self.data_interim = self.project_root / "data" / "interim"
        self.data_processed = self.project_root / "data" / "processed"
        self.config_dir = self.project_root / "config"

        # Load configuration
        config_file = self.config_dir / "settings.yaml"
        if config_file.exists():
            self.config = load_config(config_file)
        else:
            # Default configuration
            self.config = {
                "simulation": {
                    "n_simulations": 10000,
                    "time_horizons": [500, 1000, 2500, 5000, 10000],
                    "current_bankroll_bb": 5000,
                    "risk_tolerance": 0.05,
                    "drawdown_thresholds": [10, 20, 30, 50],
                    "kelly_fraction": 0.25,
                }
            }

        # Storage for analysis results
        self.raw_sessions = None
        self.enriched_sessions = None
        self.stake_estimates = None
        self.simulation_results = None
        self.recommendations = None

    def import_data(self) -> pd.DataFrame:
        """Import and validate raw session data."""
        print("🔄 Step 1: Importing session data...")

        self.raw_sessions = load_raw_session_data(self.data_raw)

        # Validate data quality
        validation_report = validate_session_data(self.raw_sessions)
        print(f"✅ Loaded {validation_report['total_sessions']} sessions")
        print(
            f"📅 Date range: {validation_report['date_range'][0]} to {validation_report['date_range'][1]}"
        )

        if validation_report["validation_errors"]:
            print("⚠️ Validation errors found:")
            for error in validation_report["validation_errors"]:
                print(f"  - {error}")

        return self.raw_sessions

    def enrich_data(self) -> pd.DataFrame:
        """Enrich session data with derived features."""
        print("🔄 Step 2: Enriching session data...")

        if self.raw_sessions is None:
            raise ValueError("Must import data first")

        self.enriched_sessions = enrich_session_data(self.raw_sessions)

        new_features = len(self.enriched_sessions.columns) - len(
            self.raw_sessions.columns
        )
        print(f"✅ Added {new_features} derived features")

        return self.enriched_sessions

    def estimate_parameters(self) -> pd.DataFrame:
        """Estimate win rates and variance by stake."""
        print("🔄 Step 3: Estimating parameters...")

        if self.enriched_sessions is None:
            raise ValueError("Must enrich data first")

        self.stake_estimates = estimate_mu_sigma_by_stake(
            self.enriched_sessions
        )

        # Add bootstrap confidence intervals
        bootstrap_ci = bootstrap_confidence_intervals(self.enriched_sessions)

        print(f"✅ Generated estimates for {len(self.stake_estimates)} stakes")
        print("📊 Bootstrap confidence intervals calculated")

        return self.stake_estimates

    def run_simulations(self) -> pd.DataFrame:
        """Run Monte Carlo simulations."""
        print("🔄 Step 4: Running simulations...")

        if self.stake_estimates is None:
            raise ValueError("Must estimate parameters first")

        self.simulation_results = run_stake_simulations(
            self.stake_estimates, self.config["simulation"]
        )

        n_simulations = self.config["simulation"]["n_simulations"]
        print(f"✅ Completed {n_simulations:,} simulations for each stake")

        return self.simulation_results

    def generate_recommendations(self) -> tuple[pd.DataFrame, str]:
        """Generate stake recommendations and decision memo."""
        print("🔄 Step 5: Generating recommendations...")

        if self.simulation_results is None:
            raise ValueError("Must run simulations first")

        # Generate recommendations
        self.recommendations = generate_stake_recommendations(
            self.simulation_results,
            self.config["simulation"]["current_bankroll_bb"],
            self.config["simulation"]["risk_tolerance"],
        )

        # Create decision memo
        decision_memo = create_decision_memo(
            self.recommendations,
            self.enriched_sessions,
            self.config["simulation"]["current_bankroll_bb"],
            self.config["simulation"],
        )

        print("✅ Generated stake recommendations and decision memo")

        return self.recommendations, decision_memo

    def run_full_analysis(self) -> dict:
        """Run the complete analysis workflow."""
        print("🚀 Starting full bankroll analysis...")
        print("=" * 50)

        # Run all steps
        self.import_data()
        self.enrich_data()
        self.estimate_parameters()
        self.run_simulations()
        recommendations, memo = self.generate_recommendations()

        print("\n" + "=" * 50)
        print("🎯 Analysis Complete!")

        return {
            "raw_sessions": self.raw_sessions,
            "enriched_sessions": self.enriched_sessions,
            "stake_estimates": self.stake_estimates,
            "simulation_results": self.simulation_results,
            "recommendations": self.recommendations,
            "decision_memo": memo,
        }

    def save_results(self, results: dict) -> None:
        """Save analysis results to files."""
        # Save interim data
        interim_file = self.data_interim / "enriched_sessions.csv"
        results["enriched_sessions"].to_csv(interim_file, index=False)

        # Save processed results
        processed_dir = self.data_processed
        processed_dir.mkdir(exist_ok=True)

        results["stake_estimates"].to_csv(
            processed_dir / "stake_estimates.csv", index=False
        )
        results["simulation_results"].to_csv(
            processed_dir / "simulation_results.csv", index=False
        )
        results["recommendations"].to_csv(
            processed_dir / "recommendations.csv", index=False
        )

        # Save decision memo
        memo_file = self.project_root / "bankroll_decision_memo.md"
        with open(memo_file, "w") as f:
            f.write(results["decision_memo"])

        print(f"💾 Results saved to {processed_dir}")
        print(f"📝 Decision memo saved to {memo_file}")


def quick_analysis(
    project_root: Path, current_bankroll_bb: float = 5000
) -> dict:
    """
    Run a quick analysis with minimal setup.

    Args:
        project_root: Path to project root
        current_bankroll_bb: Current bankroll in big blinds

    Returns:
        Dictionary with analysis results
    """
    analyzer = PokerBankrollAnalyzer(project_root)
    analyzer.config["simulation"]["current_bankroll_bb"] = current_bankroll_bb

    return analyzer.run_full_analysis()
