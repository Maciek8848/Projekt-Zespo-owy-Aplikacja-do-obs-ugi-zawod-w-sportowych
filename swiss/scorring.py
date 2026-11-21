def calculate_standings(players, matches, win_pts=1.0, draw_pts=0.5):
    points = {p["id"]: 0.0 for p in players}
    opponents = {p["id"]: [] for p in players}

    for m in matches:
        p1, p2, winner = m["p1"], m.get("p2"), m.get("winner")
        if p2 is None:
            points[p1] += win_pts
        else:
            opponents[p1].append(p2)
            opponents[p2].append(p1)
            if winner is None:
                points[p1] += draw_pts
                points[p2] += draw_pts
            else:
                points[winner] += win_pts

    table = [
        {
            "id": p["id"],
            "name": p["name"],
            "points": points[p["id"]],
            "buchholz": sum(points[opp] for opp in opponents[p["id"]]),
        }
        for p in players
    ]
    table.sort(key=lambda x: (-x["points"], -x["buchholz"]))
    return table