"""
Конфигурация фильтров по категориям — точь в точь как на ss.lv.
Каждая категория имеет свой набор фильтров.
"""

# ─── Опции для select-фильтров ────────────────────────────────

FUEL_OPTIONS = [
    ("⛽ Бензин",     "бензин"),
    ("🛢 Дизель",     "дизель"),
    ("🔋 Электро",    "электро"),
    ("♻️ Гибрид",     "гибрид"),
    ("💨 Газ (LPG)",  "газ"),
    ("🔀 Газ/Бензин", "газ бензин"),
]

DRIVE_OPTIONS = [
    ("⬅️ Передний",   "передний привод"),
    ("➡️ Задний",     "задний привод"),
    ("🔄 Полный",     "полный привод"),
    ("🔄 4x4",        "4x4"),
]

COLOR_OPTIONS = [
    ("⚫ Чёрный",     "чёрный"),
    ("⚪ Белый",      "белый"),
    ("🔴 Красный",    "красный"),
    ("🔵 Синий",      "синий"),
    ("🟤 Коричневый", "коричневый"),
    ("🟡 Жёлтый",     "жёлтый"),
    ("🟢 Зелёный",    "зелёный"),
    ("🩶 Серый",      "серый"),
    ("🥈 Серебристый","серебристый"),
    ("🟠 Оранжевый",  "оранжевый"),
]

ENGINE_PRESETS = [
    ("до 1.0 л",     None,  1000),
    ("1.0–1.5 л",    1000,  1500),
    ("1.5–2.0 л",    1500,  2000),
    ("2.0–2.5 л",    2000,  2500),
    ("2.5–3.0 л",    2500,  3000),
    ("3.0–4.0 л",    3000,  4000),
    ("4.0+ л",       4000,   None),
]

ROOMS_OPTIONS = [
    ("1 комната",    "1 комн"),
    ("2 комнаты",    "2 комн"),
    ("3 комнаты",    "3 комн"),
    ("4 комнаты",    "4 комн"),
    ("5+ комнат",    "5 комн"),
]

AREA_PRESETS = [
    ("до 30 м²",     None,    30),
    ("30–50 м²",     30,      50),
    ("50–70 м²",     50,      70),
    ("70–100 м²",    70,     100),
    ("100–150 м²",   100,    150),
    ("150+ м²",      150,    None),
]

FLOOR_OPTIONS = [
    ("🏠 Не первый",    "не первый"),
    ("🏠 Не последний", "не последний"),
    ("1 этаж",          "1 этаж"),
    ("2 этаж",          "2 этаж"),
    ("3 этаж",          "3 этаж"),
    ("4-5 этаж",        "4 этаж"),
    ("6-9 этаж",        "6 этаж"),
    ("10+ этаж",        "10 этаж"),
]

CONDITION_OPTIONS = [
    ("✨ Новое",         "новое"),
    ("👍 Хорошее",       "хорошее"),
    ("🔧 Требует ремонта","ремонт"),
]

SIZE_OPTIONS = [
    ("XS", "xs"), ("S", "s"), ("M", "m"),
    ("L", "l"), ("XL", "xl"), ("XXL", "xxl"),
    ("XXXL", "xxxl"),
]

EXPERIENCE_OPTIONS = [
    ("Без опыта",     "без опыта"),
    ("1–2 года",      "1-2 года"),
    ("3–5 лет",       "3-5 лет"),
    ("5+ лет",        "5 лет"),
]

# ─── Определения фильтров по категориям ───────────────────────
# Формат: {"id": str, "label": str, "type": str, ...}
# type: "range" | "select" | "text"

CATEGORY_FILTERS: dict[str, list[dict]] = {

    # ── Транспорт — Легковые авто ──────────────────────────────
    "transport_cars": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "year",    "label": "📅 Год выпуска",        "type": "range",  "presets": None},
        {"id": "mileage", "label": "🛣 Пробег км",          "type": "range",  "presets": None},
        {"id": "engine",  "label": "🔧 Объём двигателя",    "type": "range",  "presets": "engine"},
        {"id": "fuel",    "label": "⛽ Тип топлива",         "type": "select", "options": "fuel"},
        {"id": "gearbox", "label": "⚙️ Коробка передач",    "type": "select", "options": "gearbox"},
        {"id": "bodytype","label": "🚙 Тип кузова",          "type": "select", "options": "bodytype"},
        {"id": "drive",   "label": "🔄 Привод",              "type": "select", "options": "drive"},
        {"id": "color",   "label": "🎨 Цвет",               "type": "select", "options": "color"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Транспорт — Мото ───────────────────────────────────────
    "transport_motorcycles": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "year",    "label": "📅 Год выпуска",        "type": "range",  "presets": None},
        {"id": "mileage", "label": "🛣 Пробег км",          "type": "range",  "presets": None},
        {"id": "engine",  "label": "🔧 Объём двигателя",    "type": "range",  "presets": "engine"},
        {"id": "gearbox", "label": "⚙️ Коробка передач",    "type": "select", "options": "gearbox"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Транспорт — Грузовые, прочее ──────────────────────────
    "transport_other": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "year",    "label": "📅 Год выпуска",        "type": "range",  "presets": None},
        {"id": "mileage", "label": "🛣 Пробег км",          "type": "range",  "presets": None},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Недвижимость — Квартиры ────────────────────────────────
    "realty_flats": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "area",    "label": "📐 Площадь м²",        "type": "range",  "presets": "area"},
        {"id": "rooms",   "label": "🚪 Комнат",            "type": "select", "options": "rooms"},
        {"id": "floor",   "label": "🏢 Этаж",              "type": "select", "options": "floor"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Недвижимость — Дома ────────────────────────────────────
    "realty_houses": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "area",    "label": "📐 Площадь м²",        "type": "range",  "presets": "area"},
        {"id": "rooms",   "label": "🚪 Комнат",            "type": "select", "options": "rooms"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Недвижимость — Земля ───────────────────────────────────
    "realty_land": [
        {"id": "price",   "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "area",    "label": "📐 Площадь м²",        "type": "range",  "presets": "area"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Работа — Вакансии ──────────────────────────────────────
    "work": [
        {"id": "price",      "label": "💶 Зарплата €",      "type": "range",  "presets": None},
        {"id": "experience", "label": "📋 Опыт работы",      "type": "select", "options": "experience"},
        {"id": "keyword",    "label": "🔎 Должность/слово",  "type": "text"},
    ],

    # ── Электротехника ─────────────────────────────────────────
    "electro": [
        {"id": "price",     "label": "💶 Цена €",           "type": "range",  "presets": None},
        {"id": "condition", "label": "✨ Состояние",         "type": "select", "options": "condition"},
        {"id": "keyword",   "label": "🔎 Ключевое слово",   "type": "text"},
    ],

    # ── Одежда ────────────────────────────────────────────────
    "clothing": [
        {"id": "price",   "label": "💶 Цена €",             "type": "range",  "presets": None},
        {"id": "size",    "label": "📏 Размер",              "type": "select", "options": "size"},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],

    # ── Животные ──────────────────────────────────────────────
    "animals": [
        {"id": "price",   "label": "💶 Цена €",             "type": "range",  "presets": None},
        {"id": "keyword", "label": "🔎 Порода / слово",     "type": "text"},
    ],

    # ── Универсальный (для всех остальных) ─────────────────────
    "default": [
        {"id": "price",   "label": "💶 Цена €",             "type": "range",  "presets": None},
        {"id": "keyword", "label": "🔎 Ключевое слово",     "type": "text"},
    ],
}


def get_filters(cat_id: str, sub_path: str = "") -> list[dict]:
    """Вернуть список фильтров для категории + подкатегории."""
    # Транспорт — определяем по sub_path
    if cat_id == "transport":
        if "motorcycles" in sub_path:
            return CATEGORY_FILTERS["transport_motorcycles"]
        elif "cars" in sub_path:
            return CATEGORY_FILTERS["transport_cars"]
        else:
            return CATEGORY_FILTERS["transport_other"]

    # Недвижимость — по типу
    if cat_id == "realty":
        if "flats" in sub_path:
            return CATEGORY_FILTERS["realty_flats"]
        elif "houses" in sub_path or "homes" in sub_path or "farms" in sub_path:
            return CATEGORY_FILTERS["realty_houses"]
        elif "land" in sub_path:
            return CATEGORY_FILTERS["realty_land"]
        else:
            return CATEGORY_FILTERS["realty_flats"]  # по умолчанию

    # Остальные
    return CATEGORY_FILTERS.get(cat_id, CATEGORY_FILTERS["default"])


def get_options(options_key: str) -> list[tuple]:
    """Вернуть список опций по ключу."""
    mapping = {
        "fuel":       FUEL_OPTIONS,
        "drive":      DRIVE_OPTIONS,
        "color":      COLOR_OPTIONS,
        "rooms":      ROOMS_OPTIONS,
        "floor":      FLOOR_OPTIONS,
        "condition":  CONDITION_OPTIONS,
        "size":       SIZE_OPTIONS,
        "experience": EXPERIENCE_OPTIONS,
    }
    return mapping.get(options_key, [])


def get_presets(presets_key: str) -> list[tuple]:
    """Вернуть пресеты диапазона по ключу."""
    if presets_key == "engine":
        return ENGINE_PRESETS
    if presets_key == "area":
        return AREA_PRESETS
    return []
