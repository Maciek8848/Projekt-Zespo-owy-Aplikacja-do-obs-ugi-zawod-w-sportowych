import math
from .scoring import calculate_standings


def recommended_rounds(num_players):
    return 0 if num_players < 2 else math.ceil(math.log2(num_players))


def generate_next_round(players, matches):
    if len(players) < 2:
        return {"pairs": [], "bye": players[0]["id"] if players else None}

    ids = [row["id"] for row in calculate_standings(players, matches)]
    played = {frozenset({m["p1"], m["p2"]}) for m in matches if m.get("p2") is not None}
    had_bye = {m["p1"] for m in matches if m.get("p2") is None}

    bye = None
    if len(ids) % 2 != 0:
        bye = next((pid for pid in reversed(ids) if pid not in had_bye), ids[-1])
        ids.remove(bye)

    def find_pairs(pool):
        if not pool:
            return []
        p1 = pool[0]
        for i in range(1, len(pool)):
            p2 = pool[i]
            if frozenset({p1, p2}) not in played:
                res = find_pairs(pool[1:i] + pool[i + 1:])
                if res is not None:
                    return [(p1, p2)] + res
        return None

    pairs = find_pairs(ids)
    if pairs is None:
        raise ValueError("Brak możliwości utworzenia par")

    return {"pairs": pairs, "bye": bye}