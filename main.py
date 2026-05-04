# main.py

from parse import parse_formula
from cnf import to_cnf
from resolution import clauses_from_cnf
from belief_base import BeliefBase


HELP = """\
Commands:
  add <formula>           - expand belief base with formula (auto-priority)
  add <priority> <formula>- expand with explicit integer priority (higher = more entrenched)
  contract <formula>      - partial meet contraction: remove formula from KB
  revise <formula>        - AGM revision: contract ~formula, then add formula
  entails <formula>       - check whether KB entails formula
  kb                      - list current belief base with priorities
  clear                   - empty the belief base
  cnf <formula>           - show CNF form of formula
  clauses <formula>       - show clausal form of formula
  help                    - show this message
  quit                    - exit

Formulas use Polish/prefix notation:
  AND A B   OR A B   NOT A   IMPLIES A B   BICONDITIONAL A B
Use parentheses to group: IMPLIES (AND A B) C

Priority: higher number = more entrenched = survives contraction when possible.
Default priority is assigned automatically (later additions get higher priority).
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


def _parse_add_arg(arg):
    """Parse 'add' argument into (formula_string, optional_priority).

    Accepts:
      add A                -> ("A", None)
      add 5 A              -> ("A", 5)
      add 5 IMPLIES A B    -> ("IMPLIES A B", 5)
    """
    tokens = arg.split(None, 1)
    if tokens and tokens[0].lstrip('-').isdigit():
        priority = int(tokens[0])
        formula_str = tokens[1] if len(tokens) > 1 else ""
        return formula_str, priority
    return arg, None


def main():
    print("Belief Revision REPL")
    print(HELP)

    kb = BeliefBase()

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
                    for i, (f, pri) in enumerate(kb.beliefs(), 1):
                        print(f"  {i}. {f}  [priority: {pri}]")

            elif cmd == "clear":
                kb.clear()
                print("KB cleared.")

            elif cmd == "add":
                if not arg:
                    print("Error: 'add' needs a formula")
                    continue
                formula_str, priority = _parse_add_arg(arg)
                if not formula_str:
                    print("Error: 'add' needs a formula after the priority")
                    continue
                tree = parse_formula(formula_str)
                kb.expand(tree, priority=priority)
                _, stored_pri = kb.beliefs()[-1]
                print(f"Added: {tree}  [priority: {stored_pri}]")

            elif cmd == "contract":
                if not arg:
                    print("Error: 'contract' needs a formula")
                    continue
                phi = parse_formula(arg)
                before = len(kb)
                kb.contract(phi)
                after = len(kb)
                removed = before - after
                print(f"Contracted.  Removed {removed} formula(s).  KB now has {after} formula(s).")

            elif cmd == "revise":
                if not arg:
                    print("Error: 'revise' needs a formula")
                    continue
                phi = parse_formula(arg)
                before = len(kb)
                kb.revise(phi)
                after = len(kb)
                print(f"Revised with {phi}.  KB now has {after} formula(s).")

            elif cmd == "entails":
                if not arg:
                    print("Error: 'entails' needs a formula")
                    continue
                query = parse_formula(arg)
                print("yes" if kb.entails(query) else "no")

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
