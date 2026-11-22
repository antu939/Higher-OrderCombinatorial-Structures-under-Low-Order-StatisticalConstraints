# Equation-by-equation reproduction map

Reference: `paper/main-zh.tex` (Chinese original) and `paper/main-en.tex`
(English translation), Sections 1--6.

| Manuscript anchor | Source location | What the code checks |
|---|---|---|
| `eq:blocks`, `eq:incidence-counts` | `core.System`, `core.HardConstraints` | Every record uses a set of distinct elements; fixed sizes and element quotas; repeatable complete record types allowed |
| `eq:high-order`, `eq:high-order-total`, `eq:high-order-distance` | `System.count`, `System.higher_counts`, `System.distance` | Counts are by containment; \(T_h=\sum_o {k_o\choose h}\); \(0\le d_h\le1\) when applicable |
| `eq:global-loss` | `core.LossSpec` | Weighted pair-count and singleton-count squared residuals, with independent singleton scale |
| `eq:2switch` | `switches.Swap`, `apply`, `all_swaps` | Disjoint element transfer, intact row sizes and quotas, forbidden-pair checking |
| `eq:baseline-network` | `baseline.feasible_initialization` | Integral bipartite max flow for absence of forbidden pairs |
| `eq:switch-local-change`, `eq:switch-loss-delta` | `switches.count_delta`, `local_loss_delta` | Full enumeration of legal moves on small samples matches direct recount |
| `eq:baseline-swap-example` | `examples/ex01_cross_stratum.py` | \(\{1\},\{2,3\}\to\{3\},\{1,2\}\), \(4\to0\) |
| `alg:baseline` | `baseline.fit_residuals` | Mixed residual/random proposals, temperature-based acceptance, best-seen state |
| `eq:trade-signature`, `eq:zero-sum-condition` | `switches.signature`, `matched_trades` | Matched cancelling pair and singleton deltas for four distinct records |
| `eq:example-invariant`, `eq:example-distance` | `examples/ex02_zero_sum.py` | XA/XB low-order equality and \(d_3=1\) |
| `alg:variation` | `switches.matched_trades` | Exhaustively generate cancelling nontrivial moves at this small size |
| `eq:budget-subtraction`, `eq:loss-equivalence` | `core.ResidualBudget`, `verify_residual_equivalence` | Subtract frozen block resource and statistical contributions; test full/residual loss identity |
| `eq:directed-validation`, `alg:directed` | `directed.construct_directed`, `residual_refit_bfs` | Provisional induction, real-record anchors, exact/tolerance acceptance, past goal checking |
| `eq:directed-example-initial` through `eq:level-two-example` | `directed.paper_directed_trace`, `examples/ex03_directed_freeze.py` | Reproduce paper sequence and its after-commit optional second freeze |
| `eq:frozen-distance` | `examples/ex03_directed_freeze.py` | Bound falls from 3/4 to 2/4 as two 3-element records become frozen |
| `eq:support-graphs`, `eq:clique-extension` | `feasibility.support_pairs`, `clique_candidates` | Enumerate graph clique candidates |
| `eq:integer-feasibility`, `eq:max-higher-count` | `feasibility.maximize_occurrences` | Search nonnegative integer multiplicities \(z_B\); maximize target occurrence |
| `eq:resource-counterexample`, `eq:resource-exclusion` | `examples/ex04_resource_conflict.py` | abc is a support triangle but \(U(abc)=0\) with required support coverage |
| `eq:path-inclusion`, `eq:operation-family` | `reachability.find_path`, `examples/ex05_reachability.py` | Endpoint reachability vs exact-valid intermediate states under different operations |

## Careful distinction: example vs algorithm

**Paper witness:** Explicitly named records and swaps in experiments 01--05
are lifted from the submitted draft. The fixed witness checks exact expected
records and all stated numerical values.

**Independent verification:** `matched_trades` enumerates other valid trade
candidates. `construct_directed` searches candidate inductions rather than
using the paper's fixed witness. `maximize_occurrences` uses integer type
multiplicities. State graph paths are found by BFS.

**Added experiment:** Experiment 06 chooses a new, documented mixed-size
reference system. It tests the manuscript's procedure but is not claimed
to have appeared in the TeX.

## Exact vs tolerance mode

- `exact`: match every realized pair and singleton count of `initial`;
  comparing only the ideal-target weighted loss is insufficient.
- `tolerance`: require hard feasibility and \(E\le\varepsilon\), using
  the specified ideal or fitted targets.

In both modes, induction intermediate candidates are not called
"committed" until their complete state passes the acceptance predicate.
