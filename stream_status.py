import sys


from fetch_tourney import get_tournament


def player_standing(username, tournament_id):
    t = get_tournament(tournament_id)
    divisions = t["divisions"]
    foundd = None
    founddiv = None
    foundp = None

    for dname, div in divisions.items():
        for p in div["players"]["persons"]:
            if username == username:
                foundp = p
                foundd = dname
                founddiv = div
                break
        if foundp:
            break
    print("division", foundd)
    standings = founddiv["standings"]
    current_round = founddiv["current_round"]
    standings = standings[str(current_round)]["standings"]
    for idx, p in enumerate(standings):
        if p["player_id"].split(":")[1] == username:
            place = idx+1
            standing = p
            break

    print(place)
    print(standing)
    if place % 10 == 1:
        suffix = 'st'
    elif place % 10 == 2:
        suffix = 'nd'
    elif place % 10 == 3:
        suffix = 'rd'
    else:
        suffix = 'th'
    with open("out.txt", 'w') as f:
        f.write(f"{standing['wins'] + standing['draws']/2} - {standing['losses'] + standing['draws']/2} {'+' if standing['spread']>= 0 else ''}{standing['spread']}")
        f.write('\n')
        f.write(f'In {place}{suffix} place\n')

if __name__ == "__main__":
    
    player_standing(sys.argv[1], sys.argv[2])