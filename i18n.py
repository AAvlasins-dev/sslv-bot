"""
Переводы интерфейса бота на три языка.
Использование: T[lang]["ключ"] или t(lang, "ключ", **kwargs)
"""
from typing import Optional

LANGS = {
    "ru": "🇷🇺 Русский",
    "lv": "🇱🇻 Latviešu",
    "en": "🇬🇧 English",
}

# ss.lv URL prefix per language
SS_PREFIX = {
    "ru": "/ru",
    "lv": "/lv",
    "en": "/en",  # ss.lv не имеет /en/, фолбэк на /ru/
}
SS_LANG_URL = {"ru": "ru", "lv": "lv", "en": "ru"}  # en → uses /ru/ on ss.lv


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
        "ru": "✅ Фильтр <b>#{fid}</b> сохранён!\nОбъявлений сейчас: <b>{n}</b>\n<a href='{url}'>Открыть на ss.lv →</a>",
        "lv": "✅ Filtrs <b>#{fid}</b> saglabāts!\nSludinājumu tagad: <b>{n}</b>\n<a href='{url}'>Atvērt ss.lv →</a>",
        "en": "✅ Filter <b>#{fid}</b> saved!\nCurrent listings: <b>{n}</b>\n<a href='{url}'>Open on ss.lv →</a>",
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
        "ru": "📍 Выбери свой город",
        "lv": "📍 Izvēlies savu pilsētu",
        "en": "📍 Choose your city",
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


def t(lang: str, key: str, **kwargs) -> str:
    """Get translated string for the given lang and key."""
    lang = lang if lang in ("ru", "lv", "en") else "ru"
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
