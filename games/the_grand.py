from __future__ import annotations

from games.the_grand_old import (
    BOARD_SIZE,
    CHARACTERS,
    COIN_TARGET,
    DEBUG_FIELD_TYPE,
    FIELD_TYPES,
    GameError,
    MAX_SETS,
    MIN_SPAWN_DISTANCE,
    PlayerSlot,
    ROUNDS_PER_SET,
    SkillDef,
    TEAM_NAMES,
    TEAM_SYMBOLS,
    TheGrandOldGame,
    UnitState,
    VIEWPORT_SIZE,
    CharacterDef,
    FlagState,
    ceil_half,
)


class TheGrandGame(TheGrandOldGame):
    game_type = "the_grand"
    title = "The Grand"
    subtitle = "広域フィールド対戦プロトタイプ"
    category = "original"
    min_players = 2
    max_players = 2
    player_label = "2 players"

    @classmethod
    def catalog_entry(cls) -> dict:
        return {
            "game_type": cls.game_type,
            "title": cls.title,
            "subtitle": cls.subtitle,
            "category": cls.category,
            "status": "playable",
            "min_players": cls.min_players,
            "max_players": cls.max_players,
            "player_label": cls.player_label,
        }
