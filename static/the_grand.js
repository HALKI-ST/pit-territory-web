(() => {
  const root = document.getElementById("grandGameView");
  if (!root) return;

  const ui = {
    inspectKey: "",
    orderDraft: [],
    orderSeed: "",
    path: [],
    battleSeed: "",
  };

  const TEAM_LABELS = {
    A: "青チーム",
    B: "赤チーム",
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function sendGrandAction(payload) {
    if (typeof sendAction === "function") {
      sendAction(payload);
    }
  }

  function viewerSymbol(game) {
    return game.viewer_symbol || (window.state?.playerSymbol ?? "");
  }

  function viewerPlayer(game) {
    return (game.players || {})[viewerSymbol(game)] || null;
  }

  function isHost(game) {
    return viewerSymbol(game) === "A";
  }

  function connectedPlayers(game) {
    return Object.values(game.players || {}).filter((player) => player?.connected);
  }

  function characterByKey(game, key) {
    return (game.catalog || []).find((entry) => entry.key === key) || null;
  }

  function characterLabel(entry) {
    if (!entry) return "";
    return entry.role === entry.name ? entry.role : `${entry.role}：${entry.name}`;
  }

  function spritePath(key, hero = false) {
    return hero
      ? `/static/assets/the_grand/hero/${key}.png`
      : `/static/assets/the_grand/${key}.png`;
  }

  function syncInspectKey(game) {
    const player = viewerPlayer(game);
    const selected = player?.selected_keys || [];
    if (selected.includes(ui.inspectKey)) return;
    ui.inspectKey = selected[selected.length - 1] || game.catalog?.[0]?.key || "";
  }

  function syncOrderDraft(game) {
    const player = viewerPlayer(game);
    if (!player) {
      ui.orderDraft = [];
      ui.orderSeed = "";
      return;
    }
    const seed = `${game.set_number}:${player.selected_keys.join("|")}`;
    if (seed !== ui.orderSeed) {
      ui.orderSeed = seed;
      ui.orderDraft = [...(player.order?.length ? player.order : player.selected_keys || [])];
    }
  }

  function syncBattleInput(game) {
    const seed = `${game.viewer_actor_id}:${game.set_number}:${game.round_number}:${game.result_ready ? "result" : "input"}`;
    if (seed !== ui.battleSeed) {
      ui.battleSeed = seed;
      ui.path = [];
    }
  }

  function currentActor(game) {
    return (game.units || {})[game.viewer_actor_id] || null;
  }

  function wallsSet(game) {
    return new Set((game.walls || []).map((cell) => `${cell[0]},${cell[1]}`));
  }

  function visibleSet(game) {
    return new Set((game.viewport?.visible_cells || []).map((cell) => `${cell[0]},${cell[1]}`));
  }

  function unitsByCell(game) {
    const result = new Map();
    Object.values(game.units || {}).forEach((unit) => {
      if (!unit?.alive) return;
      result.set(`${unit.cell[0]},${unit.cell[1]}`, unit);
    });
    return result;
  }

  function flagsByCell(game) {
    const result = new Map();
    Object.values(game.flags || {}).forEach((flag) => {
      if (!flag?.alive) return;
      result.set(`${flag.cell[0]},${flag.cell[1]}`, flag);
    });
    return result;
  }

  function battlePathSet() {
    return new Set(ui.path.map((cell) => `${cell[0]},${cell[1]}`));
  }

  function reachableSet(game, actor) {
    const result = new Set();
    if (!actor || game.viewer_waiting || game.result_ready) return result;
    const walls = wallsSet(game);
    const current = ui.path.length ? ui.path[ui.path.length - 1] : actor.cell;
    const remaining = actor.move - ui.path.length;
    if (remaining <= 0) return result;
    [[1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dx, dy]) => {
      const next = [current[0] + dx, current[1] + dy];
      const key = `${next[0]},${next[1]}`;
      if (next[0] < 0 || next[0] >= game.board_size || next[1] < 0 || next[1] >= game.board_size) return;
      if (walls.has(key)) return;
      result.add(key);
    });
    return result;
  }

  function moveOrder(index, delta, game) {
    const target = index + delta;
    if (target < 0 || target >= ui.orderDraft.length) return;
    const next = [...ui.orderDraft];
    [next[index], next[target]] = [next[target], next[index]];
    ui.orderDraft = next;
    renderGrandGame(game);
  }

  function renderWaiting(game) {
    const canAdvance = isHost(game) && connectedPlayers(game).length >= 2;
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">待機画面</p>
          <h3>The Grand</h3>
          <p class="grand2-copy">${escapeHtml(game.message || "2人揃うまで待機中です。")}</p>
          <div class="grand2-player-grid">
            ${Object.values(game.players || []).map((player) => `
              <div class="grand2-player-card">
                <strong>${escapeHtml(player.name)}</strong>
                <span>${player.connected ? "参加中" : "未参加"}</span>
              </div>
            `).join("")}
          </div>
          <button type="button" class="primary" data-grand-advance ${canAdvance ? "" : "disabled"}>フィールド選択へ進む</button>
        </section>
      </div>
    `;
    root.querySelector("[data-grand-advance]")?.addEventListener("click", () => {
      sendGrandAction({ action: "advance_phase" });
    });
  }

  function renderFieldSelect(game) {
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">フィールド選択</p>
          <h3>戦うフィールドを選んでください</h3>
          <p class="grand2-copy">${escapeHtml(game.message || "")}</p>
          <div class="grand2-field-grid">
            ${(game.field_options || []).map((field) => `
              <button type="button" class="grand2-field-card" data-grand-field="${escapeHtml(field.key)}" ${isHost(game) ? "" : "disabled"}>
                <strong>${escapeHtml(field.name)}</strong>
                <span>${escapeHtml(field.summary)}</span>
              </button>
            `).join("")}
          </div>
        </section>
      </div>
    `;
    root.querySelectorAll("[data-grand-field]").forEach((button) => {
      button.addEventListener("click", () => {
        sendGrandAction({ action: "confirm_field", settings: { field_type: button.dataset.grandField } });
      });
    });
  }

  function renderCharacterSelect(game) {
    syncInspectKey(game);
    const player = viewerPlayer(game);
    const inspect = characterByKey(game, ui.inspectKey);
    root.innerHTML = `
      <div class="grand2-phase grand2-character-layout">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">キャラ選択</p>
          ${inspect ? `
            <div class="grand2-hero">
              <img src="${spritePath(inspect.key, true)}" alt="${escapeHtml(inspect.name)}" class="grand2-hero-image" onerror="this.src='${spritePath(inspect.key, false)}'">
              <div class="grand2-hero-copy">
                <h3>${escapeHtml(characterLabel(inspect))}</h3>
                <p class="grand2-copy">${escapeHtml(inspect.summary || "")}</p>
                <div class="grand2-stat-row">
                  <div><span>行動力</span><strong>${inspect.move}</strong></div>
                  <div><span>戦闘力</span><strong>${inspect.power}</strong></div>
                  <div><span>探知力</span><strong>${inspect.vision}</strong></div>
                </div>
              </div>
            </div>
            <div class="grand2-skill-list">
              <article><strong>小技 / ${escapeHtml(inspect.small.name)}</strong><span>コスト ${inspect.small.cost}</span><p>${escapeHtml(inspect.small.description)}</p></article>
              <article><strong>中技 / ${escapeHtml(inspect.medium.name)}</strong><span>コスト ${inspect.medium.cost}</span><p>${escapeHtml(inspect.medium.description)}</p></article>
              <article><strong>大技 / ${escapeHtml(inspect.large.name)}</strong><span>コスト ${inspect.large.cost}</span><p>${escapeHtml(inspect.large.description)}</p></article>
            </div>
          ` : `<p class="grand2-copy">キャラクターを押すと詳細が表示されます。</p>`}
        </section>
        <section class="grand2-panel">
          <p class="grand2-eyebrow">現在の編成</p>
          <div class="grand2-selected-list">
            ${(player?.selected_keys || []).map((key) => {
              const entry = characterByKey(game, key);
              return `<button type="button" class="grand2-selected-item" data-grand-inspect="${escapeHtml(key)}">${escapeHtml(characterLabel(entry))}</button>`;
            }).join("") || '<p class="grand2-copy">まだ選ばれていません。</p>'}
          </div>
          <button type="button" class="primary" data-grand-confirm-roster ${(player?.selected_keys?.length || 0) > 0 ? "" : "disabled"}>この編成で決定</button>
          <p class="grand2-copy">${player?.roster_confirmed ? "編成を確定済みです。" : "キャラクターを選んで編成を決定してください。"}</p>
        </section>
        <section class="grand2-panel grand2-panel-wide">
          <p class="grand2-eyebrow">キャラクター一覧</p>
          <div class="grand2-character-grid">
            ${(game.catalog || []).map((entry) => {
              const selected = Boolean(player?.selected_keys?.includes(entry.key));
              return `
                <button type="button" class="grand2-character-card ${selected ? "is-selected" : ""}" data-grand-toggle="${escapeHtml(entry.key)}" data-grand-inspect="${escapeHtml(entry.key)}">
                  <img src="${spritePath(entry.key)}" alt="${escapeHtml(entry.name)}" class="grand2-card-image">
                  <strong>${escapeHtml(entry.role)}</strong>
                  <span>${escapeHtml(entry.name)}</span>
                </button>
              `;
            }).join("")}
          </div>
        </section>
      </div>
    `;

    root.querySelectorAll("[data-grand-inspect]").forEach((button) => {
      button.addEventListener("click", () => {
        ui.inspectKey = button.dataset.grandInspect || "";
        renderGrandGame(game);
      });
    });

    root.querySelectorAll("[data-grand-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const key = button.dataset.grandToggle || "";
        const selected = [...(player?.selected_keys || [])];
        const index = selected.indexOf(key);
        if (index >= 0) {
          selected.splice(index, 1);
        } else if (selected.length < 10) {
          selected.push(key);
        }
        ui.inspectKey = key;
        sendGrandAction({ action: "update_setup", settings: { selected_keys: selected } });
      });
    });

    root.querySelector("[data-grand-confirm-roster]")?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_roster" });
    });
  }

  function renderOrderSelect(game) {
    syncOrderDraft(game);
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">行動順設定</p>
          <h3>このセットの行動順</h3>
          <p class="grand2-copy">${escapeHtml(game.message || "")}</p>
          <div class="grand2-order-list">
            ${ui.orderDraft.map((key, index) => {
              const entry = characterByKey(game, key);
              return `
                <div class="grand2-order-row">
                  <strong>${index + 1}. ${escapeHtml(characterLabel(entry))}</strong>
                  <div class="grand2-order-actions">
                    <button type="button" data-grand-order="${index}" data-grand-delta="-1">上へ</button>
                    <button type="button" data-grand-order="${index}" data-grand-delta="1">下へ</button>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
          <button type="button" class="primary" data-grand-confirm-order ${ui.orderDraft.length ? "" : "disabled"}>この順番で確定</button>
        </section>
      </div>
    `;

    root.querySelectorAll("[data-grand-order]").forEach((button) => {
      button.addEventListener("click", () => {
        moveOrder(Number(button.dataset.grandOrder || 0), Number(button.dataset.grandDelta || 0), game);
      });
    });

    root.querySelector("[data-grand-confirm-order]")?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_order", settings: { priority: ui.orderDraft } });
    });
  }

  function buildMinimap(game) {
    const boardSize = Number(game.board_size || 50);
    const group = 2;
    const miniSize = Math.ceil(boardSize / group);
    const knownFloor = new Set((game.known_floor || []).map((cell) => `${cell[0]},${cell[1]}`));
    const knownWalls = new Set((game.known_walls || []).map((cell) => `${cell[0]},${cell[1]}`));
    const visibleCells = new Set((game.visible_cells || []).map((cell) => `${cell[0]},${cell[1]}`));
    const flags = Object.values(game.flags || {}).filter((flag) => flag?.alive);
    const units = Object.values(game.units || {}).filter((unit) => unit?.alive);
    const activeActorId = game.viewer_actor_id || "";

    const cells = [];
    for (let my = 0; my < miniSize; my += 1) {
      for (let mx = 0; mx < miniSize; mx += 1) {
        let hasKnownFloor = false;
        let hasVisible = false;
        let hasWall = false;
        let hasFlagA = false;
        let hasFlagB = false;
        let hasUnitA = false;
        let hasUnitB = false;
        let hasFocusA = false;
        let hasFocusB = false;
        for (let y = my * group; y < Math.min(boardSize, (my + 1) * group); y += 1) {
          for (let x = mx * group; x < Math.min(boardSize, (mx + 1) * group); x += 1) {
            const key = `${x},${y}`;
            if (knownFloor.has(key)) hasKnownFloor = true;
            if (visibleCells.has(key)) hasVisible = true;
            if (knownWalls.has(key)) hasWall = true;
            flags.forEach((flag) => {
              if (flag.cell[0] === x && flag.cell[1] === y) {
                if (flag.team === "A") hasFlagA = true;
                if (flag.team === "B") hasFlagB = true;
              }
            });
            units.forEach((unit) => {
              if (unit.cell[0] === x && unit.cell[1] === y) {
                if (unit.team === "A") hasUnitA = true;
                if (unit.team === "B") hasUnitB = true;
                if (unit.id === activeActorId && unit.team === "A") hasFocusA = true;
                if (unit.id === activeActorId && unit.team === "B") hasFocusB = true;
              }
            });
          }
        }
        const classes = ["grand2-mini-cell"];
        if (hasKnownFloor) classes.push("is-floor");
        if (hasVisible) classes.push("is-visible");
        if (hasWall) classes.push("is-wall");
        cells.push(`
          <div class="${classes.join(" ")}">
            ${hasFlagA ? '<span class="grand2-mini-flag team-a"></span>' : ""}
            ${hasFlagB ? '<span class="grand2-mini-flag team-b"></span>' : ""}
            ${hasUnitA ? `<span class="grand2-mini-unit team-a ${hasFocusA ? "is-focus" : ""}"></span>` : ""}
            ${hasUnitB ? `<span class="grand2-mini-unit team-b ${hasFocusB ? "is-focus" : ""}"></span>` : ""}
          </div>
        `);
      }
    }
    return {
      size: miniSize,
      html: cells.join(""),
    };
  }

  function renderBattle(game) {
    syncBattleInput(game);
    const actor = currentActor(game);
    const viewport = game.viewport || { cells: [], visible_cells: [] };
    const visible = visibleSet(game);
    const walls = wallsSet(game);
    const units = unitsByCell(game);
    const flags = flagsByCell(game);
    const path = battlePathSet();
    const reachable = reachableSet(game, actor);

    const board = (viewport.cells || []).map((cell) => {
      const key = `${cell[0]},${cell[1]}`;
      const unit = units.get(key);
      const flag = flags.get(key);
      const floorClass = (cell[0] + cell[1]) % 2 === 0 ? "is-floor-a" : "is-floor-b";
      const classes = [
        "grand2-board-cell",
        floorClass,
        visible.has(key) ? "is-visible" : "is-hidden",
        walls.has(key) ? "is-wall" : "",
        path.has(key) ? "is-path" : "",
        reachable.has(key) ? "is-reachable" : "",
        unit ? `team-${String(unit.team).toLowerCase()}` : "",
        actor && unit && unit.id === actor.id ? "is-current-actor" : "",
      ].filter(Boolean).join(" ");
      return `
        <button type="button" class="${classes}" data-grand-cell="${cell[0]},${cell[1]}" ${reachable.has(key) ? "" : "disabled"}>
          ${flag ? `<span class="grand2-flag team-${String(flag.team).toLowerCase()}">⚑</span>` : ""}
          ${unit ? `<img src="${spritePath(unit.character_key)}" alt="${escapeHtml(unit.name)}" class="grand2-unit-sprite">` : ""}
        </button>
      `;
    }).join("");

    const minimap = buildMinimap(game);

    root.innerHTML = `
      <div class="grand2-phase grand2-battle-layout">
        <section class="grand2-panel">
          <div class="grand2-battle-head">
            <div><span>セット</span><strong>${game.set_number} / 10</strong></div>
            <div><span>ターン</span><strong>${game.round_number} / 10</strong></div>
            <div><span>状態</span><strong>${escapeHtml(game.message || "")}</strong></div>
          </div>
          <div class="grand2-board-wrap">
            <div class="grand2-board">${board}</div>
          </div>
        </section>
        <section class="grand2-panel">
          <p class="grand2-eyebrow">現在の操作キャラ</p>
          ${actor ? `
            <div class="grand2-battle-actor">
              <img src="${spritePath(actor.character_key)}" alt="${escapeHtml(actor.name)}" class="grand2-battle-actor-image">
              <div>
                <h3>${escapeHtml(characterLabel(actor))}</h3>
                <p class="grand2-copy">HP ${actor.hp}/${actor.max_hp} / 行動力 ${actor.move} / 探知力 ${actor.vision} / コスト ${actor.cost}</p>
              </div>
            </div>
          ` : `<p class="grand2-copy">行動できるキャラがいません。</p>`}
          <div class="grand2-action-row">
            <button type="button" class="primary" data-grand-clear ${game.viewer_waiting || game.result_ready ? "disabled" : ""}>入力クリア</button>
            <button type="button" class="primary" data-grand-submit ${game.viewer_waiting || game.result_ready || !actor ? "disabled" : ""}>この行動で決定</button>
          </div>
          ${game.result_ready ? `
            <div class="grand2-action-row">
              <button type="button" class="primary" data-grand-confirm-result ${game.viewer_continue_confirmed ? "disabled" : ""}>結果を確認して次へ</button>
            </div>
          ` : ""}
          <p class="grand2-copy">今回は移動のみの最小戦闘ループです。技は次の段階で本編へ戻します。</p>
          <p class="grand2-eyebrow">全体マップ</p>
          <div class="grand2-mini-wrap">
            <div class="grand2-mini-board" style="--mini-size:${minimap.size};">${minimap.html}</div>
          </div>
          <div class="grand2-mini-legend">
            <span><i class="team-a"></i>青ユニット</span>
            <span><i class="team-b"></i>赤ユニット</span>
            <span><i class="flag-a"></i>青旗</span>
            <span><i class="flag-b"></i>赤旗</span>
            <span><i class="wall"></i>壁</span>
          </div>
          <div class="grand2-team-status">
            ${Object.entries(game.players || {}).map(([team, player]) => `
              <div class="grand2-team-box">
                <strong>${escapeHtml(TEAM_LABELS[team] || team)}</strong>
                <p>コイン ${player.coins || 0}</p>
                <p>編成 ${escapeHtml((player.selected_keys || []).map((key) => characterLabel(characterByKey(game, key))).join(" / "))}</p>
              </div>
            `).join("")}
          </div>
        </section>
      </div>
    `;

    root.querySelectorAll("[data-grand-cell]").forEach((button) => {
      button.addEventListener("click", () => {
        const [x, y] = (button.dataset.grandCell || "").split(",").map(Number);
        ui.path = [...ui.path, [x, y]];
        renderGrandGame(game);
      });
    });
    root.querySelector("[data-grand-clear]")?.addEventListener("click", () => {
      ui.path = [];
      renderGrandGame(game);
    });
    root.querySelector("[data-grand-submit]")?.addEventListener("click", () => {
      sendGrandAction({
        action: "submit_turn",
        settings: {
          actor_id: game.viewer_actor_id,
          path: ui.path,
        },
      });
    });
    root.querySelector("[data-grand-confirm-result]")?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_result" });
    });
  }

  function renderOld(game) {
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">旧版</p>
          <h3>旧 The Grand</h3>
          <p class="grand2-copy">${escapeHtml(game.message || "旧版は保管用です。")}</p>
        </section>
      </div>
    `;
  }

  window.renderGrandGame = function renderGrandGame(game) {
    if (!root) return;
    root.classList.remove("hidden");
    if (game.game_type === "the_grand_old") {
      renderOld(game);
      return;
    }
    if (game.phase === "waiting") {
      renderWaiting(game);
      return;
    }
    if (game.phase === "field_select") {
      renderFieldSelect(game);
      return;
    }
    if (game.phase === "character_select") {
      renderCharacterSelect(game);
      return;
    }
    if (game.phase === "order_select") {
      renderOrderSelect(game);
      return;
    }
    renderBattle(game);
  };
})();
