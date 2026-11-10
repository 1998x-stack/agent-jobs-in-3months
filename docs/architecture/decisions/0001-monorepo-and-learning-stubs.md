# ADR-0001 · Monorepo / Atomic Skill Structure

**Status:** Accepted for the learning scaffold.

## Context

The curriculum needs 30 independent micro-competencies and three integrated projects with clear traceability.

## Decision

Use a single Python-oriented monorepo, placing each atomic skill in its own folder with `README.md`, `concept.md`, `exercise.py`, `check_exercise.py`.
Put runnable demonstration logic under three isolated `projects` packages.

## Consequences

- Positive: easy navigation, deterministic learning evidence, clear concept→code→project route.
- Negative: some duplication; educational scripts are not packaged as production libraries.
- Extension: migrate shared contracts to a proper package if integration complexity demands it.
