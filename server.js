const express = require("express");
const cors = require("cors");
const {v4: uuidv4} = require("uuid");
const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");

const app = express();
app.use(cors());
app.use(express.json());

// Swagger definition
const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Battleship Game API",
      version: "1.0.0",
      description: "Local 2-player Battleship game API for hot-seat gaming",
      contact: {
        name: "Battleship Team",
      },
    },
    servers: [
      {
        url: "http://localhost:3000",
        description: "Local development server",
      },
    ],
    tags: [
      {
        name: "Game",
        description: "Game management endpoints",
      },
      {
        name: "Config",
        description: "Configuration endpoints",
      },
    ],
  },
  apis: ["./server.js"],
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use("/api-docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Local game storage
const games = new Map();

// Default ship configurations
const DEFAULT_SHIPS = {
  carrier: {name: "Carrier", size: 5, color: "#FF6B6B"},
  battleship: {name: "Battleship", size: 4, color: "#4ECDC4"},
  cruiser: {name: "Cruiser", size: 3, color: "#45B7D1"},
  submarine: {name: "Submarine", size: 3, color: "#FFA07A"},
  destroyer: {name: "Destroyer", size: 2, color: "#98D8C8"},
};

const BOARD_SIZE = 10;

// Helper functions
function createEmptyBoard() {
  return Array(BOARD_SIZE)
    .fill(null)
    .map(() => Array(BOARD_SIZE).fill(null));
}

function validateShipPlacement(board, shipSize, x, y, isHorizontal) {
  if (isHorizontal) {
    if (x + shipSize > BOARD_SIZE || y >= BOARD_SIZE) return false;
  } else {
    if (x >= BOARD_SIZE || y + shipSize > BOARD_SIZE) return false;
  }

  for (let i = 0; i < shipSize; i++) {
    const checkX = isHorizontal ? x + i : x;
    const checkY = isHorizontal ? y : y + i;
    if (board[checkY][checkX] !== null) return false;
  }

  return true;
}

function placeShip(board, shipId, shipSize, x, y, isHorizontal) {
  for (let i = 0; i < shipSize; i++) {
    const placeX = isHorizontal ? x + i : x;
    const placeY = isHorizontal ? y : y + i;
    board[placeY][placeX] = shipId;
  }
}

function checkAllShipsSunk(board, hitBoard) {
  for (let y = 0; y < BOARD_SIZE; y++) {
    for (let x = 0; x < BOARD_SIZE; x++) {
      if (board[y][x] !== null && !hitBoard[y][x]) {
        return false;
      }
    }
  }
  return true;
}

// API Endpoints

/**
 * @swagger
 * /api/health:
 *   get:
 *     summary: Health check endpoint
 *     tags: [Config]
 *     responses:
 *       200:
 *         description: API is running
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: ok
 *                 mode:
 *                   type: string
 *                   example: local
 *                 games:
 *                   type: number
 *                   example: 3
 */
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    mode: "local",
    games: games.size,
  });
});

/**
 * @swagger
 * /api/config:
 *   get:
 *     summary: Get game configuration
 *     tags: [Config]
 *     description: Returns board size and available ships
 *     responses:
 *       200:
 *         description: Game configuration
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 boardSize:
 *                   type: number
 *                   example: 10
 *                 ships:
 *                   type: object
 *                   additionalProperties:
 *                     type: object
 *                     properties:
 *                       name:
 *                         type: string
 *                       size:
 *                         type: number
 *                       color:
 *                         type: string
 */
app.get("/api/config", (req, res) => {
  res.json({
    boardSize: BOARD_SIZE,
    ships: DEFAULT_SHIPS,
  });
});

/**
 * @swagger
 * /api/game/create:
 *   post:
 *     summary: Create a new local game
 *     tags: [Game]
 *     description: Creates a new game for 2 local players on the same device
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               player1Name:
 *                 type: string
 *                 example: Admiral
 *               player2Name:
 *                 type: string
 *                 example: Captain
 *     responses:
 *       200:
 *         description: Game created successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 gameId:
 *                   type: string
 *                   format: uuid
 *                 game:
 *                   type: object
 */
app.post("/api/game/create", (req, res) => {
  const {player1Name, player2Name} = req.body;

  const gameId = uuidv4();
  const game = {
    id: gameId,
    player1: {
      name: player1Name || "Player 1",
      board: createEmptyBoard(),
      hitBoard: createEmptyBoard(),
      ships: {},
      ready: false,
      shots: 0,
      hits: 0,
    },
    player2: {
      name: player2Name || "Player 2",
      board: createEmptyBoard(),
      hitBoard: createEmptyBoard(),
      ships: {},
      ready: false,
      shots: 0,
      hits: 0,
    },
    currentTurn: "player1",
    status: "setup",
    winner: null,
    ships: DEFAULT_SHIPS,
    createdAt: Date.now(),
  };

  games.set(gameId, game);
  res.json({gameId, game});
});

/**
 * @swagger
 * /api/game/{gameId}:
 *   get:
 *     summary: Get game state
 *     tags: [Game]
 *     description: Get the complete game state (admin view)
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *         description: Game ID
 *     responses:
 *       200:
 *         description: Game state
 *       404:
 *         description: Game not found
 */
app.get("/api/game/:gameId", (req, res) => {
  const game = games.get(req.params.gameId);
  if (!game) {
    return res.status(404).json({error: "Game not found"});
  }
  res.json({game});
});

/**
 * @swagger
 * /api/game/{gameId}/{player}/ships:
 *   post:
 *     summary: Place ships for a player
 *     tags: [Game]
 *     description: Place all ships on the board for player1 or player2
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *       - in: path
 *         name: player
 *         required: true
 *         schema:
 *           type: string
 *           enum: [player1, player2]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               ships:
 *                 type: array
 *                 items:
 *                   type: object
 *                   properties:
 *                     shipId:
 *                       type: string
 *                       example: carrier
 *                     x:
 *                       type: number
 *                       example: 0
 *                     y:
 *                       type: number
 *                       example: 0
 *                     isHorizontal:
 *                       type: boolean
 *                       example: true
 *     responses:
 *       200:
 *         description: Ships placed successfully
 *       400:
 *         description: Invalid ship placement
 *       404:
 *         description: Game not found
 */
app.post("/api/game/:gameId/:player/ships", (req, res) => {
  const {ships} = req.body;
  const game = games.get(req.params.gameId);
  const player = req.params.player;

  if (!game) {
    return res.status(404).json({error: "Game not found"});
  }

  if (player !== "player1" && player !== "player2") {
    return res.status(400).json({error: "Invalid player"});
  }

  const playerData = game[player];
  const newBoard = createEmptyBoard();
  const placedShips = {};

  for (const shipData of ships) {
    const shipConfig = game.ships[shipData.shipId];

    if (!shipConfig) {
      return res.status(400).json({error: `Invalid ship: ${shipData.shipId}`});
    }

    if (placedShips[shipData.shipId]) {
      return res
        .status(400)
        .json({error: `Ship ${shipData.shipId} already placed`});
    }

    if (
      !validateShipPlacement(
        newBoard,
        shipConfig.size,
        shipData.x,
        shipData.y,
        shipData.isHorizontal
      )
    ) {
      return res
        .status(400)
        .json({error: `Invalid placement for ${shipConfig.name}`});
    }

    placeShip(
      newBoard,
      shipData.shipId,
      shipConfig.size,
      shipData.x,
      shipData.y,
      shipData.isHorizontal
    );
    placedShips[shipData.shipId] = shipData;
  }

  if (Object.keys(placedShips).length !== Object.keys(game.ships).length) {
    return res.status(400).json({error: "Not all ships placed"});
  }

  playerData.board = newBoard;
  playerData.ships = placedShips;
  playerData.ready = true;

  if (game.player1.ready && game.player2.ready) {
    game.status = "playing";
  }

  res.json({
    success: true,
    ready: playerData.ready,
    gameStatus: game.status,
    bothReady: game.player1.ready && game.player2.ready,
  });
});

/**
 * @swagger
 * /api/game/{gameId}/{player}/attack:
 *   post:
 *     summary: Attack opponent
 *     tags: [Game]
 *     description: Attack a position on opponent's board
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *       - in: path
 *         name: player
 *         required: true
 *         schema:
 *           type: string
 *           enum: [player1, player2]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - x
 *               - y
 *             properties:
 *               x:
 *                 type: number
 *                 minimum: 0
 *                 maximum: 9
 *                 example: 5
 *               y:
 *                 type: number
 *                 minimum: 0
 *                 maximum: 9
 *                 example: 3
 *     responses:
 *       200:
 *         description: Attack processed
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 hit:
 *                   type: boolean
 *                 shipId:
 *                   type: string
 *                 shipName:
 *                   type: string
 *                 sunk:
 *                   type: boolean
 *                 gameOver:
 *                   type: boolean
 *                 winner:
 *                   type: string
 *                 nextTurn:
 *                   type: string
 *       400:
 *         description: Invalid attack
 *       404:
 *         description: Game not found
 */
app.post("/api/game/:gameId/:player/attack", (req, res) => {
  const {x, y} = req.body;
  const game = games.get(req.params.gameId);
  const attackingPlayer = req.params.player;

  if (!game) {
    return res.status(404).json({error: "Game not found"});
  }

  if (game.status !== "playing") {
    return res.status(400).json({error: "Game not in playing state"});
  }

  if (game.currentTurn !== attackingPlayer) {
    return res.status(400).json({error: "Not your turn"});
  }

  const opponent = attackingPlayer === "player1" ? game.player2 : game.player1;
  const attacker = game[attackingPlayer];

  if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) {
    return res.status(400).json({error: "Invalid coordinates"});
  }

  if (opponent.hitBoard[y][x] !== null) {
    return res.status(400).json({error: "Already attacked this position"});
  }

  attacker.shots++;
  const isHit = opponent.board[y][x] !== null;
  opponent.hitBoard[y][x] = isHit;

  if (isHit) {
    attacker.hits++;
  }

  const hitShipId = isHit ? opponent.board[y][x] : null;
  const hitShipConfig = hitShipId ? game.ships[hitShipId] : null;

  let isSunk = false;
  if (isHit) {
    isSunk = true;
    for (let py = 0; py < BOARD_SIZE; py++) {
      for (let px = 0; px < BOARD_SIZE; px++) {
        if (
          opponent.board[py][px] === hitShipId &&
          !opponent.hitBoard[py][px]
        ) {
          isSunk = false;
          break;
        }
      }
      if (!isSunk) break;
    }
  }

  const allSunk = checkAllShipsSunk(opponent.board, opponent.hitBoard);
  if (allSunk) {
    game.status = "finished";
    game.winner = attackingPlayer;
  } else {
    game.currentTurn = attackingPlayer === "player1" ? "player2" : "player1";
  }

  res.json({
    hit: isHit,
    shipId: hitShipId,
    shipName: hitShipConfig ? hitShipConfig.name : null,
    sunk: isSunk,
    gameOver: allSunk,
    winner: game.winner,
    nextTurn: game.currentTurn,
  });
});

/**
 * @swagger
 * /api/game/{gameId}/{player}/view:
 *   get:
 *     summary: Get player view
 *     tags: [Game]
 *     description: Get game state from player's perspective (hides opponent ships)
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *       - in: path
 *         name: player
 *         required: true
 *         schema:
 *           type: string
 *           enum: [player1, player2]
 *     responses:
 *       200:
 *         description: Player view of game state
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 game:
 *                   type: object
 *                 player:
 *                   type: object
 *                 opponent:
 *                   type: object
 *       404:
 *         description: Game not found
 */
app.get("/api/game/{gameId}/{player}/view", (req, res) => {
  const game = games.get(req.params.gameId);
  const player = req.params.player;

  if (!game) {
    return res.status(404).json({error: "Game not found"});
  }

  if (player !== "player1" && player !== "player2") {
    return res.status(400).json({error: "Invalid player"});
  }

  const playerData = game[player];
  const opponentKey = player === "player1" ? "player2" : "player1";
  const opponentData = game[opponentKey];

  res.json({
    game: {
      id: game.id,
      status: game.status,
      currentTurn: game.currentTurn,
      isMyTurn: game.currentTurn === player,
      winner: game.winner,
      ships: game.ships,
    },
    player: {
      name: playerData.name,
      board: playerData.board,
      hitBoard: playerData.hitBoard,
      ships: playerData.ships,
      ready: playerData.ready,
      shots: playerData.shots,
      hits: playerData.hits,
    },
    opponent: {
      name: opponentData.name,
      hitBoard: opponentData.hitBoard,
      ready: opponentData.ready,
      shots: opponentData.shots,
      hits: opponentData.hits,
    },
  });
});

/**
 * @swagger
 * /api/game/{gameId}:
 *   delete:
 *     summary: Delete a game
 *     tags: [Game]
 *     description: Delete a game from the server
 *     parameters:
 *       - in: path
 *         name: gameId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: Game deleted
 *       404:
 *         description: Game not found
 */
app.delete("/api/game/:gameId", (req, res) => {
  const deleted = games.delete(req.params.gameId);
  if (!deleted) {
    return res.status(404).json({error: "Game not found"});
  }
  res.json({success: true});
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚢 Battleship LOCAL API running on port ${PORT}`);
  console.log(`📍 Health: http://localhost:${PORT}/api/health`);
  console.log(`📚 Swagger UI: http://localhost:${PORT}/api-docs`);
  console.log(`🎮 Local 2-player mode - Hot seat gaming!`);
});
