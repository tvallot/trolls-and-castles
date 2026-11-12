"""Command-line entry point.

Examples:
    python main.py solve --cells 7 --stones 15
    python main.py match --p1 prudent --p2 nash --games 1000 --show
    python main.py tournament --cells 15 --stones 30
    python main.py curve --cells 7 --max-stones 30 --out docs/value_vs_stones.png
"""

import argparse
import itertools

import random

from troll import STRATEGIES, Game, Solver, play_game, play_match


def build_game(args) -> Game:
    s1 = args.stones1 if args.stones1 is not None else args.stones
    s2 = args.stones2 if args.stones2 is not None else args.stones
    return Game(args.cells, s1, s2, args.start)


def describe(game: Game) -> str:
    return (f"{game.cells} squares, troll on square {game.start}, "
            f"stones P1={game.stones1} P2={game.stones2}")


def cmd_solve(args):
    game = build_game(args)
    solver = Solver(game)
    state = game.initial_state()
    print(describe(game))
    print(f"  P1 prudent value (pure max-min) : {solver.lower[state]:+.0f}")
    print(f"  P2 prudent value (pure min-max) : {solver.upper[state]:+.0f}")
    print(f"  Game value (mixed equilibrium)  : {solver.value[state] + 0.0:+.3f}")
    if game.outcome(*state) is None:
        _, mix1, mix2 = solver.equilibrium(*state)
        for name, mix in (("P1", mix1), ("P2", mix2)):
            support = ", ".join(f"{a + 1}: {p:.2f}" for a, p in enumerate(mix) if p > 1e-6)
            print(f"  {name} first-turn mix {{{support}}}")


def cmd_match(args):
    game = build_game(args)
    solver = Solver(game)
    print(describe(game))
    if args.show:
        rng = random.Random(args.seed)
        p1 = STRATEGIES[args.p1](solver, 1, rng)
        p2 = STRATEGIES[args.p2](solver, 2, rng)
        result = play_game(solver, p1, p2, verbose=True)
        print({1: "  -> P1 wins", -1: "  -> P2 wins", 0: "  -> draw"}[result])
    print(play_match(solver, args.p1, args.p2, args.games, args.seed))


def cmd_tournament(args):
    game = build_game(args)
    solver = Solver(game)
    print(describe(game), f"| {args.games} games per match")
    points = dict.fromkeys(STRATEGIES, 0)
    for n1, n2 in itertools.product(STRATEGIES, repeat=2):
        res = play_match(solver, n1, n2, args.games, args.seed)
        print(res)
        if n1 == n2:
            continue
        # Contest scoring: 3 points for winning more games, 1 each for a tie.
        if res.wins1 > res.wins2:
            points[n1] += 3
        elif res.wins2 > res.wins1:
            points[n2] += 3
        else:
            points[n1] += 1
            points[n2] += 1
    print("Standings (both seats, self-play excluded):")
    for name, pts in sorted(points.items(), key=lambda kv: -kv[1]):
        print(f"  {name:<9} {pts:3d} pts")


def cmd_curve(args):
    import matplotlib.pyplot as plt

    n = args.max_stones
    starts = sorted({(args.cells - 1) // 2, (args.cells - 1) // 2 - 1})
    fig, ax = plt.subplots(figsize=(7, 4))
    for start in starts:
        solver = Solver(Game(args.cells, n, n, start))
        xs = range(1, n + 1)
        ax.plot(xs, [solver.value[start, k, k] for k in xs], marker="o", ms=3,
                label=f"troll on square {start}, game value")
        ax.plot(xs, [solver.lower[start, k, k] for k in xs], ls="--",
                label=f"troll on square {start}, P1 prudent value")
    ax.set_xlabel("stones per player")
    ax.set_ylabel("value for P1 (+1 win, -1 loss)")
    ax.set_title(f"{args.cells}-square path")
    ax.set_ylim(-1.1, 1.1)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"saved {args.out}")


def main():
    parser = argparse.ArgumentParser(description="Trolls & Castles solver and simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    def game_args(p):
        p.add_argument("--cells", type=int, default=7, help="squares on the path, castles included")
        p.add_argument("--stones", type=int, default=15, help="stones per player")
        p.add_argument("--stones1", type=int, help="override P1's stones")
        p.add_argument("--stones2", type=int, help="override P2's stones")
        p.add_argument("--start", type=int, help="troll start square (default: middle)")

    def match_args(p):
        p.add_argument("--games", type=int, default=1000)
        p.add_argument("--seed", type=int, default=0)

    p = sub.add_parser("solve", help="value of the game and optimal first move")
    game_args(p)
    p.set_defaults(func=cmd_solve)

    p = sub.add_parser("match", help="play two strategies against each other")
    game_args(p)
    match_args(p)
    p.add_argument("--p1", choices=STRATEGIES, default="prudent")
    p.add_argument("--p2", choices=STRATEGIES, default="nash")
    p.add_argument("--show", action="store_true", help="print the moves of one game")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("tournament", help="every strategy against every other")
    game_args(p)
    match_args(p)
    p.set_defaults(func=cmd_tournament)

    p = sub.add_parser("curve", help="plot the value against the number of stones")
    p.add_argument("--cells", type=int, default=7)
    p.add_argument("--max-stones", type=int, default=20)
    p.add_argument("--out", default="value_vs_stones.png")
    p.set_defaults(func=cmd_curve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
