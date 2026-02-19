# Stock-3DNest — Warehouse Management & Intelligent 3D Cutting System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production-success.svg)

**Integrated warehouse management system with intelligent 3D cutting optimization**

</div>

---

## About

**Stock-3DNest** is a production system for metalworking enterprises, combining warehouse management with intelligent 3D cutting algorithms.

The system helps bandsaw operators find suitable stock, optimally cut it with minimal waste, and get visual confirmation - all in one interface or via Telegram.

---

## Modules

### Module 1 - Warehouse (Public)

Web interface for managing and searching stock:

- **Excel Parsing** from 1C exports (.xlsx) to local SQLite
- **Smart Search** by profile type, material, and dimensions
- **Auto-detection** of current warehouse file by date
- **REST API** for integration
- **Adaptive web interface** with filters

> Warehouse data comes as standard Excel exports from 1C. On startup, files are automatically parsed to SQLite.

---

### Module 2 - 3D Guillotine Cutting (Intellectual Property)

> Source code not published. Principles described below.

Intelligent algorithm for optimal cutting of metal blocks:

- 3D Guillotine Bin Packing algorithm
- Auto-selection of optimal block from warehouse
- 3D visualization (Three.js)
- Cutting sequence output

---

### Module 3 - Telegram Bot (Intellectual Property)

> Source code not published. Principles described below.

Telegram bot duplicating Modules 1 and 2:

- Built on aiogram 3
- PDF reports with 3D cutting scheme
- OpenAI GPT integration
- FSM for dialog management

---

## Demo

> Add your screenshots here

![Warehouse](docs/images/warehouse_main.png)

![3D Cutting](docs/images/cutting_3d.png)

![Telegram Bot](docs/images/telegram_bot.png)

---

## Technologies

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Main language |
| **FastAPI** | REST API |
| **SQLite** | Database |
| **openpyxl/pandas** | Excel parsing |
| **Docker** | Containerization |
| **Three.js** | 3D visualization (Module 2) |
| **aiogram 3** | Telegram bot (Module 3) |

---

## Installation

### Docker (recommended)

```bash
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest
mkdir -p data/warehouse
cp /path/to/Warehouse.xlsx data/warehouse/
docker-compose up -d

# http://localhost:3001/warehouse
```

### Local

```bash
git clone https://github.com/Dmitriy-Schneider/Stock_3Dnest.git
cd Stock_3Dnest
python -m venv venv
source venv/bin/activate
pip install -r requirements-web.txt
mkdir -p data/warehouse
cp /path/to/Warehouse.xlsx data/warehouse/
uvicorn server_fastapi:app --host 0.0.0.0 --port 3001
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /warehouse | Web UI |
| GET | /api/warehouse/items | List items |
| GET | /api/warehouse/items?profile=... | Search |
| POST | /api/warehouse/sync | Sync with Excel |
| GET | /docs | Swagger UI |

---

## Project Structure

```
Stock_3Dnest/
+-- server_fastapi.py         # FastAPI REST API
+-- warehouse_parser.py       # Excel parser
+-- database.py               # SQLite layer
+-- requirements-web.txt      # Dependencies
+-- static/
    +-- warehouse.html        # Warehouse UI (Module 1)
    +-- warehouse.js
    +-- warehouse.css
    +-- index.html            # 3D cutting (Module 2, IP)
    +-- app.js                # 3D UI (Module 2, IP)
+-- data/warehouse/           # Excel files (not in repo)
+-- BotCut/                   # Telegram bot (Module 3, IP)
    +-- EnvExample.txt
    +-- requirements.txt
+-- docker-compose.yml
+-- Dockerfile.web
+-- Dockerfile.bot
```

---

## Open vs Closed Components

| Component | Status |
|-----------|--------|
| warehouse_parser.py | Open |
| database.py | Open |
| server_fastapi.py | Open |
| static/warehouse.* | Open |
| server.py | IP |
| static/app.js | IP |
| BotCut/*.py | IP |
| data/warehouse/*.xlsx | Private |

---

## License

**MIT** for open parts (Module 1 - Warehouse).

3D Cutting Algorithm (Module 2) and Telegram Bot (Module 3) are **intellectual property** of the author.

See [LICENSE](LICENSE)

---

## Author

**Dmitriy Schneider** - [@Dmitriy-Schneider](https://github.com/Dmitriy-Schneider)

---

<div align="center">

If this project was useful, please give it a star!

**Stock-3DNest** - From 1C export to optimal cutting in seconds

</div>
