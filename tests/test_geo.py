"""Unit tests for geo.py (distance calculation + city lookup)."""
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import geo


class TestHaversine:
    def test_same_point(self):
        """Distance from a point to itself is 0."""
        d = geo.haversine_km(56.9460, 24.1059, 56.9460, 24.1059)
        assert d == 0.0

    def test_riga_jelgava(self):
        """Rīga → Jelgava ≈ 42 km."""
        d = geo.haversine_km(56.9460, 24.1059, 56.6511, 23.7234)
        assert 38 <= d <= 48, f"Expected ~42 km, got {d:.1f}"

    def test_riga_daugavpils(self):
        """Rīga → Daugavpils straight line ≈ 191 km."""
        d = geo.haversine_km(56.9460, 24.1059, 55.8770, 26.5355)
        assert 175 <= d <= 210, f"Expected ~191 km, got {d:.1f}"

    def test_riga_liepaja(self):
        """Rīga → Liepāja straight line ≈ 173 km."""
        d = geo.haversine_km(56.9460, 24.1059, 56.5047, 21.0107)
        assert 155 <= d <= 205, f"Expected ~195 km, got {d:.1f}"

    def test_riga_ventspils(self):
        """Rīga → Ventspils straight line ≈ 161 km."""
        d = geo.haversine_km(56.9460, 24.1059, 57.3944, 21.5607)
        assert 145 <= d <= 180, f"Expected ~161 km, got {d:.1f}"

    def test_symmetry(self):
        """Distance A→B == B→A."""
        d1 = geo.haversine_km(56.9460, 24.1059, 56.5047, 21.0107)
        d2 = geo.haversine_km(56.5047, 21.0107, 56.9460, 24.1059)
        assert abs(d1 - d2) < 0.001

    def test_positive(self):
        """Distance is always non-negative."""
        d = geo.haversine_km(55.0, 23.0, 57.0, 26.0)
        assert d >= 0


class TestCityCoords:
    def test_riga_latvian(self):
        c = geo.city_coords("Rīga")
        assert c is not None
        lat, lon = c
        assert abs(lat - 56.9460) < 0.01
        assert abs(lon - 24.1059) < 0.01

    def test_riga_russian(self):
        c = geo.city_coords("Рига")
        assert c is not None

    def test_riga_ascii(self):
        c = geo.city_coords("Riga")
        assert c is not None

    def test_jelgava(self):
        c = geo.city_coords("Jelgava")
        assert c is not None
        assert abs(c[0] - 56.6511) < 0.01

    def test_daugavpils_ru(self):
        c = geo.city_coords("Даугавпилс")
        assert c is not None

    def test_unknown_city(self):
        c = geo.city_coords("Nonexistent City XYZ")
        assert c is None

    def test_empty(self):
        assert geo.city_coords("") is None
        assert geo.city_coords(None) is None

    def test_case_insensitive(self):
        c1 = geo.city_coords("RIGA")
        c2 = geo.city_coords("riga")
        c3 = geo.city_coords("Riga")
        assert c1 == c2 == c3

    def test_liepaja_latvian(self):
        c = geo.city_coords("Liepāja")
        assert c is not None

    def test_liepaja_ascii(self):
        c = geo.city_coords("Liepaja")
        assert c is not None

    def test_valmiera(self):
        c = geo.city_coords("Valmiera")
        assert c is not None


class TestFormatDistance:
    def test_less_than_1km(self):
        assert "< 1" in geo.format_distance(0.3)

    def test_exact_km(self):
        result = geo.format_distance(43.0)
        assert "43" in result
        assert "км" in result

    def test_rounding(self):
        result = geo.format_distance(43.6)
        assert "44" in result

    def test_thousands(self):
        result = geo.format_distance(1500.0)
        assert "тыс" in result


class TestNearestCity:
    def test_riga_center(self):
        name = geo.nearest_city(56.9460, 24.1059)
        assert name is not None
        assert "rig" in name.lower() or "рига" in name.lower() or "Rīga" in name

    def test_jelgava_center(self):
        name = geo.nearest_city(56.6511, 23.7234)
        assert name is not None
        assert "jelgava" in name.lower() or "елгава" in name.lower()

    def test_far_outside_latvia(self):
        # Moscow - more than 80 km from any Latvian city
        name = geo.nearest_city(55.7558, 37.6176, limit_km=80)
        assert name is None


class TestParseDateStr:
    """Tests for parser.parse_date_str()."""
    def setup_method(self):
        import parser as p
        self.parse = p.parse_date_str

    def test_today_russian(self):
        result = self.parse("сегодня 14:23")
        assert "Сегодня" in result
        assert "14:23" in result

    def test_today_latvian(self):
        result = self.parse("šodien 16:45")
        assert "Сегодня" in result
        assert "16:45" in result

    def test_yesterday_russian(self):
        result = self.parse("вчера 09:05")
        assert "Вчера" in result
        assert "09:05" in result

    def test_yesterday_latvian(self):
        result = self.parse("vakar 21:00")
        assert "Вчера" in result

    def test_full_date(self):
        result = self.parse("25.05.2026")
        assert "25" in result
        assert "мая" in result

    def test_short_date(self):
        result = self.parse("10.03.")
        assert "10" in result
        assert "мар" in result

    def test_empty(self):
        assert self.parse("") == ""

    def test_passthrough(self):
        # Unknown format returns as-is
        result = self.parse("unknown format")
        assert result == "unknown format"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
