import argparse
import os
from pathlib import Path
import sys

from Bun.app import Bun
from Bun.splash import run_splash


def run() -> None:
    """Run the TUI application."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-splash", action="store_true")
    parser.add_argument("--seed", action="store_true")
    args, _ = parser.parse_known_args()
    if not args.no_splash:
        run_splash()
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    if args.seed:
        os.environ["BUN_SEED"] = "1"
        os.environ["BUN_TEST_DATA_DIR"] = str(
            Path(__file__).resolve().parents[2] / "test_data"
        )
    Bun().run()


if __name__ == "__main__":
    run()
