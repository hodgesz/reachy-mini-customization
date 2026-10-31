#!/usr/bin/env python3
"""Compatibility launcher for earlier Hello links."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from reachy_customizations.cli import hello_main

if __name__ == '__main__':
    raise SystemExit(hello_main())
