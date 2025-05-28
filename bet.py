import sys
import argparse
import random
import logging


class Strategy:
    def __init__(self, p, start, target, min_bet=1, win_is_bet_amount=True):
        self.p = p
        self.start = start
        self.target = target
        self.min_bet = min_bet
        self.win_is_bet_amount = win_is_bet_amount

    def should_bet_again(self, curr, total_bet):
        if curr < self.min_bet:
            return False

        if self.win_is_bet_amount:
            return total_bet < self.target
        else:
            return curr < self.target

    def run(self):
        total_bet = 0
        curr = self.start
        nsteps = 0

        while self.should_bet_again(curr, total_bet):
            bet = self.get_next_bet(curr, total_bet)
            if bet > curr:
                break
            bet = max(self.min_bet, bet)
            nsteps += 1
            total_bet += bet
            q = random.uniform(0, 1)
            if self.p >= q:
                curr += bet
            else:
                curr -= bet

        if self.win_is_bet_amount:
            return total_bet >= self.target
        else:
            return curr >= self.target


class AllBetStragegy(Strategy):
    def get_next_bet(self, curr, total_bet):
        return curr


class MinBetStragegy(Strategy):
    def get_next_bet(self, curr, total_bet):
        return self.min_bet


class FixedBetStrategy(Strategy):
    def __init__(self, p, start, target, bet_size, min_bet=1, win_is_bet_amount=True):
        super().__init__(
            p, start, target, min_bet=min_bet, win_is_bet_amount=win_is_bet_amount
        )
        self.bet_size = bet_size

    def get_next_bet(self, curr, total_bet):
        return min(self.bet_size, curr)


class FractionBetStrategy(Strategy):
    def __init__(self, p, start, target, fraction, min_bet=1, win_is_bet_amount=True):
        super().__init__(
            p, start, target, min_bet=min_bet, win_is_bet_amount=win_is_bet_amount
        )
        self.fraction = fraction

    def get_next_bet(self, curr, total_bet):
        return int(round(self.fraction * curr))


class FractionCumulativeBetStrategy(Strategy):
    def __init__(self, p, start, target, fraction, min_bet=1, starting_bet=None, win_is_bet_amount=True):
        super().__init__(
            p, start, target, min_bet=min_bet, win_is_bet_amount=win_is_bet_amount
        )
        if starting_bet is None:
            starting_bet = self.min_bet
        self.starting_bet = starting_bet
        self.fraction = fraction

    def get_next_bet(self, curr, total_bet):
        if total_bet == 0:
            return self.starting_bet

        return int(round(self.fraction * total_bet))


class KellyBetStrategy(Strategy):
    def get_next_bet(self, curr, total_bet):
        if self.win_is_bet_amount:
            if curr >= self.target - total_bet:
                return self.target - total_bet

            p = (self.target - total_bet - curr + 1) // 2
            return min(p, curr)
        else:
            return min(curr, self.target - curr)


def run_strategy(name, strategy, n):
    nwins = 0
    logging.debug("Running %s", name)
    for i in range(n):
        if strategy.run():
            nwins += 1
    logging.debug("%s done", name)
    return nwins


class StrategiesToRun:
    def __init__(self, args):
        self.args = args
        a = (args.probability, args.start, args.target)
        kw = {"win_is_bet_amount": args.win_is_bet}
        strategies = {
            "all": AllBetStragegy(*a, **kw),
            "min": MinBetStragegy(*a, **kw),
        }
        for bet_size in range(1, args.start + 1):
            strategies[f"fixed_{bet_size}"] = FixedBetStrategy(
                *a, **kw, bet_size=bet_size
            )
        for fraction in range(1, 101):
            strategies[f"fraction_{fraction}"] = FractionBetStrategy(
                *a, **kw, fraction=fraction / 100.0
            )
        for fraction in range(1, 101):
            strategies[f"cum_fraction_{fraction}"] = FractionCumulativeBetStrategy(
                *a, **kw, fraction=fraction / 100.0
            )

        strategies["kelly"] = KellyBetStrategy(*a, **kw)
        self.strategies = strategies

    def __iter__(self):
        return iter(self.strategies)


def setup_logging(debug=False):
    lvl = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(format="%(message)s", level=lvl)


def run(args):
    setup_logging(debug=args.debug)
    strategies = StrategiesToRun(args)
    args.outfile.write(f"name,nwins,n,ratio\n")
    best = None
    best_nwins = 0
    n = args.num_rounds
    for name in strategies:
        strategy = strategies.strategies[name]
        nwins = run_strategy(name, strategy, n)
        if nwins > best_nwins:
            best_nwins = nwins
            best = name
        msg = f"{name},{nwins},{n},{nwins / n}"
        args.outfile.write("%s\n" % (msg,))
        logging.info("%s", msg)

    sys.stdout.write(f"Best: {best} {best_nwins} {n}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-D", "--debug", action="store_true", default=False)
    parser.add_argument(
        "-W",
        "--win-is-bet",
        action="store_true",
        default=False,
        help="use total bet amount for target, instead of the total amount in hand",
    )
    parser.add_argument("-n", "--num-rounds", default=10000)
    parser.add_argument("-p", "--probability", default=0.4)
    parser.add_argument("-s", "--start", default=2000)
    parser.add_argument("-t", "--target", default=10000)
    parser.add_argument(
        "outfile", nargs="?", type=argparse.FileType("w"), default=sys.stdout
    )
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
