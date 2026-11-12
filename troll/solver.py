"""Exact solution of the game by backward induction.

Three tables are computed for every state (pos, s1, s2), from the smallest
stone counts upwards:

* `lower`: what P1 can guarantee with pure moves if P2 could see P1's throw
  before answering (max-min). This is P1's prudent value.
* `upper`: the same for P2 (min-max). P2's prudent value.
* `value`: the value of the real, simultaneous game, where both players may
  randomise. Each state is a zero-sum matrix game whose entries are the values
  of the next states; it is solved with a linear program.

We always have lower <= value <= upper. When the bounds meet, pure play is
already optimal; otherwise only a mixed strategy reaches the value.
"""

import numpy as np
from scipy.optimize import linprog

from .game import Game

EPS = 1e-9


def solve_matrix_game(m: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """Value and optimal mixed strategies of the zero-sum game `m`.

    The row player maximises. Returns (value, row_mix, col_mix).
    """
    rows, cols = m.shape
    row_mins = m.min(axis=1)
    col_maxs = m.max(axis=0)
    i, j = int(row_mins.argmax()), int(col_maxs.argmin())
    if row_mins[i] >= col_maxs[j] - EPS:  # saddle point, no LP needed
        row_mix, col_mix = np.zeros(rows), np.zeros(cols)
        row_mix[i] = col_mix[j] = 1.0
        return float(row_mins[i]), row_mix, col_mix

    # Variables: x_1..x_rows (row mix) and v. Maximise v subject to
    # sum_i x_i * m[i, j] >= v for every column j, sum_i x_i = 1, x >= 0.
    c = np.zeros(rows + 1)
    c[-1] = -1.0
    a_ub = np.hstack([-m.T, np.ones((cols, 1))])
    a_eq = np.append(np.ones(rows), 0.0)[None, :]
    res = linprog(
        c, A_ub=a_ub, b_ub=np.zeros(cols), A_eq=a_eq, b_eq=[1.0],
        bounds=[(0, None)] * rows + [(None, None)], method="highs",
    )
    if not res.success:
        raise RuntimeError(f"LP failed: {res.message}")
    row_mix = np.clip(res.x[:rows], 0, None)
    # The duals of the column constraints are the column player's mix.
    col_mix = np.clip(-res.ineqlin.marginals, 0, None)
    return float(res.x[-1]), row_mix / row_mix.sum(), col_mix / col_mix.sum()


class Solver:
    def __init__(self, game: Game):
        self.game = game
        shape = (game.cells, game.stones1 + 1, game.stones2 + 1)
        self.lower = np.zeros(shape)
        self.upper = np.zeros(shape)
        self.value = np.zeros(shape)
        self._solve()

    def payoff_matrix(self, table: np.ndarray, pos: int, s1: int, s2: int) -> np.ndarray:
        """m[a1-1, a2-1] = table value of the state reached after throws (a1, a2)."""
        a1 = np.arange(1, s1 + 1)[:, None]
        a2 = np.arange(1, s2 + 1)[None, :]
        next_pos = pos + np.sign(a1 - a2)
        return table[next_pos, s1 - a1, s2 - a2]

    def _solve(self):
        g = self.game
        # Process states by total number of stones so that every successor
        # (which has strictly fewer stones) is already known.
        for total in range(g.stones1 + g.stones2 + 1):
            for s1 in range(max(0, total - g.stones2), min(g.stones1, total) + 1):
                s2 = total - s1
                for pos in range(g.cells):
                    result = g.outcome(pos, s1, s2)
                    if result is not None:
                        self.lower[pos, s1, s2] = result
                        self.upper[pos, s1, s2] = result
                        self.value[pos, s1, s2] = result
                        continue
                    lo = self.payoff_matrix(self.lower, pos, s1, s2)
                    up = self.payoff_matrix(self.upper, pos, s1, s2)
                    self.lower[pos, s1, s2] = lo.min(axis=1).max()
                    self.upper[pos, s1, s2] = up.max(axis=0).min()
                    m = self.payoff_matrix(self.value, pos, s1, s2)
                    self.value[pos, s1, s2] = solve_matrix_game(m)[0]

    def equilibrium(self, pos: int, s1: int, s2: int) -> tuple[float, np.ndarray, np.ndarray]:
        """Value and optimal mixes (over 1..s1 and 1..s2 stones) at a state."""
        return solve_matrix_game(self.payoff_matrix(self.value, pos, s1, s2))
