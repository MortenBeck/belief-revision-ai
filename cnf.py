# cnf.py

from parse import Atom, Not, Operator


def eliminate_implications(node):
    """First step in converting to CNF: eliminate IMPLIES and BICONDITIONAL operators."""
    if isinstance(node, Atom):
        return node

    if isinstance(node, Not):
        return Not(eliminate_implications(node.child))

    if isinstance(node, Operator):
        left = eliminate_implications(node.left)
        right = eliminate_implications(node.right)

        if node.operator == 'IMPLIES':
            return Operator('OR', Not(left), right)

        if node.operator == 'BICONDITIONAL':
            return Operator(
                'AND',
                Operator('OR', Not(left), right),
                Operator('OR', Not(right), left)
            )

        return Operator(node.operator, left, right)


def push_not(node):
    """Second step: push NOT operators inward"""
    if isinstance(node, Atom):
        return node

    if isinstance(node, Not):
        child = node.child

        if isinstance(child, Atom):
            return node

        if isinstance(child, Not):
            return push_not(child.child)

        if isinstance(child, Operator):
            if child.operator == 'AND':
                return Operator(
                    'OR',
                    push_not(Not(child.left)),
                    push_not(Not(child.right))
                )

            if child.operator == 'OR':
                return Operator(
                    'AND',
                    push_not(Not(child.left)),
                    push_not(Not(child.right))
                )

    if isinstance(node, Operator):
        return Operator(
            node.operator,
            push_not(node.left),
            push_not(node.right)
        )


def distribute(node):
    """Third step: distribute OR over AND."""
    if isinstance(node, Atom) or isinstance(node, Not):
        return node

    left = distribute(node.left)
    right = distribute(node.right)

    if node.operator == 'OR':
        if isinstance(left, Operator) and left.operator == 'AND':
            return Operator(
                'AND',
                distribute(Operator('OR', left.left, right)),
                distribute(Operator('OR', left.right, right))
            )

        if isinstance(right, Operator) and right.operator == 'AND':
            return Operator(
                'AND',
                distribute(Operator('OR', left, right.left)),
                distribute(Operator('OR', left, right.right))
            )

    return Operator(node.operator, left, right)


def to_cnf(tree):
    step1 = eliminate_implications(tree)
    step2 = push_not(step1)
    step3 = distribute(step2)
    return step3