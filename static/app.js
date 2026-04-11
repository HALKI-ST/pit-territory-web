const state = {
  roomCode: "",
  playerToken: "",
  playerSymbol: "",
  selectedGameType: "",
  socket: null,
  gameState: null,
  games: [],
  mode: "move",
};

const boardEl = document.getElementById("board");
const gameSectionEl = document.getElementById("gameSection");
const gameSelectEl = document.getElementById("gameSelect");
const gameTitleLabelEl = document.getElementById("gameTitleLabel");
const lobbyStatusEl = document.getElementById("lobbyStatus");
const roomCodeLabelEl = document.getElementById("roomCodeLabel");
const turnLabelEl = document.getElementById("turnLabel");
const messageLabelEl = document.getElementById("messageLabel");
const winnerLabelEl = document.getElementById("winnerLabel");
const playersPanelEl = document.getElementById("playersPanel");
const youAreEl = document.getElementById("youAre");
const modeBannerEl = document.getElementById("modeBanner");

function playerName() {
  return document.getElementById("nameInput").value.trim();
}

function roomCodeInput() {
  return document.getElementById("roomCodeInput").value.trim().toUpperCase();
}

function setLobbyStatus(message) {
  lobbyStatusEl.textContent = message;
}

function actionLabel(action) {
  const labels = {
    move: "移動",
    jump: "ジャンプ",
    pit: "落とし穴",
    pass: "行動終了",
  };
  return labels[action] || "-";
}

function setMode(mode) {
  state.mode = mode;
  const labels = {
    move: "通常移動モード",
    jump: "ジャンプモード: 方向ボタンか矢印キーで方向を選びます",
    pit: "落とし穴モード: 盤面をクリックして設置します",
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
  gameSectionEl.classList.add("hidden");
  setLobbyStatus("ルームを退出しました。");
}

function sendAction(action) {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    messageLabelEl.textContent = "サーバーに接続できていません。";
    return;
  }
  if (!state.gameState || state.gameState.turn !== state.playerSymbol) {
    messageLabelEl.textContent = "いまはあなたの手番ではありません。";
    return;
  }
  state.socket.send(JSON.stringify({ type: "action", ...action }));
}

function sendDirectionalAction(direction) {
  if (!state.gameState || !state.gameState.started || state.gameState.game_over) {
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
  const myTurn = game.turn === state.playerSymbol;
  const myPlayer = currentPlayerState();

  gameTitleLabelEl.textContent = game.title || "ゲーム";
  turnLabelEl.textContent = game.game_over
    ? "ゲーム終了"
    : game.started
      ? `手番: ${game.players[game.turn].name}（${game.turn}）`
      : "対戦相手の参加待ち";
  messageLabelEl.textContent = game.message;
  winnerLabelEl.textContent = game.winner_text || "";

  renderPlayers(game, myPlayer);
  renderBoard(game, myTurn);
}

function renderPlayers(game, myPlayer) {
  playersPanelEl.innerHTML = "";
  for (const symbol of ["O", "X"]) {
    const player = game.players[symbol];
    const card = document.createElement("div");
    card.className = `player-card ${symbol.toLowerCase()}`;
    const turnLine = game.turn === symbol && !game.game_over ? " / 手番" : "";
    const youLine = symbol === state.playerSymbol ? " / あなた" : "";
    const activeLine = myPlayer && symbol === state.playerSymbol ? ` / ジャンプ残り ${myPlayer.jumps_left}` : "";
    card.innerHTML = `
      <strong>${player.name} (${symbol})${youLine}${turnLine}${activeLine}</strong>
      <div>足跡数: ${player.score}</div>
      <div>落とし穴残り: ${player.pits_left}</div>
      <div>ジャンプ残り: ${player.jumps_left}</div>
      <div>状態: ${player.surrendered ? "行動終了" : player.connected ? "接続中" : "オフライン"}</div>
      <div>前回行動: ${actionLabel(player.last_action)}</div>
      <div>位置: (${player.position[0] + 1}, ${player.position[1] + 1})</div>
    `;
    playersPanelEl.appendChild(card);
  }
}

function renderBoard(game, myTurn) {
  boardEl.innerHTML = "";
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
      if (trail === "O") {
        cell.classList.add("trail-o");
      } else if (trail === "X") {
        cell.classList.add("trail-x");
      }
      if (pitSet.has(key)) {
        cell.classList.add("pit");
      }

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
          if (game.turn === symbol && !game.game_over) {
            cell.classList.add("active-turn");
          }
        }
      }

      const canClickPit = state.mode === "pit" && myTurn && game.started && !game.game_over;
      if (canClickPit) {
        cell.classList.add("clickable");
        cell.disabled = false;
        cell.addEventListener("click", () => {
          sendAction({ action: "pit", cell: [x, y] });
        });
      } else {
        cell.disabled = true;
      }

      boardEl.appendChild(cell);
    }
  }
}

function bindDirectionButton(buttonId, direction) {
  document.getElementById(buttonId).addEventListener("click", () => {
    sendDirectionalAction(direction);
  });
}

document.getElementById("createRoomButton").addEventListener("click", createRoom);
document.getElementById("joinRoomButton").addEventListener("click", joinRoom);
document.getElementById("leaveRoomButton").addEventListener("click", leaveRoom);
document.getElementById("copyRoomButton").addEventListener("click", async () => {
  if (!state.roomCode) {
    return;
  }
  await navigator.clipboard.writeText(state.roomCode).catch(() => {});
  setLobbyStatus(`ルームID ${state.roomCode} をコピーしました。`);
});

document.getElementById("moveModeButton").addEventListener("click", () => setMode("move"));
document.getElementById("jumpModeButton").addEventListener("click", () => setMode("jump"));
document.getElementById("pitModeButton").addEventListener("click", () => setMode("pit"));
document.getElementById("passButton").addEventListener("click", () => sendAction({ action: "pass" }));

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
  if (!direction) {
    return;
  }

  event.preventDefault();
  sendDirectionalAction(direction);
});

loadGames();
