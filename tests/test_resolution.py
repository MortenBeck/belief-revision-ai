# test_resolution.py
#
# Unit tests for resolution.py — the module that turns CNF parse trees into
# clause sets and uses resolution-refutation to decide propositional
# entailment. Resolution is the core inference procedure that the belief
# revision engine relies on: contraction, expansion, and revision are all
# defined in terms of "does the current belief base entail X?".
#
# Quick refresher on the algorithm being tested:
#
#   A clause is represented as a frozenset of literal-strings, where a
#   literal is either "A" or "~A". The whole knowledge base is a list of
#   such clauses (a CNF formula in clausal form).
#
#   To decide  KB |= q  (KB entails q):
#     1. Convert each formula in KB to CNF, then to clauses.
#     2. Convert  ~q  to CNF, then to clauses, and add them to the KB.
#     3. Repeatedly resolve pairs of clauses (resolve = drop a literal that
#        appears positive in one clause and negative in the other, then
#        union the rest). If the empty clause appears, the augmented set
#        is unsatisfiable, which means KB |= q. If we run out of new
#        clauses to derive without producing the empty clause, KB does not
#        entail q.
#
# Tests are organized in three groups:
#   - Existing helpers (convert_to_set, negate) that are already in
#     resolution.py and used as building blocks.
#   - The new clauses_from_cnf API, which replaces the buggy
#     convert_from_single_to_multiple by handling AND-trees of any depth.
#   - The new entails API, written in given/when/then style so each test
#     also serves as documentation of one well-known propositional
#     inference pattern.

import sys
import os

import pytest

# Same path trick as test_cnf.py — make project root importable.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula
from cnf import to_cnf
from resolution import convert_to_set, negate


# Tiny helpers so tests read as English. parse() turns a Polish-notation
# string into a parse tree; cnf() additionally runs the CNF pipeline on it.
def parse(s):
    return parse_formula(s)


def cnf(s):
    return to_cnf(parse(s))


# --- existing helpers ---
# convert_to_set takes a parse tree representing a single CNF clause (a
# disjunction of literals, possibly just one literal) and turns it into a
# set of literal strings, e.g. Operator("OR", Atom("A"), Not(Atom("B")))
# becomes {"A", "~B"}. negate flips the polarity of a literal-string.
# Both are small enough to test exhaustively.

# A bare atom should become a singleton set containing its name.
def test_convert_to_set_atom():
    assert convert_to_set(parse("A")) == {"A"}


# A negated atom should produce a single negative literal "~A".
def test_convert_to_set_negation():
    assert convert_to_set(cnf("NOT A")) == {"~A"}


# A two-literal clause: positive A together with a negated B.
def test_convert_to_set_or():
    assert convert_to_set(cnf("OR A (NOT B)")) == {"A", "~B"}


# Right-associated disjunction. CNF should flatten OR A (OR B C) into a
# single three-literal clause; convert_to_set should return all three.
def test_convert_to_set_long_disjunction():
    assert convert_to_set(cnf("OR A (OR B C)")) == {"A", "B", "C"}


# Negate adds a tilde to a positive literal.
def test_negate_positive_literal():
    assert negate("A") == "~A"


# Negate strips the tilde from a negative literal — it does not just prepend
# another tilde, which would give us "~~A" and break clause comparison.
def test_negate_negative_literal():
    assert negate("~A") == "A"


# Negation is an involution: applying it twice returns the original literal.
# This property is what makes the resolution rule symmetric in its inputs.
def test_negate_is_involution():
    assert negate(negate("A")) == "A"
    assert negate(negate("~A")) == "~A"


# --- new API: clauses_from_cnf ---
# clauses_from_cnf walks an arbitrary CNF tree (which may have ANDs nested
# arbitrarily deep on either side, since CNF conversion typically produces
# left-associated AND chains) and returns a flat list of clauses, each
# represented as a frozenset of literal-strings.
#
# This replaces the existing convert_from_single_to_multiple, which only
# handled the case where the top-level tree is a single binary AND. Anything
# more deeply nested silently produced wrong output.
#
# Each test here also documents one shape of CNF tree the function must cope
# with.

# A unit clause is a single literal, returned as a one-element list with a
# one-element frozenset.
def test_clauses_from_single_atom():
    from resolution import clauses_from_cnf
    assert clauses_from_cnf(cnf("A")) == [frozenset({"A"})]


# A pure disjunction is a single multi-literal clause.
def test_clauses_from_disjunction():
    from resolution import clauses_from_cnf
    assert clauses_from_cnf(cnf("OR A B")) == [frozenset({"A", "B"})]


# A simple binary AND of two atoms produces two unit clauses. Order is not
# checked because clause sets are conceptually unordered.
def test_clauses_from_simple_conjunction():
    from resolution import clauses_from_cnf
    result = clauses_from_cnf(cnf("AND A B"))
    assert frozenset({"A"}) in result
    assert frozenset({"B"}) in result
    assert len(result) == 2


# Nested AND on the left: (A ^ B) ^ C must be flattened into three unit
# clauses, NOT two clauses where one is "A ^ B" treated as a single set.
# This is the case the old convert_from_single_to_multiple got wrong.
def test_clauses_flattens_nested_and():
    from resolution import clauses_from_cnf
    result = clauses_from_cnf(cnf("AND (AND A B) C"))
    assert set(result) == {frozenset({"A"}), frozenset({"B"}), frozenset({"C"})}


# Mixed shape: AND of a unit clause and a multi-literal clause. Tests that
# the function correctly identifies the boundary between AND-traversal and
# clause-building.
def test_clauses_from_mixed():
    from resolution import clauses_from_cnf
    # AND A (OR B (NOT C))  -> [{A}, {B, ~C}]
    result = clauses_from_cnf(cnf("AND A (OR B (NOT C))"))
    assert set(result) == {frozenset({"A"}), frozenset({"B", "~C"})}


# --- new API: entails ---
# entails(kb_formulas, query) returns True iff KB |= query.
#
# Implementation strategy is resolution-refutation, as described at the top
# of this file. The tests below are split into two groups: cases where
# entailment SHOULD hold (modus ponens and friends) and cases where it
# should NOT (independent atoms, weak premises). Each test name follows the
# given/when/then convention so the pytest output reads as a list of
# specifications, not a list of opaque function names.

# --- when entailment SHOULD hold ---

# Trivial reflexive case: if q is literally one of the formulas in KB, then
# KB |= q. After negating q, we directly get a unit clause that resolves
# with the matching positive unit clause from KB to produce the empty clause.
def test_given_query_already_in_kb_when_checking_entailment_then_holds():
    from resolution import entails
    assert entails([parse("A"), parse("B")], parse("A")) is True


# Modus ponens: {A, A->B} |= B. After CNF the implication becomes (~A v B);
# adding ~B (from the negated query) and resolving with A gives B, then
# resolving B with ~B gives the empty clause.
def test_given_kb_with_implication_when_antecedent_known_then_consequent_entailed():
    from resolution import entails
    kb = [parse("A"), parse("IMPLIES A B")]
    assert entails(kb, parse("B")) is True


# Modus tollens: {A->B, ~B} |= ~A. The classical contrapositive form of
# modus ponens; resolution discovers it without us hard-coding the rule.
def test_given_kb_with_implication_when_consequent_negated_then_antecedent_negation_entailed():
    from resolution import entails
    kb = [parse("IMPLIES A B"), parse("NOT B")]
    assert entails(kb, parse("NOT A")) is True


# Disjunctive syllogism: {A v B, ~A} |= B. If at least one of A or B holds
# and we know A does not, then B must hold.
def test_given_disjunction_when_one_disjunct_negated_then_other_entailed():
    from resolution import entails
    kb = [parse("OR A B"), parse("NOT A")]
    assert entails(kb, parse("B")) is True


# Hypothetical syllogism / transitivity of implication chained with a
# concrete fact: {A, A->B, B->C} |= C. Stresses that resolution can chain
# inferences across multiple clauses, not just two.
def test_given_chained_implications_when_first_premise_known_then_final_consequent_entailed():
    from resolution import entails
    kb = [parse("A"), parse("IMPLIES A B"), parse("IMPLIES B C")]
    assert entails(kb, parse("C")) is True


# Ex falso quodlibet: from a contradiction, anything follows. An
# inconsistent KB derives the empty clause directly from its own clauses
# (e.g. {A} and {~A}), so adding the negated query never even matters.
def test_given_inconsistent_kb_when_checking_any_query_then_entailed():
    from resolution import entails
    kb = [parse("A"), parse("NOT A")]
    assert entails(kb, parse("Z")) is True


# Tautology with empty KB: |= (A v ~A). The negated query is (~A ^ A) in
# CNF, whose two unit clauses immediately resolve to the empty clause.
# Validates the algorithm's behavior at the empty-KB edge case.
def test_given_empty_kb_when_query_is_tautology_then_entailed():
    from resolution import entails
    assert entails([], parse("OR A (NOT A)")) is True


# Conjunction elimination: {A ^ B} |= A. CNF will split A ^ B into two unit
# clauses, so the query A immediately resolves with one of them.
def test_given_kb_with_conjunction_when_querying_a_conjunct_then_entailed():
    from resolution import entails
    assert entails([parse("AND A B")], parse("A")) is True


# --- when entailment should NOT hold ---
# These are the harder cases for a resolution implementation: the algorithm
# must terminate (resolution may loop forever on naive implementations) and
# must correctly conclude "no" rather than "yes" when no derivation exists.

# Two completely independent atoms. The resolver should saturate without
# producing the empty clause and return False.
def test_given_consistent_kb_when_querying_unrelated_atom_then_not_entailed():
    from resolution import entails
    assert entails([parse("A")], parse("B")) is False


# Knowing A does NOT mean we know ~A — that would be a contradiction.
# This guards against an implementation that conflates "q is consistent
# with KB" and "KB entails q".
def test_given_atom_in_kb_when_querying_its_negation_then_not_entailed():
    from resolution import entails
    assert entails([parse("A")], parse("NOT A")) is False


# An empty KB does not entail any contingent (non-tautological) atom: A
# could be either true or false. Important corner case.
def test_given_empty_kb_when_querying_contingent_atom_then_not_entailed():
    from resolution import entails
    assert entails([], parse("A")) is False


# {A v B} alone does not entail A — only B might hold. This is the test
# that's easy to get wrong with a buggy resolver: the disjunction has A in
# it, so a sloppy implementation might decide A is "supported" and return
# True. Resolution-refutation correctly returns False because resolving
# (A v B) with (~A) only produces (B), not the empty clause.
def test_given_disjunction_only_when_querying_one_disjunct_then_not_entailed():
    from resolution import entails
    assert entails([parse("OR A B")], parse("A")) is False


# {A -> B} alone does not entail B. The implication is vacuously satisfied
# whenever A is false, so B is not forced. Same reasoning as the previous
# test in the implication form.
def test_given_only_implication_when_querying_consequent_then_not_entailed():
    from resolution import entails
    assert entails([parse("IMPLIES A B")], parse("B")) is False


# Biconditional in the KB. {A <-> B, A} |= B exercises the full pipeline:
# CNF must rewrite A <-> B into (~A v B) ^ (~B v A), clauses_from_cnf must
# split that into two separate clauses, and entails must combine the result
# with the unit clause {A} to derive B. A bug in any of those three steps
# breaks this test, so it serves as an integration check across the stack.
def test_given_kb_with_biconditional_when_one_side_known_then_other_entailed():
    from resolution import entails
    kb = [parse("BICONDITIONAL A B"), parse("A")]
    assert entails(kb, parse("B")) is True
