"""Reproducible research code for higher-order combinatorial structures."""
from .core import HardConstraints, LossSpec, ResidualBudget, System
from .switches import Swap, apply, all_swaps, local_loss_delta, matched_trades
from .baseline import feasible_initialization, fit_residuals
from .directed import Goal, construct_directed
from .feasibility import maximize_occurrences, clique_candidates
from .reachability import find_path

__all__ = [
    "System", "HardConstraints", "LossSpec", "ResidualBudget",
    "Swap", "apply", "all_swaps", "local_loss_delta", "matched_trades",
    "feasible_initialization", "fit_residuals", "Goal", "construct_directed",
    "maximize_occurrences", "clique_candidates", "find_path",
]
