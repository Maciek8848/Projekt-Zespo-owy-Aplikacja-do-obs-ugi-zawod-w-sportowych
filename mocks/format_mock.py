
def knockout_mock(players, matches, round_number):
    ids = []
    if round_number == 1:
        ids = [p["id"] for p in players]
    else:
        for m in matches:
            if m["round"] == round_number - 1:
                if m["player_ids"][1] is None or m["scores"][0] > m["scores"][1]:
                    ids.append(m["player_ids"][0])
                else:
                    ids.append(m["player_ids"][1])
    if len(ids) <= 1:
        return []  # Pusta lista meczów nastęnej rundy oznacza koniec turnieju
    
    next_round_matches = []
    for i in range(0, len(ids), 2):
        next_round_matches.append({
            "round": round_number,
            "player_ids": [ids[i], 
                           ids[i+1] if i+1 < len(ids) else None]
        })
    return next_round_matches
