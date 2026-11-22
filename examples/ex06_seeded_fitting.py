"""Extended experiment based on Section 3: max-flow init + seeded fitting.

This particular mixed-size target instance is an ADDITIONAL software
benchmark, not an example copied from the submitted TeX manuscript.
"""
from hocomb import LossSpec, System, feasible_initialization, fit_residuals
from .common import print_result


def run_with_trace() -> tuple[dict, tuple[dict, ...]]:
    reference = System.create([
        (1,), (2, 3), (4, 5, 6), (1, 4, 6), (2, 5), (3,)
    ], universe=range(1, 7))
    targets = LossSpec.from_reference(reference)
    initial = feasible_initialization(
        reference.universe, reference.sizes(), reference.quotas()
    )
    result = fit_residuals(
        initial, targets, iterations=650, seed=2026,
        residual_proposal_probability=0.75,
        start_temperature=0.5, end_temperature=0.02,
    )
    assert result.initial_loss > result.best_loss
    assert result.best_loss == 0.0
    assert reference.quotas() == result.best.quotas()
    assert reference.sizes() == result.best.sizes()
    return {
        "paper": "Section 3 algorithm, ADDITIONAL mixed-size seeded benchmark",
        "not_from_original_paper_example": True,
        "seed": 2026,
        "reference": reference.readable(),
        "maxflow_initialized_system": initial.readable(),
        "best_system": result.best.readable(),
        "initial_loss": result.initial_loss,
        "best_loss": result.best_loss,
        "iterations_executed": len(result.trajectory) - 1,
        "accepted_transitions": sum(
            item["accepted"] for item in result.trajectory[1:]
        ),
        "exact_local_delta_checked_at_every_accepted_swap": True,
    }, result.trajectory


def run() -> dict:
    report, _ = run_with_trace()
    return report


if __name__ == "__main__":
    print_result(run())
