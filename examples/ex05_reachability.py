"""Paper Section 6: distinct operation and intermediate-state constraints."""
from hocomb import System, find_path, maximize_occurrences
from hocomb.feasibility import support_pairs
from .common import print_result


def run() -> dict:
    XA = System.create([
        (1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6),
    ], universe=range(1, 7))
    XB = System.create([
        (1, 2, 4), (1, 3, 5), (2, 3, 6), (4, 5, 6),
    ], universe=range(1, 7))
    unrestricted = find_path(XA, XB, "switch", max_depth=2)
    strict_switch = find_path(
        XA, XB, "switch", strict_intermediate=True, max_depth=2,
    )
    strict_trade = find_path(
        XA, XB, "zero_sum_trade", strict_intermediate=True, max_depth=1,
    )
    assert unrestricted.found and unrestricted.transitions == 2
    assert not strict_switch.found and not strict_switch.truncated
    assert strict_trade.found and strict_trade.transitions == 1
    exact = maximize_occurrences(
        XA.universe, XA.quotas(), XA.size_distribution(),
        required_pairs=support_pairs(XA), target=(1, 2, 4),
        exact_pairs=XA.pair_counts(),
        exact_singletons=XA.singleton_counts(),
    )
    assert exact.feasible and exact.max_count >= 1
    return {
        "paper": "Section 6, operation reachability and finite feasibility",
        "general_switch_endpoint": {
            "found": unrestricted.found,
            "transitions": unrestricted.transitions,
            "path": [state.readable() for state in unrestricted.path],
            "visited": unrestricted.visited_states,
        },
        "every_switch_must_preserve_pair_counts": {
            "found": strict_switch.found,
            "visited": strict_switch.visited_states,
            "truncated": strict_switch.truncated,
        },
        "one_zero_sum_trade_must_preserve_pair_counts": {
            "found": strict_trade.found,
            "transitions": strict_trade.transitions,
            "path": [state.readable() for state in strict_trade.path],
        },
        "finite_integer_model_with_exact_pair_counts": {
            "feasible": exact.feasible,
            "max_t124": exact.max_count,
            "witness": exact.witness.readable() if exact.witness else None,
            "integer_states": exact.states_explored,
        },
    }


if __name__ == "__main__":
    print_result(run())
