from parse import Atom, Not, Operator, parse_formula
from cnf import to_cnf

def convert_to_set(node):
    """We convert the tree structure back to sets of strings(as it's meant to look like in the belief base)"""
    if isinstance(node, Atom):
        return {node.name}
    if isinstance(node, Not):
        return {f"~{node.child.name}"}
    if isinstance(node, Operator) and node.operator == 'OR':
        left_set = convert_to_set(node.left)
        right_set = convert_to_set(node.right)
        return left_set | right_set
    return set()

def convert_from_single_to_multiple(node):
    """If we have any "AND" operators, we need to convert them to multiple clauses"""
    if isinstance(node, Operator) and node.operator == 'AND':
        left_clause = convert_to_set(node.left)
        right_clause = convert_to_set(node.right)
        return [left_clause, right_clause]
    else:
        return [convert_to_set(node)]
    
def negate(var):
    """Method to negate a variable"""
    if var.startswith('~'):
        return var[1:]
    return f'~{var}'





if __name__ == "__main__":
    # WE PROBABLY NEED A DIFFERENT FORMATTING WITH V INSTEAD OF JUST COMMAS

    # Test: OR(A, NOT(B))
    formula = to_cnf(parse_formula("OR A (NOT B)"))
    result = convert_to_set(formula)
    print(result)  # Should print: {'A', '~B'}

    # Test: AND(A, OR(B, NOT(C)))
    formula2 = to_cnf(parse_formula("AND A (OR B (NOT C))"))
    result2 = convert_from_single_to_multiple(formula2)
    print(result2)  # Should print: [{'A'}, {'B', '~C'}]
