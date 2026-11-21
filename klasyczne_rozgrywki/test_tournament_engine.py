import unittest
from tournament_engine import Player, GroupStageEngine, KnockoutBracketEngine


class TestTournamentEngine(unittest.TestCase):
    def setUp(self):
        # Sztuczni zawodnicy z przypisanym rankingiem
        self.players_8 = [
            Player(id=i, name=f"Gracz_{i}", ranking=i) for i in range(1, 9)
        ]

    # --- TESTY FAZY GRUPOWEJ ---

    def test_group_pot_distribution(self):
        """Sprawdza, czy zawodnicy z tego samego koszyka nie trafiają do tej samej grupy."""
        engine = GroupStageEngine(self.players_8, num_groups=2)
        groups = engine.assign_groups_from_pots(shuffle_pots=True, seed=42)

        self.assertEqual(len(groups["Grupa A"]), 4)
        self.assertEqual(len(groups["Grupa B"]), 4)

        # Koszyk 1 to gracze o rankingu 1 i 2 - muszą być w osobnych grupach
        top_seeds_in_a = [p for p in groups["Grupa A"] if p.ranking in (1, 2)]
        self.assertEqual(len(top_seeds_in_a), 1)

    def test_group_points_and_advancement(self):
        """Sprawdza zliczanie punktów (3/1/0), bilans bramek i poprawny awans."""
        engine = GroupStageEngine(self.players_8, num_groups=2)
        # Deterministyczny podział bez tasowania:
        # Grupa A: Gracz_1, Gracz_3, Gracz_5, Gracz_7
        # Grupa B: Gracz_2, Gracz_4, Gracz_6, Gracz_8
        engine.assign_groups_from_pots(shuffle_pots=False)

        # Symulacja wyników w Grupie A:
        # M1: Gracz_1 vs Gracz_3 -> 2:0 (Gracz_1: 3 pkt)
        # M2: Gracz_1 vs Gracz_5 -> 1:1 (Gracz_1: 4 pkt, Gracz_5: 1 pkt)
        # M3: Gracz_1 vs Gracz_7 -> 0:1 (Gracz_7: 3 pkt)
        # M4: Gracz_3 vs Gracz_5 -> 3:0 (Gracz_3: 3 pkt, bilans +1)
        # M5: Gracz_3 vs Gracz_7 -> 1:1 (Gracz_3: 4 pkt, Gracz_7: 4 pkt)
        # M6: Gracz_5 vs Gracz_7 -> 0:2 (Gracz_7: 7 pkt)
        engine.record_match_result("Grupa A", "Grupa A_M1", 2, 0)
        engine.record_match_result("Grupa A", "Grupa A_M2", 1, 1)
        engine.record_match_result("Grupa A", "Grupa A_M3", 0, 1)
        engine.record_match_result("Grupa A", "Grupa A_M4", 3, 0)
        engine.record_match_result("Grupa A", "Grupa A_M5", 1, 1)
        engine.record_match_result("Grupa A", "Grupa A_M6", 0, 2)

        standings_a = engine.get_standings("Grupa A")
        # Oczekiwana kolejność w Grupie A:
        # 1. Gracz_7 (7 pkt)
        # 2. Gracz_1 (4 pkt, bilans +1, bramki 3) vs Gracz_3 (4 pkt, bilans +1, bramki 4) -> wyżej Gracz_3!
        self.assertEqual(standings_a[0].player.name, "Gracz_7")
        self.assertEqual(standings_a[0].points, 7)
        self.assertEqual(standings_a[1].player.name, "Gracz_3")
        self.assertEqual(standings_a[2].player.name, "Gracz_1")

        # Symulacja wyników w Grupie B (wygrywają faworyci Gracz_2 i Gracz_4)
        engine.record_match_result("Grupa B", "Grupa B_M1", 2, 1)  # 2 vs 4
        engine.record_match_result("Grupa B", "Grupa B_M2", 3, 0)  # 2 vs 6
        engine.record_match_result("Grupa B", "Grupa B_M3", 2, 0)  # 2 vs 8
        engine.record_match_result("Grupa B", "Grupa B_M4", 2, 0)  # 4 vs 6
        engine.record_match_result("Grupa B", "Grupa B_M5", 1, 0)  # 4 vs 8
        engine.record_match_result("Grupa B", "Grupa B_M6", 1, 1)  # 6 vs 8

        advancing = engine.get_advancing_players(advance_per_group=2)
        advancing_names = [p.name for p in advancing]
        self.assertEqual(advancing_names, ["Gracz_7", "Gracz_3", "Gracz_2", "Gracz_4"])

    # --- TESTY DRABINKI PUCHAROWEJ ---

    def test_knockout_initial_pairing_and_advancement(self):
        """Sprawdza poprawne parowanie 1. rundy, przepchnięcie do finału i wyłonienie mistrza."""
        players_4 = self.players_8[:4]
        bracket = KnockoutBracketEngine(players_4)

        # Dla 4 graczy rozstawienie to: (1 vs 4) oraz (2 vs 3)
        sf1 = bracket.matches["R1_M1"]
        sf2 = bracket.matches["R1_M2"]
        final = bracket.matches["R2_M1"]

        self.assertEqual((sf1.player_a.ranking, sf1.player_b.ranking), (1, 4))
        self.assertEqual((sf2.player_a.ranking, sf2.player_b.ranking), (2, 3))
        self.assertEqual(final.round_name, "Finał")

        # Rozstrzygnięcie półfinałów
        w1 = bracket.record_match_result("R1_M1", 3, 1)  # Wygrywa Gracz_1
        w2 = bracket.record_match_result("R1_M2", 0, 2)  # Wygrywa Gracz_3 (niespodzianka)

        self.assertEqual(w1.name, "Gracz_1")
        self.assertEqual(w2.name, "Gracz_3")

        # Sprawdzenie czy gracze zostali przepchnięci do finału
        self.assertEqual(final.player_a.name, "Gracz_1")
        self.assertEqual(final.player_b.name, "Gracz_3")
        self.assertIsNone(bracket.champion)

        # Rozstrzygnięcie finału
        champion = bracket.record_match_result("R2_M1", 1, 2)
        self.assertEqual(champion.name, "Gracz_3")
        self.assertEqual(bracket.champion.name, "Gracz_3")

    def test_knockout_rejects_draw(self):
        """Sprawdza, czy drabinka blokuje remis w meczu pucharowym."""
        bracket = KnockoutBracketEngine(self.players_8[:2])
        with self.assertRaises(ValueError):
            bracket.record_match_result("R1_M1", 2, 2)


if __name__ == "__main__":
    unittest.main()