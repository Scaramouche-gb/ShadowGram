import os
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Dict, Any, List, Optional, Tuple


class LolzMarketClient:
    BASE_URL = "https://api.lzt.market"

    def __init__(self, token: str, proxy: Optional[str] = None):
        self.token = token.strip()
        self.proxy = proxy

    def _get_opener(self) -> urllib.request.OpenerDirector:
        handlers = []
        if self.proxy:
            handlers.append(urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy}))
        ctx = ssl.create_default_context()
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
        return urllib.request.build_opener(*handlers)

    def _request(self, endpoint: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        if params:
            url += f"?{urllib.parse.urlencode(params)}"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "User-Agent": "ShadowGram/2.0"
        }

        encoded_data = None
        if data:
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
        opener = self._get_opener()

        try:
            with opener.open(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return True, json.loads(raw)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                parsed = json.loads(err_body)
                msg = parsed.get("errors", [str(e)])
                if isinstance(msg, list):
                    msg = "; ".join(msg)
                return False, f"HTTP {e.code}: {msg}"
            except Exception:
                return False, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            return False, str(e)

    def get_profile_balance(self) -> Tuple[bool, Dict[str, Any]]:
        """Получение информации о текущем пользователе и балансе маркета"""
        ok, res = self._request("me")
        if not ok:
            return False, {"error": res}
        user = res.get("user", {})
        return True, {
            "username": user.get("username", "Unknown"),
            "user_id": user.get("user_id"),
            "balance": user.get("balance", 0.0),
            "hold": user.get("hold", 0.0),
            "currency": user.get("currency", "rub")
        }

    def search_telegram_accounts(
        self,
        max_price: Optional[float] = None,
        country: Optional[str] = None,
        limit: int = 20,
        order_by: str = "price_to_up"
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Поиск доступных Telegram аккаунтов на маркете"""
        params: Dict[str, Any] = {
            "order_by": order_by,
        }
        if max_price:
            params["pmax"] = int(max_price)
        if country:
            params["country[]"] = country.upper()

        ok, res = self._request("telegram", method="GET", params=params)
        if not ok:
            return False, []

        items = res.get("items", [])
        return True, items[:limit]

    def fast_buy(self, item_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Быстрая покупка аккаунта по его ID"""
        endpoint = f"{item_id}/fast-buy"
        ok, res = self._request(endpoint, method="POST")
        if not ok:
            return False, {"error": res}
        return True, res

    def download_account_archive(self, item_id: int, save_path: str) -> Tuple[bool, str]:
        """Скачивание файла сессии/tdata купленного аккаунта"""
        url = f"{self.BASE_URL}/{item_id}/download"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "ShadowGram/2.0"
        }
        req = urllib.request.Request(url, headers=headers, method="GET")
        opener = self._get_opener()

        try:
            with opener.open(req, timeout=60) as resp:
                with open(save_path, "wb") as f:
                    f.write(resp.read())
            return True, save_path
        except Exception as e:
            return False, f"Ошибка скачивания: {e}"
