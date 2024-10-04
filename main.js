import { createBoard, playMove } from "./connect4.js";

const IPaddress = "197.163.56.124";

function initGame(websocket) {
  websocket.addEventListener("open", () => {
    // Send an "init" event according to who is connecting.
    // get the URL parameters
    const params = new URLSearchParams(window.location.search);
    let event = { type: "init"};
    if (params.has("join")) {
      // Player 2 joins the game.
      event.join = params.get("join");
    } else {
      // Player 1 creates the game.
    }
    websocket.send(JSON.stringify(event));
  });
}

// when the page loads -> someone connects to the server
window.addEventListener("DOMContentLoaded", () => {
  // Initialize the UI.
  const board = document.querySelector(".board");
  createBoard(board);

  // Websocket initialization
  // Open the WebSocket connection and register event handlers.
  const websocket = new WebSocket("ws://localhost:8001/");

  initGame(websocket);
  receiveMoves(board, websocket);
  sendMoves(board, websocket);
});

function sendMoves(board, websocket) {
  // When clicking a column, send a "play" event for a move in that column.
  board.addEventListener("click", ({ target }) => {
    const column = target.dataset.column;
    // Ignore clicks outside a column.
    if (column === undefined) {
      return;
    }
    const event = {
      type: "play",
      column: parseInt(column, 10),
    };
    websocket.send(JSON.stringify(event));
  });
}

function showMessage(message) {
  window.setTimeout(() => window.alert(message), 50);
}

function receiveMoves(board, websocket) {
  websocket.addEventListener("message", ({ data }) => {
    // turn JSON into js object type; JSON parse
    const event = JSON.parse(data);
    switch (event.type) {
      case "init":
        // Create a link for inviting Player2
        const link = `${IPaddress}:8000/?join=${event.join}`;
        document.querySelector(".join").value = `${link}`;
        showMessage(`Send this link to Player2: ${link}`);
        break;
      case "play":
        // Update the UI with the move.
        playMove(board, event.player, event.column, event.row);
        break;
      case "win":
        showMessage(`Player ${event.player} wins!`);
        // No further messages are expected; close the WebSocket connection.
        websocket.close(1000);
        break;
      case "error":
        showMessage(event.message);
        break;
      case "player joined":
        document.querySelector(".join").classList.add("hidden");
        break;
      default:
        throw new Error(`Unsupported event type: ${event.type}.`);
    }
  });
}

const linkBtn = document.querySelector(".join");
linkBtn.addEventListener("click", () => {
  console.log("Button clicked " + linkBtn);

  // Copy the text inside the text field
  navigator.clipboard.writeText(linkBtn.value);

  // Alert the copied text
  alert("Copied the text: " + linkBtn.value);
});