from __future__ import annotations

import time

from bot.client import BinanceClient
from bot.logging_config import setup_logging
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_symbol,
)

logger = setup_logging()

SEP = "-" * 45
TWAP_SLICES = 5        # number of child orders
TWAP_INTERVAL = 10     # seconds between slices


def _build_params(symbol, side, order_type, quantity, price):
    params = {"symbol": symbol, "side": side, "type": order_type, "quantity": quantity}
    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"
    return params


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float | str,
    price: float | str | None = None,
    **_,
) -> dict | list[dict]:
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_quantity(quantity)
    price = validate_price(price, order_type)

    if order_type == "TWAP":
        return _place_twap(client, symbol, side, quantity)

    params = _build_params(symbol, side, order_type, quantity, price)
    logger.info(
        "Placing %s %s order | symbol=%s qty=%s%s",
        side, order_type, symbol, quantity,
        f" price={price}" if price else "",
    )
    response = client.place_order(**params)
    logger.info(
        "Order placed | orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"), response.get("status"),
        response.get("executedQty"), response.get("avgPrice"),
    )
    return response


def _place_twap(client: BinanceClient, symbol: str, side: str, total_qty: float) -> list[dict]:
    slice_qty = round(total_qty / TWAP_SLICES, 3)
    logger.info(
        "TWAP order | symbol=%s side=%s total_qty=%s slices=%s slice_qty=%s interval=%ss",
        symbol, side, total_qty, TWAP_SLICES, slice_qty, TWAP_INTERVAL,
    )
    print(f"\n  TWAP: splitting {total_qty} into {TWAP_SLICES} x {slice_qty} MARKET orders")
    print(f"  Interval: {TWAP_INTERVAL}s between slices\n")

    results = []
    for i in range(1, TWAP_SLICES + 1):
        print(f"  Slice {i}/{TWAP_SLICES} ...", end=" ", flush=True)
        params = _build_params(symbol, side, "MARKET", slice_qty, None)
        resp = client.place_order(**params)
        results.append(resp)
        logger.info(
            "TWAP slice %s/%s | orderId=%s status=%s executedQty=%s avgPrice=%s",
            i, TWAP_SLICES, resp.get("orderId"), resp.get("status"),
            resp.get("executedQty"), resp.get("avgPrice"),
        )
        print(f"orderId={resp.get('orderId')} status={resp.get('status')}")
        if i < TWAP_SLICES:
            time.sleep(TWAP_INTERVAL)

    return results


def format_response(response: dict | list[dict]) -> str:
    if isinstance(response, list):
        lines = [SEP, "  TWAP ORDER SUMMARY", SEP]
        total_exec = sum(float(r.get("executedQty", 0)) for r in response)
        lines.append(f"  Slices     : {len(response)}")
        lines.append(f"  Symbol     : {response[0].get('symbol')}")
        lines.append(f"  Side       : {response[0].get('side')}")
        lines.append(f"  Total Exec : {total_exec:.3f}")
        lines += [
            f"  [{i+1}] orderId={r.get('orderId')} qty={r.get('executedQty')} status={r.get('status')}"
            for i, r in enumerate(response)
        ]
        lines.append(SEP)
        return "\n".join(lines)

    lines = [
        SEP,
        "  ORDER CONFIRMATION",
        SEP,
        f"  Order ID   : {response.get('orderId')}",
        f"  Symbol     : {response.get('symbol')}",
        f"  Side       : {response.get('side')}",
        f"  Type       : {response.get('type')}",
        f"  Quantity   : {response.get('origQty')}",
        f"  Exec Qty   : {response.get('executedQty')}",
        f"  Avg Price  : {response.get('avgPrice')}",
        f"  Status     : {response.get('status')}",
        f"  Time       : {response.get('updateTime')}",
        SEP,
    ]
    return "\n".join(lines)
