"""Paper Section 4: cancelling signatures, invariant pair counts, d3=1."""
from hocomb import Swap, System, apply, matched_trades
from hocomb.switches import signature
from .common import format_pair_counts, print_result


def run() -> dict:
    XA = System.create([
        (1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6)
    ], universe=range(1, 7))
    XB = System.create([
        (1, 2, 4), (1, 3, 5), (2, 3, 6), (4, 5, 6)
    ], universe=range(1, 7))
    first = Swap(0, 1, 3, 4)
    second = Swap(2, 3, 4, 3)
    provisional = apply(XA, first)
    finish = apply(provisional, second)
    assert finish == XB
    sig1, sig2 = signature(XA, first), signature(XA, second)
    assert sig1.opposite() == sig2
    assert XA.equivalent_low_order(XB)
    assert XA.distance(XB, 3) == 1.
    alternatives = matched_trades(XA, h=3)
    assert any(t.result == XB for t in alternatives)
    return {
        "paper": "Section 4, four-record zero-sum trade",
        "XA": XA.readable(),
        "after_first_swap": provisional.readable(),
        "XB": XB.readable(),
        "first_swap": vars(first),
        "second_swap": vars(second),
        "signatures_cancel": sig1.opposite() == sig2,
        "same_quotas": XA.quotas() == XB.quotas(),
        "same_pair_counts": XA.pair_counts() == XB.pair_counts(),
        "same_singletons": XA.singleton_counts() == XB.singleton_counts(),
        "pair_counts": format_pair_counts(XA),
        "third_order_support_overlap": len(
            set(XA.higher_counts(3)) & set(XB.higher_counts(3))
        ),
        "L1_h3": sum(
            abs(XA.higher_counts(3)[s] - XB.higher_counts(3)[s])
            for s in XA.higher_counts(3).keys() | XB.higher_counts(3).keys()
        ),
        "T3": XA.total_h(3),
        "d3": XA.distance(XB, 3),
        "distinct_nontrivial_matched_outputs_found": len(alternatives),
    }


if __name__ == "__main__":
    print_result(run())
