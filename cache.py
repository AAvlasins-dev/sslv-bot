"""
Кэш данных ss.lv с предзагрузкой при старте.
После preload() все категории и модели топ-марок отдаются мгновенно из памяти.
"""
import asyncio
import logging
import time
from typing import Optional

log = logging.getLogger("cache")

_CACHE: dict = {}
_TTL = 3600  # 1 час — потом обновляется при следующем запросе


# ─── Базовые операции ─────────────────────────────────────────

def get(key: str):
    entry = _CACHE.get(key)
    if entry and time.time() - entry[0] < _TTL:
        return entry[1]
    return None


def put(key: str, value):
    if value:
        _CACHE[key] = (time.time(), value)


def stats() -> str:
    return f"{len(_CACHE)} записей в кэше"


def clear() -> int:
    """Полный сброс кэша (для /diag «авто-починка»). Возвращает число записей."""
    n = len(_CACHE)
    _CACHE.clear()
    return n


# ─── Кэшированные получатели ──────────────────────────────────

async def subcats(path: str, p_module, lang: str = "ru") -> list:
    key = f"sub:{lang}:{path}"
    cached = get(key)
    if cached is not None:
        return cached
    result = await p_module.get_subcategories(path, lang)
    put(key, result)
    return result


async def models(brand_slug: str, cat: str, p_module, lang: str = "ru") -> list:
    key = f"mod:{lang}:{brand_slug}:{cat}"
    cached = get(key)
    if cached is not None:
        return cached
    try:
        result = await asyncio.wait_for(
            p_module.get_models(brand_slug, cat, lang), timeout=8.0
        )
    except Exception:
        result = []
    put(key, result)
    return result


# ─── Предзагрузка при старте ──────────────────────────────────

# Топ-марки авто для предзагрузки моделей (самые популярные в Латвии)
PRELOAD_CAR_BRANDS = [
    "bmw", "mercedes", "audi", "volkswagen", "toyota",
    "ford", "opel", "skoda", "volvo", "nissan",
    "mazda", "honda", "renault", "hyundai", "kia",
]

PRELOAD_MOTO_BRANDS = [
    "honda", "yamaha", "kawasaki", "suzuki", "bmw",
]


async def preload(p_module):
    """
    Запускается при старте. Параллельно загружает:
    - Подкатегории всех 12 разделов ss.lv
    - Модели топ-15 марок авто
    - Модели топ-5 марок мото
    """
    import categories as cat_mod

    log.info("Начинаю предзагрузку кэша ss.lv…")
    start = time.time()

    # Ограничиваем параллельность чтобы не заблокировали
    sem = asyncio.Semaphore(4)

    async def _safe(coro):
        async with sem:
            try:
                await asyncio.wait_for(coro, timeout=10.0)
            except Exception:
                pass

    tasks = []

    # 1. Подкатегории всех топ-категорий (русский — язык по умолчанию)
    for cat in cat_mod.TOP_CATEGORIES:
        key  = f"sub:ru:{cat['path']}"
        tasks.append(_safe(_load_subcats(cat["path"], p_module, key)))

    # 2. Модели топ авто-марок (русский — язык по умолчанию)
    for slug in PRELOAD_CAR_BRANDS:
        key = f"mod:ru:{slug}:cars"
        tasks.append(_safe(_load_models(slug, "cars", p_module, key)))

    # 3. Модели топ мото-марок
    for slug in PRELOAD_MOTO_BRANDS:
        key = f"mod:ru:{slug}:motorcycles"
        tasks.append(_safe(_load_models(slug, "motorcycles", p_module, key)))

    await asyncio.gather(*tasks)

    elapsed = time.time() - start
    log.info(f"Кэш готов за {elapsed:.1f}с — {len(_CACHE)} записей")


async def _load_subcats(path: str, p_module, cache_key: str):
    result = await p_module.get_subcategories(path)
    put(cache_key, result)
    if result:
        log.debug(f"  subcats {path}: {len(result)} шт.")


async def _load_models(slug: str, cat: str, p_module, cache_key: str):
    try:
        result = await p_module.get_models(slug, cat)
        put(cache_key, result)
        if result:
            log.debug(f"  models {slug}/{cat}: {len(result)} шт.")
    except Exception as e:
        log.debug(f"  models {slug}/{cat}: ошибка {e}")
