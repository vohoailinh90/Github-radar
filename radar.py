# layout: entry-point
"""Entry point: `python3 radar.py run`. See README.md and docs/."""

import sys

from radar.cli import main

if __name__ == "__main__":
    sys.exit(main())
