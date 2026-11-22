"""Paper Section 3: singleton/pair cross-stratum swap, E=4 -> 0."""
from hocomb import HardConstraints, LossSpec, Swap, System, apply, local_loss_delta
from hocomb.core import pair
from .common import format_pair_counts, format_singletons, print_result


def run() -> dict:
    start = System.create([(1,), (2, 3)], universe=range(1, 4))
    constraints = HardConstraints.from_system(start)
    target = LossSpec(
        {pair(1, 2): 1., pair(1, 3): 0., pair(2, 3): 0.},
        {1: 0., 2: 0., 3: 1.},
    )
    move = Swap(0, 1, 1, 3)
    delta = local_loss_delta(start, move, target)
    finish = apply(start, move)
    constraints.require(finish)
    assert (target.loss(start), target.loss(finish), delta) == (4., 0., -4.)
    return {
        "paper": "Section 3, cross-stratum 2-switch and exact delta",
        "start": start.readable(),
        "finish": finish.readable(),
        "sizes_preserved": start.sizes() == finish.sizes(),
        "quotas_preserved": start.quotas() == finish.quotas(),
        "initial_pairs": format_pair_counts(start),
        "final_pairs": format_pair_counts(finish),
        "initial_singletons": format_singletons(start),
        "final_singletons": format_singletons(finish),
        "initial_loss": target.loss(start),
        "final_loss": target.loss(finish),
        "predicted_local_delta": delta,
        "observed_full_delta": target.loss(finish) - target.loss(start),
    }


if __name__ == "__main__":
    print_result(run())
