from __future__ import annotations

import unittest
from itertools import combinations

from hocomb import HardConstraints, LossSpec, ResidualBudget, Swap, System, apply, all_swaps, local_loss_delta, matched_trades
from hocomb.core import pair, pairs, sub_system, verify_residual_equivalence
from hocomb.switches import count_delta, legal, signature


def example_a() -> System:
    return System.create([
        (1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6)
    ], universe=range(1, 7))


def example_b() -> System:
    return System.create([
        (1, 2, 4), (1, 3, 5), (2, 3, 6), (4, 5, 6)
    ], universe=range(1, 7))


class CoreTests(unittest.TestCase):
    def test_paper_h3_distance(self):
        a, b = example_a(), example_b()
        self.assertEqual(a.total_h(3), 4)
        self.assertEqual(b.total_h(3), 4)
        self.assertTrue(a.equivalent_low_order(b))
        self.assertEqual(a.distance(b, 3), 1.0)
        self.assertEqual(set(a.higher_counts(3)) & set(b.higher_counts(3)), set())
        self.assertEqual(a.quotas(), dict.fromkeys(range(1, 7), 2))

    def test_t_S_containment_not_just_exact_blocks(self):
        x = System.create([(1, 2, 3, 4), (1, 2, 3)], universe=range(1, 5))
        self.assertEqual(x.count((1, 2, 3)), 2)
        self.assertEqual(x.total_h(3), 5)
        self.assertEqual(x.higher_counts(3)[(1, 2, 3)], 2)

    def test_repeated_records_preserve_multiplicity(self):
        x = System.create([(1, 2, 3), (1, 2, 3)], universe=range(1, 4))
        self.assertEqual(x.count((1, 2, 3)), 2)
        self.assertEqual(x.total_h(3), 2)
        self.assertEqual(x.pair_counts()[pair(1, 2)], 2)
        self.assertEqual(len(x.blocks), 2)

    def test_empty_record_and_duplicate_element_rejected(self):
        with self.assertRaises(ValueError):
            System.create([(1, 1)])
        with self.assertRaises(ValueError):
            System.create([()])

    def test_loss_noninteger_target_and_residual_identity(self):
        x = System.create([(1,), (2, 3), (1, 2, 4)], universe=range(1, 5))
        spec = LossSpec(
            {p: (i + 0.25) for i, p in enumerate(pairs(x.universe))},
            {1: 0.7, 2: 0.2, 3: 0.4, 4: -0.1},
            {p: 1.0 + i / 4 for i, p in enumerate(pairs(x.universe))},
            {1: 2.0, 2: 1.0, 3: 3.0, 4: 0.5},
            0.8,
        )
        for size in range(len(x.blocks) + 1):
            for frozen in combinations(range(len(x.blocks)), size):
                self.assertTrue(verify_residual_equivalence(x, frozen, spec))
                budget = ResidualBudget.compute(x, frozen, spec)
                free = sub_system(x, set(range(len(x.blocks))) - set(frozen))
                self.assertAlmostEqual(
                    spec.loss(x),
                    budget.remaining_loss_targets.loss(free),
                )

    def test_hard_constraints_reject_forbidden(self):
        a = example_a()
        bad = HardConstraints.from_system(a, [(1, 2)])
        self.assertFalse(bad.check(a))


class SwapTests(unittest.TestCase):
    def test_paper_cross_stratum_exact_delta(self):
        a = System.create([(1,), (2, 3)], universe=range(1, 4))
        spec = LossSpec(
            {pair(1, 2): 1, pair(1, 3): 0, pair(2, 3): 0},
            {1: 0, 2: 0, 3: 1},
        )
        swap = Swap(0, 1, 1, 3)
        b = apply(a, swap)
        self.assertEqual((spec.loss(a), spec.loss(b)), (4, 0))
        self.assertEqual(local_loss_delta(a, swap, spec), -4)
        self.assertEqual(a.sizes(), b.sizes())
        self.assertEqual(a.quotas(), b.quotas())

    def test_every_local_delta_matches_direct_recount(self):
        systems = [
            example_a(),
            System.create([(1,), (2, 3), (1, 2, 4), (3, 4)],
                          universe=range(1, 5)),
            System.create([(1, 2, 3, 4), (1, 2), (3,)],
                          universe=range(1, 5)),
        ]
        for x in systems:
            target = LossSpec(
                {p: i + 0.35 for i, p in enumerate(pairs(x.universe))},
                {e: i * 0.25 for i, e in enumerate(x.universe)},
                {p: 1 + i / 10 for i, p in enumerate(pairs(x.universe))},
                {e: 1 + i / 5 for i, e in enumerate(x.universe)},
                singleton_scale=1.7,
            )
            for move in all_swaps(x):
                nxt = apply(x, move)
                dp, ds = count_delta(x, move)
                for p in pairs(x.universe):
                    self.assertEqual(
                        nxt.pair_counts()[p] - x.pair_counts()[p], dp.get(p, 0)
                    )
                for e in x.universe:
                    self.assertEqual(
                        nxt.singleton_counts()[e] - x.singleton_counts()[e],
                        ds.get(e, 0),
                    )
                self.assertAlmostEqual(
                    local_loss_delta(x, move, target),
                    target.loss(nxt) - target.loss(x),
                )

    def test_illegal_swaps_are_rejected(self):
        x = System.create([(1, 2), (2, 3)], universe=range(1, 4))
        self.assertFalse(legal(x, Swap(0, 1, 2, 3)))
        with self.assertRaises(ValueError):
            apply(x, Swap(0, 1, 2, 3))

    def test_forbidden_constraints_filter_swaps(self):
        x = System.create([(1, 2), (3, 4)], universe=range(1, 5))
        constrained = list(all_swaps(x, [pair(1, 3)]))
        self.assertGreater(len(constrained), 0)
        for s in constrained:
            y = apply(x, s, [pair(1, 3)])
            self.assertEqual(y.pair_counts()[pair(1, 3)], 0)

    def test_all_matched_trades_preserve_low_order(self):
        a = example_a()
        trades = matched_trades(a)
        self.assertTrue(trades)
        self.assertEqual(max(t.distance for t in trades), 1.0)
        self.assertIn(example_b(), [t.result for t in trades])
        for t in trades:
            self.assertEqual(len({t.first.i, t.first.j,
                                  t.second.i, t.second.j}), 4)
            self.assertEqual(
                signature(a, t.first).opposite(),
                signature(a, t.second)
            )
            self.assertTrue(a.equivalent_low_order(t.result))
            self.assertNotEqual(a.higher_counts(3), t.result.higher_counts(3))


if __name__ == "__main__":
    unittest.main()
