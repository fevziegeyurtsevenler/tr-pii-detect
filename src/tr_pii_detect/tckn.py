"""TC Kimlik Numarası (TCKN) algoritma doğrulamalı tespit.

TCKN 11 haneli bir Türkiye Cumhuriyeti vatandaşlık numarasıdır.
NVI (Nüfus ve Vatandaşlık İşleri) tarafından tanımlanan kurallar:

    1. Tam olarak 11 hane (yalnızca rakam).
    2. İlk hane 0 olamaz.
    3. 10. hane = ((1+3+5+7+9. hanelerin toplamı) * 7
                  - (2+4+6+8. hanelerin toplamı)) mod 10
    4. 11. hane = ilk 10 hanenin toplamının mod 10'u.

Yalnızca regex eşleşmesi (`\\d{11}`) yetersiz: müşteri ID, sipariş
numarası, telefon numarası gibi 11 haneli sayılar yanlış pozitif üretir.
Algoritma doğrulaması yanlış pozitifleri ~%99 azaltır.
"""
from __future__ import annotations

import re
from typing import Iterator

from .types import PIIMatch

# Kelime sınırı içinde tam 11 hane. Aradaki boşluk/tire kabul edilmez —
# TCKN her zaman bitişik yazılır.
_TCKN_RE = re.compile(r"(?<!\d)(\d{11})(?!\d)")


def is_valid_tckn(value: str) -> bool:
    """11 hane string'in geçerli bir TCKN olup olmadığını döndür.

    >>> is_valid_tckn("10000000146")
    True
    >>> is_valid_tckn("12345678901")
    False
    >>> is_valid_tckn("00000000000")
    False
    """
    if not value or len(value) != 11 or not value.isdigit():
        return False

    digits = [int(c) for c in value]

    # Kural 2: ilk hane 0 olamaz.
    if digits[0] == 0:
        return False

    # Kural 3: 10. hane (index 9) kontrolü.
    odd_sum = digits[0] + digits[2] + digits[4] + digits[6] + digits[8]
    even_sum = digits[1] + digits[3] + digits[5] + digits[7]
    check_10 = (odd_sum * 7 - even_sum) % 10
    if check_10 != digits[9]:
        return False

    # Kural 4: 11. hane (index 10) kontrolü.
    check_11 = sum(digits[:10]) % 10
    if check_11 != digits[10]:
        return False

    return True


def find_tckn(text: str) -> Iterator[PIIMatch]:
    """Metindeki tüm geçerli TCKN'leri yield et."""
    for m in _TCKN_RE.finditer(text):
        candidate = m.group(1)
        if is_valid_tckn(candidate):
            yield PIIMatch(
                type="tckn",
                value=candidate,
                start=m.start(1),
                end=m.end(1),
                valid=True,
            )
