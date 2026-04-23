# main.py

from parse import parse_formula
from cnf import to_cnf


def main():
    while True:
        user_input = input("Enter formula (or 'quit'): ")

        if user_input.lower() == 'quit':
            break

        try:
            tree = parse_formula(user_input)
            cnf_tree = to_cnf(tree)

            print(f"Parsed: {tree}")
            print(f"CNF:    {cnf_tree}\n")

        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    main()