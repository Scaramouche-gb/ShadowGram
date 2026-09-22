# 🚜 Фермы и аккаунты (Farms & Accounts)

Управление пулами аккаунтов в ShadowGram организовано по принципу независимых пространств (ферм). Каждая ферма содержит свои аккаунты, собственные конфигурации прокси и выделенные рабочие каталоги.

---

## 1. Файловая структура фермы

Все фермы (кроме корневой `default`) располагаются в директории `farms/`:

```
farms/
├── .gitkeep
└── MF2/                           # Имя фермы
    ├── config.json                # Конфигурация аккаунтов и параметров фермы
    └── accounts/                  # Рабочие директории аккаунтов
        ├── acc1/
        │   ├── acc1.session       # Telethon / Hydrogram сессия
        │   ├── tdata/             # Профиль Telegram Desktop (нативный)
        │   ├── avatar.jpg         # Аватар профиля
        │   ├── proxychains.conf   # Сгенерированный конфиг маршрутизации
        │   ├── gost.yaml          # Конфигурация локального Gost туннеля
        │   └── .tz_bwrap          # Кэшированный часовой пояс для bwrap
        └── acc2/
            └── ...
```

Текущая выбранная ферма фиксируется в файле `active_farm.txt` в корне проекта (например: `MF2`).

---

## 2. Структура записи аккаунта в `config.json`

Каждый аккаунт описывается JSON-объектом:

```json
{
  "name": "acc1",
  "workdir": "/home/user/ShadowGram/farms/MF2/accounts/acc1",
  "proxy_url": "http://user:pass@192.168.1.100:8080",
  "device_name": "Razer Blade 16",
  "api_id": "10840",
  "api_hash": "33c45224029d59cb3889c8969766562b",
  "hardware_profile": {
    "device_model": "Mac Studio",
    "system_version": "macOS 14.1",
    "app_version": "10.1.1",
    "lang_code": "en"
  },
  "first_name": "John",
  "last_name": "Doe",
  "phone": "15752166372",
  "password": "Cloud2FAPassword",
  "username": "johndoe_tg",
  "is_valid": true,
  "status": "ГОТОВ"
}
```

---

## 3. Сессии: `.session` и `tdata`

ShadowGram поддерживает работу как через официальный десктопный клиент Telegram, так и через прямой MTProto протокол:

1. **`.session` (SQLite формат Telethon / Hydrogram / Pyrogram):**
   - Используется модулями автоматизации, скриптами и `NodeScenarioExecutor`.
   - Не требует запущенного GUI, потребляет минимально ресурсов процессора и памяти.
2. **`tdata` (Telegram Desktop):**
   - Бинарная папка сессии для нативного запуска клиента Telegram.
   - Запускается через `process_manager.py` с изоляцией `bwrap`/`firejail` и аргументом `-workdir <account_path>`.

---

## 4. Аппаратный профиль и маскировка (Hardware Profile)

Для предотвращения ассоциации всех аккаунтов с одним хостом система генерирует уникальный профиль (`hw_manager.py`):
- **DMI Fake Data:** генерируются виртуальные дескрипторы для `/sys/devices/virtual/dmi/id/sys_vendor` и `product_name`.
- **Hostname / UTS:** подменяется имя машины внутри песочницы (`--unshare-uts --hostname <device_name>`).
- **Таймзона и локаль:** подменяется `/etc/localtime` (на базе страны IP-адреса прокси) и переменная `LC_ALL` / `LANG`.

---

## 5. Сеть и привязка прокси

Для каждого аккаунта может быть назначен индивидуальный HTTP или SOCKS5 прокси:
1. При запуске Telegram Desktop поднимается локальный маршрутизатор `gost` (v3), пробрасывающий локальный порт на внешний прокси.
2. Генерируется изолированный `proxychains.conf` для перехвата сетевых системных вызовов (`connect()`).
3. Запуск осуществляется через команду `proxychains4 -f <path>/proxychains.conf Telegram -workdir <path>`.
