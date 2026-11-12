import random

import numpy as np
import pytest

from troll import STRATEGIES, Game, Solver, play_match
from troll.game import DRAW, P1_WINS, P2_WINS, step
from troll.solver import solve_matrix_game


def test_troll_moves_away_from_bigger_throw():
    assert step(3, 5, 2) == 4
    assert step(3, 2, 5) == 2
    assert step(3, 4, 4) == 3


def test_end_of_game():
    g = Game(cells=7)
    assert g.outcome(0, 5, 5) == P2_WINS
    assert g.outcome(6, 5, 5) == P1_WINS
    assert g.outcome(3, 5, 5) is None
    # P1 is out of stones: P2's 2 stones push the troll from 3 to 1.
    assert g.outcome(3, 0, 2) == P2_WINS
    # Pushed back exactly to the middle: draw.
    assert g.outcome(2, 1, 0) == DRAW
    assert g.outcome(3, 0, 0) == DRAW


def test_matching_pennies():
    value, row, col = solve_matrix_game(np.array([[1.0, -1.0], [-1.0, 1.0]]))
    assert value == pytest.approx(0)
    assert row == pytest.approx([0.5, 0.5])
    assert col == pytest.approx([0.5, 0.5])


# Values worked out by hand in the course slides, on a 5-square path.
# Key: (stones P1, stones P2, troll offset from the middle).
COURSE_VALUES = {
    (4, 2, -2): -1, (3, 3, 0): 0, (3, 2, -1): 0, (3, 1, -2): -1,
    (2, 3, 0): -1, (2, 2, 0): 0, (2, 1, -1): 0, (2, 0, -2): -1,
    (1, 3, 0): -1, (1, 2, 0): -1, (1, 1, 0): 0, (1, 0, -1): 0,
    (0, 3, 0): -1, (0, 2, 0): -1, (0, 1, 0): -1, (0, 0, 0): 0,
}


@pytest.fixture(scope="module")
def small():
    return Solver(Game(cells=5, stones1=5, stones2=5))


@pytest.mark.parametrize("key,expected", COURSE_VALUES.items())
def test_course_values(small, key, expected):
    s1, s2, offset = key
    assert small.value[2 + offset, s1, s2] == pytest.approx(expected)


def test_mixed_state_needs_randomisation(small):
    # The open question of the slides: V(4, 3, -1). No pure strategy reaches it.
    state = (1, 4, 3)
    assert small.value[state] == pytest.approx(-0.5)
    assert small.lower[state] == -1
    assert small.upper[state] == 0


def test_bounds_are_ordered():
    s = Solver(Game(cells=7, stones1=10, stones2=12))
    assert np.all(s.lower <= s.value + 1e-9)
    assert np.all(s.value <= s.upper + 1e-9)


def test_symmetric_game_is_fair():
    s = Solver(Game(cells=7, stones1=15, stones2=15))
    assert s.value[s.game.initial_state()] == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize("name", STRATEGIES)
def test_strategies_only_play_legal_moves(name):
    solver = Solver(Game(cells=7, stones1=8, stones2=8))
    # play_match raises on an illegal throw
    res = play_match(solver, name, "random", games=50, seed=1)
    assert res.wins1 + res.wins2 + res.draws == 50
