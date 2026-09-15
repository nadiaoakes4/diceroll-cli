"""Command-line interface for diceroll.

Streaming note: when expressions come from a file or stdin, we iterate over
the handle line by line instead of calling .read()/.readlines(). A batch
file of a million dice expressions is processed one line at a time and
never has to fit in memory at once.
"""

from __future__ import annotations

import argparse
import random
import sys
from typing import Iterable, TextIO

from .notation import NotationError, roll_text


def _iter_expressions(handle: TextIO) -> Iterable[str]:
    for line in handle:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield line


def _run(lines: Iterable[str], rng: random.Random, out: TextIO) -> int:
    exit_code = 0
    for line in lines:
        try:
            result = roll_text(line, rng)
        except NotationError as exc:
            print(f"{line}: error: {exc}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"{line}: {result}", file=out)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diceroll",
        description="Parse and roll dice notation expressions like '3d6+2'.",
    )
    parser.add_argument(
        "expression",
        nargs="?",
        help=(
            "a single expression to roll, e.g. '2d20kh1+4'. If omitted, "
            "expressions are read one per line from --file or stdin"
        ),
    )
    parser.add_argument(
        "-f", "--file", help="read expressions from this file, one per line"
    )
    parser.add_argument(
        "--seed", type=int, help="seed the RNG for reproducible rolls"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rng = random.Random(args.seed)

    if args.expression is not None:
        return _run([args.expression], rng, sys.stdout)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            return _run(_iter_expressions(handle), rng, sys.stdout)

    return _run(_iter_expressions(sys.stdin), rng, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
