from src.core.constants import *
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QScrollArea, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QPixmap
import os

from src import styles
from src.core.constants import (
    TOOGLE_ICON_PATH, PHONE_ICON_PATH, KEY_ICON_PATH,
    PEAPLE_ICON_PATH, REFRESH_ICON_PATH, REBOOT_ICON_PATH,
    ROBOT_ICON_PATH, CALL_ICON_PATH
)

_ICON_CACHE = {}


class ServiceCard(QFrame):
    def __init__(self, title, description, icon, category, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setObjectName("ServiceCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(54, 54)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            f"background-color: {styles.COLOR_SELECT_BG}; border: 1px solid {styles.COLOR_BORDER_LIGHT}; border-radius: 14px;"
        )

        if os.path.exists(icon):
            if icon not in _ICON_CACHE:
                _ICON_CACHE[icon] = QPixmap(icon).scaled(
                    28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            icon_label.setPixmap(_ICON_CACHE[icon])
        else:
            icon_label.setText(icon)
            icon_label.setStyleSheet(
                f"font-size: 24px; color: {styles.COLOR_PRIMARY}; background-color: {styles.COLOR_SELECT_BG}; "
                f"border: 1px solid {styles.COLOR_BORDER_LIGHT}; border-radius: 14px;"
            )

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        category_label = QLabel(category)
        category_label.setObjectName("ServiceCategory")
        title_col.addWidget(category_label)

        title_label = QLabel(title)
        title_label.setObjectName("ServiceTitle")
        title_label.setWordWrap(True)
        title_col.addWidget(title_label)

        top_row.addWidget(icon_label)
        top_row.addLayout(title_col, 1)
        layout.addLayout(top_row)

        description_label = QLabel(description)
        description_label.setObjectName("ServiceDescription")
        description_label.setWordWrap(True)
        layout.addWidget(description_label, 1)

        launch_btn = QPushButton("Открыть сервис")
        launch_btn.setObjectName("GhostBtn")
        launch_btn.clicked.connect(self.callback)
        layout.addWidget(launch_btn, alignment=Qt.AlignmentFlag.AlignLeft)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback()
        super().mousePressEvent(event)


class ServicesPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setObjectName("PageRoot")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("PageHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(6)

        eyebrow = QLabel("UTILITY SUITE")
        eyebrow.setObjectName("PageEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("Дополнительные сервисы")
        title.setObjectName("PageTitle")
        hero_layout.addWidget(title)

        subtitle = QLabel("Набор инструментов для массовых операций, генерации данных и подготовки аккаунтов к работе.")
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        layout.addWidget(hero)

        intro_card = QFrame()
        intro_card.setObjectName("ToolbarCard")
        intro_layout = QHBoxLayout(intro_card)
        intro_layout.setContentsMargins(18, 16, 18, 16)
        intro_layout.setSpacing(12)

        intro_icon = QLabel()
        intro_icon.setFixedSize(40, 40)
        intro_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = str(TOOGLE_ICON_PATH)
        if os.path.exists(icon_path):
            if icon_path not in _ICON_CACHE:
                _ICON_CACHE[icon_path] = QPixmap(icon_path).scaled(
                    22, 22, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
            intro_icon.setPixmap(_ICON_CACHE[icon_path])
        else:
            intro_icon.setText("T")
        intro_icon.setStyleSheet(
            f"background-color: {styles.COLOR_SELECT_BG}; border: 1px solid {styles.COLOR_BORDER_LIGHT}; border-radius: 12px;"
        )
        intro_layout.addWidget(intro_icon)

        intro_text = QLabel("Сервисы вынесены в отдельные карточки, чтобы сложные операции запускались быстрее и считывались без перегруза интерфейса.")
        intro_text.setObjectName("StatHint")
        intro_text.setWordWrap(True)
        intro_layout.addWidget(intro_text, 1)
        layout.addWidget(intro_card)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        services = [
            ("Авторизация сессий", "Массовый вход по номеру телефона с получением рабочих `.session` файлов.", str(PHONE_ICON_PATH), "Sessions", self.main_window.open_session_manager),
            ("Масс-создание сессий", "Создание дополнительных `.session` по существующим аккаунтам с автополучением кода из `777000` и 2FA из базы.", str(PHONE_ICON_PATH), "Sessions", self.main_window.open_mass_session_creator),
            ("Покупка Lolzteam", "Автоматическая закупка Telegram-аккаунтов с Lolz Market (Зеленка) с распределением сессий и прокси.", str(ROCKET_ICON_PATH), "Market", self.main_window.open_lolz_buyer),
            ("Экспорт в Agregator", "Автоматическая сборка `config.json` и выгрузка `.session` файлов для `Agregator-Viewer-soft`.", str(REFRESH_ICON_PATH), "Export", self.main_window.open_agregator_prep),
            ("Fallback API", "Назначение локальных vetted fallback-пар `api_id` / `api_hash` для аккаунтов.", str(KEY_ICON_PATH), "API", self.main_window.open_api_generator),
            ("Масс-реггер профилей", "Пакетное создание профилей фермы с первичной структурой и данными.", str(PEAPLE_ICON_PATH), "Profiles", self.main_window.open_mass_profile_creator),
            ("Конвертер TData", "Преобразование профилей Telegram Desktop в формат, пригодный для автоматизации.", str(REFRESH_ICON_PATH), "Convert", self.main_window.open_tdata_converter),
            ("Конвертер Telethon", "Перевод Telethon-сессий в формат Hydrogram/Pyrogram для текущей фермы.", str(REBOOT_ICON_PATH), "Convert", self.main_window.open_telethon_converter),
            ("Имена устройств", "Генерация и обновление `device model`, чтобы профили выглядели правдоподобнее.", str(PHONE_ICON_PATH), "Fingerprint", self.main_window.open_device_generator),
            ("Генератор промптов", "Подготовка индивидуальных AI-промптов для аккаунтов и сценариев.", str(ROBOT_ICON_PATH), "AI", self.main_window.open_prompt_generator),
            ("Экспорт номеров", "Выгрузка всех найденных номеров телефонов в отдельный текстовый файл.", str(CALL_ICON_PATH), "Export", self.main_window.export_phone_numbers),
        ]

        columns = 2
        for index, service in enumerate(services):
            row = index // columns
            col = index % columns
            card = ServiceCard(*service)
            grid.addWidget(card, row, col)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch((len(services) + columns - 1) // columns, 1)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
