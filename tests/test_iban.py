"""IBAN tespit ve MOD-97 doğrulama testleri."""
from __future__ import annotations

import pytest

from tr_pii_detect import find_iban, is_valid_iban


class TestIsValidIBAN:
    """ISO 7064 MOD-97 doğrulayıcı test cases."""

    @pytest.mark.parametrize(
        "iban",
        [
            "TR330006100519786457841326",
            "TR33 0006 1005 1978 6457 8413 26",
            "tr33 0006 1005 1978 6457 8413 26",
            "TR33-0006-1005-1978-6457-8413-26",
            "GB82WEST12345698765432",
            "DE89370400440532013000",
            "FR1420041010050500013M02606",
            "NL91ABNA0417164300",
        ],
    )
    def test_known_valid(self, iban):
        assert is_valid_iban(iban) is True

    @pytest.mark.parametrize(
        "iban",
        [
            "TR340006100519786457841326",  # checksum bozuk
            "TR33000610051978645784132",   # eksik hane
            "TR3300061005197864578413266", # fazla hane
            "XX330006100519786457841326",  # geçersiz ülke
            "TR",
            "",
            "1234567890",
        ],
    )
    def test_invalid_iban(self, iban):
        assert is_valid_iban(iban) is False


class TestFindIBAN:
    """Metinden IBAN çıkarma testleri."""

    def test_compact_format(self):
        text = "IBAN: TR330006100519786457841326 olarak gönderildi."
        hits = list(find_iban(text))
        assert len(hits) == 1
        assert hits[0].value == "TR330006100519786457841326"
        assert hits[0].meta["bank_code"] == "00061"

    def test_spaced_format(self):
        text = "IBAN: TR33 0006 1005 1978 6457 8413 26"
        hits = list(find_iban(text))
        assert len(hits) == 1
        assert hits[0].value == "TR330006100519786457841326"

    def test_hyphenated_format(self):
        text = "IBAN: TR33-0006-1005-1978-6457-8413-26"
        hits = list(find_iban(text))
        assert len(hits) == 1

    def test_multiple_ibans(self):
        text = (
            "Ana hesap: TR33 0006 1005 1978 6457 8413 26\n"
            "Yedek hesap: TR330006100519786457841326"
        )
        hits = list(find_iban(text))
        assert len(hits) == 2

    def test_ignores_invalid_checksum(self):
        text = "Bozuk IBAN: TR340006100519786457841326"
        hits = list(find_iban(text))
        assert len(hits) == 0

    def test_position_correctness(self):
        text = "IBAN: TR330006100519786457841326 bittirdik"
        hits = list(find_iban(text))
        assert len(hits) == 1
        h = hits[0]
        assert text[h.start : h.end] == "TR330006100519786457841326"

    def test_meta_contains_bank_code(self):
        text = "TR330006100519786457841326"
        hits = list(find_iban(text))
        assert hits[0].meta["country"] == "TR"
        assert hits[0].meta["bank_code"] == "00061"  # Ziraat Bankası kodu
