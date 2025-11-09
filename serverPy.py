"""
Battleship Game API with Custom Ships, Achievements, and Spells
Run with: uvicorn battleship_api:app --reload
Access Swagger UI at: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
import uuid
from datetime import datetime

app = FastAPI(
    title="Battleship Game API",
    description="Multi-player Battleship game API with custom ships, spells, and achievements",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= ENUMS =============
class CellState(str, Enum):
    EMPTY = "empty"
    SHIP = "ship"
    HIT = "hit"
    MISS = "miss"
    NUKED = "nuked"

class GameStatus(str, Enum):
    SETUP = "setup"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class SpellType(str, Enum):
    NUKE = "nuke"  # 3x3 area damage
    SONAR = "sonar"  # Reveal if ship exists in 5x5 area
    AIRSTRIKE = "airstrike"  # Full row or column
    REPAIR = "repair"  # Restore one ship cell

class AchievementType(str, Enum):
    FIRST_BLOOD = "first_blood"
    LUCKY_SHOT = "lucky_shot"  # Random hit
    SHARPSHOOTER = "sharpshooter"  # 5 hits in a row
    ANNIHILATOR = "annihilator"  # Sink all ships
    SPELL_MASTER = "spell_master"  # Use 3 different spells
    PERFECT_GAME = "perfect_game"  # Win without losing a ship

# ============= MODELS =============
class Position(BaseModel):
    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")

class Ship(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    positions: List[Position]
    hits: List[Position] = []
    is_sunk: bool = False

class Spell(BaseModel):
    type: SpellType
    uses_remaining: int

class Achievement(BaseModel):
    type: AchievementType
    name: str
    description: str
    earned_at: Optional[datetime] = None
    player_id: Optional[str] = None

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    board_size: int
    board: List[List[CellState]] = []
    ships: List[Ship] = []
    spells: List[Spell] = []
    achievements: List[Achievement] = []
    is_ready: bool = False
    consecutive_hits: int = 0

class GameConfig(BaseModel):
    board_size: int = Field(default=10, ge=5, le=20)
    max_players: int = Field(default=2, ge=2, le=4)
    allow_custom_ships: bool = True
    initial_spells: List[SpellType] = [SpellType.NUKE, SpellType.SONAR]

class Game(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: GameConfig
    players: List[Player] = []
    current_player_index: int = 0
    status: GameStatus = GameStatus.SETUP
    winner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class CreateGameRequest(BaseModel):
    config: GameConfig

class JoinGameRequest(BaseModel):
    player_name: str

class PlaceShipRequest(BaseModel):
    ship_name: str
    positions: List[Position]

class PlaceShipsRequest(BaseModel):
    ships: List[PlaceShipRequest]

class AttackRequest(BaseModel):
    position: Position

class UseSpellRequest(BaseModel):
    spell_type: SpellType
    target_position: Position

class AttackResponse(BaseModel):
    hit: bool
    sunk_ship: Optional[str] = None
    achievement_earned: Optional[Achievement] = None
    affected_positions: List[Position] = []

# ============= STORAGE =============
games: Dict[str, Game] = {}

# ============= HELPER FUNCTIONS =============
def create_empty_board(size: int) -> List[List[CellState]]:
    return [[CellState.EMPTY for _ in range(size)] for _ in range(size)]

def is_valid_position(pos: Position, board_size: int) -> bool:
    return 0 <= pos.x < board_size and 0 <= pos.y < board_size

def check_ship_placement(ship_positions: List[Position], existing_ships: List[Ship], board_size: int) -> bool:
    # Check all positions are valid
    for pos in ship_positions:
        if not is_valid_position(pos, board_size):
            return False
    
    # Check no overlap with existing ships
    existing_positions = set()
    for ship in existing_ships:
        for pos in ship.positions:
            existing_positions.add((pos.x, pos.y))
    
    for pos in ship_positions:
        if (pos.x, pos.y) in existing_positions:
            return False
    
    return True

def update_board(player: Player):
    player.board = create_empty_board(player.board_size)
    for ship in player.ships:
        for pos in ship.positions:
            if pos in ship.hits:
                player.board[pos.y][pos.x] = CellState.HIT
            else:
                player.board[pos.y][pos.x] = CellState.SHIP

def check_achievement(player: Player, achievement_type: AchievementType):
    if any(a.type == achievement_type for a in player.achievements):
        return None
    
    achievement_data = {
        AchievementType.FIRST_BLOOD: ("First Blood", "Hit an enemy ship for the first time"),
        AchievementType.LUCKY_SHOT: ("Lucky Shot", "Hit a ship on your first try in a game"),
        AchievementType.SHARPSHOOTER: ("Sharpshooter", "Land 5 consecutive hits"),
        AchievementType.ANNIHILATOR: ("Annihilator", "Sink all enemy ships"),
        AchievementType.SPELL_MASTER: ("Spell Master", "Use 3 different types of spells"),
        AchievementType.PERFECT_GAME: ("Perfect Game", "Win without losing any ships"),
    }
    
    name, desc = achievement_data[achievement_type]
    achievement = Achievement(
        type=achievement_type,
        name=name,
        description=desc,
        earned_at=datetime.now(),
        player_id=player.id
    )
    player.achievements.append(achievement)
    return achievement

def apply_nuke(game: Game, target_player: Player, center: Position) -> List[Position]:
    affected = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            x, y = center.x + dx, center.y + dy
            if is_valid_position(Position(x=x, y=y), target_player.board_size):
                pos = Position(x=x, y=y)
                affected.append(pos)
                for ship in target_player.ships:
                    if pos in ship.positions and pos not in ship.hits:
                        ship.hits.append(pos)
                        if len(ship.hits) == len(ship.positions):
                            ship.is_sunk = True
    return affected

def apply_sonar(target_player: Player, center: Position) -> bool:
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            x, y = center.x + dx, center.y + dy
            if is_valid_position(Position(x=x, y=y), target_player.board_size):
                for ship in target_player.ships:
                    if Position(x=x, y=y) in ship.positions:
                        return True
    return False

def apply_airstrike(target_player: Player, pos: Position, is_row: bool) -> List[Position]:
    affected = []
    if is_row:
        for x in range(target_player.board_size):
            p = Position(x=x, y=pos.y)
            affected.append(p)
            for ship in target_player.ships:
                if p in ship.positions and p not in ship.hits:
                    ship.hits.append(p)
                    if len(ship.hits) == len(ship.positions):
                        ship.is_sunk = True
    else:
        for y in range(target_player.board_size):
            p = Position(x=pos.x, y=y)
            affected.append(p)
            for ship in target_player.ships:
                if p in ship.positions and p not in ship.hits:
                    ship.hits.append(p)
                    if len(ship.hits) == len(ship.positions):
                        ship.is_sunk = True
    return affected

# ============= API ENDPOINTS =============

@app.get("/")
def root():
    return {"message": "Battleship Game API", "docs": "/docs"}

@app.post("/games", response_model=Game)
def create_game(request: CreateGameRequest):
    """Create a new game with custom configuration"""
    game = Game(config=request.config)
    games[game.id] = game
    return game

@app.get("/games", response_model=List[Game])
def list_games():
    """List all active games"""
    return list(games.values())

@app.get("/games/{game_id}", response_model=Game)
def get_game(game_id: str):
    """Get game details"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]

@app.post("/games/{game_id}/join", response_model=Player)
def join_game(game_id: str, request: JoinGameRequest):
    """Join an existing game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if len(game.players) >= game.config.max_players:
        raise HTTPException(status_code=400, detail="Game is full")
    
    if game.status != GameStatus.SETUP:
        raise HTTPException(status_code=400, detail="Game already started")
    
    player = Player(
        name=request.player_name,
        board_size=game.config.board_size,
        board=create_empty_board(game.config.board_size)
    )
    
    # Initialize spells
    for spell_type in game.config.initial_spells:
        player.spells.append(Spell(type=spell_type, uses_remaining=1))
    
    game.players.append(player)
    
    return player

@app.post("/games/{game_id}/players/{player_id}/ships")
def place_ships(game_id: str, player_id: str, request: PlaceShipsRequest):
    """Place multiple ships on the board"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    player = next((p for p in game.players if p.id == player_id), None)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if game.status != GameStatus.SETUP:
        raise HTTPException(status_code=400, detail="Cannot place ships after game started")
    
    for ship_data in request.ships:
        if not check_ship_placement(ship_data.positions, player.ships, player.board_size):
            raise HTTPException(status_code=400, detail=f"Invalid placement for ship {ship_data.ship_name}")
        
        ship = Ship(name=ship_data.ship_name, positions=ship_data.positions)
        player.ships.append(ship)
    
    update_board(player)
    
    return {"message": "Ships placed successfully", "ships": player.ships}

@app.post("/games/{game_id}/players/{player_id}/ready")
def set_player_ready(game_id: str, player_id: str):
    """Mark player as ready to start the game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    player = next((p for p in game.players if p.id == player_id), None)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if not player.ships:
        raise HTTPException(status_code=400, detail="Must place at least one ship")
    
    player.is_ready = True
    
    # Check if all players are ready
    if all(p.is_ready for p in game.players) and len(game.players) >= 2:
        game.status = GameStatus.IN_PROGRESS
    
    return {"message": "Player ready", "game_status": game.status}

@app.post("/games/{game_id}/attack", response_model=AttackResponse)
def attack(game_id: str, attacker_id: str, target_id: str, request: AttackRequest):
    """Attack opponent's position"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Game not in progress")
    
    attacker = next((p for p in game.players if p.id == attacker_id), None)
    target = next((p for p in game.players if p.id == target_id), None)
    
    if not attacker or not target:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if game.players[game.current_player_index].id != attacker_id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    pos = request.position
    if not is_valid_position(pos, target.board_size):
        raise HTTPException(status_code=400, detail="Invalid position")
    
    hit = False
    sunk_ship_name = None
    achievement = None
    
    # Check if hit
    for ship in target.ships:
        if pos in ship.positions and pos not in ship.hits:
            ship.hits.append(pos)
            hit = True
            attacker.consecutive_hits += 1
            
            # Check achievements
            if not any(a.type == AchievementType.FIRST_BLOOD for a in attacker.achievements):
                achievement = check_achievement(attacker, AchievementType.FIRST_BLOOD)
            
            if attacker.consecutive_hits == 1 and sum(len(s.hits) for s in target.ships) == 1:
                check_achievement(attacker, AchievementType.LUCKY_SHOT)
            
            if attacker.consecutive_hits >= 5:
                achievement = check_achievement(attacker, AchievementType.SHARPSHOOTER)
            
            if len(ship.hits) == len(ship.positions):
                ship.is_sunk = True
                sunk_ship_name = ship.name
            
            break
    
    if not hit:
        attacker.consecutive_hits = 0
    
    # Check if all ships sunk
    if all(ship.is_sunk for ship in target.ships):
        game.status = GameStatus.FINISHED
        game.winner_id = attacker_id
        achievement = check_achievement(attacker, AchievementType.ANNIHILATOR)
        
        # Check perfect game
        if not any(ship.hits for ship in attacker.ships):
            check_achievement(attacker, AchievementType.PERFECT_GAME)
    
    # Next player turn
    game.current_player_index = (game.current_player_index + 1) % len(game.players)
    
    return AttackResponse(
        hit=hit,
        sunk_ship=sunk_ship_name,
        achievement_earned=achievement,
        affected_positions=[pos]
    )

@app.post("/games/{game_id}/spell", response_model=AttackResponse)
def use_spell(game_id: str, caster_id: str, target_id: str, request: UseSpellRequest):
    """Use a spell on opponent"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    caster = next((p for p in game.players if p.id == caster_id), None)
    target = next((p for p in game.players if p.id == target_id), None)
    
    if not caster or not target:
        raise HTTPException(status_code=404, detail="Player not found")
    
    spell = next((s for s in caster.spells if s.type == request.spell_type and s.uses_remaining > 0), None)
    if not spell:
        raise HTTPException(status_code=400, detail="Spell not available")
    
    spell.uses_remaining -= 1
    affected = []
    hit = False
    
    if request.spell_type == SpellType.NUKE:
        affected = apply_nuke(game, target, request.target_position)
        hit = len(affected) > 0
    elif request.spell_type == SpellType.SONAR:
        has_ship = apply_sonar(target, request.target_position)
        return AttackResponse(hit=has_ship, affected_positions=[])
    elif request.spell_type == SpellType.AIRSTRIKE:
        # Randomly choose row or column
        affected = apply_airstrike(target, request.target_position, True)
        hit = len(affected) > 0
    
    # Check spell master achievement
    used_spells = set(s.type for s in caster.spells if s.uses_remaining == 0)
    if len(used_spells) >= 3:
        check_achievement(caster, AchievementType.SPELL_MASTER)
    
    update_board(target)
    
    return AttackResponse(hit=hit, affected_positions=affected)

@app.get("/games/{game_id}/players/{player_id}/achievements", response_model=List[Achievement])
def get_achievements(game_id: str, player_id: str):
    """Get player achievements"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    player = next((p for p in game.players if p.id == player_id), None)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player.achievements

@app.delete("/games/{game_id}")
def delete_game(game_id: str):
    """Delete a game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    del games[game_id]
    return {"message": "Game deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)