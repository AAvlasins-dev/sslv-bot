"""
Геолокация для ss.lv объявлений.

- CITIES: ~100 городов Латвии (LV + RU названия) с координатами
- city_coords(name) -> (lat, lon) | None
- haversine_km(lat1, lon1, lat2, lon2) -> float
- geocode_city(name) -> (lat, lon, canonical_name) | None  (Nominatim fallback)
- format_distance(km) -> «45 км»
"""
import asyncio
import json
import logging
import math
import re
from typing import Optional

import aiohttp

log = logging.getLogger("geo")

# ---------------------------------------------------------------------------
# Таблица городов: название -> (lat, lon)
# Включаем LV и RU варианты написания.
# ---------------------------------------------------------------------------
CITIES: dict[str, tuple[float, float]] = {
    # --- Rīga metropolitan ---
    "rīga": (56.9460, 24.1059),
    "рига": (56.9460, 24.1059),
    "riga": (56.9460, 24.1059),
    "jūrmala": (56.9685, 23.7702),
    "юрмала": (56.9685, 23.7702),
    "jurmala": (56.9685, 23.7702),
    "salaspils": (56.8610, 24.3485),
    "саласпилс": (56.8610, 24.3485),
    "ķekava": (56.8025, 24.2296),
    "кекава": (56.8025, 24.2296),
    "kekava": (56.8025, 24.2296),
    "mārupe": (56.8957, 24.0367),
    "марупе": (56.8957, 24.0367),
    "marupe": (56.8957, 24.0367),
    "ādaži": (57.0778, 24.3254),
    "адажи": (57.0778, 24.3254),
    "adazi": (57.0778, 24.3254),
    "carnikava": (57.1022, 24.2264),
    "карникава": (57.1022, 24.2264),
    "saulkrasti": (57.2656, 24.4159),
    "саулкрасти": (57.2656, 24.4159),
    "ogre": (56.8147, 24.6046),
    "огре": (56.8147, 24.6046),
    "lielvārde": (56.7155, 24.9647),
    "лиелварде": (56.7155, 24.9647),
    "lielvarde": (56.7155, 24.9647),
    "ikšķile": (56.8312, 24.4966),
    "икшкиле": (56.8312, 24.4966),
    "ikskile": (56.8312, 24.4966),
    "sigulda": (57.1525, 24.8523),
    "сигулда": (57.1525, 24.8523),
    "inčukalns": (57.1378, 24.6877),
    "инчукалнс": (57.1378, 24.6877),
    "incukalns": (57.1378, 24.6877),
    # --- Vidzeme ---
    "valmiera": (57.5379, 25.4265),
    "валмиера": (57.5379, 25.4265),
    "cēsis": (57.3130, 25.2756),
    "цесис": (57.3130, 25.2756),
    "cesis": (57.3130, 25.2756),
    "smiltene": (57.4222, 25.9007),
    "смилтене": (57.4222, 25.9007),
    "gulbene": (57.1739, 26.7584),
    "гулбене": (57.1739, 26.7584),
    "alūksne": (57.4247, 27.0456),
    "алуксне": (57.4247, 27.0456),
    "aluksne": (57.4247, 27.0456),
    "limbaži": (57.5138, 24.7131),
    "лимбажи": (57.5138, 24.7131),
    "limbazi": (57.5138, 24.7131),
    "rūjiena": (57.8965, 25.3350),
    "руйиена": (57.8965, 25.3350),
    "rujiena": (57.8965, 25.3350),
    "strenči": (57.6278, 25.7025),
    "стренчи": (57.6278, 25.7025),
    "strenci": (57.6278, 25.7025),
    "madona": (56.8550, 26.2237),
    "мадона": (56.8550, 26.2237),
    "cesvaine": (56.9706, 26.3069),
    "цесвайне": (56.9706, 26.3069),
    "vecpiebalga": (57.0665, 25.8148),
    "vecumnieki": (56.6067, 24.5228),
    "вецумниеки": (56.6067, 24.5228),
    # --- Zemgale ---
    "jelgava": (56.6511, 23.7234),
    "елгава": (56.6511, 23.7234),
    "bauska": (56.4079, 24.1877),
    "бауска": (56.4079, 24.1877),
    "dobele": (56.6264, 23.2786),
    "добеле": (56.6264, 23.2786),
    "aizkraukle": (56.6035, 25.0048),
    "айзкраукле": (56.6035, 25.0048),
    "tērvete": (56.4956, 23.3781),
    "тервете": (56.4956, 23.3781),
    "tervete": (56.4956, 23.3781),
    "iecava": (56.5990, 24.1979),
    "иецава": (56.5990, 24.1979),
    "pļaviņas": (56.6176, 25.7192),
    "плявиняс": (56.6176, 25.7192),
    "plavinas": (56.6176, 25.7192),
    "jaunjelgava": (56.6164, 25.0761),
    "яунелгава": (56.6164, 25.0761),
    "koknese": (56.6491, 25.4325),
    "кокнесе": (56.6491, 25.4325),
    "skrīveri": (56.6345, 25.1168),
    "скривери": (56.6345, 25.1168),
    "skriveri": (56.6345, 25.1168),
    # --- Kurzeme ---
    "liepāja": (56.5047, 21.0107),
    "лиепая": (56.5047, 21.0107),
    "liepaja": (56.5047, 21.0107),
    "ventspils": (57.3944, 21.5607),
    "вентспилс": (57.3944, 21.5607),
    "kuldīga": (56.9680, 21.9604),
    "кулдига": (56.9680, 21.9604),
    "kuldiga": (56.9680, 21.9604),
    "tukums": (56.9671, 23.1522),
    "тукумс": (56.9671, 23.1522),
    "talsi": (57.2453, 22.5861),
    "талси": (57.2453, 22.5861),
    "saldus": (56.6681, 22.4945),
    "салдус": (56.6681, 22.4945),
    "aizpute": (56.7217, 21.5966),
    "айзпуте": (56.7217, 21.5966),
    "skrunda": (56.6779, 22.0119),
    "скрунда": (56.6779, 22.0119),
    "kandava": (57.0369, 22.7769),
    "кандава": (57.0369, 22.7769),
    "grobiņa": (56.5378, 21.1631),
    "гробиня": (56.5378, 21.1631),
    "grobina": (56.5378, 21.1631),
    "pāvilosta": (56.8883, 21.1966),
    "павилоста": (56.8883, 21.1966),
    "pavilosta": (56.8883, 21.1966),
    "nīca": (56.3436, 21.0628),
    "ница": (56.3436, 21.0628),
    "nica": (56.3436, 21.0628),
    "brocēni": (56.6847, 22.5791),
    "броцены": (56.6847, 22.5791),
    "broceni": (56.6847, 22.5791),
    "engure": (57.1599, 23.2175),
    "энгуре": (57.1599, 23.2175),
    # --- Latgale ---
    "daugavpils": (55.8770, 26.5355),
    "даугавпилс": (55.8770, 26.5355),
    "rēzekne": (56.5100, 27.3331),
    "резекне": (56.5100, 27.3331),
    "rezekne": (56.5100, 27.3331),
    "jēkabpils": (56.4981, 25.8768),
    "екабпилс": (56.4981, 25.8768),
    "jekabpils": (56.4981, 25.8768),
    "krāslava": (55.8938, 27.1700),
    "краслава": (55.8938, 27.1700),
    "kraslava": (55.8938, 27.1700),
    "ludza": (56.5468, 27.7127),
    "лудза": (56.5468, 27.7127),
    "preiļi": (56.2913, 26.7247),
    "прейли": (56.2913, 26.7247),
    "preili": (56.2913, 26.7247),
    "balvi": (57.1338, 27.2666),
    "балви": (57.1338, 27.2666),
    "viļāni": (56.5495, 26.9200),
    "виляны": (56.5495, 26.9200),
    "vilani": (56.5495, 26.9200),
    "varakļāni": (56.6018, 26.7537),
    "варакляны": (56.6018, 26.7537),
    "varaklani": (56.6018, 26.7537),
    "viļaka": (57.1826, 27.6654),
    "виляка": (57.1826, 27.6654),
    "vilaka": (57.1826, 27.6654),
    "zilupe": (56.3819, 28.1310),
    "зилупе": (56.3819, 28.1310),
    "kārsava": (56.7812, 27.6826),
    "карсава": (56.7812, 27.6826),
    "karsava": (56.7812, 27.6826),
    "dagda": (56.0889, 27.5296),
    "дагда": (56.0889, 27.5296),
    "subate": (56.0152, 25.9108),
    "субате": (56.0152, 25.9108),
    "aknīste": (56.1639, 25.7431),
    "акнисте": (56.1639, 25.7431),
    "akniste": (56.1639, 25.7431),
    "nereta": (56.2019, 25.3221),
    "нерета": (56.2019, 25.3221),
    # --- Regions (approx) ---
    "pierīgas novads": (56.9460, 24.1059),
    "рижский район": (56.9460, 24.1059),
    "рижский": (56.9460, 24.1059),
    "rīgas raj.": (56.9460, 24.1059),
    "pierīga": (56.9460, 24.1059),
    "pieria": (56.9460, 24.1059),
}

# Nominatim cache: city_name -> (lat, lon, canonical) | None
_nominatim_cache: dict[str, Optional[tuple]] = {}
_nominatim_lock = asyncio.Lock()


def _normalize(name: str) -> str:
    """Приводим к нижнему регистру + базовые замены."""
    return name.lower().strip()


def city_coords(name: str) -> Optional[tuple[float, float]]:
    """Ищет координаты города в локальной таблице. Возвращает (lat, lon) или None."""
    if not name:
        return None
    key = _normalize(name)
    if key in CITIES:
        return CITIES[key]
    # Частичное совпадение: «Rīgas rajons» → «rīga»
    for k, v in CITIES.items():
        if k in key or key in k:
            return v
    return None


async def geocode_nominatim(name: str) -> Optional[tuple[float, float, str]]:
    """Запрашивает Nominatim OSM. Возвращает (lat, lon, display_name) или None.
    Rate-limit: 1 req/sec по ToS Nominatim."""
    key = _normalize(name)
    async with _nominatim_lock:
        if key in _nominatim_cache:
            return _nominatim_cache[key]
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": f"{name}, Latvia", "format": "json", "limit": 1}
            headers = {"User-Agent": "ss-lv-monitor-bot/1.0"}
            async with aiohttp.ClientSession(headers=headers,
                                             timeout=aiohttp.ClientTimeout(total=10)) as s:
                async with s.get(url, params=params) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data:
                            item = data[0]
                            result = (
                                float(item["lat"]),
                                float(item["lon"]),
                                item.get("display_name", name),
                            )
                            _nominatim_cache[key] = result
                            return result
        except Exception as e:
            log.warning(f"Nominatim failed for '{name}': {e}")
        _nominatim_cache[key] = None
        return None


async def resolve_city(name: str) -> Optional[tuple[float, float, str]]:
    """Пробует локальную таблицу, потом Nominatim. Возвращает (lat, lon, canonical_name)."""
    if not name:
        return None
    coords = city_coords(name)
    if coords:
        # Капитализируем для отображения
        canonical = name.strip().title()
        return coords[0], coords[1], canonical
    # Fallback
    await asyncio.sleep(1.1)  # Nominatim rate-limit
    result = await geocode_nominatim(name)
    return result


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя координатами по формуле Хаверсина, в км."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def format_distance(km: float) -> str:
    """«3 км», «45 км», «1 230 км»"""
    if km < 1:
        return "< 1 км"
    if km < 1000:
        return f"{round(km)}\u00a0км"
    return f"{km/1000:.1f}\u00a0тыс. км"


# --- Reverse geocode (для Telegram Location) ---
def nearest_city(lat: float, lon: float, limit_km: float = 80.0) -> Optional[str]:
    """Возвращает название ближайшего города из CITIES в пределах limit_km."""
    best_name, best_dist = None, float("inf")
    for name, (clat, clon) in CITIES.items():
        d = haversine_km(lat, lon, clat, clon)
        if d < best_dist:
            best_dist = d
            best_name = name
    if best_name and best_dist <= limit_km:
        return best_name.title()
    return None

# ---------------------------------------------------------------------------
# Список городов для кнопочного меню
# ---------------------------------------------------------------------------
CITY_BUTTONS: list[str] = sorted([
    "Rīga", "Daugavpils", "Jelgava", "Jūrmala", "Liepāja",
    "Rēzekne", "Valmiera", "Ventspils", "Jēkabpils", "Ogre",
    "Sigulda", "Tukums", "Cēsis", "Kuldīga", "Talsi", "Saldus",
    "Bauska", "Alūksne", "Gulbene", "Madona", "Dobele", "Krāslava",
    "Ludza", "Preiļi", "Balvi", "Limbaži", "Smiltene", "Rūjiena",
    "Strenči", "Carnikava", "Salaspils", "Ķekava", "Mārupe",
    "Ādaži", "Saulkrasti", "Aizkraukle", "Pļaviņas", "Jaunjelgava",
    "Koknese", "Skrīveri", "Lielvārde", "Ikšķile", "Aizpute",
    "Skrunda", "Engure", "Kandava", "Grobiņa", "Nīca", "Pāvilosta",
    "Brocēni", "Iecava", "Varakļāni", "Viļāni", "Viļaka", "Zilupe",
    "Kārsava", "Dagda", "Subate", "Aknīste", "Nereta", "Vecumnieki",
    "Cesvaine", "Lubāna", "Koknese", "Salacgrīva", "Pārgauja",
],
key=lambda x: x.lower()
    .replace("ā", "a").replace("ē", "e").replace("ī", "i").replace("ū", "u")
    .replace("ģ", "g").replace("ķ", "k").replace("ļ", "l")
    .replace("ņ", "n").replace("š", "s").replace("ž", "z").replace("č", "c")
)
