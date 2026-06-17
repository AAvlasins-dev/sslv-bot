"""
База данных технических характеристик автомобилей.
Поддерживаемые бренды: BMW, Mercedes-Benz, Audi, Volkswagen, Toyota, Honda,
Volvo, Mazda, Opel, Ford, Skoda.

lookup(brand, model, year) → CarSpec | None
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CarSpec:
    brand: str
    model: str
    generation: str
    year_from: int
    year_to: int
    engine_cc: int        # объём в куб.см
    engine_label: str     # "2.5L" / "1998cc"
    hp: int               # лошадиные силы
    kw: int               # киловатты
    torque_nm: int        # момент Нм
    fuel: str             # petrol / diesel / hybrid / electric
    cylinders: int
    drive: str = "RWD"    # RWD / FWD / AWD
    gearbox_hint: str = "" # информация о КПП

    def format_ru(self) -> str:
        fuel_ru = {"petrol": "Бензин", "diesel": "Дизель",
                   "hybrid": "Гибрид", "electric": "Электро"}.get(self.fuel, self.fuel)
        drive_ru = {"RWD": "Задний", "FWD": "Передний", "AWD": "Полный"}.get(self.drive, self.drive)
        return (
            f"🔧 <b>{self.brand} {self.model}</b> ({self.generation}, {self.year_from}–{self.year_to})\n"
            f"   ⚡ <b>{self.hp} л.с.</b> / <b>{self.kw} кВт</b>\n"
            f"   🔩 Объём: {self.engine_label} · {self.cylinders} цил. · {fuel_ru}\n"
            f"   💪 Момент: {self.torque_nm} Нм\n"
            f"   🚗 Привод: {drive_ru}"
            + (f"\n   ⚙️ {self.gearbox_hint}" if self.gearbox_hint else "")
        )


# ─────────────────────────────────────────────────────────────
# Базы данных характеристик
# ─────────────────────────────────────────────────────────────

_DB: list[CarSpec] = [

    # ── BMW 3 серия E36 (1990–2000) ────────────────────────────────────────
    CarSpec("BMW","316i","E36",1990,2000, 1596,"1.6L", 100, 74, 150,"petrol",4,"RWD"),
    CarSpec("BMW","318i","E36",1990,2000, 1796,"1.8L", 118, 87, 168,"petrol",4,"RWD"),
    CarSpec("BMW","320i","E36",1990,2000, 1991,"2.0L", 150,110, 190,"petrol",6,"RWD"),
    CarSpec("BMW","323i","E36",1994,2000, 2494,"2.5L", 170,125, 245,"petrol",6,"RWD"),
    CarSpec("BMW","325i","E36",1990,2000, 2494,"2.5L", 192,141, 245,"petrol",6,"RWD"),
    CarSpec("BMW","328i","E36",1994,2000, 2793,"2.8L", 193,142, 280,"petrol",6,"RWD"),
    CarSpec("BMW","M3",  "E36",1992,1999, 2990,"3.0L", 286,210, 320,"petrol",6,"RWD","Только МКПП 5/6 ст."),
    CarSpec("BMW","318tds","E36",1994,1998,1665,"1.7L",90, 66, 190,"diesel",4,"RWD"),
    CarSpec("BMW","325tds","E36",1991,2000,2503,"2.5L",143,105,260,"diesel",6,"RWD"),

    # ── BMW 3 серия E46 (1998–2006) ────────────────────────────────────────
    CarSpec("BMW","316i","E46",1998,2005, 1796,"1.8L", 115, 85, 165,"petrol",4,"RWD"),
    CarSpec("BMW","318i","E46",1998,2006, 1995,"2.0L", 143,105, 200,"petrol",4,"RWD"),
    CarSpec("BMW","320i","E46",1998,2006, 2171,"2.2L", 150,110, 210,"petrol",6,"RWD"),
    CarSpec("BMW","323i","E46",1998,2000, 2494,"2.5L", 170,125, 245,"petrol",6,"RWD"),
    CarSpec("BMW","325i","E46",2000,2006, 2494,"2.5L", 192,141, 245,"petrol",6,"RWD"),
    CarSpec("BMW","328i","E46",1998,2000, 2793,"2.8L", 193,142, 280,"petrol",6,"RWD"),
    CarSpec("BMW","330i","E46",2000,2006, 2979,"3.0L", 231,170, 300,"petrol",6,"RWD"),
    CarSpec("BMW","M3",  "E46",2000,2006, 3246,"3.2L", 343,252, 365,"petrol",6,"RWD","МКПП 6ст. или SMG"),
    CarSpec("BMW","316d","E46",2001,2005, 1995,"2.0L", 115, 85, 265,"diesel",4,"RWD"),
    CarSpec("BMW","318d","E46",1999,2006, 1995,"2.0L", 116, 85, 270,"diesel",4,"RWD"),
    CarSpec("BMW","320d","E46",1998,2006, 1995,"2.0L", 150,110, 330,"diesel",4,"RWD"),
    CarSpec("BMW","330d","E46",1999,2006, 2926,"3.0L", 204,150, 410,"diesel",6,"RWD"),

    # ── BMW 3 серия E90/E91/E92 (2005–2012) ────────────────────────────────
    CarSpec("BMW","316i","E90",2005,2012, 1596,"1.6L", 115, 85, 150,"petrol",4,"RWD"),
    CarSpec("BMW","318i","E90",2005,2012, 1995,"2.0L", 143,105, 190,"petrol",4,"RWD"),
    CarSpec("BMW","320i","E90",2005,2012, 1995,"2.0L", 163,120, 210,"petrol",4,"RWD"),
    CarSpec("BMW","323i","E90",2006,2011, 2494,"2.5L", 177,130, 230,"petrol",6,"RWD"),
    CarSpec("BMW","325i","E90",2005,2012, 2494,"2.5L", 218,160, 250,"petrol",6,"RWD"),
    CarSpec("BMW","328i","E90",2005,2012, 2996,"3.0L", 230,170, 270,"petrol",6,"RWD"),
    CarSpec("BMW","330i","E90",2005,2012, 2996,"3.0L", 258,190, 300,"petrol",6,"RWD"),
    CarSpec("BMW","335i","E90",2006,2012, 2979,"3.0L bi-turbo", 306,225, 400,"petrol",6,"RWD"),
    CarSpec("BMW","M3",  "E90",2007,2013, 3999,"4.0L V8",420,309, 400,"petrol",8,"RWD"),
    CarSpec("BMW","316d","E90",2008,2012, 1995,"2.0L", 116, 85, 260,"diesel",4,"RWD"),
    CarSpec("BMW","318d","E90",2005,2012, 1995,"2.0L", 143,105, 300,"diesel",4,"RWD"),
    CarSpec("BMW","320d","E90",2005,2012, 1995,"2.0L", 177,130, 350,"diesel",4,"RWD"),
    CarSpec("BMW","325d","E90",2006,2012, 2993,"3.0L", 197,145, 400,"diesel",6,"RWD"),
    CarSpec("BMW","330d","E90",2005,2012, 2993,"3.0L", 245,180, 500,"diesel",6,"RWD"),
    CarSpec("BMW","335d","E90",2007,2012, 2993,"3.0L bi-turbo", 286,210, 580,"diesel",6,"RWD"),

    # ── BMW 5 серия E60 (2003–2010) ────────────────────────────────────────
    CarSpec("BMW","520i","E60",2003,2010, 1995,"2.0L", 170,125, 210,"petrol",4,"RWD"),
    CarSpec("BMW","523i","E60",2005,2010, 2494,"2.5L", 177,130, 230,"petrol",6,"RWD"),
    CarSpec("BMW","525i","E60",2003,2010, 2494,"2.5L", 218,160, 250,"petrol",6,"RWD"),
    CarSpec("BMW","528i","E60",2007,2010, 2996,"3.0L", 234,172, 270,"petrol",6,"RWD"),
    CarSpec("BMW","530i","E60",2003,2010, 2996,"3.0L", 258,190, 300,"petrol",6,"RWD"),
    CarSpec("BMW","535i","E60",2004,2010, 2979,"3.0L bi-turbo", 306,225, 400,"petrol",6,"RWD"),
    CarSpec("BMW","545i","E60",2003,2005, 4398,"4.4L V8", 333,245, 450,"petrol",8,"RWD"),
    CarSpec("BMW","550i","E60",2005,2010, 4799,"4.8L V8", 367,270, 490,"petrol",8,"RWD"),
    CarSpec("BMW","520d","E60",2005,2010, 1995,"2.0L", 163,120, 340,"diesel",4,"RWD"),
    CarSpec("BMW","525d","E60",2003,2010, 2497,"2.5L", 197,145, 400,"diesel",6,"RWD"),
    CarSpec("BMW","530d","E60",2003,2010, 2993,"3.0L", 235,173, 500,"diesel",6,"RWD"),
    CarSpec("BMW","535d","E60",2004,2010, 2993,"3.0L bi-turbo", 286,210, 580,"diesel",6,"RWD"),

    # ── BMW X5 E53 (1999–2006) / E70 (2006–2013) ───────────────────────────
    CarSpec("BMW","X5 3.0i","E53",1999,2006, 2979,"3.0L", 231,170, 300,"petrol",6,"AWD"),
    CarSpec("BMW","X5 4.4i","E53",1999,2006, 4398,"4.4L V8", 286,210, 440,"petrol",8,"AWD"),
    CarSpec("BMW","X5 3.0d","E53",2001,2006, 2926,"3.0L", 218,160, 500,"diesel",6,"AWD"),
    CarSpec("BMW","X5 xDrive30i","E70",2006,2013, 2996,"3.0L", 272,200, 315,"petrol",6,"AWD"),
    CarSpec("BMW","X5 xDrive35i","E70",2006,2013, 2979,"3.0L bi-turbo", 306,225, 400,"petrol",6,"AWD"),
    CarSpec("BMW","X5 xDrive30d","E70",2006,2013, 2993,"3.0L", 245,180, 520,"diesel",6,"AWD"),
    CarSpec("BMW","X5 xDrive35d","E70",2007,2013, 2993,"3.0L bi-turbo", 286,210, 580,"diesel",6,"AWD"),

    # ── Mercedes-Benz C-класс W203 (2000–2007) ─────────────────────────────
    CarSpec("Mercedes-Benz","C180","W203",2000,2007, 1797,"1.8L", 129, 95, 180,"petrol",4,"RWD"),
    CarSpec("Mercedes-Benz","C200","W203",2000,2007, 1796,"1.8L kompressor", 163,120, 240,"petrol",4,"RWD"),
    CarSpec("Mercedes-Benz","C220","W203",2000,2007, 2148,"2.1L diesel",143,105, 315,"diesel",4,"RWD"),
    CarSpec("Mercedes-Benz","C240","W203",2000,2007, 2597,"2.6L V6", 170,125, 240,"petrol",6,"RWD"),
    CarSpec("Mercedes-Benz","C270","W203",2000,2007, 2685,"2.7L diesel",170,125, 400,"diesel",5,"RWD"),
    CarSpec("Mercedes-Benz","C320","W203",2000,2007, 3199,"3.2L V6", 218,160, 300,"petrol",6,"RWD"),
    CarSpec("Mercedes-Benz","C55 AMG","W203",2004,2007, 5439,"5.4L V8", 367,270, 510,"petrol",8,"RWD"),

    # ── Mercedes-Benz E-класс W211 (2002–2009) ─────────────────────────────
    CarSpec("Mercedes-Benz","E200","W211",2002,2009, 1796,"1.8L K",163,120, 230,"petrol",4,"RWD"),
    CarSpec("Mercedes-Benz","E220","W211",2002,2009, 2148,"2.1L CDI",150,110, 340,"diesel",4,"RWD"),
    CarSpec("Mercedes-Benz","E240","W211",2002,2005, 2597,"2.6L V6", 177,130, 240,"petrol",6,"RWD"),
    CarSpec("Mercedes-Benz","E270","W211",2002,2006, 2685,"2.7L CDI",177,130, 400,"diesel",5,"RWD"),
    CarSpec("Mercedes-Benz","E280","W211",2005,2009, 2996,"3.0L CDI",190,140, 440,"diesel",6,"RWD"),
    CarSpec("Mercedes-Benz","E320","W211",2002,2005, 3199,"3.2L V6", 224,165, 315,"petrol",6,"RWD"),
    CarSpec("Mercedes-Benz","E350","W211",2005,2009, 3498,"3.5L V6", 272,200, 350,"petrol",6,"RWD"),
    CarSpec("Mercedes-Benz","E500","W211",2002,2009, 4966,"5.0L V8", 306,225, 460,"petrol",8,"RWD"),
    CarSpec("Mercedes-Benz","E63 AMG","W211",2006,2009, 6208,"6.2L V8",514,378,630,"petrol",8,"RWD"),

    # ── Audi A4 B6/B7 (2001–2008) ──────────────────────────────────────────
    CarSpec("Audi","A4 1.6","B6",2001,2005, 1595,"1.6L", 102, 75, 148,"petrol",4,"FWD"),
    CarSpec("Audi","A4 1.8T","B6",2001,2005, 1781,"1.8T", 163,120, 225,"petrol",4,"FWD"),
    CarSpec("Audi","A4 2.0","B6",2001,2005, 1984,"2.0L", 131, 96, 195,"petrol",4,"FWD"),
    CarSpec("Audi","A4 2.0T","B7",2005,2008, 1984,"2.0 TFSI", 200,147, 280,"petrol",4,"FWD"),
    CarSpec("Audi","A4 3.0","B6",2001,2005, 2976,"3.0L V6", 220,162, 300,"petrol",6,"AWD"),
    CarSpec("Audi","A4 3.2","B7",2004,2008, 3123,"3.2 FSI", 255,188, 330,"petrol",6,"AWD"),
    CarSpec("Audi","A4 1.9 TDI","B6",2001,2005, 1896,"1.9 TDI", 130, 96, 285,"diesel",4,"FWD"),
    CarSpec("Audi","A4 2.0 TDI","B7",2004,2008, 1968,"2.0 TDI", 140,103, 320,"diesel",4,"FWD"),
    CarSpec("Audi","A4 2.5 TDI","B6",2001,2005, 2496,"2.5 TDI", 163,120, 350,"diesel",6,"AWD"),
    CarSpec("Audi","RS4","B7",2005,2008, 4163,"4.2 V8", 420,309, 430,"petrol",8,"AWD"),

    # ── Audi A6 C6 (2004–2011) ─────────────────────────────────────────────
    CarSpec("Audi","A6 2.0T","C6",2004,2011, 1984,"2.0 TFSI", 170,125, 280,"petrol",4,"FWD"),
    CarSpec("Audi","A6 2.4","C6",2004,2008, 2393,"2.4L V6", 177,130, 230,"petrol",6,"FWD"),
    CarSpec("Audi","A6 2.8","C6",2005,2011, 2773,"2.8 FSI", 210,154, 280,"petrol",6,"FWD"),
    CarSpec("Audi","A6 3.0T","C6",2008,2011, 2995,"3.0 TFSI", 290,213, 420,"petrol",6,"AWD"),
    CarSpec("Audi","A6 2.0 TDI","C6",2004,2011, 1968,"2.0 TDI", 140,103, 320,"diesel",4,"FWD"),
    CarSpec("Audi","A6 2.7 TDI","C6",2004,2011, 2698,"2.7 TDI", 190,140, 400,"diesel",6,"AWD"),
    CarSpec("Audi","A6 3.0 TDI","C6",2004,2011, 2967,"3.0 TDI", 225,165, 500,"diesel",6,"AWD"),

    # ── Volkswagen Golf 5 (2003–2008) / Golf 6 (2008–2013) ─────────────────
    CarSpec("Volkswagen","Golf 1.4","Golf 5",2003,2008, 1390,"1.4L", 80, 59, 132,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf 1.6","Golf 5",2003,2008, 1595,"1.6L", 102, 75, 148,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf 2.0","Golf 5",2003,2008, 1984,"2.0L", 115, 85, 175,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf 1.4 TSI","Golf 6",2008,2013, 1390,"1.4 TSI", 122, 90, 200,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf 2.0 GTI","Golf 5",2004,2008, 1984,"2.0 TFSI", 200,147, 280,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf 2.0 GTI","Golf 6",2008,2013, 1984,"2.0 TFSI", 210,154, 280,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Golf R32","Golf 5",2005,2008, 3189,"3.2 V6", 250,184, 320,"petrol",6,"AWD"),
    CarSpec("Volkswagen","Golf 1.9 TDI","Golf 5",2003,2008, 1896,"1.9 TDI", 105, 77, 250,"diesel",4,"FWD"),
    CarSpec("Volkswagen","Golf 2.0 TDI","Golf 5",2003,2008, 1968,"2.0 TDI", 140,103, 320,"diesel",4,"FWD"),
    CarSpec("Volkswagen","Golf 2.0 TDI","Golf 6",2008,2013, 1968,"2.0 TDI", 140,103, 320,"diesel",4,"FWD"),

    # ── Volkswagen Passat B6 (2005–2010) ───────────────────────────────────
    CarSpec("Volkswagen","Passat 1.6","B6",2005,2010, 1596,"1.6L", 102, 75, 148,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Passat 2.0 FSI","B6",2005,2010, 1984,"2.0 FSI", 150,110, 200,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Passat 2.0 TSI","B6",2005,2010, 1984,"2.0 TFSI", 200,147, 280,"petrol",4,"FWD"),
    CarSpec("Volkswagen","Passat 3.6 4Motion","B6",2007,2010, 3597,"3.6 V6", 300,221, 350,"petrol",6,"AWD"),
    CarSpec("Volkswagen","Passat 2.0 TDI","B6",2005,2010, 1968,"2.0 TDI", 140,103, 320,"diesel",4,"FWD"),
    CarSpec("Volkswagen","Passat 3.0 TDI","B6",2005,2010, 2967,"3.0 TDI", 225,165, 500,"diesel",6,"AWD"),

    # ── Toyota Camry XV40 (2006–2011) ──────────────────────────────────────
    CarSpec("Toyota","Camry 2.4","XV40",2006,2011, 2362,"2.4L", 163,120, 224,"petrol",4,"FWD"),
    CarSpec("Toyota","Camry 3.5","XV40",2006,2011, 3456,"3.5L V6", 277,204, 343,"petrol",6,"FWD"),

    # ── Toyota RAV4 XA30 (2005–2012) ───────────────────────────────────────
    CarSpec("Toyota","RAV4 2.0","XA30",2005,2012, 1987,"2.0L", 152,112, 200,"petrol",4,"AWD"),
    CarSpec("Toyota","RAV4 2.2 D-4D","XA30",2005,2012, 2231,"2.2L diesel",150,110, 340,"diesel",4,"AWD"),

    # ── Volvo XC90 (2002–2014) ─────────────────────────────────────────────
    CarSpec("Volvo","XC90 2.5T","I",2002,2014, 2521,"2.5T",210,154, 320,"petrol",5,"AWD"),
    CarSpec("Volvo","XC90 3.2","I",2006,2014, 3192,"3.2L",238,175, 320,"petrol",6,"AWD"),
    CarSpec("Volvo","XC90 T6","I",2002,2014, 2921,"2.9L bi-turbo",272,200, 380,"petrol",6,"AWD"),
    CarSpec("Volvo","XC90 D5","I",2002,2014, 2401,"2.4D",185,136, 420,"diesel",5,"AWD"),

    # ── Honda Accord 7 (2002–2008) ─────────────────────────────────────────
    CarSpec("Honda","Accord 2.0","VII",2002,2008, 1998,"2.0L",155,114, 192,"petrol",4,"FWD"),
    CarSpec("Honda","Accord 2.4","VII",2002,2008, 2354,"2.4L",190,140, 222,"petrol",4,"FWD"),
    CarSpec("Honda","Accord 3.0 V6","VII",2003,2008, 2997,"3.0L V6",240,177, 289,"petrol",6,"FWD"),
    CarSpec("Honda","Accord 2.2 CDTi","VII",2004,2008, 2204,"2.2L diesel",140,103, 340,"diesel",4,"FWD"),

    # ── Mazda 6 (GH, 2008–2012) ────────────────────────────────────────────
    CarSpec("Mazda","6 1.8","GH",2008,2012, 1798,"1.8L",120, 88, 164,"petrol",4,"FWD"),
    CarSpec("Mazda","6 2.0","GH",2008,2012, 1999,"2.0L",147,108, 185,"petrol",4,"FWD"),
    CarSpec("Mazda","6 2.5","GH",2008,2012, 2488,"2.5L",170,125, 226,"petrol",4,"FWD"),
    CarSpec("Mazda","6 2.2 MZR-CD","GH",2008,2012, 2184,"2.2L diesel",163,120, 380,"diesel",4,"FWD"),
]


# ─────────────────────────────────────────────────────────────
# Lookup
# ─────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return s.lower().strip().replace("-", " ").replace("_", " ")


def lookup(brand: str, model: str, year: Optional[int] = None) -> Optional[CarSpec]:
    """
    Поиск характеристик.
    brand — напр. "BMW" / "bmw"
    model — напр. "325i" / "325i E90" / "3 серия 325i"
    year  — опционально, уточняет поколение
    """
    nb = _normalize(brand)
    nm = _normalize(model)

    candidates: list[CarSpec] = []
    for spec in _DB:
        if _normalize(spec.brand) not in nb and nb not in _normalize(spec.brand):
            continue
        sm = _normalize(spec.model)
        # Ищем вхождение модели в поисковой строке или наоборот
        if sm in nm or nm in sm or nm.replace(" ", "") in sm.replace(" ", ""):
            candidates.append(spec)

    if not candidates:
        return None

    if year:
        # Ищем точное попадание по году
        exact = [c for c in candidates if c.year_from <= year <= c.year_to]
        if exact:
            return exact[0]

    # Возвращаем самую свежую версию
    return sorted(candidates, key=lambda c: c.year_from, reverse=True)[0]


def lookup_info_block(brand: str, model: str, year: Optional[int] = None) -> str:
    """
    Возвращает блок с характеристиками в формате Telegram HTML,
    или пустую строку если не нашли.
    """
    spec = lookup(brand, model, year)
    if not spec:
        return ""
    return "\n\n🔩 <b>Характеристики</b>\n" + spec.format_ru()
