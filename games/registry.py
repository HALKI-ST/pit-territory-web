from __future__ import annotations

from typing import Callable, Dict

from games.auction_race import AuctionRaceGame
from games.battle_line import BattleLineGame
from games.five_ruler import FiveRulerGame
from games.english_shooter import EnglishShooterGame
from games.iko import IkoGame
from games.morning_answer import MorningAnswerGame
from games.mouse_trap import MouseTrapGame
from games.pit_territory import PitTerritoryGame
from games.spi_rush import SpiRushGame
from games.the_grand import TheGrandGame
from games.the_grand_old import TheGrandOldGame
from games.word_spy import WordSpyGame


GAME_REGISTRY: Dict[str, Callable[[], object]] = {
    PitTerritoryGame.game_type: PitTerritoryGame,
    BattleLineGame.game_type: BattleLineGame,
    IkoGame.game_type: IkoGame,
    SpiRushGame.game_type: SpiRushGame,
    AuctionRaceGame.game_type: AuctionRaceGame,
    FiveRulerGame.game_type: FiveRulerGame,
    EnglishShooterGame.game_type: EnglishShooterGame,
    MorningAnswerGame.game_type: MorningAnswerGame,
    MouseTrapGame.game_type: MouseTrapGame,
    TheGrandGame.game_type: TheGrandGame,
    TheGrandOldGame.game_type: TheGrandOldGame,
    WordSpyGame.game_type: WordSpyGame,
}

GAME_CATALOG = [
    PitTerritoryGame.catalog_entry(),
    BattleLineGame.catalog_entry(),
    IkoGame.catalog_entry(),
    SpiRushGame.catalog_entry(),
    AuctionRaceGame.catalog_entry(),
    FiveRulerGame.catalog_entry(),
    EnglishShooterGame.catalog_entry(),
    MorningAnswerGame.catalog_entry(),
    MouseTrapGame.catalog_entry(),
    TheGrandGame.catalog_entry(),
    TheGrandOldGame.catalog_entry(),
    WordSpyGame.catalog_entry(),
]


def create_game(game_type: str):
    factory = GAME_REGISTRY.get(game_type)
    if factory is None:
        raise KeyError(game_type)
    return factory()
