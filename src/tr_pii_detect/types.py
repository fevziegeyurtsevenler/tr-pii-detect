"""Ortak veri tipleri."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PIIMatch:
    """Bir PII (Personally Identifiable Information) eşleşmesi.

    Attributes:
        type:   PII tipi (örn. 'tckn', 'iban', 'vkn', 'card', 'phone', 'plate').
        value:  Tespit edilen ham metin.
        start:  Orijinal metindeki başlangıç index'i (inclusive).
        end:    Orijinal metindeki bitiş index'i (exclusive).
        valid:  Algoritma doğrulamasından geçti mi? Sadece regex eşleşen
                ama checksum'u tutmayan değerler için False olur. Regex
                + algoritma her ikisinden geçen değerler için True.
        meta:   Tip-spesifik ekstra bilgiler (örn. IBAN için banka kodu).
    """

    type: str
    value: str
    start: int
    end: int
    valid: bool = True
    meta: Optional[dict] = field(default=None)

    def __len__(self) -> int:
        return self.end - self.start

    def as_dict(self) -> dict:
        d = {
            "type": self.type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "valid": self.valid,
        }
        if self.meta:
            d["meta"] = self.meta
        return d
