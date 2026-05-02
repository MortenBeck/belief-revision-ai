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


def clauses_from_cnf(node):
    """Flatten a CNF parse tree into a list of clauses (frozensets of literals).

    Recurses through AND nodes at any depth so nested conjunctions are
    flattened; anything else is treated as a single clause.
    """
    if isinstance(node, Operator) and node.operator == 'AND':
        return clauses_from_cnf(node.left) + clauses_from_cnf(node.right)
    return [frozenset(convert_to_set(node))]


def _is_tautology(clause):
    return any(negate(lit) in clause for lit in clause)


def _resolve(c1, c2):
    """All non-trivial resolvents of two clauses."""
    resolvents = set()
    for lit in c1:
        if negate(lit) in c2:
            resolvents.add(frozenset((c1 - {lit}) | (c2 - {negate(lit)})))
    return resolvents


def entails(kb_formulas, query):
    """Decide KB |= query by resolution-refutation."""
    clauses = set()
    for formula in kb_formulas:
        for c in clauses_from_cnf(to_cnf(formula)):
            if not _is_tautology(c):
                clauses.add(c)

    for c in clauses_from_cnf(to_cnf(Not(query))):
        if not _is_tautology(c):
            clauses.add(c)

    if frozenset() in clauses:
        return True

    while True:
        new = set()
        clause_list = list(clauses)
        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                for r in _resolve(clause_list[i], clause_list[j]):
                    if not r:
                        return True
                    if not _is_tautology(r):
                        new.add(r)
        if new.issubset(clauses):
            return False
        clauses |= new



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
