# diceroll

A small library and CLI for parsing and rolling tabletop dice notation:
`3d6+2`, `2d20kh1` (advantage), `4d6dl1` (drop the lowest die), and so on.

I wanted something I could hand a batch file of a few hundred thousand
dice expressions (logged from a game session, or generated for a
probability simulation) and get results back without the process
ballooning in memory. Most of the small dice-notation scripts I found
`read()` the whole input up front, which falls over exactly when you
actually need it - on the big file. `diceroll` reads line by line, so
memory use stays flat no matter how large the input is.

## Notation supported

```
d20            one twenty-sided die
3d6            three six-sided dice, summed
3d6+2          same, plus a flat modifier
2d20kh1        roll two d20, keep the highest (advantage)
2d20kl1        roll two d20, keep the lowest (disadvantage)
4d6dl1         roll four d6, drop the lowest (common ability-score roll)
1d8+1d4+2      multiple dice terms and a modifier combined
```

## Library usage

```python
from diceroll import roll_text

result = roll_text("2d6+3")
print(result.total)   # e.g. 11
print(result.rolls)   # [("2d6", [4, 4])]
print(result)          # "11 (2d6=[4, 4])"
```

For reproducible rolls, pass your own `random.Random`:

```python
import random
from diceroll import roll_text

rng = random.Random(42)
print(roll_text("1d20", rng))
```

If you want to parse once and roll many times (useful for simulations),
split parsing from evaluation:

```python
from diceroll import parse, roll

expr = parse("4d6dl1")
totals = [roll(expr).total for _ in range(10_000)]
```

## CLI usage

Roll a single expression:

```
$ diceroll "2d20kh1+5"
2d20kh1+5: 23 (2d20kh1=[18])
```

Roll a batch from a file, one expression per line, streamed rather than
loaded whole:

```
$ cat session.txt
3d6
1d20+4
2d20kh1

$ diceroll --file session.txt
3d6: 11 (3d6=[2, 5, 4])
1d20+4: 17 (1d20=[13])
2d20kh1: 19 (2d20kh1=[19])
```

Or pipe expressions in over stdin, which works the same way for input of
any size:

```
$ generate_expressions.sh | diceroll > results.txt
```

Blank lines and lines starting with `#` are skipped. Pass `--seed` to make
a run reproducible.

## Status

Early skeleton. The parser and CLI work for the notation listed above;
see the roadmap in the repository description for what's planned next.

## License

MIT, see LICENSE.
