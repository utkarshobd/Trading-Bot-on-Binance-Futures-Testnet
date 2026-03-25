#!/usr/bin/env python3
"""
Trading Bot CLI - Binance Futures Demo (USDT-M)
"""
import argparse
import os
import sys

from dotenv import load_dotenv

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.orders import format_response, place_order
import bot.orders as orders_module

load_dotenv()
logger = setup_logging()

SEP = "-" * 45


def _get_credentials() -> tuple[str, str]:
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        logger.error("BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env or environment.")
        sys.exit(1)
    return api_key, api_secret


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--symbol",    required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",      required=True, choices=["BUY", "SELL"], help="Order side")
    parser.add_argument("--type",      required=True, dest="order_type",
                        choices=["MARKET", "LIMIT", "TWAP"], help="Order type")
    parser.add_argument("--quantity",  required=True, type=float, help="Order quantity")
    parser.add_argument("--price",     type=float, default=None,
                        help="Limit price (required for LIMIT)")
    parser.add_argument("--slices",    type=int, default=None,
                        help="TWAP: number of child orders (default: 5)")
    parser.add_argument("--interval",  type=int, default=None,
                        help="TWAP: seconds between slices (default: 10)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Apply TWAP overrides if provided
    if args.slices is not None:
        orders_module.TWAP_SLICES = args.slices
    if args.interval is not None:
        orders_module.TWAP_INTERVAL = args.interval

    print("\n" + SEP)
    print("  ORDER REQUEST SUMMARY")
    print(SEP)
    print(f"  Symbol     : {args.symbol.upper()}")
    print(f"  Side       : {args.side.upper()}")
    print(f"  Type       : {args.order_type.upper()}")
    print(f"  Quantity   : {args.quantity}")
    if args.price:
        print(f"  Price      : {args.price}")
    if args.order_type == "TWAP":
        print(f"  Slices     : {orders_module.TWAP_SLICES}")
        print(f"  Interval   : {orders_module.TWAP_INTERVAL}s")
    print(SEP + "\n")

    api_key, api_secret = _get_credentials()
    client = BinanceClient(api_key, api_secret)

    try:
        response = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
        print(format_response(response))
        print("\n[OK] Order placed successfully!\n")
        logger.info("CLI session completed successfully.")

    except ValueError as exc:
        logger.warning("Validation error: %s", exc)
        print(f"\n[ERROR] Validation error: {exc}\n")
        sys.exit(2)

    except RuntimeError as exc:
        logger.error("API error: %s", exc)
        print(f"\n[ERROR] {exc}\n")
        sys.exit(3)

    except ConnectionError as exc:
        logger.error("Connection error: %s", exc)
        print(f"\n[ERROR] {exc}\n")
        sys.exit(4)


if __name__ == "__main__":
    main()
