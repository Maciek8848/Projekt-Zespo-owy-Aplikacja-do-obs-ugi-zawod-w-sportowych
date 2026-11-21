
# Stany turnieju
STATE_REGISTRATION = "registration"
STATE_IN_PROGRESS = "in_progress"
STATE_FINISHED = "finished"


class DatabaseMock:
    def __init__(self):
        self._players = {}
        self._tournaments = {}
        self._matches = {}
        self._participants = {}
        self._counter = 0

    def _next_id(self):
        self._counter += 1
        return self._counter

    def add_player(self, name):
        player = {"id": self._next_id(), "name": name}
        self._players[player["id"]] = player
        return player

    def get_player(self, player_id):
        player = self._players.get(player_id)
        return player

    def add_tournament(self, name, format):
        tournament = {
            "id": self._next_id(),
            "name": name,
            "format": format,
            "state": STATE_REGISTRATION,
            "current_round": 0,
        }
        self._tournaments[tournament["id"]] = tournament
        self._participants[tournament["id"]] = []
        return tournament

    def get_tournament(self, tournament_id):
        tournament = self._tournaments.get(tournament_id)
        return tournament

    def update_tournament(self, tournament_id, **fields):
        self._tournaments[tournament_id].update(fields)
        return self._tournaments[tournament_id]

    def add_participant(self, tournament_id, player_id):
        self._participants[tournament_id].append(player_id)

    def get_participants(self, tournament_id):
        return [self._players[p_id] for p_id in self._participants[tournament_id]]

    def add_match(self, tournament_id, matchups):
        for matchup in matchups:
            match = {
                "id": self._next_id(),
                "tournament_id": tournament_id,
                "round": matchup["round"],
                "player_ids": matchup["player_ids"],
                "scores": [],
                "finished": False,
            }
            self._matches[match["id"]] = match

    def get_matches(self, tournament_id):
        matches = []
        for m in self._matches.values():
            if m["tournament_id"] == tournament_id:
                matches.append(m)
        return matches

    def get_match(self, match_id):
        match = self._matches.get(match_id)
        return match

    def save_result(self, match_id, scores):
        match = self._matches[match_id]
        match.update(scores=scores, finished=True)
        return match