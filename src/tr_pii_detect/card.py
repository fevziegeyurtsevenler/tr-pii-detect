"""Kredi/banka kartı numarası Luhn algoritmalı tespit.

Luhn (mod-10) algoritması ISO/IEC 7812 ile tanımlıdır.
Kart numaraları 13-19 hane arasındadır (yaygın olarak 16).

Algoritma:
    1. Sağdan sola doğru, çift pozisyondaki haneleri 2 ile çarp.
    2. Çarpım 9'dan büyükse iki hanesini topla (ya da -9 yap).
    3. Tüm haneleri topla. Toplam mod 10 == 0 olmalı.

Bu kütüphane KART NUMARASINI MASKELER VE LOGLAMAZ.
Asla ham kart numarasını dış bir sisteme göndermez.
"""
from __future__ import annotations

import re
from typing import Iterator, Optional

from .types import PIIMatch

# 13-19 hane, aralarda opsiyonel boşluk veya tire. Negatif lookbehind/ahead
# ile uzun rakam dizilerinin (örn. 20+ haneli barkod, ID) ortasından yakalama.
_CARD_RE = re.compile(
    r"(?<!\d)(?:\d[\s\-]?){12,18}\d(?!\d)"
)


def luhn_check(number: str) -> bool:
    """Saf rakam string'i için Luhn (mod-10) checksum.

    >>> luhn_check("4532015112830366")
    True
    >>> luhn_check("4532015112830367")
    False
    >>> luhn_check("0000000000000000")  # degenerate; reddedilir
    False
    """
    if not number or not number.isdigit() or len(number) < 13 or len(number) > 19:
        return False
    # Degenerate case: tüm aynı hane veya tüm sıfır. Matematiksel olarak Luhn
    # geçer ama gerçek kart numarası değildir.
    if len(set(number)) == 1:
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _detect_brand(number: str) -> Optional[str]:
    """Kart numarasından markayı bul (visa, mastercard, amex, troy, ...)."""
    if not number or not number.isdigit():
        return None
    n = number
    # Troy (TR yerli): 9792 başlıkları, ayrıca BIN aralıkları
    if n.startswith("9792") or n.startswith("65"):
        return "troy"
    if n.startswith("4"):
        return "visa"
    if n[:2] in {"34", "37"}:
        return "amex"
    if n[:2] in {"51", "52", "53", "54", "55"}:
        return "mastercard"
    # MC 2-series: 2221-2720
    if len(n) >= 4:
        prefix4 = int(n[:4])
        if 2221 <= prefix4 <= 2720:
            return "mastercard"
    if n.startswith("6011") or n.startswith("65"):
        return "discover"
    return None


def find_card(text: str) -> Iterator[PIIMatch]:
    """Metindeki Luhn-geçerli kart numaralarını yield et."""
    for m in _CARD_RE.finditer(text):
        raw = m.group(0)
        digits_only = re.sub(r"[\s\-]+", "", raw)
        if not luhn_check(digits_only):
            continue
        brand = _detect_brand(digits_only)
        yield PIIMatch(
            type="card",
            value=digits_only,
            start=m.start(),
            end=m.end(),
            valid=True,
            meta={"brand": brand, "raw": raw, "length": len(digits_only)},
        )
