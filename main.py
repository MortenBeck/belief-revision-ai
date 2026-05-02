# main.py

from parse import parse_formula
from cnf import to_cnf
from resolution import entails, clauses_from_cnf


HELP = """\
Commands:
  add <formula>     - add formula to the belief base (KB)
  entails <formula> - check whether KB entails formula
  kb                - list current belief base
  clear             - empty the belief base
  cnf <formula>     - show CNF form of formula
  clauses <formula> - show clausal form of formula
  help              - show this message
  quit              - exit

Formulas use Polish/prefix notation:
  AND A B   OR A B   NOT A   IMPLIES A B   BICONDITIONAL A B
Use parentheses to group: IMPLIES (AND A B) C
"""


def format_clauses(clauses):
    """Render a clause list as a set of disjunctions."""
    if not clauses:
        return "{}"
    parts = []
    for c in clauses:
        if not c:
            parts.append("[]")
        elif len(c) == 1:
            parts.append(next(iter(c)))
        else:
            parts.append("(" + " v ".join(sorted(c)) + ")")
    return "{" + ", ".join(parts) + "}"


def main():
    print("Belief Revision REPL")
    print(HELP)

    kb = []

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        parts = line.split(None, 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        try:
            if cmd in ("quit", "exit"):
                break

            elif cmd == "help":
                print(HELP)

            elif cmd == "kb":
                if not kb:
                    print("(empty)")
                else:
                    for i, f in enumerate(kb, 1):
                        print(f"  {i}. {f}")

            elif cmd == "clear":
                kb.clear()
                print("KB cleared.")

            elif cmd == "add":
                if not arg:
                    print("Error: 'add' needs a formula")
                    continue
                tree = parse_formula(arg)
                kb.append(tree)
                print(f"Added: {tree}")

            elif cmd == "entails":
                if not arg:
                    print("Error: 'entails' needs a formula")
                    continue
                query = parse_formula(arg)
                print("yes" if entails(kb, query) else "no")

            elif cmd == "cnf":
                if not arg:
                    print("Error: 'cnf' needs a formula")
                    continue
                print(to_cnf(parse_formula(arg)))

            elif cmd == "clauses":
                if not arg:
                    print("Error: 'clauses' needs a formula")
                    continue
                print(format_clauses(clauses_from_cnf(to_cnf(parse_formula(arg)))))

            else:
                print(f"Unknown command: {cmd}. Type 'help' for usage.")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
