"""
ss.lv parser.

Функции:
- get_brands(category)    -> [{name, slug}]
- get_models(brand, cat)  -> [{name, slug}]
- get_filters(category)   -> список полей детальной формы
- fetch_listings(url)     -> [Ad]
- build_listing_url(...)  -> str
- build_url_with_params(base, params) -> str
- parse_date_str(s)       -> «Сегодня в 14:23» | «25.05.2026 14:23»

Ad = {id, url, title, price, date_raw, date_fmt, city, details}
"""
import asyncio
import datetime
import logging
import re
from typing import Optional
from urllib.parse import urlencode, urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag

import config

log = logging.getLogger("parser")

BASE = "https://www.ss.lv"
LANG = config.SS_LANG

CATEGORIES = {
    "cars":        f"/{LANG}/transport/cars/",
    "motorcycles": f"/{LANG}/transport/motorcycles/",
}

NON_CATEGORY = {
    "today", "yesterday", "this-week", "filter", "sell", "buy", "rent",
    "service", "all", "msg", "hand", "search", "wanted", "exchange",
    "give", "lost", "found", "barter",
    # служебные ссылки ss.lv, которые не являются марками/категориями
    "rss", "new", "login", "favorites", "reklama", "api", "feedback",
    "rules", "help", "en", "lv", "ru",
    # «Другие»/«Обмен» — не модели, а catch-all и тип сделки
    "another", "change", "-other",
    # переключатели вида/режима из <select>
    "photo", "list",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": f"{LANG},ru;q=0.9,lv;q=0.8,en;q=0.7",
}

_brand_cache: dict[str, list[dict]] = {}
_model_cache: dict[str, list[dict]] = {}
_filter_cache: dict[str, list[dict]] = {}
_subcat_cache: dict[str, list[dict]] = {}
_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
async def _fetch(url: str) -> str:
    async with aiohttp.ClientSession(
        headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)
    ) as s:
        async with s.get(url) as r:
            r.raise_for_status()
            return await r.text()


# ---------------------------------------------------------------------------
# Brand / Model scraping
# ---------------------------------------------------------------------------
def _extract_subcats(html: str, base_path: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(rf"^{re.escape(base_path)}([^/]+)/$")
    found: dict[str, str] = {}

    def _add(slug: str, name: str):
        # служебные ссылки (sell/buy/today-2/photo…) — не подкатегории
        if not slug or slug in NON_CATEGORY or re.match(r"^today-?\d*$", slug):
            return
        if not name or len(name) > 60:
            return
        clean = re.sub(r"\s*\(\d+\)\s*$", "", name).strip()
        if not clean:
            return
        if slug not in found or len(clean) < len(found[slug]):
            found[slug] = clean

    # 1) обычные ссылки <a href>
    for a in soup.find_all("a", href=True):
        m = pat.match(a["href"])
        if m:
            _add(m.group(1), a.get_text(strip=True))
    # 2) опции <select> — на страницах марок полный список моделей лежит
    #    в выпадающем списке «Модель» (value = путь), а не в ссылках.
    #    Пропускаем select name="sid" — там типы сделки (Продажа/Ремонт…).
    for sel in soup.find_all("select"):
        if (sel.get("name") or "") == "sid":
            continue
        for o in sel.find_all("option"):
            m = pat.match((o.get("value") or "").strip())
            if m:
                _add(m.group(1), o.get_text(" ", strip=True))

    items = [{"name": n, "slug": s} for s, n in found.items()]
    items.sort(key=lambda x: x["name"].lower())
    return items


async def get_brands(category: str = "cars") -> list[dict]:
    async with _lock:
        if category in _brand_cache:
            return _brand_cache[category]
    html = await _fetch(urljoin(BASE, CATEGORIES[category]))
    brands = _extract_subcats(html, CATEGORIES[category])
    async with _lock:
        _brand_cache[category] = brands
    log.info(f"brands({category}): {len(brands)}")
    return brands


async def get_models(brand_slug: str, category: str = "cars") -> list[dict]:
    key = f"{category}:{brand_slug}"
    async with _lock:
        if key in _model_cache:
            return _model_cache[key]
    base_path = f"{CATEGORIES[category]}{brand_slug}/"
    try:
        html = await _fetch(urljoin(BASE, base_path))
        models = _extract_subcats(html, base_path)
    except Exception as e:
        log.warning(f"get_models {brand_slug}: {e}")
        models = []
    async with _lock:
        _model_cache[key] = models
    return models


def _extract_a_category(html: str, path: str) -> list[dict]:
    """Достаёт подкатегории из ссылок `a.a_category` — единый формат меню ss.lv
    на любом уровне (категория → подкатегория → марка → модель).

    Берём только ссылки ВНУТРИ текущего пути (href начинается с path), чтобы
    не уехать в чужой раздел по кросс-ссылкам внизу страницы.
    """
    soup = BeautifulSoup(html, "lxml")
    out, seen = [], set()
    for a in soup.select("a.a_category"):
        href = (a.get("href") or "").strip()
        name = a.get_text(" ", strip=True)
        if not href or not name or href in seen:
            continue
        if not href.startswith(path) or href.rstrip("/") == path.rstrip("/"):
            continue
        slug = href.rstrip("/").rsplit("/", 1)[-1]
        if slug in NON_CATEGORY:
            continue
        name = re.sub(r"\s*\(\d[\d\s]*\)\s*$", "", name).strip()  # убрать счётчик
        if not name or len(name) > 70:
            continue
        seen.add(href)
        out.append({"name": name, "slug": slug, "url": href})
    return out


def _title_group_name(html: str) -> str:
    """Имя группы из <title>: «SS.LV Электротехника - Компьютеры, оргтехника»
    → «Компьютеры, оргтехника»."""
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else ""
    title = re.sub(r"^SS\.LV\s+", "", title)
    parts = [x.strip() for x in title.split(" - ") if x.strip()]
    for pt in parts[1:]:                      # parts[0] — сама категория
        if pt.lower() not in ("объявления", "sludinājumi", "ads"):
            # убрать SEO-хвост «…, Цены»/«…, Цена»
            return re.sub(r",\s*цен[аы]\s*$", "", pt, flags=re.IGNORECASE).strip()
    return ""


async def _collapse_to_groups(items: list[dict], path: str) -> list[dict]:
    """Сворачивает развёрнутое мега-меню до непосредственных подкатегорий.

    На страницах вроде /ru/electronics/ ss.lv отдаёт сразу все «листья»
    (/ru/electronics/phones/mobile-phones/…). Группируем их по первому
    сегменту → получаем чистый первый уровень, как на сайте. Имя «скрытой»
    группы берём из <title> её страницы (параллельно, кэшируется в _fetch).
    """
    direct: dict[str, dict] = {}
    order: list[str] = []
    deep: set[str] = set()
    for it in items:
        rest = it["url"][len(path):].strip("/")
        seg  = rest.split("/")[0]
        if seg not in order:
            order.append(seg)
        if "/" in rest:
            deep.add(seg)
        else:
            direct[seg] = it

    out, need_name = [], []
    for seg in order:
        if seg in direct:
            out.append(direct[seg])
        else:                                  # только глубокие ссылки → группа
            grp = {"name": "", "slug": seg, "url": path + seg + "/"}
            out.append(grp)
            need_name.append(grp)

    if need_name:
        async def _resolve(g):
            try:
                g["name"] = _title_group_name(await _fetch(urljoin(BASE, g["url"]))) or g["slug"]
            except Exception:
                g["name"] = g["slug"]
        await asyncio.gather(*[_resolve(g) for g in need_name])
    return out


async def get_subcategories(path: str) -> list[dict]:
    """Скрейп подкатегорий со страницы категории ss.lv.

    path — путь категории, например "/ru/transport/" или
    "/ru/real-estate/flats/". Возвращает [{name, slug, url}] —
    чистый первый уровень, как в навигации ss.lv (мега-меню сворачивается
    до групп). Пустой результат означает «лист» (на странице объявления).
    Результат кэшируется. При ошибке возвращает [].
    """
    async with _lock:
        if path in _subcat_cache:
            return _subcat_cache[path]
    try:
        html  = await _fetch(urljoin(BASE, path))
        items = _extract_a_category(html, path)
        # Объединяем со ссылками/опциями нужного уровня: на страницах марок
        # полный список моделей лежит в дропдауне «Модель» (a.a_category его
        # не видит — у Mercedes 29 серий vs 198 моделей в дропдауне).
        seen = {it["url"] for it in items}
        for it in _extract_subcats(html, path):
            url = path + it["slug"] + "/"
            if url not in seen:
                items.append({"name": it["name"], "slug": it["slug"], "url": url})
                seen.add(url)
        # Транспорт ss.lv показывает все виды плоско (включая водный, багги и
        # т.п.) — не сворачиваем, чтобы было точь в точь как на сайте.
        if path.rstrip("/") != "/ru/transport":
            items = await _collapse_to_groups(items, path)
    except Exception as e:
        log.warning(f"get_subcategories {path}: {e}")
        items = []
    async with _lock:
        _subcat_cache[path] = items
    log.info(f"subcategories({path}): {len(items)}")
    return items


# ---------------------------------------------------------------------------
# Detailed filter form scraping
# ---------------------------------------------------------------------------
RANGE_MIN = ("от", "no", "min", "мин")
RANGE_MAX = ("до", "līdz", "lidz", "max", "макс")


def _clean_range_label(label: str) -> str:
    s = label
    for tok in (*RANGE_MIN, *RANGE_MAX):
        s = re.sub(rf"\s+{re.escape(tok)}\b", "", s, flags=re.IGNORECASE)
    return s.replace(" ,", ",").strip().rstrip(":").rstrip(",")


def _label_for(elem: Tag) -> Optional[str]:
    td = elem.find_parent("td")
    if td:
        prev = td.find_previous_sibling()
        while prev is not None:
            t = prev.get_text(" ", strip=True).rstrip(":").strip()
            if t and len(t) <= 80 and not t.replace(" ", "").isdigit():
                return t
            prev = prev.find_previous_sibling()
    return (elem.get("title") or "").strip() or None


def _parse_form_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    form = soup.find("form", id="filter_frm")
    if not form:
        form = next(
            (f for f in soup.find_all("form") if f.find(attrs={"name": "pr_min"})),
            None,
        )
    if not form:
        return []
    raw = []
    for elem in form.find_all(["input", "select"]):
        if elem.name == "input":
            t = (elem.get("type") or "text").lower()
            if t in ("hidden", "submit", "reset", "button", "image", "checkbox", "radio", "file"):
                continue
        name = elem.get("name")
        if not name or name.lower() in ("sid", "topt", "view", "f1", "f2", "f3"):
            continue
        label = _label_for(elem) or ""
        if not label:
            continue
        is_min = name.lower().endswith("_min")
        is_max = name.lower().endswith("_max")
        f = {"name": name, "label": label, "is_min": is_min, "is_max": is_max}
        if is_min or is_max:
            f["base_name"] = name.rsplit("_", 1)[0]
        if elem.name == "select":
            f["type"] = "select"
            f["options"] = [
                {"value": (o.get("value") or "").strip(), "label": o.get_text(" ", strip=True)}
                for o in elem.find_all("option")
                if (o.get("value") or "").strip() not in ("", "-1")
                and o.get_text(strip=True) not in ("-", "—", "...")
            ]
            if not f["options"]:
                continue
        else:
            f["type"] = "text"
        raw.append(f)
    return _group_ranges(raw)


def _group_ranges(fields: list[dict]) -> list[dict]:
    out, by_name, used = [], {f["name"]: f for f in fields}, set()
    for f in fields:
        if f["name"] in used:
            continue
        if f["is_min"]:
            mx_name = f.get("base_name", "") + "_max"
            if mx_name in by_name:
                out.append({
                    "type": "range",
                    "label": _clean_range_label(f["label"]),
                    "min_name": f["name"],
                    "max_name": mx_name,
                })
                used.add(f["name"])
                used.add(mx_name)
                continue
        if f["is_max"] and (f.get("base_name", "") + "_min") in by_name:
            continue
        item = {"type": f["type"], "label": f["label"].rstrip(":").strip(), "name": f["name"]}
        if f["type"] == "select":
            item["options"] = f["options"]
        out.append(item)
    return out


async def get_filters(category: str = "cars") -> list[dict]:
    async with _lock:
        if category in _filter_cache:
            return _filter_cache[category]
    brands = await get_brands(category)
    if not brands:
        return []
    listing = build_listing_url(brands[0]["slug"], category=category)
    fields: list[dict] = []
    for u in (listing + "filter/", listing):
        try:
            fields = _parse_form_html(await _fetch(u))
            if fields:
                break
        except Exception:
            continue
    async with _lock:
        _filter_cache[category] = fields
    log.info(f"filters({category}): {len(fields)} fields")
    return fields


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------
def build_listing_url(
    brand_slug: str,
    model_slug: Optional[str] = None,
    category: str = "cars",
    mode: str = "sell",
) -> str:
    path = f"{CATEGORIES[category]}{brand_slug}/"
    if model_slug:
        path += f"{model_slug}/"
    path += f"{mode}/"
    return urljoin(BASE, path)


def build_url_with_params(base_url: str, params: dict) -> str:
    if not params:
        return base_url
    clean: list[tuple] = []
    for k, v in params.items():
        if v in (None, "", []):
            continue
        if isinstance(v, list):
            for i in v:
                if i not in (None, ""):
                    clean.append((k, str(i)))
        else:
            clean.append((k, str(v)))
    if not clean:
        return base_url
    sep = "&" if "?" in base_url else "?"
    return base_url + sep + urlencode(clean)


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------
def parse_date_str(raw: str) -> str:
    """Превращает ss.lv date-строку в читаемый формат.

    «сегодня 14:23»      → «Сегодня в 14:23»
    «вчера 09:05»        → «Вчера в 09:05»
    «25.05.»             → «25 мая»
    «25.05.2025»         → «25.05.2025»
    «šodien 14:23»       → «Сегодня в 14:23»
    «vakar 14:23»        → «Вчера в 14:23»
    """
    if not raw:
        return ""
    s = raw.strip()

    # Лат. "šodien" / рус. "сегодня"
    if re.search(r"šodien|сегодня|šodien", s, re.I):
        t = re.search(r"(\d{1,2}:\d{2})", s)
        return f"Сегодня в {t.group(1)}" if t else "Сегодня"

    # Лат. "vakar" / рус. "вчера"
    if re.search(r"vakar|вчера", s, re.I):
        t = re.search(r"(\d{1,2}:\d{2})", s)
        return f"Вчера в {t.group(1)}" if t else "Вчера"

    # DD.MM.YYYY или DD.MM. (текущий год)
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})?", s)
    if m:
        day, mon, year = m.group(1), m.group(2), m.group(3)
        mon_names = ["", "янв", "фев", "мар", "апр", "мая", "июн",
                     "июл", "авг", "сен", "окт", "ноя", "дек"]
        try:
            mon_idx = int(mon)
            mon_str = mon_names[mon_idx] if 1 <= mon_idx <= 12 else mon
        except ValueError:
            mon_str = mon
        t = re.search(r"(\d{1,2}:\d{2})", s)
        time_str = f" в {t.group(1)}" if t else ""
        if year:
            return f"{int(day)} {mon_str} {year}{time_str}"
        return f"{int(day)} {mon_str}{time_str}"

    return s  # вернуть как есть


# ---------------------------------------------------------------------------
# Listings parsing
# ---------------------------------------------------------------------------

def _parse_row_date(tr) -> tuple[str, str]:
    """Ищем дату в <td class="msg_date"> или по паттерну текста.
    Возвращает (raw_date, formatted_date)."""
    # Попытка 1: специфичный класс
    date_td = tr.find("td", class_=re.compile(r"msg_date|date", re.I))
    if not date_td:
        # data-date атрибут (unix timestamp)
        date_td = tr.find("td", attrs={"data-date": True})
    if date_td:
        raw = date_td.get_text(" ", strip=True)
        if raw:
            return raw, parse_date_str(raw)

    # Попытка 2: ищем ячейку с датой по паттерну (сегодня/вчера/полная дата).
    # ВАЖНО: требуем второй разделитель-точку или ключевое слово, иначе объём
    # двигателя «3.0» / «1.6» ложно распознаётся как дата.
    DATE_PAT = re.compile(
        r"(šodien|vakar|сегодня|вчера"
        r"|\d{1,2}\.\d{1,2}\.\d{2,4}"      # 25.05.2026 / 25.05.26
        r"|\d{1,2}\.\d{1,2}\.(?!\d))",     # 25.05.  (краткая форма с точкой)
        re.I,
    )
    for td in tr.find_all("td"):
        txt = td.get_text(" ", strip=True)
        if DATE_PAT.search(txt) and len(txt) < 30:
            return txt, parse_date_str(txt)

    return "", ""


def _clean_city(val: str) -> str:
    if not val: return ""
    if re.search(r"тыс|km|\d{4,}", val, re.I): return ""
    return val.strip()


def _parse_row_city(tr) -> str:
    """Ищем город в <td class="msg_region"> или в последней ячейке."""
    region_td = tr.find("td", class_=re.compile(r"msg_region|region", re.I))
    if region_td:
        # В ячейке может быть ссылка с городом
        a = region_td.find("a")
        if a:
            return _clean_city(a.get_text(strip=True))
        return _clean_city(region_td.get_text(strip=True))

    # Fallback: последняя ячейка, не содержащая €
    cells = tr.find_all("td")
    for td in reversed(cells):
        txt = td.get_text(strip=True)
        if txt and "€" not in txt and len(txt) < 50:
            # Проверяем, что это не год и не пробег (числа)
            if not re.fullmatch(r"[\d\s.,km/%]+", txt, re.I):
                return _clean_city(txt)

    return ""


# ---------------------------------------------------------------------------
# Individual ad page: seller city + publish date
# ---------------------------------------------------------------------------
# «Лиепая и р-он» / «Рига, Центр» / «Cēsu nov.» → оставляем сам город
_CITY_SUFFIX_RE = re.compile(
    r"\s*(?:и\s+)?(?:р-?он|р-?н|район|раj?\.?|nov\.?|novads|pag\.?|pagasts|"
    r"un\s+raj\.?|и\s+р-?он)\.?\s*$",
    re.IGNORECASE,
)


def _clean_seller_city(raw: str) -> str:
    """«Лиепая и р-он» → «Лиепая»; «Рига, Центр» → «Рига»."""
    if not raw:
        return ""
    s = raw.split(",")[0].strip()
    s = _CITY_SUFFIX_RE.sub("", s).strip()
    return s


def canon_fuel(s: str) -> str:
    """Нормализует тип топлива к канону: diesel/hybrid/electric/gas/petrol/''.

    Принимает как значение из меню («дизель», «газ бензин»), так и текст со
    страницы объявления («3.0 дизель»). Порядок проверок важен:
    «бензин/газ» → gas (газ проверяем раньше бензина)."""
    s = (s or "").lower()
    if any(w in s for w in ("дизель", "diz", "diesel")):           return "diesel"
    if any(w in s for w in ("гибрид", "hibr", "hybrid")):          return "hybrid"
    if any(w in s for w in ("электр", "elektr", "electr")):        return "electric"
    if any(w in s for w in ("газ", "gāz", "gaz", "lpg")):          return "gas"
    if any(w in s for w in ("бензин", "benz", "petrol")):          return "petrol"
    return ""


def _ad_options(soup) -> dict:
    """Полная таблица характеристик объявления → {метка: значение}.

    Напр. {«Коробка передач»: «Автомат», «Тип кузова»: «Седан»,
    «Цвет»: «Серый», «Двигатель»: «1.6 бензин», «Место»: «Рига»}.
    """
    opts: dict[str, str] = {}
    for td in soup.find_all("td", class_=re.compile("ads_opt_name")):
        label = td.get_text(" ", strip=True).rstrip(":").strip()
        val   = td.find_next_sibling("td")
        if label and val and label not in opts:
            opts[label] = val.get_text(" ", strip=True)
    # «Место:» лежит вне таблицы характеристик
    if "Место" not in opts:
        for td in soup.find_all("td"):
            if td.get_text(" ", strip=True).rstrip(":").strip() in ("Место", "Vieta"):
                val = td.find_next_sibling("td")
                if val:
                    opts["Место"] = val.get_text(" ", strip=True)
                break
    return opts


async def fetch_ad_details(url: str) -> dict:
    """Грузит страницу объявления: город, дата публикации, топливо и ПОЛНАЯ
    таблица характеристик (opts) для фильтров «из карточки» (КПП, кузов, цвет…).

    Возвращает {city, date_raw, date_fmt, fuel, opts}. При ошибке — пусто.
    """
    out = {"city": "", "date_raw": "", "date_fmt": "", "fuel": "", "opts": {}}
    try:
        html = await _fetch(url)
    except Exception as e:
        log.debug(f"fetch_ad_details {url}: {e}")
        return out
    soup = BeautifulSoup(html, "lxml")

    opts = _ad_options(soup)
    out["opts"] = opts
    out["city"] = _clean_seller_city(opts.get("Место", ""))
    out["fuel"] = canon_fuel(opts.get("Двигатель", "") or opts.get("Dzinējs", ""))

    # Дата публикации в футере: «Дата: 17.06.2026 14:53» (всегда со временем)
    m = re.search(
        r"(?:Дата|Datums)\s*:?\s*(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2})",
        soup.get_text(" ", strip=True),
    )
    if m:
        out["date_raw"] = m.group(1)
        out["date_fmt"] = parse_date_str(m.group(1))
    return out


# ---------------------------------------------------------------------------
# Structured specs from a listing row (для клиентской фильтрации)
# ---------------------------------------------------------------------------
_YEAR_RE   = re.compile(r"^(?:19|20)\d{2}$")
_ENGINE_RE = re.compile(r"^(\d\.\d+)\s*([A-Za-zА-Яа-я/]*)$")


def _digits_int(s: str) -> Optional[int]:
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


def _parse_listing_specs(cell_texts: list[str]) -> dict:
    """Из ячеек строки достаёт year / engine_vol / fuel / mileage_km.

    Колонки транспорта: модель | год | объём(«2.0D») | пробег(«320 тыс.») | цена.
    Разбираем по шаблону, а не по позиции — порядок в категориях разный.
    """
    out = {"year": None, "engine_vol": None, "fuel": None, "mileage_km": None}
    for t in (x.strip() for x in cell_texts):
        if not t:
            continue
        if out["year"] is None and _YEAR_RE.match(t):
            out["year"] = int(t)
            continue
        if out["mileage_km"] is None and re.search(r"тыс|tūkst|\bkm\b|\bкм\b", t, re.I):
            n = _digits_int(t)
            if n is not None:
                out["mileage_km"] = n * 1000 if re.search(r"тыс|tūkst", t, re.I) else n
            continue
        if out["engine_vol"] is None:
            m = _ENGINE_RE.match(t)
            if m:
                out["engine_vol"] = float(m.group(1))
                suf = (m.group(2) or "").lower()
                if "d" in suf:
                    out["fuel"] = "diesel"
                elif "h" in suf:
                    out["fuel"] = "hybrid"
    return out


def _header_cols(soup) -> list[str]:
    """Заголовки колонок списка: «Объявления дата | Консоль | Сост. | Цена»."""
    head = soup.find("tr", id="head_line")
    if not head:
        return []
    return [td.get_text(" ", strip=True) for td in head.find_all(["td", "th"])]


async def fetch_listings(url: str) -> list[dict]:
    """Парсит страницу объявлений ss.lv. Возвращает список Ad.

    Каждый Ad содержит cols = {колонка: значение} (Консоль, Сост., Год…),
    что позволяет клиентскую фильтрацию по любым колонкам категории.
    """
    html = await _fetch(url)
    soup = BeautifulSoup(html, "lxml")
    header = _header_cols(soup)
    ads: list[dict] = []

    for tr in soup.find_all("tr", id=re.compile(r"^tr_\d+$")):
        ad_id = tr["id"].replace("tr_", "")

        # Ссылка на объявление
        link = tr.find("a", class_="am") or tr.find("a", href=re.compile(r"/msg/"))
        if not link or not link.get("href"):
            continue
        ad_url = urljoin(BASE, link["href"])
        title = link.get_text(" ", strip=True)

        # Ячейки с параметрами (год, объём, пробег, цена)
        cells = tr.find_all("td", class_=re.compile(r"msga2"))
        cell_texts = [c.get_text(" ", strip=True) for c in cells]

        price = next((t for t in reversed(cell_texts) if "€" in t), "")
        # Детали: всё кроме первого (заголовок) и последнего (цена, если нашли)
        if price:
            details_cells = [t for t in cell_texts[1:] if t and t != price]
        else:
            details_cells = [t for t in cell_texts[1:] if t]
        details = " | ".join(details_cells[:5])  # не больше 5 полей

        # Дата и город
        date_raw, date_fmt = _parse_row_date(tr)
        city = _parse_row_city(tr)

        # Структурные характеристики для клиентской фильтрации
        specs = _parse_listing_specs(cell_texts)

        # Значения по колонкам (Консоль, Сост., Год…) — для category-specific
        # фильтров. Колонки данных идут после колонки заголовка/даты (header[0]).
        value_cells = [c.get_text(" ", strip=True)
                       for c in tr.find_all("td", class_=re.compile(r"msga2-[or]"))]
        cols = {h: v for h, v in zip(header[1:], value_cells)} if header else {}

        # Фото
        photo = ""
        img = tr.find("img", src=re.compile(r"im|thumb", re.I))
        if img and img.get("src"):
            src = img["src"]
            photo = src if src.startswith("http") else BASE + src

        ads.append({
            "id": ad_id,
            "url": ad_url,
            "title": title,
            "price": price,
            "price_eur": _digits_int(price),
            "year": specs["year"],
            "engine_vol": specs["engine_vol"],
            "fuel": specs["fuel"],
            "mileage_km": specs["mileage_km"],
            "date_raw": date_raw,
            "date_fmt": date_fmt,
            "city": city,
            "details": details,
            "cols": cols,
            "photo": photo,
        })

    return ads


def apply_keyword(ads: list[dict], keyword: Optional[str]) -> list[dict]:
    if not keyword:
        return ads
    kw = keyword.lower()
    return [
        a for a in ads
        if kw in f"{a.get('title','')} {a.get('details','')}".lower()
    ]


def _in_range(val, lo, hi) -> bool:
    """True если val в [lo, hi]. Если val не распарсен (None) — НЕ отсеиваем,
    чтобы не пропустить потенциально подходящее объявление."""
    if val is None:
        return True
    if lo is not None and val < lo:
        return False
    if hi is not None and val > hi:
        return False
    return True


def apply_filters(ads: list[dict], params: Optional[dict]) -> list[dict]:
    """Клиентская фильтрация по цене / году / пробегу и по колонкам категории.

    ss.lv фильтрует через POST/сессию — по сохранённому GET-URL это не
    воспроизвести, поэтому критерии хранятся в params и применяются здесь
    к распарсенным полям (price_eur, year, mileage_km) и колонкам списка
    (params["cols"] = {«Консоль»: «PlayStation 5», «Сост.»: «б/у»}).
    """
    if not params:
        return ads

    def _i(*keys):
        for k in keys:
            v = params.get(k)
            if v not in (None, "", 0):
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return None
        return None

    pmin, pmax = _i("price_min", "pr_min"), _i("price_max", "pr_max")
    ymin, ymax = _i("year_min"), _i("year_max")
    mmin, mmax = _i("mile_min"), _i("mile_max")
    emin, emax = _i("engine_min"), _i("engine_max")   # в куб.см
    col_filters = {k: v for k, v in (params.get("cols") or {}).items() if v}

    if not any(x is not None for x in (pmin, pmax, ymin, ymax, mmin, mmax, emin, emax)) \
       and not col_filters:
        return ads

    def _engine_cc(a):
        v = a.get("engine_vol")          # литры → куб.см
        return int(round(v * 1000)) if v else None

    def _cols_ok(a) -> bool:
        cols = a.get("cols") or {}
        for label, want in col_filters.items():
            val = cols.get(label)
            if val is None:          # колонки нет у объявления — не отсеиваем
                continue
            if val != want:
                return False
        return True

    return [
        a for a in ads
        if _in_range(a.get("price_eur"),  pmin, pmax)
        and _in_range(a.get("year"),       ymin, ymax)
        and _in_range(a.get("mileage_km"), mmin, mmax)
        and _in_range(_engine_cc(a),       emin, emax)
        and _cols_ok(a)
    ]


_catfilter_cache: dict[str, list[dict]] = {}
_listing_cols_cache: dict[str, list[str]] = {}


def listing_columns(url: str) -> list[str]:
    """Заголовки колонок списка для url (заполняется в get_category_filters)."""
    return _listing_cols_cache.get(url, [])


def _match_adopt_label(opts: list[str], ad_opts: dict) -> Optional[str]:
    """К какой характеристике карточки относится селект формы.

    Значение в карточке может быть длиннее опции («Ручная 6-и ступенчатая»
    для «Ручная», «1.6 бензин» для «Бензин») — матчим подстрокой."""
    low = [o.lower() for o in opts]
    for label, val in ad_opts.items():
        vl = val.lower()
        if any(o and (o in vl or vl in o) for o in low):
            return label
    return None


async def get_category_filters(url: str) -> list[dict]:
    """Фильтры конкретной категории, применимые на стороне бота.

    Берёт селекты формы фильтра и привязывает каждый к источнику значения:
      - source="col"   — значение есть в КОЛОНКЕ списка (Консоль, Сост.);
      - source="adopt" — значение есть в КАРТОЧКЕ объявления (КПП, кузов, цвет,
                         топливо) — монитор всё равно грузит карточку.
    Возвращает [{label, options:[str], source}].
    """
    async with _lock:
        if url in _catfilter_cache:
            return _catfilter_cache[url]
    out: list[dict] = []
    try:
        soup   = BeautifulSoup(await _fetch(url), "lxml")
        header = _header_cols(soup)
        _listing_cols_cache[url] = header
        col_vals = {h: set() for h in header[1:]} if header else {}
        for tr in soup.find_all("tr", id=re.compile(r"^tr_\d+$")):
            vals = [c.get_text(" ", strip=True)
                    for c in tr.find_all("td", class_=re.compile(r"msga2-[or]"))]
            for h, v in zip(header[1:], vals):
                if v:
                    col_vals[h].add(v)

        form = soup.find("form", id="filter_frm") or soup.find("form")
        selects = []
        for sel in (form.find_all("select") if form else []):
            name = sel.get("name") or ""
            if not name or name == "sid" or "[min]" in name or "[max]" in name:
                continue
            opts = [o.get_text(" ", strip=True) for o in sel.find_all("option")
                    if (o.get("value") or "").strip() not in ("", "-1")
                    and o.get_text(strip=True) not in ("", "-", "—", "...")]
            if opts and len(opts) <= 60:
                selects.append(opts)

        unmatched = []
        for opts in selects:
            opt_set = set(opts)
            best, score = None, 0
            for h, vals in col_vals.items():
                s = len(opt_set & vals)
                if s > score:
                    best, score = h, s
            if best and score >= 1:
                out.append({"label": best, "options": opts, "source": "col"})
            else:
                unmatched.append(opts)

        # Оставшиеся селекты пробуем привязать к характеристикам карточки
        if unmatched:
            ad_opts = {}
            for tr in soup.find_all("tr", id=re.compile(r"^tr_\d+$"))[:3]:
                link = tr.find("a", href=re.compile(r"/msg/"))
                if not link:
                    continue
                ad_soup = BeautifulSoup(await _fetch(urljoin(BASE, link["href"])), "lxml")
                for k, v in _ad_options(ad_soup).items():
                    ad_opts.setdefault(k, v)
                if {"Коробка передач", "Тип кузова", "Цвет"} & set(ad_opts):
                    break
            for opts in unmatched:
                label = _match_adopt_label(opts, ad_opts)
                if label:
                    out.append({"label": label, "options": opts, "source": "adopt"})
    except Exception as e:
        log.warning(f"get_category_filters {url}: {e}")
    async with _lock:
        _catfilter_cache[url] = out
    return out
