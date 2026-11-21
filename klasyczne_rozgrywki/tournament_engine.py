from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import math
import random


@dataclass(frozen=True)
class Player:
    id: int
    name: str
    ranking: int  # Niższa wartość = wyższy rozstawiony numer (np. 1 to lider rankingu)


@dataclass
class Match:
    id: str
    round_name: str
    player_a: Optional[Player] = None
    player_b: Optional[Player] = None
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    winner: Optional[Player] = None
    next_match_id: Optional[str] = None
    next_match_slot: Optional[str] = None  # 'A' lub 'B'

    @property
    def is_finished(self) -> bool:
        return self.score_a is not None and self.score_b is not None


@dataclass
class GroupStanding:
    player: Player
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against


# =====================================================================
# SILNIK ROZGRYWEK (II.2) - FAZA GRUPOWA
# =====================================================================

class GroupStageEngine:
    def __init__(self, players: List[Player], num_groups: int):
        if len(players) % num_groups != 0:
            raise ValueError("Liczba zawodników musi być podzielna przez liczbę grup.")
        self.players = sorted(players, key=lambda p: p.ranking)
        self.num_groups = num_groups
        self.groups: Dict[str, List[Player]] = {}
        self.matches: Dict[str, List[Match]] = {}

    def assign_groups_from_pots(self, shuffle_pots: bool = True, seed: Optional[int] = None) -> Dict[str, List[Player]]:
        """
        Dzieli zawodników na koszyki na podstawie rankingu i losuje po jednym
        zawodniku z każdego koszyka do każdej z grup.
        """
        rng = random.Random(seed)
        group_names = [f"Grupa {chr(65 + i)}" for i in range(self.num_groups)]
        self.groups = {name: [] for name in group_names}

        # Podział na koszyki o rozmiarze równym liczbie grup
        pots = [
            self.players[i : i + self.num_groups]
            for i in range(0, len(self.players), self.num_groups)
        ]

        for pot in pots:
            pot_copy = list(pot)
            if shuffle_pots:
                rng.shuffle(pot_copy)
            for group_name, player in zip(group_names, pot_copy):
                self.groups[group_name].append(player)

        self._generate_group_matches()
        return self.groups

    def _generate_group_matches(self) -> None:
        """Generuje mecze systemem każdy z każdym (round-robin) w ramach grup."""
        self.matches = {}
        for group_name, members in self.groups.items():
            group_matches = []
            match_idx = 1
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    m = Match(
                        id=f"{group_name}_M{match_idx}",
                        round_name=group_name,
                        player_a=members[i],
                        player_b=members[j],
                    )
                    group_matches.append(m)
                    match_idx += 1
            self.matches[group_name] = group_matches

    def record_match_result(self, group_name: str, match_id: str, score_a: int, score_b: int) -> None:
        """Zapisuje wynik meczu grupowego (dozwolone remisy)."""
        if score_a < 0 or score_b < 0:
            raise ValueError("Wynik nie może być ujemny.")

        for match in self.matches[group_name]:
            if match.id == match_id:
                match.score_a = score_a
                match.score_b = score_b
                if score_a > score_b:
                    match.winner = match.player_a
                elif score_b > score_a:
                    match.winner = match.player_b
                else:
                    match.winner = None
                return
        raise KeyError(f"Nie znaleziono meczu {match_id} w {group_name}.")

    def get_standings(self, group_name: str) -> List[GroupStanding]:
        """
        Zlicza punkty (3 za wygraną, 1 za remis, 0 za porażkę) i sortuje tabelę.
        Kryteria rozstrzygania remisów: 1. Punkty, 2. Bilans bramek, 3. Bramki zdobyte, 4. Ranking.
        """
        standings_map: Dict[int, GroupStanding] = {
            p.id: GroupStanding(player=p) for p in self.groups[group_name]
        }

        for match in self.matches[group_name]:
            if not match.is_finished:
                continue

            st_a = standings_map[match.player_a.id]
            st_b = standings_map[match.player_b.id]

            st_a.played += 1
            st_b.played += 1
            st_a.goals_for += match.score_a
            st_a.goals_against += match.score_b
            st_b.goals_for += match.score_b
            st_b.goals_against += match.score_a

            if match.score_a > match.score_b:
                st_a.won += 1
                st_a.points += 3
                st_b.lost += 1
            elif match.score_b > match.score_a:
                st_b.won += 1
                st_b.points += 3
                st_a.lost += 1
            else:
                st_a.drawn += 1
                st_b.drawn += 1
                st_a.points += 1
                st_b.points += 1

        return sorted(
            standings_map.values(),
            key=lambda s: (s.points, s.goal_diff, s.goals_for, -s.player.ranking),
            reverse=True,
        )

    def get_advancing_players(self, advance_per_group: int = 2) -> List[Player]:
        """Wyłania awansujących zawodników z każdej grupy."""
        advancing: List[Player] = []
        for group_name in sorted(self.groups.keys()):
            table = self.get_standings(group_name)
            if advance_per_group > len(table):
                raise ValueError("Liczba awansujących przekracza rozmiar grupy.")
            advancing.extend(entry.player for entry in table[:advance_per_group])
        return advancing


# =====================================================================
# SILNIK ROZGRYWEK (II.2) - DRABINKA PUCHAROWA
# =====================================================================

class KnockoutBracketEngine:
    def __init__(self, players: List[Player]):
        n = len(players)
        if n < 2 or (n & (n - 1)) != 0:
            raise ValueError("Liczba zawodników w drabince musi być potęgą dwójki (np. 2, 4, 8, 16).")
        self.players = players
        self.total_rounds = int(math.log2(n))
        self.matches: Dict[str, Match] = {}
        self.rounds: List[List[Match]] = []
        self.champion: Optional[Player] = None
        self._build_bracket()

    @staticmethod
    def _seeded_order(n: int) -> List[int]:
        """Generuje klasyczne rozstawienie turniejowe (np. dla 8: [1, 8, 4, 5, 2, 7, 3, 6])."""
        order = [1, 2]
        while len(order) < n:
            next_layer = []
            current_sum = len(order) * 2 + 1
            for seed in order:
                next_layer.extend([seed, current_sum - seed])
            order = next_layer
        return order

    def _get_round_name(self, round_idx: int) -> str:
        remaining_rounds = self.total_rounds - round_idx
        if remaining_rounds == 1:
            return "Finał"
        if remaining_rounds == 2:
            return "Półfinał"
        if remaining_rounds == 3:
            return "Ćwierćfinał"
        return f"Runda {round_idx + 1}"

    def _build_bracket(self) -> None:
        """Tworzy strukturę wszystkich rund i paruje zawodników w 1. rundzie."""
        # Tworzenie pustych slotów meczowych od 1. rundy do Finału
        for r_idx in range(self.total_rounds):
            num_matches = 2 ** (self.total_rounds - r_idx - 1)
            r_name = self._get_round_name(r_idx)
            round_matches = []
            for m_idx in range(num_matches):
                match_id = f"R{r_idx + 1}_M{m_idx + 1}"
                match = Match(id=match_id, round_name=r_name)
                round_matches.append(match)
                self.matches[match_id] = match
            self.rounds.append(round_matches)

        # Łączenie meczów w drzewo (wskazanie gdzie trafia zwycięzca)
        for r_idx in range(self.total_rounds - 1):
            for m_idx, match in enumerate(self.rounds[r_idx]):
                next_match = self.rounds[r_idx + 1][m_idx // 2]
                match.next_match_id = next_match.id
                match.next_match_slot = "A" if m_idx % 2 == 0 else "B"

        # Obsadzenie par początkowych zgodnie z rozstawieniem
        seed_indices = self._seeded_order(len(self.players))
        seeded_players = [self.players[idx - 1] for idx in seed_indices]

        for m_idx, match in enumerate(self.rounds[0]):
            match.player_a = seeded_players[2 * m_idx]
            match.player_b = seeded_players[2 * m_idx + 1]

    def record_match_result(self, match_id: str, score_a: int, score_b: int) -> Player:
        """
        Zapisuje wynik meczu pucharowego i automatycznie przepycha wygranego
        do kolejnej rundy lub ogłasza mistrza po finale.
        """
        if match_id not in self.matches:
            raise KeyError(f"Nieznany mecz: {match_id}")

        match = self.matches[match_id]
        if match.player_a is None or match.player_b is None:
            raise RuntimeError(f"Mecz {match_id} nie ma jeszcze kompletu zawodników.")
        if match.is_finished:
            raise RuntimeError(f"Mecz {match_id} został już rozstrzygnięty.")
        if score_a == score_b:
            raise ValueError("W fazie pucharowej mecz nie może zakończyć się remisem.")

        match.score_a = score_a
        match.score_b = score_b
        winner = match.player_a if score_a > score_b else match.player_b
        match.winner = winner

        # Przepchnięcie wygranego dalej lub zakończenie turnieju
        if match.next_match_id:
            next_match = self.matches[match.next_match_id]
            if match.next_match_slot == "A":
                next_match.player_a = winner
            else:
                next_match.player_b = winner
        else:
            # Brak kolejnego meczu oznacza Finał
            self.champion = winner

        return winner
    
if __name__ == "__main__":
    # 1. Wygenerowanie 8 sztucznych zawodników
    mock_players = [
        Player(1, "Anna Kowalska", 1),
        Player(2, "Jan Nowak", 2),
        Player(3, "Piotr Wiśniewski", 3),
        Player(4, "Maria Wójcik", 4),
        Player(5, "Krzysztof Kamiński", 5),
        Player(6, "Agnieszka Lewandowska", 6),
        Player(7, "Tomasz Zieliński", 7),
        Player(8, "Magdalena Szymańska", 8),
    ]

    # 2. Faza grupowa (2 grupy po 4 osoby)
    group_stage = GroupStageEngine(mock_players, num_groups=4)
    group_stage.assign_groups_from_pots()

    rng = random.Random()
    for g_name, g_matches in group_stage.matches.items():
        for m in g_matches:
            group_stage.record_match_result(g_name, m.id, rng.randint(0, 4), rng.randint(0, 4))

    print("=== TABELE KOŃCOWE GRUP ===")
    for g_name in sorted(group_stage.groups.keys()):
        print(f"\n{g_name}:")
        for pos, st in enumerate(group_stage.get_standings(g_name), start=1):
            print(f"  {pos}. {st.player.name:<22} | Pkt: {st.points} | Bramki: {st.goals_for}:{st.goals_against}")

    # 3. Awans po 2 najlepszych zawodników do półfinałów (Drabinka dla 4 osób)
    finalists = group_stage.get_advancing_players(advance_per_group=2)
    knockout = KnockoutBracketEngine(finalists)

    print("\n=== FAZA PUCHAROWA ===")
    for round_matches in knockout.rounds:
        for m in round_matches:
            s_a, s_b = rng.randint(1, 3), rng.randint(0, 2)
            if s_a == s_b:
                s_a += 1  # Brak remisów w drabince
            knockout.record_match_result(m.id, s_a, s_b)
            print(f"[{m.round_name}] {m.player_a.name} {m.score_a}:{m.score_b} {m.player_b.name} -> Awans: {m.winner.name}")

    print(f"\nZWYCIĘZCA TURNIEJU: {knockout.champion.name}")