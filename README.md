# Belief Revision AI

Assignment for **02180 Intro to AI, SP25** — Due: May 4th, 2026 at 23:59

## Overview

A belief revision engine that works with propositional logic in symbolic form. The agent maintains a belief base and can revise it when new information is received, following the AGM framework for belief revision.

## Components

### 1. Belief Base
Stores the agent's current beliefs as a set of propositional formulas with a priority ordering.

### 2. Logical Entailment
Checks whether a formula is entailed by the belief base. Implemented from scratch (no external logic packages) — likely resolution-based or truth-table based.

### 3. Contraction
Removes a belief from the belief base using partial meet contraction, based on the priority order of formulas.

### 4. Expansion
Adds a new formula to the belief base.

### 5. Revision (AGM)
Combines contraction and expansion (Levi identity: `B * p = (B ÷ ¬p) + p`) to revise the belief base with a new formula.

## AGM Postulates

The implementation is tested against the following AGM postulates:
- **Success**: The new formula is in the revised belief base
- **Inclusion**: The revised base is a subset of the expanded base
- **Vacuity**: If the negation was not believed, revision equals expansion
- **Consistency**: The revised base is consistent (unless the new formula itself is contradictory)
- **Extensionality**: Logically equivalent inputs produce the same result

## Optional: Mastermind

The engine may optionally be used to play Mastermind as the code-breaker, using belief revision to incorporate feedback from each guess and derive the next guess.

## How to Run

> Instructions to be added once implementation language and structure are decided.

## Report

The accompanying report (4–6 pages) covers formalism, implementation choices, and lessons learned.
