# test_cnf.py
#
# Unit tests for the CNF (Conjunctive Normal Form) conversion pipeline in cnf.py.
# A formula is in CNF when it is a conjunction (AND) of clauses, where each
# clause is a disjunction (OR) of literals, and each literal is either an atom
# or a negated atom. Example CNF: (A v ~B) ^ (C v D v ~E).
#
# The pipeline in cnf.py is composed of three stages, applied in order:
#   1. eliminate_implications  — rewrites IMPLIES and BICONDITIONAL using only
#                                AND, OR, and NOT.
#   2. push_not                — moves NOT operators inward using De Morgan's
#                                laws and double-negation elimination, so NOT
#                                only ever sits directly in front of an atom.
#   3. distribute              — distributes OR over AND so that no AND is
#                                nested inside an OR.
#
# Tests are split into two groups:
#   - End-to-end tests that exercise the full to_cnf() pipeline on parsed
#     formulas and check the result is a valid CNF tree.
#   - Step-by-step tests that exercise each individual stage in isolation, so a
#     regression is easy to localize to the offending stage.

import sys
import os

# Make the project root importable so we can pull in parse and cnf without
# needing to install the project as a package. tests/ lives one level below
# the modules it tests, so we prepend the parent directory to sys.path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula, Atom, Not, Operator
from cnf import to_cnf, eliminate_implications, push_not, distribute


# Convenience helper: parse a Polish-notation string and run it through the
# full CNF pipeline. Most tests below want a CNF tree from a string, and this
# wrapper keeps the test bodies readable.
def cnf(s):
    return to_cnf(parse_formula(s))


# --- structural validators ---
# These three predicates recursively check whether a parse tree has a CNF
# shape. They are NOT what we are testing — they are the oracles used by the
# tests to assert "the result is in CNF" without hard-coding a specific tree.
#
# A literal is the smallest CNF building block: an atom (e.g. A) or the
# negation of an atom (e.g. ~A). Any deeper structure inside a NOT means the
# tree is not yet in CNF.
def is_literal(node):
    return isinstance(node, Atom) or (isinstance(node, Not) and isinstance(node.child, Atom))


# A clause is either a single literal or an OR-tree whose leaves are all
# literals. So (A), (A v B), and (A v ~B v C) are all clauses.
def is_clause(node):
    if is_literal(node):
        return True
    return (
        isinstance(node, Operator)
        and node.operator == "OR"
        and is_clause(node.left)
        and is_clause(node.right)
    )


# A formula is in CNF if it is a clause, or an AND-tree whose leaves are all
# clauses. Crucially, this rejects any tree where an AND is found inside an
# OR — that's the situation `distribute` exists to fix.
def is_cnf(node):
    if is_clause(node):
        return True
    return (
        isinstance(node, Operator)
        and node.operator == "AND"
        and is_cnf(node.left)
        and is_cnf(node.right)
    )


# --- end-to-end pipeline tests ---
# Each of these feeds a Polish-notation string into to_cnf() and checks that
# the result has the expected shape. They cover the canonical rewrites a CNF
# converter must perform.

# A bare atom is already in CNF — no rewriting should happen.
def test_atom_unchanged():
    result = cnf("A")
    assert isinstance(result, Atom)
    assert result.name == "A"


# A negated atom is also already in CNF — push_not has nothing to push past.
def test_negated_atom_unchanged():
    result = cnf("NOT A")
    assert isinstance(result, Not)
    assert isinstance(result.child, Atom)


# Implication elimination: A -> B is logically equivalent to ~A v B, which is
# a single clause and therefore already CNF after the rewrite.
def test_implies_eliminated():
    result = cnf("IMPLIES A B")
    assert isinstance(result, Operator)
    assert result.operator == "OR"
    assert isinstance(result.left, Not)
    assert result.left.child.name == "A"
    assert result.right.name == "B"


# Biconditional elimination: A <-> B becomes (~A v B) ^ (~B v A). This is the
# standard "implication in both directions" rewrite, and it produces a top-
# level AND of two clauses — already a textbook CNF shape.
def test_biconditional_eliminated():
    result = cnf("BICONDITIONAL A B")
    assert isinstance(result, Operator)
    assert result.operator == "AND"
    assert is_cnf(result)


# Double-negation elimination: ~~A reduces to A. push_not is responsible for
# this; if it ever stops firing the test will catch it.
def test_double_negation_eliminated():
    result = cnf("NOT (NOT A)")
    assert isinstance(result, Atom)
    assert result.name == "A"


# Triple negation should collapse to a single negation: ~~~A becomes ~A.
# This is essentially "double negation applied once, leaving one NOT behind".
def test_triple_negation_collapses_to_single():
    result = cnf("NOT (NOT (NOT A))")
    assert isinstance(result, Not)
    assert isinstance(result.child, Atom)
    assert result.child.name == "A"


# De Morgan over AND: ~(A ^ B) becomes ~A v ~B. The NOT distributes across
# the conjunction and flips it to a disjunction.
def test_de_morgan_and():
    result = cnf("NOT (AND A B)")
    assert isinstance(result, Operator)
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert isinstance(result.right, Not) and result.right.child.name == "B"


# De Morgan over OR: ~(A v B) becomes ~A ^ ~B. The dual of the previous test.
def test_de_morgan_or():
    result = cnf("NOT (OR A B)")
    assert isinstance(result, Operator)
    assert result.operator == "AND"


# Distributivity: A v (B ^ C) becomes (A v B) ^ (A v C). This is the rewrite
# that turns "an AND lives inside an OR" into "two ORs sit under a single AND",
# which is what makes the tree CNF-shaped rather than just NNF (negation
# normal form).
def test_or_distributes_over_and():
    result = cnf("OR A (AND B C)")
    assert isinstance(result, Operator)
    assert result.operator == "AND"
    assert is_cnf(result)


# Distributivity from the other side: (A ^ B) v C becomes (A v C) ^ (B v C).
# Same rule, AND-on-the-left instead of AND-on-the-right.
def test_or_distributes_other_side():
    result = cnf("OR (AND A B) C")
    assert result.operator == "AND"
    assert is_cnf(result)


# Distributivity blow-up: (A ^ B) v (C ^ D) must produce all four pairwise
# clauses (A v C) ^ (A v D) ^ (B v C) ^ (B v D). This is the case where naive
# distribute implementations recurse on only one side and silently drop
# clauses. We check the resulting tree is CNF and that all four expected
# clauses appear after extracting them.
def test_or_distributes_when_both_sides_are_and():
    from resolution import clauses_from_cnf
    result = cnf("OR (AND A B) (AND C D)")
    assert is_cnf(result)
    assert set(clauses_from_cnf(result)) == {
        frozenset({"A", "C"}),
        frozenset({"A", "D"}),
        frozenset({"B", "C"}),
        frozenset({"B", "D"}),
    }


# Idempotence: running to_cnf on something that is already in CNF should be a
# no-op. This is important because resolution will repeatedly produce CNF
# clauses, and we don't want the second pass to mutate them.
def test_cnf_idempotent():
    once = cnf("AND (OR A B) (OR C D)")
    twice = to_cnf(once)
    assert repr(once) == repr(twice)


# A small integration test: two implications joined by AND should turn into
# (~A v B) ^ (~B v C). We don't pin the exact tree, just that whatever comes
# out is structurally CNF.
def test_complex_formula_is_cnf():
    result = cnf("AND (IMPLIES A B) (IMPLIES B C)")
    assert is_cnf(result)


# Right-associated implication: A -> (B -> C) is equivalent to ~A v ~B v C,
# a single three-literal clause. Worth testing because it exercises nested
# implication elimination.
def test_nested_implication_is_cnf():
    result = cnf("IMPLIES A (IMPLIES B C)")
    assert is_cnf(result)


# Biconditional whose right-hand side is itself a compound formula. The
# rewrite produces something more elaborate than the simple A <-> B case,
# so this guards against bugs that only appear with non-atomic operands.
def test_biconditional_with_compound_is_cnf():
    result = cnf("BICONDITIONAL A (OR B C)")
    assert is_cnf(result)


# --- step-by-step pipeline behavior ---
# These document what each stage of to_cnf does in isolation, in the order
# they are composed: eliminate_implications -> push_not -> distribute. They
# are written in given/when/then style so each test reads as a one-line spec
# of the stage's behavior. Use these to localize bugs: if the end-to-end test
# fails but every per-stage test still passes, the bug is in composition;
# otherwise it's in the failing stage.

# eliminate_implications has nothing to rewrite if the input contains only
# AND, OR, and NOT, so it should return a structurally identical tree.
def test_given_no_implications_when_eliminating_implications_then_tree_unchanged():
    tree = parse_formula("AND A (OR B (NOT C))")
    assert repr(eliminate_implications(tree)) == repr(tree)


# Single implication rewrite, isolated from the rest of the pipeline.
# A -> B becomes ~A v B.
def test_given_implication_when_eliminating_then_rewritten_as_disjunction():
    result = eliminate_implications(parse_formula("IMPLIES A B"))
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert result.right.name == "B"


# Biconditional is rewritten as an AND of two ORs at this stage. Note that
# push_not and distribute have not run yet — we are checking the immediate
# output of eliminate_implications only.
def test_given_biconditional_when_eliminating_then_conjunction_of_two_disjunctions():
    # A <-> B  becomes  (~A v B) ^ (~B v A)
    result = eliminate_implications(parse_formula("BICONDITIONAL A B"))
    assert result.operator == "AND"
    assert result.left.operator == "OR"
    assert result.right.operator == "OR"


# push_not has no work to do when the negation already sits directly in front
# of an atom. The output should be the same Not(Atom) tree.
def test_given_negation_of_atom_when_pushing_not_then_unchanged():
    tree = parse_formula("NOT A")
    assert repr(push_not(tree)) == repr(tree)


# De Morgan in isolation. We bypass eliminate_implications and feed push_not
# a tree that already only contains AND/OR/NOT. ~(A ^ B) becomes ~A v ~B.
def test_given_negation_of_conjunction_when_pushing_not_then_de_morgan_applied():
    result = push_not(parse_formula("NOT (AND A B)"))
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert isinstance(result.right, Not) and result.right.child.name == "B"


# The dual De Morgan rewrite. ~(A v B) becomes ~A ^ ~B.
def test_given_negation_of_disjunction_when_pushing_not_then_de_morgan_applied():
    result = push_not(parse_formula("NOT (OR A B)"))
    assert result.operator == "AND"


# Double negation elimination is also push_not's responsibility — when it sees
# Not(Not(x)) it should recurse into x and drop both negations.
def test_given_double_negation_when_pushing_not_then_collapsed_to_atom():
    result = push_not(parse_formula("NOT (NOT A)"))
    assert isinstance(result, Atom)
    assert result.name == "A"


# distribute is a no-op when there is no AND nested inside an OR. A pure
# disjunction of literals (a clause) goes in, the same shape comes out.
def test_given_clause_without_inner_and_when_distributing_then_still_clause():
    result = distribute(parse_formula("OR A (OR B C)"))
    assert is_clause(result)


# The core distributive rewrite, isolated. A v (B ^ C) becomes (A v B) ^ (A v C).
# After this, the AND is at the top level and each side is a clause.
def test_given_or_over_and_when_distributing_then_split_into_two_clauses():
    result = distribute(parse_formula("OR A (AND B C)"))
    assert result.operator == "AND"
    assert result.left.operator == "OR"
    assert result.right.operator == "OR"


# CNF only requires us to distribute OR over AND, NOT the other way around.
# A formula like A ^ (B v C) is already CNF — distribute should leave it alone.
# This test guards against an over-eager distribute that tries to turn it into
# (A ^ B) v (A ^ C), which would actually take us OUT of CNF.
def test_given_and_over_or_when_distributing_then_unchanged():
    tree = parse_formula("AND A (OR B C)")
    result = distribute(tree)
    assert is_cnf(result)
    assert result.operator == "AND"
