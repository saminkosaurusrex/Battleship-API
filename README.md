# Disclaimer

Everything AI generated even this
JS API = shit API

#

Try index.html

- only for PY API
- don't forget to change PORT

# ⚓ Battleship Game API (Node.js)

Local 2-player Battleship game API for hot-seat gaming.

---

## 🚀 Ako spustiť

### 1. Nainštaluj Node.js knižnice

```bash
npm install express cors uuid swagger-ui-express swagger-jsdoc
```

Alebo ak máš `package.json`:

```bash
npm install
```

### 2. Spusti server

```bash
node server.js
```

### 3. Otvor Swagger UI

Choď v prehliadači na:

```
http://localhost:3000/api-docs
```

**To je všetko!** 🎉

---

## 📖 Ako používať Swagger UI

Swagger UI sa **automaticky zapne** keď spustíš server.

### Kde to nájdem?

```
http://localhost:3000/api-docs
```

### Health check:

```
http://localhost:3000/api/health
```

### Ako to používať?

1. **Klikni na endpoint** (napr. `POST /api/game/create`)
2. **Klikni "Try it out"**
3. **Vyplň JSON** (alebo použi ukážkový)
4. **Klikni "Execute"**
5. **Vidíš odpoveď** nižšie

### Príklad: Vytvor hru

1. Otvor `http://localhost:3000/api-docs`
2. Klikni na **POST /api/game/create**
3. Klikni **"Try it out"**
4. Do Request body vlož:

```json
{
  "player1Name": "Admiral",
  "player2Name": "Captain"
}
```

5. Klikni **Execute**
6. Skopíruj `gameId` z odpovede

---

## 🎮 Workflow hry

```
1. POST /api/game/create              → Vytvor hru (dostaneš gameId)
2. POST /api/game/{id}/{player}/ships → Umiestni lode pre hráča
3. POST /api/game/{id}/{player}/attack → Útok
4. GET  /api/game/{id}/{player}/view  → Stav hry pre hráča
5. GET  /api/game/{id}                → Kompletný stav hry (admin)
```

---

## 📋 Príklady endpointov

### Vytvorenie hry

```bash
POST http://localhost:3000/api/game/create
Content-Type: application/json

{
  "player1Name": "Hráč 1",
  "player2Name": "Hráč 2"
}
```

### Umiestnenie lodí

```bash
POST http://localhost:3000/api/game/{gameId}/player1/ships
Content-Type: application/json

{
  "ships": [
    {
      "shipId": "carrier",
      "x": 0,
      "y": 0,
      "isHorizontal": true
    },
    {
      "shipId": "battleship",
      "x": 0,
      "y": 2,
      "isHorizontal": false
    }
  ]
}
```

### Útok

```bash
POST http://localhost:3000/api/game/{gameId}/player1/attack
Content-Type: application/json

{
  "x": 5,
  "y": 3
}
```

---

## 🛡️ Dostupné lode

| Loď        | Veľkosť | ID           |
| ---------- | ------- | ------------ |
| Carrier    | 5       | `carrier`    |
| Battleship | 4       | `battleship` |
| Cruiser    | 3       | `cruiser`    |
| Submarine  | 3       | `submarine`  |
| Destroyer  | 2       | `destroyer`  |

---

## 🐛 Problémy?

### "Port 3000 is already in use"

```bash
PORT=3001 node server.js
```

Potom: `http://localhost:3001/api-docs`

### "Cannot find module"

```bash
npm install express cors uuid swagger-ui-express swagger-jsdoc
```

### Swagger UI sa nenačíta

Skontroluj či server beží:

```bash
curl http://localhost:3000/api/health
```

Malo by vrátiť: `{"status":"ok","mode":"local","games":0}`

---

## 📦 Dependencies (package.json)

```json
{
  "name": "battleship-api",
  "version": "1.0.0",
  "description": "Battleship Game API",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "uuid": "^9.0.0",
    "swagger-ui-express": "^5.0.0",
    "swagger-jsdoc": "^6.2.8"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}
```

---

## 🎯 Game Modes

Toto API je pre **hot-seat gaming** - dvaja hráči na jednom zariadení sa striedajú.

### Stavy hry:

- `setup` - umiestnenie lodí
- `playing` - hra prebieha
- `finished` - hra skončená

---

## 🔗 Endpoints Overview

| Method | Endpoint                         | Popis             |
| ------ | -------------------------------- | ----------------- |
| GET    | `/api/health`                    | Health check      |
| GET    | `/api/config`                    | Board size a lode |
| POST   | `/api/game/create`               | Vytvor hru        |
| GET    | `/api/game/{id}`                 | Stav hry (admin)  |
| POST   | `/api/game/{id}/{player}/ships`  | Umiestni lode     |
| POST   | `/api/game/{id}/{player}/attack` | Útok              |
| GET    | `/api/game/{id}/{player}/view`   | Stav pre hráča    |
| DELETE | `/api/game/{id}`                 | Zmaž hru          |

---

**Happy coding! ⚓🎮**

# ⚓ Battleship Game API(PY)

REST API pre hru Battleship s vlastnými loďami, achievementami a kúzlami.

---

## 🚀 Ako spustiť

### 1. Nainštaluj Python knižnice

```bash
pip install fastapi uvicorn pydantic
```

### 2. Spusti server

```bash
uvicorn battleship_api:app --reload
```

### 3. Otvor Swagger UI

Choď v prehliadači na:

```
http://localhost:8000/docs
```

**To je všetko!** 🎉

---

## 📖 Ako používať Swagger UI

Swagger UI sa **automaticky zapne** keď spustíš server. Nemusíš nič nastavovať.

### Kde to nájdem?

```
http://localhost:8000/docs
```

### Ako to používať?

1. **Klikni na endpoint** (napr. `POST /games`)
2. **Klikni "Try it out"**
3. **Vyplň JSON** (alebo použi ukážkový)
4. **Klikni "Execute"**
5. **Vidíš odpoveď** nižšie

### Príklad: Vytvor hru

1. Otvor `http://localhost:8000/docs`
2. Klikni na **POST /games**
3. Klikni **"Try it out"**
4. Do Request body vlož:

```json
{
  "config": {
    "board_size": 10,
    "max_players": 2,
    "allow_custom_ships": true,
    "initial_spells": ["nuke", "sonar"]
  }
}
```

5. Klikni **Execute**
6. Skopíruj `id` z odpovede

---

## 🎮 Workflow hry

```
1. POST /games                    → Vytvor hru (dostaneš game_id)
2. POST /games/{id}/join          → Pripoj hráčov (dostaneš player_id)
3. POST /games/{id}/players/{pid}/ships  → Umiestni lode
4. POST /games/{id}/players/{pid}/ready  → Som pripravený
5. POST /games/{id}/attack        → Útočím
6. GET  /games/{id}               → Skontroluj stav hry
```

---

## 🐛 Problémy?

### "Port 8000 is already in use"

```bash
uvicorn battleship_api:app --reload --port 8001
```

Potom: `http://localhost:8001/docs`

### "Module not found"

```bash
pip install fastapi uvicorn pydantic
```

### Swagger UI sa nenačíta

Skontroluj či server beží:

```bash
curl http://localhost:8000
```

Malo by vrátiť: `{"message":"Battleship Game API","docs":"/docs"}`

---

## 📦 Čo potrebuješ

- Python 3.8+
- 3 knižnice: `fastapi`, `uvicorn`, `pydantic`

---

## 🎯 Web UI Demo

Otvor `battleship.html` v prehliadači a hraj!

---

**Happy coding! ⚓**
