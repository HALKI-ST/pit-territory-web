# Pit Territory Web

Browser-based multiplayer version of the pit territory game using FastAPI and WebSocket.

## What You Need

For local play:

- Python 3.10 or newer
- A terminal
- Two browser tabs or two devices on the same server URL

For the first version, you do not need:

- a paid service
- player login
- player account creation
- a database

You only need a hosting account later if you want to deploy it on the internet so a friend outside your machine can open a URL.

## Cost, Setup, and Accounts

### Does WebSocket cost money?

No by itself. WebSocket is only a communication method supported by browsers and servers.

### Do FastAPI and WebSocket require a paid account?

No. FastAPI is an open-source Python framework, and browsers support WebSocket without payment.

### Do I need my own setup?

Yes, but only a light one for development:

- Python installed
- dependencies from `requirements.txt`
- a terminal to run the server

If you later deploy online, you will need an account on a hosting service such as Render or Railway, but players still do not need accounts for this MVP.

### Do players need login or account creation?

No. This version uses room codes. One player creates a room and shares the code. The other player joins with the code.

## Project Structure

```text
pit_territory_web/
  app.py
  game_logic.py
  requirements.txt
  DESIGN.md
  static/
    index.html
    styles.css
    app.js
```

## Features

- 2-player room creation and join
- Authoritative server-side rule validation
- WebSocket live updates
- 5x5 board rendering in the browser
- Move, jump, pit, and pass actions
- Room-code-based access
- No login required

## Run Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   If you installed dependencies before this update, run it again so WebSocket support is added.

2. Start the server:

   ```bash
   python -m uvicorn app:app --reload
   ```

3. Open the game:

   [http://127.0.0.1:8000](http://127.0.0.1:8000)

4. Test with two players:

- Open the site in two browser tabs or two browsers.
- Create a room in one tab.
- Join the room from the other tab using the room code.

## Deployment Later

To play with friends over the internet, deploy this folder as a Python web service.

For the MVP you can use one service only:

- FastAPI serves the API, WebSocket endpoint, and static frontend together.

That keeps deployment simpler and avoids a separate frontend build system.

## Limitations Of This MVP

- Room state is stored only in memory
- Server restart deletes all rooms
- No spectating
- No rematch button yet
- No long-term persistence
