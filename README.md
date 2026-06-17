<div align="center">

# 🛎️ ss.lv Monitor Bot

**A Telegram bot that watches the entire [ss.lv](https://www.ss.lv) classifieds catalogue and pings you the moment a new listing matches your filters.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.13-2CA5E0?logo=telegram&logoColor=white)](https://docs.aiogram.dev)
[![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![CI](https://github.com/AAvlasins-dev/sslv-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/AAvlasins-dev/sslv-bot/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Viewing%20only-red)](#-license)

🇬🇧 [English](#-english) · 🇷🇺 [Русский](#-русский) · 🇱🇻 [Latviešu](#-latviešu)

</div>

---

<a name="-english"></a>
## 🇬🇧 English

### What it does

You pick *what* to watch on ss.lv — **any category, any subcategory, any filter** — and the bot keeps polling in the background and sends you a Telegram notification the second a fresh matching ad appears. Cars, real estate, electronics, jobs, animals, services… the whole site.

Each notification includes a direct link, price, posting date, the seller's city **and the distance from you to the seller in km**.

### ✨ Key features

| | Feature |
|---|---|
| 🌐 | **Monitors the entire ss.lv** — all 12 top categories and ~7,600+ end subcategories, navigated **dynamically** (no hard-coded tree — the menu mirrors the live site) |
| 🎛️ | **Real per-category filters** — the bot scrapes each category's actual ss.lv filter form (price, year, mileage, fuel, gearbox, body, colour, console, condition, location…) and lets you set them |
| 📍 | **Distance to seller** — set your location once (`/location`); every notification shows how far the seller is, via a built-in 100+ Latvian-city geocoder + OpenStreetMap fallback |
| 📅 | **Smart date parsing** — understands ss.lv formats (`сегодня`, `vakar`, `DD.MM.YYYY`) and pulls the exact publish time from each ad |
| 🗣️ | **Trilingual UI** — Russian, Latvian, English, switchable on the fly |
| 🔔 | **Instant, de-duplicated alerts** — never the same ad twice; per-filter check interval (1 min … 2 h) |
| 💾 | **Persistent** — filters and seen-ads live in SQLite, survive restarts |
| 🐳 | **Production-ready** — Docker / docker-compose, Railway config, GitHub Actions CI, unit tests |

### 💬 Example notification

```
🆕 BMW 5 series

BMW 520d Touring xDrive
2019 | 2.0 D | 130 000 km | Automatic
💰 22 500 €
📅 Today at 09:12
📍 Jelgava — 43 km from you

Open listing →
```

### 🧠 How it works (the interesting part)

Two problems made this more than a simple scraper:

1. **ss.lv has no public API and an inconsistent, deeply-nested category tree.**
   Instead of hard-coding thousands of URLs, the bot treats the site as a graph: a single generic crawler walks it via the site's own navigation markup (`a.a_category` links **and** the `<select>` model drop-downs), recursing until it reaches a listing page. Pick *Transport → Cars → BMW → 320 → Diesel* or *Real estate → Flats → Rīga → Centre* — same code path, any depth.

2. **ss.lv filtering is POST/session-based — you can't reproduce a filtered view from a saved URL.**
   So filtering is done **client-side**: the bot parses the listing table into named columns (price, year, console, condition…) and filters there; attributes that only live on the ad page (gearbox, body type, colour, fuel) are matched on-demand from the ad card the monitor already fetches for the date & city — **zero extra requests**.

### 🕹️ Commands

| Command | Action |
|---|---|
| `/start` | start / main menu |
| `/add` | add a filter (menu mirrors ss.lv) |
| `/list` | view & delete filters |
| `/stats` | monitoring statistics |
| `/location` | set your location (GPS or city name) |
| `/lang` | switch interface language |
| `/cancel` | cancel current action |

---

<a name="-русский"></a>
## 🇷🇺 Русский

### Что делает

Ты выбираешь, *что* отслеживать на ss.lv — **любую категорию, подкатегорию, любой фильтр** — а бот в фоне опрашивает сайт и присылает уведомление в Telegram, как только появляется новое подходящее объявление. Авто, недвижимость, электроника, работа, животные, услуги… весь сайт.

В каждом уведомлении — прямая ссылка, цена, дата публикации, город продавца **и расстояние от тебя до него в км**.

### ✨ Возможности

| | Возможность |
|---|---|
| 🌐 | **Мониторит весь ss.lv** — все 12 разделов и ~7 600+ конечных подкатегорий, навигация **динамическая** (дерево не захардкожено — меню повторяет живой сайт) |
| 🎛️ | **Реальные фильтры каждой категории** — бот скрейпит настоящую форму фильтра ss.lv (цена, год, пробег, топливо, КПП, кузов, цвет, консоль, состояние, местоположение…) |
| 📍 | **Расстояние до продавца** — задаёшь своё место один раз (`/location`), и каждое уведомление показывает, сколько км до продавца (встроенная база 100+ городов Латвии + OpenStreetMap-фолбэк) |
| 📅 | **Парсинг даты** — понимает форматы ss.lv (`сегодня`, `vakar`, `DD.MM.YYYY`) и достаёт точное время публикации |
| 🗣️ | **Три языка** — русский, латышский, английский, переключаются на лету |
| 🔔 | **Мгновенные уведомления без дублей** — одно объявление никогда не придёт дважды; свой интервал проверки на каждый фильтр (1 мин … 2 ч) |
| 💾 | **Сохранность** — фильтры и просмотренные объявления в SQLite, переживают перезапуск |
| 🐳 | **Готов к продакшену** — Docker / docker-compose, конфиг Railway, CI на GitHub Actions, юнит-тесты |

### 💬 Пример уведомления

```
🆕 BMW 5 серия

BMW 520d Touring xDrive
2019 | 2.0 D | 130 000 км | Автомат
💰 22 500 €
📅 Сегодня в 09:12
📍 Jelgava — 43 км от вас

Открыть объявление →
```

### 🧠 Как это устроено (самое интересное)

Две задачи сделали проект сложнее обычного скрапера:

1. **У ss.lv нет публичного API, а дерево категорий — глубокое и неоднородное.**
   Вместо тысяч захардкоженных URL бот рассматривает сайт как граф: один универсальный краулер обходит его по родной навигации сайта (ссылки `a.a_category` **и** выпадающие списки моделей `<select>`), спускаясь до страницы с объявлениями. *Транспорт → Авто → BMW → 320 → Дизель* или *Недвижимость → Квартиры → Рига → Центр* — один и тот же код, любая глубина.

2. **Фильтрация ss.lv работает через POST/сессию — отфильтрованную выдачу нельзя воспроизвести сохранённым URL.**
   Поэтому фильтрация **на стороне бота**: таблица объявлений разбирается на именованные колонки (цена, год, консоль, состояние…) и фильтруется там; характеристики, которые есть только в карточке (КПП, кузов, цвет, топливо), матчатся из карточки, которую монитор и так загружает ради даты и города — **без лишних запросов**.

### 🕹️ Команды

| Команда | Действие |
|---|---|
| `/start` | запуск / главное меню |
| `/add` | добавить фильтр (меню повторяет ss.lv) |
| `/list` | список и удаление фильтров |
| `/stats` | статистика мониторинга |
| `/location` | задать местоположение (GPS или город) |
| `/lang` | сменить язык интерфейса |
| `/cancel` | отменить текущее действие |

---

<a name="-latviešu"></a>
## 🇱🇻 Latviešu

### Ko tas dara

Tu izvēlies, *ko* sekot ss.lv — **jebkuru kategoriju, apakškategoriju, jebkuru filtru** — un bots fonā regulāri pārbauda vietni un nosūta Telegram paziņojumu, tiklīdz parādās jauns atbilstošs sludinājums. Auto, nekustamais īpašums, elektronika, darbs, dzīvnieki, pakalpojumi… visa vietne.

Katrā paziņojumā ir tieša saite, cena, publicēšanas datums, pārdevēja pilsēta **un attālums no tevis līdz pārdevējam kilometros**.

### ✨ Galvenās funkcijas

| | Funkcija |
|---|---|
| 🌐 | **Uzrauga visu ss.lv** — visas 12 sadaļas un ~7 600+ gala apakškategorijas, navigācija ir **dinamiska** (koks nav iekodēts — izvēlne atspoguļo dzīvo vietni) |
| 🎛️ | **Reālie katras kategorijas filtri** — bots nolasa īsto ss.lv filtru formu (cena, gads, nobraukums, degviela, ātrumkārba, virsbūve, krāsa, konsole, stāvoklis, atrašanās vieta…) |
| 📍 | **Attālums līdz pārdevējam** — norādi savu atrašanās vietu vienreiz (`/location`), un katrs paziņojums rāda attālumu km (iebūvēta 100+ Latvijas pilsētu datubāze + OpenStreetMap rezerves variants) |
| 📅 | **Datuma parsēšana** — saprot ss.lv formātus (`šodien`, `vakar`, `DD.MM.GGGG`) un izvelk precīzu publicēšanas laiku |
| 🗣️ | **Trīs valodas** — krievu, latviešu, angļu, pārslēdzamas uzreiz |
| 🔔 | **Tūlītēji paziņojumi bez dublikātiem** — viens sludinājums nekad nepienāks divreiz; atsevišķs pārbaudes intervāls katram filtram (1 min … 2 h) |
| 💾 | **Saglabāšana** — filtri un redzētie sludinājumi SQLite datubāzē, pārdzīvo pārstartēšanu |
| 🐳 | **Gatavs ražošanai** — Docker / docker-compose, Railway konfigurācija, GitHub Actions CI, vienībtesti |

### 💬 Paziņojuma piemērs

```
🆕 BMW 5. sērija

BMW 520d Touring xDrive
2019 | 2.0 D | 130 000 km | Automāts
💰 22 500 €
📅 Šodien plkst. 09:12
📍 Jelgava — 43 km no tevis

Atvērt sludinājumu →
```

### 🧠 Kā tas darbojas (interesantākais)

Divas problēmas padarīja šo par vairāk nekā parastu skreperi:

1. **ss.lv nav publiska API, un kategoriju koks ir dziļš un nevienmērīgs.**
   Tā vietā, lai iekodētu tūkstošiem URL, bots uztver vietni kā grafu: viens universāls rāpotājs to apstaigā pa pašas vietnes navigāciju (`a.a_category` saites **un** `<select>` modeļu izvēlnes), nokāpjot līdz sludinājumu lapai. *Transports → Auto → BMW → 320 → Dīzelis* vai *Nekustamais īpašums → Dzīvokļi → Rīga → Centrs* — viens un tas pats kods, jebkurš dziļums.

2. **ss.lv filtrēšana darbojas caur POST/sesiju — filtrētu skatu nevar atveidot ar saglabātu URL.**
   Tāpēc filtrēšana notiek **bota pusē**: sludinājumu tabula tiek sadalīta nosauktās kolonnās (cena, gads, konsole, stāvoklis…) un filtrēta tur; pazīmes, kas ir tikai sludinājuma kartē (ātrumkārba, virsbūve, krāsa, degviela), tiek salīdzinātas no kartes, ko monitors jau ielādē datuma un pilsētas dēļ — **bez liekiem pieprasījumiem**.

### 🕹️ Komandas

| Komanda | Darbība |
|---|---|
| `/start` | palaišana / galvenā izvēlne |
| `/add` | pievienot filtru (izvēlne atspoguļo ss.lv) |
| `/list` | filtru saraksts un dzēšana |
| `/stats` | uzraudzības statistika |
| `/location` | norādīt atrašanās vietu (GPS vai pilsēta) |
| `/lang` | mainīt saskarnes valodu |
| `/cancel` | atcelt pašreizējo darbību |

---

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Bot framework | **aiogram 3.13** (async, FSM) |
| HTTP / scraping | **aiohttp** + **BeautifulSoup4** + **lxml** |
| Database | **SQLite** via **aiosqlite** |
| Geocoding | built-in 100+ LV city table + OpenStreetMap **Nominatim** fallback |
| Config | **python-dotenv** |
| Packaging | **Docker** + **docker-compose**, **Railway** |
| Quality | **pytest** unit tests + **GitHub Actions** CI |

## 🗂️ Project structure

```
sslv-bot/
├── main.py            # entry point — bot polling + background monitor + cache preload
├── bot.py             # Telegram UI: commands, inline menus, FSM, recursive category drill-down
├── parser.py          # ss.lv scraper — categories, filters, listings, ad cards, date parsing
├── monitor.py         # background loop: poll → filter → de-dup → notify
├── geo.py             # haversine distance + Latvian-city geocoder
├── db.py              # SQLite layer (users, filters, seen_ads)
├── cache.py           # in-memory cache + startup preload
├── categories.py      # top-level category map & fallbacks
├── filters_config.py  # range-filter presets (price/year/mileage…)
├── i18n.py            # RU / LV / EN translations
├── config.py          # env configuration
├── tests/             # unit tests (geo + date parsing)
└── .github/workflows/ # CI
```

## 🚀 Run it

**1. Get a bot token** from [@BotFather](https://t.me/BotFather).

**2. Configure** — copy `.env.example` to `.env` and put your token in:

```bash
cp .env.example .env      # then edit BOT_TOKEN=...
```

**Local (Python 3.12):**

```bash
pip install -r requirements.txt
python main.py
```

**Docker:**

```bash
docker compose up -d        # runs 24/7, restarts on failure
```

### ⚙️ Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | — | Telegram bot token (required) |
| `DB_PATH` | `data.db` | SQLite database path |
| `CHECK_INTERVAL_SEC` | `120` | base polling interval |
| `MAX_NOTIFICATIONS_PER_CYCLE` | `10` | anti-spam cap per filter per cycle |
| `SS_LANG` | `ru` | ss.lv locale used for scraping (`ru` / `lv`) |

## ☁️ Deployment

The bot is a long-running process (Telegram long-polling), so it needs an **always-on host** — not a serverless/CI runner. The repo ships a `Dockerfile` (with a persistent volume for the SQLite DB) and a `railway.toml`, so going live is a few clicks.

**Railway** (one-click from this repo):

1. *New Project → Deploy from GitHub repo → `sslv-bot`* — Railway auto-detects the `Dockerfile` + `railway.toml`.
2. Add the `BOT_TOKEN` variable.
3. Mount a volume at `/app/data` so saved filters survive redeploys.

It runs anywhere Docker does — Fly.io, a VPS, even a Raspberry Pi:

```bash
docker compose up -d        # runs 24/7, auto-restarts on failure
```

## ✅ Tests & CI

```bash
pytest -q        # 33 unit tests (distance math + ss.lv date parsing)
```

GitHub Actions runs the suite on every push (`.github/workflows/ci.yml`).

## 📜 License

© 2026 — **All Rights Reserved**. This repository is published **for portfolio / evaluation viewing only**; copying, modifying, or redistributing the code is not permitted without written permission. See [LICENSE](LICENSE).
