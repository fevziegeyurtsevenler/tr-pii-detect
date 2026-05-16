"""TCKN tespit ve doğrulama testleri."""
from __future__ import annotations

import random

import pytest

from tr_pii_detect import find_tckn, is_valid_tckn
from tr_pii_detect.tckn import _TCKN_RE


def _generate_valid_tckn() -> str:
    """NVI algoritmasına uygun rastgele TCKN üret."""
    d = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(8)]
    odd = d[0] + d[2] + d[4] + d[6] + d[8]
    even = d[1] + d[3] + d[5] + d[7]
    d.append((odd * 7 - even) % 10)
    d.append(sum(d[:10]) % 10)
    return "".join(str(x) for x in d)


class TestIsValidTCKN:
    """Algoritma doğrulayıcı temel test cases."""

    def test_known_valid(self):
        # 10000000146 — yaygın olarak referans gösterilen geçerli test TCKN
        assert is_valid_tckn("10000000146") is True

    def test_self_consistency_100(self):
        """100 generated TCKN'in 100'ü de doğrulamadan geçmeli."""
        random.seed(42)
        for _ in range(100):
            t = _generate_valid_tckn()
            assert is_valid_tckn(t), f"Generated TCKN {t} failed validation"

    @pytest.mark.parametrize(
        "invalid",
        [
            "12345678901",
            "00000000000",   # ilk hane 0
            "10000000147",   # checksum bozuk
            "1234567890",    # 10 hane
            "123456789012",  # 12 hane
            "1000000014a",   # alphanumeric
            "",
            "abcdefghijk",
        ],
    )
    def test_invalid_inputs(self, invalid):
        assert is_valid_tckn(invalid) is False

    def test_first_digit_zero_rejected(self):
        # İlk hanesi 0 olan, başka türlü doğru görünen string
        assert is_valid_tckn("01234567890") is False

    def test_algorithmically_valid_but_synthetic(self):
        """11111111110 gibi tüm-aynı-rakam pattern'leri algoritmik olarak geçerli
        olabilir (NVI algoritması bunu engellemez). Kütüphane bunu rapor eder;
        pratik filtre uygulamak isteyen kullanıcı kendi katmanını ekleyebilir."""
        # NOT: 11111111110 → 10. hane: (5*1*7 - 4*1) mod 10 = 1, 11. hane: 10 mod 10 = 0 → valid
        assert is_valid_tckn("11111111110") is True


class TestFindTCKN:
    """Metin içinden tespit testleri."""

    def test_single_match(self):
        text = "Müşterinin TC kimlik numarası 10000000146 şeklindedir."
        hits = list(find_tckn(text))
        assert len(hits) == 1
        assert hits[0].value == "10000000146"
        assert hits[0].type == "tckn"
        assert hits[0].valid is True

    def test_position_correctness(self):
        text = "TC: 10000000146 son"
        hits = list(find_tckn(text))
        assert len(hits) == 1
        h = hits[0]
        assert text[h.start : h.end] == "10000000146"

    def test_multiple_matches(self):
        random.seed(1)
        t1 = _generate_valid_tckn()
        t2 = _generate_valid_tckn()
        text = f"Birinci: {t1}, ikinci: {t2}"
        hits = list(find_tckn(text))
        assert len(hits) == 2
        values = {h.value for h in hits}
        assert values == {t1, t2}

    def test_no_match_in_longer_number(self):
        """12 hane veya daha uzun rakam dizisi içinde TCKN yakalanmamalı."""
        text = "Barkod: 1000000014612345"  # 11 hane + 5 hane bitişik
        hits = list(find_tckn(text))
        assert len(hits) == 0

    def test_no_match_for_invalid_checksum(self):
        text = "Belge no: 12345678901"
        hits = list(find_tckn(text))
        assert len(hits) == 0

    def test_match_at_text_boundary(self):
        random.seed(2)
        t = _generate_valid_tckn()
        # Başta
        hits1 = list(find_tckn(f"{t} ile başlar"))
        assert len(hits1) == 1
        # Sonda
        hits2 = list(find_tckn(f"sonu {t}"))
        assert len(hits2) == 1
        # Tek başına
        hits3 = list(find_tckn(t))
        assert len(hits3) == 1
