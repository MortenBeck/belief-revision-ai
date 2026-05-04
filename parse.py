class Node:
    """Base class for all nodes in the parse tree."""
    pass

class Atom(Node):
    """"A variable in the tree structure, such as A, B, C, etc."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name
    
class Not(Node):
    """"This class if for negation"""
    def __init__(self, child):
        self.child = child

    def __repr__(self):
        return f"Not({self.child})"
    
class Operator(Node):
    """"Class for binary operators like AND, OR, IMPLIES, BICONDITIONAL"""
    def __init__(self, operator, left, right):
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.operator}({self.left}, {self.right})"
    
BINARY_OPERATORS = {'AND', 'OR', 'IMPLIES', 'BICONDITIONAL'}
UNARY_OPERATORS = {'NOT'}
# Here the operators are defined
    
def tokenize(input_string):
    """Split the input into tokens.

    Whitespace separates tokens. Parentheses are pre-padded with spaces so
    they tokenize on their own even when written flush against an operator
    (e.g. ``IMPLIES(AND A B)C`` becomes ``IMPLIES ( AND A B ) C``).

    No other punctuation is recognised: commas, dots, etc. become part of
    the surrounding token and will fail later as "Unknown token". So
    ``IMPLIES(A,B)`` does NOT work — operands must be space-separated.
    Valid forms: ``IMPLIES A B``, ``IMPLIES (AND A B) C``.
    """
    tokens = input_string.replace('(', ' ( ').replace(')', ' ) ').split()
    return tokens

def parse(tokens):
    """"This function takes a list of tokens and recursively builds a tree structure"""
    if not tokens:
        raise ValueError("Unexpected end of input")
    
    #Here we split the first token from the rest
    token = tokens[0]
    tokens = tokens[1:]

    # Handle opening parenthesis
    if token == '(':
        result, tokens = parse(tokens)
        if not tokens or tokens[0] != ')':
            raise ValueError("Expected ')'")
        return result, tokens[1:]  # Skip the ')'
    
    # Normalize to uppercase for standardization
    token_upper = token.upper()
    
    # Case for if the token is a unary operator (NOT)
    if token_upper in UNARY_OPERATORS:
        child, tokens = parse(tokens)
        return Not(child), tokens
    
    # Case for if the token is a binary operator (AND, OR, IMPLIES, BICONDITIONAL)
    if token_upper in BINARY_OPERATORS:
        left, tokens = parse(tokens)
        right, tokens = parse(tokens)
        return Operator(token_upper, left, right), tokens
    
    # Case for if the token is an atom (a variable)
    if token.isalpha():
        return Atom(token.upper()), tokens
    
    raise ValueError(f"Unknown token: {token}")


def parse_formula(input_string):
    """Here we take the input string, tokenize it, and parse it into a tree structure."""
    tokens = tokenize(input_string)
    tree, remaining = parse(tokens)
    
    if remaining:
        raise ValueError(f"Unexpected tokens at end: {remaining}")
    
    return tree

#Test
if __name__ == "__main__":
    # Interactive mode
    while True:
        user_input = input("Enter formula (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        
        try:
            tree = parse_formula(user_input)
            print(f"Result: {tree}\n")
        except Exception as e:
            print(f"Error: {e}\n")