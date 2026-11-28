POINTS_WIN = 1.0
POINTS_DRAW = 0.5
POINTS_NO_OPPONENT = 1.0


def build_table(players, matches, before_round=None):
    table = {}
    for p in players:
        table[p["id"]] = {
            "id": p["id"],
            "name": p["name"],
            "points": 0.0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "opponents": [],
            "had_bye": False,
            "buchholz": 0.0,
        }

    for m in matches:
        if before_round is not None and m["round"] >= before_round:
            continue

        if not m["finished"]:
            if before_round is not None:
                raise ValueError(f"Mecz id={m['id']} nie ma wpisanego wyniku.")
            continue

        ids = []
        for player_id in m["player_ids"]:
            if player_id is not None:
                ids.append(player_id)

        if len(ids) == 1:
            row = table[ids[0]]
            row["points"] += POINTS_NO_OPPONENT
            row["wins"] += 1
            row["had_bye"] = True
            continue

        if len(ids) != 2:
            raise ValueError("System szwajcarski obsługuje tylko mecze 1 na 1.")

        a, b = ids
        score_a, score_b = m["scores"]

        if score_a == score_b:
            for player_id in (a, b):
                table[player_id]["points"] += POINTS_DRAW
                table[player_id]["draws"] += 1
        else:
            if score_a > score_b:
                winner, loser = a, b
            else:
                winner, loser = b, a
            table[winner]["points"] += POINTS_WIN
            table[winner]["wins"] += 1
            table[loser]["losses"] += 1

        table[a]["opponents"].append(b)
        table[b]["opponents"].append(a)

    for row in table.values():
        row["buchholz"] = sum(table[o]["points"] for o in row["opponents"])

    return table


def sorted_ids(table):
    keys = []
    for player_id, row in table.items():
        keys.append((-row["points"], -row["buchholz"], player_id))
    keys.sort()

    ids = []
    for _, _, player_id in keys:
        ids.append(player_id)
    return ids


def swiss_standings(players, matches):
    table = build_table(players, matches)
    order = sorted_ids(table)

    standings = []
    for rank, player_id in enumerate(order, start=1):
        row = table[player_id]
        standings.append({
            "rank": rank,
            "id": player_id,
            "name": row["name"],
            "points": row["points"],
            "buchholz": row["buchholz"],
            "wins": row["wins"],
            "draws": row["draws"],
            "losses": row["losses"],
        })
    return standings