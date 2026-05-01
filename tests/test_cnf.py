import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula, Atom, Not, Operator
from cnf import to_cnf, eliminate_implications, push_not, distribute


def cnf(s):
    return to_cnf(parse_formula(s))


def is_literal(node):
    return isinstance(node, Atom) or (isinstance(node, Not) and isinstance(node.child, Atom))


def is_clause(node):
    if is_literal(node):
        return True
    return (
        isinstance(node, Operator)
        and node.operator == "OR"
        and is_clause(node.left)
        and is_clause(node.right)
    )


def is_cnf(node):
    if is_clause(node):
        return True
    return (
        isinstance(node, Operator)
        and node.operator == "AND"
        and is_cnf(node.left)
        and is_cnf(node.right)
    )


def test_atom_unchanged():
    result = cnf("A")
    assert isinstance(result, Atom)
    assert result.name == "A"


def test_negated_atom_unchanged():
    result = cnf("NOT A")
    assert isinstance(result, Not)
    assert isinstance(result.child, Atom)


def test_implies_eliminated():
    # A -> B  becomes  ~A v B
    result = cnf("IMPLIES A B")
    assert isinstance(result, Operator)
    assert result.operator == "OR"
    assert isinstance(result.left, Not)
    assert result.left.child.name == "A"
    assert result.right.name == "B"


def test_biconditional_eliminated():
    result = cnf("BICONDITIONAL A B")
    assert isinstance(result, Operator)
    assert result.operator == "AND"
    assert is_cnf(result)


def test_double_negation_eliminated():
    result = cnf("NOT (NOT A)")
    assert isinstance(result, Atom)
    assert result.name == "A"


def test_triple_negation_collapses_to_single():
    result = cnf("NOT (NOT (NOT A))")
    assert isinstance(result, Not)
    assert isinstance(result.child, Atom)
    assert result.child.name == "A"


def test_de_morgan_and():
    # ~(A ^ B)  becomes  ~A v ~B
    result = cnf("NOT (AND A B)")
    assert isinstance(result, Operator)
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert isinstance(result.right, Not) and result.right.child.name == "B"


def test_de_morgan_or():
    # ~(A v B)  becomes  ~A ^ ~B
    result = cnf("NOT (OR A B)")
    assert isinstance(result, Operator)
    assert result.operator == "AND"


def test_or_distributes_over_and():
    # A v (B ^ C)  becomes  (A v B) ^ (A v C)
    result = cnf("OR A (AND B C)")
    assert isinstance(result, Operator)
    assert result.operator == "AND"
    assert is_cnf(result)


def test_or_distributes_other_side():
    # (A ^ B) v C  becomes  (A v C) ^ (B v C)
    result = cnf("OR (AND A B) C")
    assert result.operator == "AND"
    assert is_cnf(result)


def test_cnf_idempotent():
    once = cnf("AND (OR A B) (OR C D)")
    twice = to_cnf(once)
    assert repr(once) == repr(twice)


def test_complex_formula_is_cnf():
    # (A -> B) ^ (B -> C) should produce valid CNF
    result = cnf("AND (IMPLIES A B) (IMPLIES B C)")
    assert is_cnf(result)


def test_nested_implication_is_cnf():
    # (A -> (B -> C))  =>  ~A v ~B v C
    result = cnf("IMPLIES A (IMPLIES B C)")
    assert is_cnf(result)


def test_biconditional_with_compound_is_cnf():
    result = cnf("BICONDITIONAL A (OR B C)")
    assert is_cnf(result)


# --- Step-by-step pipeline behavior ---
# These document what each stage of to_cnf does in isolation, in the order
# they are composed: eliminate_implications -> push_not -> distribute.

def test_given_no_implications_when_eliminating_implications_then_tree_unchanged():
    tree = parse_formula("AND A (OR B (NOT C))")
    assert repr(eliminate_implications(tree)) == repr(tree)


def test_given_implication_when_eliminating_then_rewritten_as_disjunction():
    # A -> B  becomes  ~A v B
    result = eliminate_implications(parse_formula("IMPLIES A B"))
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert result.right.name == "B"


def test_given_biconditional_when_eliminating_then_conjunction_of_two_disjunctions():
    # A <-> B  becomes  (~A v B) ^ (~B v A)
    result = eliminate_implications(parse_formula("BICONDITIONAL A B"))
    assert result.operator == "AND"
    assert result.left.operator == "OR"
    assert result.right.operator == "OR"


def test_given_negation_of_atom_when_pushing_not_then_unchanged():
    tree = parse_formula("NOT A")
    assert repr(push_not(tree)) == repr(tree)


def test_given_negation_of_conjunction_when_pushing_not_then_de_morgan_applied():
    # ~(A ^ B)  becomes  ~A v ~B
    result = push_not(parse_formula("NOT (AND A B)"))
    assert result.operator == "OR"
    assert isinstance(result.left, Not) and result.left.child.name == "A"
    assert isinstance(result.right, Not) and result.right.child.name == "B"


def test_given_negation_of_disjunction_when_pushing_not_then_de_morgan_applied():
    # ~(A v B)  becomes  ~A ^ ~B
    result = push_not(parse_formula("NOT (OR A B)"))
    assert result.operator == "AND"


def test_given_double_negation_when_pushing_not_then_collapsed_to_atom():
    result = push_not(parse_formula("NOT (NOT A)"))
    assert isinstance(result, Atom)
    assert result.name == "A"


def test_given_clause_without_inner_and_when_distributing_then_still_clause():
    # distribute is structurally a no-op on a pure disjunction of literals
    result = distribute(parse_formula("OR A (OR B C)"))
    assert is_clause(result)


def test_given_or_over_and_when_distributing_then_split_into_two_clauses():
    # A v (B ^ C)  becomes  (A v B) ^ (A v C)
    result = distribute(parse_formula("OR A (AND B C)"))
    assert result.operator == "AND"
    assert result.left.operator == "OR"
    assert result.right.operator == "OR"


def test_given_and_over_or_when_distributing_then_unchanged():
    # AND distributes-over-OR is NOT done by CNF (only OR over AND).
    # (A ^ B) v ... is the case that needs distributing; A ^ (B v C) is already CNF.
    tree = parse_formula("AND A (OR B C)")
    result = distribute(tree)
    assert is_cnf(result)
    assert result.operator == "AND"
