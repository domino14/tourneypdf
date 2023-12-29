from fetch_tourney import get_tournament, player_by_idx
import sys


def stats(tourney, div):
    # Calculate biggest upset.
    players = tourney["divisions"][div]["players"]["persons"]
    pairings = tourney["divisions"][div]["pairing_map"]

    upsets = []
    high_scores = []
    for _, pairing in pairings.items():
        p1 = pairing["players"][0]
        p2 = pairing["players"][1]
        results = pairing["games"][0]["results"]
        if results[0] == "WIN":
            winner = player_by_idx(tourney, div, p1)
            loser = player_by_idx(tourney, div, p2)
        elif results[1] == "WIN":
            winner = player_by_idx(tourney, div, p2)
            loser = player_by_idx(tourney, div, p1)
        else:
            winner = -1
        if winner != -1:
            if winner[1] < loser[1]:
                diff = loser[1] - winner[1]
                upsets.append((diff, (winner[0], loser[0])))

    upsets = sorted(upsets, key=lambda y: -y[0])
    print("RatingDiff\tWinner\tLoser")
    for upset in upsets:
        print(f"{upset[0]}\t{upset[1][0]}\t{upset[1][1]}")

    # Calculate highest game


if __name__ == "__main__":
    tid = sys.argv[1]
    div = sys.argv[2]
    tourney = get_tournament(tid)
    stats(tourney['t'], div)
