"""VKN tespit ve GİB checksum doğrulama testleri."""
from __future__ import annotations

import random

import pytest

from tr_pii_detect import find_vkn, is_valid_vkn


def _generate_valid_vkn() -> str:
    """GİB algoritmasına göre rastgele geçerli VKN üret."""
    d = [random.randint(0, 9) for _ in range(9)]
    total = 0
    for i in range(9):
        tmp = (d[i] + (9 - i)) % 10
        v = (tmp * pow(2, 9 - i)) % 9
        if tmp != 0 and v == 0:
            v = 9
        total += v
    check = (10 - (total % 10)) % 10
    return "".join(str(x) for x in d) + str(check)


def _reference_validate(kno: str) -> bool:
    """Bağımsız kanonik referans implementasyon (atagulalan, gist).

    Cross-check için kullanılır.
    """
    if len(kno) != 10 or not kno.isdigit():
        return False
    last = int(kno[9])
    v = []
    for i in range(9):
        tmp = (int(kno[i]) + (9 - i)) % 10
        vi = (tmp * (2 ** (9 - i))) % 9
        if tmp != 0 and vi == 0:
            vi = 9
        v.append(vi)
    s = sum(v) % 10
    return (10 - (s % 10)) % 10 == last


class TestIsValidVKN:
    def test_self_consistency(self):
        random.seed(42)
        for _ in range(200):
            v = _generate_valid_vkn()
            assert is_valid_vkn(v), f"Generated VKN failed: {v}"

    def test_cross_check_with_reference(self):
        """Random sample üzerinde kütüphane çıktısı kanonik referansa eşit."""
        random.seed(7)
        for _ in range(5000):
            s = "".join(str(random.randint(0, 9)) for _ in range(10))
            assert is_valid_vkn(s) == _reference_validate(s), s

    @pytest.mark.parametrize(
        "invalid",
        [
            "0000000000",
            "9999999999",
            "1",
            "",
            "abcdefghij",
            "12345",
            "12345678901",  # 11 hane
        ],
    )
    def test_invalid_inputs(self, invalid):
        # Hepsi açıkça invalid (boş, hatalı uzunluk, vb).
        # Not: 1234567890 algoritmik olarak geçerli bir VKN'dir; bu yüzden
        # negatif testten çıkarılmıştır (cross-check ile doğrulanmıştır).
        assert is_valid_vkn(invalid) is False

    def test_known_algorithmically_valid_number(self):
        """1234567890 algoritmik olarak geçerli bir VKN — kanonik referansla
        doğrulandı. Pratik bir vergi numarası olmayabilir ama format-uyumlu."""
        assert is_valid_vkn("1234567890") is True


class TestFindVKN:
    def test_single_match(self):
        random.seed(123)
        v = _generate_valid_vkn()
        text = f"Şirket VKN'si {v} olarak kayıtlıdır."
        hits = list(find_vkn(text))
        assert len(hits) == 1
        assert hits[0].value == v

    def test_no_match_for_random_10_digits(self):
        # 9999999999 — algoritmik olarak invalid (kanonik referansla doğrulandı)
        text = "Doküman numarası: 9999999999"
        hits = list(find_vkn(text))
        assert len(hits) == 0

    def test_multiple_vkns(self):
        random.seed(456)
        v1 = _generate_valid_vkn()
        v2 = _generate_valid_vkn()
        text = f"Şirket A: {v1}, Şirket B: {v2}"
        hits = list(find_vkn(text))
        assert len(hits) == 2
