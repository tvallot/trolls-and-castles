"""Rules of Trolls & Castles.

The path has `cells` squares numbered 0 .. cells-1. Player 1's castle is on
square 0 and player 2's castle on the last square, so the troll moving right
is good for player 1. A state is the tuple (troll position, stones of P1,
stones of P2).
"""

from dataclasses import dataclass

P1_WINS, DRAW, P2_WINS = 1, 0, -1


@dataclass(frozen=True)
class Game:
    cells: int = 7
    stones1: int = 15
    stones2: int = 15
    start: int | None = None  # defaults to the middle square

    def __post_init__(self):
        if self.cells < 3:
            raise ValueError("the path needs at least 3 squares")
        if self.stones1 < 0 or self.stones2 < 0:
            raise ValueError("stone counts must be non-negative")
        if self.start is None:
            object.__setattr__(self, "start", (self.cells - 1) // 2)
        if not 0 < self.start < self.cells - 1:
            raise ValueError("the troll must start between the castles")

    @property
    def last(self) -> int:
        return self.cells - 1

    def initial_state(self) -> tuple[int, int, int]:
        return self.start, self.stones1, self.stones2

    def outcome(self, pos: int, s1: int, s2: int) -> int | None:
        """Final result of the state, or None if the game goes on."""
        if pos <= 0:
            return P2_WINS
        if pos >= self.last:
            return P1_WINS
        if s1 > 0 and s2 > 0:
            return None
        # One player is out of stones: the other one's remaining stones each
        # push the troll one square, then the troll walks to the nearest castle.
        pos += s1 - s2
        centre = self.last / 2
        if pos < centre:
            return P2_WINS
        if pos > centre:
            return P1_WINS
        return DRAW


def legal_moves(stones: int) -> range:
    """A player must throw at least one stone and at most what is left."""
    return range(1, stones + 1)


def step(pos: int, throw1: int, throw2: int) -> int:
    """The troll moves one square away from whoever threw more."""
    return pos + (throw1 > throw2) - (throw1 < throw2)
