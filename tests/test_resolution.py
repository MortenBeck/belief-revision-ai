import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula
from cnf import to_cnf
from resolution import convert_to_set, negate


def parse(s):
    return parse_formula(s)


def cnf(s):
    return to_cnf(parse(s))


# --- existing helpers ---

def test_convert_to_set_atom():
    assert convert_to_set(parse("A")) == {"A"}


def test_convert_to_set_negation():
    assert convert_to_set(cnf("NOT A")) == {"~A"}


def test_convert_to_set_or():
    assert convert_to_set(cnf("OR A (NOT B)")) == {"A", "~B"}


def test_convert_to_set_long_disjunction():
    # OR A (OR B C)  -> {A, B, C}
    assert convert_to_set(cnf("OR A (OR B C)")) == {"A", "B", "C"}


def test_negate_positive_literal():
    assert negate("A") == "~A"


def test_negate_negative_literal():
    assert negate("~A") == "A"


def test_negate_is_involution():
    assert negate(negate("A")) == "A"
    assert negate(negate("~A")) == "~A"


# --- new API: clauses_from_cnf ---
# Drives a replacement for convert_from_single_to_multiple that handles
# arbitrarily-deep AND-trees, not just a single binary AND at the top.

def test_clauses_from_single_atom():
    from resolution import clauses_from_cnf
    assert clauses_from_cnf(cnf("A")) == [frozenset({"A"})]


def test_clauses_from_disjunction():
    from resolution import clauses_from_cnf
    assert clauses_from_cnf(cnf("OR A B")) == [frozenset({"A", "B"})]


def test_clauses_from_simple_conjunction():
    from resolution import clauses_from_cnf
    result = clauses_from_cnf(cnf("AND A B"))
    assert frozenset({"A"}) in result
    assert frozenset({"B"}) in result
    assert len(result) == 2


def test_clauses_flattens_nested_and():
    from resolution import clauses_from_cnf
    # AND (AND A B) C  -> three unit clauses
    result = clauses_from_cnf(cnf("AND (AND A B) C"))
    assert set(result) == {frozenset({"A"}), frozenset({"B"}), frozenset({"C"})}


def test_clauses_from_mixed():
    from resolution import clauses_from_cnf
    # AND A (OR B (NOT C))  -> [{A}, {B, ~C}]
    result = clauses_from_cnf(cnf("AND A (OR B (NOT C))"))
    assert set(result) == {frozenset({"A"}), frozenset({"B", "~C"})}


# --- new API: entails ---
# Resolution-refutation: KB |= q  iff  KB ∪ {¬q} is unsatisfiable.
# Tests below are written in given/when/then style and document the algorithm's
# expected behavior across the standard cases of propositional entailment.

# --- when entailment SHOULD hold ---

def test_given_query_already_in_kb_when_checking_entailment_then_holds():
    from resolution import entails
    assert entails([parse("A"), parse("B")], parse("A")) is True


def test_given_kb_with_implication_when_antecedent_known_then_consequent_entailed():
    """Modus ponens: {A, A->B} |= B."""
    from resolution import entails
    kb = [parse("A"), parse("IMPLIES A B")]
    assert entails(kb, parse("B")) is True


def test_given_kb_with_implication_when_consequent_negated_then_antecedent_negation_entailed():
    """Modus tollens: {A->B, ~B} |= ~A."""
    from resolution import entails
    kb = [parse("IMPLIES A B"), parse("NOT B")]
    assert entails(kb, parse("NOT A")) is True


def test_given_disjunction_when_one_disjunct_negated_then_other_entailed():
    """Disjunctive syllogism: {A v B, ~A} |= B."""
    from resolution import entails
    kb = [parse("OR A B"), parse("NOT A")]
    assert entails(kb, parse("B")) is True


def test_given_chained_implications_when_first_premise_known_then_final_consequent_entailed():
    """Hypothetical syllogism / transitivity: {A, A->B, B->C} |= C."""
    from resolution import entails
    kb = [parse("A"), parse("IMPLIES A B"), parse("IMPLIES B C")]
    assert entails(kb, parse("C")) is True


def test_given_inconsistent_kb_when_checking_any_query_then_entailed():
    """Ex falso quodlibet: a contradictory KB entails every formula."""
    from resolution import entails
    kb = [parse("A"), parse("NOT A")]
    assert entails(kb, parse("Z")) is True


def test_given_empty_kb_when_query_is_tautology_then_entailed():
    """A tautology is entailed by any KB, including the empty one."""
    from resolution import entails
    assert entails([], parse("OR A (NOT A)")) is True


def test_given_kb_with_conjunction_when_querying_a_conjunct_then_entailed():
    """{A ^ B} |= A."""
    from resolution import entails
    assert entails([parse("AND A B")], parse("A")) is True


# --- when entailment should NOT hold ---

def test_given_consistent_kb_when_querying_unrelated_atom_then_not_entailed():
    from resolution import entails
    assert entails([parse("A")], parse("B")) is False


def test_given_atom_in_kb_when_querying_its_negation_then_not_entailed():
    from resolution import entails
    assert entails([parse("A")], parse("NOT A")) is False


def test_given_empty_kb_when_querying_contingent_atom_then_not_entailed():
    """Empty KB does not entail a contingent atom — both A and ~A are possible."""
    from resolution import entails
    assert entails([], parse("A")) is False


def test_given_disjunction_only_when_querying_one_disjunct_then_not_entailed():
    """{A v B} alone does not entail A — only B might hold."""
    from resolution import entails
    assert entails([parse("OR A B")], parse("A")) is False


def test_given_only_implication_when_querying_consequent_then_not_entailed():
    """{A -> B} alone does not entail B — A might be false."""
    from resolution import entails
    assert entails([parse("IMPLIES A B")], parse("B")) is False
