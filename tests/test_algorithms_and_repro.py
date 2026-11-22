from __future__ import annotations

import unittest
from collections import Counter

from hocomb import (
    Goal, LossSpec, System, clique_candidates, construct_directed,
    feasible_initialization, find_path, fit_residuals, maximize_occurrences,
)
from hocomb.core import pair
from hocomb.directed import paper_directed_trace
from hocomb.feasibility import support_pairs
from examples import (
    ex01_cross_stratum, ex02_zero_sum, ex03_directed_freeze,
    ex04_resource_conflict, ex05_reachability, ex06_seeded_fitting,
)


def six_a():
    return System.create([
        (1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6)
    ], universe=range(1, 7))


def six_b():
    return System.create([
        (1, 2, 4), (1, 3, 5), (2, 3, 6), (4, 5, 6)
    ], universe=range(1, 7))


class FeasibilityTests(unittest.TestCase):
    def test_triangle_candidate_but_zero_occurrences(self):
        x = System.create(
            [("a", "b", "d"), ("a", "c"), ("b", "c")],
            universe=("a", "b", "c", "d"),
        )
        support = support_pairs(x)
        self.assertIn(
            ("a", "b", "c"), clique_candidates(x.universe, support, 3)
        )
        exact = maximize_occurrences(
            x.universe, x.quotas(), x.size_distribution(),
            required_pairs=support, target=("a", "b", "c"),
        )
        self.assertTrue(exact.feasible)
        self.assertEqual(exact.max_count, 0)
        self.assertEqual(exact.witness.quotas(), x.quotas())
        self.assertEqual(exact.witness.size_distribution(), x.size_distribution())
        loose = maximize_occurrences(
            x.universe, x.quotas(), x.size_distribution(),
            target=("a", "b", "c"),
        )
        self.assertTrue(loose.feasible)
        self.assertEqual(loose.max_count, 1)

    def test_exact_pair_requirements_find_124(self):
        x = six_a()
        r = maximize_occurrences(
            x.universe, x.quotas(), x.size_distribution(),
            required_pairs=support_pairs(x),
            target=(1, 2, 4),
            exact_pairs=x.pair_counts(),
            exact_singletons=x.singleton_counts(),
        )
        self.assertTrue(r.feasible)
        self.assertEqual(r.max_count, 1)
        self.assertEqual(r.witness.pair_counts(), x.pair_counts())
        self.assertEqual(r.witness.singleton_counts(), x.singleton_counts())
        self.assertEqual(r.witness.count((1, 2, 4)), 1)

    def test_infeasible_is_distinct_from_feasible_but_U_zero(self):
        r = maximize_occurrences(
            (1, 2, 3), {1: 1, 2: 1, 3: 1}, {2: 2},
            target=(1, 2, 3)
        )
        self.assertFalse(r.feasible)
        self.assertIsNone(r.max_count)
        self.assertIsNone(r.witness)

    def test_multiset_integer_multiplicities(self):
        r = maximize_occurrences(
            (1, 2, 3), {1: 2, 2: 2, 3: 2}, {3: 2},
            required_pairs={(1, 2), (1, 3), (2, 3)},
            target=(1, 2, 3),
        )
        self.assertTrue(r.feasible)
        self.assertEqual(r.max_count, 2)
        self.assertEqual(len(r.witness.blocks), 2)

    def test_maxflow_initialization_keeps_rows_and_quotas(self):
        x = System.create([
            (1,), (2, 3), (4, 5, 6), (1, 4, 6), (2, 5), (3,)
        ], universe=range(1, 7))
        y = feasible_initialization(x.universe, x.sizes(), x.quotas())
        self.assertEqual(y.quotas(), x.quotas())
        self.assertEqual(y.sizes(), x.sizes())

    def test_forbidden_initialization_exact_small_instance(self):
        y = feasible_initialization(
            (1, 2, 3, 4), (2, 2),
            {1: 1, 2: 1, 3: 1, 4: 1},
            forbidden=((1, 2), (3, 4)),
        )
        self.assertEqual(y.quotas(), dict.fromkeys(range(1, 5), 1))
        self.assertEqual(y.pair_counts()[pair(1, 2)], 0)
        self.assertEqual(y.pair_counts()[pair(3, 4)], 0)

    def test_infeasible_forbidden_initialization(self):
        with self.assertRaises(ValueError):
            feasible_initialization(
                (1, 2, 3), (3,), {1: 1, 2: 1, 3: 1},
                forbidden=((1, 2),),
            )


class DirectedAndPathTests(unittest.TestCase):
    def test_exact_paper_trace(self):
        trace = paper_directed_trace()
        self.assertEqual(
            [trace["initial_loss"], trace["induction_loss"], trace["commit_loss"]],
            [0, 4, 0]
        )
        self.assertEqual(trace["frozen_first"], frozenset((0,)))
        self.assertEqual(trace["frozen_second"], frozenset((0, 3)))
        self.assertEqual(trace["residual_second"].remaining_quotas[4], 0)
        self.assertTrue(trace["residual_identity_holds"])

    def test_generic_directed_constructor_no_hardcoded_answer(self):
        x = six_a()
        g = (
            Goal(frozenset((1, 2, 4))),
            Goal(frozenset((4, 5, 6))),
        )
        result = construct_directed(x, g, induction_budget=200, refit_depth=3)
        self.assertEqual(result.status, "SUCCESS")
        self.assertTrue(x.equivalent_low_order(result.final))
        self.assertTrue(all(goal.holds(result.final) for goal in g))
        self.assertTrue(result.accepted_steps)
        self.assertTrue(result.frozen_ids)
        self.assertEqual(result.accepted_steps[0]["newly_committed_goal_count"], 2)

    def test_equals_zero_goal_already_satisfied(self):
        x = six_a()
        result = construct_directed(x, (Goal(frozenset((1, 2, 4)), 0, "="),))
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.final, x)
        self.assertFalse(result.frozen_ids)

    def test_unattainable_combination_is_not_falsely_committed(self):
        x = six_a()
        impossible_together = (
            Goal(frozenset((1, 2, 3)), 1),
            Goal(frozenset((1, 2, 4)), 1),
        )
        result = construct_directed(x, impossible_together, induction_budget=200)
        self.assertNotEqual(result.status, "SUCCESS")
        self.assertTrue(x.equivalent_low_order(result.final))
        self.assertTrue(all(g.holds(result.final) for g in result.committed))

    def test_reachability_enforces_forbidden_pairs(self):
        start = System.create([(1, 2), (3, 4)], universe=range(1, 5))
        target = System.create([(1, 4), (2, 3)], universe=range(1, 5))
        path = find_path(
            start, target, operation="switch", forbidden=((1, 3),),
            max_depth=2
        )
        self.assertTrue(path.found)
        self.assertTrue(all(
            state.pair_counts()[pair(1, 3)] == 0 for state in path.path
        ))
        with self.assertRaises(ValueError):
            find_path(start, target, forbidden=((1, 4),))

    def test_paths_distinguish_intermediate_invariants(self):
        a, b = six_a(), six_b()
        path = find_path(a, b, "switch", max_depth=2)
        self.assertTrue(path.found)
        self.assertEqual(path.transitions, 2)
        strict = find_path(
            a, b, "switch", strict_intermediate=True, max_depth=2
        )
        self.assertFalse(strict.found)
        self.assertFalse(strict.truncated)
        trade = find_path(
            a, b, "zero_sum_trade", strict_intermediate=True, max_depth=1
        )
        self.assertTrue(trade.found)
        self.assertEqual(trade.transitions, 1)


class FittingAndCaseTests(unittest.TestCase):
    def test_seeded_reproducibility_and_monotone_best_record(self):
        ref = System.create([
            (1,), (2, 3), (4, 5, 6), (1, 4, 6), (2, 5), (3,)
        ], universe=range(1, 7))
        initial = feasible_initialization(ref.universe, ref.sizes(), ref.quotas())
        spec = LossSpec.from_reference(ref)
        kwargs = dict(
            iterations=650, seed=2026, residual_proposal_probability=.75,
            start_temperature=.5, end_temperature=.02,
        )
        r1 = fit_residuals(initial, spec, **kwargs)
        r2 = fit_residuals(initial, spec, **kwargs)
        self.assertEqual(r1.trajectory, r2.trajectory)
        self.assertEqual(r1.best, r2.best)
        self.assertEqual(r1.initial_loss, 16.0)
        self.assertEqual(r1.best_loss, 0.0)
        previous = float("inf")
        for entry in r1.trajectory:
            self.assertLessEqual(entry["best_loss"], previous)
            previous = entry["best_loss"]
        self.assertEqual(r1.best.sizes(), initial.sizes())
        self.assertEqual(r1.best.quotas(), initial.quotas())

    def test_six_experiments_report_expected_invariants(self):
        a = ex01_cross_stratum.run()
        b = ex02_zero_sum.run()
        c = ex03_directed_freeze.run()
        d = ex04_resource_conflict.run()
        e = ex05_reachability.run()
        f = ex06_seeded_fitting.run()
        self.assertEqual((a["initial_loss"], a["final_loss"]), (4.0, 0.0))
        self.assertEqual((b["T3"], b["L1_h3"], b["d3"]), (4, 8, 1.0))
        self.assertEqual((c["E_initial"], c["E_provisional"], c["E_committed"]),
                         (0.0, 4.0, 0.0))
        self.assertEqual(d["with_required_coverage"]["U_abc"], 0)
        self.assertFalse(e["every_switch_must_preserve_pair_counts"]["found"])
        self.assertEqual(f["best_loss"], 0.0)


if __name__ == "__main__":
    unittest.main()
