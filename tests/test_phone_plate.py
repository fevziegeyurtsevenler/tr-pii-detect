"""Telefon ve plaka format tespiti testleri."""
from __future__ import annotations

import pytest

from tr_pii_detect import (
    find_phone,
    find_plate,
    is_valid_plate,
    is_valid_tr_mobile,
)


class TestPhone:
    @pytest.mark.parametrize(
        "phone,expected_value",
        [
            ("0532 123 45 67", "5321234567"),
            ("0532-123-45-67", "5321234567"),
            ("05321234567", "5321234567"),
            ("+90 532 123 45 67", "5321234567"),
            ("+905321234567", "5321234567"),
            ("(0532) 123 45 67", "5321234567"),
        ],
    )
    def test_format_variants(self, phone, expected_value):
        hits = list(find_phone(phone))
        assert len(hits) == 1, f"No match for {phone!r}"
        assert hits[0].value == expected_value
        assert hits[0].meta["operator_known"] is True
        assert hits[0].meta["country"] == "TR"

    def test_unknown_operator_still_matched(self):
        # 599 — bilinmeyen prefix; format yine geçerli kabul
        text = "+90 599 123 45 67"
        hits = list(find_phone(text))
        assert len(hits) == 1
        assert hits[0].meta["operator_known"] is False

    def test_no_match_for_landline(self):
        """0212 (sabit telefon) mobil olarak yakalanmamalı."""
        text = "Sabit: 0212 123 45 67"
        hits = list(find_phone(text))
        assert len(hits) == 0

    def test_multiple_phones(self):
        text = "Aramalar: 0532 111 22 33, 0533 444 55 66"
        hits = list(find_phone(text))
        assert len(hits) == 2


class TestPlate:
    @pytest.mark.parametrize(
        "plate",
        [
            "06 ABC 123",   # standart 3+3 — 8 karakter
            "34 AB 1234",   # 2+4 — 8 karakter
            "01 A 1234",    # 1+4 — 7 karakter
            "35 ABC 12",    # 3+2 — 7 karakter
            "81 PR 999",    # 2+3 — 7 karakter
        ],
    )
    def test_valid_plates(self, plate):
        assert is_valid_plate(plate) is True

    @pytest.mark.parametrize(
        "plate",
        [
            "00 ABC 123",     # il kodu 00 geçersiz
            "82 ABC 123",     # 82 il yok
            "06 QWX 123",     # Q,W,X harfleri geçersiz
            "06 ABC 1",       # toplam 6 karakter, çok kısa (2+3+1)
            "35 ABCD 1234",   # harf bloğu 4 — geçersiz (max 3)
            "06 AB 1",        # toplam 5 karakter, çok kısa
            "",
            "ABC 06 123",     # sıra yanlış
        ],
    )
    def test_invalid_plates(self, plate):
        assert is_valid_plate(plate) is False

    def test_find_plate_in_text(self):
        text = "Aracın plakası 06 ABC 123 olarak kayıtlı."
        hits = list(find_plate(text))
        assert len(hits) == 1
        assert hits[0].meta["province_code"] == "06"
        assert hits[0].meta["letters"] == "ABC"
        assert hits[0].meta["digits"] == "123"

    def test_normalized_value_has_spaces(self):
        text = "Plaka: 34AB1234"
        hits = list(find_plate(text))
        assert len(hits) == 1
        assert hits[0].value == "34 AB 1234"

    def test_no_match_for_invalid_letters(self):
        text = "Kod: 06 QWX 123"
        hits = list(find_plate(text))
        assert len(hits) == 0
