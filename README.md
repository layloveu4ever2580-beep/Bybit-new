# Bybit Money Management Bot

A trading bot that receives signals from TradingView webhooks, calculates position size using a money management formula, and executes trades on Bybit Perpetual Futures.

## Overview

This bot does NOT generate trading signals. It only:
1. Receives signals from TradingView (entry, TP, SL)
2. Calculates position size using: `Quantity = Target_Profit / abs(Entry - TP)`
3. Sets leverage per coin from config
4. Places market orders on Bybit for immediate entry
5. Validates market price is still between SL and TP before entering
6. Takes profit using conditional limit orders to minimize slippage
7. Syncs trade status with Bybit to track closed PnL and trade history

The React dashboard is for monitoring trades, viewing history, and configuring settings.

## Live Dashboard

**URL:** https://bybit-bot-zu0d.onrender.com

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Bybit API credentials:
   ```env
   BYBIT_API_KEY=your_api_key_here
   BYBIT_API_SECRET=your_api_secret_here
   BYBIT_TESTNET=false
   PORT=5000
   ```

3. Run the Flask server:
   ```bash
   cd backend
   python main.py
   ```
   The backend runs on `http://localhost:5000`

### Frontend Setup

1. Install and build:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. For development:
   ```bash
   npm run dev
   ```
   Dev server runs on `http://localhost:3000`

### Deployment (Render)

The bot is deployed on Render. Set these environment variables in the Render dashboard:
- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`
- `BYBIT_TESTNET` = `false`
- `PORT` = `5000`

Render auto-deploys on push to the connected Git repo.

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhook` | Receive TradingView signals |
| GET | `/api/settings` | Get current settings |
| POST | `/api/settings` | Update settings (target profit, timezone, theme) |
| GET | `/api/trades` | Get all trades (open, closed, failed) |
| PATCH | `/api/trades/:id/target-profit` | Update target profit for a specific trade |
| POST | `/api/sync-trades` | Sync open trades with Bybit (updates status & PnL) |
| GET | `/health` | Health check |

## Supported Tickers & Leverage

Configured in `backend/leverage_config.py`.

## License

MIT
