"""Türkiye araç plakası format tespiti.

Türkiye plaka formatı (Karayolları Trafik Yönetmeliği):
    İl kodu (01-81) + 1-3 harf + 2-4 rakam
    Toplam karakter sayısı 7-8 (boşluksuz)

    Örnekler:
        06 ABC 123        # Ankara
        34 AB 1234        # İstanbul
        16 A 12345        # Bursa (eski format, nadir)
        35 ABCD 12        # İzmir

Geçerli harf seti: TR plakalarında Türkçe-spesifik harfler (Ç, Ş, Ğ, İ, Ö, Ü)
**kullanılmaz**. Sadece basic Latin: A-Z eksi Q, W, X.

Bu modül **format kontrolü** ve **il kodu doğrulaması** yapar.
İl kodu 01-81 aralığında olmalı (Türkiye 81 il).
"""
from __future__ import annotations

import re
from typing import Iterator

from .types import PIIMatch

# İl kodu 01-81, harf bloğu 1-3 karakter (Q,W,X hariç), rakam bloğu 2-4 hane.
# Aralarda opsiyonel boşluk veya tire kabul edilir.
_PLATE_RE = re.compile(
    r"(?<![A-Z0-9])"
    r"(0[1-9]|[1-7]\d|8[01])"          # il kodu 01-81
    r"[\s\-]?"
    r"([A-PR-VYZ]{1,3})"               # harf bloğu (Q,W,X yok)
    r"[\s\-]?"
    r"(\d{2,4})"                       # rakam bloğu
    r"(?![A-Z0-9])",
    re.IGNORECASE,
)


def is_valid_plate(value: str) -> bool:
    """Plaka string'in TR plaka formatına uyup uymadığını kontrol et."""
    cleaned = re.sub(r"[\s\-]+", "", value).upper()
    m = re.fullmatch(
        r"(0[1-9]|[1-7]\d|8[01])([A-PR-VYZ]{1,3})(\d{2,4})",
        cleaned,
    )
    if not m:
        return False
    # Toplam karakter sayısı 7-8 olmalı (Karayolları Trafik Yönetmeliği)
    total_len = len(m.group(1)) + len(m.group(2)) + len(m.group(3))
    return 7 <= total_len <= 8


def find_plate(text: str) -> Iterator[PIIMatch]:
    """Metindeki TR araç plakalarını yield et."""
    for m in _PLATE_RE.finditer(text):
        raw = m.group(0)
        province = m.group(1)
        letters = m.group(2).upper()
        digits = m.group(3)
        normalized = f"{province} {letters} {digits}"
        total_len = len(province) + len(letters) + len(digits)
        if not (7 <= total_len <= 8):
            continue
        yield PIIMatch(
            type="plate",
            value=normalized,
            start=m.start(),
            end=m.end(),
            valid=True,
            meta={
                "raw": raw,
                "province_code": province,
                "letters": letters,
                "digits": digits,
            },
        )
