"""
Poker Bankroll Decision System

Turn messy live poker logs into win rate and variance estimates,
run risk of ruin and drawdown simulations, and output clear stake
recommendations for the current bankroll and conditions.
"""

from .poker_bankroll import PokerBankrollAnalyzer, quick_analysis
from .io_ops import load_raw_session_data, create_sample_session_data
from .enrich import enrich_session_data
from .estimate import estimate_mu_sigma_by_stake
from .simulate import run_stake_simulations
from .recommend import generate_stake_recommendations

__version__ = "0.1.0"
__author__ = "Poker RoR Team"

__all__ = [
    "PokerBankrollAnalyzer",
    "quick_analysis",
    "load_raw_session_data",
    "create_sample_session_data",
    "enrich_session_data",
    "estimate_mu_sigma_by_stake",
    "run_stake_simulations",
    "generate_stake_recommendations",
]
