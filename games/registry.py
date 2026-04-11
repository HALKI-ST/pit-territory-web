from __future__ import annotations

from typing import Callable, Dict

from games.pit_territory import PitTerritoryGame


GAME_REGISTRY: Dict[str, Callable[[], object]] = {
    PitTerritoryGame.game_type: PitTerritoryGame,
}

GAME_CATALOG = [
    PitTerritoryGame.catalog_entry(),
]


def create_game(game_type: str):
    factory = GAME_REGISTRY.get(game_type)
    if factory is None:
        raise KeyError(game_type)
    return factory()
