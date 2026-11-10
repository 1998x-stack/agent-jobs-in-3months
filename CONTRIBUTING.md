# Contribution Guide

Use one atomic skill ID per small PR wherever possible.

1. Update `concept.md`, implement `exercise.py`, strengthen `check_exercise.py`.
2. Add at least one happy-path, one failure and one boundary-case test.
3. Update current week's progress and link to a project integration.
4. Run `python -m pytest` and `python scripts/validate_structure.py`.
5. Record whether the implementation is a teaching demo or production-oriented.

Keep tasks synthetic, deterministic by default, and small enough to review.
