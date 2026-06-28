"""
ss.lv Monitor Bot — полная версия.
Все меню — кнопки. Постоянная клавиатура внизу. Пресеты цена/год/пробег.
"""
import asyncio
import logging
from datetime import datetime
from html import escape as _esc

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommandScopeChat,
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
import monitor

log = logging.getLogger("bot")
router = Router()

BRANDS_PER_PAGE = br.PAGE_SIZE
CITIES_PER_PAGE = 15
SUBS_PER_PAGE   = 8   # по 2 в ряд → 4 строки, помещается на один экран


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
    waiting = State()

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
        "lang":     "🌐 LV/RU",
        "diag":     "🩺 Диагностика",
    },
    "lv": {
        "add":      "➕ Pievienot filtru",
        "list":     "📋 Mani filtri",
        "stats":    "📊 Statistika",
        "location": "📍 Mana vieta",
        "lang":     "🌐 LV/RU",
        "diag":     "🩺 Diagnostika",
    },
    # «en» оставлен только для маршрутизации старых (англ.) клавиатур у юзеров,
    # что выбирали English до перехода на ru/lv. Новые клавиатуры — ru/lv.
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
    )
    kb.row(
        KeyboardButton(text=b["lang"]),
        KeyboardButton(text=b.get("diag", "🩺")),
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
    """Показать следующий экран меню НОВЫМ сообщением внизу чата.

    Раньше тут был edit_text (правка на месте), но Telegram при росте меню
    проматывал к ВЕРХУ редактируемого сообщения — отсюда «прыжок вверх».
    Теперь шлём НОВОЕ сообщение и удаляем старое: клиент сам проматывает чат
    ВНИЗ к свежему меню. Сначала отправка, потом удаление — чтобы при сбое
    отправки чат не остался пустым.
    """
    try:
        new = await msg.answer(text, **kw)
        try:    await msg.delete()
        except Exception: pass
        return new
    except Exception as e:
        log.warning(f"_edit send failed: {e}")
        try:    return await msg.edit_text(text, **kw)   # фолбэк: правка на месте
        except Exception: return msg


def _grid(kb: InlineKeyboardBuilder, btns: list, wide: int = 3):
    """Разложить кнопки рядами так, чтобы подписи НЕ обрезались ни на каком языке.

    Чем длиннее самая длинная подпись — тем меньше колонок (шире кнопки):
    >24 символов → по 1 в ряд, >12 → по 2, иначе → `wide`. Так длинные названия
    (особенно латышские) получают полную ширину и помещаются целиком.
    """
    if not btns:
        return
    m = max(len(b.text) for b in btns)
    cols = 1 if m > 24 else (2 if m > 12 else wide)
    for i in range(0, len(btns), cols):
        kb.row(*btns[i:i + cols])


async def _top_cats(lang: str) -> list[dict]:
    """Верхние категории = курируемые 12 (свои эмодзи/порядок) + автоматически
    подхваченные НОВЫЕ из корня ss.lv. Если ss.lv когда-нибудь добавит новый
    верхний раздел — он появится в боте сам, с нативным именем на двух языках и
    эмодзи 📁, без правок кода. Кэш на язык (TTL ~1ч) → работает годами.
    """
    key = f"topcats:{lang}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    cats = [{"id": c["id"], "path": c["path"], "type": c["type"],
             "label": i18n.cat_label(c["id"], lang)} for c in cat_mod.TOP_CATEGORIES]
    known = {p._loc(c["path"], "ru").rstrip("/") for c in cats}
    try:
        root = await asyncio.wait_for(p.get_subcategories("/ru/", lang), timeout=10)
        for r in root:
            canon = p._loc(r.get("url", ""), "ru").rstrip("/")
            if canon and canon not in known:
                cats.append({"id": "auto:" + r["slug"], "path": canon + "/",
                             "type": "simple", "label": "📁 " + r["name"]})
                known.add(canon)
                log.info("автоподхват новой верхней категории: %s", r["name"])
    except Exception as e:
        log.warning("top cats autodiscover: %s", e)
    cache.put(key, cats)
    return cats


async def _lang(user_id: int) -> str:
    u = await db.get_user(user_id)
    l = (u or {}).get("lang") or "ru"
    return l if l in ("ru", "lv") else "ru"   # интерфейс только ru/lv


def _brand_list(category: str):
    return br.CAR_BRANDS if category == "cars" else br.MOTO_BRANDS


def _interval_label(sec: int, lang: str = "ru") -> str:
    u = {"ru": ("мин", "ч"), "en": ("min", "h"), "lv": ("min.", "st.")}.get(lang, ("мин", "ч"))
    return f"{sec//3600} {u[1]}" if sec % 3600 == 0 else f"{sec//60} {u[0]}"


# Метки сводки фильтра по языкам
_SUMMARY_L = {
    "ru": {"price":"💶 Цена","year":"📅 Год","mileage":"🛣 Пробег","engine":"🔧 Двигатель",
           "area":"📐 Площадь","none":"Фильтры не заданы","from":"от","to":"до","km":" км"},
    "en": {"price":"💶 Price","year":"📅 Year","mileage":"🛣 Mileage","engine":"🔧 Engine",
           "area":"📐 Area","none":"No filters set","from":"from","to":"up to","km":" km"},
    "lv": {"price":"💶 Cena","year":"📅 Gads","mileage":"🛣 Nobraukums","engine":"🔧 Dzinējs",
           "area":"📐 Platība","none":"Filtri nav iestatīti","from":"no","to":"līdz","km":" km"},
}


def _filter_summary(data: dict, lang: str = "ru") -> str:
    L = _SUMMARY_L.get(lang, _SUMMARY_L["ru"])
    def rng(a, b, u=""):
        if a and b: return f"{a}–{b}{u}"
        if a: return f"{L['from']} {a}{u}"
        if b: return f"{L['to']} {b}{u}"
        return None
    lines = []
    r = rng(data.get("price_min"),  data.get("price_max"),  " €")
    if r: lines.append(f"{L['price']}: {r}")
    r = rng(data.get("year_min"),   data.get("year_max"))
    if r: lines.append(f"{L['year']}: {r}")
    r = rng(data.get("mile_min"),   data.get("mile_max"),   L['km'])
    if r: lines.append(f"{L['mileage']}: {r}")
    r = rng(data.get("engine_min"), data.get("engine_max"), " cc")
    if r: lines.append(f"{L['engine']}: {r}")
    r = rng(data.get("area_min"),   data.get("area_max"),   " m²")
    if r: lines.append(f"{L['area']}: {r}")
    # Значения опций храним по-русски (для матчинга), показываем локализованно.
    vmap: dict[str, str] = {}
    for f in (data.get("cat_filters") or []):
        for ru_v, disp_v in zip(f.get("options", []), f.get("options_disp") or f.get("options", [])):
            vmap[ru_v] = disp_v
    for label, val in (data.get("cols_sel") or {}).items():
        lines.append(f"🔹 {i18n.filter_label(label, lang)}: {vmap.get(val, val)}")
    for label, val in (data.get("adopts_sel") or {}).items():
        lines.append(f"🔹 {i18n.filter_label(label, lang)}: {vmap.get(val, val)}")
    if data.get("keyword"):
        lines.append(f"🔎 {_esc(str(data['keyword']))}")
    return "\n".join(lines) if lines else L["none"]


async def _show_filter_menu(msg: Message, state: FSMContext):
    data  = await state.get_data()
    lang  = data.get("_lang", "ru")

    cat_id   = data.get("cat_id", "")
    sub_path = data.get("sub_path", "")

    # Лениво (один раз) подтягиваем РЕАЛЬНЫЕ фильтры ss.lv — уже локализованные
    # (значения с /lv/), поэтому новые варианты (топливо/цвет) переводятся сами.
    #  • легковые (марочный флоу) → форма конкретной марки/модели …/sell/;
    #  • остальные категории      → лист по sub_path.
    # Если скрейп не удался — cf=[] и ниже сработает hardcoded-фолбэк.
    if data.get("cat_filters") is None:
        cf = []
        target = None
        if data.get("brand_slug"):
            t_cat  = data.get("transport_cat", "cars")
            target = p.build_listing_url(data["brand_slug"], data.get("model_slug"), category=t_cat)
        elif sub_path.startswith("/"):
            target = "https://www.ss.lv" + sub_path
        if target:
            try:  # таймаут, чтобы медленный ss.lv не подвешивал меню
                cf = await asyncio.wait_for(p.get_category_filters(target, lang), timeout=12)
            except Exception as e:
                log.warning("get_category_filters timeout/err: %s", e)
                cf = []
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
                kb.button(text=i18n.ui(f["label"], lang), callback_data=f"set:{f['id']}")
        # Селекты — реальные фильтры ss.lv (Консоль, КПП, Кузов, Цвет…).
        for i, f in enumerate(cat_filters):
            kb.button(text=f"🔽 {i18n.filter_label(f['label'], lang)}", callback_data=f"catf:{i}")
        kb.button(text=t(lang, "keyword"), callback_data="set:keyword")
    else:
        for f in fc.get_filters(cat_id, sub_path):
            kb.button(text=i18n.ui(f["label"], lang), callback_data=f"set:{f['id']}")
    # Гео (регион/район/радиус) задаётся один раз в «📍 Моё место» и применяется
    # ко всем фильтрам — в мастере фильтра его больше нет.
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
        f"{_filter_summary(data, lang)}\n"
        f"⏱ {t(lang,'interval_label')}: <b>{_interval_label(interval, lang)}</b>\n\n"
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
    elif action == "diag":   await cmd_diag(msg)


# ─────────────────────────────────────────────
# /lang
# ─────────────────────────────────────────────
async def _show_lang_picker(msg: Message, edit: bool = False):
    kb = InlineKeyboardBuilder()
    for code, label in i18n.LANGS.items():
        kb.button(text=label, callback_data=f"setlang:{code}")
    kb.adjust(1)
    txt = "🌐 Izvēlies valodu / Выбери язык:"
    if edit: await _edit(msg, txt, reply_markup=kb.as_markup())
    else:    await msg.answer(txt, reply_markup=kb.as_markup())


@router.message(Command("lang"))
async def cmd_lang(msg: Message, state: FSMContext):
    await state.clear()
    await _show_lang_picker(msg)
    await state.set_state(SetLang.picking)
    log.info("LANG cmd_lang: picker shown, state=%s", await state.get_state())


# Без привязки к состоянию: кнопки setlang приходят только из языкового меню,
# поэтому меняем язык в ЛЮБОМ состоянии — это исключает «зависшую» кнопку.
@router.callback_query(F.data.startswith("setlang:"))
async def on_lang_pick(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":", 1)[1]
    if lang not in ("ru", "lv"):   # интерфейс только ru/lv
        lang = "ru"
    log.info("LANG on_lang_pick: data=%r -> lang=%s", cb.data, lang)
    await db.set_user_lang(cb.from_user.id, lang)
    user = await db.get_user(cb.from_user.id)
    loc  = t(lang, "loc_not_set")
    if user and user.get("location_name"):
        loc = f"📍 {user['location_name']}"
    # edit_text может упасть («message is not modified» и т.п.) — это не должно
    # оставлять кнопку «висящей»: state.clear() и cb.answer() ниже сработают всегда.
    try:
        await cb.message.edit_text(
            t(lang, "lang_set") + "\n\n" + t(lang, "start", loc=loc),
            parse_mode="HTML",
        )
    except Exception:
        pass
    try:
        await cb.message.answer("⬇️", reply_markup=main_kb(lang))
    except Exception:
        pass
    await state.clear()
    await cb.answer(t(lang, "lang_set").replace("<b>", "").replace("</b>", ""))


# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await db.upsert_user(msg.from_user.id, msg.from_user.username)
    user = await db.get_user(msg.from_user.id)
    lang = (user or {}).get("lang")
    if lang not in ("ru", "lv"):   # легаси en / не выбран → пусть выберет ru/lv
        lang = None

    # Меню команд «/» не используем (есть нижние кнопки). Чистим per-chat
    # команды, если остались от старой версии — иначе меню «двоилось».
    try:
        await msg.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=msg.from_user.id))
    except Exception:
        pass

    if not lang:
        await _show_lang_picker(msg)
        await state.set_state(SetLang.picking)
        return

    loc = f"📍 {user['location_name']}" if user and user.get("location_name") else t(lang, "loc_not_set")

    # Inline-кнопки в самом сообщении (lang здесь уже строго ru/lv)
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ " + {"ru":"Добавить фильтр","lv":"Pievienot filtru"}.get(lang,"Pievienot filtru"),
              callback_data="menu:add")
    kb.button(text="📋 " + {"ru":"Мои фильтры","lv":"Mani filtri"}.get(lang,"Mani filtri"),
              callback_data="menu:list")
    kb.button(text="📊 " + {"ru":"Статистика","lv":"Statistika"}.get(lang,"Statistika"),
              callback_data="menu:stats")
    kb.button(text="📍 " + {"ru":"Местоположение","lv":"Atrašanās vieta"}.get(lang,"Atrašanās vieta"),
              callback_data="menu:location")
    kb.button(text="🌐 LV/RU", callback_data="menu:lang")
    kb.button(text="🩺 " + {"ru":"Диагностика","lv":"Diagnostika"}.get(lang,"Diagnostika"),
              callback_data="menu:diag")
    kb.adjust(1, 2, 2, 1)

    greeting = {
        "ru": "👋 <b>ss.lv Monitor</b>\nМониторю любые объявления на ss.lv.\n\n" + loc,
        "lv": "👋 <b>ss.lv Monitor</b>\nUzraugu jebkādus sludinājumus.\n\n" + loc,
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
async def cmd_stats(msg: Message, uid: int | None = None):
    import time
    uid     = uid or msg.from_user.id
    lang    = await _lang(uid)
    filters = await db.list_filters(uid)
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
        iv    = _interval_label(f.get("check_interval") or 300, lang)
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
        await cmd_add(cb.message, state, uid=cb.from_user.id)
    elif action == "list":
        await cmd_list(cb.message, uid=cb.from_user.id)
    elif action == "stats":
        await cmd_stats(cb.message, uid=cb.from_user.id)
    elif action == "location":
        lang = await _lang(cb.from_user.id)
        await state.clear()
        await state.update_data(_lang=lang)
        await _show_place_menu(cb.message, state, edit=False)
        await state.set_state(SetLocation.waiting)
    elif action == "lang":
        await _show_lang_picker(cb.message, edit=False)
        await state.set_state(SetLang.picking)
        log.info("LANG inline: picker shown, state=%s", await state.get_state())
    elif action == "diag":
        await cmd_diag(cb.message, uid=cb.from_user.id)

# ─────────────────────────────────────────────
# «Моё место» — геолокация ИЛИ город→район (одна гео-настройка на пользователя)
# ─────────────────────────────────────────────
@router.message(Command("location"))
async def cmd_location(msg: Message, state: FSMContext):
    lang = await _lang(msg.from_user.id)
    await state.clear()
    await state.update_data(_lang=lang)
    await _show_place_menu(msg, state, edit=False)
    await state.set_state(SetLocation.waiting)


async def _show_place_menu(msg, state, edit=True):
    lang = (await state.get_data()).get("_lang","ru")
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang,"place_gps"),    callback_data="loc_gps")
    kb.button(text=t(lang,"place_cities"), callback_data="loc_cities")
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    if edit: await _edit(msg, t(lang,"place_title"), reply_markup=kb.as_markup(), parse_mode="HTML")
    else:    await msg.answer(t(lang,"place_title"), reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(SetLocation.waiting, F.data == "loc_back")
async def loc_back(cb: CallbackQuery, state: FSMContext):
    await _show_place_menu(cb.message, state, edit=True)
    await cb.answer()


# ─── Вариант 1: моя геолокация (GPS) → радиус ───────────────────
@router.callback_query(SetLocation.waiting, F.data == "loc_gps")
async def loc_gps(cb: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("_lang","ru")
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang,"city_gps_btn"), request_location=True)],
                  [KeyboardButton(text=t(lang,"cancel"))]],
        resize_keyboard=True, one_time_keyboard=True)
    await cb.message.answer(t(lang,"place_gps_ask"), reply_markup=kb)
    await cb.answer()


@router.message(SetLocation.waiting, F.location)
async def on_gps(msg: Message, state: FSMContext):
    lang = (await state.get_data()).get("_lang","ru")
    lat, lon = msg.location.latitude, msg.location.longitude
    name = geo.nearest_city(lat, lon) or f"{lat:.4f}, {lon:.4f}"
    await state.update_data(gps_lat=lat, gps_lon=lon, gps_name=name)
    km_u = "km" if lang == "lv" else "км"
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang,"any_region"), callback_data="lrad:0")   # без ограничения
    for km in (5, 10, 20, 50, 100):
        kb.button(text=f"{km} {km_u}", callback_data=f"lrad:{km}")
    kb.adjust(3)
    await msg.answer(t(lang,"place_radius_ask", name=name),
                     reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(SetLocation.waiting, F.data.startswith("lrad:"))
async def loc_radius(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data(); lang = data.get("_lang","ru")
    km   = int(cb.data.split(":",1)[1]) or None
    lat, lon, name = data.get("gps_lat"), data.get("gps_lon"), data.get("gps_name","GPS")
    await db.set_user_geo(cb.from_user.id, "gps", lat, lon, name, radius=km)
    await state.clear()
    km_u = "km" if lang == "lv" else "км"
    suffix = f" · ≤{km} {km_u}" if km else ""
    await cb.message.edit_text(t(lang,"location_saved", name=_esc(name) + suffix), parse_mode="HTML")
    await cb.message.answer("⬇️", reply_markup=main_kb(lang))
    await cb.answer("✅")


# ─── Вариант 2: список городов/регионов → район ─────────────────
@router.callback_query(SetLocation.waiting, F.data == "loc_cities")
async def loc_cities(cb: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("_lang","ru")
    await cb.bot.send_chat_action(cb.from_user.id, "typing")
    # Матч в мониторе идёт по полю «Местонахождение» карточки, а оно ВСЕГДА
    # русское → значение региона храним по-русски (names_ru), а на кнопках
    # показываем на языке интерфейса (names_show). Порядок опций одинаков на
    # /ru/ и /lv/ страницах, поэтому зипуем по индексу.
    names_ru, names_show = [], []
    try:
        ru = await asyncio.wait_for(p.get_subcategories("/ru/real-estate/flats/", "ru"), timeout=15)
        names_ru = [r["name"] for r in ru]
        if lang == "ru":
            names_show = list(names_ru)
        else:
            loc = await asyncio.wait_for(p.get_subcategories("/ru/real-estate/flats/", lang), timeout=15)
            show = [r["name"] for r in loc]
            names_show = show if len(show) == len(names_ru) else list(names_ru)
    except Exception as e:
        log.warning("loc regions: %s", e)
    if not names_ru:                              # фолбэк при сбое скрейпа (русские значения)
        names_ru   = [n.title() for n in geo.CITY_RU2LV.keys()]
        names_show = [geo.localize_city(n, lang) for n in names_ru]
    await state.update_data(loc_regions=names_ru, loc_regions_show=names_show)
    kb = InlineKeyboardBuilder()
    _grid(kb, [InlineKeyboardButton(text=s, callback_data=f"lreg:{i}")
               for i, s in enumerate(names_show)], wide=2)
    kb.row(InlineKeyboardButton(text=t(lang,"back"), callback_data="loc_back"))
    await _edit(cb.message, t(lang,"city_page_title"), reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(SetLocation.waiting, F.data.startswith("lreg:"))
async def loc_region_pick(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data(); lang = data.get("_lang","ru")
    regs = data.get("loc_regions", [])                 # русские значения (для матча)
    show = data.get("loc_regions_show", regs)
    try: idx = int(cb.data.split(":",1)[1])
    except ValueError: idx = -1
    if not (0 <= idx < len(regs)):
        await cb.answer(); return
    region      = regs[idx]                             # русское значение
    region_show = show[idx] if idx < len(show) else region
    await state.update_data(loc_region=region, loc_region_show=region_show)
    await cb.bot.send_chat_action(cb.from_user.id, "typing")
    # Районы: русские значения (для матча) + локализованные подписи, зип по индексу.
    dist_ru, dist_show = [], []
    try:
        dist_ru = await asyncio.wait_for(p.get_region_districts(region, "ru"), timeout=15)
        if lang == "ru":
            dist_show = list(dist_ru)
        else:
            d2 = await asyncio.wait_for(p.get_region_districts(region_show, lang), timeout=15)
            dist_show = d2 if len(d2) == len(dist_ru) else list(dist_ru)
    except Exception as e:
        log.warning("loc districts: %s", e)
    await state.update_data(loc_districts=dist_ru, loc_districts_show=dist_show)
    kb = InlineKeyboardBuilder()
    btns = [InlineKeyboardButton(text=t(lang,"any_district"), callback_data="ldist:_all_")]
    btns += [InlineKeyboardButton(text=s, callback_data=f"ldist:{i}") for i, s in enumerate(dist_show)]
    _grid(kb, btns, wide=2)
    kb.row(InlineKeyboardButton(text=t(lang,"back"), callback_data="loc_cities"))
    await _edit(cb.message, t(lang,"district_title", region=_esc(region_show)),
                reply_markup=kb.as_markup(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(SetLocation.waiting, F.data.startswith("ldist:"))
async def loc_district_pick(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data(); lang = data.get("_lang","ru")
    region      = data.get("loc_region", "")           # русское значение
    region_show = data.get("loc_region_show", region)
    key = cb.data.split(":",1)[1]
    district = district_show = None
    if key != "_all_":
        dl  = data.get("loc_districts", [])             # русские значения
        dls = data.get("loc_districts_show", dl)
        try: idx = int(key)
        except ValueError: idx = -1
        if 0 <= idx < len(dl):
            district      = dl[idx]
            district_show = dls[idx] if idx < len(dls) else dl[idx]
    name = region_show + (f", {district_show}" if district_show else "")   # для показа
    # Точка отсчёта для расстояния: геокодим район/город по РУССКОМУ имени
    # (один запрос), фолбэк — координаты города из таблицы.
    lat = lon = None
    try:
        g = await asyncio.wait_for(geo.geocode_nominatim(f"{district}, {region}" if district else region),
                                   timeout=12)
        if g: lat, lon = g[0], g[1]
    except Exception:
        pass
    if lat is None:
        c = geo.city_coords(region) or geo.city_coords(region.split()[0] if region else "")
        if c: lat, lon = c
    # region/district храним ПО-РУССКИ — поле «Местонахождение» карточки русское.
    await db.set_user_geo(cb.from_user.id, "area", lat, lon, name, region=region, district=district)
    await state.clear()
    await cb.message.edit_text(t(lang,"location_saved", name=_esc(name)), parse_mode="HTML")
    await cb.message.answer("⬇️", reply_markup=main_kb(lang))
    await cb.answer("✅")


@router.message(SetLocation.waiting, F.text)
async def loc_cancel_text(msg: Message, state: FSMContext):
    # Текст в состоянии выбора места — это «❌ Отмена» с GPS-клавиатуры.
    lang = (await state.get_data()).get("_lang","ru")
    await state.clear()
    await msg.answer(t(lang,"cancelled"), reply_markup=main_kb(lang))


# ─────────────────────────────────────────────
# /add → категории
# ─────────────────────────────────────────────
@router.message(Command("add"))
async def cmd_add(msg: Message, state: FSMContext, uid: int | None = None):
    # uid передаётся, когда команда вызвана из inline-кнопки (там msg.from_user —
    # это бот, а не пользователь). По умолчанию берём отправителя сообщения.
    uid  = uid or msg.from_user.id
    lang = await _lang(uid)
    cnt  = await db.count_filters(uid)
    if cnt >= config.MAX_FILTERS_PER_USER:
        await msg.answer(t(lang,"max_filters",max=config.MAX_FILTERS_PER_USER))
        return
    await state.clear()
    await state.update_data(_lang=lang)
    kb = InlineKeyboardBuilder()
    _grid(kb, [InlineKeyboardButton(text=c["label"], callback_data=f"topcat:{c['id']}")
               for c in await _top_cats(lang)], wide=2)
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await msg.answer(t(lang,"what_monitor"), reply_markup=kb.as_markup())
    await state.set_state(AddFilter.top_cat)


@router.callback_query(AddFilter.top_cat, F.data.startswith("topcat:"))
async def on_top_cat(cb: CallbackQuery, state: FSMContext):
    cat_id = cb.data.split(":",1)[1]
    data   = await state.get_data()
    lang   = data.get("_lang","ru")
    cat    = next((c for c in await _top_cats(lang) if c["id"]==cat_id), None)
    if not cat: return
    cat_l  = cat["label"]
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
    # имена приходят уже на языке пользователя (ss.lv отдаёт нативно).
    # Таймаут, чтобы медленный ss.lv не подвешивал добавление фильтра.
    try:
        subs = await asyncio.wait_for(cache.subcats(cat["path"], p, lang), timeout=20)
    except Exception as e:
        log.warning("subcats timeout %s: %s", cat["path"], e)
        subs = []
    if not subs:
        raw  = cat_mod.FALLBACK_SUBS.get(cat_id, [])
        subs = [{"name": i18n.translate_subcat(n,lang),
                 "slug": u.rstrip("/").rsplit("/",1)[-1], "url": u}
                for n, u in raw]
    else:
        for s in subs:
            if "url" not in s: s["url"] = cat["path"] + s["slug"] + "/"

    # «Редкие авто» (ретро/спорт/тюнинг/эксклюзив/электро) — спец-разделы
    # легковых, которых нет в одноуровневой навигации /ru/transport/.
    if cat_id == "transport":
        have = {s.get("url") for s in subs}
        for names, url in cat_mod.CARS_SPECIAL:
            if url not in have:
                subs.append({"name": names.get(lang, names["ru"]),
                             "slug": url.rstrip("/").rsplit("/", 1)[-1],
                             "url": url})
    await state.update_data(subs=subs, nav_stack=[], nav_label=None, here_url=None)
    await _show_subs(cb.message, state, 0)
    await state.set_state(AddFilter.sub_cat)
    await cb.answer()


async def _show_subs(msg, state, page=0):
    data  = await state.get_data()
    subs  = data.get("subs",[])
    label = data.get("nav_label") or data.get("cat_label","")
    lang  = data.get("_lang","ru")
    # Колонки и размер страницы — под длину названий: длинные (как латышские
    # «Brilles, siksnas…») по 1 в ряд на всю ширину (не обрезаются), короткие
    # (как «Собаки», «Кошки») по 2. Меню всегда помещается на экран.
    m    = max((len(s.get("name","")) for s in subs), default=0)
    cols = 1 if m > 24 else 2
    per  = 5 if cols == 1 else 8
    total = max(1,(len(subs)-1)//per+1)
    page  = max(0, min(page, total-1))
    chunk = subs[page*per:(page+1)*per]
    kb = InlineKeyboardBuilder()
    # Если мы внутри раздела (углубились) — даём мониторить его ЦЕЛИКОМ или искать
    # по слову («весь Samsung», как «любая модель» у авто). Одной строкой.
    here = data.get("here_url")
    if here and here.startswith("/"):
        kb.row(InlineKeyboardButton(text=t(lang,"monitor_all"), callback_data="subhere"),
               InlineKeyboardButton(text=t(lang,"keyword"),     callback_data="kwhere"))
    sub_btns = [InlineKeyboardButton(text=s.get("name",""), callback_data=f"sub:{page*per+i}")
                for i, s in enumerate(chunk)]
    for j in range(0, len(sub_btns), cols):
        kb.row(*sub_btns[j:j+cols])
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"subp:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"subp:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_top"),
           InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
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
                                nav_label=prev["label"], here_url=prev.get("url"))
        await _show_subs(cb.message, state, 0)
        await cb.answer(); return

    kb   = InlineKeyboardBuilder()
    _grid(kb, [InlineKeyboardButton(text=c["label"], callback_data=f"topcat:{c['id']}")
               for c in await _top_cats(lang)], wide=2)
    kb.row(InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
    await _edit(cb.message, t(lang,"what_monitor"), reply_markup=kb.as_markup())
    await state.set_state(AddFilter.top_cat)
    await cb.answer()


@router.callback_query(AddFilter.sub_cat, F.data == "subhere")
async def on_sub_here(cb: CallbackQuery, state: FSMContext):
    """«Мониторить весь раздел» — текущий раздел (here_url) как лист, без выбора
    конкретного подпункта. Например «весь Samsung»."""
    data = await state.get_data()
    here = data.get("here_url")
    if not here:
        await cb.answer(); return
    crumb = data.get("nav_label") or ""
    name  = crumb.split("›")[-1].strip() if crumb else here.rstrip("/").rsplit("/", 1)[-1]
    await state.update_data(sub_path=here, sub_label=name,
                            cat_filters=None, cols_sel={}, adopts_sel={})
    await _show_filter_menu(cb.message, state)
    await cb.answer()


@router.callback_query(AddFilter.sub_cat, F.data == "kwhere")
async def on_kw_here(cb: CallbackQuery, state: FSMContext):
    """«Искать по слову» прямо из раздела: текущий раздел + ввод ключевого слова."""
    data = await state.get_data()
    lang = data.get("_lang","ru")
    here = data.get("here_url")
    if not here:
        await cb.answer(); return
    crumb = data.get("nav_label") or ""
    name  = crumb.split("›")[-1].strip() if crumb else here.rstrip("/").rsplit("/", 1)[-1]
    await state.update_data(sub_path=here, sub_label=name,
                            cat_filters=None, cols_sel={}, adopts_sel={})
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang,"back"), callback_data="back_to_filters")
    await _edit(cb.message, t(lang,"keyword_hint"), reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(AddFilter.inp_keyword)
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
        try:
            dynamic = await asyncio.wait_for(p.get_subcategories(base_url, lang), timeout=20)
        except Exception:
            dynamic = []
        districts = [(d["name"],d["slug"]) for d in dynamic] if dynamic else list(cat_mod.RIGA_DISTRICTS)
        await state.update_data(riga_type=riga_type, riga_districts=districts, sub_path=base_url)
        await _show_riga_districts(cb.message, state, 0)
        await state.set_state(AddFilter.riga_district)
    elif sub_url in cat_mod.TRANSPORT_FULL:
        t_cat = cat_mod.TRANSPORT_FULL[sub_url]
        await cb.message.edit_text(f"<b>{sub['name']}</b>\n{t(lang,'loading_brands')}", parse_mode="HTML")
        await cb.bot.send_chat_action(cb.from_user.id, "typing")
        try:
            brands_list = await asyncio.wait_for(p.get_brands(t_cat, lang), timeout=20)
        except Exception as e:
            log.warning("get_brands timeout: %s", e); brands_list = []
        await state.update_data(transport_cat=t_cat, brands=brands_list)
        await _show_brands(cb.message, state, 0)
        await state.set_state(AddFilter.brand)
    else:
        # Универсальный рекурсивный drill по дереву ss.lv:
        # есть вложенные подкатегории → показываем их; нет → это лист
        # (сами объявления) → переходим к меню фильтров.
        await cb.message.edit_text(f"<b>{sub['name']}</b>\n⏳…", parse_mode="HTML")
        await cb.bot.send_chat_action(cb.from_user.id, "typing")
        children = []
        if sub_url.startswith("/"):
            try:
                children = await asyncio.wait_for(p.get_subcategories(sub_url, lang), timeout=20)
            except Exception as e:
                log.warning("drill timeout %s: %s", sub_url, e)
        if children:
            stack = data.get("nav_stack", [])
            stack.append({"subs": subs, "label": data.get("nav_label") or data.get("cat_label",""),
                          "url": data.get("here_url")})
            # имена детей уже на языке пользователя (ss.lv отдаёт нативно)
            crumb = (data.get("nav_label") or data.get("cat_label","")) + " › " + sub["name"]
            # here_url = текущий раздел (его можно мониторить целиком — «весь Samsung»)
            await state.update_data(nav_stack=stack, subs=children, nav_label=crumb,
                                    here_url=sub_url)
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
    _rtitle = {"flats": {"ru":"🏘 Квартиры","lv":"🏘 Dzīvokļi","en":"🏘 Apartments"},
               "houses":{"ru":"🏠 Дома","lv":"🏠 Mājas","en":"🏠 Houses"}}
    title = _rtitle.get(rtype, _rtitle["flats"]).get(lang, _rtitle.get(rtype, _rtitle["flats"])["ru"])
    total = max(1,(len(dist)-1)//RIGA_PAGE+1)
    chunk = dist[page*RIGA_PAGE:(page+1)*RIGA_PAGE]
    kb    = InlineKeyboardBuilder()
    _grid(kb, [InlineKeyboardButton(text=name, callback_data=f"rig:{slug}:{name}")
               for name, slug in chunk], wide=2)
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
    if slug == "_all_":   # «Вся Рига» — подпись на языке пользователя
        name = t(data.get("_lang","ru"), "all_riga")
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
    _grid(kb, [InlineKeyboardButton(text=item["name"],
                                    callback_data=f"br:{item['slug']}:{item['name']}")
               for item in chunk], wide=3)
    nav = []
    if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"brp:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"brp:{page+1}"))
    if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"input_manual"), callback_data="br:_manual_:"))
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_sub_from_brand"),
           InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
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
        models = await cache.models(slug, data.get("transport_cat","cars"), p, lang)
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
    kb.row(InlineKeyboardButton(text=t(lang,"any_model"), callback_data="md:_any_:Любая"))
    if models:
        total = max(1,(len(models)-1)//PAGE+1)
        chunk = models[page*PAGE:(page+1)*PAGE]
        _grid(kb, [InlineKeyboardButton(text=m["name"],
                                        callback_data=f"md:{m['slug']}:{m['name'][:20]}")
                   for m in chunk], wide=3)
        nav = []
        if page > 0:   nav.append(InlineKeyboardButton(text="◀", callback_data=f"mdp:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
        if page < total-1: nav.append(InlineKeyboardButton(text="▶", callback_data=f"mdp:{page+1}"))
        if nav: kb.row(*nav)
    kb.row(InlineKeyboardButton(text=t(lang,"input_manual"), callback_data="md:_manual_:"))
    kb.row(InlineKeyboardButton(text=t(lang,"back"),   callback_data="back_brands"),
           InlineKeyboardButton(text=t(lang,"cancel"), callback_data="cancel"))
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
            models = await cache.models(slug, data.get("transport_cat","cars"), p, lang)
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
            emoji = label.split(" ", 1)[0]
            kb.button(text=f"{emoji} {_interval_label(sec, lang)}", callback_data=f"iv:{sec}")
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
            kb2.button(text=i18n.ui(label, lang), callback_data=f"pick:{which}:{val}")
        kb2.adjust(2)
        kb2.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data=f"clear:{which}"),
                InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
        await cb.message.edit_text(f"<b>{i18n.ui(title, lang)}</b>:",
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
        await cb.message.edit_text(f"<b>{i18n.ui(title, lang)}</b>:",
                                   reply_markup=kb2.as_markup(), parse_mode="HTML")
        # отдельное состояние, чтобы ручной ввод не попал в цену
        await state.update_data(_rk=key)
        await state.set_state(AddFilter.inp_range)
        await cb.answer(); return

    if which == "gearbox":
        kb = InlineKeyboardBuilder()
        for label, val in br.GEARBOX_OPTIONS:
            kb.button(text=i18n.ui(label, lang), callback_data=f"pick:gearbox:{val}")
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
            kb.button(text=i18n.ui(label, lang), callback_data=f"pick:bodytype:{val}")
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
    disp = f.get("options_disp") or f["options"]
    for j, opt in enumerate(disp):
        kb.button(text=opt, callback_data=f"catpick:{i}:{j}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=t(lang,"clear"), callback_data=f"catclear:{i}"),
           InlineKeyboardButton(text=t(lang,"back"),  callback_data="back_to_filters"))
    await cb.message.edit_text(f"<b>{i18n.filter_label(f['label'], lang)}</b>:",
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
    sec  = int(cb.data.split(":",1)[1])
    lang = (await state.get_data()).get("_lang","ru")
    await state.update_data(check_interval=sec)
    await _show_filter_menu(cb.message, state)
    await cb.answer(f"✅ {_interval_label(sec, lang)}")


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
    # Гео (регион/район/радиус) теперь общее в «Моё место» (на пользователе),
    # применяется в мониторе ко всем фильтрам — в params фильтра его не храним.
    url = base  # чистый URL марки/модели/сделки без неработающих GET-параметров

    combined_kw = data.get("keyword") or None

    summary: dict = {}
    # Саммари сохраняется в БД и показывается в /list — локализуем предлоги/единицы.
    _from = "no"   if lang == "lv" else "от"
    _to   = "līdz" if lang == "lv" else "до"
    _km   = " km"  if lang == "lv" else " км"
    def rng(a,b,u=""):
        if a and b: return f"{a}–{b}{u}"
        if a: return f"{_from} {a}{u}"
        if b: return f"{_to} {b}{u}"
        return None
    for key,kmin,kmax,unit in [
        ("price","price_min","price_max"," €"),
        ("year","year_min","year_max",""),
        ("mileage","mile_min","mile_max",_km),
    ]:
        r = rng(data.get(kmin),data.get(kmax),unit)
        if r: summary[key] = r
    if data.get("keyword"):  summary["keyword"]  = data["keyword"]
    for label, val in {**cols_sel, **adopts_sel}.items():
        summary[label] = val

    await cb.message.edit_text(t(lang,"saving"))
    await cb.bot.send_chat_action(cb.from_user.id, "typing")

    # ── Проверяем целевой URL и определяем самую свежую выдачу ────────────────
    # Голый раздел-ХАБ (меню подразделов) мониторить бессмысленно. Раздел с
    # выдачей через период (вакансии и т.п.) мониторим через его свежую выдачу.
    # Фильтр периода (сегодня/2дн/5дн) есть в КАЖДОМ разделе ss.lv.
    probe_ads = None
    try:
        probe_ads = await asyncio.wait_for(p.fetch_listings(url), timeout=15.0)
    except Exception as e:
        log.warning(f"save probe: {e}")
    period_key, period_url = None, None
    try:
        period_key, _pn, period_url = await asyncio.wait_for(p.get_recent(url), timeout=15.0)
    except Exception as e:
        log.warning(f"get_recent: {e}")
    if probe_ads is not None and len(probe_ads) == 0:
        if period_url:                         # раздел-агрегатор → мониторим выдачу
            url = period_url
            try:    probe_ads = await asyncio.wait_for(p.fetch_listings(url), timeout=15.0)
            except Exception: probe_ads = []
        elif not combined_kw:                  # ни листинга, ни периодов
            kids = []
            try: kids = await asyncio.wait_for(p.get_subcategories(sub_path, lang), timeout=10.0)
            except Exception: pass
            if kids:                           # это меню-хаб → просим углубиться
                kbw = InlineKeyboardBuilder()
                kbw.button(text=t(lang,"open_sslv"), url=url)
                kbw.button(text=t(lang,"back"),      callback_data="back_to_filters")
                await cb.message.edit_text(t(lang,"save_hub_warning"),
                                           reply_markup=kbw.as_markup(), disable_web_page_preview=True)
                await cb.answer(); return
            # иначе тихий лист (0 объявлений сейчас, но подразделов нет) — сохраняем

    fid = await db.add_filter(
        user_id=cb.from_user.id, category=data.get("cat_id","other"),
        category_path=sub_path, brand=brand, brand_slug=bslug,
        model=model, model_slug=mslug,
        params=params, params_summary=summary,
        keyword=combined_kw, url=url,
        check_interval=data.get("check_interval", cat_mod.DEFAULT_INTERVAL),
    )

    # Снимок текущей выдачи → помечаем «виденным» (переиспользуем probe_ads).
    seen_n = 0
    try:
        ads = p.apply_filters(p.apply_keyword(list(probe_ads or []), combined_kw), params)
        await db.mark_seen(fid, [a["id"] for a in ads])
        seen_n = len(ads)
    except Exception as e:
        log.warning(f"snapshot: {e}")

    # Счёт раздела за период — БЫСТРО, без открытия карточек (иначе каждое
    # сохранение тормозит на десятках сетевых запросов). Точную фильтрацию по
    # «Моё место» применяем при ПОКАЗЕ (кнопка) и в УВЕДОМЛЕНИЯХ — там монитор и
    # так открывает карточку каждого нового объявления, гео там бесплатно.
    fresh_n = 0
    geo_active = False
    if period_url:
        try:
            tads = await asyncio.wait_for(p.fetch_listings(period_url), timeout=15.0)
            tads = p.apply_filters(p.apply_keyword(tads, combined_kw), params)
            fresh_n = len(tads)
            geo_user = await db.get_user(cb.from_user.id)
            geo_active = bool(geo_user and geo_user.get("geo_mode"))
        except Exception as e:
            log.warning(f"recent count: {e}")

    specs_block = ""
    if brand and model and sub_path in cat_mod.TRANSPORT_FULL:
        year = data.get("year_min") or data.get("year_max")
        specs_block = cs.lookup_info_block(brand, model, year)

    cat_l = data.get("cat_label","")
    sub_l = data.get("sub_label","")
    iv    = data.get("check_interval", cat_mod.DEFAULT_INTERVAL)

    today_str = datetime.now().strftime("%d.%m.%Y")
    period_phrase = t(lang, {"today-2": "period_2", "today-5": "period_5"}.get(period_key, "period_today"))
    text = (
        t(lang,"saved",fid=fid,period=period_phrase,n=fresh_n,date=today_str,url=url)
        + (f"\n{t(lang,'geo_note')}" if geo_active else "")   # гео применится при показе/уведомлениях
        + f"\n\n{_esc(cat_l)}" + (f" › {_esc(sub_l)}" if sub_l else "")
        + (f"\n<b>{_esc(brand)}</b>" if brand else "")
        + (f" {_esc(model)}" if model else "")
        + f"\n{_filter_summary(data, lang)}"
        + f"\n⏱ {_interval_label(iv, lang)}"
        + specs_block
    )

    # Если есть свежие объявления — предлагаем показать (иначе юзер их пропустит:
    # они помечены «виденными» и в уведомления не пойдут).
    kb = None
    if fresh_n > 0 and period_url:
        kb = InlineKeyboardBuilder()
        kb.button(text=t(lang,"yes"), callback_data=f"showtoday:{fid}")
        kb.button(text=t(lang,"no"),  callback_data="hidetoday")
        text += f"\n\n{t(lang,'show_today_q')}"

    markup = kb.as_markup() if kb else None
    try:
        await cb.message.edit_text(text, parse_mode="HTML", disable_web_page_preview=True,
                                   reply_markup=markup)
    except Exception:   # сообщение могло устареть/не отредактироваться — шлём новым
        try:
            await cb.message.answer(text, parse_mode="HTML", disable_web_page_preview=True,
                                    reply_markup=markup)
        except Exception as e:
            log.warning(f"save final msg: {e}")
    await state.clear()
    await cb.answer()


@router.callback_query(F.data == "hidetoday")
async def on_hide_today(cb: CallbackQuery):
    # Убираем кнопки, оставляем текст карточки сохранения как есть.
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.answer()


@router.callback_query(F.data.startswith("showtoday:"))
async def on_show_today(cb: CallbackQuery):
    await cb.answer()
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    fid  = int(cb.data.split(":", 1)[1])
    lang = await _lang(cb.from_user.id)
    uid  = cb.from_user.id
    f    = await db.get_filter(fid, uid)
    if not f:
        log.warning("show_today: filter #%s not found for user %s", fid, uid)
        await cb.bot.send_message(uid, t(lang, "today_empty"))
        return

    await cb.bot.send_chat_action(uid, "typing")

    # Самая свежая выдача (сегодня → 2 дня → 5 дней) + клиентские фильтры.
    # Несколько попыток: ss.lv иногда отдаёт пустую/сбойную страницу, хотя при
    # сохранении объявления были — не хотим из-за этого писать «нет».
    ads, err, period_url = [], False, None
    for attempt in range(3):
        try:
            _pk, _pn, period_url = await asyncio.wait_for(p.get_recent(f["url"]), timeout=20.0)
            log.info("show_today #%s try%d: period_url=%s", fid, attempt, period_url)
            if period_url:
                ads = await asyncio.wait_for(p.fetch_listings(period_url), timeout=20.0)
                ads = p.apply_keyword(ads, f.get("keyword"))
                ads = p.apply_filters(ads, f.get("params"))
            err = False
        except Exception as e:
            err = True
            log.warning("show_today fetch #%s try%d: %s", fid, attempt, e)
        if ads or not err:
            break
        await asyncio.sleep(1.0)

    log.info("show_today #%s: %d объявлений к показу (err=%s)", fid, len(ads), err)
    if not ads:
        # Прямая ссылка на свежую выдачу ss.lv как запасной вариант.
        link = period_url or f["url"]
        kbl = InlineKeyboardBuilder()
        kbl.button(text=t(lang, "open_sslv"), url=link)
        await cb.bot.send_message(uid, t(lang, "today_retry" if err else "today_empty"),
                                  reply_markup=kbl.as_markup())
        return

    # Эти объявления считаем «виденными» — повторно в уведомления не уйдут.
    await db.mark_seen(fid, [a["id"] for a in ads])
    geo_user = await db.get_user(uid)            # общее гео «Моё место»
    geo_active = bool(geo_user and geo_user.get("geo_mode"))

    # Отбор показа. С активным гео надо открыть карточки и отфильтровать —
    # делаем ПАРАЛЛЕЛЬНО (карточки кэшируются, многие уже открыты счётчиком).
    # Без гео карточки для фильтра не нужны → показываем первые как есть (быстро).
    if geo_active:
        scan = ads[:30]                          # ограничиваем скан — показ остаётся шустрым
        sem = asyncio.Semaphore(8)
        async def _hydrate(ad):
            async with sem:
                try:
                    det = await asyncio.wait_for(p.fetch_ad_details(ad["url"]), timeout=8.0)
                    if det.get("archived"):
                        ad["_skip"] = True; return
                    if det.get("city"):     ad["city"]     = det["city"]
                    if det.get("date_fmt"): ad["date_fmt"] = det["date_fmt"]
                    ad["opts"] = det.get("opts", {})
                except Exception:
                    pass
        await asyncio.gather(*(_hydrate(a) for a in scan))
        picked = []
        for ad in scan:
            if ad.get("_skip"):
                continue
            try:
                if await monitor.geo_ok(ad, geo_user):
                    picked.append(ad)
            except Exception:
                picked.append(ad)
    else:
        picked = ads

    matched = len(picked)
    sent = 0
    for ad in picked[:15]:
        if not geo_active:                       # детали для показа (город/дата); кэш дешёвый
            try:
                det = await asyncio.wait_for(p.fetch_ad_details(ad["url"]), timeout=8.0)
                if det.get("city"):     ad["city"]     = det["city"]
                if det.get("date_fmt"): ad["date_fmt"] = det["date_fmt"]
                ad["opts"] = det.get("opts", {})
            except Exception:
                pass
        try:
            txt = await monitor._build_msg(f, ad, lang)
        except Exception as e:
            log.warning("show_today build #%s: %s", fid, e)
            txt = (f"🆕 {_esc(ad.get('title',''))}\n{_esc(ad.get('details',''))}\n"
                   f"{_esc(ad.get('price',''))}\n{_esc(ad.get('url',''))}")
        try:
            if ad.get("photo"):
                try:
                    await cb.bot.send_photo(uid, ad["photo"], caption=txt, parse_mode="HTML")
                except Exception:        # битый URL фото у ss.lv → шлём текстом
                    await cb.bot.send_message(uid, txt, parse_mode="HTML",
                                              disable_web_page_preview=False)
            else:
                await cb.bot.send_message(uid, txt, parse_mode="HTML",
                                          disable_web_page_preview=False)
            sent += 1
            await asyncio.sleep(0.2)
        except Exception as e:
            log.warning("show_today send #%s: %s", fid, e)
    if matched > sent:                           # показали не все подходящие — подсказка
        try: await cb.bot.send_message(uid, t(lang, "more_listings", n=matched - sent))
        except Exception: pass
    await cb.bot.send_message(uid, t(lang, "today_done") if sent else t(lang, "today_empty"))


# ─────────────────────────────────────────────
# /list
# ─────────────────────────────────────────────
@router.message(Command("list"))
async def cmd_list(msg: Message, uid: int | None = None):
    uid     = uid or msg.from_user.id
    lang    = await _lang(uid)
    filters = await db.list_filters(uid)
    if not filters:
        await msg.answer(t(lang,"no_filters"))
        return
    for f in filters:
        s     = f.get("params_summary") or {}
        brand = f.get("brand") or ""
        model = f.get("model") or ""
        cat   = i18n.cat_label(f.get("category",""), lang)
        iv    = _interval_label(f.get("check_interval") or 300, lang)
        sent  = f.get("total_sent") or 0
        lines = [f"<b>#{f['id']}</b> {_esc(cat)}"]
        if brand: lines.append(f"  🚗 {_esc(brand)}{f' {_esc(model)}' if model else ''}")
        for k,icon in [("price","💶"),("year","📅"),("mileage","🛣"),
                       ("gearbox","⚙️"),("bodytype","🚙"),("keyword","🔎")]:
            if s.get(k): lines.append(f"  {icon} {_esc(str(s[k]))}")
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
# /diag — самодиагностика прямо в Telegram + безопасное само-лечение
# ─────────────────────────────────────────────
# Эталонные «живые» точки: транспорт-лист, вакансии-агрегатор, недвижимость-лист.
_DIAG_TARGETS = [
    ("🚗", "https://www.ss.lv/ru/transport/cars/audi/sell/"),
    ("💼", "https://www.ss.lv/ru/work/are-required/today/"),
    ("🏠", "https://www.ss.lv/ru/real-estate/flats/jurmala/"),
]


@router.message(Command("diag"))
async def cmd_diag(msg: Message, uid: int | None = None):
    # uid передаётся, когда вызвано из inline-кнопки (msg.from_user там — бот).
    uid  = uid or msg.from_user.id
    lang = await _lang(uid)
    m    = await msg.answer(t(lang, "diag_running"))
    lines = [t(lang, "diag_title"), ""]

    async def _check(icon, url):
        try:
            ads = await asyncio.wait_for(p.fetch_listings(url), timeout=15.0)
            n, turl = await asyncio.wait_for(p.get_today(url), timeout=15.0)
            ok = "✅" if ads else "⚠️"
            return t(lang, "diag_line", ok=ok, icon=icon, ads=len(ads),
                     today=n, chk=" /today✓" if turl else "")
        except Exception as e:
            return f"❌ {icon} {type(e).__name__}"

    try:
        res = await asyncio.gather(*[_check(i, u) for i, u in _DIAG_TARGETS])
        lines += list(res)
    except Exception as e:
        log.warning("diag checks: %s", e)
    lines.append("")

    # Тест доставки сообщений: отправить и сразу удалить.
    try:
        ping = await msg.bot.send_message(uid, "·")
        try: await msg.bot.delete_message(uid, ping.message_id)
        except Exception: pass
        lines.append(t(lang, "diag_send_ok"))
    except Exception:
        lines.append(t(lang, "diag_send_fail"))

    # Фильтры пользователя + детект «застрявших» (0 объявлений, не по слову).
    try:
        filters = await db.list_filters(uid)
        lines.append(t(lang, "diag_filters", n=len(filters)))
        stuck = []
        for f in filters[:10]:
            if f.get("keyword"):
                continue
            try:
                a = await asyncio.wait_for(p.fetch_listings(f["url"]), timeout=10.0)
                if not a:
                    stuck.append(f["id"])
            except Exception:
                pass
        if stuck:
            lines.append(t(lang, "diag_stuck", ids=", ".join("#" + str(x) for x in stuck)))
    except Exception as e:
        log.warning("diag db: %s", e)

    lines.append("💾 " + cache.stats())
    kb = InlineKeyboardBuilder()
    kb.button(text=t(lang, "diag_fix_btn"), callback_data="diagfix")
    await _edit(m, "\n".join(lines), reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "diagfix")
async def on_diag_fix(cb: CallbackQuery, state: FSMContext):
    # Безопасное само-лечение (код НЕ правим — это делает деплой):
    #  1) сброс кэшей ss.lv;  2) форс-перепроверка фильтров;  3) снятие
    #  «зависшего» состояния мастера добавления (главная причина «бот виснет»);
    #  4) переустановка меню «/» и кнопок — если они слетели.
    lang = await _lang(cb.from_user.id)
    await cb.answer()
    total = 0
    try:    total += sum(p.clear_caches().values())
    except Exception as e: log.warning("diagfix parser caches: %s", e)
    try:    total += cache.clear()
    except Exception as e: log.warning("diagfix cache: %s", e)
    try:    await db.reset_user_checks(cb.from_user.id)
    except Exception as e: log.warning("diagfix reset checks: %s", e)
    try:    await state.clear()          # снять зависший мастер добавления
    except Exception as e: log.warning("diagfix state: %s", e)
    try:                                  # убрать дублирующее меню команд «/»
        await cb.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=cb.from_user.id))
    except Exception as e: log.warning("diagfix cmds: %s", e)
    await cb.message.answer(t(lang, "diag_fixed", n=total))
    try:                                  # вернуть постоянные кнопки внизу
        await cb.bot.send_message(cb.from_user.id, "⬇️", reply_markup=main_kb(lang))
    except Exception as e: log.warning("diagfix kb: %s", e)


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
async def on_stale_callback(cb: CallbackQuery, state: FSMContext):
    log.warning("STALE callback: data=%r state=%s", cb.data, await state.get_state())
    try:
        await cb.answer("⏳ Кнопка устарела — открой меню заново: /add", show_alert=False)
    except Exception:
        pass
