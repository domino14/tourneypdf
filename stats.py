from fetch_tourney import get_tournament, player_by_idx
import sys


def stats(tourney):
    sd = {}
    for div in tourney["divisions"]:
        # Calculate biggest upset.
        players = tourney["divisions"][div]["players"]["persons"]
        pairings = tourney["divisions"][div]["pairing_map"]
        upsets = []
        highest_score = [-100000, None, None]
        lowest_win = [100000, None, None]
        total_scores = {}
        for _, pairing in pairings.items():
            scores = pairing["games"][0]["scores"]
            results = pairing["games"][0]["results"]
            players = [
                player_by_idx(tourney, div, pairing["players"][0]),
                player_by_idx(tourney, div, pairing["players"][1]),
            ]
            rd = pairing["round"]
            if results[0] == "WIN":
                winner = players[0]
                loser = players[1]
            elif results[1] == "WIN":
                winner = players[1]
                loser = players[0]
            else:
                winner = -1
            if winner != -1:
                if winner[1] < loser[1]:
                    diff = loser[1] - winner[1]
                    upsets.append((diff, rd, (winner[0], loser[0])))

            # only count non-bye scores
            if players[0] != players[1]:
                for idx, sc in enumerate(scores):
                    if sc > highest_score[0]:
                        highest_score = [sc, players[idx][0], rd]
                    if results[idx] == "WIN" and sc < lowest_win[0]:
                        lowest_win = [sc, players[idx][0], rd]
                    if players[idx][0] not in total_scores:
                        total_scores[players[idx][0]] = [sc]
                    else:
                        total_scores[players[idx][0]].append(sc)

        upsets = sorted(upsets, key=lambda y: -y[0])

        print("RatingDiff\tWinner\tLoser\tRound")
        for upset in upsets:
            print(f"{upset[0]}\t{upset[2][0]}\t{upset[2][1]}\t{upset[1] + 1}")

        print("Highest game: ", highest_score)
        print("Lowest win: ", lowest_win)

        average_scores = [
            (player, sum(scores) / len(scores))
            for player, scores in total_scores.items()
        ]
        sorted_average_scores = sorted(average_scores, key=lambda x: x[1], reverse=True)

        # Calculate highest game
        # High Game, Biggest Upset, Low Win, Tuff Luck
        sd[div] = {
            "upsets": upsets,
            "highscore": highest_score,
            "lowwin": lowest_win,
            "avgscores": sorted_average_scores,
        }
        print("Average Scores", sorted_average_scores)
    return sd


if __name__ == "__main__":
    turl = sys.argv[1]
    tourney = get_tournament(turl)
    stats(tourney["t"])
