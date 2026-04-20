from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

from games.the_grand import CHARACTERS, CharacterDef, GameError, PlayerSlot, UnitState


Cell = Tuple[int, int]


class TheGrandLabGame:
    game_type = "the_grand_lab"
    title = "The Grand お試し部屋（1人デバッグ専用）"
    subtitle = "本編ではなくデバッグ専用です。自分・味方・敵を置いて、全技の効果をすぐ検証できます。"
    category = "original"
    min_players = 1
    max_players = 1
    player_label = "1人用"
    seat_order = ["A"]
    host_control_actions: set[str] = set()
    allow_midgame_join = True

    def __init__(self) -> None:
        self.players = {"A": PlayerSlot(symbol="A", name="Player A", connected=False)}
        self.started = False
        self.game_over = False
        self.phase = "lab"
        self.message = "自分と敵を配置して、技の効果をすぐ確認できます。"
        self.winner_text = ""
        self.board_size = 15
        self.viewport_size = 15
        self.actor_key = "speed_star"
        self.ally_keys = ["saint", "spiritualist"]
        self.enemy_key = "soldier"
        self.units: Dict[str, UnitState] = {}
        self.last_result_lines: List[str] = []
        self.last_replay_frames: List[dict] = []
        self.replay_token = 0
        self.lab_state: Dict[str, object] = {}
        self._build_units()

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

    def set_player_name(self, symbol: str, name: str) -> None:
        if symbol in self.players:
            self.players[symbol].name = (name or "Player A").strip()[:24] or "Player A"

    def update_connection(self, symbol: str, connected: bool) -> None:
        if symbol in self.players:
            self.players[symbol].connected = connected
            self.started = connected

    def apply_host_action(self, action: str, settings: Optional[dict] = None, **_: object) -> None:
        raise GameError("このお試し部屋ではホスト専用操作はありません。")

    def apply_player_action(
        self,
        symbol: str,
        action: str,
        cell: Optional[List[int]] = None,
        settings: Optional[dict] = None,
        **_: object,
    ) -> None:
        if symbol != "A":
            raise GameError("このお試し部屋は Player A だけが操作できます。")
        settings = settings or {}
        if action == "lab_select_actor":
            self._select_actor(str(settings.get("character_key") or ""))
            return
        if action == "lab_select_enemy":
            self._select_enemy(str(settings.get("character_key") or ""))
            return
        if action == "lab_select_ally":
            self._select_ally(str(settings.get("slot") or "ally_1"), str(settings.get("character_key") or ""))
            return
        if action == "lab_place_actor":
            self._place_unit("actor", self._parse_cell(settings.get("cell") or cell))
            return
        if action == "lab_place_enemy":
            self._place_unit("enemy", self._parse_cell(settings.get("cell") or cell))
            return
        if action == "lab_place_ally":
            self._place_unit(str(settings.get("slot") or "ally_1"), self._parse_cell(settings.get("cell") or cell))
            return
        if action == "lab_set_cost":
            self._set_unit_cost(str(settings.get("unit_id") or "actor"), int(settings.get("cost", 0)))
            return
        if action == "lab_set_hp":
            self._set_unit_hp(str(settings.get("unit_id") or "actor"), int(settings.get("hp", 0)))
            return
        if action == "lab_control_unit":
            self._set_active_unit(str(settings.get("unit_id") or "actor"))
            return
        if action == "lab_toggle_alternate":
            self.lab_state["alternate_mode"] = not bool(self.lab_state.get("alternate_mode"))
            self.message = f"交互手番モードを {'ON' if self.lab_state['alternate_mode'] else 'OFF'} にしました。"
            return
        if action == "lab_reset":
            self._build_units()
            self.message = "配置と状態を初期化しました。"
            return
        if action == "submit_turn":
            self._submit_turn(settings)
            return
        raise GameError("このお試し部屋では使えない操作です。")

    def to_public_dict(self, viewer_symbol: str = "") -> dict:
        controller = self._controller_unit()
        return {
            "game_type": self.game_type,
            "title": self.title,
            "started": self.started,
            "game_over": False,
            "phase": self.phase,
            "message": self.message,
            "winner_text": "",
            "field_type": "lab",
            "board_size": self.board_size,
            "viewport_size": self.viewport_size,
            "set_number": 1,
            "max_sets": 1,
            "round_number": 1,
            "rounds_per_set": 1,
            "coin_target": 0,
            "players": {symbol: player.to_public_dict() for symbol, player in self.players.items()},
            "catalog": [self._character_catalog_payload(character) for character in CHARACTERS.values()],
            "flags": [],
            "coins": [],
            "known_floor": [[x, y] for y in range(self.board_size) for x in range(self.board_size)],
            "known_walls": [],
            "known_lava": [],
            "known_coins": [],
            "visible_cells": [[x, y] for x, y in sorted(self._visible_cells())],
            "units": self._units_payload(),
            "viewer_symbol": "A",
            "viewer_actor_id": controller.id if controller else "actor",
            "enemy_actor_id": "enemy",
            "pending_actions": {"A": False, "B": False},
            "viewer_waiting": False,
            "result_ready": False,
            "continue_confirmed": {"A": False, "B": False},
            "viewer_continue_confirmed": False,
            "replay_token": self.replay_token,
            "replay_frames": self.last_replay_frames,
            "setup_note": "キャラ変更、敵変更、配置変更、コスト調整をしながら技を1つずつ検証します。",
            "lab_mode": True,
            "lab_actor_key": self.actor_key,
            "lab_ally_keys": list(self.ally_keys),
            "lab_enemy_key": self.enemy_key,
            "lab_result_lines": list(self.last_result_lines),
            "lab_state": dict(self.lab_state),
            "lab_alternate_mode": bool(self.lab_state.get("alternate_mode")),
            "lab_bird_snapshot": self.lab_state.get("bird_listening_snapshot"),
            "lab_enemy_targets": [
                {"id": unit.id, "name": unit.display_name}
                for unit in self.units.values()
                if unit.owner == "B" and unit.alive
            ],
            "lab_skill_notes": self._lab_skill_notes(),
        }

    def _build_units(self) -> None:
        actor_cell = self.units.get("actor").cell if "actor" in self.units else (4, 7)
        ally_1_cell = self.units.get("ally_1").cell if "ally_1" in self.units else (3, 10)
        ally_2_cell = self.units.get("ally_2").cell if "ally_2" in self.units else (3, 4)
        enemy_cell = self.units.get("enemy").cell if "enemy" in self.units else (10, 7)
        actor_cost = self.units.get("actor").cost if "actor" in self.units else 10
        ally_1_cost = self.units.get("ally_1").cost if "ally_1" in self.units else 0
        ally_2_cost = self.units.get("ally_2").cost if "ally_2" in self.units else 0
        self.units = {
            "actor": self._make_unit("actor", "A", self.actor_key, actor_cell, actor_cost),
            "ally_1": self._make_unit("ally_1", "A", self.ally_keys[0], ally_1_cell, ally_1_cost),
            "ally_2": self._make_unit("ally_2", "A", self.ally_keys[1], ally_2_cell, ally_2_cost),
            "enemy": self._make_unit("enemy", "B", self.enemy_key, enemy_cell, 0),
        }
        self.lab_state = {
            "active_unit": "actor",
            "shared_vision": False,
            "shared_vision_owner": "",
            "persistent_true_sight_units": [],
            "persistent_reflect_units": {},
            "enemy_bound_target": "",
            "enemy_last_seen": [enemy_cell[0], enemy_cell[1]],
            "archer_marked": False,
            "archer_mark_range": 10,
            "archer_mark_turns": 0,
            "samurai_sky": False,
            "samurai_guard": False,
            "saint_blessing": 0,
            "berserk_radius": 0,
            "alternate_mode": False,
            "debug_set": 1,
            "debug_turn": 1,
            "bird_listening_snapshot": None,
        }
        self.last_result_lines = []
        self.last_replay_frames = []
        self.replay_token += 1

    def _make_unit(self, unit_id: str, owner: str, key: str, cell: Cell, cost: int) -> UnitState:
        character = CHARACTERS[key]
        return UnitState(
            id=unit_id,
            owner=owner,
            character_key=key,
            display_name=character.name,
            move=character.move,
            base_power=character.power,
            base_vision=character.vision,
            cell=cell,
            spawn_cell=cell,
            hp=character.power,
            cost=cost,
            alive=True,
        )

    def _select_actor(self, key: str) -> None:
        if key not in CHARACTERS:
            raise GameError("存在しないキャラクターです。")
        cell = self.units["actor"].cell
        cost = self.units["actor"].cost
        self.actor_key = key
        self.units["actor"] = self._make_unit("actor", "A", key, cell, cost)
        self.lab_state["active_unit"] = "actor"
        self.last_result_lines = [f"自分キャラを {CHARACTERS[key].name} に変更しました。"]
        self.message = "自分キャラを変更しました。"

    def _select_enemy(self, key: str) -> None:
        if key not in CHARACTERS:
            raise GameError("存在しないキャラクターです。")
        cell = self.units["enemy"].cell
        self.enemy_key = key
        self.units["enemy"] = self._make_unit("enemy", "B", key, cell, 0)
        self.lab_state["enemy_last_seen"] = [cell[0], cell[1]]
        self.last_result_lines = [f"敵キャラを {CHARACTERS[key].name} に変更しました。"]
        self.message = "敵キャラを変更しました。"

    def _select_ally(self, slot: str, key: str) -> None:
        if slot not in {"ally_1", "ally_2"}:
            raise GameError("存在しない味方スロットです。")
        if key not in CHARACTERS:
            raise GameError("存在しないキャラクターです。")
        cell = self.units[slot].cell
        cost = self.units[slot].cost
        index = 0 if slot == "ally_1" else 1
        self.ally_keys[index] = key
        self.units[slot] = self._make_unit(slot, "A", key, cell, cost)
        self.last_result_lines = [f"{self._unit_label(slot)}を {CHARACTERS[key].name} に変更しました。"]
        self.message = "味方キャラを変更しました。"

    def _parse_cell(self, raw: object) -> Cell:
        if not isinstance(raw, list) or len(raw) != 2:
            raise GameError("配置マスが正しくありません。")
        cell = (int(raw[0]), int(raw[1]))
        if not self._in_bounds(cell):
            raise GameError("盤面外には配置できません。")
        return cell
    def _place_unit(self, which: str, cell: Cell) -> None:
        unit = self.units.get(which)
        if not unit:
            raise GameError("存在しない配置対象です。")
        unit.cell = cell
        unit.spawn_cell = cell
        unit.alive = True
        unit.hp = unit.max_hp
        if which == "enemy":
            self.lab_state["enemy_last_seen"] = [cell[0], cell[1]]
        label = self._unit_label(which)
        self.last_result_lines = [f"{label}を {cell[0] + 1},{cell[1] + 1} に配置しました。"]
        self.message = f"{label}を配置しました。"

    def _set_unit_cost(self, unit_id: str, cost: int) -> None:
        unit = self.units.get(unit_id)
        if not unit:
            raise GameError("存在しないユニットです。")
        unit.cost = max(0, min(99, cost))
        self.last_result_lines = [f"{self._unit_label(unit_id)}のコストを {unit.cost} に設定しました。"]
        self.message = "コストを変更しました。"

    def _set_unit_hp(self, unit_id: str, hp: int) -> None:
        unit = self.units.get(unit_id)
        if not unit:
            raise GameError("存在しないユニットです。")
        unit.hp = max(0, min(unit.max_hp, hp))
        unit.alive = unit.hp > 0
        self.last_result_lines = [f"{self._unit_label(unit_id)}のHPを {unit.hp} に設定しました。"]
        self.message = "HPを変更しました。"

    def _set_active_unit(self, unit_id: str) -> None:
        unit = self.units.get(unit_id)
        if not unit or not unit.alive:
            raise GameError("操作できないユニットです。")
        self.lab_state["active_unit"] = unit_id
        self.last_result_lines = [f"操作ユニットを {unit.display_name} に切り替えました。"]
        self.message = "操作ユニットを切り替えました。"

    def _controller_unit(self) -> Optional[UnitState]:
        unit_id = str(self.lab_state.get("active_unit") or "actor")
        unit = self.units.get(unit_id)
        if unit and unit.alive:
            return unit
        actor = self.units.get("actor")
        return actor if actor and actor.alive else None

    def _living_allies(self) -> List[UnitState]:
        return [unit for unit in self.units.values() if unit.owner == "A" and unit.alive]

    def _living_team_units(self, owner: str) -> List[UnitState]:
        return [unit for unit in self.units.values() if unit.owner == owner and unit.alive]

    def _living_team_units(self, owner: str) -> List[UnitState]:
        return [unit for unit in self.units.values() if unit.owner == owner and unit.alive]

    def _unit_label(self, unit_id: str) -> str:
        return {
            "actor": "自分",
            "ally_1": "味方1",
            "ally_2": "味方2",
            "enemy": "敵",
            "hamster": "ハムスター",
            "hundred_night": "ハンドレッド・ナイト",
        }.get(unit_id, unit_id)

    def _submit_turn(self, settings: dict) -> None:
        actor = self._controller_unit()
        enemy = self.units["enemy"]
        if not actor or not actor.alive:
            raise GameError("自分キャラが戦闘不能です。")

        self._reset_round_state()
        self._expire_start_of_turn_states(actor)
        self._process_lab_states(actor, enemy)

        tier = str(settings.get("skill_tier") or "")
        if actor.character_key not in CHARACTERS:
            tier = ""
        bound_target = str(self.lab_state.get("enemy_bound_target") or "")
        if bound_target and actor.id == bound_target:
            self.lab_state["enemy_bound_target"] = ""
            self.last_result_lines.append(f"ゴールド・バインド: {actor.display_name} は今回の行動を封じられました。")
            self.last_replay_frames = [self._snapshot_frame()]
            self.replay_token += 1
            self.message = "ゴールド・バインドにより行動不能でした。"
            return

        step_limit = self._planned_step_limit(actor, tier)
        path = self._normalize_move_plan(actor, settings.get("path") or [], step_limit)
        if actor.character_key == "speed_star" and tier == "large":
            direction = str(settings.get("skill_direction") or "")
            distance = int(settings.get("skill_distance") or 0)
            straight_path = self._build_straight_path(actor.cell, direction, distance)
            if straight_path:
                path = straight_path

        skill_used = False
        if tier in {"small", "medium", "large"}:
            skill_used = self._apply_skill(actor, enemy, tier, path, settings)

        frames = [self._snapshot_frame()]
        soldier_small_used = False
        leader_seen_targets: set[str] = set()
        for cell in path:
            previous = actor.cell
            actor.cell = cell
            if tier == "small" and actor.character_key == "soldier" and not soldier_small_used:
                targets = self._units_in_chebyshev(actor.cell, 1, source=actor)
                if targets:
                    self._deal_damage(targets[0], max(1, actor.max_hp // 3), "剣技", attacker=actor)
                    soldier_small_used = True
            if tier == "small" and actor.character_key == "leader":
                visible_enemies = [
                    unit
                    for unit in self._living_team_units("B" if actor.owner == "A" else "A")
                    if unit.cell in self._visible_cells_for(actor)
                ]
                new_targets = [unit for unit in visible_enemies if unit.id not in leader_seen_targets]
                for target in new_targets:
                    self._deal_damage(target, max(1, actor.max_hp // 5), "通常業務", attacker=actor)
                    leader_seen_targets.add(target.id)
            if tier == "medium" and actor.character_key == "speed_star":
                for target in self._units_at_cell(actor.cell, source=actor):
                    self._deal_damage(target, max(1, actor.max_hp // 5), "ブーストバスター", attacker=actor)
            if tier == "small" and actor.character_key == "archer":
                for target in self._visible_targets(actor):
                    self._deal_damage(target, 1, "通常射出追撃", attacker=actor)
            if tier == "small" and actor.character_key == "beastmaster":
                for target in self._units_at_cell(actor.cell, source=actor):
                    self._deal_damage(target, 4, "獅子ライド", attacker=actor)
            if tier == "large" and actor.character_key == "speed_star":
                for target in self._units_at_cell(actor.cell, source=actor):
                    self._deal_damage(target, target.hp, "ソニックスター直撃", attacker=actor)
                self._apply_speed_star_large_side_damage(actor, previous)
            if actor.id == "hamster":
                hit_targets = self._units_at_cell(actor.cell, source=actor)
                for target in hit_targets:
                    self._deal_damage(target, 1, "ハムスター体当たり", attacker=actor)
                if hit_targets:
                    frames.append(self._snapshot_frame())
                    break
            frames.append(self._snapshot_frame())

        self._advance_summons(enemy)
        if tier == "small" and actor.character_key == "soldier" and not soldier_small_used:
            targets = self._units_in_chebyshev(actor.cell, 1, source=actor)
            if targets:
                self._deal_damage(targets[0], max(1, actor.max_hp // 3), "剣技", attacker=actor)
                soldier_small_used = True
            elif skill_used:
                self.last_result_lines.append("剣技: 移動中を含めて八方向1マスに対象がいません。")
        if tier == "small" and actor.character_key == "leader":
            visible_enemies = [
                unit
                for unit in self._living_team_units("B" if actor.owner == "A" else "A")
                if unit.cell in self._visible_cells_for(actor)
            ]
            new_targets = [unit for unit in visible_enemies if unit.id not in leader_seen_targets]
            for target in new_targets:
                self._deal_damage(target, max(1, actor.max_hp // 5), "通常業務", attacker=actor)
                leader_seen_targets.add(target.id)
            if skill_used and not leader_seen_targets:
                self.last_result_lines.append("通常業務: この行動中に新しく見えた敵はいません。")

        if not path and not skill_used and not self.last_result_lines:
            self.last_result_lines.append("移動も技も指定されていないため待機扱いです。")
        if not self.last_result_lines:
            self.last_result_lines.append("この行動では追加効果は発生しませんでした。")
        self.last_replay_frames = frames
        self.replay_token += 1
        current_set = int(self.lab_state.get("debug_set") or 1)
        current_turn = int(self.lab_state.get("debug_turn") or 1) + 1
        if current_turn > 10:
            current_turn = 1
            current_set += 1
        self.lab_state["debug_set"] = current_set
        self.lab_state["debug_turn"] = current_turn
        if self.lab_state.get("alternate_mode"):
            if actor.id == "enemy" and self.units.get("actor") and self.units["actor"].alive:
                self.lab_state["active_unit"] = "actor"
            elif self.units.get("enemy") and self.units["enemy"].alive:
                self.lab_state["active_unit"] = "enemy"
        self.message = "お試し部屋の結果を更新しました。右側のログで確認してください。"

    def _reset_round_state(self) -> None:
        self.last_result_lines = []
        self.last_replay_frames = []
        for unit in self.units.values():
            unit.vision_bonus = 0
            unit.true_sight = False
            unit.reflect_ratio = 0.0

    def _expire_start_of_turn_states(self, actor: UnitState) -> None:
        reflect_units = dict(self.lab_state.get("persistent_reflect_units") or {})
        if actor.id in reflect_units:
            reflect_units.pop(actor.id, None)
        self.lab_state["persistent_reflect_units"] = reflect_units

    def _process_lab_states(self, actor: UnitState, enemy: UnitState) -> None:
        if actor.character_key == "archer" and int(self.lab_state.get("archer_mark_turns") or 0) > 0:
            for target in self._damageable_units(include_self=False, source=actor):
                if self._manhattan(actor.cell, target.cell) <= int(self.lab_state.get("archer_mark_range") or 10):
                    self._deal_damage(target, 2, "中距離曲射追撃", attacker=actor)
            self.lab_state["archer_mark_turns"] = 0
            self.lab_state["archer_marked"] = False
        if actor.character_key == "samurai" and self.lab_state.get("samurai_sky"):
            for target in self._visible_targets(actor):
                self._deal_damage(target, max(1, actor.max_hp // 2), "空の間合い", attacker=actor)
            self.lab_state["samurai_sky"] = False
        if actor.character_key == "samurai" and self.lab_state.get("samurai_guard"):
            for target in self._units_in_chebyshev(actor.cell, 1, source=actor):
                self._deal_damage(target, target.hp, "極の間合い", attacker=actor)
            self.lab_state["samurai_guard"] = False
        bound_target = str(self.lab_state.get("enemy_bound_target") or "")
        if bound_target:
            target = self.units.get(bound_target)
            if target and target.alive:
                self.last_result_lines.append(f"ゴールド・バインド: {target.display_name} の次回行動を封じています。")
            else:
                self.lab_state["enemy_bound_target"] = ""

    def _apply_skill(
        self, actor: UnitState, enemy: UnitState, tier: str, path: List[Cell], settings: Optional[dict] = None
    ) -> bool:
        character = CHARACTERS[actor.character_key]
        skill = getattr(character, tier)
        if actor.cost < skill.cost:
            self.last_result_lines.append(f"{skill.name}: コスト不足です。")
            return False
        actor.cost -= skill.cost
        if actor.character_key == "speed_star":
            return self._speed_star_skill(actor, enemy, tier)
        if actor.character_key == "spiritualist":
            return self._spiritualist_skill(actor, enemy, tier, settings or {})
        if actor.character_key == "archer":
            return self._archer_skill(actor, enemy, tier, settings or {})
        if actor.character_key == "soldier":
            return self._soldier_skill(actor, enemy, tier)
        if actor.character_key == "leader":
            return self._leader_skill(actor, enemy, tier, settings or {})
        if actor.character_key == "saint":
            return self._saint_skill(actor, enemy, tier)
        if actor.character_key == "psychic":
            return self._psychic_skill(actor, enemy, tier)
        if actor.character_key == "samurai":
            return self._samurai_skill(actor, enemy, tier)
        if actor.character_key == "berserker":
            return self._berserker_skill(actor, enemy, tier)
        if actor.character_key == "beastmaster":
            return self._beastmaster_skill(actor, enemy, tier, path)
        return False
    def _speed_star_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            self.last_result_lines.append("ダッシュ: 10マス移動として扱います。")
            return True
        if tier == "medium":
            self.last_result_lines.append("ブーストバスター: 10マス移動し、重なった敵へ戦闘力/5ダメージを与えます。")
            return True
        self.last_result_lines.append("ソニックスター: 方向と距離を指定して直線移動します。")
        return True

    def _spiritualist_skill(self, actor: UnitState, enemy: UnitState, tier: str, settings: dict) -> bool:
        if tier == "small":
            self.lab_state["shared_vision"] = True
            self.last_result_lines.append("サウザンド・アイ: このセット中、味方全員で視界共有します。")
            return True
        if tier == "medium":
            target_id = str(settings.get("skill_target_unit_id") or "")
            target = self.units.get(target_id)
            if not target or not target.alive or target.owner != "B":
                actor.cost += CHARACTERS[actor.character_key].medium.cost
                self.last_result_lines.append("ゴールド・バインド: 対象の敵を選んでください。")
                return False
            self.lab_state["enemy_bound_target"] = target.id
            self.last_result_lines.append(f"ゴールド・バインド: {target.display_name} が次に動く時の行動を封じました。")
            return True
        self.units["hundred_night"] = UnitState(
            id="hundred_night",
            owner="A",
            character_key="hundred_night",
            display_name="ハンドレッド・ナイト",
            move=2,
            base_power=9999,
            base_vision=99,
            cell=actor.cell,
            spawn_cell=actor.cell,
            hp=9999,
            cost=0,
            alive=True,
            is_summon=True,
        )
        self.last_result_lines.append("ハンドレッド・ナイト: 幽霊ユニットを召喚しました。")
        return True

    def _archer_skill(self, actor: UnitState, enemy: UnitState, tier: str, settings: Optional[dict] = None) -> bool:
        if tier == "small":
            targets = self._visible_targets(actor)
            if targets:
                for target in targets:
                    self._deal_damage(target, 1, "通常射出", attacker=actor)
            else:
                self.last_result_lines.append("通常射出: 見えている対象がいません。")
            return True
        if tier == "medium":
            marked = bool(self._visible_targets(actor))
            self.lab_state["archer_marked"] = marked
            self.lab_state["archer_mark_range"] = 10
            self.lab_state["archer_mark_turns"] = 1 if marked else 0
            if marked:
                self.last_result_lines.append("中距離曲射: 捕捉状態を記録しました。次の自分手番開始時に10マス以内なら2ダメージです。")
            else:
                self.last_result_lines.append("中距離曲射: 捕捉できる対象がいません。")
            return True
        target_cell = settings.get("skill_target_cell") if settings else None
        targets = self._units_in_target_line(actor, target_cell)
        if targets:
            self._deal_damage(targets[0], targets[0].hp, "超遠距離攻撃", attacker=actor)
        else:
            self.last_result_lines.append("超遠距離攻撃: 狙った直線上に対象がいません。")
        return True

    def _soldier_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            return True
        if tier == "medium":
            targets = [
                unit
                for unit in self._living_team_units(actor.owner)
                if unit.id != actor.id and unit.cell in self._visible_cells_for(actor)
            ]
            healed_count = 0
            for unit in targets:
                if unit.hp < unit.max_hp:
                    unit.hp = min(unit.max_hp, unit.hp + 1)
                    healed_count += 1
            if healed_count:
                self.last_result_lines.append(f"弱者の祈り: 視界に入っている味方 {healed_count} 体の戦闘力を 1 回復しました。")
            else:
                self.last_result_lines.append("弱者の祈り: 視界内に回復対象の味方がいません。")
            return True
        if actor.hp <= 5:
            actor.hp = 30
            actor.move = 15
            self.last_result_lines.append("主人公補正: 現在戦闘力30、移動15にしました。")
        else:
            self.last_result_lines.append("主人公補正: 現在戦闘力が5以下ではないため不発です。")
        return True

    def _leader_skill(self, actor: UnitState, enemy: UnitState, tier: str, settings: dict) -> bool:
        if tier == "small":
            return True
        if tier == "medium":
            draft = settings.get("leader_reconfigure") or {}
            if isinstance(draft, dict) and draft:
                ordered = []
                for turn_key in sorted(draft.keys(), key=lambda value: int(str(value)) if str(value).isdigit() else 999):
                    unit_id = str(draft.get(turn_key) or "")
                    unit = self.units.get(unit_id)
                    if unit and unit.alive and unit.owner == actor.owner:
                        ordered.append(f"{turn_key}ターン目: {unit.display_name}")
                if ordered:
                    self.last_result_lines.append("再構成: " + " / ".join(ordered))
                else:
                    self.last_result_lines.append("再構成: 残りターンの担当を選んでください。")
            else:
                self.last_result_lines.append("再構成: 残りターンの担当をターンごとに選べます。")
            return True
        mapping = settings.get("leader_redeploy") or {}
        allies = [unit for unit in self._living_team_units(actor.owner)]
        snapshot = {unit.id: unit.cell for unit in allies}
        moved = []
        if isinstance(mapping, dict):
            for unit in allies:
                target_id = str(mapping.get(unit.id) or "")
                if target_id in snapshot:
                    unit.cell = snapshot[target_id]
                    moved.append(f"{unit.display_name}→{self.units[target_id].display_name}位置")
        if moved:
            self.last_result_lines.append("再配置: " + " / ".join(moved))
        else:
            self.last_result_lines.append("再配置: 味方ごとの移動先を選んでください。")
        return True

    def _saint_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            actor.reflect_ratio = 1.0
            reflect_units = dict(self.lab_state.get("persistent_reflect_units") or {})
            reflect_units[actor.id] = 1.0
            self.lab_state["persistent_reflect_units"] = reflect_units
            self.last_result_lines.append("リフレクト: 次の自分の番まで完全反射状態を付けました。アリア自身はダメージを受けません。")
            return True
        if tier == "medium":
            allies = self._living_allies()
            wounded = [unit for unit in allies if unit.hp < unit.max_hp]
            if not wounded:
                self.last_result_lines.append("聖女の祈り: 戦闘力が減っている味方がいないため不発でした。")
                return True
            target = random.choice(wounded)
            healed = min(3, target.max_hp - target.hp)
            target.hp = min(target.max_hp, target.hp + 3)
            self.lab_state["saint_blessing"] = 3
            self.last_result_lines.append(f"聖女の祈り: {target.display_name} の戦闘力を {healed} 回復しました。現在 {target.hp}。")
            return True
        actor.true_sight = True
        true_sight_units = set(self.lab_state.get("persistent_true_sight_units") or [])
        true_sight_units.add(actor.id)
        self.lab_state["persistent_true_sight_units"] = sorted(true_sight_units)
        self.last_result_lines.append("見通す目: このセット中、アリアは視野とマップ情報を全開放します。")
        return True

    def _psychic_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            for target in self._units_in_radius(actor.cell, 5, source=actor, include_self=False):
                self._deal_damage(target, 3, "フラッシュ", attacker=actor)
            self._deal_damage(actor, 1, "フラッシュ反動", attacker=None)
            self.last_result_lines.append("フラッシュ: 半径5マス以内の相手へ 3 ダメージ、自分は 1 ダメージを受けました。")
            return True
        if tier == "medium":
            while True:
                cell = (random.randrange(self.board_size), random.randrange(self.board_size))
                if cell != enemy.cell:
                    actor.cell = cell
                    break
            self.last_result_lines.append(f"テレポート: {actor.cell[0] + 1},{actor.cell[1] + 1} へ移動しました。")
            return True
        hit_any = False
        for target in self._damageable_units(include_self=False, source=actor):
            distance = self._euclidean_distance(actor.cell, target.cell)
            if distance <= 10:
                amount = 5
            elif distance <= 20:
                amount = 3
            else:
                amount = 1
            self._deal_damage(target, amount, "ブラックホール", attacker=actor)
            hit_any = True
        if not hit_any:
            self.last_result_lines.append("ブラックホール: 範囲内の対象がいません。")
        return True

    def _samurai_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            targets = self._units_in_chebyshev(actor.cell, 3, source=actor)
            if targets:
                for target in targets:
                    self._deal_damage(target, max(1, actor.max_hp // 3), "間合い", attacker=actor)
            else:
                self.last_result_lines.append("間合い: 3マス圏に対象がいません。")
            return True
        if tier == "medium":
            self.lab_state["samurai_sky"] = True
            self.last_result_lines.append("空の間合い: 次の自分の番まで反応斬り状態に入りました。")
            return True
        self.lab_state["samurai_guard"] = True
        self.last_result_lines.append("極の間合い: 次の自分の番まで迎撃状態に入りました。")
        return True

    def _berserker_skill(self, actor: UnitState, enemy: UnitState, tier: str) -> bool:
        if tier == "small":
            radius = int(self.lab_state.get("berserk_radius") or 0)
            targets = self._units_in_chebyshev(actor.cell, radius, source=actor)
            if targets:
                for target in targets:
                    self._deal_damage(target, actor.max_hp, "ホショク", attacker=actor)
            else:
                self.last_result_lines.append(f"ホショク: 現在の捕食半径 {radius} では対象に届きません。")
            return True
        if tier == "medium":
            actor.hp = max(1, actor.hp - 5)
            self.last_result_lines.append(f"シュンソク: HPを5消費し、この検証では移動量を倍として扱います。現在 {actor.hp}。")
            return True
        actor.hp = max(1, actor.hp // 2)
        self.lab_state["berserk_radius"] = int(self.lab_state.get("berserk_radius") or 0) + 1
        self.last_result_lines.append(f"バーサーク: 攻撃半径を {self.lab_state['berserk_radius']} に拡張しました。現在 {actor.hp}。")
        return True

    def _beastmaster_skill(self, actor: UnitState, enemy: UnitState, tier: str, path: List[Cell]) -> bool:
        if tier == "small":
            self.last_result_lines.append("獅子ライド: 10マス移動し、移動した先で重なった相手へ4ダメージを与えます。")
            return True
        if tier == "medium":
            debug_set = int(self.lab_state.get("debug_set") or 1)
            debug_turn = int(self.lab_state.get("debug_turn") or 1)
            snapshot = {
                "cell": [enemy.cell[0], enemy.cell[1]],
                "label": f"{debug_set}セット目 {debug_turn}ターン時点",
            }
            self.lab_state["bird_listening_snapshot"] = snapshot
            self.lab_state["enemy_last_seen"] = [enemy.cell[0], enemy.cell[1]]
            self.last_result_lines.append(
                f"バードリスニング: {snapshot['label']} の敵位置 {enemy.cell[0] + 1},{enemy.cell[1] + 1} を記録しました。"
            )
            return True
        hamster_cell = path[-1] if path else actor.cell
        self.units["hamster"] = UnitState(
            id="hamster",
            owner="A",
            character_key="hamster",
            display_name="ハムスター",
            move=20,
            base_power=1,
            base_vision=2,
            cell=hamster_cell,
            spawn_cell=hamster_cell,
            hp=1,
            cost=0,
            alive=True,
            is_summon=True,
        )
        self.lab_state["active_unit"] = "hamster"
        self.last_result_lines.append(f"ハムマッチ: ハムスターを {hamster_cell[0] + 1},{hamster_cell[1] + 1} に召喚しました。")
        return True
    def _apply_speed_star_large_side_damage(self, actor: UnitState, previous: Cell) -> None:
        dx = actor.cell[0] - previous[0]
        dy = actor.cell[1] - previous[1]
        if dx == 0 and dy == 0:
            return
        side_vectors = [(0, 1), (0, -1)] if dx else [(1, 0), (-1, 0)]
        for sx, sy in side_vectors:
            for distance in (1, 2):
                side_cell = (actor.cell[0] + sx * distance, actor.cell[1] + sy * distance)
                for target in self._units_at_cell(side_cell, source=actor):
                    self._deal_damage(target, max(1, actor.max_hp // 2), "ソニックスター横ダメージ", attacker=actor)

    def _advance_summons(self, enemy: UnitState) -> None:
        ghost = self.units.get("hundred_night")
        if ghost and ghost.alive:
            targets = [unit for unit in self._damageable_units(include_self=False, source=ghost) if unit.owner != ghost.owner]
            if targets:
                target = min(targets, key=lambda unit: self._manhattan(ghost.cell, unit.cell))
                for _ in range(2):
                    next_cell = self._step_toward(ghost.cell, target.cell)
                    if next_cell == ghost.cell:
                        break
                    ghost.cell = next_cell
                    if ghost.cell == target.cell:
                        self._deal_damage(target, 100, "ハンドレッド・ナイト", attacker=ghost)
                        break

    def _step_toward(self, origin: Cell, target: Cell) -> Cell:
        candidates: List[Cell] = []
        ox, oy = origin
        tx, ty = target
        if ox < tx:
            candidates.append((ox + 1, oy))
        elif ox > tx:
            candidates.append((ox - 1, oy))
        if oy < ty:
            candidates.append((ox, oy + 1))
        elif oy > ty:
            candidates.append((ox, oy - 1))
        if not candidates:
            return origin
        return min(candidates, key=lambda cell: self._manhattan(cell, target))

    def _deal_damage(self, target: UnitState, amount: int, label: str, attacker: Optional[UnitState] = None) -> None:
        if not target.alive:
            return
        if label == "超遠距離攻撃" and target.character_key == "samurai" and self.lab_state.get("samurai_guard"):
            self.last_result_lines.append("超遠距離攻撃: 極の間合いに弾かれて侍には届きませんでした。")
            return
        reflect_ratio = self._reflect_ratio_for(target)
        if amount > 0 and reflect_ratio > 0 and attacker and attacker.alive and attacker.id != target.id:
            reflected = max(1, math.ceil(amount * reflect_ratio))
            before_reflect = attacker.hp
            attacker.hp = max(0, attacker.hp - reflected)
            actual_reflect = before_reflect - attacker.hp
            self.last_result_lines.append(
                f"{label}: {target.display_name} は完全反射しました。{attacker.display_name} に {actual_reflect} ダメージを返しました。残り {attacker.hp}。"
            )
            if attacker.hp <= 0:
                attacker.alive = False
                self.last_result_lines.append(f"{attacker.display_name} は戦闘不能になりました。")
            return
        before = target.hp
        target.hp = max(0, target.hp - max(0, amount))
        actual = before - target.hp
        self.last_result_lines.append(f"{label}: {target.display_name} に {actual} ダメージ。残り {target.hp}。")
        if target.hp <= 0:
            target.alive = False
            self.last_result_lines.append(f"{target.display_name} は戦闘不能になりました。")

    def _reflect_ratio_for(self, unit: UnitState) -> float:
        reflect_units = dict(self.lab_state.get("persistent_reflect_units") or {})
        if unit.id in reflect_units:
            return float(reflect_units[unit.id] or 0.0)
        return unit.reflect_ratio

    def _has_full_vision(self, unit: UnitState) -> bool:
        return unit.true_sight or unit.id in set(self.lab_state.get("persistent_true_sight_units") or [])

    def _enemy_visible(self, actor: UnitState, enemy: UnitState) -> bool:
        if self._has_full_vision(actor):
            return True
        return enemy.cell in self._visible_cells_for(actor)

    def _visible_targets(self, actor: UnitState) -> List[UnitState]:
        visible_cells = self._visible_cells_for(actor)
        return [
            unit
            for unit in self._damageable_units(include_self=False, source=actor)
            if unit.cell in visible_cells
        ]

    def _chebyshev(self, a: Cell, b: Cell) -> int:
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    def _euclidean_distance(self, a: Cell, b: Cell) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx * dx + dy * dy) ** 0.5

    def _damageable_units(self, include_self: bool = False, source: Optional[UnitState] = None) -> List[UnitState]:
        units: List[UnitState] = []
        for unit in self.units.values():
            if not unit.alive:
                continue
            if unit.is_summon:
                continue
            if not include_self and source is not None and unit.id == source.id:
                continue
            units.append(unit)
        return units

    def _units_in_radius(self, origin: Cell, radius: int, source: Optional[UnitState] = None, include_self: bool = False) -> List[UnitState]:
        return [
            unit
            for unit in self._damageable_units(include_self=include_self, source=source)
            if self._euclidean_distance(origin, unit.cell) <= radius
        ]

    def _units_at_cell(self, cell: Cell, source: Optional[UnitState] = None, include_self: bool = False) -> List[UnitState]:
        return [
            unit
            for unit in self._damageable_units(include_self=include_self, source=source)
            if unit.cell == cell
        ]

    def _units_in_chebyshev(self, origin: Cell, radius: int, source: Optional[UnitState] = None, include_self: bool = False) -> List[UnitState]:
        return [
            unit
            for unit in self._damageable_units(include_self=include_self, source=source)
            if self._chebyshev(origin, unit.cell) <= radius
        ]

    def _units_in_straight_line(self, actor: UnitState, source: Optional[UnitState] = None) -> List[UnitState]:
        targets = [
            unit
            for unit in self._damageable_units(include_self=False, source=source or actor)
            if self._is_straight_line(actor.cell, unit.cell)
        ]
        targets.sort(key=lambda unit: self._manhattan(actor.cell, unit.cell))
        return targets

    def _units_in_target_line(self, actor: UnitState, raw_target_cell: object) -> List[UnitState]:
        if not isinstance(raw_target_cell, list) or len(raw_target_cell) != 2:
            return []
        target_cell = (int(raw_target_cell[0]), int(raw_target_cell[1]))
        if not self._in_bounds(target_cell) or target_cell == actor.cell:
            return []
        line_cells = self._build_line_to_target(actor.cell, target_cell)
        if not line_cells:
            return []
        line_set = set(line_cells)
        targets = [
            unit
            for unit in self._damageable_units(include_self=False, source=actor)
            if unit.cell in line_set
        ]
        targets.sort(key=lambda unit: line_cells.index(unit.cell))
        return targets

    def _is_straight_line(self, a: Cell, b: Cell) -> bool:
        return a[0] == b[0] or a[1] == b[1]

    def _planned_step_limit(self, actor: UnitState, skill_tier: str) -> int:
        if skill_tier == "small" and actor.character_key in {"speed_star", "beastmaster"}:
            return 10
        if skill_tier == "medium" and actor.character_key == "speed_star":
            return 10
        if skill_tier == "medium" and actor.character_key == "berserker":
            return actor.effective_move * 2
        if skill_tier == "large" and actor.character_key == "speed_star":
            return self.board_size
        return actor.effective_move

    def _direction_delta(self, direction: str) -> Optional[Cell]:
        return {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.get(direction)

    def _build_straight_path(self, origin: Cell, direction: str, distance: int) -> List[Cell]:
        delta = self._direction_delta(direction)
        if not delta or distance <= 0:
            return []
        path: List[Cell] = []
        x, y = origin
        for _ in range(min(distance, self.board_size)):
            x += delta[0]
            y += delta[1]
            cell = (x, y)
            if not self._in_bounds(cell):
                break
            path.append(cell)
        return path

    def _build_line_to_target(self, origin: Cell, target: Cell) -> List[Cell]:
        x0, y0 = origin
        x1, y1 = target
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        cells: List[Cell] = []
        passed_target = False
        while True:
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
            if not self._in_bounds((x0, y0)):
                break
            cells.append((x0, y0))
            if (x0, y0) == (x1, y1):
                passed_target = True
            if passed_target:
                next_x = x0 + sx
                next_y = y0 + sy
                if not self._in_bounds((next_x, next_y)):
                    break
        return cells

    def _normalize_move_plan(self, actor: UnitState, raw_path: object, step_limit: int) -> List[Cell]:
        if not isinstance(raw_path, list):
            return []
        plan: List[Cell] = []
        previous = actor.cell
        for item in raw_path[:step_limit]:
            if not isinstance(item, list) or len(item) != 2:
                continue
            cell = (int(item[0]), int(item[1]))
            if not self._in_bounds(cell):
                continue
            if self._manhattan(previous, cell) != 1:
                break
            plan.append(cell)
            previous = cell
        return plan

    def _snapshot_frame(self) -> dict:
        return {"units": self._units_payload(), "visible_cells": [[x, y] for x, y in sorted(self._visible_cells())]}

    def _units_payload(self) -> dict:
        payload = {}
        for unit_id, unit in self.units.items():
            character = CHARACTERS.get(unit.character_key)
            payload[unit_id] = {
                "id": unit.id,
                "owner": unit.owner,
                "character_key": unit.character_key,
                "name": unit.display_name,
                "cell": [unit.cell[0], unit.cell[1]],
                "alive": unit.alive,
                "hp": unit.hp,
                "max_hp": unit.max_hp,
                "cost": unit.cost,
                "move": unit.effective_move,
                "vision": unit.effective_vision,
                "small": self._skill_payload(character.small) if character else None,
                "medium": self._skill_payload(character.medium) if character else None,
                "large": self._skill_payload(character.large) if character else None,
            }
        return payload

    def _lab_skill_notes(self) -> dict:
        controller = self._controller_unit() or self.units["actor"]
        if controller.character_key not in CHARACTERS:
            return {}
        character = CHARACTERS[controller.character_key]
        return {
            "small": self._skill_note_payload(controller.character_key, "small", character.small),
            "medium": self._skill_note_payload(controller.character_key, "medium", character.medium),
            "large": self._skill_note_payload(controller.character_key, "large", character.large),
        }

    def _skill_note_payload(self, character_key: str, tier: str, skill) -> dict:
        return {
            "name": skill.name,
            "cost": skill.cost,
            "description": skill.description,
            "move_type": self._move_type_note(character_key, tier),
            "attack_power": self._attack_power_note(character_key, tier),
            "effect": self._effect_note(character_key, tier),
            "range": self._range_note(character_key, tier),
            "diagram_note": self._diagram_note(character_key, tier),
            "implementation": self._implementation_note(character_key, tier),
        }
    def _move_type_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "技そのものが移動になる",
            ("speed_star", "medium"): "技そのものが移動になる",
            ("speed_star", "large"): "技そのものが移動になる",
            ("spiritualist", "small"): "通常移動しながら使える",
            ("spiritualist", "medium"): "移動不可",
            ("spiritualist", "large"): "移動不可",
            ("archer", "small"): "通常移動しながら使える",
            ("archer", "medium"): "移動不可",
            ("archer", "large"): "移動不可",
            ("soldier", "small"): "通常移動しながら使える",
            ("soldier", "medium"): "移動不可",
            ("soldier", "large"): "移動不可",
            ("leader", "small"): "通常移動しながら使える",
            ("leader", "medium"): "移動不可",
            ("leader", "large"): "移動不可",
            ("saint", "small"): "通常移動しながら使える",
            ("saint", "medium"): "移動不可",
            ("saint", "large"): "通常移動しながら使える",
            ("psychic", "small"): "移動不可",
            ("psychic", "medium"): "技そのものが移動になる",
            ("psychic", "large"): "移動不可",
            ("samurai", "small"): "移動不可",
            ("samurai", "medium"): "移動不可",
            ("samurai", "large"): "移動不可",
            ("berserker", "small"): "通常移動しながら使える",
            ("berserker", "medium"): "通常移動しながら使える",
            ("berserker", "large"): "通常移動しながら使える",
            ("beastmaster", "small"): "技そのものが移動になる",
            ("beastmaster", "medium"): "移動不可",
            ("beastmaster", "large"): "移動不可",
        }
        return notes.get((character_key, tier), "未整理")

    def _attack_power_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "なし",
            ("speed_star", "medium"): "戦闘力/5",
            ("speed_star", "large"): "直撃は撃破、横1-2マスは戦闘力/2",
            ("spiritualist", "small"): "なし",
            ("spiritualist", "medium"): "なし",
            ("spiritualist", "large"): "100",
            ("archer", "small"): "1を移動ごと",
            ("archer", "medium"): "2を対象移動ごと",
            ("archer", "large"): "基本必殺",
            ("soldier", "small"): "戦闘力/3",
            ("soldier", "medium"): "味方全員を1回復",
            ("soldier", "large"): "現在戦闘力30に変更",
            ("leader", "small"): "戦闘力/5",
            ("leader", "medium"): "なし",
            ("leader", "large"): "なし",
            ("saint", "small"): "受けたダメージを完全反射",
            ("saint", "medium"): "+3",
            ("saint", "large"): "なし",
            ("psychic", "small"): "相手へ3 / 自分へ1",
            ("psychic", "medium"): "なし",
            ("psychic", "large"): "10マス以内5 / 20マス以内3 / それ以外1",
            ("samurai", "small"): "戦闘力/3",
            ("samurai", "medium"): "戦闘力/2",
            ("samurai", "large"): "侵入対象を撃破",
            ("berserker", "small"): "戦闘力ぶん",
            ("berserker", "medium"): "なし",
            ("berserker", "large"): "半径拡張",
            ("beastmaster", "small"): "4",
            ("beastmaster", "medium"): "なし",
            ("beastmaster", "large"): "ハムスター1",
        }
        return notes.get((character_key, tier), "未整理")

    def _effect_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "10マスまで移動する。",
            ("speed_star", "medium"): "10マスまで移動し、移動中に敵と重なるたびに戦闘力/5ダメージを与える。",
            ("speed_star", "large"): "方向と距離を決めて一直線に突進し、直線上を撃破しながら進む。",
            ("spiritualist", "small"): "このセット中、味方の見えている範囲を共有する。",
            ("spiritualist", "medium"): "指定した敵が次に自分で動く時の行動を封じる。",
            ("spiritualist", "large"): "ハンドレッド・ナイトを投下して最寄りの敵へ追尾させる。",
            ("archer", "small"): "移動中に視界へ入った敵へ、残り移動ごとに1ダメージを与える。",
            ("archer", "medium"): "捕捉した敵が次の自分の番まで10マス以内で動くたび2ダメージを与える。",
            ("archer", "large"): "狙点を選び、その点を通って盤面端まで伸びる直線上で最も近い相手に基本必殺ダメージを与える。",
            ("soldier", "small"): "移動中を含め、八方向1マスに入った最初の相手1体だけを斬る。",
            ("soldier", "medium"): "視界に入っている味方全員の戦闘力を1回復する。",
            ("soldier", "large"): "瀕死なら主人公補正で強化される。",
            ("leader", "small"): "視界内に新しく入った敵だけをその都度撃つ。同じ敵はそのターン中に1回しか撃たない。",
            ("leader", "medium"): "残りターンの担当キャラをターンごとに組み直す。",
            ("leader", "large"): "味方が今いる位置を基準に、誰をどこへ寄せるか決めて再配置する。",
            ("saint", "small"): "次の自分の番まで反射状態になる。",
            ("saint", "medium"): "味方1体をランダムに選び戦闘力を3上げる。",
            ("saint", "large"): "このセット中、敵とコインの位置を全て把握する。",
            ("psychic", "small"): "自分中心の半径5マス以内の相手へ3ダメージを与え、自分は1ダメージを受ける。",
            ("psychic", "medium"): "ランダムな空きマスへテレポートする。",
            ("psychic", "large"): "自分以外へ、10マス以内5ダメージ、20マス以内3ダメージ、それ以外1ダメージを与える。",
            ("samurai", "small"): "3マス圏の敵へ斬撃を飛ばす。",
            ("samurai", "medium"): "次の自分の番まで、視界に入った敵へ自動斬撃を飛ばす。",
            ("samurai", "large"): "次の自分の番まで迎撃態勢に入り、接近したほぼ全てを弾く。",
            ("berserker", "small"): "捕食半径内の敵へ大ダメージを与える。",
            ("berserker", "medium"): "HP5を消費して移動量を倍にする。",
            ("berserker", "large"): "HP半減と引き換えに攻撃半径を累積で広げる。",
            ("beastmaster", "small"): "10マスまで移動し、移動先で重なった相手へ4ダメージを与える。",
            ("beastmaster", "medium"): "その時点の敵位置を聞き出し、そのセット中はマップへ記録する。",
            ("beastmaster", "large"): "ハムスターを召喚し、以後は本体かハムスターを選んで動かせる。",
        }
        return notes.get((character_key, tier), "未整理")

    def _range_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "進行先10マス",
            ("speed_star", "medium"): "進行線そのもの",
            ("speed_star", "large"): "進行線 + 各歩の左右1-2マス",
            ("spiritualist", "small"): "味方全員の視界",
            ("spiritualist", "medium"): "敵一覧から1体指定",
            ("spiritualist", "large"): "最寄り敵へ追尾する召喚物",
            ("archer", "small"): "自分の視界内",
            ("archer", "medium"): "捕捉済みの敵 / 自分から10マス以内",
            ("archer", "large"): "狙点を通って盤面端まで伸びる直線",
            ("soldier", "small"): "移動中を含む八方向1マス、ただし最初の1回だけ",
            ("soldier", "medium"): "視界内の味方全員",
            ("soldier", "large"): "自分自身",
            ("leader", "small"): "自分の視界内で新しく見えた敵",
            ("leader", "medium"): "2ターン目以降の残りターン枠",
            ("leader", "large"): "現在の味方位置一覧",
            ("saint", "small"): "自分自身へ張る完全反射",
            ("saint", "medium"): "味方ランダム1体",
            ("saint", "large"): "マップ全域（このセット中）",
            ("psychic", "small"): "自分中心の円形5マス（相手へ3 / 自分へ1）",
            ("psychic", "medium"): "空きマス全域",
            ("psychic", "large"): "自分以外の全ユニット",
            ("samurai", "small"): "円形3マス圏",
            ("samurai", "medium"): "自分の視界内",
            ("samurai", "large"): "自分周囲1マスの侵入判定",
            ("berserker", "small"): "現在の捕食半径内",
            ("berserker", "medium"): "自分自身",
            ("berserker", "large"): "自分自身",
            ("beastmaster", "small"): "移動した先で重なったマス",
            ("beastmaster", "medium"): "その時点の敵位置1点（記録表示）",
            ("beastmaster", "large"): "召喚位置1点",
        }
        return notes.get((character_key, tier), "未整理")

    def _diagram_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "自分から伸びる移動線だけを見ます。",
            ("speed_star", "medium"): "移動線と敵が重なった瞬間が当たり判定です。停止地点だけではありません。",
            ("speed_star", "large"): "中央の進行線が直撃範囲で、左右1マスと2マスが横ダメージ範囲です。",
            ("spiritualist", "small"): "味方が見ているマスをまとめて表示するイメージです。",
            ("spiritualist", "medium"): "敵一覧から選んだ1体に次回行動封じの印が付くイメージです。",
            ("spiritualist", "large"): "幽霊が2歩ずつ最短で敵へ近づく線を見ます。",
            ("archer", "small"): "移動線の途中で敵が視界に入ったら、残り歩数ぶん矢が飛びます。",
            ("archer", "medium"): "一度捕捉した敵に印が付き、次の自分の番まで移動のたびに追撃します。",
            ("archer", "large"): "アチャ爺から狙点を通過して、その先の盤面端まで伸ばした直線上で、一番手前の相手に当たるイメージです。",
            ("soldier", "small"): "移動しながら周囲8マスを見て、最初に入った1体だけを斬るイメージです。",
            ("soldier", "medium"): "今見えている味方全員に1ずつ回復が入るイメージです。サウザンド・アイ中は共有視界内の味方も含みます。",
            ("soldier", "large"): "瀕死条件を満たした瞬間に自己強化が乗ります。",
            ("leader", "small"): "移動しながら新しく視界へ入った敵にだけ銃弾が飛ぶイメージです。",
            ("leader", "medium"): "残りターンの枠を上から順に誰が担当するか埋め直す表を使うイメージです。",
            ("leader", "large"): "味方名と味方位置名を対応付ける表を使うイメージです。",
            ("saint", "small"): "自分を中心に完全反射の膜が張られるイメージです。アリア本人はダメージを受けません。",
            ("saint", "medium"): "味方一覧からランダムに1人が光るイメージです。",
            ("saint", "large"): "このセット中、アリアを操作している間はマップ全体に敵とコインが浮かぶイメージです。",
            ("psychic", "small"): "白星夢を中心に半径5マスへ衝撃波が広がり、周囲には3ダメージ、自分には反動1ダメージが入るイメージです。",
            ("psychic", "medium"): "空きマスへ瞬間移動するだけで壁内には入りません。",
            ("psychic", "large"): "白星夢から広がる重力波で、近いほど強く遠いほど弱いイメージです。本人は対象外です。",
            ("samurai", "small"): "自分中心の円形3マスへ斬撃が届きます。",
            ("samurai", "medium"): "待機中に視界へ入った敵へ自動で線が飛びます。",
            ("samurai", "large"): "自分周囲に迎撃結界があり、侵入したものを弾くイメージです。",
            ("berserker", "small"): "現在の捕食半径内に入った敵を噛み砕くイメージです。",
            ("berserker", "medium"): "移動線が通常の2倍になるだけです。",
            ("berserker", "large"): "自分中心の攻撃円が使うたび1段広がります。",
            ("beastmaster", "small"): "移動した先のマスで相手と重なった瞬間にダメージが入るイメージです。",
            ("beastmaster", "medium"): "その時点の敵位置を聞き出し、別色の記録点としてマップに残すイメージです。",
            ("beastmaster", "large"): "本体とは別にハムスター駒が増え、ハムスター移動ボタンで切り替えるイメージです。",
        }
        return notes.get((character_key, tier), "未整理")

    def _implementation_note(self, character_key: str, tier: str) -> str:
        notes = {
            ("speed_star", "small"): "実装済み。移動上限を10に拡張します。",
            ("speed_star", "medium"): "実装済み。10マス移動し、重なった瞬間ごとに戦闘力/5ダメージを与えます。",
            ("speed_star", "large"): "実装済み。方向と距離で直線移動し、直撃撃破と左右1-2マスへの戦闘力/2ダメージを行います。",
            ("spiritualist", "small"): "実装済み。ラボではこのターン中の共有視界として扱います。",
            ("spiritualist", "medium"): "実装済み。敵一覧から選んだ対象の次回行動を実際に封じます。",
            ("spiritualist", "large"): "実装済み。ハンドレッド・ナイト召喚と追尾を行います。",
            ("archer", "small"): "実装済み。移動中に見えた敵へ残り歩数ぶん1ダメージ追撃します。",
            ("archer", "medium"): "実装済み。捕捉後、次の自分の番開始時に10マス以内なら2ダメージを与える近似です。",
            ("archer", "large"): "実装済み。狙点を通って盤面端まで伸びる直線上の一番近い相手に当たります。リフレクトは反射し、極の間合い中の侍には効きません。",
            ("soldier", "small"): "実装済み。移動中を含めて八方向1マスへ入り込んだ最初の1体にだけ戦闘力/3ダメージです。",
            ("soldier", "medium"): "実装済み。視界内の味方全員を1回復します。自分は対象外で、上限以上には回復しません。",
            ("soldier", "large"): "実装済み。HP5以下なら現在戦闘力30、移動15へ変更します。",
            ("leader", "small"): "実装済み。移動中を含め、そのターン中に新しく見えた敵だけへ1回ずつ戦闘力/5ダメージです。味方は撃ちません。",
            ("leader", "medium"): "押下可能。ラボでは2〜10ターン目の担当キャラ表を作ってログ確認できます。",
            ("leader", "large"): "実装済み。味方ごとに移動先となる味方位置を選ぶと、指定先へ同時再配置します。",
            ("saint", "small"): "実装済み。次の自分の番まで完全反射状態を付け、アリア本人はダメージを受けません。",
            ("saint", "medium"): "実装済み。味方ランダム1体へ+3します。",
            ("saint", "large"): "実装済み。このセット中、true sight を有効化します。",
            ("psychic", "small"): "実装済み。半径5マス以内の相手へ3ダメージ、自分へ1ダメージです。移動はできません。",
            ("psychic", "medium"): "実装済み。空きマスへランダム転移します。",
            ("psychic", "large"): "実装済み。自分以外へ、10マス以内5 / 20マス以内3 / それ以外1ダメージです。",
            ("samurai", "small"): "実装済み。円形3マスへ戦闘力/3ダメージです。",
            ("samurai", "medium"): "実装済み。次の自分の番まで視界侵入へ反応斬りします。",
            ("samurai", "large"): "実装済み。次の自分の番まで周囲1マス侵入へ迎撃します。",
            ("berserker", "small"): "実装済み。現在の捕食半径内へ戦闘力ぶんダメージです。",
            ("berserker", "medium"): "実装済み。HP5消費で移動量倍として扱います。",
            ("berserker", "large"): "実装済み。HP半減と攻撃半径+1を累積させます。",
            ("beastmaster", "small"): "実装済み。移動先で重なった相手へ4ダメージです。",
            ("beastmaster", "medium"): "実装済み。記録時点ラベル付きで敵位置をマップへ残します。",
            ("beastmaster", "large"): "実装済み。ハムスターを召喚し、操作切替やハムスター移動が可能です。",
        }
        return notes.get((character_key, tier), "未整理")

    def _character_catalog_payload(self, character: CharacterDef) -> dict:
        return {
            "key": character.key,
            "name": character.name,
            "move": character.move,
            "power": character.power,
            "vision": character.vision,
            "small": self._skill_payload(character.small),
            "medium": self._skill_payload(character.medium),
            "large": self._skill_payload(character.large),
            "memo": character.memo,
        }

    def _skill_payload(self, skill) -> dict:
        return {
            "key": skill.key,
            "name": skill.name,
            "cost": skill.cost,
            "description": skill.description,
        }

    def _visible_cells(self) -> set[Cell]:
        controller = self._controller_unit()
        return self._visible_cells_for(controller)

    def _visible_cells_for(self, controller: Optional[UnitState]) -> set[Cell]:
        if not controller or not controller.alive:
            return set()
        if self._has_full_vision(controller):
            return {(x, y) for y in range(self.board_size) for x in range(self.board_size)}
        sources: List[UnitState] = [controller]
        if controller.owner == "A" and self.lab_state.get("shared_vision"):
            sources = [unit for unit in self.units.values() if unit.owner == "A" and unit.alive]
        visible: set[Cell] = set()
        for source in sources:
            radius = max(1, source.effective_vision)
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if self._euclidean_distance(source.cell, (x, y)) <= radius:
                        visible.add((x, y))
        return visible

    def _front_cell(self, previous: Cell, current: Cell) -> Optional[Cell]:
        dx = current[0] - previous[0]
        dy = current[1] - previous[1]
        if dx == 0 and dy == 0:
            return None
        return current[0] + dx, current[1] + dy

    def _manhattan(self, a: Cell, b: Cell) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.board_size and 0 <= cell[1] < self.board_size
