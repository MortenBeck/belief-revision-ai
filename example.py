"""Worked examples for the belief revision agent (used in the report).

Each example prints the belief base before/after the operation along with a
few entailment queries so the behaviour can be inspected.

Run with:
    python example.py
"""

from parse import parse_formula
from belief_base import BeliefBase


# ---------------------------------------------------------------- helpers --

def banner(title):
    bar = "=" * 72
    print(f"\n{bar}\n{title}\n{bar}")


def section(title):
    print(f"\n--- {title} ---")


def show_kb(kb):
    if not kb:
        print("  (empty)")
        return
    for i, (f, p) in enumerate(kb.beliefs(), 1):
        print(f"  {i}. {f}    [priority: {p}]")


def check(kb, formula_str):
    phi = parse_formula(formula_str)
    answer = "YES" if kb.entails(phi) else "no"
    print(f"  KB |= {formula_str:<40s}  ->  {answer}")


# ============================================================ EXAMPLE 1 ===
# Baseline: expansion + entailment by modus ponens.
# ==========================================================================
banner("Example 1 -- Expansion and entailment (modus ponens)")
print("KB: 'Birds fly' and 'Tweety is a Bird'.")
print("Resolution should derive 'Flies' even though it was never asserted.")

kb = BeliefBase()
kb.expand(parse_formula("IMPLIES Bird Flies"), priority=2)
kb.expand(parse_formula("Bird"),               priority=1)

section("Belief base")
show_kb(kb)
section("Queries")
check(kb, "Flies")           # entailed by modus ponens
check(kb, "Bird")            # asserted directly
check(kb, "NOT Bird")        # not entailed


# ============================================================ EXAMPLE 2 ===
# Contraction is decided by the priority ordering.
# ==========================================================================
banner("Example 2 -- Contraction guided by priority")
print("Both 'Bird' and 'Bird -> Flies' support 'Flies'. To stop entailing")
print("'Flies' we have to drop one of them. The lower-priority formula goes.")

kb = BeliefBase()
kb.expand(parse_formula("IMPLIES Bird Flies"), priority=1)   # weak: rule
kb.expand(parse_formula("Bird"),               priority=5)   # strong: observation

section("Before contraction")
show_kb(kb)
check(kb, "Flies")

print("\n>>> kb.contract(Flies)")
kb.contract(parse_formula("Flies"))

section("After contracting Flies")
show_kb(kb)
check(kb, "Flies")
check(kb, "Bird")            # high-priority observation is preserved


# ============================================================ EXAMPLE 3 ===
# AGM revision: classic Tweety / penguin scenario.
# ==========================================================================
banner("Example 3 -- AGM revision: Tweety turns out to be a penguin")
print("Old KB derives 'Flies'. New evidence says Tweety does NOT fly.")
print("revise = contract(NOT NOT Flies) then expand(NOT Flies).")

kb = BeliefBase()
kb.expand(parse_formula("IMPLIES Bird Flies"), priority=1)
kb.expand(parse_formula("Bird"),               priority=5)

section("Before revision")
show_kb(kb)
check(kb, "Flies")

print("\n>>> kb.revise(NOT Flies)")
kb.revise(parse_formula("NOT Flies"))

section("After revision")
show_kb(kb)
check(kb, "Flies")           # no longer entailed
check(kb, "NOT Flies")       # success postulate
check(kb, "Bird")            # high-priority belief survived


# ============================================================ EXAMPLE 4 ===
# Without AGM: blind expansion makes the KB inconsistent and explodes.
# ==========================================================================
banner("Example 4 -- Naive (non-AGM) expansion: ex falso quodlibet")
print("Same starting KB as Example 3, but instead of revising we just")
print("EXPAND with 'NOT Flies'. The KB is now logically inconsistent")
print("(it contains Bird, Bird -> Flies, AND NOT Flies all at once),")
print("so by classical logic it entails every formula whatsoever.")

kb = BeliefBase()
kb.expand(parse_formula("IMPLIES Bird Flies"), priority=1)
kb.expand(parse_formula("Bird"),               priority=5)
kb.expand(parse_formula("NOT Flies"),          priority=5)   # naive!

section("Inconsistent belief base")
show_kb(kb)

section("Watch the KB entail nonsense")
check(kb, "Flies")
check(kb, "NOT Flies")
check(kb, "MarsHasLittleGreenMen")
check(kb, "NOT MarsHasLittleGreenMen")
check(kb, "AtlantisExists")
check(kb, "AND MarsHasLittleGreenMen NOT MarsHasLittleGreenMen")

print("\n>>> Every query above returns YES. The KB has lost all ability")
print("    to distinguish truth from falsehood. This is exactly what AGM")
print("    revision is designed to prevent.")


# ============================================================ EXAMPLE 5 ===
# After the failure: revise (correctly) with an absurd belief.
# ==========================================================================
banner("Example 5 -- AGM revision survives even absurd input")
print("'MarsHasLittleGreenMen' is silly, but it does NOT contradict the KB,")
print("so AGM revision just adds it. The KB stays consistent.")
print("Then we revise with its NEGATION; this conflicts with what we just")
print("added, so contraction drops the absurd belief before the negation")
print("is added. The bird beliefs are completely untouched throughout.")

kb = BeliefBase()
kb.expand(parse_formula("IMPLIES Bird Flies"), priority=1)
kb.expand(parse_formula("Bird"),               priority=5)

section("Initial KB")
show_kb(kb)

print("\n>>> kb.revise(MarsHasLittleGreenMen)")
kb.revise(parse_formula("MarsHasLittleGreenMen"))
section("After revising in the absurdity")
show_kb(kb)
check(kb, "MarsHasLittleGreenMen")
check(kb, "Flies")                           # bird inference still works
check(kb, "AtlantisExists")                  # KB is NOT exploding -> 'no'

print("\n>>> kb.revise(NOT MarsHasLittleGreenMen)")
kb.revise(parse_formula("NOT MarsHasLittleGreenMen"))
section("After revising it back out")
show_kb(kb)
check(kb, "MarsHasLittleGreenMen")
check(kb, "NOT MarsHasLittleGreenMen")
check(kb, "Flies")                           # bird inference STILL works


# ============================================================ EXAMPLE 6 ===
# AGM postulates demonstrated on a tiny KB.
# ==========================================================================
banner("Example 6 -- AGM postulates on a minimal KB")

kb = BeliefBase()
kb.expand(parse_formula("P"), priority=1)
kb.expand(parse_formula("Q"), priority=1)

section("Initial KB")
show_kb(kb)

# --- vacuity ----------------------------------------------------------------
print("\nVacuity: contracting something the KB does not entail (R) is a no-op.")
kb.contract(parse_formula("R"))
show_kb(kb)

# --- success ----------------------------------------------------------------
print("\nSuccess: contracting P removes it from the KB.")
kb.contract(parse_formula("P"))
show_kb(kb)
check(kb, "P")

# --- success of revision ----------------------------------------------------
print("\nSuccess (revision): revising with NOT Q makes NOT Q believed.")
kb.revise(parse_formula("NOT Q"))
show_kb(kb)
check(kb, "Q")
check(kb, "NOT Q")

# --- consistency ------------------------------------------------------------
print("\nConsistency: the revised KB is still consistent.")
check(kb, "AND R NOT R")     # would only be 'YES' from an inconsistent KB


print("\n" + "=" * 72)
print("End of examples.")
print("=" * 72)
