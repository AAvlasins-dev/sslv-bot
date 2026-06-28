"""
Переводы интерфейса бота. Интерфейс — два языка: русский и латышский.
(Английский остаётся только в README на GitHub, в боте его нет.)
Использование: T[lang]["ключ"] или t(lang, "ключ", **kwargs)
"""
import re
from typing import Optional

# Языки интерфейса бота (выбор в /lang). Английский намеренно не предлагаем —
# латышские названия ss.lv отдаёт нативно, а англоязычные подписи фильтров
# пришлось бы вести вручную. Любой иной код приводится к ru.
LANGS = {
    "ru": "🇷🇺 Русский",
    "lv": "🇱🇻 Latviešu",
}

# Команды бота (меню «/») по языкам — только ru/lv. По умолчанию русское,
# при выборе языка в боте меню переключается на выбранный (per-chat).
BOT_COMMANDS: dict[str, list[tuple[str, str]]] = {
    "ru": [
        ("start",    "🚀 Запустить бота"),
        ("add",      "➕ Добавить фильтр"),
        ("list",     "📋 Мои фильтры"),
        ("stats",    "📊 Статистика"),
        ("location", "📍 Моё местоположение"),
        ("lang",     "🌐 Выбрать язык"),
        ("diag",     "🩺 Диагностика"),
        ("cancel",   "❌ Отмена"),
    ],
    "lv": [
        ("start",    "🚀 Palaist botu"),
        ("add",      "➕ Pievienot filtru"),
        ("list",     "📋 Mani filtri"),
        ("stats",    "📊 Statistika"),
        ("location", "📍 Mana atrašanās vieta"),
        ("lang",     "🌐 Valoda"),
        ("diag",     "🩺 Diagnostika"),
        ("cancel",   "❌ Atcelt"),
    ],
}

# ss.lv URL prefix per language. ss.lv отдаёт ВСЕ три языка нативно
# (/ru/, /lv/, /en/) с переведёнными названиями категорий/марок/моделей —
# имена тянем с нужного префикса (см. parser._loc), а внутренние URL для
# мониторинга держим каноничными на /ru/.
SS_PREFIX = {"ru": "/ru", "lv": "/lv", "en": "/en"}
SS_LANG_URL = {"ru": "ru", "lv": "lv", "en": "en"}


T: dict[str, dict[str, str]] = {

    # ── Приветствие / Start ────────────────────────────────────────────────
    "start": {
        "ru": (
            "👋 <b>ss.lv Monitor</b> — мониторю любые объявления.\n\n"
            "Моё местоположение: {loc}\n\n"
            "/add       — добавить фильтр\n"
            "/list      — мои фильтры\n"
            "/stats     — статистика\n"
            "/location  — моё местоположение\n"
            "/lang      — сменить язык\n"
            "/cancel    — отмена"
        ),
        "lv": (
            "👋 <b>ss.lv Monitor</b> — uzraugu jebkādus sludinājumus.\n\n"
            "Mana atrašanās vieta: {loc}\n\n"
            "/add       — pievienot filtru\n"
            "/list      — mani filtri\n"
            "/stats     — statistika\n"
            "/location  — mana atrašanās vieta\n"
            "/lang      — mainīt valodu\n"
            "/cancel    — atcelt"
        ),
        "en": (
            "👋 <b>ss.lv Monitor</b> — monitoring any listings.\n\n"
            "My location: {loc}\n\n"
            "/add       — add filter\n"
            "/list      — my filters\n"
            "/stats     — statistics\n"
            "/location  — set location\n"
            "/lang      — change language\n"
            "/cancel    — cancel"
        ),
    },

    "lang_pick": {
        "ru": "🌐 Выбери язык интерфейса:",
        "lv": "🌐 Izvēlies saskarnes valodu:",
        "en": "🌐 Choose interface language:",
    },
    "lang_set": {
        "ru": "✅ Язык изменён на <b>Русский</b>",
        "lv": "✅ Valoda mainīta uz <b>Latviešu</b>",
        "en": "✅ Language changed to <b>English</b>",
    },

    "choose_cat": {
        "ru": "Выбери категорию:",
        "lv": "Izvēlies kategoriju:",
        "en": "Choose a category:",
    },
    "choose_subcat": {
        "ru": "Выбери подкатегорию",
        "lv": "Izvēlies apakškategoriju",
        "en": "Choose a subcategory",
    },
    "monitor_all": {
        "ru": "✅ Весь раздел",
        "lv": "✅ Visa sadaļa",
        "en": "✅ Whole section",
    },
    "choose_brand": {
        "ru": "Выбери марку",
        "lv": "Izvēlies marku",
        "en": "Choose a brand",
    },
    "choose_model": {
        "ru": "Выбери модель",
        "lv": "Izvēlies modeli",
        "en": "Choose a model",
    },
    "choose_district": {
        "ru": "Выбери район",
        "lv": "Izvēlies rajonu",
        "en": "Choose a district",
    },
    "loading_brands": {
        "ru": "⏳ Загружаю марки…",
        "lv": "⏳ Ielādēju markas…",
        "en": "⏳ Loading brands…",
    },
    "loading_models": {
        "ru": "⏳ Загружаю модели… (до 7 сек)",
        "lv": "⏳ Ielādēju modeļus… (līdz 7 sek)",
        "en": "⏳ Loading models… (up to 7 sec)",
    },
    "models_found": {
        "ru": "✅ {n} моделей",
        "lv": "✅ {n} modeļi",
        "en": "✅ {n} models",
    },
    "models_failed": {
        "ru": "⚠️ Не загрузились — выбери «Любая»",
        "lv": "⚠️ Neizdevās ielādēt — izvēlies «Jebkurš»",
        "en": "⚠️ Failed to load — choose «Any»",
    },
    "any_model": {
        "ru": "🔘 Любая модель",
        "lv": "🔘 Jebkurš modelis",
        "en": "🔘 Any model",
    },
    "any_brand": {
        "ru": "🔘 Любая марка",
        "lv": "🔘 Jebkura marka",
        "en": "🔘 Any brand",
    },
    "region_btn":  {"ru": "📍 Регион", "lv": "📍 Reģions", "en": "📍 Region"},
    "radius_btn":  {"ru": "📍 Радиус", "lv": "📍 Rādiuss", "en": "📍 Radius"},
    "any_region":  {"ru": "🔘 Любой",  "lv": "🔘 Jebkurš", "en": "🔘 Any"},
    "region_title": {
        "ru": "📍 Выбери регион (фильтр по городу из объявления):",
        "lv": "📍 Izvēlies reģionu (filtrs pēc pilsētas sludinājumā):",
        "en": "📍 Pick a region (filters by the ad's city):",
    },
    "region_none": {
        "ru": "⚠️ Для этого раздела регионы недоступны. Попробуй радиус от себя.",
        "lv": "⚠️ Šai sadaļai reģioni nav pieejami. Mēģini rādiusu no sevis.",
        "en": "⚠️ No regions for this section. Try a radius from you.",
    },
    "radius_hint": {
        "ru": "📍 <b>Радиус от твоего местоположения</b>\nПришлю только объявления в пределах N км.\n(Нужно задать /location.)",
        "lv": "📍 <b>Rādiuss no tavas atrašanās vietas</b>\nSūtīšu tikai sludinājumus N km rādiusā.\n(Nepieciešams /location.)",
        "en": "📍 <b>Radius from your location</b>\nI'll send only listings within N km.\n(Set /location first.)",
    },
    "region_lbl":  {"ru": "📍 Регион", "lv": "📍 Reģions", "en": "📍 Region"},
    "radius_lbl":  {"ru": "📍 Радиус", "lv": "📍 Rādiuss", "en": "📍 Radius"},
    "district_lbl": {"ru": "📍 Район", "lv": "📍 Rajons", "en": "📍 District"},
    "any_district": {"ru": "🔘 Весь регион", "lv": "🔘 Viss reģions", "en": "🔘 Whole region"},
    "district_title": {
        "ru": "📍 Выбери район ({region}):",
        "lv": "📍 Izvēlies rajonu ({region}):",
        "en": "📍 Pick a district ({region}):",
    },
    "all_riga": {
        "ru": "🌆 Вся Рига",
        "lv": "🌆 Visa Rīga",
        "en": "🌆 All Riga",
    },
    "input_brand": {
        "ru": "✏️ Напиши марку:",
        "lv": "✏️ Ieraksti marku:",
        "en": "✏️ Type the brand:",
    },
    "input_model": {
        "ru": "✏️ Напиши модель:",
        "lv": "✏️ Ieraksti modeli:",
        "en": "✏️ Type the model:",
    },
    "input_manual": {
        "ru": "✏️ Ввести вручную",
        "lv": "✏️ Ievadīt manuāli",
        "en": "✏️ Enter manually",
    },
    "filters_title": {
        "ru": "Настрой фильтры и нажми <b>✅ Сохранить</b>.",
        "lv": "Noregulē filtrus un nospied <b>✅ Saglabāt</b>.",
        "en": "Set your filters then press <b>✅ Save</b>.",
    },
    "price": {"ru": "💶 Цена €",    "lv": "💶 Cena €",   "en": "💶 Price €"},
    "year":  {"ru": "📅 Год",       "lv": "📅 Gads",     "en": "📅 Year"},
    "mileage":{"ru":"🛣 Пробег км",  "lv": "🛣 Nobraukums km","en": "🛣 Mileage km"},
    "gearbox":{"ru":"⚙️ КПП",       "lv": "⚙️ Ātr.kārba", "en": "⚙️ Gearbox"},
    "bodytype":{"ru":"🚙 Кузов",    "lv": "🚙 Virsbūve",  "en": "🚙 Body type"},
    "keyword": {"ru":"🔎 Слово",    "lv": "🔎 Vārds",     "en": "🔎 Keyword"},
    "interval_label":{"ru":"⏱ Интервал","lv":"⏱ Intervāls","en":"⏱ Interval"},
    "reset_all":{"ru":"🧹 Сбросить всё","lv":"🧹 Atiestatīt visu","en":"🧹 Reset all"},
    "save": {"ru": "✅ Сохранить", "lv": "✅ Saglabāt", "en": "✅ Save"},
    "cancel":{"ru": "❌ Отмена",   "lv": "❌ Atcelt",   "en": "❌ Cancel"},
    "back":  {"ru": "◀ Назад",    "lv": "◀ Atpakaļ",  "en": "◀ Back"},
    "clear": {"ru": "🗑 Очистить","lv": "🗑 Dzēst",    "en": "🗑 Clear"},
    "set_interval":{"ru": "⏱ Интервал","lv":"⏱ Intervāls","en":"⏱ Check interval"},

    "price_hint": {
        "ru": "💶 <b>Цена €</b>\nПример: <code>1000-5000</code>  или  <code>-8000</code>  или  <code>2000-</code>",
        "lv": "💶 <b>Cena €</b>\nPiemērs: <code>1000-5000</code>  vai  <code>-8000</code>  vai  <code>2000-</code>",
        "en": "💶 <b>Price €</b>\nExample: <code>1000-5000</code>  or  <code>-8000</code>  or  <code>2000-</code>",
    },
    "year_hint": {
        "ru": "📅 <b>Год выпуска</b>\nПример: <code>2015-2022</code>  или  <code>2018-</code>",
        "lv": "📅 <b>Izlaiduma gads</b>\nPiemērs: <code>2015-2022</code>  vai  <code>2018-</code>",
        "en": "📅 <b>Year</b>\nExample: <code>2015-2022</code>  or  <code>2018-</code>",
    },
    "mileage_hint": {
        "ru": "🛣 <b>Пробег км</b>\nПример: <code>50000-200000</code>",
        "lv": "🛣 <b>Nobraukums km</b>\nPiemērs: <code>50000-200000</code>",
        "en": "🛣 <b>Mileage km</b>\nExample: <code>50000-200000</code>",
    },
    "keyword_hint": {
        "ru": "🔎 <b>Ключевое слово</b>\nИщу в тексте объявления.\nПример: <code>quattro</code>, <code>ps5</code>, <code>panorama</code>",
        "lv": "🔎 <b>Atslēgvārds</b>\nMeklēju sludinājuma tekstā.\nPiemērs: <code>quattro</code>, <code>panorama</code>",
        "en": "🔎 <b>Keyword</b>\nSearched in listing text.\nExample: <code>quattro</code>, <code>ps5</code>, <code>panorama</code>",
    },
    "gearbox_title": {
        "ru": "⚙️ <b>Коробка передач</b>:",
        "lv": "⚙️ <b>Ātrumkārba</b>:",
        "en": "⚙️ <b>Gearbox</b>:",
    },
    "bodytype_title": {
        "ru": "🚙 <b>Тип кузова</b>:",
        "lv": "🚙 <b>Virsbūves tips</b>:",
        "en": "🚙 <b>Body type</b>:",
    },
    "interval_title": {
        "ru": "⏱ <b>Как часто проверять ss.lv?</b>",
        "lv": "⏱ <b>Cik bieži pārbaudīt ss.lv?</b>",
        "en": "⏱ <b>How often to check ss.lv?</b>",
    },
    "saving": {
        "ru": "⏳ Сохраняю…",
        "lv": "⏳ Saglabāju…",
        "en": "⏳ Saving…",
    },
    "saved": {
        "ru": "✅ Фильтр <b>#{fid}</b> сохранён!\n📅 {date} · {period}: <b>{n}</b>\nДальше пришлю только новые.\n<a href='{url}'>Открыть на ss.lv →</a>",
        "lv": "✅ Filtrs <b>#{fid}</b> saglabāts!\n📅 {date} · {period}: <b>{n}</b>\nTurpmāk paziņošu tikai par jaunajiem.\n<a href='{url}'>Atvērt ss.lv →</a>",
        "en": "✅ Filter <b>#{fid}</b> saved!\n📅 {date} · {period}: <b>{n}</b>\nFrom now I'll alert only new ones.\n<a href='{url}'>Open on ss.lv →</a>",
    },
    "period_today": {"ru": "За сегодня", "lv": "Šodien",          "en": "Today"},
    "period_2":     {"ru": "За 2 дня",   "lv": "Pēdējās 2 dienās", "en": "Last 2 days"},
    "period_5":     {"ru": "За 5 дней",  "lv": "Pēdējās 5 dienās", "en": "Last 5 days"},
    "save_hub_warning": {
        "ru": "⚠️ В этом разделе нет объявлений напрямую — это меню подразделов.\nЗайди глубже и выбери подраздел со списком объявлений (или «🔎 Слово» в нём).",
        "lv": "⚠️ Šajā sadaļā nav sludinājumu tieši — tā ir apakšsadaļu izvēlne.\nIeej dziļāk un izvēlies apakšsadaļu ar sludinājumu sarakstu (vai «🔎 Vārds» tajā).",
        "en": "⚠️ This section has no listings directly — it's a subcategory menu.\nGo deeper and pick a subsection with an actual listing (or «🔎 Keyword» in it).",
    },
    "show_today_q": {
        "ru": "Показать эти объявления?",
        "lv": "Rādīt šos sludinājumus?",
        "en": "Show these listings?",
    },
    "yes": {"ru": "✅ Да", "lv": "✅ Jā", "en": "✅ Yes"},
    "no":  {"ru": "❌ Нет", "lv": "❌ Nē", "en": "❌ No"},
    "today_empty": {
        "ru": "За сегодня подходящих объявлений нет.",
        "lv": "Šodien atbilstošu sludinājumu nav.",
        "en": "No matching listings posted today.",
    },
    "diag_running": {
        "ru": "🩺 Проверяю работоспособность…",
        "lv": "🩺 Pārbaudu darbspēju…",
        "en": "🩺 Running self-test…",
    },
    "diag_title": {
        "ru": "🩺 <b>Самодиагностика</b>",
        "lv": "🩺 <b>Pašdiagnostika</b>",
        "en": "🩺 <b>Self-test</b>",
    },
    "diag_line": {
        "ru": "{ok} {icon} {ads} объявл. · сегодня {today}{chk}",
        "lv": "{ok} {icon} {ads} sludin. · šodien {today}{chk}",
        "en": "{ok} {icon} {ads} ads · today {today}{chk}",
    },
    "diag_send_ok": {
        "ru": "📨 Отправка сообщений: ✅",
        "lv": "📨 Ziņu sūtīšana: ✅",
        "en": "📨 Message delivery: ✅",
    },
    "diag_send_fail": {
        "ru": "📨 Отправка сообщений: ⚠️",
        "lv": "📨 Ziņu sūtīšana: ⚠️",
        "en": "📨 Message delivery: ⚠️",
    },
    "diag_filters": {
        "ru": "📋 Твои фильтры: <b>{n}</b> активных",
        "lv": "📋 Tavi filtri: <b>{n}</b> aktīvi",
        "en": "📋 Your filters: <b>{n}</b> active",
    },
    "diag_stuck": {
        "ru": "⚠️ Без объявлений (возможно, раздел-хаб): {ids}",
        "lv": "⚠️ Bez sludinājumiem (iespējams, sadaļa-izvēlne): {ids}",
        "en": "⚠️ No listings (possibly a hub section): {ids}",
    },
    "diag_fix_btn": {
        "ru": "🔧 Авто-починка",
        "lv": "🔧 Pašlabošana",
        "en": "🔧 Auto-heal",
    },
    "diag_fixed": {
        "ru": "🔧 Готово: кэш сброшен ({n} записей), фильтры перепроверятся в ближайшем цикле.",
        "lv": "🔧 Gatavs: kešs notīrīts ({n} ieraksti), filtri tiks pārbaudīti tuvākajā ciklā.",
        "en": "🔧 Done: cache cleared ({n} entries), filters will re-check on the next cycle.",
    },
    "today_retry": {
        "ru": "⚠️ ss.lv сейчас не ответил. Нажми «Открыть на ss.lv» или попробуй ещё раз позже.",
        "lv": "⚠️ ss.lv pašlaik neatbildēja. Spied «Atvērt ss.lv» vai mēģini vēlāk vēlreiz.",
        "en": "⚠️ ss.lv didn't respond. Tap «Open on ss.lv» or try again later.",
    },
    "today_done": {
        "ru": "👆 Это объявления за сегодня. Дальше — только новые.",
        "lv": "👆 Šodienas sludinājumi. Turpmāk — tikai jaunie.",
        "en": "👆 Today's listings. From now on — only new ones.",
    },
    "more_listings": {
        "ru": "…и ещё {n} подходящих за сегодня (показал первые 15).",
        "lv": "…un vēl {n} atbilstoši šodien (parādīju pirmos 15).",
        "en": "…and {n} more matching today (showed the first 15).",
    },
    "geo_note": {
        "ru": "📍 Это по всему разделу. По «Моё место» отфильтрую при показе и в уведомлениях.",
        "lv": "📍 Tas ir par visu sadaļu. Pēc «Mana vieta» atfiltrēšu rādot un paziņojumos.",
        "en": "📍 This is the whole section. I'll filter by «My place» on show and in alerts.",
    },
    "no_filters": {
        "ru": "Фильтров нет.\n/add — добавить первый.",
        "lv": "Filtru nav.\n/add — pievienot pirmo.",
        "en": "No filters yet.\n/add — add your first one.",
    },
    "filter_deleted": {
        "ru": "🗑 Фильтр #{fid} удалён.",
        "lv": "🗑 Filtrs #{fid} dzēsts.",
        "en": "🗑 Filter #{fid} deleted.",
    },
    "cancelled": {
        "ru": "Отменено.",
        "lv": "Atcelts.",
        "en": "Cancelled.",
    },
    "location_ask": {
        "ru": "📍 <b>Твоё местоположение</b>{cur}\n\nВыбери город кнопкой или напиши название:",
        "lv": "📍 <b>Tava atrašanās vieta</b>{cur}\n\nIzvēlies pilsētu vai ieraksti nosaukumu:",
        "en": "📍 <b>Your location</b>{cur}\n\nPick a city or type its name:",
    },
    "location_saved": {
        "ru": "✅ Сохранено!\n📍 <b>{name}</b>",
        "lv": "✅ Saglabāts!\n📍 <b>{name}</b>",
        "en": "✅ Saved!\n📍 <b>{name}</b>",
    },
    "location_notfound": {
        "ru": "❌ «{name}» не найден. Попробуй другое название.",
        "lv": "❌ «{name}» nav atrasts. Mēģini citu nosaukumu.",
        "en": "❌ «{name}» not found. Try another name.",
    },
    "city_page_title": {
        "ru": "📍 Выбери свой город / регион",
        "lv": "📍 Izvēlies pilsētu / reģionu",
        "en": "📍 Choose your city / region",
    },
    "place_title": {
        "ru": "📍 <b>Моё место</b>\nКак задать?",
        "lv": "📍 <b>Mana atrašanās vieta</b>\nKā norādīt?",
        "en": "📍 <b>My location</b>\nHow to set it?",
    },
    "place_gps": {
        "ru": "📍 Моя геолокация",
        "lv": "📍 Mana ģeolokācija",
        "en": "📍 My GPS location",
    },
    "place_cities": {
        "ru": "🏙 Список городов",
        "lv": "🏙 Pilsētu saraksts",
        "en": "🏙 City list",
    },
    "place_gps_ask": {
        "ru": "📍 Нажми кнопку ниже, чтобы поделиться геолокацией:",
        "lv": "📍 Nospied pogu zemāk, lai dalītos ar ģeolokāciju:",
        "en": "📍 Tap the button below to share your location:",
    },
    "place_radius_ask": {
        "ru": "📍 <b>{name}</b>\nВ каком радиусе присылать объявления?",
        "lv": "📍 <b>{name}</b>\nKādā rādiusā sūtīt sludinājumus?",
        "en": "📍 <b>{name}</b>\nWithin what radius to send listings?",
    },
    "city_gps_btn": {
        "ru": "📍 Отправить GPS",
        "lv": "📍 Nosūtīt GPS",
        "en": "📍 Send GPS location",
    },
    "city_type_btn": {
        "ru": "✏️ Написать название",
        "lv": "✏️ Ierakstīt nosaukumu",
        "en": "✏️ Type city name",
    },
    "what_monitor": {
        "ru": "Что мониторим?",
        "lv": "Ko uzraugam?",
        "en": "What to monitor?",
    },
    "stats_title": {
        "ru": "📊 <b>Статистика мониторинга</b>",
        "lv": "📊 <b>Uzraudzības statistika</b>",
        "en": "📊 <b>Monitoring statistics</b>",
    },
    "stats_empty": {
        "ru": "Фильтров нет. /add чтобы начать.",
        "lv": "Filtru nav. /add lai sāktu.",
        "en": "No filters. Use /add to start.",
    },
    "max_filters": {
        "ru": "⚠️ Достигнут лимит фильтров ({max}). Удали старый через /list.",
        "lv": "⚠️ Sasniegts filtru limits ({max}). Dzēs veco ar /list.",
        "en": "⚠️ Filter limit reached ({max}). Delete an old one via /list.",
    },
    "loc_not_set": {
        "ru": "📍 не задано",
        "lv": "📍 nav iestatīts",
        "en": "📍 not set",
    },
    "open_sslv": {
        "ru": "🔗 На ss.lv",
        "lv": "🔗 Uz ss.lv",
        "en": "🔗 On ss.lv",
    },
    "delete_btn": {
        "ru": "🗑 Удалить",
        "lv": "🗑 Dzēst",
        "en": "🗑 Delete",
    },
}


# Перевод названий фильтров ss.lv (которые скрейпятся по-русски) для показа.
# Матчинг остаётся по русской метке — это только отображение.
FILTER_LABELS: dict[str, dict[str, str]] = {
    "Консоль":          {"en": "Console",    "lv": "Konsole"},
    "Сост.":            {"en": "Cond.",      "lv": "Stāv."},
    "Состояние":        {"en": "Condition",  "lv": "Stāvoklis"},
    "Коробка передач":  {"en": "Gearbox",    "lv": "Ātrumkārba"},
    "Тип кузова":       {"en": "Body type",  "lv": "Virsbūve"},
    "Цвет":             {"en": "Colour",     "lv": "Krāsa"},
    "Двигатель":        {"en": "Fuel",       "lv": "Degviela"},
    "Привод":           {"en": "Drive",      "lv": "Piedziņa"},
    "Дни работы":       {"en": "Work days",  "lv": "Darba dienas"},
    "Местонахождение":  {"en": "Location",   "lv": "Atrašanās vieta"},
    "Серия":            {"en": "Series",     "lv": "Sērija"},
    "Тип двери":        {"en": "Door type",  "lv": "Durvju tips"},
    "Материал":         {"en": "Material",   "lv": "Materiāls"},
    "Размер":           {"en": "Size",       "lv": "Izmērs"},
    "Производитель":    {"en": "Maker",      "lv": "Ražotājs"},
}


def filter_label(label: str, lang: str) -> str:
    """Перевод метки фильтра для показа; для ru — как есть, иначе — из таблицы."""
    if lang == "ru":
        return label
    return FILTER_LABELS.get(label, {}).get(lang, label)


def t(lang: str, key: str, **kwargs) -> str:
    """Get translated string for the given lang and key."""
    lang = lang if lang in ("ru", "lv") else "ru"
    msg = T.get(key, {}).get(lang) or T.get(key, {}).get("ru") or key
    if kwargs:
        try:
            msg = msg.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return msg


# ── Category labels per language ─────────────────────────────────────────────
CAT_LABELS: dict[str, dict[str, str]] = {
    "transport":  {"ru": "🚗 Транспорт",           "lv": "🚗 Transports",         "en": "🚗 Transport"},
    "work":       {"ru": "💼 Работа и бизнес",      "lv": "💼 Darbs un bizness",    "en": "💼 Jobs & Business"},
    "realty":     {"ru": "🏠 Недвижимость",         "lv": "🏠 Nekustamais īpašums", "en": "🏠 Real Estate"},
    "construct":  {"ru": "🏗 Строительство",        "lv": "🏗 Celtniecība",         "en": "🏗 Construction"},
    "electro":    {"ru": "📱 Электротехника",        "lv": "📱 Elektronika",          "en": "📱 Electronics"},
    "clothing":   {"ru": "👗 Одежда, обувь",         "lv": "👗 Apģērbs, apavi",      "en": "👗 Clothing & Shoes"},
    "home":       {"ru": "🛋 Для дома",             "lv": "🛋 Mājai",               "en": "🛋 Home & Garden"},
    "children":   {"ru": "🧸 Для детей",            "lv": "🧸 Bērniem",             "en": "🧸 For Children"},
    "animals":    {"ru": "🐕 Животные",             "lv": "🐕 Dzīvnieki",           "en": "🐕 Animals"},
    "agro":       {"ru": "🚜 Сельское хозяйство",   "lv": "🚜 Lauksaimniecība",     "en": "🚜 Agriculture"},
    "leisure":    {"ru": "🎮 Отдых, увлечения",     "lv": "🎮 Atpūta, hobiji",      "en": "🎮 Leisure & Hobbies"},
    "production": {"ru": "🏭 Производство",         "lv": "🏭 Ražošana",            "en": "🏭 Production"},
}

# Subcategory translations (key = Russian name as used in FALLBACK_SUBS)
SUBCAT_LABELS: dict[str, dict[str, str]] = {
    "Легковые авто":         {"lv": "Vieglās automašīnas",        "en": "Cars"},
    "Мото транспорт":        {"lv": "Motocikli",                  "en": "Motorcycles"},
    "Грузовые машины":       {"lv": "Kravas auto",                "en": "Trucks"},
    "Велосипеды, самокаты":  {"lv": "Velosipēdi, skrejriteņi",   "en": "Bikes & Scooters"},
    "Ремонт и запчасти":     {"lv": "Remonts un rezerves daļas", "en": "Repair & Parts"},
    "Перевозка грузов и людей":{"lv":"Pārvadājumi",              "en": "Transport services"},
    "Аренда транспорта":     {"lv": "Transports īrē",            "en": "Vehicle rental"},
    "Вакансии":              {"lv": "Vakances",                  "en": "Job vacancies"},
    "Ищут работу":           {"lv": "Meklē darbu",              "en": "Job seekers"},
    "Курсы, образование":    {"lv": "Kursi, izglītība",          "en": "Courses & Education"},
    "Деловые контакты":      {"lv": "Biznesa kontakti",          "en": "Business contacts"},
    "Квартиры":              {"lv": "Dzīvokļi",                  "en": "Apartments"},
    "Дома, дачи":            {"lv": "Mājas, dači",               "en": "Houses & Dachas"},
    "Земля и участки":       {"lv": "Zeme un zemesgabali",       "en": "Land & Plots"},
    "Офисы":                 {"lv": "Biroji",                    "en": "Offices"},
    "Стройматериалы":        {"lv": "Celtniecības materiāli",    "en": "Building materials"},
    "Строительные работы":   {"lv": "Celtniecības darbi",        "en": "Construction works"},
    "Инструмент и техника":  {"lv": "Instrumenti un tehnika",    "en": "Tools & Equipment"},
    "Телефоны и связь":      {"lv": "Tālruņi un saziņa",        "en": "Phones & Communication"},
    "Бытовая техника":       {"lv": "Sadzīves tehnika",          "en": "Household appliances"},
    "Компьютеры, оргтехника":{"lv": "Datori, biroja tehnika",   "en": "Computers & IT"},
    "Аудио, Видео, DVD, SAT":{"lv": "Audio, video, DVD, SAT",   "en": "Audio, Video, SAT"},
    "Телевизоры":            {"lv": "Televizori",                "en": "Televisions"},
    "Фото и оптика":         {"lv": "Foto un optika",            "en": "Photo & Optics"},
    "GPS навигаторы":        {"lv": "GPS navigatori",            "en": "GPS Navigation"},
    "Женская одежда":        {"lv": "Sieviešu apģērbs",         "en": "Women's clothing"},
    "Мужская одежда":        {"lv": "Vīriešu apģērbs",          "en": "Men's clothing"},
    "Детская одежда, обувь": {"lv": "Bērnu apģērbs, apavi",     "en": "Children's clothing"},
    "Обувь":                 {"lv": "Apavi",                     "en": "Footwear"},
    "Мебель, интерьер":      {"lv": "Mēbeles, interjers",       "en": "Furniture & Interior"},
    "Здоровье, красота":     {"lv": "Veselība, skaistums",      "en": "Health & Beauty"},
    "Антиквариат, картины":  {"lv": "Antīkvariāts, gleznas",   "en": "Antiques & Art"},
    "Домашние растения":     {"lv": "Istabas augi",             "en": "House plants"},
    "Игрушки, качели":       {"lv": "Rotaļlietas",             "en": "Toys & Swings"},
    "Коляски":               {"lv": "Bērnu ratiņi",            "en": "Baby strollers"},
    "Автокресла, переноски": {"lv": "Auto sēdeklīši, nēsāšanas rīki","en":"Car seats & Carriers"},
    "Собаки, щенки":         {"lv": "Suņi, kucēni",            "en": "Dogs & Puppies"},
    "Кошки, котята":         {"lv": "Kaķi, kaķēni",            "en": "Cats & Kittens"},
    "Попугаи и птицы":       {"lv": "Papagaiļi un putni",      "en": "Parrots & Birds"},
    "Рыбки, аквариумы":      {"lv": "Zivis, akvāriji",         "en": "Fish & Aquariums"},
    "Ветеринария":           {"lv": "Veterinārija",             "en": "Veterinary"},
    "Животноводство":        {"lv": "Lopkopība",               "en": "Livestock"},
    "Птицеводство":          {"lv": "Putnkopība",              "en": "Poultry farming"},
    "Сельхозтехника":        {"lv": "Lauksaimniecības tehnika","en": "Agricultural machinery"},
    "Семена и рассада":      {"lv": "Sēklas un stādi",         "en": "Seeds & Seedlings"},
    "Хобби, увлечения":      {"lv": "Hobiji, vaļasprieki",     "en": "Hobbies"},
    "Коллекционирование":    {"lv": "Kolekcionēšana",          "en": "Collecting"},
    "Спорт, активный отдых": {"lv": "Sports, aktīvā atpūta",  "en": "Sports & Outdoor"},
    "Охота, рыбалка":        {"lv": "Medības, makšķerēšana",  "en": "Hunting & Fishing"},
    "Туризм":                {"lv": "Tūrisms",                 "en": "Tourism"},
    "Книги":                 {"lv": "Grāmatas",               "en": "Books"},
    "Билеты, концерты":      {"lv": "Biļetes, koncerti",      "en": "Tickets & Events"},
    "Оборудование":          {"lv": "Iekārtas",               "en": "Equipment"},
    "Дрова, брикеты, гранулы":{"lv":"Malka, briketes, granulas","en":"Firewood & Pellets"},
    # Riga districts
    "Квартиры — Рига (по районам)": {"lv": "Dzīvokļi — Rīga (rajoni)", "en": "Apartments — Riga (districts)"},
    "Дома — Рига (по районам)":     {"lv": "Mājas — Rīga (rajoni)",    "en": "Houses — Riga (districts)"},
}


def translate_subcat(name: str, lang: str) -> str:
    """Translate a subcategory name if translation exists, otherwise return original."""
    if lang == "ru":
        return name
    return SUBCAT_LABELS.get(name, {}).get(lang, name)


def cat_label(cat_id: str, lang: str) -> str:
    return CAT_LABELS.get(cat_id, {}).get(lang) or cat_id


# ── Статический перевод подписей фильтров (filters_config.py / brands.py) ─────
# Эти подписи захардкожены по-русски и показываются в меню легковых/простого
# флоу (метки полей, заголовки подменю, подписи опций). Значения для матчинга
# (2-й элемент кортежей в filters_config) НЕ трогаем — они в меню не видны.
# Ключ = русское «ядро» подписи без ведущего эмодзи, в нижнем регистре.
# Латышские термины — как у самого ss.lv (Benzīns/Dīzelis/Sedans/Melna…).
UI_I18N: dict[str, dict[str, str]] = {
    # поля / заголовки
    "цена €":            {"lv": "Cena €"},
    "год выпуска":       {"lv": "Izlaiduma gads"},
    "пробег км":         {"lv": "Nobraukums km"},
    "объём двигателя":   {"lv": "Dzinēja tilpums"},
    "тип топлива":       {"lv": "Degvielas tips"},
    "коробка передач":   {"lv": "Ātrumkārba"},
    "тип кузова":        {"lv": "Virsbūves tips"},
    "привод":            {"lv": "Piedziņa"},
    "цвет":              {"lv": "Krāsa"},
    "ключевое слово":    {"lv": "Atslēgvārds"},
    "площадь м²":        {"lv": "Platība m²"},
    "комнат":            {"lv": "Istabas"},
    "этаж":              {"lv": "Stāvs"},
    "зарплата €":        {"lv": "Alga €"},
    "опыт работы":       {"lv": "Darba pieredze"},
    "опыт":              {"lv": "Pieredze"},
    "должность/слово":   {"lv": "Amats/vārds"},
    "состояние":         {"lv": "Stāvoklis"},
    "размер":            {"lv": "Izmērs"},
    "порода / слово":    {"lv": "Šķirne / vārds"},
    # топливо
    "бензин":            {"lv": "Benzīns"},
    "дизель":            {"lv": "Dīzelis"},
    "электро":           {"lv": "Elektriskais"},
    "гибрид":            {"lv": "Hibrīds"},
    "газ (lpg)":         {"lv": "Gāze (LPG)"},
    "газ/бензин":        {"lv": "Benzīns/gāze"},
    # коробка
    "автомат":           {"lv": "Automāts"},
    "механика":          {"lv": "Manuālā"},
    "полуавтомат":       {"lv": "Pusautomāts"},
    # кузов
    "седан":             {"lv": "Sedans"},
    "внедорожник / джип":{"lv": "Apvidus / džips"},
    "универсал":         {"lv": "Universāls"},
    "хэтчбек":           {"lv": "Hečbeks"},
    "минивэн":           {"lv": "Minivens"},
    "купе":              {"lv": "Kupeja"},
    "кабриолет":         {"lv": "Kabriolets"},
    "пикап":             {"lv": "Pikaps"},
    "микроавтобус":      {"lv": "Mikroautobuss"},
    # привод
    "передний":          {"lv": "Priekšējā"},
    "задний":            {"lv": "Aizmugurējā"},
    "полный":            {"lv": "Pilnpiedziņa"},
    # цвет
    "чёрный":            {"lv": "Melna"},
    "белый":             {"lv": "Balta"},
    "красный":           {"lv": "Sarkana"},
    "синий":             {"lv": "Zila"},
    "коричневый":        {"lv": "Brūna"},
    "жёлтый":            {"lv": "Dzeltena"},
    "зелёный":           {"lv": "Zaļa"},
    "серый":             {"lv": "Pelēka"},
    "серебристый":       {"lv": "Sudraba"},
    "оранжевый":         {"lv": "Oranža"},
    # комнаты
    "1 комната":         {"lv": "1 istaba"},
    "2 комнаты":         {"lv": "2 istabas"},
    "3 комнаты":         {"lv": "3 istabas"},
    "4 комнаты":         {"lv": "4 istabas"},
    "5+ комнат":         {"lv": "5+ istabas"},
    # этаж
    "не первый":         {"lv": "Ne pirmais"},
    "не последний":      {"lv": "Ne pēdējais"},
    "1 этаж":            {"lv": "1. stāvs"},
    "2 этаж":            {"lv": "2. stāvs"},
    "3 этаж":            {"lv": "3. stāvs"},
    "4-5 этаж":          {"lv": "4.-5. stāvs"},
    "6-9 этаж":          {"lv": "6.-9. stāvs"},
    "10+ этаж":          {"lv": "10.+ stāvs"},
    # состояние
    "новое":             {"lv": "Jauns"},
    "хорошее":           {"lv": "Labs"},
    "требует ремонта":   {"lv": "Nepieciešams remonts"},
    # опыт
    "без опыта":         {"lv": "Bez pieredzes"},
    "1–2 года":          {"lv": "1–2 gadi"},
    "3–5 лет":           {"lv": "3–5 gadi"},
    "5+ лет":            {"lv": "5+ gadi"},
}

_UI_EMOJI = re.compile(r"^[^\w]+", re.UNICODE)


def ui(text: str, lang: str) -> str:
    """Локализованный ПОКАЗ статичной русской подписи фильтра (для меню).

    ru → как есть. Для lv ищем перевод «ядра» подписи (без ведущего эмодзи)
    в UI_I18N; эмодзи сохраняем. Нет перевода → возвращаем оригинал.
    """
    if lang == "ru" or not text:
        return text
    m = _UI_EMOJI.match(text)
    prefix = m.group(0) if m else ""
    core = text[len(prefix):]
    tr = UI_I18N.get(core.strip().lower())
    if not tr:
        return text
    return prefix + tr.get(lang, core)
