import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QDoubleSpinBox, QTextEdit, QProgressBar, QMessageBox, QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.services.lolz_buyer_service import LolzAccountBuyerService
from src.core.managers import farm_manager, config_manager
from src.core.constants import CONFIG_FILE
from src import styles


class LolzBuyerWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(int, int)

    def __init__(self, token: str, count: int, max_price: float, country: str, farm_name: str):
        super().__init__()
        self.token = token
        self.count = count
        self.max_price = max_price
        self.country = country
        self.farm_name = farm_name
        self.is_running = True

    def run(self):
        service = LolzAccountBuyerService(token=self.token)
        self.log_signal.emit(f"🔍 Поиск доступных аккаунтов на маркете (до {self.max_price} ₽, страна: {self.country or 'любая'})...")

        ok, items = service.client.search_telegram_accounts(
            max_price=self.max_price if self.max_price > 0 else None,
            country=self.country if self.country else None,
            limit=max(self.count * 3, 30)
        )

        if not ok or not items:
            self.log_signal.emit("❌ По вашим фильтрам не найдено подходящих аккаунтов!")
            self.finished_signal.emit(0, 0)
            return

        self.log_signal.emit(f"Найдено {len(items)} предложений. Начинаем покупку...")
        bought_count = 0
        failed_count = 0

        for idx, item in enumerate(items):
            if not self.is_running or bought_count >= self.count:
                break

            item_id = item.get("item_id")
            price = item.get("price", 0)
            self.log_signal.emit(f"[{bought_count + 1}/{self.count}] Выбран лот #{item_id} за {price} ₽...")

            ok, res_msg = service.buy_and_install_account(
                item_id=item_id,
                farm_name=self.farm_name,
                log_callback=self.log_signal.emit
            )

            if ok:
                bought_count += 1
                self.progress_signal.emit(bought_count, self.count)
                time.sleep(2)
            else:
                failed_count += 1
                self.log_signal.emit(f"⚠️ Пропуск лота: {res_msg}")
                time.sleep(1)

        self.log_signal.emit(f"🏁 Завершено! Успешно куплено: {bought_count}, ошибок/пропусков: {failed_count}.")
        self.finished_signal.emit(bought_count, failed_count)

    def stop(self):
        self.is_running = False


class LolzBuyerPage(QWidget):
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.init_ui()
        self.load_saved_token()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 1. Секция токена и баланса
        auth_group = QGroupBox("🔑 Авторизация Lolzteam Market (Зеленка)")
        auth_layout = QHBoxLayout(auth_group)

        self.input_token = QLineEdit()
        self.input_token.setPlaceholderText("Вставьте API токен маркета (с правами на покупку)...")
        self.input_token.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addWidget(self.input_token, 1)

        self.btn_check_balance = QPushButton("💳 Проверить баланс")
        self.btn_check_balance.setObjectName("PrimaryBtn")
        self.btn_check_balance.clicked.connect(self.check_balance)
        auth_layout.addWidget(self.btn_check_balance)

        self.lbl_balance = QLabel("Баланс: —")
        self.lbl_balance.setStyleSheet(f"font-weight: bold; color: {styles.COLOR_PRIMARY}; padding-left: 10px;")
        auth_layout.addWidget(self.lbl_balance)

        layout.addWidget(auth_group)

        # 2. Фильтры покупки
        filter_group = QGroupBox("⚙️ Параметры покупки")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("Количество аккаунтов:"))
        self.spin_count = QSpinBox()
        self.spin_count.setRange(1, 100)
        self.spin_count.setValue(5)
        filter_layout.addWidget(self.spin_count)

        filter_layout.addWidget(QLabel("Макс. цена (₽):"))
        self.spin_max_price = QDoubleSpinBox()
        self.spin_max_price.setRange(1.0, 5000.0)
        self.spin_max_price.setValue(80.0)
        filter_layout.addWidget(self.spin_max_price)

        filter_layout.addWidget(QLabel("Страна (ГЕО):"))
        self.combo_country = QComboBox()
        self.combo_country.addItems(["Любая", "US", "RU", "KZ", "ID", "NG", "BR", "IN", "VN"])
        filter_layout.addWidget(self.combo_country)

        layout.addWidget(filter_group)

        # 3. Кнопка запуска и прогресс
        action_layout = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Начать автоматическую покупку")
        self.btn_start.setObjectName("PrimaryBtn")
        self.btn_start.setFixedHeight(45)
        self.btn_start.clicked.connect(self.start_buying)
        action_layout.addWidget(self.btn_start)

        layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 4. Консоль логов
        layout.addWidget(QLabel("Лог выполнения:"))
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet(f"background-color: {styles.COLOR_CONSOLE_BG}; color: #CFD8DC; font-family: monospace;")
        layout.addWidget(self.log_console, 1)

    def load_saved_token(self):
        cfg = config_manager._read_config(CONFIG_FILE)
        token = cfg.get("settings", {}).get("lolz_market_token", "")
        if token:
            self.input_token.setText(token)

    def save_token(self, token: str):
        cfg = config_manager._read_config(CONFIG_FILE)
        if "settings" not in cfg:
            cfg["settings"] = {}
        cfg["settings"]["lolz_market_token"] = token
        config_manager._write_config(CONFIG_FILE, cfg)

    def append_log(self, text: str):
        self.log_console.append(text)

    def check_balance(self):
        token = self.input_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Внимание", "Введите API токен маркета!")
            return

        self.save_token(token)
        service = LolzAccountBuyerService(token=token)
        ok, res = service.client.get_profile_balance()

        if ok:
            balance = res.get("balance", 0.0)
            currency = res.get("currency", "rub")
            user = res.get("username", "Unknown")
            self.lbl_balance.setText(f"Пользователь: {user} | Баланс: {balance} {currency.upper()}")
            self.append_log(f"✅ Баланс успешно обновлен: {balance} {currency.upper()} ({user})")
        else:
            err = res.get("error", "Ошибка запроса")
            self.lbl_balance.setText("Ошибка авторизации")
            QMessageBox.critical(self, "Ошибка Lolzteam", f"Не удалось авторизоваться:\n{err}")

    def start_buying(self):
        token = self.input_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Внимание", "Введите API токен маркета перед запуском!")
            return

        self.save_token(token)
        count = self.spin_count.value()
        max_price = self.spin_max_price.value()
        country = self.combo_country.currentText()
        if country == "Любая":
            country = ""

        farm_name = farm_manager.get_active_farm_name()

        reply = QMessageBox.question(
            self,
            "Подтверждение покупки",
            f"Купить до {count} аккаунтов по цене до {max_price} ₽ в ферму '{farm_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.btn_start.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(count)
        self.progress_bar.setValue(0)
        self.append_log(f"--- Запуск автопокупки в ферму '{farm_name}' ---")

        self.worker = LolzBuyerWorker(token, count, max_price, country, farm_name)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_buying_finished)
        self.worker.start()

    def on_buying_finished(self, bought: int, failed: int):
        self.btn_start.setEnabled(True)
        if self.main_window and hasattr(self.main_window, "acc_list_page"):
            self.main_window.acc_list_page.refresh_accounts()
        QMessageBox.information(self, "Готово", f"Покупка завершена!\nУспешно добавлено: {bought}\nПропущено: {failed}")
