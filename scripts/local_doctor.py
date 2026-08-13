#!/usr/bin/env python3
"""Standalone entry point for the local environment doctor.

The implementation lives in dci.diagnostics, inside the installed package,
because `dci doctor` advertises it: a CLI command whose implementation sits
outside the distribution fails on any checkout that has the package and not this
working tree. This file remains so the documented `python scripts/local_doctor.py`
invocation keeps working.
"""
import sys

from dci.diagnostics import main

if __name__ == "__main__":
    sys.exit(main())
