"""Render all figures, or selected stems, independently of the working directory."""
from pathlib import Path
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stems", nargs="*", help="Figure stems, e.g. 01-fig2-host-kernel")
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / "src"
    available = {p.stem: p for p in sorted(source.glob("[0-9][0-9]-fig*.py"))}
    unknown = set(args.stems) - available.keys()
    if unknown:
        parser.error(f"Unknown figure(s): {', '.join(sorted(unknown))}")
    for stem in args.stems or available:
        subprocess.run([sys.executable, str(available[stem])], check=True)


if __name__ == "__main__":
    main()
