"""Parse and roll standard tabletop dice notation, e.g. "3d6+2" or "2d20kh1"."""

from .notation import (
    ConstantTerm,
    DiceTerm,
    Expression,
    NotationError,
    RollResult,
    parse,
    roll,
    roll_text,
)

__all__ = [
    "ConstantTerm",
    "DiceTerm",
    "Expression",
    "NotationError",
    "RollResult",
    "parse",
    "roll",
    "roll_text",
]

__version__ = "0.1.0"
