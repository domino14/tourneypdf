# Only works with woggles tournaments
import requests
import json


class FetchTourneyError(Exception):
    pass


def get_tournament(url: str):
    print("get tourney with url", url)
    slug = None
    for prefix in [
        "https://woogles.io",
        "https://www.woogles.io",
        "www.woogles.io",
        "woogles.io",
    ]:
        if url.startswith(prefix):
            slug = url[len(prefix) :]
    if not slug:
        raise FetchTourneyError("Bad URL format")

    tm = requests.post(
        "https://woogles.io/twirp/tournament_service.TournamentService/GetTournamentMetadata",
        headers={"content-type": "application/json"},
        data=json.dumps({"slug": slug}),
    )
    if tm.status_code != 200:
        raise FetchTourneyError("Error fetching metadata: " + str(tm.status_code))

    tid = tm.json()["metadata"]["id"]
    t = requests.post(
        "https://woogles.io/twirp/tournament_service.TournamentService/GetTournament",
        headers={"content-type": "application/json"},
        data=json.dumps({"id": tid}),
    )

    return {"t": t.json(), "meta": tm.json()}


def player_by_idx(tourney, div, idx):
    p = tourney["divisions"][div]["players"]["persons"][idx]
    return p["id"].split(":")[1], p["rating"]
