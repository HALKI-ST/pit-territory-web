const state = {
  roomCode: "",
  playerToken: "",
  playerSymbol: "",
  selectedGameType: "",
  socket: null,
  gameState: null,
  games: [],
  mode: "move",
  auctionSettingsOpen: false,
  replayTurn: 0,
};

const boardEl = document.getElementById("board");
const auctionBoardEl = document.getElementById("auctionBoard");
const auctionBoardLinesEl = document.getElementById("auctionBoardLines");
const mouseBoardEl = document.getElementById("mouseBoard");
const gameSectionEl = document.getElementById("gameSection");
const pitGameViewEl = document.getElementById("pitGameView");
const auctionGameViewEl = document.getElementById("auctionGameView");
const mouseTrapViewEl = document.getElementById("mouseTrapView");
const gameSelectEl = document.getElementById("gameSelect");
const gameTitleLabelEl = document.getElementById("gameTitleLabel");
const lobbyStatusEl = document.getElementById("lobbyStatus");
const roomCodeLabelEl = document.getElementById("roomCodeLabel");
const turnLabelEl = document.getElementById("turnLabel");
const messageLabelEl = document.getElementById("messageLabel");
const winnerLabelEl = document.getElementById("winnerLabel");
const playersPanelEl = document.getElementById("playersPanel");
const auctionPlayersPanelEl = document.getElementById("auctionPlayersPanel");
const auctionPlayersPanelBlockEl = document.getElementById("auctionPlayersPanelBlock");
const auctionLogPanelEl = document.getElementById("auctionLogPanel");
const quickBidButtonsEl = document.getElementById("quickBidButtons");
const youAreEl = document.getElementById("youAre");
const modeBannerEl = document.getElementById("modeBanner");
const pitStartPanelEl = document.getElementById("pitStartPanel");
const pitStartPanelNoteEl = document.getElementById("pitStartPanelNote");
const pitRematchPanelEl = document.getElementById("pitRematchPanel");
const auctionStartPanelEl = document.getElementById("auctionStartPanel");
const auctionStartNoteEl = document.getElementById("auctionStartNote");
const auctionSettingsPanelEl = document.getElementById("auctionSettingsPanel");
const auctionRematchPanelEl = document.getElementById("auctionRematchPanel");
const auctionResultsPanelEl = document.getElementById("auctionResultsPanel");
const auctionReplayPanelEl = document.getElementById("auctionReplayPanel");
const auctionRoundLabelEl = document.getElementById("auctionRoundLabel");
const auctionRollLabelEl = document.getElementById("auctionRollLabel");
const auctionTrackLabelEl = document.getElementById("auctionTrackLabel");
const bankBalanceLabelEl = document.getElementById("bankBalanceLabel");
const bidUnitsInputEl = document.getElementById("bidUnitsInput");
const goalRewardBannerEl = document.getElementById("goalRewardBanner");
const auctionTurnDetailEl = document.getElementById("auctionTurnDetail");
const replayTurnLabelEl = document.getElementById("replayTurnLabel");
const replaySummaryLabelEl = document.getElementById("replaySummaryLabel");
const mousePhaseLabelEl = document.getElementById("mousePhaseLabel");
const mouseWallLabelEl = document.getElementById("mouseWallLabel");
const mouseTurnLabelEl = document.getElementById("mouseTurnLabel");
const mouseGuideLabelEl = document.getElementById("mouseGuideLabel");
const mouseBuildLogEl = document.getElementById("mouseBuildLog");
const mouseChaseLogEl = document.getElementById("mouseChaseLog");
const mouseRematchPanelEl = document.getElementById("mouseRematchPanel");

const settingEls = {
  startingBalance: document.getElementById("settingStartingBalance"),
  diceSides: document.getElementById("settingDiceSides"),
  trackLength: document.getElementById("settingTrackLength"),
  plusCount: document.getElementById("settingPlusCount"),
  minusCount: document.getElementById("settingMinusCount"),
  forwardCount: document.getElementById("settingForwardCount"),
  backwardCount: document.getElementById("settingBackwardCount"),
  forwardSteps: document.getElementById("settingForwardSteps"),
  backwardSteps: document.getElementById("settingBackwardSteps"),
  blankCount: document.getElementById("settingBlankCount"),
  netTileTotal: document.getElementById("settingNetTileTotal"),
  moneyTileMin: document.getElementById("settingMoneyTileMin"),
  moneyTileMax: document.getElementById("settingMoneyTileMax"),
  tapePosition: document.getElementById("settingTapePosition"),
  tapeBonus: document.getElementById("settingTapeBonus"),
  goalRewards: document.getElementById("settingGoalRewards"),
  tileLayout: document.getElementById("settingTileLayout"),
};

function playerName() {
  return document.getElementById("nameInput").value.trim();
}

function roomCodeInput() {
  return document.getElementById("roomCodeInput").value.trim().toUpperCase();
}

function setLobbyStatus(message) {
  lobbyStatusEl.textContent = message;
}

function yen(value) {
  return new Intl.NumberFormat("ja-JP", {
    style: "currency",
    currency: "JPY",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function actionLabel(action) {
  const labels = {
    move: "移動",
    jump: "ジャンプ",
    pit: "ピット",
    pass: "行動終了",
  };
  return labels[action] || "-";
}

function statusLabel(status) {
  const labels = {
    waiting: "待機中",
    playing: "続行中",
    finished: "ゴール済み",
    bankrupt: "破産負け",
    resigned: "降参負け",
  };
  return labels[status] || status;
}

function isHost(game) {
  return Boolean(game) && game.host_symbol === state.playerSymbol;
}

function setMode(mode) {
  state.mode = mode;
  const labels = {
    move: "通常移動モード",
    jump: "ジャンプモード: 1回だけ2マス先へ飛べます",
    pit: "ピットモード: 置きたいマスを押してください",
  };
  modeBannerEl.textContent = labels[mode] || labels.move;
  if (state.gameState) {
    render();
  }
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "読み込みに失敗しました。");
  }
  return payload;
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "送信に失敗しました。");
  }
  return payload;
}

async function loadGames() {
  try {
    const payload = await fetchJson("/api/games");
    state.games = payload.games || [];
    if (!state.selectedGameType && state.games.length > 0) {
      state.selectedGameType = state.games[0].game_type;
    }
    renderGameCards();
  } catch (error) {
    setLobbyStatus(error.message);
  }
}

function renderGameCards() {
  gameSelectEl.innerHTML = "";
  for (const game of state.games) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `game-card ${state.selectedGameType === game.game_type ? "selected" : ""}`;
    button.innerHTML = `
      <strong>${game.title}</strong>
      <span>${game.subtitle}</span>
      <span>${game.min_players === game.max_players ? `${game.min_players}人用` : `${game.min_players}-${game.max_players}人用`}</span>
    `;
    button.addEventListener("click", () => {
      state.selectedGameType = game.game_type;
      renderGameCards();
    });
    gameSelectEl.appendChild(button);
  }
}

async function createRoom() {
  if (!state.selectedGameType) {
    setLobbyStatus("先にゲームを選んでください。");
    return;
  }

  try {
    const payload = await postJson("/api/rooms", {
      name: playerName(),
      game_type: state.selectedGameType,
    });
    enterRoom(payload.room_code, payload.player_token, payload.player_symbol, payload.game_type);
    const selectedGame = state.games.find((game) => game.game_type === payload.game_type);
    setLobbyStatus(`ルーム ${payload.room_code} を作成しました。${selectedGame ? selectedGame.title : "ゲーム"} のルームです。`);
  } catch (error) {
    setLobbyStatus(error.message);
  }
}

async function joinRoom() {
  const code = roomCodeInput();
  if (!code) {
    setLobbyStatus("先にルームIDを入力してください。");
    return;
  }

  try {
    const payload = await postJson(`/api/rooms/${code}/join`, { name: playerName() });
    enterRoom(payload.room_code, payload.player_token, payload.player_symbol, payload.game_type);
    setLobbyStatus(`ルーム ${payload.room_code} に参加しました。`);
  } catch (error) {
    setLobbyStatus(error.message);
  }
}

function connectSocket() {
  if (state.socket) {
    state.socket.close();
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  state.socket = new WebSocket(`${protocol}://${window.location.host}/ws/${state.roomCode}/${state.playerToken}`);

  state.socket.addEventListener("open", () => {
    gameSectionEl.classList.remove("hidden");
  });

  state.socket.addEventListener("message", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === "state") {
      state.gameState = payload.state;
      render();
    } else if (payload.type === "error") {
      messageLabelEl.textContent = payload.message;
    }
  });

  state.socket.addEventListener("close", () => {
    messageLabelEl.textContent = "ルームとの接続が切れました。";
  });
}

function enterRoom(roomCode, token, symbol, gameType) {
  state.roomCode = roomCode;
  state.playerToken = token;
  state.playerSymbol = symbol;
  state.selectedGameType = gameType;
  state.auctionSettingsOpen = false;
  state.replayTurn = 0;
  roomCodeLabelEl.textContent = `ルームID: ${roomCode}`;
  youAreEl.textContent = `${symbol} プレイヤー`;
  setMode("move");
  connectSocket();
}

function leaveRoom() {
  if (state.socket) {
    state.socket.close();
  }
  state.roomCode = "";
  state.playerToken = "";
  state.playerSymbol = "";
  state.gameState = null;
  state.auctionSettingsOpen = false;
  state.replayTurn = 0;
  gameSectionEl.classList.add("hidden");
  setLobbyStatus("ルームを退出しました。");
}

function sendAction(action) {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    messageLabelEl.textContent = "サーバーに接続できていません。";
    return;
  }
  state.socket.send(JSON.stringify({ type: "action", ...action }));
}

function sendDirectionalAction(direction) {
  if (!state.gameState || !state.gameState.started || state.gameState.game_over) {
    return;
  }
  if (state.gameState.game_type !== "pit_territory") {
    return;
  }

  if (state.mode === "jump") {
    sendAction({ action: "jump", direction });
  } else {
    sendAction({ action: "move", direction });
  }
}

function currentPlayerState() {
  if (!state.gameState) {
    return null;
  }
  return state.gameState.players[state.playerSymbol] || null;
}

function render() {
  if (!state.gameState) {
    return;
  }

  const game = state.gameState;
  const myPlayer = currentPlayerState();

  gameTitleLabelEl.textContent = game.title || "ゲーム";
  roomCodeLabelEl.textContent = `ルームID: ${game.room_code}`;
  youAreEl.textContent = `${state.playerSymbol} プレイヤー`;
  messageLabelEl.textContent = game.message || "";
  winnerLabelEl.textContent = game.winner_text || "";

  pitGameViewEl.classList.toggle("hidden", game.game_type !== "pit_territory");
  auctionGameViewEl.classList.toggle("hidden", game.game_type !== "auction_race");
  mouseTrapViewEl.classList.toggle("hidden", game.game_type !== "mouse_trap");

  if (game.game_type === "pit_territory") {
    renderPitTerritory(game, myPlayer);
  } else if (game.game_type === "auction_race") {
    renderAuctionRace(game, myPlayer);
  } else if (game.game_type === "mouse_trap") {
    renderMouseTrap(game);
  }
}

function renderPitTerritory(game, myPlayer) {
  const host = isHost(game);
  pitStartPanelEl.classList.toggle("hidden", game.started);
  pitRematchPanelEl.classList.toggle("hidden", !game.game_over);
  pitStartPanelNoteEl.textContent = host
    ? "あなたが先手を決められます。"
    : "部屋を作った人が先手を決めるまで待ってください。";

  turnLabelEl.textContent = game.game_over
    ? "ゲーム終了"
    : game.started
      ? `手番: ${game.players[game.turn].name}（${game.turn}）`
      : "開始待ち";

  renderPitPlayers(game, myPlayer);
  renderPitBoard(game);
}

function renderPitPlayers(game, myPlayer) {
  playersPanelEl.innerHTML = "";
  for (const symbol of ["O", "X"]) {
    const player = game.players[symbol];
    const card = document.createElement("div");
    card.className = `player-card ${symbol.toLowerCase()}`;
    const labels = [];
    if (symbol === state.playerSymbol) labels.push("あなた");
    if (symbol === game.host_symbol) labels.push("部屋主");
    if (game.started && game.turn === symbol && !game.game_over) labels.push("手番");

    card.innerHTML = `
      <strong>${player.name} (${symbol})${labels.length ? ` / ${labels.join(" / ")}` : ""}</strong>
      <div>足跡数: ${player.score}</div>
      <div>ピット残り: ${player.pits_left}</div>
      <div>ジャンプ残り: ${player.jumps_left}</div>
      <div>接続: ${player.surrendered ? "行動終了" : player.connected ? "接続中" : "オフライン"}</div>
      <div>前回の行動: ${actionLabel(player.last_action)}</div>
      <div>位置: (${player.position[0] + 1}, ${player.position[1] + 1})</div>
      ${myPlayer && symbol === state.playerSymbol ? `<div>自分のジャンプ残り: ${myPlayer.jumps_left}</div>` : ""}
    `;
    playersPanelEl.appendChild(card);
  }
}

function renderPitBoard(game) {
  boardEl.innerHTML = "";
  const myTurn = game.turn === state.playerSymbol;
  const trailMap = new Map();
  const pitSet = new Set(game.pits.map(([x, y]) => `${x},${y}`));

  for (const symbol of ["O", "X"]) {
    for (const [x, y] of game.players[symbol].trails) {
      trailMap.set(`${x},${y}`, symbol);
    }
  }

  for (let y = 0; y < game.board_size; y += 1) {
    for (let x = 0; x < game.board_size; x += 1) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "cell";

      const key = `${x},${y}`;
      const trail = trailMap.get(key);
      if (trail === "O") cell.classList.add("trail-o");
      if (trail === "X") cell.classList.add("trail-x");
      if (pitSet.has(key)) cell.classList.add("pit");

      const label = document.createElement("span");
      label.className = "cell-label";
      label.textContent = `${x + 1},${y + 1}`;
      cell.appendChild(label);

      for (const symbol of ["O", "X"]) {
        const [px, py] = game.players[symbol].position;
        if (px === x && py === y) {
          const piece = document.createElement("div");
          piece.className = `piece piece-${symbol.toLowerCase()}`;
          cell.appendChild(piece);
          if (game.started && game.turn === symbol && !game.game_over) {
            cell.classList.add("active-turn");
          }
        }
      }

      const canClickPit = state.mode === "pit" && myTurn && game.started && !game.game_over;
      if (canClickPit) {
        cell.classList.add("clickable");
        cell.disabled = false;
        cell.addEventListener("click", () => sendAction({ action: "pit", cell: [x, y] }));
      } else {
        cell.disabled = true;
      }

      boardEl.appendChild(cell);
    }
  }
}

function renderAuctionRace(game, myPlayer) {
  const host = isHost(game);
  const inProgress = game.started && !game.game_over;

  turnLabelEl.textContent = game.game_over
    ? "ゲーム終了"
    : game.awaiting_judge
      ? "全員入札済み / ジャッジ待ち"
      : game.started
        ? `ラウンド ${game.round_number} / 出目 ${game.current_roll}`
        : `開始待ち (${game.players_joined}/${game.max_players} 人参加中)`;

  auctionRoundLabelEl.textContent = game.round_number || "-";
  auctionRollLabelEl.textContent = game.current_roll || "-";
  auctionTrackLabelEl.textContent = game.track_length || game.settings.track_length || "-";
  bankBalanceLabelEl.textContent = myPlayer && myPlayer.balance_visible ? yen(myPlayer.balance) : "非公開";

  auctionStartPanelEl.classList.toggle("hidden", inProgress || game.game_over);
  auctionRematchPanelEl.classList.toggle("hidden", !game.game_over);
  auctionResultsPanelEl.classList.toggle("hidden", !game.game_over || game.results_revealed);
  auctionReplayPanelEl.classList.toggle("hidden", !game.results_revealed);
  auctionPlayersPanelBlockEl.classList.toggle("hidden", !game.results_revealed);
  auctionSettingsPanelEl.classList.toggle("hidden", !state.auctionSettingsOpen || inProgress || game.game_over);
  auctionStartNoteEl.textContent = host
    ? `現在 ${game.players_joined} 人参加中です。必要なら開始前に設定を変更できます。`
    : "部屋を作った人が開始または設定変更するまで待ってください。";

  if (!game.results_revealed) {
    state.replayTurn = 0;
  } else {
    state.replayTurn = Math.max(0, Math.min(state.replayTurn, (game.round_history || []).length));
  }

  syncAuctionSettingsForm(game);
  renderQuickBidButtons(game, myPlayer);
  renderAuctionPlayers(game);
  renderGoalRewards(game);
  renderReplayPanel(game);
  renderAuctionBoard(game);
  renderAuctionLogs(game);
}

function syncAuctionSettingsForm(game) {
  const settings = game.settings || {};
  const active = state.auctionSettingsOpen && !game.started && !game.game_over;
  if (!active) {
    return;
  }
  settingEls.startingBalance.value = settings.starting_balance ?? "";
  settingEls.diceSides.value = settings.dice_sides ?? "";
  settingEls.trackLength.value = settings.track_length ?? "";
  settingEls.plusCount.value = settings.plus_count ?? "";
  settingEls.minusCount.value = settings.minus_count ?? "";
  settingEls.forwardCount.value = settings.forward_count ?? "";
  settingEls.backwardCount.value = settings.backward_count ?? "";
  settingEls.forwardSteps.value = settings.forward_steps ?? "";
  settingEls.backwardSteps.value = settings.backward_steps ?? "";
  settingEls.blankCount.value = settings.blank_count ?? "";
  settingEls.netTileTotal.value = settings.net_tile_total ?? "";
  settingEls.moneyTileMin.value = settings.money_tile_min ?? "";
  settingEls.moneyTileMax.value = settings.money_tile_max ?? "";
  settingEls.tapePosition.value = settings.tape_bonus_position ?? "";
  settingEls.tapeBonus.value = settings.tape_bonus_value ?? "";
  settingEls.goalRewards.value = settings.goal_rewards ?? "";
  settingEls.tileLayout.value = settings.tile_layout_text ?? "";
}

function collectAuctionSettings() {
  const plusCount = emptyToNull(settingEls.plusCount.value) ?? 0;
  const minusCount = emptyToNull(settingEls.minusCount.value) ?? 0;
  const forwardCount = emptyToNull(settingEls.forwardCount.value) ?? 0;
  const backwardCount = emptyToNull(settingEls.backwardCount.value) ?? 0;
  const forwardSteps = emptyToNull(settingEls.forwardSteps.value) ?? 1;
  const backwardSteps = emptyToNull(settingEls.backwardSteps.value) ?? 1;
  const trackLength = emptyToNull(settingEls.trackLength.value);
  const blankCount = calculateBlankCount(trackLength ?? 0, plusCount, minusCount, forwardCount, backwardCount);
  settingEls.blankCount.value = blankCount >= 0 ? blankCount : "不足";

  return {
    starting_balance: emptyToNull(settingEls.startingBalance.value),
    dice_sides: emptyToNull(settingEls.diceSides.value),
    track_length: trackLength || null,
    plus_count: plusCount,
    minus_count: minusCount,
    forward_count: forwardCount,
    backward_count: backwardCount,
    forward_steps: forwardSteps,
    backward_steps: backwardSteps,
    net_tile_total: emptyToNull(settingEls.netTileTotal.value),
    money_tile_min: emptyToNull(settingEls.moneyTileMin.value),
    money_tile_max: emptyToNull(settingEls.moneyTileMax.value),
    tape_bonus_position: emptyToNull(settingEls.tapePosition.value),
    tape_bonus_value: emptyToNull(settingEls.tapeBonus.value),
    goal_rewards: settingEls.goalRewards.value.trim(),
    tile_layout_text: settingEls.tileLayout.value.trim(),
  };
}

function emptyToNull(value) {
  return value === "" ? null : Number(value);
}

function calculateBlankCount(trackLength, plusCount, minusCount, forwardCount, backwardCount) {
  return (trackLength - 1) - plusCount - minusCount - forwardCount - backwardCount;
}

function syncBlankCount() {
  const plusCount = Number(settingEls.plusCount.value || 0);
  const minusCount = Number(settingEls.minusCount.value || 0);
  const forwardCount = Number(settingEls.forwardCount.value || 0);
  const backwardCount = Number(settingEls.backwardCount.value || 0);
  const currentTrackLength = Number(settingEls.trackLength.value || 0);
  const blankCount = calculateBlankCount(currentTrackLength, plusCount, minusCount, forwardCount, backwardCount);
  settingEls.blankCount.value = blankCount >= 0 ? blankCount : "不足";
}

function renderQuickBidButtons(game, myPlayer) {
  quickBidButtonsEl.innerHTML = "";
  const disabled = !game.started || game.game_over || game.awaiting_judge || !myPlayer || myPlayer.status !== "playing";

  for (const amount of game.quick_bids || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chip-button";
    button.textContent = amount === 0 ? "0" : `${amount / 1000}`;
    button.disabled = disabled;
    button.addEventListener("click", () => {
      bidUnitsInputEl.value = amount / 1000;
    });
    quickBidButtonsEl.appendChild(button);
  }

  bidUnitsInputEl.disabled = disabled;
  document.getElementById("submitBidButton").disabled = disabled;
  document.getElementById("judgeButton").disabled = !game.awaiting_judge || game.game_over;
  document.getElementById("resignButton").disabled = !myPlayer || game.game_over || myPlayer.status !== "playing";
}

function renderAuctionPlayers(game) {
  auctionPlayersPanelEl.innerHTML = "";
  for (const symbol of Object.keys(game.players)) {
    const player = game.players[symbol];
    const card = document.createElement("div");
    card.className = `player-card seat-${symbol.toLowerCase()}`;
    const labels = [];
    if (symbol === state.playerSymbol) labels.push("あなた");
    if (symbol === game.host_symbol) labels.push("部屋主");
    if (player.locked_bid && !game.game_over) labels.push("入札済み");
    if (player.placement) labels.push(`${player.placement}位`);

    const balanceText = player.balance_visible ? yen(player.balance) : "非公開";
    const deltaValue = player.last_delta == null ? null : player.last_delta;
    const deltaText = deltaValue == null ? "-" : `${deltaValue >= 0 ? "+" : ""}${yen(deltaValue)}`;

    card.innerHTML = `
      <strong>${player.name} (${symbol})${labels.length ? ` / ${labels.join(" / ")}` : ""}</strong>
      <div>状態: ${statusLabel(player.status)}</div>
      <div>位置: ${player.position} / ${game.track_length || "-"}</div>
      <div>残高: ${balanceText}</div>
      <div>今回の増減: ${deltaText}</div>
      <div>接続: ${player.connected ? "接続中" : "オフライン"}</div>
      <div>ゴール報酬: ${player.finish_reward ? yen(player.finish_reward) : "-"}</div>
    `;
    auctionPlayersPanelEl.appendChild(card);
  }
}

function renderReplayPanel(game) {
  if (!game.results_revealed) {
    replayTurnLabelEl.textContent = "0";
    replaySummaryLabelEl.textContent = "結果発表後に、各ターンの動きとセリ結果を確認できます。";
    auctionTurnDetailEl.textContent = game.awaiting_judge
      ? "全員の入札がそろいました。ジャッジすると結果が表示されます。"
      : "ここにそのターンのセリ結果が表示されます。";
    return;
  }

  const history = game.round_history || [];
  replayTurnLabelEl.textContent = String(state.replayTurn);
  if (state.replayTurn === 0) {
    replaySummaryLabelEl.textContent = "開始時点の盤面です。";
    auctionTurnDetailEl.textContent = "開始時点です。まだセリ結果はありません。";
    return;
  }
  const round = history[state.replayTurn - 1];
  replaySummaryLabelEl.textContent = round?.summary || "このターンの結果です。";
  auctionTurnDetailEl.textContent = formatRoundDetail(round);
}

function renderGoalRewards(game) {
  const rewards = (game.goal_rewards || [])
    .map((item) => `${item.place}位 ${yen(item.reward)}`)
    .join(" / ");
  const nonGoalText = `${Math.max(2, Object.keys(game.players).length)}人戦では最下位にゴールボーナスなし`;
  const blankText = `空きマス ${game.settings.blank_count}`;
  const tapeText = game.tape_bonus_position != null
    ? `先着テープ: ${game.tape_bonus_position} マス目で ${yen(game.tape_bonus_value)}`
    : `先着テープ: ${yen(game.tape_bonus_value)}`;
  goalRewardBannerEl.textContent = `${tapeText} / ゴール報酬: ${rewards} / ${nonGoalText} / ${blankText}`;
}

function formatRoundDetail(round) {
  if (!round) {
    return "このターンの情報はありません。";
  }
  const bids = Object.values(round.bids || {})
    .map((bid) => `${bid.name} ${yen(bid.amount)}`)
    .join(" / ");
  const winners = (round.winners || [])
    .map((symbol) => round.bids?.[symbol]?.name || symbol)
    .join(" / ");
  return `ターン ${round.round} / 出目 ${round.roll} / 入札 ${bids || "なし"} / 勝者 ${winners || "なし"} / 移動 ${round.move_amount} マス`;
}

function renderAuctionBoard(game) {
  auctionBoardEl.innerHTML = "";
  const replayPositions = getReplayPositions(game);
  const replayTapeClaimedBy = getReplayTapeClaimedBy(game);
  const layout = buildSnakeLayout(game.track_length, game.track_columns || 6);
  auctionBoardEl.style.setProperty("--snake-cols", layout.cols);
  auctionBoardEl.style.setProperty("--snake-rows", layout.rows);

  const piecesByPosition = new Map();
  for (const symbol of Object.keys(game.players)) {
    const pos = replayPositions[symbol] ?? game.players[symbol].position;
    if (!piecesByPosition.has(pos)) {
      piecesByPosition.set(pos, []);
    }
    piecesByPosition.get(pos).push(symbol);
  }

  const tileElements = [];

  for (let index = 0; index <= game.track_length; index += 1) {
    const tile = game.board_tiles[index] || { kind: "blank", value: 0, label: "空き" };
    const snakePos = layout.positions[index];
    const tileEl = document.createElement("div");
    tileEl.className = `track-tile kind-${tile.kind}`;
    tileEl.style.gridColumn = String(snakePos.col + 1);
    tileEl.style.gridRow = String(snakePos.row + 1);
    tileEl.dataset.index = String(index);

    if (game.tape_bonus_position === index) {
      tileEl.classList.add("tape-tile");
      if (replayTapeClaimedBy) {
        tileEl.classList.add("tape-claimed");
      }
    }
    if (tile.kind === "plus") {
      tileEl.classList.add("kind-plus");
    } else if (tile.kind === "minus") {
      tileEl.classList.add("kind-minus");
    } else if (tile.kind === "forward") {
      tileEl.classList.add("kind-forward", "tile-forward");
    } else if (tile.kind === "backward") {
      tileEl.classList.add("kind-backward", "tile-backward");
    }

    const badge = document.createElement("span");
    badge.className = "tile-index";
    badge.textContent = index;
    tileEl.appendChild(badge);

    const label = document.createElement("div");
    label.className = "tile-label";
    label.innerHTML = tileMarkup(tile, index, game);
    tileEl.appendChild(label);

    const pieces = document.createElement("div");
    pieces.className = "tile-pieces";
    for (const symbol of piecesByPosition.get(index) || []) {
      const piece = document.createElement("div");
      piece.className = `track-piece seat-${symbol.toLowerCase()} ${symbol === state.playerSymbol ? "is-you" : ""}`;
      piece.textContent = symbol;
      pieces.appendChild(piece);
    }
    tileEl.appendChild(pieces);

    auctionBoardEl.appendChild(tileEl);
    tileElements.push(tileEl);
  }

  requestAnimationFrame(() => renderSnakeLines(tileElements));
}

function getReplayPositions(game) {
  if (!game.results_revealed) {
    return Object.fromEntries(Object.keys(game.players).map((symbol) => [symbol, game.players[symbol].position]));
  }

  const history = game.round_history || [];
  if (state.replayTurn <= 0 || history.length === 0) {
    return history[0]?.snapshot?.before || Object.fromEntries(Object.keys(game.players).map((symbol) => [symbol, 0]));
  }

  const round = history[Math.min(state.replayTurn, history.length) - 1];
  return round?.snapshot?.after || {};
}

function getReplayTapeClaimedBy(game) {
  if (!game.results_revealed) {
    return game.tape_bonus_claimed_by;
  }
  const history = game.round_history || [];
  if (state.replayTurn <= 0 || history.length === 0) {
    return null;
  }
  const round = history[Math.min(state.replayTurn, history.length) - 1];
  return round?.snapshot?.tape_claimed_by || null;
}

function buildSnakeLayout(trackLength, cols) {
  const count = trackLength + 1;
  const rows = Math.ceil(count / cols);
  const positions = [];

  for (let index = 0; index < count; index += 1) {
    const row = Math.floor(index / cols);
    const offset = index % cols;
    const col = row % 2 === 0 ? offset : cols - 1 - offset;
    positions.push({ row, col });
  }

  return { cols, rows, positions };
}

function renderSnakeLines(tileElements) {
  if (tileElements.length === 0) {
    auctionBoardLinesEl.innerHTML = "";
    return;
  }

  const boardRect = auctionBoardEl.getBoundingClientRect();
  const points = tileElements.map((tileEl) => {
    const rect = tileEl.getBoundingClientRect();
    return {
      x: rect.left - boardRect.left + rect.width / 2,
      y: rect.top - boardRect.top + rect.height / 2,
    };
  });

  auctionBoardLinesEl.setAttribute("viewBox", `0 0 ${boardRect.width} ${boardRect.height}`);
  auctionBoardLinesEl.innerHTML = "";

  for (let index = 0; index < points.length - 1; index += 1) {
    const from = points[index];
    const to = points[index + 1];
    const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const midX = (from.x + to.x) / 2;
    line.setAttribute("d", `M ${from.x} ${from.y} C ${midX} ${from.y}, ${midX} ${to.y}, ${to.x} ${to.y}`);
    line.setAttribute("class", "snake-path");
    auctionBoardLinesEl.appendChild(line);
  }
}

function tileMarkup(tile, index, game) {
  if (index === 0) {
    return `<span class="tile-main">スタート</span>`;
  }
  if (index === game.track_length) {
    const rewards = (game.goal_rewards || [])
      .slice(0, 3)
      .map((item) => `${item.place}位 ${yen(item.reward)}`)
      .join("<br>");
    return `<span class="tile-main">ゴール</span><span class="tile-sub">${rewards}</span>`;
  }
  if (game.tape_bonus_position === index) {
    return `<span class="tile-main">先着テープ</span><span class="tile-sub">先着1名 ${yen(game.tape_bonus_value)}</span>`;
  }
  if (tile.kind === "plus") {
    return `<span class="tile-main">青マス</span><span class="tile-sub">+${yen(tile.value)}</span>`;
  }
  if (tile.kind === "minus") {
    return `<span class="tile-main">赤マス</span><span class="tile-sub">-${yen(Math.abs(tile.value))}</span>`;
  }
  if (tile.kind === "forward") {
    return `<span class="tile-main">進むマス</span><span class="tile-sub">+${tile.value}マス</span>`;
  }
  if (tile.kind === "backward") {
    return `<span class="tile-main">戻るマス</span><span class="tile-sub">-${Math.abs(tile.value)}マス</span>`;
  }
  return `<span class="tile-main">空きマス</span><span class="tile-sub">変化なし</span>`;
}

function renderAuctionLogs(game) {
  auctionLogPanelEl.innerHTML = "";
  const hasReplay = game.results_revealed && (game.round_history || []).length > 0;
  const logs = hasReplay ? game.round_history.slice().reverse() : (game.activity_log || []).slice().reverse();

  if (logs.length === 0) {
    const empty = document.createElement("div");
    empty.className = "log-item";
    empty.textContent = "まだログはありません。";
    auctionLogPanelEl.appendChild(empty);
    return;
  }

  if (!hasReplay) {
    for (const line of logs) {
      const item = document.createElement("div");
      item.className = "log-item";
      item.textContent = line;
      auctionLogPanelEl.appendChild(item);
    }
    return;
  }

  for (const round of logs) {
    const item = document.createElement("div");
    item.className = "log-item round-log";

    const bids = Object.values(round.bids || {})
      .map((bid) => `${bid.name}: ${yen(bid.amount)}`)
      .join(" / ");

    const movement = (round.movement || [])
      .map((step) => `${step.name} ${step.from}→${step.to}`)
      .join(" / ");

    const events = (round.events || []).map((event) => `<li>${event}</li>`).join("");

    item.innerHTML = `
      <strong>ラウンド ${round.round}</strong>
      <div>出目: ${round.roll}</div>
      <div>勝敗: ${round.summary || "なし"}</div>
      <div>入札: ${bids || "なし"}</div>
      <div>移動: ${movement || "移動なし"}</div>
      ${events ? `<ul class="round-events">${events}</ul>` : ""}
    `;
    auctionLogPanelEl.appendChild(item);
  }
}

const mouseSelection = {
  humanPiece: null,
};

function legacyRenderMouseTrap(game) {
  if (game.phase !== "chase" || game.active_side !== "H") {
    mouseSelection.humanPiece = null;
  }
  mouseRematchPanelEl.classList.toggle("hidden", !game.game_over);
  turnLabelEl.textContent = game.game_over
    ? "ゲーム終了"
    : game.phase === "build"
      ? `${game.active_side === "H" ? "人間" : "ネズミ"} が壁を置く番`
      : `${game.chase_turn}ターン目 / ${game.active_side === "H" ? "人間" : "ネズミ"} の番`;

  mousePhaseLabelEl.textContent = game.phase === "build" ? "壁作成" : "追跡";
  mouseWallLabelEl.textContent = `${game.wall_count}/${game.max_walls}`;
  mouseTurnLabelEl.textContent = game.phase === "build" ? "-" : `${game.chase_turn}/${game.max_chase_turns}`;
  mouseGuideLabelEl.textContent = mouseGuideText(game);

  renderMouseBoard(game);
  renderSimpleLog(mouseBuildLogEl, game.build_log || []);
  renderSimpleLog(mouseChaseLogEl, game.chase_log || []);
}

function legacyRenderMouseBoard(game) {
  mouseBoardEl.innerHTML = "";
  mouseBoardEl.style.gridTemplateColumns = "";

  const humanCells = new Map();
  game.humans.forEach((cell, index) => {
    const key = `${cell[0]},${cell[1]}`;
    if (!humanCells.has(key)) humanCells.set(key, []);
    humanCells.get(key).push(index === 0 ? "H1" : "H2");
  });
  const wallSet = new Set(game.walls || []);

  for (let row = 0; row < 9; row += 1) {
    for (let col = 0; col < 9; col += 1) {
      const isCell = row % 2 === 0 && col % 2 === 0;
      const isVertical = row % 2 === 0 && col % 2 === 1;
      const isHorizontal = row % 2 === 1 && col % 2 === 0;
      const node = document.createElement("button");
      node.type = "button";

      if (isCell) {
        const cell = [row / 2, col / 2];
        node.className = "mouse-cell";
        node.textContent = "";
        const key = `${cell[0]},${cell[1]}`;
        const humans = humanCells.get(key) || [];
        if (humans.length > 0) {
          const wrap = document.createElement("div");
          wrap.className = "mouse-piece-wrap";
          for (const human of humans) {
            const piece = document.createElement("div");
            piece.className = `mouse-piece human-piece ${mouseSelection.humanPiece === human ? "selected" : ""}`;
            piece.textContent = "×";
            piece.addEventListener("click", (event) => {
              event.stopPropagation();
              if (state.gameState?.active_side === "H" && state.playerSymbol === "H" && state.gameState.phase === "chase" && !state.gameState.game_over) {
                mouseSelection.humanPiece = human;
                render();
              }
            });
            wrap.appendChild(piece);
          }
          node.appendChild(wrap);
        }
        if (game.mouse[0] === cell[0] && game.mouse[1] === cell[1]) {
          const mousePiece = document.createElement("div");
          mousePiece.className = "mouse-piece mouse-token";
          mousePiece.textContent = "□";
          node.appendChild(mousePiece);
        }
        const label = document.createElement("span");
        label.className = "mouse-cell-label";
        label.textContent = `${cell[0] + 1},${cell[1] + 1}`;
        node.appendChild(label);
        node.addEventListener("click", () => handleMouseCellClick(game, cell));
      } else if (isVertical) {
        const edgeId = `v:${row / 2}:${(col - 1) / 2}`;
        node.className = `mouse-edge vertical ${wallSet.has(edgeId) ? "wall-on" : ""}`;
        node.addEventListener("click", () => handleMouseWallClick(game, edgeId));
      } else if (isHorizontal) {
        const edgeId = `h:${(row - 1) / 2}:${col / 2}`;
        node.className = `mouse-edge horizontal ${wallSet.has(edgeId) ? "wall-on" : ""}`;
        node.addEventListener("click", () => handleMouseWallClick(game, edgeId));
      } else {
        node.className = "mouse-joint";
        node.disabled = true;
      }
      mouseBoardEl.appendChild(node);
    }
  }
}

function legacyMouseGuideText(game) {
  if (game.game_over) {
    return "対戦終了です。ログを見ながら感想戦できます。";
  }
  if (game.phase === "build") {
    return `${game.active_side === "H" ? "人間" : "ネズミ"} が壁を1本置きます。袋小路と4本交差は禁止です。`;
  }
  if (game.active_side === "H") {
    return "人間は動かす×を選んでから、隣のマスを押してください。";
  }
  return game.mouse_steps_taken === 0
    ? "ネズミは1歩目を選んでください。必ず2マス動きます。"
    : "ネズミは続けて2歩目を選んでください。";
}

function handleMouseWallClick(game, edgeId) {
  if (game.phase !== "build" || game.game_over || state.playerSymbol !== game.active_side) {
    return;
  }
  sendAction({ action: "place_wall", edge_id: edgeId });
}

function legacyHandleMouseCellClick(game, cell) {
  if (game.phase !== "chase" || game.game_over || state.playerSymbol !== game.active_side) {
    return;
  }

  if (game.active_side === "H") {
    if (!mouseSelection.humanPiece) {
      messageLabelEl.textContent = "先に動かす人間を選んでください。";
      return;
    }
    sendAction({ action: "move_human", cell, piece: mouseSelection.humanPiece });
    mouseSelection.humanPiece = null;
    return;
  }

  sendAction({ action: "move_mouse", cell });
}

function renderSimpleLog(target, items) {
  target.innerHTML = "";
  if (!items || items.length === 0) {
    const empty = document.createElement("div");
    empty.className = "log-item";
    empty.textContent = "まだログはありません。";
    target.appendChild(empty);
    return;
  }
  for (const line of items.slice().reverse()) {
    const item = document.createElement("div");
    item.className = "log-item";
    item.textContent = line;
    target.appendChild(item);
  }
}

function renderGoalRewards(game) {
  const rewards = (game.goal_rewards || [])
    .map((item) => `${item.place}位 ${yen(item.reward)}`)
    .join(" / ");
  const nonGoalText = `${Math.max(2, Object.keys(game.players).length)}人戦では最下位にゴールボーナスなし`;
  const blankText = `空きマス ${game.settings.blank_count}`;
  const rangeText = `金額マス ${yen(game.settings.money_tile_min)}-${yen(game.settings.money_tile_max)} ランダム`;
  const tapeText = game.tape_bonus_position != null
    ? `先着テープ ${game.tape_bonus_position} マス目で ${yen(game.tape_bonus_value)}`
    : `先着テープ ${yen(game.tape_bonus_value)}`;
  goalRewardBannerEl.textContent = `${tapeText} / ゴール報酬: ${rewards} / ${rangeText} / ${nonGoalText} / ${blankText}`;
}

function mouseCellKey(cell) {
  return `${cell[0]},${cell[1]}`;
}

function mouseIsBlocked(game, from, to) {
  const wallSet = new Set(game.walls || []);
  if (from[0] === to[0]) {
    const row = from[0];
    const col = Math.min(from[1], to[1]);
    return wallSet.has(`v:${row}:${col}`);
  }
  const row = Math.min(from[0], to[0]);
  const col = from[1];
  return wallSet.has(`h:${row}:${col}`);
}

function mouseNeighbors(game, cell) {
  const list = [];
  for (const [dr, dc] of [[-1, 0], [1, 0], [0, -1], [0, 1]]) {
    const next = [cell[0] + dr, cell[1] + dc];
    if (next[0] < 0 || next[0] >= 5 || next[1] < 0 || next[1] >= 5) {
      continue;
    }
    if (!mouseIsBlocked(game, cell, next)) {
      list.push(next);
    }
  }
  return list;
}

function mouseHumansAtCell(game, cell) {
  const humans = [];
  if (game.humans[0][0] === cell[0] && game.humans[0][1] === cell[1]) humans.push("H1");
  if (game.humans[1][0] === cell[0] && game.humans[1][1] === cell[1]) humans.push("H2");
  return humans;
}

function mouseGuideText(game) {
  if (game.game_over) {
    return "対戦終了です。ログを見ながら感想戦できます。";
  }
  if (game.phase === "build") {
    if (state.playerSymbol === game.active_side) {
      return `${game.active_side === "H" ? "人間" : "ネズミ"}側です。明るい線の場所を押して壁を1本置いてください。`;
    }
    return `${game.active_side === "H" ? "人間" : "ネズミ"}側の壁配置ターンです。相手の操作を待ってください。`;
  }
  if (state.playerSymbol !== game.active_side) {
    return `いまは ${game.active_side === "H" ? "人間" : "ネズミ"} 側の番です。あなたは ${state.playerSymbol === "H" ? "人間" : "ネズミ"} 側なので待機してください。`;
  }
  if (game.active_side === "H") {
    return "H1 か H2 を押して選択し、光っている隣マスを押してください。";
  }
  return game.mouse_steps_taken === 0
    ? "ネズミの1歩目です。光っている隣マスへ移動してください。"
    : "ネズミの2歩目です。続けてもう1マス移動してください。";
}

function renderMouseTrap(game) {
  if (game.phase !== "chase" || game.active_side !== "H") {
    mouseSelection.humanPiece = null;
  }
  mouseRematchPanelEl.classList.toggle("hidden", !game.game_over);
  document.getElementById("mouseResetSelectionButton").disabled = game.game_over;
  turnLabelEl.textContent = game.game_over
    ? "ゲーム終了"
    : game.phase === "build"
      ? `${game.active_side === "H" ? "壁作成: 人間" : "壁作成: ネズミ"}`
      : `${game.chase_turn}ターン目 / ${game.active_side === "H" ? "人間" : "ネズミ"} の番`;

  mousePhaseLabelEl.textContent = game.phase === "build" ? "壁作成" : "追跡";
  mouseWallLabelEl.textContent = `${game.wall_count}/${game.max_walls}`;
  mouseTurnLabelEl.textContent = game.phase === "build" ? "-" : `${game.chase_turn}/${game.max_chase_turns}`;
  mouseGuideLabelEl.textContent = mouseGuideText(game);

  renderMouseBoard(game);
  renderSimpleLog(mouseBuildLogEl, game.build_log || []);
  renderSimpleLog(mouseChaseLogEl, game.chase_log || []);
}

function renderMouseBoard(game) {
  mouseBoardEl.innerHTML = "";
  mouseBoardEl.style.gridTemplateColumns = "";

  const humanCells = new Map();
  game.humans.forEach((cell, index) => {
    const key = mouseCellKey(cell);
    if (!humanCells.has(key)) humanCells.set(key, []);
    humanCells.get(key).push(index === 0 ? "H1" : "H2");
  });
  const wallSet = new Set(game.walls || []);
  const selectedOrigin = mouseSelection.humanPiece === "H1"
    ? game.humans[0]
    : mouseSelection.humanPiece === "H2"
      ? game.humans[1]
      : null;
  const validHumanMoves = new Set(
    selectedOrigin
      ? mouseNeighbors(game, selectedOrigin)
        .filter((cell) => !mouseHumansAtCell(game, cell).length || (game.mouse[0] === cell[0] && game.mouse[1] === cell[1]))
        .map((cell) => mouseCellKey(cell))
      : [],
  );
  const validMouseMoves = new Set(
    mouseNeighbors(game, game.mouse)
      .filter((cell) => mouseHumansAtCell(game, cell).length === 0)
      .map((cell) => mouseCellKey(cell)),
  );
  const isHumanTurn = game.phase === "chase" && game.active_side === "H" && state.playerSymbol === "H" && !game.game_over;
  const isMouseTurn = game.phase === "chase" && game.active_side === "M" && state.playerSymbol === "M" && !game.game_over;
  const isBuildTurn = game.phase === "build" && state.playerSymbol === game.active_side && !game.game_over;

  for (let row = 0; row < 9; row += 1) {
    for (let col = 0; col < 9; col += 1) {
      const isCell = row % 2 === 0 && col % 2 === 0;
      const isVertical = row % 2 === 0 && col % 2 === 1;
      const isHorizontal = row % 2 === 1 && col % 2 === 0;
      const node = document.createElement("button");
      node.type = "button";

      if (isCell) {
        const cell = [row / 2, col / 2];
        const key = mouseCellKey(cell);
        node.className = "mouse-cell";
        const humans = humanCells.get(key) || [];

        if (isHumanTurn && validHumanMoves.has(key)) {
          node.classList.add("human-move-target");
        }
        if (isMouseTurn && validMouseMoves.has(key)) {
          node.classList.add("mouse-move-target");
        }
        if (humans.length > 0 && isHumanTurn) {
          node.classList.add("occupied-human-cell");
        }

        if (humans.length > 0) {
          const wrap = document.createElement("div");
          wrap.className = "mouse-piece-wrap";
          for (const human of humans) {
            const piece = document.createElement("div");
            piece.className = `mouse-piece human-piece ${mouseSelection.humanPiece === human ? "selected" : ""}`;
            piece.textContent = human;
            piece.addEventListener("click", (event) => {
              event.stopPropagation();
              if (isHumanTurn) {
                mouseSelection.humanPiece = human;
                render();
              }
            });
            wrap.appendChild(piece);
          }
          node.appendChild(wrap);
        }

        if (game.mouse[0] === cell[0] && game.mouse[1] === cell[1]) {
          const mousePiece = document.createElement("div");
          mousePiece.className = "mouse-piece mouse-token";
          mousePiece.textContent = "M";
          node.appendChild(mousePiece);
        }

        const label = document.createElement("span");
        label.className = "mouse-cell-label";
        label.textContent = `${cell[0] + 1},${cell[1] + 1}`;
        node.appendChild(label);
        node.addEventListener("click", () => handleMouseCellClick(game, cell));
      } else if (isVertical) {
        const edgeId = `v:${row / 2}:${(col - 1) / 2}`;
        node.className = `mouse-edge vertical ${wallSet.has(edgeId) ? "wall-on" : ""} ${isBuildTurn && !wallSet.has(edgeId) ? "wall-slot" : ""}`;
        node.addEventListener("click", () => handleMouseWallClick(game, edgeId));
      } else if (isHorizontal) {
        const edgeId = `h:${(row - 1) / 2}:${col / 2}`;
        node.className = `mouse-edge horizontal ${wallSet.has(edgeId) ? "wall-on" : ""} ${isBuildTurn && !wallSet.has(edgeId) ? "wall-slot" : ""}`;
        node.addEventListener("click", () => handleMouseWallClick(game, edgeId));
      } else {
        node.className = "mouse-joint";
        node.disabled = true;
      }
      mouseBoardEl.appendChild(node);
    }
  }
}

function handleMouseCellClick(game, cell) {
  if (game.phase !== "chase" || game.game_over || state.playerSymbol !== game.active_side) {
    return;
  }

  if (game.active_side === "H") {
    const humans = mouseHumansAtCell(game, cell);
    if (humans.length > 0) {
      mouseSelection.humanPiece = humans[0];
      render();
      return;
    }
    if (!mouseSelection.humanPiece) {
      messageLabelEl.textContent = "先に H1 か H2 を選んでください。";
      return;
    }
    sendAction({ action: "move_human", cell, piece: mouseSelection.humanPiece });
    mouseSelection.humanPiece = null;
    return;
  }

  sendAction({ action: "move_mouse", cell });
}

function bindDirectionButton(buttonId, direction) {
  document.getElementById(buttonId).addEventListener("click", () => sendDirectionalAction(direction));
}

document.getElementById("createRoomButton").addEventListener("click", createRoom);
document.getElementById("joinRoomButton").addEventListener("click", joinRoom);
document.getElementById("leaveRoomButton").addEventListener("click", leaveRoom);
document.getElementById("copyRoomButton").addEventListener("click", async () => {
  if (!state.roomCode) return;
  await navigator.clipboard.writeText(state.roomCode).catch(() => {});
  setLobbyStatus(`ルームID ${state.roomCode} をコピーしました。`);
});

document.getElementById("moveModeButton").addEventListener("click", () => setMode("move"));
document.getElementById("jumpModeButton").addEventListener("click", () => setMode("jump"));
document.getElementById("pitModeButton").addEventListener("click", () => setMode("pit"));
document.getElementById("passButton").addEventListener("click", () => sendAction({ action: "pass" }));
document.getElementById("startOButton").addEventListener("click", () => sendAction({ action: "set_start_player", start_choice: "O" }));
document.getElementById("startXButton").addEventListener("click", () => sendAction({ action: "set_start_player", start_choice: "X" }));
document.getElementById("startRandomButton").addEventListener("click", () => sendAction({ action: "set_start_player", start_choice: "random" }));
document.getElementById("rematchButton").addEventListener("click", () => {
  setMode("move");
  sendAction({ action: "rematch" });
});

document.getElementById("auctionStartButton").addEventListener("click", () => sendAction({ action: "start_match" }));
document.getElementById("auctionRematchButton").addEventListener("click", () => sendAction({ action: "rematch" }));
document.getElementById("showResultsButton").addEventListener("click", () => sendAction({ action: "show_results" }));
document.getElementById("toggleSettingsButton").addEventListener("click", () => {
  state.auctionSettingsOpen = !state.auctionSettingsOpen;
  render();
});
document.getElementById("closeSettingsButton").addEventListener("click", () => {
  state.auctionSettingsOpen = false;
  render();
});
document.getElementById("saveSettingsButton").addEventListener("click", () => {
  sendAction({ action: "update_settings", settings: collectAuctionSettings() });
});
settingEls.plusCount.addEventListener("input", syncBlankCount);
settingEls.minusCount.addEventListener("input", syncBlankCount);
settingEls.forwardCount.addEventListener("input", syncBlankCount);
settingEls.backwardCount.addEventListener("input", syncBlankCount);
settingEls.trackLength.addEventListener("input", syncBlankCount);

document.getElementById("submitBidButton").addEventListener("click", () => {
  const amount = Number(bidUnitsInputEl.value || 0) * 1000;
  sendAction({ action: "place_bid", bid_amount: amount });
});
document.getElementById("judgeButton").addEventListener("click", () => sendAction({ action: "judge_round" }));
document.getElementById("resignButton").addEventListener("click", () => sendAction({ action: "resign" }));
document.getElementById("mouseResetSelectionButton").addEventListener("click", () => {
  sendAction({ action: "resign" });
});
document.getElementById("mouseRematchButton").addEventListener("click", () => {
  sendAction({ action: "rematch" });
});
document.getElementById("replayPrevButton").addEventListener("click", () => {
  state.replayTurn = Math.max(0, state.replayTurn - 1);
  render();
});
document.getElementById("replayNextButton").addEventListener("click", () => {
  const maxTurn = state.gameState?.round_history?.length || 0;
  state.replayTurn = Math.min(maxTurn, state.replayTurn + 1);
  render();
});

bindDirectionButton("dirUpButton", "up");
bindDirectionButton("dirDownButton", "down");
bindDirectionButton("dirLeftButton", "left");
bindDirectionButton("dirRightButton", "right");

window.addEventListener("keydown", (event) => {
  const keyMap = {
    ArrowUp: "up",
    ArrowDown: "down",
    ArrowLeft: "left",
    ArrowRight: "right",
  };
  const direction = keyMap[event.key];
  if (!direction) return;
  event.preventDefault();
  sendDirectionalAction(direction);
});

window.addEventListener("resize", () => {
  if (state.gameState?.game_type === "auction_race") {
    renderAuctionBoard(state.gameState);
  }
});

loadGames();
