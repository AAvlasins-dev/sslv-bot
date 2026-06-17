"""
ss.lv Monitor Bot — полная версия.
Все меню — кнопки. Постоянная клавиатура внизу. Пресеты цена/год/пробег.
"""
import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton,
    KeyboardButton, Message,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import brands as br
import car_specs as cs
import categories as cat_mod
import config
import db
import geo
import i18n
from i18n import t
import cache
import filters_config as fc
import parser as p

log = logging.getLogger("bot")
router = Router()

BRANDS_PER_PAGE = br.PAGE_SIZE
CITIES_PER_PAGE = 15
SUBS_PER_PAGE   = 9


# ─────────────────────────────────────────────
# FSM
# ─────────────────────────────────────────────
class AddFilter(StatesGroup):
    top_cat       = State()
    sub_cat       = State()
    riga_district = State()
    brand         = State()
    model         = State()
    model_type    = State()
    filters       = State()
    inp_price     = State()   # ввод своей цены текстом
    inp_year      = State()
    inp_mileage   = State()
    inp_range     = State()   # ввод объёма/площади (по _rk)
    inp_keyword   = State()
    inp_gearbox   = State()
    inp_bodytype  = State()
    interval      = State()

class SetLocation(StatesGroup):
    waiting   = State()
    city_page = State()

class SetLang(StatesGroup):
    picking = State()


# ─────────────────────────────────────────────
# Пресеты для фильтров
# ─────────────────────────────────────────────
PRICE_PRESETS = [
    ("до 2 000 €",       None,   2000),
    ("2 000–5 000 €",    2000,   5000),
    ("5 000–10 000 €",   5000,  10000),
    ("10 000–20 000 €", 10000,  20000),
    ("20 000–40 000 €", 20000,  40000),
    ("40 000+ €",       40000,   None),
]

YEAR_PRESETS = [
    ("до 2000",    None,  2000),
    ("2000–2005",  2000,  2005),
    ("2005–2010",  2005,  2010),
    ("2010–2015",  2010,  2015),
    ("2015–2020",  2015,  2020),
    ("2020–2023",  2020,  2023),
    ("2023+",      2023,   None),
]

MILEAGE_PRESETS = [
    ("до 50 000",          None,   50000),
    ("50 000–100 000",    50000,  100000),
    ("100 000–150 000",  100000,  150000),
    ("150 000–200 000",  150000,  200000),
    ("200 000+",         200000,    None),
]

CUSTOM_LABEL = "✏️ Своё значение"


def _preset_kb(presets: list, which: str, lang: str) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    for label, lo, hi in presets:
        lo_s = str(lo) if lo is not None else "X"
        hi_s = str(hi) if hi is not None else "X"
        kb.button(text=label, callback_data=f"preset:{which}:{lo_s}:{hi_s}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=CUSTOM_LABEL, callback_data=f"preset:{which}:custom:X"))
    kb.row(
        InlineKeyboardButton(text=t(lang, "clear"), callback_data=f"clear:{which}"),
        InlineKeyboardButton(text=t(lang, "back"),  callback_data="back_to_filters"),
    )
    return kb


# ─────────────────────────────────────────────
# Постоянная клавиатура внизу
# ─────────────────────────────────────────────

# Кнопки меню на каждом языке
MENU_BTNS = {
    "ru": {
        "add":      "➕ Добавить фильтр",
        "list":     "📋 Мои фильтры",
        "stats":    "📊 Статистика",
        "location": "📍 Моё место",
        "lang":     "🌐 Язык",
    },
    "lv": {
        "add":      "➕ Pievienot filtru",
        "list":     "📋 Mani filtri",
        "stats":    "📊 Statistika",
        "location": "📍 Mana vieta",
        "lang":     "🌐 Valoda",
    },
    "en": {
        "add":      "➕ Add filter",
        "list":     "📋 My filters",
        "stats":    "📊 Statistics",
        "location": "📍 My location",
        "lang":     "🌐 Language",
    },
}

# Все тексты кнопок → действие (для роутинга)
_ALL_MENU_TEXT: dict[str, str] = {}
for _lang, _btns in MENU_BTNS.items():
    for _action, _text in _btns.items():
        _ALL_MENU_TEXT[_text] = _action


def main_kb(lang: str) -> ReplyKeyboardMarkup:
    """Постоянная клавиатура в нижней части чата."""
    b = MENU_BTNS.get(lang, MENU_BTNS["ru"])
    kb = ReplyKeyboardBuilder()
    kb.row(
        KeyboardButton(text=b["add"]),
        KeyboardButton(text=b["list"]),
    )
    kb.row(
        KeyboardButton(text=b["stats"]),
        KeyboardButton(text=b["location"]),
        KeyboardButton(text=b["lang"]),
    )
    return kb.as_markup(resize_keyboard=True, persistent=True)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _parse_range(s: str):
    s = (s or "").strip().replace(" ", "").replace("\u00a0", "")
    if not s: return None, None
    try:
        if "-" in s:
            a, b = s.split("-", 1)
            return (int(a) if a else None, int(b) if b else None)
        return None, int(s)
    except ValueError:
        return None, None


async def _edit(msg: Message, text: str, **kw):
    try:    await msg.edit_text(text, **kw)
    except: await msg.answer(text, **kw)


async def _lang(user_id: int) -> str:
    u = await db.get_user(user_id)
    return (u or {}).get("lang") or "ru"


def _brand_list(category: str):
    return br.CAR_BRANDS if category == "cars" else br.MOTO_BRANDS


def _interval_label(sec: int) -> str:
    for label, s in cat_mod.INTERVALS:
        if s == sec: return label.split(" ", 1)[1]
    m = sec // 60
    return f"{m} мин" if m < 60 else f"{m//60} ч"


def _filter_summary(data: dict) -> str:
    def rng(a, b, u=""):
        if a and b: return f"{a}–{b}{u}"
        if a: return f"от {a}{u}"
        if b: return f"до {b}{u}"
        return None
    lines = []
    r = rng(data.get("price_min"),  data.get("price_max"),  " €")
    if r: lines.append(f"💶 Цена: {r}")
    r = rng(data.get("year_min"),   data.get("year_max"))
    if r: lines.append(f"📅 Год: {r}")
    r = rng(data.get("mile_min"),   data.get("mile_max"),   " км")
    if r: lines.append(f"🛣 Пробег: {r}")
    r = rng(data.get("engine_min"), data.get("engine_max"), " куб")
    if r: lines.append(f"🔧 Двигатель: {r}")
    r = rng(data.get("area_min"),   data.get("area_max"),   " м²")
    if r: lines.append(f"📐 Площадь: {r}")
    for key, icon, label in [
        ("fuel","⛽","Топливо"),("gearbox","⚙️","КПП"),("bodytype","🚙","Кузов"),
        ("drive","🔄","Привод"),("color","🎨","Цвет"),("rooms","🚪","Комнат"),
        ("floor","🏢","Этаж"),("condition","✨","Состояние"),
        ("size","📏","Размер"),("experience","📋","Опыт"),("keyword","🔎","Слово"),
    ]:
        v = data.get(key)
        if v: lines.append(f"{icon} {label}: {v}")
    for label, val in (data.get("cols_sel") or {}).items():
        lines.append(f"🔹 {label}: {val}")
    for label, val in (data.get("adopts_sel") or {}).items():
        lines.append(f"🔹 {label}: {val}")
    return "\n".join(lines) if lines else "Фильтры не заданы"


async def _show_filter_menu(msg: Message, state: FSMContext):
    data  = await state.get_data()
    lang  = data.get("_lang", "ru")

    cat_id   = data.get("cat_id", "")
    sub_path = data.get("sub_path", "")

    # Лениво (один раз) подтягиваем реальные фильтры этой категории ss.lv.
    # Лениво (один раз) подтягиваем реальные фильтры категории/листа ss.lv.
    if data.get("cat_filters") is None:
        cf = []
        if sub_path.startswith("/"):
            cf = await p.get_category_filters("https://www.ss.lv" + sub_path)
        await state.update_data(cat_filters=cf)
        data["cat_filters"] = cf
    cat_filters = data.get("cat_filters") or []

    parts = [data.get("cat_label", "—")]
    if data.get("sub_label"):   parts.append(data["sub_label"])
    if data.get("brand_name"):  parts.append(data["brand_name"])
    if data.get("model_name"):  parts.append(data["model_name"])

    # Диапазон показываем только если в списке есть соответствующая колонка
    # (у вакансий нет «Цены/Зарплаты» → не показываем фильтр зарплаты).
    cols = p.listing_columns("https://www.ss.lv" + sub_path) if sub_path.startswith("/") else []
    _RANGE_COLS = {"price": ("Цена","Зарплата","€"), "year": ("Год",),
                   "mileage": ("Пробег",), "engine": ("Объём","Двигатель"),
                   "area": ("Площадь",)}
    def _range_applies(fid: str) -> bool:
        if fid == "area":
            return False                      # площадь пока не парсится из списка
        keys = _RANGE_COLS.get(fid)
        if not cols or not keys:
            return True                       # колонки неизвестны → показываем
        return any(k in c for c in cols for k in keys)

    kb = InlineKeyboardBuilder()
    if cat_filters:
        # Диапазоны (цена/год/пробег/объём) — удобные пресеты из hardcoded.
        for f in fc.get_filters(cat_id, sub_path):
            if f.get("type") == "range" and _range_applies(f["id"]):
                kb.button(text=f["label"], callback_data=f"set:{f['id']}")
        # Селекты — реальные фильтры ss.lv (Консоль, КПП, Кузов, Цвет…).
        for i, f in enumerate(cat_filters):
            kb.button(text=f"🔽 {f['label']}", callback_data=f"catf:{i}")
        kb.button(text=t(lang, "keyword"), callback_data="set:keyword")
    else:
        for f in fc.get_filters(cat_id, sub_path):
            kb.button(text=f["label"], callback_data=f"set:{f['id']}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=t(lang,"reset_all"),   callback_data="reset_filters"))
    kb.row(
        InlineKeyboardButton(text=t(lang,"set_interval"),   callback_data="set:interval"),
        InlineKeyboardButton(text=t(lang,"save"),           callback_data="save"),
    )
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"),      callback_data="cancel"))

    interval = data.get("check_interval", cat_mod.DEFAULT_INTERVAL)
    text = (
        f"<b>{' › '.join(parts)}</b>\n\n"
        f"{_filter_summary(data)}\n"
        f"⏱ {t(lang,'interval_label')}: <b>{_interval_label(interval)}</b>\n\n"
        + t(lang, "filters_title")
    )
    await _edit(msg, text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(AddFilter.filters)


# ─────────────────────────────────────────────
# Роутинг кнопок главного меню
# ─────────────────────────────────────────────
@router.message(F.text.in_(_ALL_MENU_TEXT))
async def on_menu_button(msg: Message, state: FSMContext):
    action = _ALL_MENU_TEXT.get(msg.text, "")
    if action == "add":      await cmd_add(msg, state)
    elif action == "list":   await cmd_list(msg)
    elif action == "stats":  await cmd_stats(msg)
    elif action == "location": await cmd_location(msg, state)
    elif action == "lang":   await cmd_lang(msg, state)


# ─────────────────────────────────────────────
# /lang
# ─────────────────────────────────────────────
async def _show_lang_picker(msg: Message, edit: bool = False):
    kb = InlineKeyboardBuilder()
    for code, label in i18n.LANGS.items():
        kb.button(text=label, callback_data=f"setlang:{code}")
    kb.adjust(1)
    txt = "🌐 Izvēlies / Выбери / Choose:"
    if edit: await _edit(msg, txt, reply_markup=kb.as_markup())
    else:    await msg.answer(txt, reply_markup=kb.as_markup())


@router.message(Command("lang"))
async def cmd_lang(msg: Message, state: FSMContext):
    await state.clear()
    await _show_lang_picker(msg)
    await state.set_state(SetLang.picking)


@router.callback_query(SetLang.picking, F.data.startswith("setlang:"))
async def on_lang_pick(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":", 1)[1]
    await db.set_user_lang(cb.from_user.id, lang)
    user = await db.get_user(cb.from_user.id)
    loc  = t(lang, "loc_not_set")
    if user and user.get("location_name"):
        loc = f"📍 {user['location_name']}"
    await cb.message.edit_text(
        t(lang, "lang_set") + "\n\n" + t(lang, "start", loc=loc),
        parse_mode="HTML",
    )
    await cb.message.answer("⬇️", reply_markup=main_kb(lang))
    await state.clear()
    await cb.answer()


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await db.upsert_user(msg.from_user.id, msg.from_user.username)
    user = await db.get_user(msg.from_user.id)
    lang = (user or {}).get("lang")

    if not lang:
        await _show_lang_picker(msg)
        await state.set_state(SetLang.picking)
        return

    loc = f"📍 {user['location_name']}" if user and user.get("location_name") else t(lang, "loc_not_set")

    # Inline-кнопки в самом сообщении
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ " + {"ru":"Добавить фильтр","lv":"Pievienot filtru","en":"Add filter"}.get(lang,"Add filter"),
              callback_data="menu:add")
    kb.button(text="📋 " + {"ru":"Мои фильтры","lv":"Mani filtri","en":"My filters"}.get(lang,"My filters"),
              callback_data="menu:list")
    kb.button(text="📊 " + {"ru":"Статистика","lv":"Statistika","en":"Statistics"}.get(lang,"Statistics"),
              callback_data="menu:stats")
    kb.button(text="📍 " + {"ru":"Местоположение","lv":"Atrašanās vieta","en":"Location"}.get(lang,"Location"),
              callback_data="menu:location")
    kb.button(text="🌐 " + {"ru":"Язык","lv":"Valoda","en":"Language"}.get(lang,"Language"),
              callback_data="menu:lang")
    kb.adjust(1, 2, 2)

    greeting = {
        "ru": "👋 <b>ss.lv Monitor</b>\nМониторю любые объявления на ss.lv.\n\n" + loc,
        "lv": "👋 <b>ss.lv Monitor</b>\nUzraugu jebkādus sludinājumus.\n\n" + loc,
        "en": "👋 <b>ss.lv Monitor</b>\nMonitoring any listings on ss.lv.\n\n" + loc,
    }.get(lang, loc)

    # Сначала постоянная клавиатура внизу
    await msg.answer("⬇️", reply_markup=main_kb(lang))
    # Потом красивое сообщение с инлайн-кнопками
    await msg.answer(greeting, parse_mode="HTML", reply_markup=kb.as_markup())


# ─────────────────────────────────────────────
# /cancel
# ─────────────────────────────────────────────
@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    lang = await _lang(msg.from_user.id)
    await state.clear()
    await msg.answer(t(lang, "cancelled"), reply_markup=main_kb(lang))


# ─────────────────────────────────────────────
# /stats
# ─────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    import time
    lang    = await _lang(msg.from_user.id)
    filters = await db.list_filters(msg.from_user.id)
    if not filters:
        await msg.answer(t(lang, "stats_empty"))
        return
    now   = time.time()
    lines = [t(lang, "stats_title"), ""]
    total_sent = sum(f.get("total_sent") or 0 for f in filters)
    for f in filters:
        brand = f.get("brand") or ""
        model = f.get("model") or ""
        cat   = i18n.cat_label(f.get("category",""), lang)
        sent  = f.get("total_sent") or 0
        last  = f.get("last_sent_at") or "—"
        iv    = _interval_label(f.get("check_interval") or 300)
        lc    = f.get("last_checked_at") or 0
        ago   = int((now - lc) / 60) if lc else None
        head  = f"<b>#{f['id']}</b> {cat}"
        if brand: head += f" · {brand}"
        if model: head += f" {model}"
        lines.append(head)
        lines.append(f"   📨 {sent}  |  ⏱ {iv}")
        if ago is not None: lines.append(f"   🕐 {ago} мин. назад")
        if last != "—":     lines.append(f"   📬 {last[:16]}")
        lines.append("")
    lines.append(f"📊 Итого: <b>{total_sent}</b> уведомлений")
    lines.append(f"🔎 Активных: <b>{len(filters)}</b> / {config.MAX_FILTERS_PER_USER}")
    await msg.answer("\n".join(lines), parse_mode="HTML")



# ─── Инлайн-кнопки главного меню (из /start) ─────────────────
@router.callback_query(F.data.startswith("menu:"))
async def on_inline_menu(cb: CallbackQuery, state: FSMContext):
    action = cb.data.split(":", 1)[1]
    await cb.answer()
    if action == "add":
        await cmd_add(cb.message, state)
    elif action == "list":
        await cmd_list(cb.message)
    elif action == "stats":
        await cmd_stats(cb.message)
    elif action == "location":
        lang = await _lang(cb.from_user.id)
        await state.update_data(_lang=lang)
        await _show_city_menu(cb.message, state, page=0, edit=False, lang=lang)
        await state.set_state(SetLocation.waiting)
    elif action == "lang":
        await _show_lang_picker(cb.message, edit=False)
        await state.set_state(SetLang.picking)

# ─────────────────────────────────────────────
# /location — город кнопками
# ─────────────────────────────────────────────
@router.message(Command("location"))
async def cmd_location(msg: Message, state: FSMContext):
    lang = await _lang(msg.from_user.id)
    await state.clear()
    await state.update_data(_lang=lang)
    await _show_city_menu(msg, state, page=0, edit=False, lang=lang)
    await state.set_state(SetLocation.waiting)


async def _show_city_menu(msg, state, page=0, edit=True, lang="ru"):
    cities = geo.CITY_BUTTONS
    total  = max(1, (len(cities) - 1) // CITIES_PER_PAGE + 1)
    chunk  = cities[page * CITIES_PER_PAGE: (page + 1) * CITIES_PER_PAGE]
    kb = InlineKeyboardBuilder()
    for c in chunk:
        kb.button(text=c, callback_data=f"city:{c}")
    kb.adjust(3)
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"cpage:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"cpage:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"city_gps_btn"),  callback_data="city_gps"))
    kb.row(InlineKeyboardButton(text=t(lang,"city_type_btn"), callback_data="city_type"))
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"),        callback_data="cancel"))
    text = f"📍 <b>{t(lang,'city_page_title')}</b>\n<i>(стр. {page+1}/{total})</i>"
    if edit: await _edit(msg, text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:    await msg.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(SetLocation.waiting, F.data.startswith("cpage:"))
async def city_page_cb(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await _show_city_menu(cb.message, state, int(cb.data.split(":",1)[1]), True, data.get("_lang","ru"))
    await cb.answer()


@router.callback_query(SetLocation.waiting, F.data.startswith("city:"))
async def on_city_pick(cb: CallbackQuery, state: FSMContext):
    name  = cb.data.split(":",1)[1]
    data  = await state.get_data()
    lang  = data.get("_lang","ru")
    coords = geo.city_coords(name)
    if coords:
        lat, lon = coords
        await db.set_user_location(cb.from_user.id, lat, lon, name)
        await cb.message.edit_text(t(lang,"location_saved",name=name), parse_mode="HTML")
        await cb.message.answer("⬇️", reply_markup=main_kb(lang))
        await state.clear()
    else:
        await cb.answer("?", show_alert=True)


@router.callback_query(SetLocation.waiting, F.data == "city_gps")
async def city_gps_btn(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("_lang","ru")
    kb   = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang,"city_gps_btn"), request_location=True)],
                  [KeyboardButton(text=t(lang,"cancel"))]],
        resize_keyboard=True, one_time_keyboard=True,
    )
    await cb.message.answer("📍", reply_markup=kb)
    await cb.answer()


@router.callback_query(SetLocation.waiting, F.data == "city_type")
async def city_type_btn(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("✏️ Напиши название города:")
    await state.set_state(SetLocation.city_page)
    await cb.answer()


@router.message(SetLocation.city_page, F.text)
async def on_city_text_input(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("_lang","ru")
    text = (msg.text or "").strip()
    if text.lower() in ("отмена","cancel","atcelt"):
        await state.clear()
        await msg.answer(t(lang,"cancelled"), reply_markup=main_kb(lang))
        return
    coords = geo.city_coords(text)
    if coords:
        lat, lon = coords
        await db.set_user_location(msg.from_user.id, lat, lon, text.title())
        await state.clear()
        await msg.answer(t(lang,"location_saved",name=text.title()),
                         parse_mode="HTML", reply_markup=main_kb(lang))
    else:
        await msg.answer("⏳…")
        result = await geo.geocode_nominatim(text)
        if result:
            lat, lon, display = result
            await db.set_user_location(msg.from_user.id, lat, lon, text.title())
            await state.clear()
            await msg.answer(t(lang,"location_saved",name=display[:60]),
                             parse_mode="HTML", reply_markup=main_kb(lang))
        else:
            await msg.answer(t(lang,"location_notfound",name=text))


@router.message(SetLocation.waiting, F.location)
async def on_gps(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("_lang","ru")
    lat, lon = msg.location.latitude, msg.location.longitude
    name = geo.nearest_city(lat, lon) or f"{lat:.4f}, {lon:.4f}"
    await db.set_user_location(msg.from_user.id, lat, lon, name)
    await state.clear()
    await msg.answer(t(lang,"location_saved",name=name),
                     parse_mode="HTML", reply_markup=main_kb(lang))


# ─────────────────────────────────────────────
# /add → категории
# ─────────────────────────────────────────────
@router.message(Command("add"))
async def cmd_add(msg: Message, state: FSMContext):
    lang = await _lang(msg.from_user.id)
    cnt  = await db.count_filters(msg.from_user.id)
    if cnt >= config.MAX_FILTERS_PER_USER:
        await msg.answer(t(lang,"max_filters",max=config.MAX_FILTERS_PER_USER))
        return
    await state.clear()
    await state.update_data(_lang=lang)
    kb = InlineKeyboardBuilder()
    for c in cat_mod.TOP_CATEGORIES:
        kb.button(text=i18n.cat_label(c["id"],lang), callback_data=f"topcat:{c['id']}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await msg.answer(t(lang,"what_monitor"), reply_markup=kb.as_markup())
    await state.set_state(AddFilter.top_cat)


@router.callback_query(AddFilter.top_cat, F.data.startswith("topcat:"))
async def on_top_cat(cb: CallbackQuery, state: FSMContext):
    cat_id = cb.data.split(":",1)[1]
    cat    = next((c for c in cat_mod.TOP_CATEGORIES if c["id"]==cat_id), None)
    if not cat: return
    data   = await state.get_data()
    lang   = data.get("_lang","ru")
    cat_l  = i18n.cat_label(cat_id, lang)
    await state.update_data(
        cat_id=cat_id, cat_label=cat_l, cat_type=cat["type"], cat_path=cat["path"],
        price_min=None, price_max=None, year_min=None, year_max=None,
        mile_min=None, mile_max=None, gearbox=None, bodytype=None, keyword=None,
        check_interval=cat_mod.DEFAULT_INTERVAL,
        sub_label=None, sub_path=None,
        brand_slug=None, brand_name=None, model_slug=None, model_name=None,
        cat_filters=None, cols_sel={}, adopts_sel={},
    )
    await cb.message.edit_text(f"{cat_l}\n⏳…")
    await cb.bot.send_chat_action(cb.from_user.id, "typing")
    subs = await cache.subcats(cat["path"], p)
    if not subs:
        raw  = cat_mod.FALLBACK_SUBS.get(cat_id, [])
        subs = [{"name": i18n.translate_subcat(n,lang),
                 "slug": u.rstrip("/").rsplit("/",1)[-1], "url": u}
                for n, u in raw]
    else:
        for s in subs:
            if "url" not in s: s["url"] = cat["path"] + s["slug"] + "/"
            s["name"] = i18n.translate_subcat(s["name"], lang)

    # «Редкие авто» (ретро/спорт/тюнинг/эксклюзив/электро) — спец-разделы
    # легковых, которых нет в одноуровневой навигации /ru/transport/.
    if cat_id == "transport":
        have = {s.get("url") for s in subs}
        for name, url in cat_mod.CARS_SPECIAL:
            if url not in have:
                subs.append({"name": name,
                             "slug": url.rstrip("/").rsplit("/", 1)[-1],
                             "url": url})
    await state.update_data(subs=subs, nav_stack=[], nav_label=None)
    await _show_subs(cb.message, state, 0)
    await state.set_state(AddFilter.sub_cat)
    await cb.answer()


async def _show_subs(msg, state, page=0):
    data  = await state.get_data()
    subs  = data.get("subs",[])
    label = data.get("nav_label") or data.get("cat_label","")
    lang  = data.get("_lang","ru")
    total = max(1,(len(subs)-1)//SUBS_PER_PAGE+1)
    chunk = subs[page*SUBS_PER_PAGE:(page+1)*SUBS_PER_PAGE]
    kb = InlineKeyboardBuilder()
    for i, s in enumerate(chunk):
        kb.button(text=s.get("name",""), callback_data=f"sub:{page*SUBS_PER_PAGE+i}")
    kb.adjust(1)
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"subp:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"subp:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_top"))
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await _edit(msg, f"<b>{label}</b>: {t(lang,'choose_subcat')} <i>({page+1}/{total})</i>",
                reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(AddFilter.sub_cat, F.data.startswith("subp:"))
async def subs_page(cb: CallbackQuery, state: FSMContext):
    await _show_subs(cb.message, state, int(cb.data.split(":",1)[1]))
    await cb.answer()


@router.callback_query(AddFilter.sub_cat, F.data == "back_top")
async def back_top(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("_lang","ru")

    # Если мы углубились по дереву — поднимаемся на уровень вверх
    stack = data.get("nav_stack", [])
    if stack:
        prev = stack.pop()
        await state.update_data(nav_stack=stack, subs=prev["subs"],
                                nav_label=prev["label"])
        await _show_subs(cb.message, state, 0)
        await cb.answer(); return

    kb   = InlineKeyboardBuilder()
    for c in cat_mod.TOP_CATEGORIES:
        kb.button(text=i18n.cat_label(c["id"],lang), callback_data=f"topcat:{c['id']}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await cb.message.edit_text(t(lang,"what_monitor"), reply_markup=kb.as_markup())
    await state.set_state(AddFilter.top_cat)
    await cb.answer()


@router.callback_query(AddFilter.sub_cat, F.data.startswith("sub:"))
async def on_sub(cb: CallbackQuery, state: FSMContext):
    idx  = int(cb.data.split(":",1)[1])
    data = await state.get_data()
    subs = data.get("subs",[])
    lang = data.get("_lang","ru")
    if not (0 <= idx < len(subs)): return
    sub  = subs[idx]
    # смена раздела → сбрасываем фильтры категории и выбранные значения
    await state.update_data(sub_label=sub.get("name",""), sub_path=sub.get("url",""),
                            cat_filters=None, cols_sel={}, adopts_sel={})

    sub_url = sub.get("url","")
    if sub_url in ("__riga_flats__","__riga_houses__"):
        riga_type = "flats" if sub_url == "__riga_flats__" else "houses"
        base_url  = cat_mod.RIGA_REALTY_BASE[riga_type]
        await cb.message.edit_text("⏳…")
        await cb.bot.send_chat_action(cb.from_user.id, "typing")
        dynamic   = await p.get_subcategories(base_url)
        districts = [(d["name"],d["slug"]) for d in dynamic] if dynamic else list(cat_mod.RIGA_DISTRICTS)
        await state.update_data(riga_type=riga_type, riga_districts=districts, sub_path=base_url)
        await _show_riga_districts(cb.message, state, 0)
        await state.set_state(AddFilter.riga_district)
    elif sub_url in cat_mod.TRANSPORT_FULL:
        t_cat = cat_mod.TRANSPORT_FULL[sub_url]
        await cb.message.edit_text(f"<b>{sub['name']}</b>\n{t(lang,'loading_brands')}", parse_mode="HTML")
        await cb.bot.send_chat_action(cb.from_user.id, "typing")
        brands_list = await p.get_brands(t_cat)
        await state.update_data(transport_cat=t_cat, brands=brands_list)
        await _show_brands(cb.message, state, 0)
        await state.set_state(AddFilter.brand)
    else:
        # Универсальный рекурсивный drill по дереву ss.lv:
        # есть вложенные подкатегории → показываем их; нет → это лист
        # (сами объявления) → переходим к меню фильтров.
        await cb.message.edit_text(f"<b>{sub['name']}</b>\n⏳…", parse_mode="HTML")
        await cb.bot.send_chat_action(cb.from_user.id, "typing")
        children = await p.get_subcategories(sub_url) if sub_url.startswith("/") else []
        if children:
            stack = data.get("nav_stack", [])
            stack.append({"subs": subs, "label": data.get("nav_label") or data.get("cat_label","")})
            for s in children:
                s["name"] = i18n.translate_subcat(s["name"], lang)
            crumb = (data.get("nav_label") or data.get("cat_label","")) + " › " + sub["name"]
            await state.update_data(nav_stack=stack, subs=children, nav_label=crumb)
            await _show_subs(cb.message, state, 0)
        else:
            await _show_filter_menu(cb.message, state)
    await cb.answer()


# ─── Riga districts ───────────────────────────────────────────
RIGA_PAGE = 12

async def _show_riga_districts(msg, state, page=0):
    data  = await state.get_data()
    lang  = data.get("_lang","ru")
    dist  = data.get("riga_districts",[])
    rtype = data.get("riga_type","flats")
    title = "🏘 Квартиры" if rtype=="flats" else "🏠 Дома"
    total = max(1,(len(dist)-1)//RIGA_PAGE+1)
    chunk = dist[page*RIGA_PAGE:(page+1)*RIGA_PAGE]
    kb    = InlineKeyboardBuilder()
    for name, slug in chunk:
        kb.button(text=name, callback_data=f"rig:{slug}:{name}")
    kb.adjust(2)
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"rigp:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"rigp:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"all_riga"), callback_data="rig:_all_:Вся Рига"))
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_sub"),
           InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await _edit(msg, f"<b>{title}</b>: {t(lang,'choose_district')} <i>({page+1}/{total})</i>",
                reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(AddFilter.riga_district, F.data.startswith("rigp:"))
async def riga_page(cb: CallbackQuery, state: FSMContext):
    await _show_riga_districts(cb.message, state, int(cb.data.split(":",1)[1]))
    await cb.answer()


@router.callback_query(AddFilter.riga_district, F.data.startswith("rig:"))
async def on_riga_district(cb: CallbackQuery, state: FSMContext):
    _, slug, name = cb.data.split(":",2)
    data = await state.get_data()
    rtype = data.get("riga_type","flats")
    url   = cat_mod.RIGA_REALTY_BASE[rtype] if slug=="_all_" else cat_mod.RIGA_REALTY_BASE[rtype]+slug+"/"
    await state.update_data(sub_label=name, sub_path=url)
    await _show_filter_menu(cb.message, state)
    await cb.answer()


@router.callback_query(AddFilter.riga_district, F.data == "back_sub")
async def riga_back_sub(cb: CallbackQuery, state: FSMContext):
    await _show_subs(cb.message, state, 0)
    await state.set_state(AddFilter.sub_cat)
    await cb.answer()


# ─── Transport: Brand → Model ─────────────────────────────────
async def _show_brands(msg, state, page=0):
    data  = await state.get_data()
    lst   = data.get("brands",[])
    lang  = data.get("_lang","ru")
    sub   = data.get("sub_label","")
    total = max(1,(len(lst)-1)//br.PAGE_SIZE+1)
    chunk = lst[page*br.PAGE_SIZE:(page+1)*br.PAGE_SIZE]
    kb    = InlineKeyboardBuilder()
    for item in chunk:
        kb.button(text=item["name"], callback_data=f"br:{item['slug']}:{item['name']}")
    kb.adjust(3)
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"brp:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"brp:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"input_manual"), callback_data="br:_manual_:"))
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_sub_from_brand"))
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await _edit(msg, f"<b>{sub}</b>: {t(lang,'choose_brand')} <i>({page+1}/{total})</i>",
                reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(AddFilter.brand, F.data.startswith("brp:"))
async def brands_page(cb: CallbackQuery, state: FSMContext):
    await _show_brands(cb.message, state, int(cb.data.split(":",1)[1]))
    await cb.answer()


@router.callback_query(AddFilter.brand, F.data == "back_sub_from_brand")
async def back_sub_from_brand(cb: CallbackQuery, state: FSMContext):
    await _show_subs(cb.message, state, 0)
    await state.set_state(AddFilter.sub_cat)
    await cb.answer()


@router.callback_query(AddFilter.brand, F.data.startswith("br:"))
async def on_brand(cb: CallbackQuery, state: FSMContext):
    _, slug, name = cb.data.split(":",2)
    data = await state.get_data()
    lang = data.get("_lang","ru")
    if slug == "_manual_":
        kbm = InlineKeyboardBuilder()
        kbm.button(text=t(lang,"cancel"), callback_data="cancel")
        await cb.message.edit_text(t(lang,"input_brand"), parse_mode="HTML",
                                   reply_markup=kbm.as_markup())
        await state.update_data(manual_input="brand")
        await state.set_state(AddFilter.model_type)
        await cb.answer(); return
    await state.update_data(brand_slug=slug, brand_name=name)
    await cb.message.edit_text(f"<b>{name}</b>\n{t(lang,'loading_models')}", parse_mode="HTML")
    await cb.bot.send_chat_action(cb.from_user.id, "typing")
    models = []
    try:
        models = await cache.models(slug, data.get("transport_cat","cars"), p)
    except Exception as e:
        log.warning(f"get_models: {e}")
    await state.update_data(models=models)
    await _show_model_kb(cb.message, state)
    await state.set_state(AddFilter.model)
    await cb.answer()


async def _show_model_kb(msg, state, page=0):
    data   = await state.get_data()
    models = data.get("models",[])
    brand  = data.get("brand_name","")
    lang   = data.get("_lang","ru")
    PAGE   = 12
    kb     = InlineKeyboardBuilder()
    kb.button(text=t(lang,"any_model"), callback_data="md:_any_:Любая")
    if models:
        total = max(1,(len(models)-1)//PAGE+1)
        chunk = models[page*PAGE:(page+1)*PAGE]
        for m in chunk:
            kb.button(text=m["name"], callback_data=f"md:{m['slug']}:{m['name'][:20]}")
        kb.adjust(3)
        nav = []
        if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"mdp:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
        if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"mdp:{page+1}"))
        if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"input_manual"), callback_data="md:_manual_:"))
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_brands"))
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    status = t(lang,"models_found",n=len(models)) if models else t(lang,"models_failed")
    await _edit(msg, f"<b>{brand}</b>: {t(lang,'choose_model')}\n<i>{status}</i>",
                reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(AddFilter.model, F.data.startswith("mdp:"))
async def models_page(cb: CallbackQuery, state: FSMContext):
    await _show_model_kb(cb.message, state, int(cb.data.split(":",1)[1]))
    await cb.answer()


@router.callback_query(AddFilter.model, F.data == "back_brands")
async def back_brands(cb: CallbackQuery, state: FSMContext):
    await _show_brands(cb.message, state, 0)
    await state.set_state(AddFilter.brand)
    await cb.answer()


@router.callback_query(AddFilter.model, F.data.startswith("md:"))
async def on_model(cb: CallbackQuery, state: FSMContext):
    _, slug, name = cb.data.split(":",2)
    data = await state.get_data()
    lang = data.get("_lang","ru")
    if slug == "_manual_":
        kbm = InlineKeyboardBuilder()
        kbm.button(text=t(lang,"cancel"), callback_data="cancel")
        await cb.message.edit_text(t(lang,"input_model"), reply_markup=kbm.as_markup())
        await state.update_data(manual_input="model")
        await state.set_state(AddFilter.model_type)
        await cb.answer(); return
    await state.update_data(
        model_slug=None if slug=="_any_" else slug,
        model_name=None if slug=="_any_" else name,
    )
    await _show_filter_menu(cb.message, state)
    await cb.answer()


@router.message(AddFilter.model_type)
async def on_manual_input(msg: Message, state: FSMContext):
    data  = await state.get_data()
    which = data.get("manual_input","model")
    lang  = data.get("_lang","ru")
    text  = (msg.text or "").strip()
    if not text: return
    slug = text.lower().replace(" ","-")
    if which == "brand":
        await state.update_data(brand_slug=slug, brand_name=text.title(), models=[])
        await msg.answer(f"<b>{text.title()}</b>\n{t(lang,'loading_models')}", parse_mode="HTML")
        await msg.bot.send_chat_action(msg.chat.id, "typing")
        models = []
        try:
            models = await cache.models(slug, data.get("transport_cat","cars"), p)
        except Exception: pass
        await state.update_data(models=models)
        await _show_model_kb(msg, state)
        await state.set_state(AddFilter.model)
    else:
        await state.update_data(model_slug=slug, model_name=text.title())
        await _show_filter_menu(msg, state)


# ─────────────────────────────────────────────
# Меню фильтров — пресеты + ввод
# ─────────────────────────────────────────────
@router.callback_query(AddFilter.filters, F.data.startswith("set:"))
async def on_set_filter(cb: CallbackQuery, state: FSMContext):
    which = cb.data.split(":",1)[1]
    data  = await state.get_data()
    lang  = data.get("_lang","ru")

    if which == "interval":
        kb = InlineKeyboardBuilder()
        for label, sec in cat_mod.INTERVALS:
            kb.button(text=label, callback_data=f"iv:{sec}")
        kb.adjust(2)
        kb.row(InlineKeyboardButton(text=t(lang,"back"), callback_data="back_to_filters"))
        await cb.message.edit_text(t(lang,"interval_title"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.interval)
        await cb.answer(); return

    if which == "price":
        kb = _preset_kb(PRICE_PRESETS, "price", lang)
        await cb.message.edit_text(t(lang,"price_hint"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_price)
        await cb.answer(); return

    if which == "year":
        kb = _preset_kb(YEAR_PRESETS, "year", lang)
        await cb.message.edit_text(t(lang,"year_hint"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_year)
        await cb.answer(); return

    if which == "mileage":
        kb = _preset_kb(MILEAGE_PRESETS, "mileage", lang)
        await cb.message.edit_text(t(lang,"mileage_hint"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_mileage)
        await cb.answer(); return

    # Универсальный обработчик select-фильтров
    SELECT_MAP = {
        "gearbox":    (br.GEARBOX_OPTIONS,    "⚙️ Коробка передач"),
        "bodytype":   (br.BODYTYPE_OPTIONS,   "🚙 Тип кузова"),
        "fuel":       (fc.FUEL_OPTIONS,       "⛽ Тип топлива"),
        "drive":      (fc.DRIVE_OPTIONS,      "🔄 Привод"),
        "color":      (fc.COLOR_OPTIONS,      "🎨 Цвет"),
        "rooms":      (fc.ROOMS_OPTIONS,      "🚪 Комнат"),
        "floor":      (fc.FLOOR_OPTIONS,      "🏢 Этаж"),
        "condition":  (fc.CONDITION_OPTIONS,  "✨ Состояние"),
        "size":       (fc.SIZE_OPTIONS,       "📏 Размер"),
        "experience": (fc.EXPERIENCE_OPTIONS, "📋 Опыт"),
    }
    if which in SELECT_MAP:
        options, title = SELECT_MAP[which]
        kb2 = InlineKeyboardBuilder()
        for label, val in options:
            kb2.button(text=label, callback_data=f"pick:{which}:{val}")
        kb2.adjust(2)
        kb2.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data=f"clear:{which}"),
                InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
        await cb.message.edit_text(f"<b>{title}</b>:",
                                   reply_markup=kb2.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_gearbox)
        await cb.answer(); return

    # Диапазонные с пресетами
    RANGE_MAP = {
        "engine": (fc.ENGINE_PRESETS, "🔧 Объём двигателя", "engine"),
        "area":   (fc.AREA_PRESETS,   "📐 Площадь м²",      "area"),
    }
    if which in RANGE_MAP:
        presets, title, key = RANGE_MAP[which]
        kb2 = _preset_kb(presets, key, lang)
        await cb.message.edit_text(f"<b>{title}</b>:",
                                   reply_markup=kb2.as_markup(), parse_mode="HTML")
        # отдельное состояние, чтобы ручной ввод не попал в цену
        await state.update_data(_rk=key)
        await state.set_state(AddFilter.inp_range)
        await cb.answer(); return

    if which == "gearbox":
        kb = InlineKeyboardBuilder()
        for label, val in br.GEARBOX_OPTIONS:
            kb.button(text=label, callback_data=f"pick:gearbox:{val}")
        kb.adjust(1)
        kb.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data="clear:gearbox"),
               InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
        await cb.message.edit_text(t(lang,"gearbox_title"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_gearbox)
        await cb.answer(); return

    if which == "bodytype":
        kb = InlineKeyboardBuilder()
        for label, val in br.BODYTYPE_OPTIONS:
            kb.button(text=label, callback_data=f"pick:bodytype:{val}")
        kb.adjust(2)
        kb.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data="clear:bodytype"),
               InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
        await cb.message.edit_text(t(lang,"bodytype_title"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_bodytype)
        await cb.answer(); return

    if which == "keyword":
        kb = InlineKeyboardBuilder()
        kb.button(text=t(lang,"clear"), callback_data="clear:keyword")
        kb.button(text=t(lang,"back"),  callback_data="back_to_filters")
        kb.adjust(2)
        await cb.message.edit_text(t(lang,"keyword_hint"),
                                   reply_markup=kb.as_markup(), parse_mode="HTML")
        await state.set_state(AddFilter.inp_keyword)
        await cb.answer(); return


# ─── Динамические фильтры категории (Консоль, Сост. и т.п.) ────
@router.callback_query(AddFilter.filters, F.data.startswith("catf:"))
async def on_cat_filter(cb: CallbackQuery, state: FSMContext):
    i    = int(cb.data.split(":",1)[1])
    data = await state.get_data()
    lang = data.get("_lang","ru")
    cat_filters = data.get("cat_filters") or []
    if not (0 <= i < len(cat_filters)):
        await cb.answer(); return
    f  = cat_filters[i]
    kb = InlineKeyboardBuilder()
    for j, opt in enumerate(f["options"]):
        kb.button(text=opt, callback_data=f"catpick:{i}:{j}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data=f"catclear:{i}"),
           InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
    await cb.message.edit_text(f"<b>{f['label']}</b>:",
                               reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(AddFilter.filters, F.data.startswith("catpick:"))
async def on_cat_pick(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    if len(parts) < 3: await cb.answer(); return
    i, j = int(parts[1]), int(parts[2])
    data = await state.get_data()
    cat_filters = data.get("cat_filters") or []
    if not (0 <= i < len(cat_filters)) or not (0 <= j < len(cat_filters[i]["options"])):
        await cb.answer(); return
    f   = cat_filters[i]
    key = "adopts_sel" if f.get("source") == "adopt" else "cols_sel"
    sel = dict(data.get(key) or {})
    sel[f["label"]] = f["options"][j]
    await state.update_data(**{key: sel})
    await _show_filter_menu(cb.message, state)
    await cb.answer("✅")


@router.callback_query(AddFilter.filters, F.data.startswith("catclear:"))
async def on_cat_clear(cb: CallbackQuery, state: FSMContext):
    i    = int(cb.data.split(":",1)[1])
    data = await state.get_data()
    cat_filters = data.get("cat_filters") or []
    if 0 <= i < len(cat_filters):
        f   = cat_filters[i]
        key = "adopts_sel" if f.get("source") == "adopt" else "cols_sel"
        sel = dict(data.get(key) or {})
        sel.pop(f["label"], None)
        await state.update_data(**{key: sel})
    await _show_filter_menu(cb.message, state)
    await cb.answer("🗑")


# ─── Обработка пресетов ───────────────────────────────────────
@router.callback_query(F.data.startswith("preset:"))
async def on_preset(cb: CallbackQuery, state: FSMContext):
    _, which, lo_s, hi_s = cb.data.split(":",3)

    # «Своё значение» → переходим в текстовый ввод
    if lo_s == "custom":
        data = await state.get_data()
        lang = data.get("_lang","ru")
        hints = {"price": t(lang,"price_hint"), "year": t(lang,"year_hint"),
                 "mileage": t(lang,"mileage_hint"),
                 "engine": "🔧 <b>Объём в куб.см</b>\nПример: <code>1500-2000</code> (1.5–2.0 л)"}
        kb = InlineKeyboardBuilder()
        kb.button(text=t(lang,"back"), callback_data="back_to_filters")
        await cb.message.edit_text(
            hints.get(which,"") + f"\n\n{CUSTOM_LABEL}:",
            reply_markup=kb.as_markup(), parse_mode="HTML",
        )
        # оставляем текущий state для получения текста
        await cb.answer(); return

    lo = None if lo_s == "X" else int(lo_s)
    hi = None if hi_s == "X" else int(hi_s)

    key_map = {
        "price":   ("price_min","price_max"),
        "year":    ("year_min", "year_max"),
        "mileage": ("mile_min", "mile_max"),
        "engine":  ("engine_min","engine_max"),
        "area":    ("area_min", "area_max"),
    }
    k_min, k_max = key_map[which]
    await state.update_data(**{k_min: lo, k_max: hi})
    await _show_filter_menu(cb.message, state)
    await cb.answer("✅")


# ─── Выбор КПП / кузова ───────────────────────────────────────
@router.callback_query(F.data.startswith("pick:"))
async def on_pick_option(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":", 2)
    if len(parts) < 3: await cb.answer(); return
    _, field, val = parts
    await state.update_data(**{field: val})
    await _show_filter_menu(cb.message, state)
    await cb.answer("✅")


# ─── Интервал ─────────────────────────────────────────────────
@router.callback_query(AddFilter.interval, F.data.startswith("iv:"))
async def on_interval(cb: CallbackQuery, state: FSMContext):
    sec = int(cb.data.split(":",1)[1])
    await state.update_data(check_interval=sec)
    await _show_filter_menu(cb.message, state)
    await cb.answer(f"✅ {_interval_label(sec)}")


# ─── Очистить ─────────────────────────────────────────────────
@router.callback_query(F.data.startswith("clear:"))
async def clear_filter(cb: CallbackQuery, state: FSMContext):
    which = cb.data.split(":",1)[1]
    upd = {
        "price":{"price_min":None,"price_max":None},"year":{"year_min":None,"year_max":None},
        "mileage":{"mile_min":None,"mile_max":None},"engine":{"engine_min":None,"engine_max":None},
        "area":{"area_min":None,"area_max":None},
    }.get(which, {which: None})
    await state.update_data(**upd)
    await _show_filter_menu(cb.message, state)
    await cb.answer("🗑")


@router.callback_query(F.data == "back_to_filters")
async def back_to_filters(cb: CallbackQuery, state: FSMContext):
    await _show_filter_menu(cb.message, state)
    await cb.answer()


@router.callback_query(AddFilter.filters, F.data == "reset_filters")
async def reset_all(cb: CallbackQuery, state: FSMContext):
    await state.update_data(
        price_min=None,price_max=None,year_min=None,year_max=None,
        mile_min=None,mile_max=None,engine_min=None,engine_max=None,
        area_min=None,area_max=None,gearbox=None,bodytype=None,
        fuel=None,drive=None,color=None,rooms=None,floor=None,
        condition=None,size=None,experience=None,keyword=None,
        cols_sel={}, adopts_sel={})
    await _show_filter_menu(cb.message, state)
    await cb.answer("🧹")


# ─── Текстовый ввод (цена/год/пробег/слово) ───────────────────
async def _handle_range_text(msg, state, k_min, k_max):
    vmin, vmax = _parse_range(msg.text)
    if vmin is None and vmax is None:
        data = await state.get_data()
        lang = data.get("_lang","ru")
        await msg.answer("Пример: <code>1000-5000</code>  или  <code>-5000</code>  или  <code>2000-</code>", parse_mode="HTML")
        return
    await state.update_data(**{k_min:vmin, k_max:vmax})
    await _show_filter_menu(msg, state)


@router.message(AddFilter.inp_price)
async def on_price(msg, state): await _handle_range_text(msg, state, "price_min", "price_max")

@router.message(AddFilter.inp_year)
async def on_year(msg, state):  await _handle_range_text(msg, state, "year_min",  "year_max")

@router.message(AddFilter.inp_mileage)
async def on_mileage(msg, state): await _handle_range_text(msg, state, "mile_min", "mile_max")

@router.message(AddFilter.inp_range)
async def on_range(msg, state):
    data = await state.get_data()
    keys = {"engine": ("engine_min", "engine_max"),
            "area":   ("area_min",   "area_max")}.get(data.get("_rk", ""))
    if not keys:
        await _show_filter_menu(msg, state); return
    await _handle_range_text(msg, state, keys[0], keys[1])

@router.message(AddFilter.inp_keyword)
async def on_keyword(msg: Message, state: FSMContext):
    await state.update_data(keyword=(msg.text or "").strip() or None)
    await _show_filter_menu(msg, state)


# ─────────────────────────────────────────────
# Сохранение фильтра
# ─────────────────────────────────────────────
@router.callback_query(AddFilter.filters, F.data == "save")
async def save_filter(cb: CallbackQuery, state: FSMContext):
    data  = await state.get_data()
    lang  = data.get("_lang","ru")
    bslug = data.get("brand_slug")
    mslug = data.get("model_slug")
    brand = data.get("brand_name")
    model = data.get("model_name")
    sub_path = data.get("sub_path","")

    if bslug and sub_path in cat_mod.TRANSPORT_FULL:
        t_cat = cat_mod.TRANSPORT_FULL[sub_path]
        base  = p.build_listing_url(bslug, mslug, category=t_cat)
    else:
        base = "https://www.ss.lv" + sub_path if sub_path else ""

    # Критерии фильтра храним в params и применяем на стороне бота:
    # ss.lv фильтрует через POST/сессию, по сохранённому GET-URL не отфильтровать.
    params: dict = {}
    for key in ("price_min", "price_max", "year_min", "year_max",
                "mile_min", "mile_max", "engine_min", "engine_max"):
        v = data.get(key)
        if v not in (None, "", 0):
            params[key] = v
    # Топливо фильтруем по странице объявления (в списке надёжно только дизель),
    # храним канон: diesel/petrol/gas/hybrid/electric.
    if data.get("fuel"):
        cf = p.canon_fuel(data["fuel"])
        if cf:
            params["fuel"] = cf
    # Фильтры категории: по колонкам списка (Консоль/Сост.) и из карточки
    # объявления (КПП/кузов/цвет/топливо).
    cols_sel   = data.get("cols_sel") or {}
    adopts_sel = data.get("adopts_sel") or {}
    if cols_sel:
        params["cols"] = cols_sel
    if adopts_sel:
        params["adopts"] = adopts_sel
    url = base  # чистый URL марки/модели/сделки без неработающих GET-параметров

    combined_kw = data.get("keyword") or None

    summary: dict = {}
    def rng(a,b,u=""):
        if a and b: return f"{a}–{b}{u}"
        if a: return f"от {a}{u}"
        if b: return f"до {b}{u}"
        return None
    for key,kmin,kmax,unit in [
        ("price","price_min","price_max"," €"),
        ("year","year_min","year_max",""),
        ("mileage","mile_min","mile_max"," км"),
    ]:
        r = rng(data.get(kmin),data.get(kmax),unit)
        if r: summary[key] = r
    if data.get("keyword"):  summary["keyword"]  = data["keyword"]
    for label, val in {**cols_sel, **adopts_sel}.items():
        summary[label] = val

    await cb.message.edit_text(t(lang,"saving"))
    await cb.bot.send_chat_action(cb.from_user.id, "typing")

    fid = await db.add_filter(
        user_id=cb.from_user.id, category=data.get("cat_id","other"),
        category_path=sub_path, brand=brand, brand_slug=bslug,
        model=model, model_slug=mslug,
        params=params, params_summary=summary,
        keyword=combined_kw, url=url,
        check_interval=data.get("check_interval", cat_mod.DEFAULT_INTERVAL),
    )

    seen_n = 0
    try:
        ads = await asyncio.wait_for(p.fetch_listings(url), timeout=15.0)
        ads = p.apply_keyword(ads, combined_kw)
        ads = p.apply_filters(ads, params)
        await db.mark_seen(fid, [a["id"] for a in ads])
        seen_n = len(ads)
    except Exception as e:
        log.warning(f"snapshot: {e}")

    specs_block = ""
    if brand and model and sub_path in cat_mod.TRANSPORT_FULL:
        year = data.get("year_min") or data.get("year_max")
        specs_block = cs.lookup_info_block(brand, model, year)

    cat_l = data.get("cat_label","")
    sub_l = data.get("sub_label","")
    iv    = data.get("check_interval", cat_mod.DEFAULT_INTERVAL)

    text = (
        t(lang,"saved",fid=fid,n=seen_n,url=url)
        + f"\n\n{cat_l}" + (f" › {sub_l}" if sub_l else "")
        + (f"\n<b>{brand}</b>" if brand else "")
        + (f" {model}" if model else "")
        + f"\n{_filter_summary(data)}"
        + f"\n⏱ {_interval_label(iv)}"
        + specs_block
    )
    await cb.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)
    await state.clear()
    await cb.answer()


# ─────────────────────────────────────────────
# /list
# ─────────────────────────────────────────────
@router.message(Command("list"))
async def cmd_list(msg: Message):
    lang    = await _lang(msg.from_user.id)
    filters = await db.list_filters(msg.from_user.id)
    if not filters:
        await msg.answer(t(lang,"no_filters"))
        return
    for f in filters:
        s     = f.get("params_summary") or {}
        brand = f.get("brand") or ""
        model = f.get("model") or ""
        cat   = i18n.cat_label(f.get("category",""), lang)
        iv    = _interval_label(f.get("check_interval") or 300)
        sent  = f.get("total_sent") or 0
        lines = [f"<b>#{f['id']}</b> {cat}"]
        if brand: lines.append(f"  🚗 {brand}{f' {model}' if model else ''}")
        for k,icon in [("price","💶"),("year","📅"),("mileage","🛣"),
                       ("gearbox","⚙️"),("bodytype","🚙"),("keyword","🔎")]:
            if s.get(k): lines.append(f"  {icon} {s[k]}")
        lines.append(f"  ⏱ {iv}  |  📨 {sent}")
        kb = InlineKeyboardBuilder()
        kb.button(text=t(lang,"open_sslv"), url=f["url"])
        kb.button(text=t(lang,"delete_btn"), callback_data=f"del:{f['id']}")
        kb.adjust(2)
        await msg.answer("\n".join(lines), reply_markup=kb.as_markup(),
                         parse_mode="HTML", disable_web_page_preview=True)


@router.callback_query(F.data.startswith("del:"))
async def del_filter(cb: CallbackQuery):
    fid  = int(cb.data.split(":",1)[1])
    lang = await _lang(cb.from_user.id)
    await db.delete_filter(fid, cb.from_user.id)
    await cb.message.edit_text(t(lang,"filter_deleted",fid=fid))
    await cb.answer()


# ─────────────────────────────────────────────
# Общие callbacks
# ─────────────────────────────────────────────
@router.callback_query(F.data == "cancel")
async def on_cancel(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("_lang") or await _lang(cb.from_user.id)
    await state.clear()
    try:    await cb.message.edit_text(t(lang,"cancelled"))
    except: pass
    await cb.answer()


@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer()


# Регистрируется ПОСЛЕДНИМ: ловит устаревшие кнопки (после смены состояния/
# нового /add), чтобы у пользователя не висели «часики».
@router.callback_query()
async def on_stale_callback(cb: CallbackQuery):
    try:
        await cb.answer("⏳ Кнопка устарела — открой меню заново: /add", show_alert=False)
    except Exception:
        pass
