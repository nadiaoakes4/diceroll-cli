"""Unit tests for diceroll.notation.

Rolls are tested with a scripted fake RNG rather than a seeded
random.Random, so expectations don't depend on the exact sequence a
particular Python version's Mersenne Twister happens to produce for a
given seed.
"""

from __future__ import annotations

import unittest

from diceroll.notation import (
    ConstantTerm,
    DiceTerm,
    NotationError,
    parse,
    roll,
    roll_text,
)


class FakeRng:
    """Returns randint() results from a fixed, pre-scripted queue."""

    def __init__(self, values: list[int]) -> None:
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if not self._values:
            raise AssertionError("FakeRng ran out of scripted values")
        return self._values.pop(0)


class ParseBasicTests(unittest.TestCase):
    def test_plain_die(self) -> None:
        expr = parse("d20")
        self.assertEqual(expr.terms, [DiceTerm(1, 20, 1)])

    def test_counted_die_with_modifier(self) -> None:
        expr = parse("3d6+2")
        self.assertEqual(
            expr.terms,
            [DiceTerm(3, 6, 1), ConstantTerm(2, 1)],
        )

    def test_negative_modifier(self) -> None:
        expr = parse("1d20-1")
        self.assertEqual(
            expr.terms,
            [DiceTerm(1, 20, 1), ConstantTerm(1, -1)],
        )

    def test_multiple_dice_terms(self) -> None:
        expr = parse("1d8+1d4+2")
        self.assertEqual(
            expr.terms,
            [DiceTerm(1, 8, 1), DiceTerm(1, 4, 1), ConstantTerm(2, 1)],
        )

    def test_bare_constant(self) -> None:
        expr = parse("5")
        self.assertEqual(expr.terms, [ConstantTerm(5, 1)])

    def test_whitespace_is_ignored(self) -> None:
        expr = parse("  3d6 + 2  ")
        self.assertEqual(
            expr.terms,
            [DiceTerm(3, 6, 1), ConstantTerm(2, 1)],
        )

    def test_uppercase_d_is_accepted(self) -> None:
        expr = parse("2D6")
        self.assertEqual(expr.terms, [DiceTerm(2, 6, 1)])


class ParseKeepDropTests(unittest.TestCase):
    def test_keep_highest(self) -> None:
        expr = parse("2d20kh1")
        self.assertEqual(expr.terms, [DiceTerm(2, 20, 1, "kh", 1)])

    def test_keep_lowest(self) -> None:
        expr = parse("2d20kl1")
        self.assertEqual(expr.terms, [DiceTerm(2, 20, 1, "kl", 1)])

    def test_drop_lowest(self) -> None:
        expr = parse("4d6dl1")
        self.assertEqual(expr.terms, [DiceTerm(4, 6, 1, "dl", 1)])

    def test_drop_highest(self) -> None:
        expr = parse("4d6dh1")
        self.assertEqual(expr.terms, [DiceTerm(4, 6, 1, "dh", 1)])

    def test_keep_count_defaults_to_one(self) -> None:
        expr = parse("2d20kh")
        self.assertEqual(expr.terms, [DiceTerm(2, 20, 1, "kh", 1)])

    def test_keep_count_can_be_explicit(self) -> None:
        expr = parse("4d6dl2")
        self.assertEqual(expr.terms, [DiceTerm(4, 6, 1, "dl", 2)])

    def test_keep_count_equal_to_dice_count_is_allowed(self) -> None:
        expr = parse("3d6kh3")
        self.assertEqual(expr.terms, [DiceTerm(3, 6, 1, "kh", 3)])


class ParseErrorTests(unittest.TestCase):
    def test_empty_string(self) -> None:
        with self.assertRaisesRegex(NotationError, "empty expression"):
            parse("")

    def test_whitespace_only(self) -> None:
        with self.assertRaisesRegex(NotationError, "empty expression"):
            parse("   ")

    def test_leading_operator(self) -> None:
        with self.assertRaisesRegex(NotationError, "unexpected '\\+' at position 0"):
            parse("+3")

    def test_trailing_operator(self) -> None:
        with self.assertRaisesRegex(
            NotationError, "expression ends with a dangling operator"
        ):
            parse("3d6+")

    def test_missing_die_size(self) -> None:
        with self.assertRaisesRegex(NotationError, "missing die size at position 2"):
            parse("3d")

    def test_zero_dice_count(self) -> None:
        with self.assertRaisesRegex(NotationError, "dice count must be at least 1"):
            parse("0d6")

    def test_zero_sided_die(self) -> None:
        with self.assertRaisesRegex(NotationError, "die size must be at least 1"):
            parse("1d0")

    def test_keep_count_zero(self) -> None:
        with self.assertRaisesRegex(NotationError, "keep/drop count out of range"):
            parse("2d20kh0")

    def test_keep_count_too_large(self) -> None:
        with self.assertRaisesRegex(NotationError, "keep/drop count out of range"):
            parse("2d20kh3")

    def test_two_terms_without_operator(self) -> None:
        with self.assertRaisesRegex(NotationError, "expected \\+ or - at position 2"):
            parse("3 3")

    def test_unrecognized_character(self) -> None:
        with self.assertRaisesRegex(
            NotationError, "unexpected character 'x' at position 0"
        ):
            parse("x")


class RollTests(unittest.TestCase):
    def test_plain_dice_term_sums_all_rolls(self) -> None:
        result = roll(parse("3d6"), FakeRng([2, 5, 4]))
        self.assertEqual(result.total, 11)
        self.assertEqual(result.rolls, [("3d6", [2, 5, 4])])

    def test_constant_only(self) -> None:
        result = roll(parse("7"), FakeRng([]))
        self.assertEqual(result.total, 7)
        self.assertEqual(result.rolls, [])

    def test_keep_highest_drops_the_rest(self) -> None:
        result = roll(parse("2d20kh1"), FakeRng([12, 19]))
        self.assertEqual(result.total, 19)
        self.assertEqual(result.rolls, [("2d20kh1", [19])])

    def test_keep_lowest_drops_the_rest(self) -> None:
        result = roll(parse("2d6kl1"), FakeRng([5, 2]))
        self.assertEqual(result.total, 2)
        self.assertEqual(result.rolls, [("2d6kl1", [2])])

    def test_drop_lowest_keeps_the_rest(self) -> None:
        result = roll(parse("4d6dl1"), FakeRng([3, 6, 1, 4]))
        self.assertEqual(result.total, 13)
        self.assertEqual(result.rolls, [("4d6dl1", [6, 4, 3])])

    def test_drop_highest_keeps_the_rest(self) -> None:
        result = roll(parse("4d6dh1"), FakeRng([3, 6, 1, 4]))
        self.assertEqual(result.total, 8)
        self.assertEqual(result.rolls, [("4d6dh1", [1, 3, 4])])

    def test_combines_multiple_dice_and_a_modifier(self) -> None:
        result = roll(parse("1d8+1d4+2"), FakeRng([5, 3]))
        self.assertEqual(result.total, 10)
        self.assertEqual(result.rolls, [("1d8", [5]), ("1d4", [3])])

    def test_negative_sign_subtracts_the_term(self) -> None:
        result = roll(parse("1d20-1d4"), FakeRng([10, 3]))
        self.assertEqual(result.total, 7)

    def test_str_with_no_dice(self) -> None:
        result = roll(parse("5"), FakeRng([]))
        self.assertEqual(str(result), "5")

    def test_str_includes_kept_values(self) -> None:
        result = roll(parse("2d6"), FakeRng([1, 2]))
        self.assertEqual(str(result), "3 (2d6=[1, 2])")


class RollTextTests(unittest.TestCase):
    def test_parses_and_rolls_in_one_step(self) -> None:
        import random

        rng_a = random.Random(42)
        rng_b = random.Random(42)
        first = roll_text("3d6+2", rng_a)
        second = roll_text("3d6+2", rng_b)
        self.assertEqual(first.total, second.total)
        self.assertEqual(first.rolls, second.rolls)

    def test_invalid_text_raises_notation_error(self) -> None:
        with self.assertRaises(NotationError):
            roll_text("not dice")


if __name__ == "__main__":
    unittest.main()
