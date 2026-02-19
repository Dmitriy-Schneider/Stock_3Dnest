# Stock-3DNest — Warehouse Management & Intelligent 3D Cutting System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production-success.svg)

**Integrated warehouse management system with intelligent 3D cutting optimization**

[Demo](#demo) | [Installation](#installation) | [API](#api) | [Architecture](#architecture)

</div>

---

## About

**Stock-3DNest** is a production system for metalworking enterprises, combining warehouse management with intelligent 3D cutting algorithms.

### Problems Solved

- **Material Search**: bandsaw operators quickly find suitable stock in the warehouse
- **Optimal Cutting**: algorithm calculates optimal cutting scheme with minimal waste
- **Visualization**: 3D model of cutting scheme for clear understanding of cut sequence
- **Mobility**: access via Telegram bot directly from the shop floor

### Key Features

| Feature | Description |
|---------|-------------|
| Auto Parsing | Import from 1C exports (Excel) to SQLite on startup |
| Smart Search | Filter by profile type, steel grade, dimensions |
| 3D Visualization | Interactive cutting scheme (Three.js) |
| REST API | Integration with external systems |
| Docker-ready | One-command deployment |

---

## Demo

### Warehouse Web Interface

Adaptive interface for searching and filtering metal stock:

![Warehouse Interface](docs/images/warehouse_main.png)

### 3D Cutting Visualization

Interactive 3D model with rotation and zoom:

![3D Cutting](docs/images/cutting_3d.png)

### Telegram Bot

Access system features via messenger:

![Telegram Bot](docs/images/telegram_bot.png)

---

## Architecture

The system consists of three modules:

```
+------------------------------------------------------------------+
|                        Stock-3DNest                               |
+-----------------+---------------------+--------------------------+
|    Module 1     |      Module 2       |       Module 3           |
|   WAREHOUSE     |    3D CUTTING       |    TELEGRAM BOT          |
|  (Open Source)  |  (Intellectual      |   (Intellectual          |
|                 |   Property)         |    Property)             |
+-----------------+---------------------+--------------------------+
| * Excel parser  | * Guillotine Bin    | * aiogram 3              |
| * SQLite DB     |   Packing algorithm | * PDF reports            |
| * REST API      | * Three.js          | * GPT integration        |
| * Web UI        |   visualization     | * FSM dialogs            |
+-----------------+---------------------+--------------------------+
```

### Module 1 — Warehouse (Open Source)

Web interface for managing and searching stock:

- **Excel Parsing** — automatic import from 1C exports (.xlsx)
- **Smart Search** — filter by profile type, steel grade, dimensions
- **Auto-detection** — automatic selection of current file by date
- **REST API** — endpoints for external system integration
- **Adaptive UI** — works on any device

### Module 2 — 3D Cutting (Intellectual Property)

> Source code not published. Principles described below.

Intelligent algorithm for optimal cutting of metal blocks:

- **3D Guillotine Bin Packing** — guillotine cutting algorithm
- **Auto Stock Selection** — choose optimal block from warehouse
- **3D Visualization** — interactive Three.js model
- **Cut Sequence** — step-by-step instructions for operator

### Module 3 — Telegram Bot (Intellectual Property)

> Source code not published. Principles described below.

Telegram bot duplicating Modules 1 and 2 functionality:

- **aiogram 3** — asynchronous framework
- **PDF Reports** — generation with cutting scheme
- **OpenAI GPT** — intelligent query processing
- **FSM** — finite state machine for dialog management

---

## Technologies

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Main language |
| **FastAPI** | REST API server |
| **SQLite** | Database |
| **openpyxl** | Excel parsing |
| **Docker** | Containerization |
| **Three.js** | 3D visualization (Module 2) |
| **aiogram 3** | Telegram bot (Module 3) |
| **OpenAI API** | GPT integration (Module 3) |

---

## Installation

### Docker (recommended)

```bash
# Clone repository
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest

# Create data directory
mkdir -p data/warehouse

# Copy Excel file with stock from 1C
cp /path/to/Warehouse.xlsx data/warehouse/

# Start
docker-compose up -d

# Open in browser: http://localhost:3001/warehouse
```

### Local Installation

```bash
# Clone
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Dependencies
pip install -r requirements-web.txt

# Data
mkdir -p data/warehouse
cp /path/to/Warehouse.xlsx data/warehouse/

# Start
uvicorn server_fastapi:app --host 0.0.0.0 --port 3001

# Open: http://localhost:3001/warehouse
```

---

## API

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/warehouse` | Warehouse web interface |
| GET | `/api/warehouse/items` | List all items |
| GET | `/api/warehouse/items?profile=circle` | Search by profile |
| GET | `/api/warehouse/items?steel_grade=4140` | Search by steel grade |
| POST | `/api/warehouse/sync` | Sync with Excel |
| GET | `/docs` | Swagger UI documentation |

### Example Request

```bash
# Get all circles made of 4140 steel
curl "http://localhost:3001/api/warehouse/items?profile=circle&steel_grade=4140"
```

### Example Response

```json
{
  "items": [
    {
      "id": 1,
      "profile": "Circle",
      "steel_grade": "4140",
      "diameter": 150,
      "length": 3000,
      "quantity": 5,
      "weight": 412.5
    }
  ],
  "total": 1
}
```

---

## Project Structure

```
Stock_3Dnest/
+-- server_fastapi.py         # FastAPI REST API server
+-- warehouse_parser.py       # Excel parser (1C exports)
+-- database.py               # SQLite layer
+-- requirements-web.txt      # Python dependencies
|
+-- static/
|   +-- warehouse.html        # Warehouse UI (Module 1)
|   +-- warehouse.js          # Warehouse UI logic
|   +-- warehouse.css         # Warehouse styles
|   +-- index.html            # 3D cutting UI (Module 2, IP)
|   +-- app.js                # 3D visualization (Module 2, IP)
|
+-- data/
|   +-- warehouse/            # Excel files (not in repo)
|
+-- BotCut/                   # Telegram bot (Module 3, IP)
|   +-- EnvExample.txt        # Environment variables example
|   +-- requirements.txt      # Bot dependencies
|
+-- docker-compose.yml        # Docker Compose config
+-- Dockerfile.web            # Web server Dockerfile
+-- Dockerfile.bot            # Bot Dockerfile
+-- LICENSE                   # MIT License + IP
```

---

## Licensing

### Open Source Components (MIT License)

| Component | Status |
|-----------|--------|
| warehouse_parser.py | Open Source |
| database.py | Open Source |
| server_fastapi.py | Open Source |
| static/warehouse.* | Open Source |
| Docker configuration | Open Source |

### Intellectual Property

| Component | Status |
|-----------|--------|
| server.py (cutting algorithm) | Closed Source |
| static/app.js (3D visualization) | Closed Source |
| BotCut/*.py (Telegram bot) | Closed Source |
| data/warehouse/*.xlsx | Private Data |

Details in [LICENSE](LICENSE) file.

---

## Author

**Dmitriy Schneider** — [@Dmitriy-Schneider](https://github.com/Dmitriy-Schneider)

### Contact

- GitHub: [Dmitriy-Schneider](https://github.com/Dmitriy-Schneider)
- Telegram: on request

---

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) — modern web framework
- [Three.js](https://threejs.org/) — 3D graphics in browser
- [aiogram](https://aiogram.dev/) — asynchronous Telegram bot

---

<div align="center">

**Stock-3DNest** — From 1C export to optimal cutting in seconds

If this project was useful, please give it a star!

Star this repo

</div>
