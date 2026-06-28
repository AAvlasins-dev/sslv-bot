"""SQLite layer — полная версия с lang, stats, interval, last_checked."""
import json
import time
import aiosqlite
from typing import Optional

DB_PATH = "data.db"

INIT_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id         INTEGER PRIMARY KEY,
    username        TEXT,
    lat             REAL,
    lon             REAL,
    location_name   TEXT,
    lang            TEXT DEFAULT 'ru',
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS filters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    category        TEXT NOT NULL DEFAULT 'other',
    category_path   TEXT,
    brand           TEXT,
    brand_slug      TEXT,
    model           TEXT,
    model_slug      TEXT,
    params          TEXT NOT NULL DEFAULT '{}',
    params_summary  TEXT NOT NULL DEFAULT '{}',
    keyword         TEXT,
    url             TEXT NOT NULL,
    check_interval  INTEGER DEFAULT 300,
    last_checked_at REAL    DEFAULT 0,
    total_sent      INTEGER DEFAULT 0,
    last_sent_at    TEXT,
    active          INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seen_ads (
    filter_id   INTEGER NOT NULL,
    ad_id       TEXT NOT NULL,
    seen_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (filter_id, ad_id)
);

CREATE INDEX IF NOT EXISTS idx_filters_user ON filters(user_id, active);
CREATE INDEX IF NOT EXISTS idx_seen          ON seen_ads(filter_id);
"""


async def init(path: str):
    global DB_PATH
    DB_PATH = path
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(INIT_SQL)
        for col, defval, table in [
            ("check_interval",  "INTEGER DEFAULT 300", "filters"),
            ("last_checked_at", "REAL DEFAULT 0",      "filters"),
            ("category_path",   "TEXT",                "filters"),
            ("total_sent",      "INTEGER DEFAULT 0",   "filters"),
            ("last_sent_at",    "TEXT",                "filters"),
            ("lang",            "TEXT DEFAULT 'ru'",   "users"),
            # Гео-настройка пользователя («Моё место»): режим + район + радиус.
            ("geo_mode",        "TEXT",                "users"),   # 'gps' | 'area' | NULL
            ("geo_region",      "TEXT",                "users"),   # напр. «Рига»
            ("geo_district",    "TEXT",                "users"),   # напр. «Плявниеки»
            ("geo_radius",      "INTEGER",             "users"),   # км (для gps), NULL=без огр.
        ]:
            try:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defval}")
            except Exception:
                pass
        await db.commit()


# ── users ─────────────────────────────────────────────────────────────────
async def upsert_user(user_id: int, username: Optional[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        if username:
            await db.execute(
                "UPDATE users SET username=? WHERE user_id=?", (username, user_id)
            )
        await db.commit()


async def set_user_lang(user_id: int, lang: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, lang) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang""",
            (user_id, lang),
        )
        await db.commit()


async def set_user_location(user_id: int, lat: float, lon: float, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, lat, lon, location_name)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
               lat=excluded.lat, lon=excluded.lon,
               location_name=excluded.location_name""",
            (user_id, lat, lon, name),
        )
        await db.commit()


async def set_user_geo(user_id: int, mode: Optional[str], lat, lon, name: str,
                       region: Optional[str] = None, district: Optional[str] = None,
                       radius: Optional[int] = None):
    """Сохранить гео-настройку «Моё место»: режим (gps/area), точку отсчёта
    (lat/lon + имя для показа) и критерий фильтра (район или радиус)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, lat, lon, location_name,
                                  geo_mode, geo_region, geo_district, geo_radius)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                  lat=excluded.lat, lon=excluded.lon,
                  location_name=excluded.location_name,
                  geo_mode=excluded.geo_mode, geo_region=excluded.geo_region,
                  geo_district=excluded.geo_district, geo_radius=excluded.geo_radius""",
            (user_id, lat, lon, name, mode, region, district, radius),
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def count_filters(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM filters WHERE user_id=? AND active=1", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ── filters ───────────────────────────────────────────────────────────────
async def add_filter(
    user_id: int, category: str,
    brand: Optional[str], brand_slug: Optional[str],
    model: Optional[str], model_slug: Optional[str],
    params: dict, params_summary: dict,
    keyword: Optional[str], url: str,
    check_interval: int = 300,
    category_path: Optional[str] = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO filters
               (user_id, category, category_path, brand, brand_slug,
                model, model_slug, params, params_summary,
                keyword, url, check_interval)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, category, category_path, brand, brand_slug,
                model, model_slug,
                json.dumps(params, ensure_ascii=False),
                json.dumps(params_summary, ensure_ascii=False),
                keyword, url, check_interval,
            ),
        )
        await db.commit()
        return cur.lastrowid


def _row(r) -> dict:
    d = dict(r)
    for k in ("params", "params_summary"):
        try:
            d[k] = json.loads(d.get(k) or "{}")
        except Exception:
            d[k] = {}
    return d


async def list_filters(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM filters WHERE user_id=? AND active=1 ORDER BY id",
            (user_id,),
        ) as cur:
            return [_row(r) for r in await cur.fetchall()]


async def get_filter(filter_id: int, user_id: int | None = None) -> dict | None:
    sql = "SELECT * FROM filters WHERE id=?"
    args: tuple = (filter_id,)
    if user_id is not None:
        sql += " AND user_id=?"
        args = (filter_id, user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(sql, args) as cur:
            r = await cur.fetchone()
            return _row(r) if r else None


async def delete_filter(filter_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE filters SET active=0 WHERE id=? AND user_id=?",
            (filter_id, user_id),
        )
        await db.commit()


async def all_active_filters() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM filters WHERE active=1") as cur:
            return [_row(r) for r in await cur.fetchall()]


async def update_last_checked(filter_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE filters SET last_checked_at=? WHERE id=?",
            (time.time(), filter_id),
        )
        await db.commit()


async def reset_user_checks(user_id: int) -> int:
    """Сбросить last_checked_at у всех фильтров пользователя → монитор
    перепроверит их в ближайшем цикле (для /diag «авто-починка»)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE filters SET last_checked_at=0 WHERE user_id=? AND active=1",
            (user_id,),
        )
        await db.commit()
        return cur.rowcount or 0


async def increment_sent(filter_id: int, count: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE filters SET
               total_sent = total_sent + ?,
               last_sent_at = datetime('now')
               WHERE id=?""",
            (count, filter_id),
        )
        await db.commit()


# ── seen_ads ──────────────────────────────────────────────────────────────
async def is_seen(filter_id: int, ad_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM seen_ads WHERE filter_id=? AND ad_id=?",
            (filter_id, ad_id),
        ) as cur:
            return await cur.fetchone() is not None


async def mark_seen(filter_id: int, ad_ids: list[str]):
    if not ad_ids:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            "INSERT OR IGNORE INTO seen_ads (filter_id, ad_id) VALUES (?, ?)",
            [(filter_id, a) for a in ad_ids],
        )
        await db.commit()


async def prune_old_seen(days: int = 60):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM seen_ads WHERE seen_at < datetime('now', ?)",
            (f"-{days} day",),
        )
        await db.commit()
