# Specific Token Pair monitoring & Top Trader Wallet Tracking

When a specific token pair from DEX Screener is given, this script will fetch pair address, liquidity, total supply and etc.

And then, this bot will get top traders for this pair and track activities of these wallets.

## Prerequisites

- [Python](https://www.python.org/downloads/) (3.10.0 or higher)
- Various API Keys


## Quick Start

1. **Clone and Install**
   ```bash
   git clone [your-repository-url]
   cd [project-directory]
   ```

2. **Configure Environment**
   
   Create a `.env` file in the root directory:
   ```env
     SCRAPERAPI_API_KEY=""
     BITQUERY_API_KEY=""
     CIELO_API_KEY=""
     ETHERSCAN_API_KEY=""
     MONGODB_URL=""
     TELEGRAM_BOT_TOKEN=""
   ```

3. **Build and Run**
   ```bash
   # Create venv environment
   python -m venv venv
   venv\Scripts\activate

   # Install dependencies
   pip install requests python-dotenv pymongo websocket-client

   # Run in development mode
   python start.py
   ```

## Feature

| Variable | Description | Required |
|----------|-------------|----------|
| `LANGUAGE` | Python | Yes |
| `BOT` | Telegram Bot | Yes |
| `DATABASE` | MongoDB | Yes |
| `ENVIRONMENT` | Cielo, ScraperAPI, Etherscan, BitQuery | Yes |
