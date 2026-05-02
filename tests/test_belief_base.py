# test_belief_base.py
#
# Tests for the BeliefBase class — the top-level AGM belief revision engine.
#
# The tests are organised in three groups:
#
#   1. Expansion  — basic add-without-check behaviour.
#   2. Contraction AGM postulates — the five properties that any well-behaved
#      contraction operator must satisfy (Success, Inclusion, Vacuity,
#      Recovery, Extensionality).
#   3. Revision AGM postulates — the five properties required by the
#      assignment spec (Success, Inclusion, Vacuity, Consistency,
#      Extensionality), derived from contraction via the Levi identity.
#
# Each test name follows given/when/then style so the pytest output reads as
# a list of specifications.

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from parse import parse_formula
from belief_base import BeliefBase


# ─── helpers ──────────────────────────────────────────────────────────────────

def p(s):
    return parse_formula(s)

def bb(*formulas, priorities=None):
    """Create a BeliefBase pre-loaded with the given formula strings."""
    base = BeliefBase()
    for i, f in enumerate(formulas):
        pri = priorities[i] if priorities else None
        base.expand(p(f), priority=pri)
    return base


# ─── 1. Expansion ─────────────────────────────────────────────────────────────

class TestExpansion:
    def test_given_empty_base_when_expanding_then_formula_is_believed(self):
        base = BeliefBase()
        base.expand(p("A"))
        assert base.entails(p("A"))

    def test_given_base_when_expanding_then_size_increases(self):
        base = bb("A", "B")
        assert len(base) == 2

    def test_given_base_when_expanding_with_contradiction_then_both_stored(self):
        # Expansion does NOT check consistency — that is Revision's job.
        base = bb("A")
        base.expand(p("NOT A"))
        assert len(base) == 2

    def test_given_base_when_expanding_with_explicit_priority_then_priority_stored(self):
        base = BeliefBase()
        base.expand(p("A"), priority=42)
        assert base.beliefs()[0][1] == 42


# ─── 2. Contraction — AGM postulates ──────────────────────────────────────────

class TestContraction:

    # Success: if phi is not a tautology, K ÷ phi should not entail phi.
    def test_given_entailed_formula_when_contracting_then_no_longer_entailed(self):
        base = bb("A", "IMPLIES A B")   # KB entails B via modus ponens
        assert base.entails(p("B"))
        base.contract(p("B"))
        assert not base.entails(p("B"))

    # Success: unit clause directly in KB.
    def test_given_atom_in_kb_when_contracting_atom_then_no_longer_entailed(self):
        base = bb("A", "B")
        base.contract(p("A"))
        assert not base.entails(p("A"))

    # Inclusion: K ÷ phi ⊆ K — contraction never adds new formulas.
    def test_given_kb_when_contracting_then_no_new_formulas_appear(self):
        base = bb("A", "B", "IMPLIES A B")
        original = set(str(f) for f in base.formulas())
        base.contract(p("B"))
        for f in base.formulas():
            assert str(f) in original

    # Vacuity: if K does not entail phi, K ÷ phi = K (nothing changes).
    def test_given_kb_not_entailing_phi_when_contracting_phi_then_kb_unchanged(self):
        base = bb("A", "B")
        original = [str(f) for f in base.formulas()]
        base.contract(p("C"))        # C is not in KB
        assert [str(f) for f in base.formulas()] == original

    # Vacuity: tautology cannot be contracted.
    def test_given_kb_when_contracting_tautology_then_kb_unchanged(self):
        base = bb("A", "B")
        base.contract(p("OR A (NOT A)"))
        assert len(base) == 2

    # Recovery: K ⊆ Cn((K ÷ phi) + phi).
    # After contracting phi and then adding it back, original inferences hold.
    def test_given_kb_when_contracting_then_expanding_back_then_original_consequences_hold(self):
        base = bb("A", "IMPLIES A B")
        assert base.entails(p("B"))
        phi = p("IMPLIES A B")
        base.contract(phi)
        base.expand(phi)
        assert base.entails(p("B"))   # modus ponens recoverable

    # Extensionality: logically equivalent phi and psi produce the same result.
    def test_given_equivalent_formulas_when_contracting_either_then_same_consequences(self):
        base1 = bb("A", "B")
        base2 = bb("A", "B")
        # A ∧ B  ≡  B ∧ A
        base1.contract(p("AND A B"))
        base2.contract(p("AND B A"))
        assert base1.entails(p("A")) == base2.entails(p("A"))
        assert base1.entails(p("B")) == base2.entails(p("B"))

    # Priority: high-priority formulas survive when there is a choice.
    def test_given_beliefs_with_different_priorities_when_contracting_then_high_priority_kept(self):
        base = BeliefBase()
        base.expand(p("A"),             priority=1)   # low priority
        base.expand(p("IMPLIES A B"),   priority=10)  # high priority
        # {A, A→B} entails B; after contraction, high-priority formula survives.
        base.contract(p("B"))
        assert base.entails(p("IMPLIES A B"))
        assert not base.entails(p("A"))


# ─── 3. Revision — AGM postulates ─────────────────────────────────────────────

class TestRevision:

    # Success: the new formula is believed after revision.
    def test_given_kb_with_conflicting_belief_when_revising_then_new_formula_believed(self):
        base = bb("NOT B")
        base.revise(p("B"))
        assert base.entails(p("B"))

    # Success with consistent KB.
    def test_given_consistent_kb_when_revising_then_new_formula_believed(self):
        base = bb("A")
        base.revise(p("B"))
        assert base.entails(p("B"))

    # Inclusion: K * phi ⊆ Cn(K + phi).
    # Every formula believed after revision was already believable via expansion.
    def test_given_kb_when_revising_then_every_belief_is_subset_of_expansion(self):
        base = bb("A")
        expanded = bb("A")
        expanded.expand(p("B"))

        base.revise(p("B"))
        for f in base.formulas():
            assert expanded.entails(f)

    # Vacuity: if ¬phi is not entailed by K, then K * phi = K + phi.
    def test_given_kb_not_entailing_negation_when_revising_then_same_as_expansion(self):
        base     = bb("A")
        expanded = bb("A")
        expanded.expand(p("B"))

        base.revise(p("B"))       # ¬B not in KB, so no contraction needed
        assert base.entails(p("A")) == expanded.entails(p("A"))
        assert base.entails(p("B")) == expanded.entails(p("B"))

    # Consistency: K * phi is consistent when phi itself is consistent.
    def test_given_kb_with_negation_when_revising_with_phi_then_kb_is_consistent(self):
        base = bb("A", "NOT B")
        base.revise(p("B"))
        # B is now believed; its negation must NOT be.
        assert base.entails(p("B"))
        assert not base.entails(p("NOT B"))

    # Consistency: unrelated beliefs are preserved.
    def test_given_kb_with_unrelated_belief_when_revising_then_unrelated_belief_preserved(self):
        base = bb("A", "NOT B")
        base.revise(p("B"))
        # A has nothing to do with B — it should survive.
        assert base.entails(p("A"))

    # Extensionality: logically equivalent inputs produce equivalent outcomes.
    def test_given_equivalent_revision_inputs_when_revising_then_same_consequences(self):
        base1 = bb("A")
        base2 = bb("A")
        # IMPLIES A B  ≡  OR (NOT A) B
        base1.revise(p("IMPLIES A B"))
        base2.revise(p("OR (NOT A) B"))
        assert base1.entails(p("IMPLIES A B")) == base2.entails(p("IMPLIES A B"))
        assert base1.entails(p("A"))           == base2.entails(p("A"))

    # Chained revision: revising twice converges to most recent belief.
    def test_given_kb_when_revising_twice_with_contradictory_formulas_then_last_revision_wins(self):
        base = bb("A")
        base.revise(p("NOT A"))
        base.revise(p("A"))
        assert base.entails(p("A"))
        assert not base.entails(p("NOT A"))
