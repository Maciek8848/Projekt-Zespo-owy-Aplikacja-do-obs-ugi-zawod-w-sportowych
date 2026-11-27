from flask import Flask, render_template_string
from mocks.format_mock import knockout_mock
from mocks.database_mock import DatabaseMock

# Stany turnieju
STATE_REGISTRATION = "registration"
STATE_IN_PROGRESS = "in_progress"
STATE_FINISHED = "finished"

# Formaty turnieju - generatory rund
ROUND_GENERATORS = {
    "knockout": knockout_mock,
}

class TournamentService:
    def __init__(self, db, round_generators):
        self.db = db
        self.round_generators = round_generators

    def _get_tournament_or_raise(self, tournament_id):
        tournament = self.db.get_tournament(tournament_id)
        if tournament is None:
            raise Exception(f"Turniej o id={tournament_id} nie istnieje w bazie danych.")
        return tournament


    def create_tournament(self, name, format):
        if not name or not name.strip():
            raise Exception("Nazwa turnieju nie może być pusta.")
        if format not in self.round_generators:
            raise Exception(f"Nieznany format turnieju: {format}")
        return self.db.add_tournament(name, format, STATE_REGISTRATION)

    def register_player(self, tournament_id, player_id):
        tournament = self._get_tournament_or_raise(tournament_id)
        if tournament["state"] != STATE_REGISTRATION:
            raise Exception("Nie można zapisywać się do turnieju, który już wystartował.")
        if self.db.get_player(player_id) is None:
            raise Exception(f"Zawodnik/drużyna o id={player_id} nie istnieje w bazie danych.")
        if any(p["id"] == player_id for p in self.db.get_participants(tournament_id)):
            raise Exception("Zawodnik/drużyna jest już zapisany do tego turnieju.")
        self.db.add_participant(tournament_id, player_id)

    def start_tournament(self, tournament_id):
        tournament = self._get_tournament_or_raise(tournament_id)
        if tournament["state"] != STATE_REGISTRATION:
            raise Exception("Turniej już wystartował lub się zakończył.")
        players = self.db.get_participants(tournament_id)
        if len(players) == 0:
            raise Exception("Nie można rozpocząć turnieju bez zawodników.")
        round_generator = self.round_generators[tournament["format"]]
        next_round_matches = round_generator(players, [], 1)
        self.db.add_matches(tournament_id, next_round_matches)
        return self.db.update_tournament(tournament_id, state=STATE_IN_PROGRESS, current_round=1)

    def submit_result(self, match_id, scores):
        match = self.db.get_match(match_id)
        if match is None:
            raise Exception(f"Mecz o id={match_id} nie istnieje.")
        tournament = self._get_tournament_or_raise(match["tournament_id"])
        if tournament["state"] != STATE_IN_PROGRESS:
            raise Exception("Wyniki można wpisywać tylko w trwającym turnieju.")
        if match["finished"]:
            raise Exception("Wynik tego meczu został już wpisany.")
        return self.db.save_result(match_id, scores)

    def advance_round(self, tournament_id):
        tournament = self._get_tournament_or_raise(tournament_id)
        if tournament["state"] != STATE_IN_PROGRESS:
            raise Exception("Turniej nie jest w trakcie.")
        matches = self.db.get_matches(tournament_id)
        current_round = tournament["current_round"]
        for m in matches:
            if m["round"] == current_round and not m["finished"]:
                raise Exception("Nie wszystkie mecze bieżącej rundy miały wpisany wynik.")
        round_generator = self.round_generators[tournament["format"]]
        players = self.db.get_participants(tournament_id)
        next_round_matches = round_generator(players, matches, current_round + 1)
        if not next_round_matches:
            return self.db.update_tournament(tournament_id, state=STATE_FINISHED)
        self.db.add_matches(tournament_id, next_round_matches)
        return self.db.update_tournament(tournament_id, current_round=current_round + 1)



PLACEHOLDER = """
<!doctype html>
<head>
    <title>System turniejowy</title>
</head>
<body>
    <h1>Kiedyś będzie tutaj frontend</h1>
</body>
</html>
"""

app = Flask(__name__)

db = DatabaseMock()
service = TournamentService(db, ROUND_GENERATORS)

@app.route("/")
def index():
    return render_template_string(PLACEHOLDER)


def testuj_czy_dziala():
    # Symuluje turniej
    test_db = DatabaseMock()
    test_service = TournamentService(test_db, ROUND_GENERATORS)

    tournament = test_service.create_tournament("Drabinka testowa", "knockout")
    t_id = tournament["id"]
    for name in ["Player A", "Player B", "Player C", "Player D", "Player E"]:
        player = test_db.add_player(name)
        test_service.register_player(t_id, player["id"])

    test_service.start_tournament(t_id)
    while test_db.get_tournament(t_id)["state"] == STATE_IN_PROGRESS:
        current_round = test_db.get_tournament(t_id)["current_round"]
        print(f"Runda {current_round}:")
        for match in test_db.get_matches(t_id):
            if match["round"] == current_round:
                if not match["finished"]:
                    test_service.submit_result(match["id"], [0, 2]) #każdemu meczowi wynik 0:2
                    match = test_db.get_match(match["id"])
                print(f"  mecz id={match['id']}: p_ids={match['player_ids']}, wynik {match['scores']}")
        test_service.advance_round(t_id)
    print("Stan turnieju:", test_db.get_tournament(t_id)["state"])


if __name__ == "__main__":
    testuj_czy_dziala()
    app.run(debug=True)
