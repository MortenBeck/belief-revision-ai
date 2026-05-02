# Belief Revision AI

Assignment for **02180 Intro to AI, SP25** — Due: May 4th, 2026 at 23:59

## Overview

A belief revision engine for propositional logic in symbolic (Polish notation) form, following the AGM framework. The agent maintains a prioritised belief base and supports contraction, expansion, and revision via the Levi identity. All logic is implemented from scratch — no external logic packages are used.

## How to Run

```bash
# Interactive REPL
python main.py

# Run the test suite (85 tests)
pytest tests/ -v
```

**Python 3.13+ required.** No dependencies beyond `pytest` for testing.

## REPL Commands

| Command | Description |
|---|---|
| `add <formula>` | Expand belief base (auto-assigned priority) |
| `add <priority> <formula>` | Expand with explicit integer priority |
| `contract <formula>` | Partial meet contraction — remove formula from KB |
| `revise <formula>` | AGM revision — contract ¬formula, then add formula |
| `entails <formula>` | Check whether KB logically entails formula |
| `kb` | List current beliefs with their priorities |
| `cnf <formula>` | Show CNF form of a formula |
| `clauses <formula>` | Show clausal form of a formula |
| `clear` | Empty the belief base |
| `help` | Show command reference |

## Input Format

Formulas use **Polish (prefix) notation** — operators appear before their operands. The notation is case-insensitive.

| Operator | Polish notation | Meaning |
|---|---|---|
| AND | `AND A B` | A ∧ B |
| OR | `OR A B` | A ∨ B |
| NOT | `NOT A` | ¬A |
| IMPLIES | `IMPLIES A B` | A → B |
| BICONDITIONAL | `BICONDITIONAL A B` | A ↔ B |

Use parentheses for grouping: `IMPLIES (AND A B) C` means (A ∧ B) → C.

## Implementation

### Modules

**`parse.py`** — Tokeniser and recursive-descent parser. Converts a Polish notation string into an AST of `Atom`, `Not`, and `Operator` nodes.

**`cnf.py`** — Three-stage CNF conversion pipeline:
1. Eliminate `IMPLIES` and `BICONDITIONAL`
2. Push `NOT` inward using De Morgan's laws and double-negation elimination
3. Distribute `OR` over `AND`

**`resolution.py`** — Resolution-refutation entailment checker. Converts CNF trees to clause sets (`frozenset` of literal-strings), then applies resolution until the empty clause is derived (KB ⊨ query) or no new clauses can be generated (KB ⊭ query).

**`belief_base.py`** — `BeliefBase` class implementing the full AGM revision cycle:
- `expand(φ)` — K + φ: add formula without consistency check
- `contract(φ)` — K ÷ φ: partial meet contraction based on priority ordering
- `revise(φ)` — K * φ: Levi identity (`(K ÷ ¬φ) + φ`)

Contraction finds all maximal subsets of the KB that do not entail φ (the *remainders*), then selects among them using lexicographic epistemic entrenchment: the remainder that retains the highest-priority formula wins.

**`main.py`** — Interactive REPL.

### Priority

Each formula stored in the belief base carries an integer priority. Higher priority means the formula is more *entrenched* — it is preferred during contraction when there is a choice about what to remove. By default, later-added formulas get higher priority. An explicit priority can be set with `add <n> <formula>`.

## AGM Postulates

The implementation is tested against all five AGM postulates for both contraction and revision:

| Postulate | Contraction (K ÷ φ) | Revision (K * φ) |
|---|---|---|
| **Success** | K ÷ φ ⊭ φ (if φ not a tautology) | K * φ ⊨ φ |
| **Inclusion** | K ÷ φ ⊆ K | K * φ ⊆ Cn(K + φ) |
| **Vacuity** | If K ⊭ φ, then K ÷ φ = K | If K ⊭ ¬φ, then K * φ = K + φ |
| **Recovery / Consistency** | K ⊆ Cn((K ÷ φ) + φ) | K * φ is consistent when φ is consistent |
| **Extensionality** | φ ≡ ψ ⟹ K ÷ φ = K ÷ ψ | φ ≡ ψ ⟹ K * φ = K * ψ |

## Test Suite

85 tests across 4 files, all passing:

| File | Tests | Covers |
|---|---|---|
| `tests/test_parse.py` | 14 | Parser: operators, nesting, parentheses, error cases |
| `tests/test_cnf.py` | 31 | CNF pipeline: each stage in isolation and end-to-end |
| `tests/test_resolution.py` | 20 | Clause extraction, entailment (positive and negative cases) |
| `tests/test_belief_base.py` | 20 | AGM postulates for expansion, contraction, and revision |

## Optional: Mastermind

Not yet implemented. The assignment optionally asks the belief revision engine to play Mastermind as the code-breaker: encode game rules as background knowledge, make a first guess, then revise the belief base upon receiving feedback to derive the next guess.

## Report

The accompanying report (4–6 pages) describes the formalism, implementation choices, and lessons learned, structured to follow the assignment's sequence of stages.

## Use of Generative AI

Generative AI was used as an analytical tool for this project, as well as for writing commit messages and this README.
