# CLAUDE.md — Belief Revision AI

## Project

02180 Intro to AI (SP25, DTU) — **Due: May 4th, 2026 at 23:59**

A propositional belief revision engine following the AGM framework.
Input is Polish (prefix) notation. No external logic packages are used.

## How to run

```bash
# Interactive REPL
python main.py

# Full test suite (85 tests, all passing as of 2026-05-02)
/Library/Frameworks/Python.framework/Versions/3.13/bin/pytest tests/ -v
```

## Module map

| File | Responsibility |
|---|---|
| `parse.py` | Tokeniser + recursive-descent parser → AST (`Atom`, `Not`, `Operator`) |
| `cnf.py` | Three-stage CNF pipeline: eliminate implications → push NOT inward → distribute OR over AND |
| `resolution.py` | Clause extraction + resolution-refutation entailment (`entails(kb, query)`) |
| `belief_base.py` | `BeliefBase`: priority-ordered partial meet contraction, Levi-identity revision |
| `main.py` | REPL with `add`, `contract`, `revise`, `entails`, `kb`, `cnf`, `clauses` commands |
| `tests/` | 85 pytest tests across all modules |

## Architecture notes

- **Formula representation**: AST nodes (`Atom`, `Not`, `Operator`). CNF is also stored as an AST, not a flat clause list.
- **Clause representation**: `frozenset` of literal-strings (`"A"`, `"~B"`). Conversion happens inside `resolution.py` on demand.
- **Priority**: each formula in `BeliefBase` carries an integer priority. Higher = more entrenched. Auto-assigned (insertion order) unless overridden with `add <priority> <formula>`.
- **Selection function** (`_select`): lexicographic epistemic entrenchment — score each remainder by its sorted priority tuple (descending); keep those tied for the maximum. This is Strategy A.
- **Contraction** (`_remainders`): enumerates all 2ⁿ subsets and filters to maximal non-entailing ones. Correct but exponential — fine for small KBs.

## Implementation status

### Complete ✅
- Parsing: Polish notation, all five operators, nested parens, error handling
- CNF conversion: implication elimination, De Morgan, distribution
- Resolution-refutation entailment (implemented from scratch)
- `BeliefBase.expand` — naive add with optional explicit priority
- `BeliefBase.contract` — partial meet contraction with priority-based selection
- `BeliefBase.revise` — Levi identity (`K * φ = (K ÷ ¬φ) + φ`)
- AGM postulate tests: Success, Inclusion, Vacuity, Recovery, Consistency, Extensionality (for both contraction and revision)
- REPL with `contract` and `revise` commands

### Not yet implemented ❌
- **Mastermind** (optional extra): use belief revision as code-breaker AI
  - Encode game rules as background knowledge
  - First guess → receive feedback → revise → output next guess
  - See assignment Section 4 for details

### Possible improvements
- `_remainders` is O(2ⁿ) — replace with a hitting-set algorithm for larger KBs
- `BeliefBase` does not deduplicate formulas on `expand`; identical formulas can appear twice
- Formula `__repr__` uses `Not(...)` / `AND(...)` style — less readable for humans; a proper printer showing `¬A`, `A ∧ B` etc. would help the report
- Tests use `str(formula)` for inclusion checks, which depends on `__repr__` format — fragile if repr changes

## AGM postulates reference

For **revision** `K * φ`:
1. **Success** — `K * φ ⊨ φ`
2. **Inclusion** — `K * φ ⊆ Cn(K + φ)`
3. **Vacuity** — if `K ⊭ ¬φ` then `K * φ = K + φ`
4. **Consistency** — `K * φ` is consistent when `φ` is consistent
5. **Extensionality** — `φ ≡ ψ` implies `K * φ = K * ψ`

For **contraction** `K ÷ φ`:
1. **Success** — if `⊬ φ` then `K ÷ φ ⊭ φ`
2. **Inclusion** — `K ÷ φ ⊆ K`
3. **Vacuity** — if `K ⊭ φ` then `K ÷ φ = K`
4. **Recovery** — `K ⊆ Cn((K ÷ φ) + φ)`
5. **Extensionality** — `φ ≡ ψ` implies `K ÷ φ = K ÷ ψ`

## Formula syntax (Polish notation)

```
AND A B          →  A ∧ B
OR A B           →  A ∨ B
NOT A            →  ¬A
IMPLIES A B      →  A → B
BICONDITIONAL A B →  A ↔ B
IMPLIES (AND A B) C   →  (A ∧ B) → C
```

Case-insensitive. Atoms are single alphabetic tokens (A, B, Rain, etc.).
