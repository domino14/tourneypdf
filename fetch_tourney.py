# Only works with woggles tournaments
import requests
import json


def get_tournament(id):
    print("get tourney with id", id)
    url = "https://woogles.io/twirp/tournament_service.TournamentService/GetTournament"
    res = requests.post(
        url,
        headers={"content-type": "application/json"},
        data=json.dumps({"id": id}),
    )
    return res.json()


def player_by_idx(tourney, div, idx):
    p = tourney["divisions"][div]["players"]["persons"][idx]
    return p["id"].split(":")[1], p["rating"]
