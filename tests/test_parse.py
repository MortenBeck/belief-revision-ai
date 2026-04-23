import unittest
import sys
import os

# Add parent directory to path so we can import parse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parse import parse_formula, Not, Operator, Atom


class TestParser(unittest.TestCase):
    
    def test_simple_and(self):
        tree = parse_formula("AND A B")
        self.assertEqual(tree.operator, "AND")
        self.assertEqual(tree.left.name, "A")
        self.assertEqual(tree.right.name, "B")
    
    def test_simple_or(self):
        tree = parse_formula("OR A B")
        self.assertEqual(tree.operator, "OR")
    
    def test_not(self):
        tree = parse_formula("NOT A")
        self.assertIsInstance(tree, Not)
        self.assertEqual(tree.child.name, "A")
    
    def test_implies(self):
        tree = parse_formula("IMPLIES A B")
        self.assertEqual(tree.operator, "IMPLIES")
    
    def test_nested(self):
        tree = parse_formula("IMPLIES (AND A B) C")
        self.assertEqual(tree.operator, "IMPLIES")
        self.assertEqual(tree.left.operator, "AND")
        self.assertEqual(tree.right.name, "C")
    
    def test_case_insensitive(self):
        tree1 = parse_formula("and a b")
        tree2 = parse_formula("AND A B")
        self.assertEqual(tree1.operator, tree2.operator)
        self.assertEqual(tree1.left.name, tree2.left.name)
    
    def test_parentheses_around_not(self):
        tree = parse_formula("(NOT A)")
        self.assertIsInstance(tree, Not)
    
    def test_complex_nested(self):
        tree = parse_formula("AND (OR A B) (NOT C)")
        self.assertEqual(tree.operator, "AND")
        self.assertEqual(tree.left.operator, "OR")
        self.assertIsInstance(tree.right, Not)
    
    def test_biconditional(self):
        tree = parse_formula("BICONDITIONAL A (OR B C)")
        self.assertEqual(tree.operator, "BICONDITIONAL")
    
    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            parse_formula("AND A")  # Missing second operand
    
    def test_unexpected_tokens(self):
        with self.assertRaises(ValueError):
            parse_formula("AND A B C")  # Extra token at the end


if __name__ == '__main__':
    unittest.main()