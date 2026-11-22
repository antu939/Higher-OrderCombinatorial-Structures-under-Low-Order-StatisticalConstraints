"""Paper Section 5: induction -> provisional anchor -> residual refit -> commit."""
from hocomb import Goal, LossSpec, System, construct_directed
from hocomb.core import pair, sub_system, verify_residual_equivalence
from hocomb.directed import paper_directed_trace
from .common import print_result


def run() -> dict:
    trace = paper_directed_trace()
    x0, interim, committed = (
        trace["reference"], trace["induced"], trace["accepted"]
    )
    targets = LossSpec.from_reference(x0)
    target_pairs = (pair(2, 3), pair(2, 4), pair(3, 5), pair(4, 5))
    r1 = trace["residual_first"]
    frozen_ids = trace["frozen_first"]
    free_ids = set(range(len(interim.blocks))) - frozen_ids
    free_before = sub_system(interim, free_ids)
    free_after = sub_system(committed, free_ids)
    residual_spec = r1.remaining_loss_targets
    assert r1.remaining_quotas == {1: 1, 2: 1, 3: 2, 4: 1, 5: 2, 6: 2}
    assert [residual_spec.pair_targets[p] for p in target_pairs] == [1, 0, 1, 1]
    assert [free_before.pair_counts()[p] for p in target_pairs] == [0, 1, 2, 0]
    assert residual_spec.loss(free_before) == 4.
    assert residual_spec.loss(free_after) == 0.
    assert verify_residual_equivalence(committed, (0, 3), targets)

    # Unlike the fixed paper witness, this generic routine searches
    # induction moves and refit paths without hard-coding the answer.
    auto = construct_directed(
        x0, (
            Goal(frozenset((1, 2, 4))),
            Goal(frozenset((4, 5, 6))),
        ),
        mode="exact", induction_budget=200,
        refit_depth=3, refit_states=3000,
    )
    assert auto.status == "SUCCESS"
    assert x0.equivalent_low_order(auto.final)
    return {
        "paper": "Section 5, complete constructive example",
        "reference": x0.readable(),
        "after_induction_NOT_COMMITTED": interim.readable(),
        "after_refit_COMMITTED": committed.readable(),
        "E_initial": trace["initial_loss"],
        "E_provisional": trace["induction_loss"],
        "E_committed": trace["commit_loss"],
        "four_affected_pairs": [",".join(map(str, p)) for p in target_pairs],
        "pair_increments_induction": [
            interim.pair_counts()[p] - x0.pair_counts()[p] for p in target_pairs
        ],
        "pair_increments_refit": [
            committed.pair_counts()[p] - interim.pair_counts()[p] for p in target_pairs
        ],
        "residual_pair_targets_after_first_anchor": [
            residual_spec.pair_targets[p] for p in target_pairs
        ],
        "residual_actual_before_refit": [
            free_before.pair_counts()[p] for p in target_pairs
        ],
        "remaining_quotas_after_first_freeze": {
            str(k): v for k, v in r1.remaining_quotas.items()
        },
        "remaining_quotas_after_second_freeze": {
            str(k): v for k, v in trace["residual_second"].remaining_quotas.items()
        },
        "frozen_h3_variation_bound_before_second_freeze":
            trace["frozen_distance_bound_first"],
        "frozen_h3_variation_bound_after_second_freeze":
            trace["frozen_distance_bound_second"],
        "targets": {"124": committed.count((1, 2, 4)),
                    "456": committed.count((4, 5, 6))},
        "independent_general_constructor": {
            "status": auto.status,
            "result": auto.final.readable(),
            "attempted_inductions": auto.attempted_inductions,
            "commit_trace": list(auto.accepted_steps),
        },
    }


if __name__ == "__main__":
    print_result(run())
