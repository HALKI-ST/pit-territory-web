const state = {
  roomCode: "",
  playerToken: "",
  playerSymbol: "",
  socket: null,
  gameState: null,
  mode: "move",
};

const boardEl = document.getElementById("board");
const gameSectionEl = document.getElementById("gameSection");
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
    move: "\u79fb\u52d5",
    jump: "\u30b8\u30e3\u30f3\u30d7",
    pit: "\u843d\u3068\u3057\u7a74",
    pass: "\u884c\u52d5\u7d42\u4e86",
  };
  return labels[action] || "-";
}

function setMode(mode) {
  state.mode = mode;
  const labels = {
    move: "\u901a\u5e38\u79fb\u52d5\u30e2\u30fc\u30c9",
    jump: "\u30b8\u30e3\u30f3\u30d7\u30e2\u30fc\u30c9: \u77e2\u5370\u30ad\u30fc\u3067\u65b9\u5411\u3092\u9078\u3073\u307e\u3059",
    pit: "\u843d\u3068\u3057\u7a74\u30e2\u30fc\u30c9: \u76e4\u9762\u3092\u30af\u30ea\u30c3\u30af\u3057\u3066\u8a2d\u7f6e\u3057\u307e\u3059",
  };
  modeBannerEl.textContent = labels[mode] || labels.move;
  if (state.gameState) {
    render();
  }
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed.");
  }
  return payload;
}

async function createRoom() {
  try {
    const payload = await postJson("/api/rooms", { name: playerName() });
    enterRoom(payload.room_code, payload.player_token, payload.player_symbol);
    setLobbyStatus(`\u30eb\u30fc\u30e0 ${payload.room_code} \u3092\u4f5c\u6210\u3057\u307e\u3057\u305f\u3002\u53cb\u9054\u306b\u30eb\u30fc\u30e0ID\u3092\u5171\u6709\u3057\u3066\u304f\u3060\u3055\u3044\u3002`);
  } catch (error) {
    setLobbyStatus(error.message);
  }
}

async function joinRoom() {
  const code = roomCodeInput();
  if (!code) {
    setLobbyStatus("\u5148\u306b\u30eb\u30fc\u30e0ID\u3092\u5165\u529b\u3057\u3066\u304f\u3060\u3055\u3044\u3002");
    return;
  }

  try {
    const payload = await postJson(`/api/rooms/${code}/join`, { name: playerName() });
    enterRoom(payload.room_code, payload.player_token, payload.player_symbol);
    setLobbyStatus(`\u30eb\u30fc\u30e0 ${payload.room_code} \u306b\u53c2\u52a0\u3057\u307e\u3057\u305f\u3002`);
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
    messageLabelEl.textContent = "\u30eb\u30fc\u30e0\u3068\u306e\u63a5\u7d9a\u304c\u5207\u308c\u307e\u3057\u305f\u3002";
  });
}

function enterRoom(roomCode, token, symbol) {
  state.roomCode = roomCode;
  state.playerToken = token;
  state.playerSymbol = symbol;
  roomCodeLabelEl.textContent = roomCode;
  youAreEl.textContent = `${symbol} \u30d7\u30ec\u30a4\u30e4\u30fc`;
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
  setLobbyStatus("\u30eb\u30fc\u30e0\u3092\u9000\u51fa\u3057\u307e\u3057\u305f\u3002");
}

function sendAction(action) {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    messageLabelEl.textContent = "\u30b5\u30fc\u30d0\u30fc\u306b\u63a5\u7d9a\u3067\u304d\u3066\u3044\u307e\u305b\u3093\u3002";
    return;
  }
  if (!state.gameState || state.gameState.turn !== state.playerSymbol) {
    messageLabelEl.textContent = "\u3044\u307e\u306f\u3042\u306a\u305f\u306e\u624b\u756a\u3067\u306f\u3042\u308a\u307e\u305b\u3093\u3002";
    return;
  }
  state.socket.send(JSON.stringify({ type: "action", ...action }));
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

  turnLabelEl.textContent = game.game_over
    ? "\u30b2\u30fc\u30e0\u7d42\u4e86"
    : game.started
      ? `\u624b\u756a: ${game.players[game.turn].name}\uff08${game.turn}\uff09`
      : "\u5bfe\u6226\u76f8\u624b\u306e\u53c2\u52a0\u5f85\u3061";
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
    const turnLine = game.turn === symbol && !game.game_over ? " / \u624b\u756a" : "";
    const youLine = symbol === state.playerSymbol ? " / \u3042\u306a\u305f" : "";
    const activeLine = myPlayer && symbol === state.playerSymbol ? ` / \u30b8\u30e3\u30f3\u30d7\u6b8b\u308a ${myPlayer.jumps_left}` : "";
    card.innerHTML = `
      <strong>${player.name} (${symbol})${youLine}${turnLine}${activeLine}</strong>
      <div>\u8db3\u8de1\u6570: ${player.score}</div>
      <div>\u843d\u3068\u3057\u7a74\u6b8b\u308a: ${player.pits_left}</div>
      <div>\u30b8\u30e3\u30f3\u30d7\u6b8b\u308a: ${player.jumps_left}</div>
      <div>\u72b6\u614b: ${player.surrendered ? "\u884c\u52d5\u7d42\u4e86" : player.connected ? "\u63a5\u7d9a\u4e2d" : "\u30aa\u30d5\u30e9\u30a4\u30f3"}</div>
      <div>\u524d\u56de\u884c\u52d5: ${actionLabel(player.last_action)}</div>
      <div>\u4f4d\u7f6e: (${player.position[0] + 1}, ${player.position[1] + 1})</div>
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

document.getElementById("createRoomButton").addEventListener("click", createRoom);
document.getElementById("joinRoomButton").addEventListener("click", joinRoom);
document.getElementById("leaveRoomButton").addEventListener("click", leaveRoom);
document.getElementById("copyRoomButton").addEventListener("click", async () => {
  if (!state.roomCode) {
    return;
  }
  await navigator.clipboard.writeText(state.roomCode).catch(() => {});
  setLobbyStatus(`\u30eb\u30fc\u30e0ID ${state.roomCode} \u3092\u30b3\u30d4\u30fc\u3057\u307e\u3057\u305f\u3002`);
});

document.getElementById("moveModeButton").addEventListener("click", () => setMode("move"));
document.getElementById("jumpModeButton").addEventListener("click", () => setMode("jump"));
document.getElementById("pitModeButton").addEventListener("click", () => setMode("pit"));
document.getElementById("passButton").addEventListener("click", () => sendAction({ action: "pass" }));

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
  if (!state.gameState || !state.gameState.started || state.gameState.game_over) {
    return;
  }

  if (state.mode === "jump") {
    sendAction({ action: "jump", direction });
  } else {
    sendAction({ action: "move", direction });
  }
});
