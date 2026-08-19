# UptimeGuard

UptimeGuard is an asynchronous website uptime monitoring service with a Telegram bot interface. It provides real-time monitoring, stateful alerting, and instant statistical reporting.

## Architecture

```mermaid
flowchart TD
    subgraph Users
        T[Telegram Client]
    end

    subgraph Application
        B[Telegram Bot Interface]
        C[Background Checker Service]
    end

    subgraph Data Layer
        DB[(PostgreSQL)]
        Cache[(Redis)]
    end
    
    subgraph External
        W[Monitored Websites]
        T_API[Telegram API]
    end

    T <-->|Manage Targets & View Stats| B
    B <-->|CRUD Operations| DB
    B -->|Fetch Real-time Stats| Cache
    
    C -->|Fetch Active Targets| DB
    C -->|Save Check Logs| DB
    C -->|HTTP GET Requests| W
    C <-->|Store/Retrieve Last State & Metrics| Cache
    C -->|Trigger Alerts on Status Change| T_API
    T_API -->|Deliver Notifications| T
```

## Features

- **Asynchronous Architecture**: Built on `asyncio`, `FastAPI`, and `httpx` to support concurrent monitoring of numerous endpoints without blocking.
- **Telegram Interface**: Seamless management via Telegram Inline Keyboards for adding, pausing, and deleting monitoring targets.
- **Stateful Alerting**: Intelligent alerting system that tracks the previous state to prevent alert fatigue. Notifications are dispatched exclusively on state transitions (e.g., UP to DOWN).
- **In-Memory Analytics**: Utilizes Redis for high-throughput, low-latency statistics calculation, bypassing heavy SQL aggregation queries.
- **Dockerized**: Fully containerized environment orchestrating the application, PostgreSQL, and Redis.

## Technology Stack

- **Language**: Python 3.12+
- **Framework**: FastAPI, Uvicorn
- **Database**: PostgreSQL (asyncpg, SQLAlchemy 2.0, Alembic)
- **Cache**: Redis (redis.asyncio)
- **Telegram**: python-telegram-bot (v21+)
- **Deployment**: Docker, Docker Compose

## Installation and Setup

The project is fully containerized. Requires Docker and Docker Compose.

### 1. Clone the repository
```bash
git clone https://github.com/Hishhiki/UptimeGuard.git
cd UptimeGuard
```

### 2. Environment Variables
Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# The following variables are overridden by docker-compose, 
# but are required for Pydantic Settings validation:
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/uptimeguard
REDIS_URL=redis://localhost:6379/0
```

### 3. Start the services
Run the following command to build and start the containers:
```bash
docker-compose up --build -d
```
This command will:
- Initialize the PostgreSQL database.
- Initialize the Redis cache.
- Apply database migrations via Alembic.
- Start the FastAPI application and the background monitoring service.

### 4. Usage
1. Open your Telegram bot.
2. Send `/start` to initialize your user profile.
3. Add targets by sending HTTP/HTTPS URLs.
4. Manage targets and view statistics using the interactive menu.

## Local Development
For development without Docker:
1. Ensure PostgreSQL and Redis are running locally.
2. `pip install -e .`
3. `alembic upgrade head`
4. `uvicorn uptime_guard.main:app --reload`