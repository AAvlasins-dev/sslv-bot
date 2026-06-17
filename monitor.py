"""Background monitor with per-filter interval and language-aware notifications."""
import asyncio
import logging
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import db
import geo
import parser as p

log = logging.getLogger("monitor")


async def _build_msg(f: dict, ad: dict, lang: str = "ru") -> str:
    brand = f.get("brand","")
    model = f.get("model","")
    header_parts = []
    if brand: header_parts.append(brand)
    if model: header_parts.append(model)
    header = " ".join(header_parts) if header_parts else "ss.lv"
    lines  = [f"🆕 <b>{header}</b>"]
    if ad.get("title"):   lines.append(ad["title"])
    if ad.get("details"): lines.append(ad["details"])
    if ad.get("price"):   lines.append(f"💰 <b>{ad['price']}</b>")
    date_str = ad.get("date_fmt") or ad.get("date_raw") or ""
    if date_str: lines.append(f"📅 {date_str}")
    city = ad.get("city","")
    if city:
        dist_str = ""
        user = await db.get_user(f["user_id"])
        if user and user.get("lat") and user.get("lon"):
            coords = geo.city_coords(city)
            if coords:
                km = geo.haversine_km(user["lat"],user["lon"],coords[0],coords[1])
                dist_str = f" — {geo.format_distance(km)}"
                if lang == "lv":   dist_str += " no tevis"
                elif lang == "en": dist_str += " from you"
                else:              dist_str += " от вас"
        lines.append(f"📍 {city}{dist_str}")
    lines.append(f'\n<a href="{ad["url"]}">{"Открыть →" if lang=="ru" else "Atvērt →" if lang=="lv" else "Open →"}</a>')
    return "\n".join(lines)


async def check_filter(bot: Bot, f: dict, max_per_cycle: int) -> int:
    try:
        ads = await p.fetch_listings(f["url"])
    except Exception as e:
        log.warning(f"filter #{f['id']} error: {e}")
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

    sent = 0
    for ad in new_ads[:max_per_cycle]:
        # Город, дата, топливо и характеристики (КПП/кузов/цвет) есть только на
        # странице объявления — грузим её для новых объявлений (их немного).
        try:
            det = await p.fetch_ad_details(ad["url"])
            if det.get("city"):     ad["city"]     = det["city"]
            if det.get("date_fmt"): ad["date_fmt"] = det["date_fmt"]
            if det.get("fuel"):     ad["fuel"]     = det["fuel"]
            ad["opts"] = det.get("opts", {})
        except Exception as e:
            log.debug(f"details failed for {ad.get('url')}: {e}")

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
                total += await check_filter(bot, f, max_per_cycle)
                await asyncio.sleep(0.5)
            if total: log.info(f"sent {total} notifications")
            prune_cycle += 1
            if prune_cycle >= 1440:
                await db.prune_old_seen(); prune_cycle = 0
        except Exception: log.exception("monitor crash")
        await asyncio.sleep(60)
