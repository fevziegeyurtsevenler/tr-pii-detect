"""IBAN (International Bank Account Number) algoritma doğrulamalı tespit.

ISO 13616 standardı, MOD-97 checksum (ISO 7064:2003).
Türk IBAN'ları "TR" ile başlar ve 26 karakter uzunluğundadır:

    TR  KK  BBBBB  R  CCCCCCCCCCCCCCCC
    |   |   |      |  |
    |   |   |      |  └ Hesap numarası (16 hane)
    |   |   |      └─── Rezerv hanesi (1 hane, genelde 0)
    |   |   └────────── Banka kodu (5 hane)
    |   └────────────── Kontrol haneleri (2 hane)
    └────────────────── Ülke kodu (TR)

Doğrulama:
    1. Ülke kodu + kontrol haneleri sona taşı: BBAN + TR + KK
    2. Harfleri sayıya çevir: A=10, B=11, ..., Z=35 (T=29, R=27)
    3. Sonucun MOD 97'si **1** olmalı.

Varsayılan olarak yalnızca TR IBAN'larını tespit eder; `accept_all=True`
geçilirse tüm ülkelerden IBAN'ı kabul eder (boyut tablosuna göre).
"""
from __future__ import annotations

import re
from typing import Iterator

from .types import PIIMatch

# TR ile başlayan IBAN aday'ları. TR + 24 hane = 26 karakter toplam.
# Hem birleşik ("TR330006...") hem boşluklu ("TR33 0006 1005 ...") hem
# tireli ("TR33-0006-...") formatları yakala.
_IBAN_TR_RE = re.compile(
    r"(?<![A-Z0-9])TR(?:[\s\-]*\d){24}(?![0-9])",
    re.IGNORECASE,
)

# ISO 13616'da resmi olarak tanımlı IBAN uzunlukları (her ülke için sabit).
# Sadece TR + en sık karşılaşılan birkaç ülke. Genişletilebilir.
IBAN_LENGTHS = {
    "TR": 26,
    "DE": 22,
    "GB": 22,
    "FR": 27,
    "NL": 18,
    "BE": 16,
    "IT": 27,
    "ES": 24,
    "CH": 21,
    "AT": 20,
    "AZ": 28,
}


def _mod97(iban: str) -> int:
    """ISO 7064 MOD-97 hesabı. Geçerli IBAN için sonuç 1 olmalı."""
    # 1) İlk 4 karakteri sona taşı
    rearranged = iban[4:] + iban[:4]
    # 2) Harfleri 2-haneli sayılara çevir (A=10..Z=35)
    digits = []
    for ch in rearranged:
        if ch.isdigit():
            digits.append(ch)
        else:
            digits.append(str(ord(ch.upper()) - ord("A") + 10))
    numeric = "".join(digits)
    # 3) Büyük tamsayı mod 97
    return int(numeric) % 97


def is_valid_iban(value: str) -> bool:
    """IBAN string'in (boşluklu/tireli/birleşik) geçerli olup olmadığını döndür.

    >>> is_valid_iban("TR33 0006 1005 1978 6457 8413 26")
    True
    >>> is_valid_iban("TR33-0006-1005-1978-6457-8413-26")
    True
    >>> is_valid_iban("TR000006100519786457841326")
    False
    """
    if not value:
        return False
    cleaned = re.sub(r"[\s\-]+", "", value).upper()
    if len(cleaned) < 4:
        return False
    country = cleaned[:2]
    if not country.isalpha():
        return False
    expected_len = IBAN_LENGTHS.get(country)
    if expected_len is not None and len(cleaned) != expected_len:
        return False
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", cleaned):
        return False
    return _mod97(cleaned) == 1


def find_iban(text: str) -> Iterator[PIIMatch]:
    """Metindeki tüm geçerli TR IBAN'larını yield et.

    Boşluklu, tireli ve birleşik formatların hepsi yakalanır.
    """
    for m in _IBAN_TR_RE.finditer(text):
        raw = m.group(0)
        # Boşluk ve tireleri sök, büyük harfe çevir.
        cleaned = re.sub(r"[\s\-]+", "", raw).upper()
        if is_valid_iban(cleaned):
            bank_code = cleaned[4:9]
            yield PIIMatch(
                type="iban",
                value=cleaned,
                start=m.start(),
                end=m.end(),
                valid=True,
                meta={"country": "TR", "bank_code": bank_code, "raw": raw},
            )
