import os
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from src.core.managers.lolz_manager import LolzMarketClient
from src.core.managers import farm_manager, config_manager, hw_manager
from src.core.constants import CONFIG_FILE, FARMS_DIR


class LolzAccountBuyerService:
    def __init__(self, token: str, proxy: Optional[str] = None):
        self.client = LolzMarketClient(token=token, proxy=proxy)

    def _get_next_account_info(self, farm_name: str) -> Tuple[str, Path]:
        """Определение следующего свободного имени accN и пути к его папке"""
        if farm_name == "default":
            accounts_dir = Path("accounts")
            cfg_path = CONFIG_FILE
        else:
            accounts_dir = FARMS_DIR / farm_name / "accounts"
            cfg_path = FARMS_DIR / farm_name / "config.json"

        accounts_dir.mkdir(parents=True, exist_ok=True)
        data = config_manager._read_config(cfg_path)
        existing_names = {acc.get("name", "") for acc in data.get("accounts", [])}

        idx = 1
        while True:
            candidate_name = f"acc{idx}"
            candidate_dir = accounts_dir / candidate_name
            if candidate_name not in existing_names and not candidate_dir.exists():
                return candidate_name, candidate_dir.resolve()
            idx += 1

    def _get_available_proxy(self) -> Optional[str]:
        """Выбор прокси из пула настроек"""
        cfg = config_manager._read_config(CONFIG_FILE)
        pool = cfg.get("settings", {}).get("proxy_pool", [])
        if not pool:
            return None
        # Возвращаем случайный прокси из пула
        import random
        return random.choice(pool)

    def buy_and_install_account(
        self,
        item_id: int,
        farm_name: str,
        log_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """Покупка одного аккаунта, скачивание сессии и размещение в активной ферме"""
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        log(f"🛒 Покупка аккаунта #{item_id} на Lolzteam...")
        ok, buy_res = self.client.fast_buy(item_id)
        if not ok:
            err = buy_res.get("error", "Неизвестная ошибка")
            return False, f"Ошибка покупки #{item_id}: {err}"

        item_data = buy_res.get("item", {})
        login_data = buy_res.get("item", {}).get("loginData", {})
        two_factor = login_data.get("password") or item_data.get("password")

        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = os.path.join(tmp_dir, f"{item_id}.zip")
            log(f"📥 Скачивание сессии для #{item_id}...")
            ok, dl_res = self.client.download_account_archive(item_id, archive_path)
            if not ok:
                return False, f"Ошибка загрузки архива: {dl_res}"

            acc_name, target_dir = self._get_next_account_info(farm_name)
            target_dir.mkdir(parents=True, exist_ok=True)

            # Распаковка
            log(f"📦 Распаковка файлов в {target_dir.name}...")
            try:
                if zipfile.is_zipfile(archive_path):
                    with zipfile.ZipFile(archive_path, "r") as zip_ref:
                        zip_ref.extractall(target_dir)
                else:
                    # Если скачан одиночный .session файл
                    dest_session = target_dir / f"{acc_name}.session"
                    shutil.copy2(archive_path, dest_session)
            except Exception as e:
                return False, f"Ошибка распаковки архива: {e}"

            # Если в папке появился .session с другим именем, переименовываем в accN.session
            for s_file in target_dir.glob("*.session"):
                expected = target_dir / f"{acc_name}.session"
                if s_file != expected:
                    s_file.rename(expected)
                    break

            # Назначаем прокси и аппаратный профиль
            assigned_proxy = self._get_available_proxy()
            device_profile = hw_manager.get_or_create_fake_hw(target_dir)

            # Регистрация аккаунта в конфигурации фермы
            if farm_name == "default":
                cfg_path = CONFIG_FILE
            else:
                cfg_path = FARMS_DIR / farm_name / "config.json"

            cfg_data = config_manager._read_config(cfg_path)
            if "accounts" not in cfg_data:
                cfg_data["accounts"] = []

            account_entry = {
                "name": acc_name,
                "workdir": str(target_dir),
                "proxy_url": assigned_proxy,
                "device_name": device_profile.get("device_model", "Desktop PC"),
                "password": two_factor or "",
                "phone": item_data.get("phone", ""),
                "username": item_data.get("username", ""),
                "status": "ГОТОВ",
                "is_valid": True,
                "notes": f"Куплен на Lolz Market (Item ID: {item_id})"
            }

            cfg_data["accounts"].append(account_entry)
            config_manager._write_config(cfg_path, cfg_data)

            log(f"✅ Аккаунт успешно добавлен как '{acc_name}' в ферму '{farm_name}'!")
            return True, acc_name
