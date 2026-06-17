"""
Полное дерево категорий ss.lv (/ru/ интерфейс).
path = путь к странице категории.
type = 'transport' (отдельный флоу марка/модель) | 'simple' (ключевое слово)
"""

TOP_CATEGORIES = [
    {"id": "transport",   "label": "🚗 Транспорт",          "path": "/ru/transport/",                  "type": "transport"},
    {"id": "work",        "label": "💼 Работа и бизнес",     "path": "/ru/work/",                       "type": "simple"},
    {"id": "realty",      "label": "🏠 Недвижимость",        "path": "/ru/real-estate/",                "type": "simple"},
    {"id": "construct",   "label": "🏗 Строительство",       "path": "/ru/construction/",               "type": "simple"},
    {"id": "electro",     "label": "📱 Электротехника",       "path": "/ru/electronics/",               "type": "simple"},
    {"id": "clothing",    "label": "👗 Одежда, обувь",        "path": "/ru/clothes-footwear/",          "type": "simple"},
    {"id": "home",        "label": "🛋 Для дома",             "path": "/ru/home-stuff/",                "type": "simple"},
    {"id": "children",    "label": "🧸 Для детей",            "path": "/ru/for-children/",              "type": "simple"},
    {"id": "animals",     "label": "🐕 Животные",             "path": "/ru/animals/",                   "type": "simple"},
    {"id": "agro",        "label": "🚜 Сельское хозяйство",   "path": "/ru/agriculture/",               "type": "simple"},
    {"id": "leisure",     "label": "🎮 Отдых, увлечения",     "path": "/ru/entertainment/",             "type": "simple"},
    {"id": "production",  "label": "🏭 Производство",         "path": "/ru/production-work/",            "type": "simple"},
]

# Фолбэк: захардоженные подкатегории на случай если ss.lv не отдаст их динамически
FALLBACK_SUBS: dict[str, list[tuple[str, str]]] = {
    "transport": [
        ("🚗 Легковые авто",            "/ru/transport/cars/"),
        ("🏍 Мото транспорт",            "/ru/transport/motorcycles/"),
        ("🚛 Грузовые машины",           "/ru/transport/trucks/"),
        ("🚲 Велосипеды, самокаты",      "/ru/sport/bicycles/"),
        ("🔄 Обмен легковых авто",       "/ru/transport/car-exchange/"),
        ("🔧 Ремонт и запчасти",         "/ru/transport/spare-parts/"),
        ("🚚 Перевозка грузов и людей",  "/ru/transport/transport-services/"),
        ("🏕 Аренда транспорта",         "/ru/transport/car-rent/"),
        ("📋 Другое",                    "/ru/transport/other/"),
    ],
    "work": [
        ("👔 Вакансии",                  "/ru/work/vacancies/"),
        ("🔍 Ищут работу",              "/ru/work/seek-work/"),
        ("📚 Курсы, образование",        "/ru/work/courses/"),
        ("🤝 Деловые контакты",          "/ru/work/business-contacts/"),
        ("⚖️ Юридические услуги",        "/ru/work/juridical-services/"),
        ("💰 Финансовые услуги",         "/ru/work/financial-services/"),
        ("📝 Переводы текстов",          "/ru/work/translations/"),
        ("🌐 Интернет-услуги",           "/ru/work/internet-services/"),
        ("📋 Разное",                    "/ru/work/other/"),
    ],
    "realty": [
        ("🏢 Квартиры",                  "/ru/real-estate/flats/"),
        ("🏠 Дома, дачи",                "/ru/real-estate/homes-summer-residences/"),
        ("🌾 Хутора, поместья",          "/ru/real-estate/farms-estates/"),
        ("🏪 Помещения",                 "/ru/real-estate/premises/"),
        ("🏬 Офисы",                     "/ru/real-estate/offices/"),
        ("🌲 Земля и участки",           "/ru/real-estate/plots-and-lands/"),
        ("🌳 Лес",                       "/ru/real-estate/wood/"),
        ("🤝 Услуги риелтора",           "/ru/real-estate/brokers-services/"),
        # ── Рига по районам ──
        ("🏘 Квартиры — Рига (по районам)",  "__riga_flats__"),
        ("🏠 Дома — Рига (по районам)",       "__riga_houses__"),
    ],
    "construct": [
        ("🧱 Стройматериалы",            "/ru/construction/materials/"),
        ("👷 Строительные работы",        "/ru/construction/works/"),
        ("🔨 Инструмент и техника",      "/ru/construction/tools/"),
        ("📦 Аренда инструмента",        "/ru/construction/rent-tools/"),
        ("🚿 Сантехника",               "/ru/construction/plumbing/"),
        ("🌱 Садовая техника",           "/ru/construction/garden-equipment/"),
        ("📐 Проекты, дизайн",           "/ru/construction/projects/"),
        ("🚛 Перевозка и погрузка",      "/ru/construction/transport/"),
        ("📋 Разное",                    "/ru/construction/other/"),
    ],
    "electro": [
        ("📱 Телефоны и связь",          "/ru/electronics/phones/"),
        ("🏠 Бытовая техника",           "/ru/electronics/household-appliances/"),
        ("💻 Компьютеры, оргтехника",    "/ru/electronics/computers/"),
        ("🎵 Аудио, Видео, DVD, SAT",    "/ru/electronics/audio-video/"),
        ("🔋 Батарейки, Аккумуляторы",   "/ru/electronics/batteries/"),
        ("📺 Телевизоры",               "/ru/electronics/tvs/"),
        ("📷 Фото и оптика",             "/ru/electronics/photo/"),
        ("🗺 GPS навигаторы",            "/ru/electronics/navigation/"),
        ("📋 Разное и ремонт",           "/ru/electronics/other/"),
    ],
    "clothing": [
        ("👟 Обувь",                     "/ru/clothes-footwear/footwear/"),
        ("🦺 Спецодежда",               "/ru/clothes-footwear/overalls/"),
        ("✂️ Услуги швей и ателье",      "/ru/clothes-footwear/seamstress-and-atelier-services/"),
        ("📋 Разное",                    "/ru/clothes-footwear/other/"),
    ],
    "home": [
        ("🛋 Мебель, интерьер",          "/ru/home-stuff/furniture/"),
        ("💊 Здоровье, красота",          "/ru/home-stuff/health/"),
        ("💎 Драгоценности, украшения",   "/ru/home-stuff/jewellery/"),
        ("🎁 Подарки, сувениры",          "/ru/home-stuff/gifts/"),
        ("🪡 Изделия ручной работы",      "/ru/home-stuff/handmade/"),
        ("🖼 Антиквариат, картины",       "/ru/home-stuff/antique/"),
        ("🌿 Домашние растения",          "/ru/home-stuff/plants/"),
        ("🔍 Поиски, находки",           "/ru/home-stuff/lost-found/"),
        ("📋 Другое",                    "/ru/home-stuff/other/"),
    ],
    "children": [
        ("📚 Все для школы",             "/ru/for-children/school/"),
        ("👕 Детская одежда, обувь",      "/ru/for-children/clothes/"),
        ("🧸 Игрушки, качели",           "/ru/for-children/toys/"),
        ("🍼 Коляски",                   "/ru/for-children/strollers/"),
        ("🪑 Детская мебель",            "/ru/for-children/furniture/"),
        ("🚗 Автокресла, переноски",      "/ru/for-children/carseats/"),
        ("🍭 Аксессуары и питание",       "/ru/for-children/accessories/"),
        ("🎨 Кружки, садики, секции",     "/ru/for-children/clubs/"),
        ("🎉 Детские мероприятия",        "/ru/for-children/events/"),
        ("📋 Разное",                    "/ru/for-children/other/"),
    ],
    "animals": [
        ("🐕 Собаки, щенки",             "/ru/animals/dogs/"),
        ("🐱 Кошки, котята",             "/ru/animals/cats/"),
        ("🐹 Грызуны",                   "/ru/animals/rodents/"),
        ("🦜 Попугаи и птицы",           "/ru/animals/birds/"),
        ("🐟 Рыбки, аквариумы",          "/ru/animals/fish/"),
        ("🦎 Экзотические животные",     "/ru/animals/exotic/"),
        ("🐄 Сельхоз животные",          "/ru/animals/farm-animals/"),
        ("🏥 Ветеринария",               "/ru/animals/veterinary/"),
        ("🔍 Поиски, находки",           "/ru/animals/lost-found/"),
        ("📋 Разное",                    "/ru/animals/other/"),
    ],
    "agro": [
        ("🐄 Животноводство",            "/ru/agriculture/livestock/"),
        ("🐓 Птицеводство",              "/ru/agriculture/poultry/"),
        ("🐟 Рыбное хозяйство",          "/ru/agriculture/fish-farming/"),
        ("🌾 Сельхозработы",             "/ru/agriculture/works/"),
        ("🚜 Сельхозтехника",            "/ru/agriculture/equipment/"),
        ("🥕 Овощеводство, садоводство", "/ru/agriculture/vegetables/"),
        ("🧪 Удобрения и химикаты",      "/ru/agriculture/fertilizers/"),
        ("🌱 Семена и рассада",          "/ru/agriculture/seeds/"),
        ("🥩 Продовольствие",            "/ru/agriculture/food/"),
        ("📋 Разное",                    "/ru/agriculture/other/"),
    ],
    "leisure": [
        ("💑 Знакомства",                "/ru/entertainment/acquaintances/"),
        ("📋 Всё остальное",             "/ru/entertainment/other/"),
    ],
    "production": [
        ("⚙️ Промышленное оборудование", "/ru/production-work/production-work-orders/"),
    ],
}

# Подкатегории с отдельным флоу «марка → модель → детальные фильтры».
# Только легковые: у них чистый список марок. Мото/грузовые/прочее идут
# через универсальный рекурсивный drill-down (parser.get_subcategories).
TRANSPORT_FULL = {
    "/ru/transport/cars/": "cars",
}

# «Редкие авто» — спец-разделы легковых, не привязанные к марке.
# Идут как простые подкатегории (сразу к меню фильтров).
CARS_SPECIAL = [
    ("🏛 Ретро авто",       "/ru/transport/cars/retro-cars/"),
    ("🏎 Спортивные",       "/ru/transport/cars/sport-cars/"),
    ("🛠 Тюнингованые",     "/ru/transport/cars/tuned-cars/"),
    ("💎 Эксклюзивные",     "/ru/transport/cars/exclusive-cars/"),
    ("⚡ Электромобили",    "/ru/transport/cars/electric-cars/"),
]

# Настройки интервала мониторинга
INTERVALS = [
    ("⚡ 1 минута",   60),
    ("🔄 5 минут",   300),
    ("🕐 15 минут",  900),
    ("🕑 30 минут", 1800),
    ("🕓 1 час",    3600),
    ("📅 2 часа",   7200),
]

DEFAULT_INTERVAL = 300  # 5 минут


# ─── Районы Риги (для недвижимости) ────────────────────────────────────────
# Slug = часть URL после /ru/real-property/flats/riga/
# Формат: (Название для кнопки, slug)

RIGA_DISTRICTS = [
    # ── Популярные (топ по количеству объявлений) ──
    ("🏙 Центр",               "centr"),
    ("🏙 Пурвциемс",           "purvciems"),
    ("🏙 Плявниеки",           "plavnieki"),
    ("🏙 Иманта",              "imanta"),
    ("🏙 Тейка",               "teika"),
    ("🏙 Кенгарагс",           "kengarags"),
    ("🏙 Зиепниеккалнс",       "ziepniekkalns"),
    ("🏙 Ильгюциемс",          "ilguciems"),
    ("🏙 Саркандаугава",        "sarkandaugava"),
    ("🏙 Вецмилгравис",        "vecmilgravis"),
    ("🏙 Югла",                "jugla"),
    ("🏙 Межциемс",            "mezciems"),
    ("🏙 Золитуде",            "zolitude"),
    # ── Остальные ──
    ("🏙 Агенскалнс",          "agenskalns"),
    ("🏙 Аплокциемс",          "aplokciems"),
    ("🏙 Болдерая",            "bolderaja"),
    ("🏙 Вецрига (Старая Рига)","vecriga"),
    ("🏙 Гризинькалнс",        "grizinkalns"),
    ("🏙 Дарзциемс",           "darzciems"),
    ("🏙 Даугавгрива",         "daugavgriva"),
    ("🏙 Дзегужкалнс",         "dzeguzkalns"),
    ("🏙 Дрейлини",            "dreilini"),
    ("🏙 Закюсала",            "zakusala"),
    ("🏙 Засулаукс",           "zasulauks"),
    ("🏙 Катлакалнс",          "katlakalns"),
    ("🏙 Кипсала",             "kipsala"),
    ("🏙 Кливерсала",          "kliversala"),
    ("🏙 Мангали",             "mangali"),
    ("🏙 Мангалсала",          "mangalsala"),
    ("🏙 Межапарк",            "mezaparks"),
    ("🏙 Торнякалнс",          "tornakalns"),
    ("🏙 Чиекуркалнс",         "ciekurkalns"),
    ("🏙 Шкиротава",           "skirotava"),
    ("🏙 VEF",                 "vef"),
    ("🏙 Яунмилгравис",        "jaunmilgravis"),
    ("🏙 Яунциемс",            "jaunciems"),
    ("🏙 Биерини",             "bierini"),
    ("🏙 Вецаки",              "vecaki"),
]

# Базовые URL для недвижимости Риги по типу
RIGA_REALTY_BASE = {
    "flats":  "/ru/real-estate/flats/riga/",
    "houses": "/ru/real-estate/houses/riga/",
    "all":    "/ru/real-estate/riga/",
}
