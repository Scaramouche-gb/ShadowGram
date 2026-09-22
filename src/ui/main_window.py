from src.core.constants import *
import os
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QLabel, QPushButton, QMenu, QComboBox, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QTimer, QEvent, Qt, QSize
from src.ui.icon_cache import get_icon

"""
Главный контроллер интерфейса приложения.
Функции:

- init_ui: настройка главного окна и стека страниц
- init_audio: инициализация системы воспроизведения звука
- show_settings: переключение на страницу настроек
- show_list: переключение на страницу списка аккаунтов
- show_modules: открытие окна модулей управления
- show_server: открытие окна управления сервером
- sync_status: периодическая синхронизация статусов всех аккаунтов
- eventFilter: перехват событий (в частности, кликов по логотипу для воспроизведения звука)
"""

from src.ui.list_page import AccountListPage
from src.ui.settings_page import SettingsPage
from src.ui.table_page import AccountTablePage
from src.ui.docs_window import DocsPage
from src import styles
from src.core.constants import (
    SOUND_PATH, LOGO_PATH, FOLDER_ICON_PATH,
    SERVER_ICON_PATH, MODULS_ICON_PATH, 
    NOTE_ICON_PATH, SETTINGS_ICON_PATH, ROCKET_ICON_PATH,
    SEARCH_ICON_PATH, USERS_ICON_PATH, NEIRO_ICON_PATH, ROBOT_ICON_PATH
)

class TelegramManager(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_audio()
        self.setup_tray()
        self.timer = QTimer()
        self.timer.timeout.connect(self.sync_status)
        self.timer.start(1000)

    def clear_nav_selection(self):
        for btn in getattr(self, "nav_buttons", []):
            if btn.isCheckable():
                btn.setChecked(False)

    def show_dashboard(self):
        self.update_nav_buttons(self.btn_dashboard)
        self.switch_page(self.dashboard_page)

    def init_ui(self):
        self.setWindowTitle("Shadowgram")
        self.resize(1000, 850)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Боковая панель навигации (Sidebar)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(270)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 18, 12, 18)
        sidebar_layout.setSpacing(10)

        # Логотип и заголовок
        sidebar_intro = QFrame()
        sidebar_intro.setObjectName("SidebarSurface")
        intro_layout = QVBoxLayout(sidebar_intro)
        intro_layout.setContentsMargins(14, 14, 14, 14)
        intro_layout.setSpacing(10)

        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(8)
        
        logo_label = QLabel()
        logo_pix = QPixmap(str(LOGO_PATH))
        if not logo_pix.isNull():
            logo_label.setPixmap(logo_pix.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo_label.setStyleSheet("background-color: transparent;")
        logo_label.installEventFilter(self)
        logo_layout.addWidget(logo_label)

        title_label = QLabel("Shadowgram")
        title_label.setObjectName("Title")
        title_label.setStyleSheet("font-size: 22px; background-color: transparent;")
        logo_layout.addWidget(title_label)
        logo_layout.addStretch()

        intro_layout.addLayout(logo_layout)

        # Подпись текущей фермы
        from src.core.managers.farm_manager import get_active_farm_name
        farm_name = get_active_farm_name()
        self.label_sidebar_farm = QLabel(f"🚜 Ферма: {farm_name}")
        self.label_sidebar_farm.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {styles.COLOR_PRIMARY}; background: {styles.COLOR_BG}; border-radius: 4px; padding: 3px 8px;")
        intro_layout.addWidget(self.label_sidebar_farm)

        self.combo_sidebar_farm = QComboBox()
        self.combo_sidebar_farm.setFixedHeight(32)
        self.combo_sidebar_farm.setToolTip("Мгновенное переключение рабочей фермы")
        self.combo_sidebar_farm.currentTextChanged.connect(self.switch_farm)
        intro_layout.addWidget(self.combo_sidebar_farm)
        self.refresh_farm_selector(farm_name)

        sidebar_layout.addWidget(sidebar_intro)

        # Навигационные кнопки
        sidebar_layout.addWidget(self.create_sidebar_section("Основное"))

        self.btn_accounts = self.create_nav_button("Аккаунты", USERS_ICON_PATH)
        self.btn_accounts.clicked.connect(self.show_list)
        self.btn_accounts.setChecked(True)
        sidebar_layout.addWidget(self.btn_accounts)

        self.btn_create_profile = self.create_nav_button("Создать", FOLDER_ICON_PATH)
        self.btn_create_profile.setCheckable(False)
        self.btn_create_profile.clicked.connect(self.open_create_profile)
        sidebar_layout.addWidget(self.btn_create_profile)
        
        self.btn_dashboard = self.create_nav_button("Дашборд", SEARCH_ICON_PATH)
        self.btn_dashboard.clicked.connect(self.show_dashboard)
        sidebar_layout.addWidget(self.btn_dashboard)

        self.btn_table = self.create_nav_button("Таблица", NOTE_ICON_PATH)
        self.btn_table.clicked.connect(self.show_table)
        sidebar_layout.addWidget(self.btn_table)

        sidebar_layout.addWidget(self.create_sidebar_section("Инструменты"))

        self.btn_server = self.create_nav_button("Сервер", SERVER_ICON_PATH)
        self.btn_server.clicked.connect(self.show_server)
        sidebar_layout.addWidget(self.btn_server)

        self.btn_modules = self.create_nav_button("Модули", MODULS_ICON_PATH)
        self.btn_modules.clicked.connect(self.show_modules)
        sidebar_layout.addWidget(self.btn_modules)

        self.btn_ai_assistant = self.create_nav_button("Ассистент", ROBOT_ICON_PATH)
        self.btn_ai_assistant.clicked.connect(self.show_ai_assistant)
        sidebar_layout.addWidget(self.btn_ai_assistant)

        self.btn_node_editor = self.create_nav_button("Сценарист", ROCKET_ICON_PATH)
        self.btn_node_editor.clicked.connect(self.show_node_editor)
        sidebar_layout.addWidget(self.btn_node_editor)

        # Меню доп сервисов
        self.btn_services = self.create_nav_button("Доп. сервисы", MODULS_ICON_PATH)
        self.btn_services.clicked.connect(self.show_services)
        sidebar_layout.addWidget(self.btn_services)

        sidebar_layout.addStretch()

        # Кнопки внизу (Документация и Настройки)
        sidebar_layout.addWidget(self.create_sidebar_section("Система"))

        self.btn_docs = self.create_nav_button("Документация", NOTE_ICON_PATH)
        self.btn_docs.clicked.connect(self.show_docs)
        sidebar_layout.addWidget(self.btn_docs)

        self.btn_settings = self.create_nav_button("Настройки", SETTINGS_ICON_PATH)
        self.btn_settings.clicked.connect(self.show_settings)
        sidebar_layout.addWidget(self.btn_settings)

        self.nav_buttons = [
            self.btn_accounts,
            self.btn_create_profile,
            self.btn_dashboard,
            self.btn_table,
            self.btn_server,
            self.btn_modules,
            self.btn_ai_assistant,
            self.btn_node_editor,
            self.btn_services,
            self.btn_docs,
            self.btn_settings,
        ]

        main_layout.addWidget(self.sidebar)

        # Стек с основным контентом
        self.stack = QStackedWidget(self)
        
        from src.ui.dashboard_page import DashboardPage
        self.dashboard_page = DashboardPage(self)
        self.acc_list_page = AccountListPage(self)
        self.settings_page = SettingsPage()
        
        from src.ui.modules_window import ModulesPage
        from src.ui.server_window import ServerPage
        from src.ui.services_page import ServicesPage
        from src.ui.ai_page import AIPage
        
        self.services_page = ServicesPage(self)
        self.modules_page = ModulesPage(self)
        self.server_page = ServerPage(self)
        self.table_page = AccountTablePage(self)
        self.docs_page = DocsPage()
        self.ai_page = AIPage(self)
        
        from src.ui.node_editor.node_editor_window import NodeEditorWindow
        self.node_editor_page = NodeEditorWindow(manager=self)

        self.settings_page.back_requested.connect(self.show_list)
        self.settings_page.settings_saved.connect(self.reload_all_windows)
        self.settings_page.docs_requested.connect(self.show_docs)
        self.docs_page.back_requested.connect(self.show_list)

        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.acc_list_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.modules_page)
        self.stack.addWidget(self.server_page)
        self.stack.addWidget(self.table_page)
        self.stack.addWidget(self.services_page)
        self.stack.addWidget(self.docs_page)
        self.stack.addWidget(self.ai_page)
        self.stack.addWidget(self.node_editor_page)

        main_layout.addWidget(self.stack, 1) # 1 - растягивать контент

        self.acc_list_page.refresh_accounts()
        self.apply_theme()

    def create_nav_button(self, text, icon_path):
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setIcon(get_icon(icon_path))
        btn.setIconSize(QSize(18, 18))
        btn.setFixedHeight(40)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def create_sidebar_section(self, text):
        label = QLabel(text)
        label.setObjectName("SidebarSectionTitle")
        return label

    def init_audio(self):
        self.sound_path = str(SOUND_PATH)

    def show_settings(self):
        self.settings_page.load_settings()
        self.update_nav_buttons(self.btn_settings)
        self.switch_page(self.settings_page)

    def show_services(self):
        self.update_nav_buttons(self.btn_services)
        self.switch_page(self.services_page)

    def update_nav_buttons(self, active_btn):
        self.clear_nav_selection()
        active_btn.setChecked(True)

    def switch_page(self, page):
        self.stack.setCurrentWidget(page)

    def refresh_farm_selector(self, active_name=None):
        from src.core.managers import farm_manager
        active_name = active_name or farm_manager.get_active_farm_name()
        self.combo_sidebar_farm.blockSignals(True)
        self.combo_sidebar_farm.clear()
        self.combo_sidebar_farm.addItems(farm_manager.list_available_farms())
        index = self.combo_sidebar_farm.findText(active_name)
        if index >= 0:
            self.combo_sidebar_farm.setCurrentIndex(index)
        self.combo_sidebar_farm.blockSignals(False)
        self.label_sidebar_farm.setText(f"🚜 Ферма: {active_name}")

    def switch_farm(self, farm_name):
        from src.core.managers import farm_manager
        farm_name = farm_name.strip()
        if not farm_name or farm_name == farm_manager.get_active_farm_name():
            return
        if not farm_manager.switch_active_farm(farm_name):
            self.refresh_farm_selector()
            QMessageBox.critical(self, "Фермы", f"Не удалось переключиться на ферму «{farm_name}».")
            return

        # Переключаем только данные, не пересоздавая страницы и окна приложения.
        self.refresh_farm_selector(farm_name)
        self.acc_list_page.refresh_accounts()
        self.table_page.refresh_data()
        if hasattr(self, "mass_sender_page"):
            self.mass_sender_page.load_accounts()
        if hasattr(self, "settings_page"):
            self.settings_page.load_settings()
        self.show_list()

    def setup_tray(self):
        from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
        from PyQt6.QtGui import QIcon
        
        self.tray_icon = QSystemTrayIcon(self)
        # Try to load app icon if exists, otherwise use default
        try:
            self.tray_icon.setIcon(QIcon("src/assets/icon.png"))
        except:
            self.tray_icon.setIcon(QIcon.fromTheme("applications-internet"))
            
        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Развернуть")
        restore_action.triggered.connect(self.showNormal)
        quit_action = tray_menu.addAction("Выход")
        quit_action.triggered.connect(self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def notify_user(self, title: str, message: str, is_error: bool = False):
        try:
            import json, os
            from src.core.constants import CONFIG_FILE
            
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                s = data.get("settings", {})
                
            if is_error and not s.get("notify_bans", True):
                return
            if not is_error and not s.get("notify_finished", True):
                return
                
            from PyQt6.QtWidgets import QSystemTrayIcon
            icon_type = QSystemTrayIcon.MessageIcon.Critical if is_error else QSystemTrayIcon.MessageIcon.Information
            self.tray_icon.showMessage(title, message, icon_type, 3000)
            
            if s.get("sound_alerts", True):
                from PyQt6.QtWidgets import QApplication
                QApplication.beep()
        except:
            pass

    def closeEvent(self, event):
        try:
            import json, os, datetime
            from src.core.constants import CONFIG_FILE
            from src.core.managers import config_manager
            
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                s = data.get("settings", {})
                
            if s.get("auto_backup", False):
                os.makedirs("backups", exist_ok=True)
                backup_path = f"backups/backup_auto_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                config_manager.export_backup(CONFIG_FILE, backup_path)
                
            if s.get("auto_clean_cache", False):
                from src.core.managers import process_manager
                accounts = data.get("accounts", [])
                for acc in accounts:
                    process_manager.clear_cache(acc.get("workdir", ""))
        except Exception as e:
            print(f"[DEBUG] Error during close event: {e}")
            
        super().closeEvent(event)

    def show_list(self):
        self.update_nav_buttons(self.btn_accounts)
        self.switch_page(self.acc_list_page)

    def show_table(self):
        self.update_nav_buttons(self.btn_table)
        self.table_page.refresh_data()
        self.switch_page(self.table_page)

    def show_ai_assistant(self):
        self.update_nav_buttons(self.btn_ai_assistant)
        self.switch_page(self.ai_page)

    def reload_all_windows(self):
        from src import styles
        from PyQt6.QtWidgets import QApplication
        
        # Перезагружаем тему
        styles.load_theme()
        
        # Применяем новую тему к приложению
        app = QApplication.instance()
        if app:
            app.setStyleSheet(styles.STYLESHEET)
            
        # Применяем новые стили к sidebar и кнопкам навигации
        self.apply_theme()
        
        # Пересоздаём settings_page — все inline-стили будут с новой темой
        old_settings = self.settings_page
        self.settings_page = SettingsPage()
        self.settings_page.back_requested.connect(self.show_list)
        self.settings_page.settings_saved.connect(self.reload_all_windows)
        self.settings_page.docs_requested.connect(self.show_docs)
        self.stack.addWidget(self.settings_page)
        self.stack.removeWidget(old_settings)
        old_settings.deleteLater()

        # Пересоздаём modules_page
        from src.ui.modules_window import ModulesPage
        old_old_modules = self.modules_page
        self.modules_page = ModulesPage(self)
        self.stack.addWidget(self.modules_page)
        self.stack.removeWidget(old_old_modules)
        old_old_modules.deleteLater()

        # Пересоздаём server_page
        from src.ui.server_window import ServerPage
        old_server = self.server_page
        self.server_page = ServerPage(self)
        self.stack.addWidget(self.server_page)
        self.stack.removeWidget(old_server)
        old_server.deleteLater()
        
        # Пересоздаём docs_page
        old_docs = self.docs_page
        self.docs_page = DocsPage()
        self.docs_page.back_requested.connect(self.show_list)
        self.stack.addWidget(self.docs_page)
        self.stack.removeWidget(old_docs)
        old_docs.deleteLater()

        # Пересоздаём node_editor_page (Сценарист)
        from src.ui.node_editor.node_editor_window import NodeEditorWindow
        old_node_editor = self.node_editor_page
        self.node_editor_page = NodeEditorWindow(manager=self)
        self.stack.addWidget(self.node_editor_page)
        self.stack.removeWidget(old_node_editor)
        old_node_editor.deleteLater()

        # Обновляем аккаунты на странице таблиц
        if hasattr(self, 'table_page'):
            self.table_page.refresh_data()

        # Восстанавливаем текущую страницу аккаунтов
        self.acc_list_page.refresh_accounts()
        
        # Показываем главную страницу
        self.show_list()


    def apply_theme(self):
        widgets = [self.sidebar, *getattr(self, "nav_buttons", [])]
        for widget in widgets:
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()


    def show_docs(self):
        self.update_nav_buttons(self.btn_docs)
        self.switch_page(self.docs_page)

    def show_modules(self):
        self.modules_page.load_accounts()
        self.update_nav_buttons(self.btn_modules)
        self.switch_page(self.modules_page)

    def show_server(self):
        self.update_nav_buttons(self.btn_server)
        self.switch_page(self.server_page)

    def open_create_profile(self):
        self.acc_list_page.open_create_profile_dialog()

    def _embed_service_page(self, widget_instance, title="Доп сервис"):
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
        from PyQt6.QtCore import Qt
        from src import styles
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {styles.COLOR_CONSOLE_BG}; border-bottom: 1px solid {styles.COLOR_BORDER};")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        btn_back = QPushButton("Назад к сервисам")
        btn_back.setIcon(QIcon(str(CANCEL_ICON_PATH)))
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {styles.COLOR_TEXT_MAIN};
                border: 1px solid {styles.COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {styles.COLOR_HOVER_BG};
                color: {styles.COLOR_PRIMARY};
                border-color: {styles.COLOR_PRIMARY};
            }}
        """)
        btn_back.clicked.connect(self.show_services)
        header_layout.addWidget(btn_back)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {styles.COLOR_TEXT_MAIN}; margin-left: 15px; border: none;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
        content_wrapper = QWidget()
        content_wrapper_layout = QVBoxLayout(content_wrapper)
        content_wrapper_layout.setContentsMargins(20, 20, 20, 20)
        
        from PyQt6.QtWidgets import QDialog
        if isinstance(widget_instance, QDialog):
            widget_instance.setWindowFlags(Qt.WindowType.Widget)
            
        content_wrapper_layout.addWidget(widget_instance)
        
        layout.addWidget(content_wrapper, 1)
        
        self.stack.addWidget(container)
        self.switch_page(container)

    def open_device_generator(self):
        from src.services.device_generator import DeviceNameGeneratorService
        service = DeviceNameGeneratorService(self)
        self._embed_service_page(service, "Генератор имён устройств")

    def open_api_generator(self):
        from src.ui.api_generator_window import ApiGeneratorWindow
        service = ApiGeneratorWindow(self)
        self._embed_service_page(service, "Fallback API")

    def open_prompt_generator(self):
        from src.services.ai_prompt_generator import AIPromptGeneratorService
        service = AIPromptGeneratorService(self)
        self._embed_service_page(service, "Генератор AI Промптов")

    def open_mass_profile_creator(self):
        from src.services.mass_profile_creator import MassProfileCreatorService
        service = MassProfileCreatorService(self)
        self._embed_service_page(service, "Массовое создание профилей")

    def open_tdata_converter(self):
        from src.ui.tdata_converter_window import TDataConverterWindow
        service = TDataConverterWindow(self)
        self._embed_service_page(service, "Конвертер TData")

    def open_session_manager(self):
        from src.ui.session_creator import SessionCreatorWindow
        service = SessionCreatorWindow(self)
        self._embed_service_page(service, "Генератор сессий")

    def open_mass_session_creator(self):
        from src.services.mass_session_service import MassSessionService
        service = MassSessionService(self)
        self._embed_service_page(service, "Массовое создание сессий")

    def open_telethon_converter(self):
        from src.ui.telethon_converter_window import TelethonConverterWindow
        service = TelethonConverterWindow(self)
        self._embed_service_page(service, "Конвертер Telethon")

    def open_agregator_prep(self):
        from src.services.agregator_prep_service import AgregatorSoftPrepService
        service = AgregatorSoftPrepService(self)
        self._embed_service_page(service, "Подготовка Agregator-Viewer-soft")

    def show_node_editor(self):
        selected_accounts = []
        if hasattr(self, 'acc_list_page') and hasattr(self.acc_list_page, 'rows'):
            selected_accounts = [
                {
                    "name": r.name,
                    "workdir": r.workdir,
                    "proxy_url": r.proxy_url,
                    "device_name": r.device_name,
                    "notes": r.notes,
                    "ai_prompt": r.ai_prompt
                }
                for r in self.acc_list_page.rows if r.checkbox.isChecked()
            ]
        self.node_editor_page.selected_accounts = selected_accounts
        if hasattr(self.node_editor_page, 'accounts_panel'):
            self.node_editor_page.accounts_panel.load_accounts()
        self.update_nav_buttons(self.btn_node_editor)
        self.switch_page(self.node_editor_page)

    def export_phone_numbers(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json
        from src.core.constants import CONFIG_FILE
        
        if not CONFIG_FILE.exists():
            QMessageBox.warning(self, "Ошибка", "Конфигурационный файл не найден.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить номера", "", "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if not file_path:
            return
            
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            accounts = config.get("accounts", [])
            phones = [acc.get("phone", "") for acc in accounts if acc.get("phone")]
            
            with open(file_path, "w", encoding="utf-8") as f:
                for phone in phones:
                    f.write(f"{phone}\n")
                    
            QMessageBox.information(self, "Успех", f"Успешно экспортировано {len(phones)} номеров.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать номера:\n{e}")

    def update_sidebar_icons(self):
        for r in self.acc_list_page.rows:
            if r.tg_process is not None:
                r.check_status()

    def sync_status(self):
        for r in self.acc_list_page.rows:
            if r.tg_process is not None:
                r.check_status()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            for cmd in ["mpv", "ffplay", "pw-play", "paplay"]:
                try:
                    args = [cmd, "--no-video", "--volume=100", self.sound_path] if cmd == "mpv" else [cmd, "-nodisp", "-autoexit", self.sound_path] if cmd == "ffplay" else [cmd, self.sound_path]
                    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
                except:
                    continue
            return True
        return super().eventFilter(obj, event)
