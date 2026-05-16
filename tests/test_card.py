"""Kredi/banka kartı Luhn doğrulama testleri."""
from __future__ import annotations

import pytest

from tr_pii_detect import find_card, luhn_check


class TestLuhn:
    @pytest.mark.parametrize(
        "card",
        [
            "4532015112830366",   # Visa
            "4111111111111111",   # Visa test
            "5555555555554444",   # MC test
            "378282246310005",    # Amex (15 hane)
            "6011111111111117",   # Discover test
        ],
    )
    def test_known_valid(self, card):
        assert luhn_check(card) is True

    @pytest.mark.parametrize(
        "card",
        [
            "4532015112830367",
            "1234567890123456",
            "0000000000000000",   # degenerate; reddedilmeli
            "1111111111111111",   # degenerate
            "",
            "12",
            "abcd123456789012",
        ],
    )
    def test_invalid(self, card):
        assert luhn_check(card) is False


class TestFindCard:
    def test_spaced_visa(self):
        text = "Kart: 4111 1111 1111 1111 son kullanma 12/27"
        hits = list(find_card(text))
        assert len(hits) == 1
        assert hits[0].value == "4111111111111111"
        assert hits[0].meta["brand"] == "visa"

    def test_hyphenated_mc(self):
        text = "MC kart: 5555-5555-5555-4444"
        hits = list(find_card(text))
        assert len(hits) == 1
        assert hits[0].meta["brand"] == "mastercard"

    def test_amex_15_digits(self):
        text = "Amex: 378282246310005"
        hits = list(find_card(text))
        assert len(hits) == 1
        assert hits[0].meta["brand"] == "amex"

    def test_ignores_invalid_luhn(self):
        text = "Bozuk kart no: 1234567890123456"
        hits = list(find_card(text))
        assert len(hits) == 0

    def test_compact_format(self):
        text = "4111111111111111"
        hits = list(find_card(text))
        assert len(hits) == 1
