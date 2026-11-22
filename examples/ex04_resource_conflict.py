"""Paper Section 6: a graph-theoretic triangle forbidden by finite resources."""
from hocomb import System, clique_candidates, maximize_occurrences
from hocomb.feasibility import support_pairs
from .common import print_result


def run() -> dict:
    XC = System.create(
        [("a", "b", "d"), ("a", "c"), ("b", "c")],
        universe=("a", "b", "c", "d"),
    )
    support = support_pairs(XC)
    triangles = clique_candidates(XC.universe, support, 3)
    target = ("a", "b", "c")
    assert target in triangles
    strict = maximize_occurrences(
        XC.universe, XC.quotas(), XC.size_distribution(),
        required_pairs=support, target=target,
    )
    assert strict.feasible and strict.max_count == 0
    # EXTRA CONTROL (not stated as a paper result):
    # Removing the positive-support coverage makes the triangle possible.
    relaxed = maximize_occurrences(
        XC.universe, XC.quotas(), XC.size_distribution(), target=target,
    )
    assert relaxed.feasible and relaxed.max_count >= 1
    return {
        "paper": "Section 6, triangle candidate versus finite feasibility",
        "initial_system": XC.readable(),
        "support_edges": [list(p) for p in sorted(support)],
        "triangle_candidates": [list(t) for t in triangles],
        "quotas": dict(XC.quotas()),
        "size_counts": {str(k): v for k, v in XC.size_distribution().items()},
        "with_required_coverage": {
            "feasible": strict.feasible,
            "U_abc": strict.max_count,
            "one_witness": strict.witness.readable(),
            "explored_integer_states": strict.states_explored,
        },
        "without_required_coverage_EXTRA_CONTROL": {
            "feasible": relaxed.feasible,
            "U_abc": relaxed.max_count,
            "one_witness": relaxed.witness.readable(),
        },
    }


if __name__ == "__main__":
    print_result(run())
