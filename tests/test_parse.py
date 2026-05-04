# test_parse.py
#
# Unit tests for parse.py — the Polish-notation tokenizer and recursive-descent
# parser that turns input strings into Atom/Not/Operator AST nodes. Written in
# pytest style to match test_cnf.py and test_resolution.py.

import sys
import os

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula, Not, Operator, Atom


# --- happy path: each operator and a few nested shapes ---

def test_simple_and():
    tree = parse_formula("AND A B")
    assert tree.operator == "AND"
    assert tree.left.name == "A"
    assert tree.right.name == "B"


def test_simple_or():
    tree = parse_formula("OR A B")
    assert tree.operator == "OR"


def test_not():
    tree = parse_formula("NOT A")
    assert isinstance(tree, Not)
    assert tree.child.name == "A"


def test_implies():
    tree = parse_formula("IMPLIES A B")
    assert tree.operator == "IMPLIES"


def test_biconditional():
    tree = parse_formula("BICONDITIONAL A (OR B C)")
    assert tree.operator == "BICONDITIONAL"


def test_nested():
    tree = parse_formula("IMPLIES (AND A B) C")
    assert tree.operator == "IMPLIES"
    assert tree.left.operator == "AND"
    assert tree.right.name == "C"


def test_complex_nested():
    tree = parse_formula("AND (OR A B) (NOT C)")
    assert tree.operator == "AND"
    assert tree.left.operator == "OR"
    assert isinstance(tree.right, Not)


def test_parentheses_around_not():
    tree = parse_formula("(NOT A)")
    assert isinstance(tree, Not)


def test_case_insensitive():
    tree1 = parse_formula("and a b")
    tree2 = parse_formula("AND A B")
    assert tree1.operator == tree2.operator
    assert tree1.left.name == tree2.left.name


# --- error paths ---
# Each of these documents one shape of invalid input. Going through the parser
# code (parse.py) shows three distinct failure modes — missing operand,
# leftover tokens, and unrecognised tokens — and we want one test per mode so a
# regression points straight at the broken branch.

# Missing operand for a binary operator: the recursive call runs out of tokens
# before it can read the second argument.
def test_invalid_input_missing_operand():
    with pytest.raises(ValueError):
        parse_formula("AND A")


# Trailing junk after a complete formula: parse() returns successfully but
# parse_formula sees there are tokens left over and raises.
def test_unexpected_tokens_at_end():
    with pytest.raises(ValueError):
        parse_formula("AND A B C")


# Unbalanced parentheses: an opening "(" is consumed but no matching ")" ever
# appears. Currently untested even though parse.py:53 explicitly raises for it.
def test_unbalanced_parentheses():
    with pytest.raises(ValueError):
        parse_formula("(AND A B")


# Empty input: tokenize returns [] and parse() should fail fast rather than
# silently produce None or a malformed tree.
def test_empty_input():
    with pytest.raises(ValueError):
        parse_formula("")


# Truly unrecognised token: a non-alphabetic symbol that is neither "(" nor
# ")" nor any operator keyword. This is the only input that lands on the
# final "Unknown token" raise at parse.py:74 — alphabetic non-operators like
# "XOR" are treated as atoms instead.
def test_unknown_token():
    with pytest.raises(ValueError):
        parse_formula("@@")
