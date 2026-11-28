from .scorring import build_table, sorted_ids

MAX_SEARCH_STEPS = 200000


def rounds_for(n_players):
    if n_players < 2:
        return 0
    return (n_players - 1).bit_length()


def _pair(order, played, allow_rematch, budget):
    if not order:
        return []
    if budget[0] <= 0:
        return None
    budget[0] -= 1

    first = order[0]
    rest = order[1:]
    for i, opponent in enumerate(rest):
        if not allow_rematch and opponent in played[first]:
            continue
        others = rest[:i] + rest[i + 1:]
        other_pairs = _pair(others, played, allow_rematch, budget)
        if other_pairs is not None:
            return [(first, opponent)] + other_pairs
    return None


def _choose_pairing(order, table):
    played = {}
    for player_id in order:
        played[player_id] = set(table[player_id]["opponents"])

    if len(order) % 2 == 0:
        bye_candidates = [None]
    else:
        without_bye = []
        with_bye = []
        for player_id in reversed(order):
            if table[player_id]["had_bye"]:
                with_bye.append(player_id)
            else:
                without_bye.append(player_id)
        bye_candidates = without_bye + with_bye

    for allow_rematch in (False, True):
        for bye in bye_candidates:
            if bye is not None and table[bye]["had_bye"] and not allow_rematch:
                continue

            rest = list(order)
            if bye is not None:
                rest.remove(bye)

            pairs = _pair(rest, played, allow_rematch, [MAX_SEARCH_STEPS])
            if pairs is not None:
                return pairs, bye

    raise RuntimeError("Nie udało się wygenerować par.")


def swiss_system(players, matches, next_round, num_rounds=None):
    if num_rounds is None:
        num_rounds = rounds_for(len(players))
    if next_round > num_rounds:
        return []

    table = build_table(players, matches, before_round=next_round)
    order = sorted_ids(table)
    pairs, bye = _choose_pairing(order, table)

    next_round_matches = []
    for a, b in pairs:
        next_round_matches.append({"round": next_round, "player_ids": [a, b]})
    if bye is not None:
        next_round_matches.append({"round": next_round, "player_ids": [bye, None]})
    return next_round_matches