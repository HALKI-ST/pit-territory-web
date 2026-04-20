(() => {
  const root = document.getElementById("grandGameView");
  if (!root) return;

  const ui = {
    inspectKey: "",
    orderDraft: [],
    orderOwner: "",
    path: [],
    selectedSkillTier: "",
    skillDirection: "right",
    skillDistance: 5,
    actorId: "",
  };

  const characterLabels = {
    speed_star: "繧ｹ繝斐・繝峨せ繧ｿ繝ｼ",
    spiritualist: "髴願・蜉幄・,
    archer: "蠑灘・",
    soldier: "髮大・",
    leader: "繝ｪ繝ｼ繝繝ｼ",
    saint: "閨門･ｳ",
    psychic: "繧ｵ繧､繧ｭ繝・き繝ｼ",
    samurai: "萓・,
    berserker: "繝舌・繧ｵ繝ｼ繧ｫ繝ｼ",
    beastmaster: "迯｣菴ｿ縺・,
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
    return viewerSymbol(game) && viewerSymbol(game) === "A";
  }

  function joinedCount(game) {
    return Object.values(game.players || {}).filter((player) => player?.connected).length;
  }

  function spritePath(key, hero = false) {
    return hero
      ? `/static/assets/the_grand/hero/${key}.png`
      : `/static/assets/the_grand/${key}.png`;
  }

  function characterByKey(game, key) {
    return (game.catalog || []).find((entry) => entry.key === key) || null;
  }

  function characterLabel(game, key) {
    const entry = characterByKey(game, key);
    return characterLabels[key] || entry?.role || entry?.name || key;
  }

  function characterLabelWithName(game, key) {
    const entry = characterByKey(game, key);
    const role = characterLabels[key] || entry?.role || key;
    const name = entry?.name || role;
    return role === name ? role : `${role}・・{name}`;
  }

  function syncInspectKey(game) {
    const player = viewerPlayer(game);
    const selected = player?.selected_keys || [];
    if (selected.includes(ui.inspectKey)) return;
    ui.inspectKey = selected[selected.length - 1] || game.catalog?.[0]?.key || "";
  }

  function syncOrderDraft(game) {
    if (game.phase !== "order_select") {
      ui.orderDraft = [];
      ui.orderOwner = "";
      return;
    }
    const player = viewerPlayer(game);
    if (!player) return;
    const ownerKey = (player.selected_keys || []).join("|");
    if (ui.orderOwner !== ownerKey || ui.orderDraft.length !== (player.selected_keys || []).length) {
      ui.orderOwner = ownerKey;
      ui.orderDraft = [...(player.order?.length ? player.order : player.selected_keys || [])];
    }
  }

  function moveDraft(index, delta, game) {
    const next = [...ui.orderDraft];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    ui.orderDraft = next;
    renderGrandGame(game);
  }

  function renderWaiting(game) {
    const canAdvance = isHost(game) && joinedCount(game) >= 2;
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">蠕・ｩ溽判髱｢</p>
          <h3>The Grand</h3>
          <p class="grand2-copy">${escapeHtml(game.message || "")}</p>
          <div class="grand2-player-grid">
            ${Object.values(game.players || []).map((player) => `
              <div class="grand2-player-card">
                <strong>${escapeHtml(player.name)}</strong>
                <span>${player.connected ? "蜿ょ刈荳ｭ" : "譛ｪ蜿ょ刈"}</span>
              </div>
            `).join("")}
          </div>
          <button type="button" class="primary" data-grand-action="advance" ${canAdvance ? "" : "disabled"}>繝輔ぅ繝ｼ繝ｫ繝蛾∈謚槭∈騾ｲ繧</button>
        </section>
      </div>
    `;
    root.querySelector('[data-grand-action="advance"]')?.addEventListener("click", () => {
      sendGrandAction({ action: "advance_phase" });
    });
  }

  function renderFieldSelect(game) {
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">繝輔ぅ繝ｼ繝ｫ繝蛾∈謚・/p>
          <h3>繝輔ぅ繝ｼ繝ｫ繝峨ｒ驕ｸ繧薙〒縺上□縺輔＞</h3>
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
          <p class="grand2-eyebrow">繧ｭ繝｣繝ｩ驕ｸ謚・/p>
          ${inspect ? `
            <div class="grand2-hero">
              <img src="${spritePath(inspect.key, true)}" alt="${escapeHtml(inspect.name)}" class="grand2-hero-image" onerror="this.src='${spritePath(inspect.key, false)}'">
              <div class="grand2-hero-copy">
                <h3>${escapeHtml(inspect.role)} : ${escapeHtml(inspect.name)}</h3>
                <p class="grand2-copy">${escapeHtml(inspect.summary || "")}</p>
                <div class="grand2-stat-row">
                  <div><span>陦悟虚蜉・/span><strong>${inspect.move}</strong></div>
                  <div><span>謌ｦ髣伜鴨</span><strong>${inspect.power}</strong></div>
                  <div><span>謗｢遏･蜉・/span><strong>${inspect.vision}</strong></div>
                </div>
              </div>
            </div>
            <div class="grand2-skill-list">
              <article><strong>蟆乗橿 / ${escapeHtml(inspect.small.name)}</strong><span>繧ｳ繧ｹ繝・${inspect.small.cost}</span><p>${escapeHtml(inspect.small.description)}</p></article>
              <article><strong>荳ｭ謚 / ${escapeHtml(inspect.medium.name)}</strong><span>繧ｳ繧ｹ繝・${inspect.medium.cost}</span><p>${escapeHtml(inspect.medium.description)}</p></article>
              <article><strong>螟ｧ謚 / ${escapeHtml(inspect.large.name)}</strong><span>繧ｳ繧ｹ繝・${inspect.large.cost}</span><p>${escapeHtml(inspect.large.description)}</p></article>
            </div>
          ` : `<p class="grand2-copy">繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧帝∈縺ｶ縺ｨ隧ｳ邏ｰ縺後％縺薙↓蜃ｺ縺ｾ縺吶・/p>`}
        </section>
        <section class="grand2-panel">
          <p class="grand2-eyebrow">迴ｾ蝨ｨ縺ｮ邱ｨ謌・/p>
          <div class="grand2-selected-list">
            ${(player?.selected_keys || []).map((key) => {
              const entry = characterByKey(game, key);
              return `<button type="button" class="grand2-selected-item" data-grand-inspect="${escapeHtml(key)}">${escapeHtml(entry?.role || key)}</button>`;
            }).join("") || '<p class="microcopy">縺ｾ縺繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ縺碁∈縺ｰ繧後※縺・∪縺帙ｓ縲・/p>'}
          </div>
          <button type="button" class="primary" data-grand-action="confirm-roster" ${(player?.selected_keys?.length || 0) > 0 ? "" : "disabled"}>縺薙・邱ｨ謌舌〒豎ｺ螳・/button>
          <p class="microcopy">${player?.roster_confirmed ? "邱ｨ謌舌ｒ遒ｺ螳壽ｸ医∩縺ｧ縺吶・ : "繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ繧帝∈繧薙〒豎ｺ螳壹＠縺ｦ縺上□縺輔＞縲・}</p>
        </section>
        <section class="grand2-panel grand2-panel-wide">
          <p class="grand2-eyebrow">繧ｭ繝｣繝ｩ繧ｯ繧ｿ繝ｼ荳隕ｧ</p>
          <div class="grand2-character-grid">
            ${(game.catalog || []).map((entry) => {
              const selected = Boolean(player?.selected_keys?.includes(entry.key));
              return `
                <button type="button" class="grand2-character-card ${selected ? "is-selected" : ""}" data-grand-toggle="${escapeHtml(entry.key)}" data-grand-inspect="${escapeHtml(entry.key)}">
                  <img src="${spritePath(entry.key, false)}" alt="${escapeHtml(entry.name)}" class="grand2-card-image">
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
    root.querySelector('[data-grand-action="confirm-roster"]')?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_roster" });
    });
  }

  function renderOrderSelect(game) {
    syncOrderDraft(game);
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">陦悟虚鬆・ｨｭ螳・/p>
          <h3>縺薙・繧ｻ繝・ヨ縺ｮ陦悟虚鬆・/h3>
          <p class="grand2-copy">${escapeHtml(game.message || "")}</p>
          <div class="grand2-order-list">
            ${ui.orderDraft.map((key, index) => {
              const entry = characterByKey(game, key);
              return `
                <div class="grand2-order-row">
                    <strong>${index + 1}. ${escapeHtml(characterLabelWithName(game, key))}</strong>
                  <div class="grand2-order-actions">
                    <button type="button" data-grand-move="${index}" data-grand-delta="-1">荳翫∈</button>
                    <button type="button" data-grand-move="${index}" data-grand-delta="1">荳九∈</button>
                  </div>
                </div>
              `;
            }).join("")}
          </div>
          <button type="button" class="primary" data-grand-action="confirm-order" ${ui.orderDraft.length ? "" : "disabled"}>縺薙・鬆・分縺ｧ遒ｺ螳・/button>
        </section>
      </div>
    `;
    root.querySelectorAll("[data-grand-move]").forEach((button) => {
      button.addEventListener("click", () => {
        moveDraft(Number(button.dataset.grandMove || 0), Number(button.dataset.grandDelta || 0), game);
      });
    });
    root.querySelector('[data-grand-action="confirm-order"]')?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_order", settings: { priority: ui.orderDraft } });
    });
  }

  function currentReplayFrame(game) {
    const frames = game.replay_frames || [];
    return frames.length ? frames[frames.length - 1] : null;
  }

  function resetBattleInput(game, actor) {
    const key = `${game.viewer_actor_id}:${game.replay_token}:${game.set_number}:${game.round_number}`;
    if (ui.actorId !== key) {
      ui.actorId = key;
      ui.path = [];
      ui.selectedSkillTier = "";
      ui.skillDirection = "right";
      ui.skillDistance = 5;
    }
    if (!actor) {
      ui.path = [];
      ui.selectedSkillTier = "";
    }
  }

  function stepLimit(actor, skillTier) {
    if (!actor) return 0;
    if (skillTier === "small" && actor.character_key === "speed_star") return 10;
    if (skillTier === "medium" && actor.character_key === "speed_star") return 10;
    if (skillTier === "large" && actor.character_key === "speed_star") return 0;
    return actor.move || 0;
  }

  function buildVisibleSet(cells) {
    return new Set((cells || []).map((cell) => `${cell[0]},${cell[1]}`));
  }

  function unitLookup(units) {
    const map = new Map();
    Object.values(units || {}).forEach((entry) => {
      if (!entry?.alive) return;
      map.set(`${entry.cell[0]},${entry.cell[1]}`, entry);
    });
    return map;
  }

  function flagLookup(flags) {
    const map = new Map();
    (flags || []).forEach((entry) => {
      if (!entry?.alive) return;
      map.set(`${entry.cell[0]},${entry.cell[1]}`, entry);
    });
    return map;
  }

  function renderBattle(game) {
    const replay = currentReplayFrame(game);
    const baseUnits = game.units || {};
    const replayUnits = replay?.units || {};
    const units = {};
    Object.entries(baseUnits).forEach(([id, entry]) => {
      units[id] = { ...entry };
    });
    Object.entries(replayUnits).forEach(([id, entry]) => {
      units[id] = { ...(units[id] || {}), ...entry };
    });
    const visibleCells = replay?.visible_cells || game.visible_cells || [];
    const flags = replay?.flags || game.flags || [];
    const coins = replay?.coins || game.coins || [];
    const visibleSet = buildVisibleSet(visibleCells);
    const knownFloor = buildVisibleSet(game.known_floor || []);
    const knownWalls = buildVisibleSet(game.known_walls || []);
    const knownLava = buildVisibleSet(game.known_lava || []);
    const knownCoins = buildVisibleSet(game.known_coins || []);
    const coinSet = buildVisibleSet(coins || []);
    const unitByCell = unitLookup(units);
    const flagByCell = flagLookup(flags);
    const viewer = viewerSymbol(game);
    const actor = units[game.viewer_actor_id] || null;
    resetBattleInput(game, actor);

    const boardSize = game.board_size || 50;
    const viewSize = game.viewport_size || 15;
    const half = Math.floor(viewSize / 2);
    const actorCell = actor?.cell || [0, 0];
    const originX = actorCell[0] - half;
    const originY = actorCell[1] - half;
    const endpoint = ui.path.length ? ui.path[ui.path.length - 1] : actorCell;
    const limit = stepLimit(actor, ui.selectedSkillTier);

    const localCells = [];
    for (let vy = 0; vy < viewSize; vy += 1) {
      for (let vx = 0; vx < viewSize; vx += 1) {
        const x = originX + vx;
        const y = originY + vy;
        const inBounds = x >= 0 && y >= 0 && x < boardSize && y < boardSize;
        const key = `${x},${y}`;
        const visible = visibleSet.has(key);
        const wall = knownWalls.has(key);
        const lava = knownLava.has(key);
        const onPath = ui.path.some((cell) => cell[0] === x && cell[1] === y);
        const canAppend =
          inBounds &&
          !game.result_ready &&
          !game.viewer_waiting &&
          !!actor &&
          ui.selectedSkillTier !== "large" &&
          !wall &&
          ui.path.length < limit &&
          Math.abs(endpoint[0] - x) + Math.abs(endpoint[1] - y) === 1;
        const unit = unitByCell.get(key);
        const flag = flagByCell.get(key);
        const coin = coinSet.has(key);
        const teamTint = "";
        localCells.push(`
          <button type="button" class="grand2-board-cell ${(x + y) % 2 === 0 ? "is-floor-a" : "is-floor-b"} ${visible ? "is-visible" : "is-hidden"} ${wall ? "is-wall" : ""} ${lava ? "is-lava" : ""} ${onPath ? "is-path" : ""} ${canAppend ? "is-reachable" : ""}${teamTint}" data-grand-cell="${x},${y}" ${canAppend ? "" : "disabled"}>
            ${flag ? `<span class="grand2-flag grand2-team-${flag.team}">${flag.team === "A" ? "髱呈覧" : "襍､譌・}</span>` : ""}
            ${coin ? `<span class="grand2-coin"></span>` : ""}
            ${unit ? `<img src="${spritePath(unit.character_key || unit.key || "", false)}" alt="${escapeHtml(unit.name)}" class="grand2-unit grand2-team-${unit.owner || unit.team}">` : ""}
          </button>
        `);
      }
    }

    const miniCells = [];
    const miniScale = 2;
    const miniSize = Math.max(1, Math.ceil(boardSize / miniScale));
    for (let my = 0; my < miniSize; my += 1) {
      for (let mx = 0; mx < miniSize; mx += 1) {
        const worldCells = [];
        for (let oy = 0; oy < miniScale; oy += 1) {
          for (let ox = 0; ox < miniScale; ox += 1) {
            const x = mx * miniScale + ox;
            const y = my * miniScale + oy;
            if (x < boardSize && y < boardSize) worldCells.push([x, y]);
          }
        }
        const focus = actor && worldCells.some(([x, y]) => actor.cell[0] === x && actor.cell[1] === y);
        const visible = worldCells.some(([x, y]) => visibleSet.has(`${x},${y}`));
        const floor = visible || worldCells.some(([x, y]) => knownFloor.has(`${x},${y}`));
        const wall = worldCells.some(([x, y]) => knownWalls.has(`${x},${y}`));
        const lava = worldCells.some(([x, y]) => knownLava.has(`${x},${y}`));
        const memoryCoin = worldCells.some(([x, y]) => knownCoins.has(`${x},${y}`));
        const flag = worldCells.map(([x, y]) => flagByCell.get(`${x},${y}`)).find(Boolean);
        const unit = worldCells.map(([x, y]) => unitByCell.get(`${x},${y}`)).find(Boolean);
        const isAlly = unit && unit.owner === viewer;
        const isEnemy = unit && unit.owner !== viewer;
        const showUnit = isAlly || (isEnemy && visible);
        miniCells.push(`
          <div class="grand2-mini-cell ${focus ? "is-focus" : ""} ${visible ? "is-visible" : ""} ${floor ? "is-floor" : ""} ${wall ? "is-wall" : ""} ${lava ? "is-lava" : ""}">
            ${flag ? `<span class="grand2-mini-dot grand2-team-${flag.team} is-flag"></span>` : ""}
            ${memoryCoin ? `<span class="grand2-mini-dot is-coin"></span>` : ""}
            ${showUnit ? `<span class="grand2-mini-dot grand2-team-${unit.owner || unit.team} ${isAlly ? "is-ally" : "is-enemy"}"></span>` : ""}
          </div>
        `);
      }
    }

    const skillButton = (tier, label) => {
      const skill = actor?.[tier];
      if (!skill) return "";
      const active = ui.selectedSkillTier === tier;
      return `<button type="button" class="${active ? "primary" : ""}" data-grand-skill="${tier}">${label} / ${escapeHtml(skill.name)} (${skill.cost})</button>`;
    };

    root.innerHTML = `
      <div class="grand2-phase grand2-battle-layout">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">謌ｦ髣倅ｸｭ</p>
          <div class="grand2-stat-row">
            <div><span>繧ｻ繝・ヨ</span><strong>${game.set_number || 1} / ${game.max_sets || 10}</strong></div>
            <div><span>繧ｿ繝ｼ繝ｳ</span><strong>${game.round_number || 1} / ${game.rounds_per_set || 10}</strong></div>
            <div><span>蜍晏茜譚｡莉ｶ</span><strong>${game.coin_target || 20}繧ｳ繧､繝ｳ / 譌・/ 驕主濠謨ｰ</strong></div>
            <div><span>迥ｶ諷・/span><strong>${escapeHtml(game.message || "")}</strong></div>
          </div>
          <div class="grand2-board">${localCells.join("")}</div>
        </section>
        <section class="grand2-panel">
          <p class="grand2-eyebrow">迴ｾ蝨ｨ縺ｮ謫堺ｽ懊く繝｣繝ｩ</p>
          ${actor ? `
            <div class="grand2-battle-actor">
              <img src="${spritePath(actor.character_key || "", false)}" alt="${escapeHtml(actor.name)}" class="grand2-battle-actor-image">
              <div>
                <h3>${escapeHtml(actor.name)}</h3>
                <p class="grand2-copy">${escapeHtml(actor.owner === "A" ? "髱偵メ繝ｼ繝" : "襍､繝√・繝")}</p>
                <p class="microcopy">HP ${actor.hp ?? "-"} / ${actor.max_hp ?? actor.hp ?? "-"} / 陦悟虚蜉・${actor.move ?? "-"} / 謗｢遏･蜉・${actor.vision ?? "-"} / 繧ｳ繧ｹ繝・${actor.cost ?? "-"}</p>
              </div>
            </div>
          ` : `<p class="grand2-copy">迴ｾ蝨ｨ縺ｮ謫堺ｽ懊く繝｣繝ｩ縺ｯ縺・∪縺帙ｓ縲・/p>`}
          <div class="grand2-action-row">
            <button type="button" class="${ui.selectedSkillTier === "" ? "primary" : ""}" data-grand-mode="move">遘ｻ蜍・/button>
            ${skillButton("small", "蟆乗橿")}
            ${skillButton("medium", "荳ｭ謚")}
            ${skillButton("large", "螟ｧ謚")}
          </div>
          ${ui.selectedSkillTier === "large" && actor?.character_key === "speed_star" ? `
            <div class="grand2-action-row">
              <select data-grand-direction>
                <option value="up" ${ui.skillDirection === "up" ? "selected" : ""}>荳・/option>
                <option value="right" ${ui.skillDirection === "right" ? "selected" : ""}>蜿ｳ</option>
                <option value="down" ${ui.skillDirection === "down" ? "selected" : ""}>荳・/option>
                <option value="left" ${ui.skillDirection === "left" ? "selected" : ""}>蟾ｦ</option>
              </select>
              <input type="number" min="1" max="${boardSize}" value="${ui.skillDistance}" data-grand-distance>
            </div>
          ` : ""}
          <div class="grand2-action-row">
            <button type="button" class="primary" data-grand-submit ${game.viewer_waiting || game.result_ready || !actor ? "disabled" : ""}>縺薙・陦悟虚縺ｧ豎ｺ螳・/button>
            <button type="button" data-grand-clear ${game.viewer_waiting || game.result_ready ? "disabled" : ""}>蜈･蜉帙け繝ｪ繧｢</button>
          </div>
          ${game.result_ready ? `
            <div class="grand2-action-row">
              <button type="button" class="primary" data-grand-confirm-result ${game.viewer_continue_confirmed ? "disabled" : ""}>邨先棡繧堤｢ｺ隱阪＠縺ｦ谺｡縺ｸ</button>
            </div>
          ` : ""}
          <p class="grand2-copy">${escapeHtml(game.setup_note || "")}</p>
          <p class="grand2-eyebrow">蜈ｨ菴薙・繝・・</p>
          <div class="grand2-mini-wrap">
            <div class="grand2-mini-board" style="grid-template-columns: repeat(${miniSize}, minmax(0, 1fr));">${miniCells.join("")}</div>
          </div>
          <div class="grand2-mini-legend">
            <span><i class="team-a"></i>蜻ｳ譁ｹ</span>
            <span><i class="team-b"></i>謨ｵ</span>
            <span><i class="flag-a"></i>髱呈覧</span>
            <span><i class="flag-b"></i>襍､譌・/span>
            <span><i class="wall"></i>髢狗､ｺ螢・/span>
          </div>
          <div class="grand2-team-status">
            ${Object.entries(game.players || {}).map(([team, player]) => `
              <div class="grand2-team-box">
                <strong>${team === "A" ? "Player A" : "Player B"}</strong>
                <p>繧ｳ繧､繝ｳ ${player.coins || 0}</p>
                <p>邱ｨ謌・${escapeHtml((player.selected_keys || []).map((key) => characterByKey(game, key)?.name || key).join(" / "))}</p>
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
    root.querySelector('[data-grand-mode="move"]')?.addEventListener("click", () => {
      ui.selectedSkillTier = "";
      renderGrandGame(game);
    });
    root.querySelectorAll("[data-grand-skill]").forEach((button) => {
      button.addEventListener("click", () => {
        ui.selectedSkillTier = button.dataset.grandSkill || "";
        ui.path = [];
        renderGrandGame(game);
      });
    });
    root.querySelector("[data-grand-direction]")?.addEventListener("change", (event) => {
      ui.skillDirection = event.target.value;
    });
    root.querySelector("[data-grand-distance]")?.addEventListener("change", (event) => {
      ui.skillDistance = Math.max(1, Number(event.target.value || 1));
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
          skill_tier: ui.selectedSkillTier,
          skill_direction: ui.skillDirection,
          skill_distance: ui.skillDistance,
        },
      });
    });
    root.querySelector("[data-grand-confirm-result]")?.addEventListener("click", () => {
      sendGrandAction({ action: "confirm_result" });
    });
  }

  function renderLab(game) {
    root.innerHTML = `
      <div class="grand2-phase">
        <section class="grand2-panel">
          <p class="grand2-eyebrow">縺願ｩｦ縺鈴Κ螻・/p>
          <h3>The Grand 縺願ｩｦ縺鈴Κ螻・/h3>
          <p class="grand2-copy">${escapeHtml(game.message || "縺薙％縺九ｉ縺ｯ譌ｧ繝・ヰ繝・げ驛ｨ螻九ｒ菴ｿ縺・∪縺吶・)}</p>
        </section>
      </div>
    `;
  }

  window.renderGrandGame = function renderGrandGame(game) {
    if (!root) return;
    if (game.phase === "waiting") return renderWaiting(game);
    if (game.phase === "field_select") return renderFieldSelect(game);
    if (game.phase === "character_select") return renderCharacterSelect(game);
    if (game.phase === "order_select") return renderOrderSelect(game);
    if (game.phase === "lab") return renderLab(game);
    return renderBattle(game);
  };
})();

