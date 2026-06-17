"""
Хардкоженные марки для ss.lv.
Слаги совпадают с URL ss.lv: /ru/transport/cars/{slug}/
Отсортированы по популярности в Латвии.
"""

# --- Авто: марки ---
# (display_name, slug)
CAR_BRANDS = [
    # ТОП Латвия
    ("BMW",           "bmw"),
    ("Mercedes",      "mercedes"),
    ("Audi",          "audi"),
    ("Volkswagen",    "volkswagen"),
    ("Toyota",        "toyota"),
    ("Ford",          "ford"),
    ("Opel",          "opel"),
    ("Skoda",         "skoda"),
    ("Renault",       "renault"),
    ("Nissan",        "nissan"),
    ("Mazda",         "mazda"),
    ("Honda",         "honda"),
    ("Hyundai",       "hyundai"),
    ("Kia",           "kia"),
    ("Volvo",         "volvo"),
    ("Peugeot",       "peugeot"),
    ("Citroen",       "citroen"),
    ("Seat",          "seat"),
    ("Mitsubishi",    "mitsubishi"),
    ("Subaru",        "subaru"),
    ("Suzuki",        "suzuki"),
    ("Jeep",          "jeep"),
    ("Land Rover",    "land-rover"),
    ("Lexus",         "lexus"),
    ("Porsche",       "porsche"),
    ("Mini",          "mini"),
    ("Dacia",         "dacia"),
    ("Fiat",          "fiat"),
    ("Tesla",         "tesla"),
    ("Alfa Romeo",    "alfa-romeo"),
    ("Chevrolet",     "chevrolet"),
    ("Chrysler",      "chrysler"),
    ("Dodge",         "dodge"),
    ("Infiniti",      "infiniti"),
    ("Jaguar",        "jaguar"),
    ("Lancia",        "lancia"),
    ("Lada/ВАЗ",      "vaz"),
    ("Saab",          "saab"),
    ("Ssangyong",     "ssangyong"),
]

# --- Мото: марки ---
MOTO_BRANDS = [
    ("Honda",         "honda"),
    ("Yamaha",        "yamaha"),
    ("Kawasaki",      "kawasaki"),
    ("Suzuki",        "suzuki"),
    ("BMW",           "bmw"),
    ("KTM",           "ktm"),
    ("Harley-Davidson","harley-davidson"),
    ("Ducati",        "ducati"),
    ("Triumph",       "triumph"),
    ("Aprilia",       "aprilia"),
    ("Husqvarna",     "husqvarna"),
    ("MV Agusta",     "mv-agusta"),
    ("Royal Enfield", "royal-enfield"),
    ("Benelli",       "benelli"),
]

# Количество марок на странице меню
PAGE_SIZE = 9   # 3 × 3

# Количество марок на странице меню

# --- Коробка передач ---
GEARBOX_OPTIONS = [
    ("⚙️ Автомат",           "автомат"),
    ("🔧 Механика",           "механика"),
    ("🔀 Полуавтомат",        "полуавтомат"),
]

# --- Тип кузова ---
BODYTYPE_OPTIONS = [
    ("🚗 Седан",              "седан"),
    ("🚙 Внедорожник / Джип", "джип"),
    ("🚌 Универсал",          "универсал"),
    ("🚘 Хэтчбек",            "хэтчбек"),
    ("🚐 Минивэн",            "минивэн"),
    ("🏎 Купе",               "купе"),
    ("☀️ Кабриолет",          "кабриолет"),
    ("🛻 Пикап",              "пикап"),
    ("🚍 Микроавтобус",       "микроавтобус"),
]
