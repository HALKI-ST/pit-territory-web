from __future__ import annotations

from typing import Callable, Dict

from games.auction_race import AuctionRaceGame
from games.english_shooter import EnglishShooterGame
from games.morning_answer import MorningAnswerGame
from games.mouse_trap import MouseTrapGame
from games.pit_territory import PitTerritoryGame
from games.word_spy import WordSpyGame


GAME_REGISTRY: Dict[str, Callable[[], object]] = {
    PitTerritoryGame.game_type: PitTerritoryGame,
    AuctionRaceGame.game_type: AuctionRaceGame,
    EnglishShooterGame.game_type: EnglishShooterGame,
    MorningAnswerGame.game_type: MorningAnswerGame,
    MouseTrapGame.game_type: MouseTrapGame,
    WordSpyGame.game_type: WordSpyGame,
}

GAME_CATALOG = [
    PitTerritoryGame.catalog_entry(),
    AuctionRaceGame.catalog_entry(),
    EnglishShooterGame.catalog_entry(),
    MorningAnswerGame.catalog_entry(),
    MouseTrapGame.catalog_entry(),
    WordSpyGame.catalog_entry(),
]


def create_game(game_type: str):
    factory = GAME_REGISTRY.get(game_type)
    if factory is None:
        raise KeyError(game_type)
    return factory()
