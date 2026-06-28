"""Background monitor with per-filter interval and language-aware notifications."""
import asyncio
import logging
import re
import time
from html import escape as _esc

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import db
import geo
import parser as p

log = logging.getLogger("monitor")


def _tokens(s: str) -> set:
    """Слова локации в нижнем регистре: «Рига, Плявниеки» → {рига, плявниеки}.
    Пословный матч (а не подстрочный) — иначе «за» из «За границей» ложно
    попадает в «Засулаукс» и т.п."""
    return {w for w in re.split(r"[^\w]+", (s or "").lower()) if w}


def _ad_location(ad: dict) -> str:
    """Полная локация объявления из карточки: «Рига, Плявниеки» (регион+район)."""
    opts = ad.get("opts") or {}
    return (opts.get("Местонахождение") or opts.get("Место") or ad.get("city", "") or "")


async def _ad_coords(ad: dict):
    """Координаты объявления: точный адрес из карточки (геокодинг, кэш) →
    фолбэк на координаты города. Для расстояния и радиуса."""
    opts = ad.get("opts") or {}
    addr = (opts.get("Адрес, улица") or "").strip()
    if addr:
        try:
            g = await geo.geocode_nominatim(addr)
            if g:
                return (g[0], g[1])
        except Exception:
            pass
    return geo.city_coords(ad.get("city", "") or "")


async def geo_ok(ad: dict, user: dict | None) -> bool:
    """Проходит ли объявление общий гео-фильтр пользователя («Моё место»).
    area: совпадение региона/района в «Местонахождении» карточки.
    gps:  расстояние от координат юзера до адреса объявления ≤ радиуса.
    Нет настройки / нет локации в карточке → True (лучше показать, чем потерять)."""
    if not user:
        return True
    mode = user.get("geo_mode")
    if mode == "area":
        loc = _ad_location(ad)
        if not loc:
            return True
        toks = _tokens(loc)                              # {рига, плявниеки}
        region   = (user.get("geo_region") or "").strip().lower()
        district = (user.get("geo_district") or "").strip().lower()
        # Регион: первое слово как ЦЕЛЫЙ токен (а не подстрока) — отсекает
        # ложные совпадения и кросс-региональные коллизии (Рига/Центр vs Лиепая/Центр).
        if region:
            rw = region.split()[0]                       # «рижский район» → «рижский»
            if rw and rw not in toks:
                return False
        # Район: все его слова должны присутствовать в локации.
        if district:
            dw = _tokens(district)
            if not (dw and dw <= toks):
                return False
        return True
    if mode == "gps":
        want_km = user.get("geo_radius")
        ulat, ulon = user.get("lat"), user.get("lon")
        if want_km and ulat and ulon:
            coords = await _ad_coords(ad)
            if coords and geo.haversine_km(ulat, ulon, coords[0], coords[1]) > float(want_km):
                return False
    return True


async def _build_msg(f: dict, ad: dict, lang: str = "ru") -> str:
    # Заголовки/описания/города ss.lv могут содержать < > & — экранируем, иначе
    # Telegram (parse_mode=HTML) отвергает сообщение: «can't parse entities».
    brand = f.get("brand","")
    model = f.get("model","")
    header_parts = []
    if brand: header_parts.append(brand)
    if model: header_parts.append(model)
    header = " ".join(header_parts) if header_parts else "ss.lv"
    lines  = [f"🆕 <b>{_esc(header)}</b>"]
    if ad.get("title"):   lines.append(_esc(ad["title"]))
    if ad.get("details"): lines.append(_esc(ad["details"]))
    if ad.get("price"):   lines.append(f"💰 <b>{_esc(ad['price'])}</b>")
    date_str = p.parse_date_str(ad.get("date_raw") or "", lang) or ad.get("date_fmt") or ""
    if date_str: lines.append(f"📅 {_esc(date_str)}")
    loc = _ad_location(ad)
    if loc:
        dist_str = ""
        # Расстояние показываем ТОЛЬКО в gps-режиме: там оно осмысленно и адрес
        # уже геокодирован в geo_ok (кэш). В area-режиме не геокодим ради строки —
        # это лишний сетевой запрос на КАЖДОЕ уведомление (Nominatim 1 req/sec).
        user = await db.get_user(f["user_id"])
        if user and user.get("geo_mode") == "gps" and user.get("lat") and user.get("lon"):
            coords = await _ad_coords(ad)          # точный адрес → координаты (из кэша)
            if coords:
                km = geo.haversine_km(user["lat"], user["lon"], coords[0], coords[1])
                dist_str = f" — {geo.format_distance(km)}"
                if lang == "lv":   dist_str += " no tevis"
                elif lang == "en": dist_str += " from you"
                else:              dist_str += " от вас"
        lines.append(f"📍 {_esc(loc)}{_esc(dist_str)}")
    label = "Открыть →" if lang=="ru" else "Atvērt →" if lang=="lv" else "Open →"
    lines.append(f'\n<a href="{_esc(ad["url"], quote=True)}">{label}</a>')
    return "\n".join(lines)


async def check_filter(bot: Bot, f: dict, max_per_cycle: int) -> int:
    # ss.lv разово таймаутит (особенно тяжёлые разделы). В ФОНОВОМ мониторе
    # (никто не ждёт) можно ещё раз повторить — гасит разовые сбои на месте.
    ads = None
    for attempt in range(2):
        try:
            ads = await p.fetch_listings(f["url"])
            break
        except Exception as e:
            if attempt == 0:
                await asyncio.sleep(1.0)
                continue
            # type(e).__name__ важен: у TimeoutError пустой str() → иначе «error:» без текста.
            log.warning(f"filter #{f['id']} error: {type(e).__name__}: {e}")
            # Помечаем проверенным даже при сбое — чтобы битый фильтр не дёргал
            # ss.lv каждый цикл; повторим по обычному интервалу.
            try: await db.update_last_checked(f["id"])
            except Exception: pass
            return 0

    ads     = p.apply_keyword(ads, f.get("keyword"))
    ads     = p.apply_filters(ads, f.get("params"))
    new_ads = [a for a in ads if not await db.is_seen(f["id"], a["id"])]
    if not new_ads: return 0

    await db.mark_seen(f["id"], [a["id"] for a in new_ads])

    # Язык пользователя
    user = await db.get_user(f["user_id"])
    lang = (user or {}).get("lang","ru")

    params      = f.get("params") or {}
    want_fuel   = params.get("fuel")
    want_adopts = params.get("adopts") or {}
    # Гео — ОБЩАЯ настройка пользователя («Моё место»), применяется ко всем
    # фильтрам (см. geo_ok): area — регион+район из карточки; gps — радиус.

    sent = 0
    for ad in new_ads[:max_per_cycle]:
        # Город, дата, топливо и характеристики (КПП/кузов/цвет) есть только на
        # странице объявления — грузим её для новых объявлений (их немного).
        det = {}
        try:
            det = await p.fetch_ad_details(ad["url"])
            if det.get("city"):     ad["city"]     = det["city"]
            if det.get("date_fmt"): ad["date_fmt"] = det["date_fmt"]
            if det.get("fuel"):     ad["fuel"]     = det["fuel"]
            ad["opts"] = det.get("opts", {})
        except Exception as e:
            log.debug(f"details failed for {ad.get('url')}: {e}")

        # Объявление уже в архиве (срок показа истёк) — не уведомляем
        if det.get("archived"):
            log.debug(f"skip archived ad {ad.get('url')}")
            continue

        # Фильтр по топливу (надёжно определяется только на странице объявления)
        if want_fuel and ad.get("fuel") and ad["fuel"] != want_fuel:
            continue
        # Фильтры «из карточки» (КПП, кузов, цвет…) — матчим подстрокой
        if want_adopts:
            opts = ad.get("opts") or {}
            mismatch = any(
                (opts.get(label) or "") and want.lower() not in (opts.get(label) or "").lower()
                for label, want in want_adopts.items()
            )
            if mismatch:
                continue
        # Гео-фильтр из «Моё место» (общий для всех фильтров пользователя).
        if not await geo_ok(ad, user):
            continue
        text = await _build_msg(f, ad, lang)
        try:
            if ad.get("photo"):
                await bot.send_photo(
                    chat_id=f["user_id"],
                    photo=ad["photo"],
                    caption=text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(f["user_id"], text,
                                       parse_mode="HTML", disable_web_page_preview=False)
            sent += 1
            await asyncio.sleep(0.2)
        except TelegramAPIError as e:
            log.warning(f"send failed: {e}")

    if len(new_ads) > max_per_cycle:
        try:
            overflow = len(new_ads) - max_per_cycle
            txt = {
                "ru": f"…и ещё {overflow} новых.",
                "lv": f"…un vēl {overflow} jauni.",
                "en": f"…and {overflow} more new listings.",
            }.get(lang, f"…+{overflow}")
            await bot.send_message(f["user_id"], txt)
        except TelegramAPIError: pass

    await db.increment_sent(f["id"], sent)
    await db.update_last_checked(f["id"])
    return sent


async def monitor_loop(bot: Bot, base_interval: int, max_per_cycle: int):
    log.info(f"monitor started (base={base_interval}s, max={max_per_cycle})")
    prune_cycle = 0
    while True:
        try:
            filters = await db.all_active_filters()
            now = time.time()
            total = 0
            for f in filters:
                if now - (f.get("last_checked_at") or 0) < (f.get("check_interval") or base_interval):
                    continue
                try:                       # один битый фильтр не должен ронять весь цикл
                    total += await check_filter(bot, f, max_per_cycle)
                except Exception:
                    log.exception("filter #%s crashed in cycle", f.get("id"))
                await asyncio.sleep(0.5)
            if total: log.info(f"sent {total} notifications")
            prune_cycle += 1
            if prune_cycle >= 1440:
                await db.prune_old_seen(); prune_cycle = 0
        except Exception: log.exception("monitor crash")
        await asyncio.sleep(60)
