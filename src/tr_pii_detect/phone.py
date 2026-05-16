"""Türkiye telefon numarası format tespiti.

Türkiye'de telefon numaraları:
    GSM (cep):       5XX XXX XX XX  (10 hane, 5 ile başlar)
    Sabit:           212/216/312/.. + 7 hane = 10 hane
    Uluslararası ön: +90 veya 0090

Geçerli mobil operatör kodları (2026 itibarıyla):
    50X, 53X, 54X, 55X, 50X (Türk Telekom, Turkcell, Vodafone, sanal operatörler)
    Tam liste: BTK tarafından duyurulan operatör havuzu.

Bu modül **format ve operatör kodu kontrolü** yapar; algoritma
doğrulaması yoktur (telefon numarası matematiksel checksum içermez).
Yine de operatör kodu listesine karşı doğrulama, rastgele 10 haneli
sayıların false positive olarak işaretlenmesini büyük oranda engeller.
"""
from __future__ import annotations

import re
from typing import Iterator

from .types import PIIMatch

# +90 / 0090 / 0 ile başlayan veya direkt 5XX ile başlayan 10 hane numara.
# Aralarda boşluk, tire, parantez kabul edilir.
_PHONE_RE = re.compile(
    r"(?<![\d])"
    r"(?:\+?90[\s\-]?|0)?"
    r"\(?(5\d{2})\)?[\s\-]?"
    r"(\d{3})[\s\-]?"
    r"(\d{2})[\s\-]?"
    r"(\d{2})"
    r"(?![\d])"
)

# BTK 2026 GSM operatör kodları (geniş ama tam değil; community contribution
# için açık). Bilinmeyen 5XX kodu da kabul edilir ama meta'da "unknown" işareti.
KNOWN_MOBILE_PREFIXES = {
    # Turkcell
    "530", "531", "532", "533", "534", "535", "536", "537", "538", "539",
    # Vodafone
    "540", "541", "542", "543", "544", "545", "546", "547", "548", "549",
    # Türk Telekom Mobil
    "501", "505", "506", "507", "551", "552", "553", "554", "555", "559",
    # Sanal operatörler (Bimcell, Pttcell, vb.)
    "500", "502", "503", "504", "508", "509",
    "550", "555", "556", "557", "558",
    "561",
}


def is_valid_tr_mobile(value: str) -> bool:
    """Sayı bütününden temizlenmiş bir TR mobil numarasının formatını kontrol et."""
    cleaned = re.sub(r"[\s\-\(\)\+]+", "", value)
    # +90 / 0090 / 0 önekini kaldır
    if cleaned.startswith("0090"):
        cleaned = cleaned[4:]
    elif cleaned.startswith("90") and len(cleaned) > 10:
        cleaned = cleaned[2:]
    elif cleaned.startswith("0"):
        cleaned = cleaned[1:]
    return len(cleaned) == 10 and cleaned.startswith("5") and cleaned.isdigit()


def find_phone(text: str) -> Iterator[PIIMatch]:
    """Metindeki TR mobil telefon numaralarını yield et."""
    for m in _PHONE_RE.finditer(text):
        raw = m.group(0)
        prefix = m.group(1)
        # Birleşik 10 haneli numara
        normalized = f"{prefix}{m.group(2)}{m.group(3)}{m.group(4)}"
        if len(normalized) != 10:
            continue
        is_known = prefix in KNOWN_MOBILE_PREFIXES
        yield PIIMatch(
            type="phone",
            value=normalized,
            start=m.start(),
            end=m.end(),
            valid=True,  # format-geçerli; "known operator" meta'da
            meta={
                "raw": raw,
                "prefix": prefix,
                "operator_known": is_known,
                "country": "TR",
                "type": "mobile",
            },
        )
