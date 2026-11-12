"""Playing strategies.

A strategy is created once per match and kept for all its games, so it can
learn from the opponent's previous throws.
"""

import random

import numpy as np

from .solver import Solver


class Strategy:
    name = "base"

    def __init__(self, solver: Solver, player: int, rng: random.Random):
        self.solver = solver
        self.player = player  # 1 or 2
        self.rng = rng
        self.opponent_moves: list[int] = []

    def own_stones(self, s1: int, s2: int) -> int:
        return s1 if self.player == 1 else s2

    def move(self, pos: int, s1: int, s2: int) -> int:
        raise NotImplementedError

    def observe(self, opponent_move: int):
        self.opponent_moves.append(opponent_move)


class Prudent(Strategy):
    """Pure maximin: the throw with the best guaranteed result.

    Among equally safe throws it keeps its stones and throws the fewest.
    """

    name = "prudent"

    def move(self, pos, s1, s2):
        if self.player == 1:
            m = self.solver.payoff_matrix(self.solver.lower, pos, s1, s2)
            return int(m.min(axis=1).argmax()) + 1
        m = self.solver.payoff_matrix(self.solver.upper, pos, s1, s2)
        return int(m.max(axis=0).argmin()) + 1


class Equilibrium(Strategy):
    """Plays the Nash equilibrium mix of the current state."""

    name = "nash"

    def move(self, pos, s1, s2):
        _, mix1, mix2 = self.solver.equilibrium(pos, s1, s2)
        mix = mix1 if self.player == 1 else mix2
        return self.rng.choices(range(1, len(mix) + 1), weights=mix)[0]


class AlwaysOne(Strategy):
    name = "one"

    def move(self, pos, s1, s2):
        return 1


class Uniform(Strategy):
    name = "random"

    def move(self, pos, s1, s2):
        return self.rng.randint(1, self.own_stones(s1, s2))


class Adaptive(Strategy):
    """Throws one more than the opponent's average throw so far.

    Falls back to the prudent move until it has seen the opponent play.
    """

    name = "adaptive"

    def __init__(self, solver, player, rng):
        super().__init__(solver, player, rng)
        self._prudent = Prudent(solver, player, rng)

    def move(self, pos, s1, s2):
        if not self.opponent_moves:
            return self._prudent.move(pos, s1, s2)
        guess = int(np.mean(self.opponent_moves)) + 1
        return max(1, min(guess, self.own_stones(s1, s2)))


STRATEGIES = {cls.name: cls for cls in (Prudent, Equilibrium, AlwaysOne, Uniform, Adaptive)}
