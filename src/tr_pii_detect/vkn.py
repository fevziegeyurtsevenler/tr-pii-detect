"""VKN (Vergi Kimlik Numarası) algoritma doğrulamalı tespit.

VKN, Türkiye'de tüzel kişilere atanan 10 haneli vergi numarasıdır.
Gelir İdaresi Başkanlığı (GİB) tarafından tanımlanan kanonik algoritma
(0-indexed):

    d[i]: VKN'nin i'inci hanesi (i=0..8 baz, i=9 kontrol)

    tmp = (d[i] + (9 - i)) mod 10
    v[i] = (tmp * 2^(9-i)) mod 9
    Eğer tmp != 0 ve v[i] == 0:  v[i] = 9
    Toplam = Σ v[i]
    Kontrol = (10 - (Toplam mod 10)) mod 10
    Kontrol == d[9] olmalı.

Referans implementasyon: gist.github.com/ziyahan/3938729 (atagulalan'ın
yorumdaki düzenlenmiş versiyonu).

Yalnızca regex (`\\d{10}`) yetersizdir — telefon, sipariş ID,
müşteri numarası gibi 10 haneli stringler yanlış pozitif üretir.
Algoritma doğrulaması yanlış pozitif oranını %90+ düşürür.
"""
from __future__ import annotations

import re
from typing import Iterator

from .types import PIIMatch

_VKN_RE = re.compile(r"(?<!\d)(\d{10})(?!\d)")


def is_valid_vkn(value: str) -> bool:
    """10 haneli string'in geçerli bir VKN olup olmadığını döndür."""
    if not value or len(value) != 10 or not value.isdigit():
        return False

    digits = [int(c) for c in value]
    total = 0
    for i in range(9):
        tmp = (digits[i] + (9 - i)) % 10
        v = (tmp * pow(2, 9 - i)) % 9
        if tmp != 0 and v == 0:
            v = 9
        total += v

    check = (10 - (total % 10)) % 10
    return check == digits[9]


def find_vkn(text: str) -> Iterator[PIIMatch]:
    """Metindeki tüm geçerli VKN'leri yield et."""
    for m in _VKN_RE.finditer(text):
        candidate = m.group(1)
        if is_valid_vkn(candidate):
            yield PIIMatch(
                type="vkn",
                value=candidate,
                start=m.start(1),
                end=m.end(1),
                valid=True,
            )
