"""Pytest configuration: make the repo root and tests dir importable.

Adds the repository root to ``sys.path`` so ``import asciigpt`` works
without installing the package, and the tests directory so the shared
``_fixtures`` helper module can be imported by test files.
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_TESTS_DIR)

for _p in (_REPO_ROOT, _TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
