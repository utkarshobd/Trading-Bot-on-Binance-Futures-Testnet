import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logging

BASE_URL = "https://testnet.binancefuture.com"
logger = setup_logging()


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": api_key})

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, endpoint: str, params: dict) -> dict[str, Any]:
        url = f"{BASE_URL}{endpoint}"
        signed = self._sign(params)

        logger.debug("REQUEST %s %s | params: %s", method.upper(), endpoint, {k: v for k, v in signed.items() if k != "signature"})

        try:
            resp = self.session.request(method, url, params=signed if method == "GET" else None, data=signed if method == "POST" else None)
            data = resp.json()
        except requests.RequestException as exc:
            logger.error("Network error: %s", exc)
            raise ConnectionError(f"Network error: {exc}") from exc

        logger.debug("RESPONSE %s | status: %s | body: %s", endpoint, resp.status_code, data)

        if not resp.ok:
            code = data.get("code", resp.status_code)
            msg = data.get("msg", "Unknown API error")
            logger.error("API error [%s]: %s", code, msg)
            raise RuntimeError(f"API error [{code}]: {msg}")

        return data

    def place_order(self, **params) -> dict[str, Any]:
        return self._request("POST", "/fapi/v1/order", params)
