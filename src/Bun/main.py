import argparse

import sys

from Bun.app import Bun
from Bun.splash import run_splash


def run() -> None:
    """Run the TUI application."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-splash", action="store_true")
    args, _ = parser.parse_known_args()
    if not args.no_splash:
        run_splash()
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    Bun().run()


if __name__ == "__main__":
    run()
