#!/usr/bin/env python
from connect4 import Connect4, PLAYER1, PLAYER2
import asyncio
import itertools
import websockets
from websockets.asyncio.server import broadcast, serve
import json
import secrets


JOIN = {}

async def start(websocket: websockets.WebSocketServerProtocol):
    # Initialize a Connect Four Game, the set of Websockets connections
    game = Connect4()
    connected = {websocket}

    # receiving moves from this game, and secret access token
    join_key = secrets.token_urlsafe(12)
    JOIN[join_key] = game, connected

    try:
        # send secret access token to the browser of the player 1
        # where it will be used for building a "join" link

        event = {
            "type": "init",
            "join": join_key,
        }
        await websocket.send(json.dumps(event))


        # Temporary - for testing
        print("Player1 start the game", id(game))
        # Send the first move, in case the first player already played it.
        await replay(websocket, game)
        await play(websocket, game, PLAYER1, connected)
        
    finally:
        del JOIN[join_key]

async def replay(websocket, game):
    """
    Send previous moves.

    """
    # Make a copy to avoid an exception if game.moves changes while iteration
    # is in progress. If a move is played while replay is running, moves will
    # be sent out of order but each move will be sent once and eventually the
    # UI will be consistent.
    for player, column, row in game.moves.copy():
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        await websocket.send(json.dumps(event))

async def join(websocket, join_key):
    event = {
        "type": "player joined",
        "player": PLAYER2,
    }
    await websocket.send(json.dumps(event))
    # Find the connect4 game and get the set of connected websockets
    try:
        game, connected = JOIN[join_key]
    except Exception as exc:
        await error(websocket, f"Game not found: {exc}")

    # Registered to receive moves from this game
    connected.add(websocket)

    try:
        # Temporary for testing
        print("Player2 join the game", id(game))
        # Send the first move, in case the first player already played it.
        await replay(websocket, game)
        await play(websocket, game, PLAYER2, connected)
    
    finally:
        connected.remove(websocket)

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))

async def handler(websocket: websockets.WebSocketServerProtocol):
    # Receive and parse tje "init" event from the UI
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"
    
    if "join" in event:
        # Player 2 joins an existing game
        join_key = event["join"]
        await join(websocket, join_key)
    
    else:
        # Player1 starts a new game
        await start(websocket)



async def play(websocket, game, player, connected):
    async for message in websocket:
        #Parse a "play" event from the UI
        event = json.loads(message)
        assert event["type"] == "play"
        column = event["column"]

        try:
            #Play the move
            row = game.play(player, column)
        except ValueError as exc:
            error_message = f"Invalid move: {exc}"
            await error(websocket, error_message)

        # Send a "play" event to update the UI.
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        broadcast(connected, json.dumps(event))
    
        # If move is winning, send a "win" event.
        if (game.winner == PLAYER1 or game.winner == PLAYER2):
            event = {
                    "type": "win",
                    "player": game.winner,
                }
            broadcast(connected, json.dumps(event))


async def main():
    async with serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())