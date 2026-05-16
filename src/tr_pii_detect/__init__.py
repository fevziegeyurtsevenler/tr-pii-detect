"""tr-pii-detect — Türkiye'ye özgü PII tipleri için algoritma doğrulamalı tespit.

Hızlı başlangıç:

    >>> from tr_pii_detect import scan, redact
    >>> hits = scan("TC'm 10000000146, IBAN'ım TR330006100519786457841326")
    >>> for h in hits:
    ...     print(h.type, h.value, h.valid)
    tckn 10000000146 True
    iban TR330006100519786457841326 True

    >>> redact("Telefon: 0532 123 45 67")
    'Telefon: [PHONE]'

Bu kütüphane sadece regex değil, her PII tipi için **algoritma doğrulaması**
yapar (TCKN için NVI checksum, IBAN için MOD-97, kredi kartı için Luhn).
Bu yaklaşım sokak numarası, sipariş ID veya tesadüfen 11 hane olan stringleri
yanlış pozitif olarak işaretlemekten kaçınır.

Desteklenen PII tipleri:
    - tckn   : TC Kimlik No (NVI checksum doğrulamalı)
    - iban   : Türkiye IBAN (ISO 7064 MOD-97 doğrulamalı)
    - vkn    : Vergi Kimlik No (GİB checksum doğrulamalı)
    - card   : Kredi/banka kartı (Luhn doğrulamalı + marka tespiti)
    - phone  : TR mobil telefon (format + operatör kodu)
    - plate  : TR araç plakası (il kodu + format)

Lisans: PolyForm Noncommercial 1.0.0
Yazar: Fevzi Ege Yurtsevenler / AltaySec
Repo: https://github.com/fevziegeyurtsevenler/tr-pii-detect
"""
from __future__ import annotations

from .types import PIIMatch
from .scanner import scan, redact, Detector, ALL_DETECTORS

# Algoritma doğrulayıcıları doğrudan kullanım için
from .tckn import is_valid_tckn, find_tckn
from .iban import is_valid_iban, find_iban
from .vkn import is_valid_vkn, find_vkn
from .card import luhn_check, find_card
from .phone import is_valid_tr_mobile, find_phone
from .plate import is_valid_plate, find_plate

__version__ = "0.1.0"

__all__ = [
    "scan",
    "redact",
    "Detector",
    "PIIMatch",
    "ALL_DETECTORS",
    "is_valid_tckn",
    "is_valid_iban",
    "is_valid_vkn",
    "luhn_check",
    "is_valid_tr_mobile",
    "is_valid_plate",
    "find_tckn",
    "find_iban",
    "find_vkn",
    "find_card",
    "find_phone",
    "find_plate",
    "__version__",
]
