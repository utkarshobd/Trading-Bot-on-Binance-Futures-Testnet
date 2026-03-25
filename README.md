# Trading Bot — Binance Futures Testnet

A minimal, well-structured Python CLI trading bot for Binance Futures Testnet (USDT-M).

## Project Structure

```
Trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST API wrapper (HMAC-signed requests)
│   ├── orders.py          # Order placement logic + response formatting
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Rotating file + console logging
├── cli.py                 # CLI entry point (argparse)
├── logs/                  # Auto-created; contains trading_bot.log
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

### 1. Get Testnet API Credentials

1. Register at [Binance Futures Testnet](https://testnet.binancefuture.com)
2. Log in and generate an API Key & Secret from the testnet dashboard

> **Note:** Your real Binance account API key also works against `testnet.binancefuture.com`.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Credentials

```bash
cp .env.example .env
# Edit .env and fill in your API key and secret
```

`.env`:
```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

## How to Run

### Market Order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Limit Order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 50000
```

### Stop-Limit Order (Bonus — TWAP)

```bash
# Split 0.05 BTC into 5 market orders, 10s apart (defaults)
python cli.py --symbol BTCUSDT --side BUY --type TWAP --quantity 0.05

# Custom: 3 slices, 5s interval
python cli.py --symbol BTCUSDT --side BUY --type TWAP --quantity 0.05 --slices 3 --interval 5
```

## CLI Arguments

| Argument       | Required | Description                                      |
|----------------|----------|--------------------------------------------------|
| `--symbol`     | Yes      | Trading pair (e.g. `BTCUSDT`)                    |
| `--side`       | Yes      | `BUY` or `SELL`                                  |
| `--type`       | Yes      | `MARKET`, `LIMIT`, or `TWAP`                 |
| `--quantity`   | Yes      | Order quantity (positive float)                  |
| `--price`      | No*      | Limit price — required for `LIMIT` orders        |
| `--slices`     | No       | TWAP: number of child orders (default: 5)        |
| `--interval`   | No       | TWAP: seconds between slices (default: 10)       |

## Logging

Logs are written to `logs/trading_bot.log` (rotating, max 5 MB × 3 backups).

- Console: `INFO` and above
- File: `DEBUG` and above (full request/response detail)

## Assumptions

- All orders are placed on Binance Futures Testnet (USDT-M) at `https://testnet.binancefuture.com`
- LIMIT orders use `timeInForce=GTC` (Good Till Cancelled) by default
- TWAP splits the total quantity into N equal MARKET slices executed at a fixed time interval
- `testnet.binancefuture.com` only supports `MARKET` and `LIMIT` on `/fapi/v1/order`; all conditional order types (STOP, STOP_MARKET, TAKE_PROFIT, etc.) return `-4120` on this environment
- Credentials are your real Binance API key/secret loaded from a `.env` file or environment variables
- No position management or account balance checks are performed — this is a pure order-placement tool
