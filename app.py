#!/usr/bin/env python
from connect4 import Connect4, PLAYER1, PLAYER2
import asyncio
import itertools
from websockets.asyncio.server import serve
import json


async def handler(websocket):
    #initialize a Connect Four Game
    game = Connect4()

    #Players take alternate turns
    turns = itertools.cycle([PLAYER1, PLAYER2])
    player = next(turns)

    async for message in websocket:
        #Parse a "play" event from the UI
        event = json.loads(message)
        assert event["type"] == "play"
        column = event["column"]

        try:
            #Play the move
            row = game.play(player, column)
        except ValueError as exc:
            event = {
                "type": "error",
                "message": str(exc),
            }
            await websocket.send(json.dumps(event))
            continue

    # Send a "play" event to update the UI.
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row,
        }
        await websocket.send(json.dumps(event))
    
    # If move is winning, send a "win" event.
    if (game.winner == PLAYER1 or game.winner == PLAYER2):
        event = {
                "type": "win",
                "player": game.winner,
            }
        await websocket.send(json.dumps(event))

    # Alternate turns.
    player = next(turns)


async def main():
    async with serve(handler, "", 8001):
        await asyncio.get_running_loop().create_future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())