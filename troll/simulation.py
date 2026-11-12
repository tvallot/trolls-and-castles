"""Games and matches between strategies."""

import random
from dataclasses import dataclass

from .game import P1_WINS, P2_WINS, legal_moves, step
from .solver import Solver
from .strategies import STRATEGIES, Strategy


def play_game(solver: Solver, p1: Strategy, p2: Strategy, verbose: bool = False) -> int:
    game = solver.game
    pos, s1, s2 = game.initial_state()
    while (result := game.outcome(pos, s1, s2)) is None:
        a1 = p1.move(pos, s1, s2)
        a2 = p2.move(pos, s1, s2)
        if a1 not in legal_moves(s1) or a2 not in legal_moves(s2):
            raise ValueError(f"illegal throw: P1={a1}/{s1}, P2={a2}/{s2}")
        new_pos = step(pos, a1, a2)
        if verbose:
            print(f"  troll {pos:2d} | P1 {s1:2d} stones, throws {a1:2d} "
                  f"| P2 {s2:2d} stones, throws {a2:2d} | troll -> {new_pos}")
        p1.observe(a2)
        p2.observe(a1)
        pos, s1, s2 = new_pos, s1 - a1, s2 - a2
    return result


@dataclass
class MatchResult:
    name1: str
    name2: str
    wins1: int = 0
    wins2: int = 0
    draws: int = 0

    def __str__(self):
        return (f"{self.name1:>9} vs {self.name2:<9} | P1 wins {self.wins1:4d} "
                f"| P2 wins {self.wins2:4d} | draws {self.draws:4d}")


def play_match(solver: Solver, name1: str, name2: str, games: int = 1000,
               seed: int = 0) -> MatchResult:
    rng = random.Random(seed)
    p1 = STRATEGIES[name1](solver, 1, rng)
    p2 = STRATEGIES[name2](solver, 2, rng)
    res = MatchResult(name1, name2)
    for _ in range(games):
        r = play_game(solver, p1, p2)
        if r == P1_WINS:
            res.wins1 += 1
        elif r == P2_WINS:
            res.wins2 += 1
        else:
            res.draws += 1
    return res
