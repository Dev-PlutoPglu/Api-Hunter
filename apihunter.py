#!/usr/bin/env python3
"""API Hunter — standalone entry point.

Usage:
    python3 apihunter.py run -k weather
    python3 apihunter.py reverse-web https://example.com
    python3 apihunter.py reverse-apk ./app.apk --apk-deep
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apihunter.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
