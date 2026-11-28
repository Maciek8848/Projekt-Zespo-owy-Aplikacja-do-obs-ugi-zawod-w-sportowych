from app import TournamentService
from mocks.database_mock import DatabaseMock
from swiss import swiss_system, rounds_for


def test_swiss_with_tournament_service():
    db = DatabaseMock()
    service = TournamentService(db, {"swiss": swiss_system})

    tournament = service.create_tournament("Test swiss", "swiss")
    tournament_id = tournament["id"]

    for i in range(1, 8):
        player = db.add_player(f"Player {i}")
        service.register_player(tournament_id, player["id"])

    service.start_tournament(tournament_id)

    rounds_played = 0
    while db.get_tournament(tournament_id)["state"] == "in_progress":
        current_round = db.get_tournament(tournament_id)["current_round"]

        for match in db.get_matches(tournament_id):
            if match["round"] == current_round and not match["finished"]:
                service.submit_result(match["id"], [2, 0])

        service.advance_round(tournament_id)
        rounds_played += 1

    assert db.get_tournament(tournament_id)["state"] == "finished"
    assert rounds_played == rounds_for(7)