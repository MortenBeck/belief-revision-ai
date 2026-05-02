from itertools import combinations

from parse import Not
from resolution import entails as _entails


class BeliefBase:
    """Belief base with priority-ordered partial meet contraction.

    Each formula is stored together with an integer priority.  Higher
    priority means the formula is more entrenched: the selection function
    prefers remainders that retain high-priority formulas.

    The three main operations follow the AGM framework:
        expand(phi)   -- K + phi  (add without consistency check)
        contract(phi) -- K ÷ phi  (partial meet contraction)
        revise(phi)   -- K * phi  (Levi identity: contract ~phi, then expand)
    """

    def __init__(self):
        self._beliefs = []   # list of (formula_tree, priority: int)
        self._counter = 0    # auto-priority counter

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def expand(self, formula, priority=None):
        """K + phi — add phi to the belief base without consistency check."""
        if priority is None:
            priority = self._counter
        # Keep counter strictly ahead of any manually assigned priority
        self._counter = max(self._counter, priority) + 1
        self._beliefs.append((formula, priority))

    def contract(self, phi):
        """K ÷ phi — partial meet contraction based on priority ordering.

        Steps:
          1. Vacuity check: if KB does not entail phi, nothing to do.
          2. Tautology check: if phi is logically valid (empty KB entails it),
             it cannot be contracted — leave KB unchanged.
          3. Compute all maximal subsets of KB that do not entail phi.
          4. Select the best subset(s) via the priority-based selection function.
          5. Replace beliefs with the intersection of the selected subsets.
        """
        if _entails([], phi):           # phi is a tautology, cannot contract
            return
        if not self.entails(phi):       # AGM Vacuity: phi not believed, nothing to do
            return

        remainders = self._remainders(phi)
        selected   = self._select(remainders)
        kept       = frozenset.intersection(*selected)
        self._beliefs = [self._beliefs[i] for i in sorted(kept)]

    def revise(self, phi):
        """K * phi — Levi identity: contract ~phi, then expand with phi."""
        self.contract(Not(phi))
        self.expand(phi)

    def entails(self, query):
        """Return True iff the current belief base logically entails query."""
        return _entails(self.formulas(), query)

    def formulas(self):
        """Return the list of formula trees currently in the belief base."""
        return [f for f, _ in self._beliefs]

    def beliefs(self):
        """Return the list of (formula, priority) pairs."""
        return list(self._beliefs)

    def clear(self):
        self._beliefs = []
        self._counter = 0

    def __len__(self):
        return len(self._beliefs)

    def __bool__(self):
        return bool(self._beliefs)

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _remainders(self, phi):
        """Return all maximal index-subsets whose formulas do not entail phi.

        A 'remainder' is a frozenset of indices into self._beliefs.
        Maximality means: you cannot add any formula back without the subset
        starting to entail phi again.

        Complexity: O(2^n) calls to the entailment oracle — fine for small KBs.
        """
        n = len(self._beliefs)
        non_entailing = set()

        for size in range(n + 1):
            for combo in combinations(range(n), size):
                subset   = frozenset(combo)
                formulas = [self._beliefs[i][0] for i in combo]
                if not _entails(formulas, phi):
                    non_entailing.add(subset)

        # Keep only maximal sets (no proper superset in the collection)
        return [s for s in non_entailing
                if not any(s < t for t in non_entailing)]

    def _select(self, remainders):
        """Select which remainders to intersect using formula priorities.

        remainders: list of frozenset of indices (into self._beliefs).
        Returns:    a non-empty sub-list of remainders — the 'best' ones.
                    The contraction result is their intersection, so a formula
                    survives only if it appears in EVERY selected remainder.

        This is the core policy decision of partial meet contraction.
        Different strategies yield different AGM-satisfying operators:

          Strategy A — lexicographic by priority (epistemic entrenchment):
            Score each remainder by the tuple of its formulas' priorities,
            sorted descending.  Compare tuples lexicographically.  Select
            all remainders tied for the maximum score.
            Effect: strongly prefers keeping the single most-important
            formula; only breaks ties by the next most-important, etc.

          Strategy B — sum of priorities:
            Score each remainder by the sum of its formulas' priorities.
            Select all remainders with the maximum sum.
            Effect: treats all formulas more equally; a remainder with many
            medium-priority beliefs can beat one with a single high-priority
            belief.

          Strategy C — full meet (baseline, ignores priorities entirely):
            Return all remainders.
            Effect: only formulas present in EVERY remainder survive —
            very conservative, but always AGM-valid.

        Available data: self._beliefs[i][1] gives the priority of formula i.

        Strategy A (lexicographic epistemic entrenchment) is implemented below.
        """
        def score(remainder):
            return tuple(sorted(
                (self._beliefs[i][1] for i in remainder), reverse=True
            ))
        best = max(score(r) for r in remainders)
        return [r for r in remainders if score(r) == best]
