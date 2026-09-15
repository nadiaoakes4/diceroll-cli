"""Parser and evaluator for standard dice notation.

Grammar, roughly:

    expr    := term (('+' | '-') term)*
    term    := dice | integer
    dice    := [count] 'd' sides [keepdrop]
    keepdrop:= ('kh' | 'kl' | 'dh' | 'dl') count

Examples: "d20", "3d6+2", "4d6dl1" (drop the lowest of four d6),
"2d20kh1" (keep the highest of two d20, i.e. roll with advantage).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


class NotationError(ValueError):
    """Raised when a dice notation string can't be parsed."""


@dataclass
class DiceTerm:
    count: int
    sides: int
    sign: int  # +1 or -1
    keep: str | None = None  # one of "kh", "kl", "dh", "dl"
    keep_count: int = 0


@dataclass
class ConstantTerm:
    value: int
    sign: int


Term = DiceTerm | ConstantTerm

_KEEP_KEYWORDS = ("kh", "kl", "dh", "dl")


@dataclass
class Expression:
    terms: list[Term] = field(default_factory=list)


def parse(text: str) -> Expression:
    """Parse a dice notation string into an Expression.

    A single pass, hand-rolled scanner is enough here; the grammar has no
    nesting, so a real tokenizer/parser split would just be ceremony.
    """
    text = text.strip()
    if not text:
        raise NotationError("empty expression")

    pos = 0
    length = len(text)
    terms: list[Term] = []
    sign = 1
    expect_term = True

    def peek() -> str:
        return text[pos] if pos < length else ""

    while pos < length:
        ch = text[pos]
        if ch.isspace():
            pos += 1
            continue

        if ch in "+-":
            if expect_term:
                raise NotationError(f"unexpected {ch!r} at position {pos}")
            sign = 1 if ch == "+" else -1
            expect_term = True
            pos += 1
            continue

        if not expect_term:
            raise NotationError(f"expected + or - at position {pos}")

        start = pos
        while pos < length and text[pos].isdigit():
            pos += 1
        number_text = text[start:pos]

        if peek().lower() == "d":
            pos += 1
            count = int(number_text) if number_text else 1
            sides_start = pos
            while pos < length and text[pos].isdigit():
                pos += 1
            sides_text = text[sides_start:pos]
            if not sides_text:
                raise NotationError(f"missing die size at position {pos}")
            sides = int(sides_text)
            if count < 1:
                raise NotationError("dice count must be at least 1")
            if sides < 1:
                raise NotationError("die size must be at least 1")

            keep = None
            keep_count = 0
            lookahead = text[pos:pos + 2].lower()
            if lookahead in _KEEP_KEYWORDS:
                keep = lookahead
                pos += 2
                kc_start = pos
                while pos < length and text[pos].isdigit():
                    pos += 1
                kc_text = text[kc_start:pos]
                keep_count = int(kc_text) if kc_text else 1
                if keep_count < 1 or keep_count > count:
                    raise NotationError("keep/drop count out of range")

            terms.append(DiceTerm(count, sides, sign, keep, keep_count))
        else:
            if not number_text:
                raise NotationError(f"unexpected character {ch!r} at position {pos}")
            terms.append(ConstantTerm(int(number_text), sign))

        expect_term = False

    if expect_term:
        raise NotationError("expression ends with a dangling operator")

    return Expression(terms)


@dataclass
class RollResult:
    total: int
    rolls: list[tuple[str, list[int]]]  # (term label, kept die values)

    def __str__(self) -> str:
        if not self.rolls:
            return str(self.total)
        parts = (f"{label}={values}" for label, values in self.rolls)
        return f"{self.total} ({', '.join(parts)})"


def roll(expression: Expression, rng: random.Random | None = None) -> RollResult:
    """Evaluate an already-parsed Expression, rolling dice with rng."""
    rng = rng if rng is not None else random.Random()
    total = 0
    detail: list[tuple[str, list[int]]] = []

    for term in expression.terms:
        if isinstance(term, ConstantTerm):
            total += term.sign * term.value
            continue

        raw = [rng.randint(1, term.sides) for _ in range(term.count)]
        if term.keep == "kh":
            kept = sorted(raw, reverse=True)[: term.keep_count]
        elif term.keep == "kl":
            kept = sorted(raw)[: term.keep_count]
        elif term.keep == "dh":
            kept = sorted(raw)[: term.count - term.keep_count]
        elif term.keep == "dl":
            kept = sorted(raw, reverse=True)[: term.count - term.keep_count]
        else:
            kept = raw

        total += term.sign * sum(kept)

        label = f"{term.count}d{term.sides}"
        if term.keep:
            label += f"{term.keep}{term.keep_count}"
        detail.append((label, kept))

    return RollResult(total, detail)


def roll_text(text: str, rng: random.Random | None = None) -> RollResult:
    """Parse and roll a dice notation string in one step."""
    return roll(parse(text), rng)
