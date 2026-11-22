# Implementation decisions, reproducibility and scope

## Model fidelity

1. **Record-labelled multiset.** Each row gets a persistent index; two
   identical sets still count as two different complete records.
2. **Containment counts.** `t(S)` counts any row containing S, including rows
   larger than S.
3. **Fixed row size and element quotas.** A legal 2-switch preserves both.
4. **Singleton diagonals.** A singleton record contributes to `s_i`, not
   to `t_ii`; swaps across sizes may affect the diagonal singleton residual.
5. **Frozen records.** Each frozen index refers to an entire actual block.
   Logical commitments are separate and continue to be checked.
6. **Exact low-order mode.** The reference is the system's realized pair
   counts and singleton counts, even when ideal \(\tau\) and \(\sigma\)
   differ from those counts.
7. **Residual identity.** We use the same weights and scaling after
   subtraction: \(E(F\sqcup R)=E_r(R)\).

## Search implementations and costs

- **Initialization without forbidden pairs:** integer maximum flow on a
  record-element bipartite network, with capacity 1 on each row-element arc.
- **Initialization with forbidden pairs:** exact allowed-type search using
  integer multiplicities; fine for tiny instances, combinatorial in size.
- **Fitter:** mixture of residual-biased proposals and random legal swaps.
  Proposal evaluation uses local \(\Delta E\), acceptance may include
  uphill moves with annealing, and output is best-seen state.
- **Zero-sum trade:** enumerate legal swap signatures, hash by signature,
  and combine inverse signatures only when the four involved records are
  distinct. Remove candidates with unchanged order-3 structure.
- **Directed construction:** enumerate *single* improving swaps for induction;
  freeze real blocks provisionally; breadth-first refit using only free
  records; apply exact/tolerance + previous-goal acceptance atomically.
  The finite `induction_budget`, `refit_depth` and `refit_states` bound the
  search. `PARTIAL` and `FAILURE` are NOT proofs of infeasibility.
- **Finite realizability:** exact memoized search over multiplicities of all
  legal block types \(B\). It respects quotas, size counts, positive-support
  coverage, forbidden pairs and optional exact pair/singleton counts. A
  `max_count=None` means the whole integer model is infeasible, while
  `max_count=0` means a feasible model exists but the selected target cannot
  occur. Exponential worst-case complexity; replace with MILP / CP-SAT when
  scaling up.
- **Reachability:** record-labelled breadth-first exploration with a chosen
  operation set, depth and visited-state limit. A truncated negative search
  is inconclusive. The strict option requires low-order equality at each
  committed state, not at the transient inner step of a zero-sum trade.

## Deliberate limitations

- The automatic directed algorithm is a defensible small-instance
  specialization. It does not implement every possible multi-swap induction,
  arbitrary target-scoring schedule, or a global completeness guarantee.
- The integer solver does not optimize general quadratic tolerance-mode
  objectives; it solves the *finite feasibility* model and optionally exact
  counts. Quadratic loss is handled by the fitter, not by the integer solver.
- The original paper specifies ideal \(P,Q\) and resource allocation
  generally. Here tests use explicit integer quotas, complete system
  witnesses, and target counts. The optimization rounding of arbitrary
  \(Np\) into quotas is not supplied as a general-purpose module.
- Max-flow initialization is deterministic for fixed record and element
  order, but this is not a uniqueness claim.
- No multi-machine or distributed execution; no external APIs.
- The explicit illustrative instances are small. Timing and convergence
  properties should NOT be extrapolated to larger systems.

## Reproduction environment

- Python 3.10+.
- No third-party runtime dependencies.
- `unittest` tests every allowed swap's incremental count/delta on
  selected small systems, as well as source-specific numerical claims.
- Fixed seed 2026 for the added fitting experiment.
- JSON outputs are UTF-8. The fit CSV uses stable column names.
- GitHub Actions runs the package, unit tests, all cases and a second
  check on exported results.

## Paper availability and publishing

`paper/main-zh.tex` is the actual uploaded revision and `paper/main-en.tex`
is its English translation, both without fabricated author or BibTeX entries.
`paper/main-en.pdf` is compiled; `paper/main-zh.pdf` is an empty placeholder
to be built locally with XeLaTeX and Noto Serif CJK SC. `LICENSE` and
`CITATION.cff` are also empty placeholders: fill in the author, copyright
holder, and license before making the repository public.
