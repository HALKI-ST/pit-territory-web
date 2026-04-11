# Pit Territory Web Design

## Goal

Create a browser-playable version of the pit territory game for two remote players.

## Constraints

- No player login required for the first version.
- No paid service required for local play.
- No database required for the first version.
- Server is authoritative for rules and turn order.
- Realtime updates use WebSocket.

## Stack

- Backend: FastAPI
- Realtime transport: WebSocket
- Frontend: HTML, CSS, vanilla JavaScript
- Storage: In-memory room state

## Architecture

### Server responsibilities

- Create rooms
- Accept room join
- Assign player symbols `O` and `X`
- Validate all actions
- Track board state, pits, jumps, trails, turn, and winner
- Broadcast the latest state to connected clients

### Client responsibilities

- Show lobby and room code
- Connect to the room WebSocket
- Render the board and side panel
- Send requested player actions
- Display status messages and winner

## Data Model

### Player

- `symbol`: `O` or `X`
- `name`: display name
- `position`: `[x, y]`
- `trails`: list of claimed cells
- `pits_left`: number
- `jumps_left`: number
- `last_action`: `move`, `jump`, `pit`, `pass`, or `null`
- `surrendered`: boolean
- `connected`: boolean

### Room

- `code`: short room code
- `players`: tokens mapped to player entries
- `turn`: current symbol
- `pits`: list of pit cells
- `started`: boolean
- `game_over`: boolean
- `message`: latest game message
- `winner_text`: final result

## Network Protocol

### HTTP

- `GET /api/health`
- `POST /api/rooms`
  - body: `{ "name": "Alice" }`
  - response: `{ "room_code": "...", "player_token": "...", "player_symbol": "O" }`
- `POST /api/rooms/{room_code}/join`
  - body: `{ "name": "Bob" }`
  - response: `{ "room_code": "...", "player_token": "...", "player_symbol": "X" }`

### WebSocket

- `WS /ws/{room_code}/{player_token}`

#### Client messages

- `{ "type": "action", "action": "move", "direction": "up" }`
- `{ "type": "action", "action": "jump", "direction": "left" }`
- `{ "type": "action", "action": "pit", "cell": [2, 3] }`
- `{ "type": "action", "action": "pass" }`

#### Server messages

- `{ "type": "state", "state": ... }`
- `{ "type": "error", "message": "..." }`

## Game Flow

1. Player A creates a room and receives symbol `O`.
2. Player B joins the room and receives symbol `X`.
3. Each player opens a WebSocket using their token.
4. Server marks room as started when both seats are filled.
5. Acting player sends one of the legal actions.
6. Server validates, mutates state, and broadcasts the latest board.
7. When both players pass, the server declares the winner.

## MVP Notes

- Room data is stored only in memory.
- Restart is done by creating a new room.
- If the server restarts, all rooms disappear.
- Reconnection is supported as long as the room still exists and the player still has the token.
