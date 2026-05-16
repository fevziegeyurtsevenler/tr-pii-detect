"""Ana scanner API: tüm dedektörleri birleştirir.

Kullanım:

    from tr_pii_detect import scan, redact

    hits = scan("TC'm 10000000146, IBAN'ım TR330006100519786457841326")
    for h in hits:
        print(h.type, h.value, h.start, h.end)

    safe = redact("Telefon: 0532 123 45 67")
    # "Telefon: [PHONE]"

Detector sınıfı tek tek dedektörleri seçili çalıştırma için.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional, Sequence

from .types import PIIMatch
from .tckn import find_tckn
from .iban import find_iban
from .vkn import find_vkn
from .card import find_card
from .phone import find_phone
from .plate import find_plate


# Tüm yerleşik dedektörler. Dış kullanıcılar Detector sınıfı ile
# bunlardan alt küme seçebilir veya kendi finder'larını ekleyebilir.
ALL_DETECTORS: dict[str, Callable[[str], Iterable[PIIMatch]]] = {
    "tckn": find_tckn,
    "iban": find_iban,
    "vkn": find_vkn,
    "card": find_card,
    "phone": find_phone,
    "plate": find_plate,
}


def _resolve_overlaps(matches: List[PIIMatch]) -> List[PIIMatch]:
    """Çakışan eşleşmeleri çöz: aynı pozisyonda birden fazla tipi varsa
    daha spesifik olanı (algoritma doğrulamalı, daha uzun) tut.

    TCKN/VKN/telefon hepsi 10-11 hane → çakışma olabilir.
    Önceliklendirme: tckn > vkn > iban > card > phone > plate
    """
    priority = {"iban": 0, "card": 1, "tckn": 2, "vkn": 3, "phone": 4, "plate": 5}
    # Span başına en yüksek öncelikli (en düşük öncelik sayısı) eşleşmeyi tut.
    by_span: dict[tuple, PIIMatch] = {}
    for m in matches:
        span = (m.start, m.end)
        existing = by_span.get(span)
        if existing is None or priority[m.type] < priority[existing.type]:
            by_span[span] = m

    # Span'lar farklı ama bir match diğerini kapsıyorsa, uzun olanı tut.
    sorted_matches = sorted(by_span.values(), key=lambda x: (x.start, -x.end))
    result: List[PIIMatch] = []
    last_end = -1
    for m in sorted_matches:
        if m.start < last_end:
            # Bu match önceki ile çakışıyor; öncelik kontrolü
            prev = result[-1]
            if priority[m.type] < priority[prev.type] or len(m) > len(prev):
                result[-1] = m
                last_end = m.end
            continue
        result.append(m)
        last_end = m.end
    return result


def scan(
    text: str,
    types: Optional[Sequence[str]] = None,
) -> List[PIIMatch]:
    """Metinde tüm (veya seçilmiş) PII tiplerini tara.

    Args:
        text:  Taranacak metin.
        types: Çalıştırılacak dedektör listesi. None ise hepsi çalışır.
               Örn: ['tckn', 'iban'] sadece TCKN ve IBAN bulur.

    Returns:
        Algoritma doğrulamasından geçmiş PIIMatch'lerin listesi.
        Çakışmalar çözülmüş, başlangıç indeksine göre sıralı.
    """
    if not text:
        return []

    selected = types or list(ALL_DETECTORS.keys())
    matches: List[PIIMatch] = []
    for type_name in selected:
        finder = ALL_DETECTORS.get(type_name)
        if finder is None:
            continue
        matches.extend(finder(text))

    return _resolve_overlaps(matches)


def redact(
    text: str,
    types: Optional[Sequence[str]] = None,
    placeholder: Optional[Callable[[PIIMatch], str]] = None,
) -> str:
    """Metni PII'leri maskelenmiş şekilde döndür.

    Varsayılan placeholder: `[TIP]` (örn. `[TCKN]`, `[IBAN]`).
    Özelleştirme için `placeholder` fonksiyonu geç.

    >>> redact("TC'm 10000000146 ve telefonum 0532 111 22 33")
    "TC'm [TCKN] ve telefonum [PHONE]"
    """
    if not text:
        return text

    hits = scan(text, types=types)
    if not hits:
        return text

    # Sondan başa doğru değiştir ki index'ler kaymasın
    result = text
    for m in sorted(hits, key=lambda x: x.start, reverse=True):
        if placeholder is None:
            mask = f"[{m.type.upper()}]"
        else:
            mask = placeholder(m)
        result = result[: m.start] + mask + result[m.end :]
    return result


class Detector:
    """Konfigüre edilebilir dedektör. Aynı konfigürasyonu birden fazla
    metin üzerinde çalıştırmak için Detector instance'ı oluştur ve
    yeniden kullan.

    Örnek:

        det = Detector(types=['tckn', 'iban'])
        for doc in documents:
            print(det.scan(doc))
    """

    def __init__(
        self,
        types: Optional[Sequence[str]] = None,
        custom_finders: Optional[dict[str, Callable[[str], Iterable[PIIMatch]]]] = None,
    ) -> None:
        self.types = types
        # Custom finder'lar yerleşik olanlarla birleştirilir; aynı isim
        # custom tarafından override edilir.
        self._finders: dict[str, Callable[[str], Iterable[PIIMatch]]] = dict(ALL_DETECTORS)
        if custom_finders:
            self._finders.update(custom_finders)

    def scan(self, text: str) -> List[PIIMatch]:
        if not text:
            return []
        selected = self.types or list(self._finders.keys())
        matches: List[PIIMatch] = []
        for type_name in selected:
            finder = self._finders.get(type_name)
            if finder is None:
                continue
            matches.extend(finder(text))
        return _resolve_overlaps(matches)

    def redact(
        self,
        text: str,
        placeholder: Optional[Callable[[PIIMatch], str]] = None,
    ) -> str:
        hits = self.scan(text)
        if not hits:
            return text
        result = text
        for m in sorted(hits, key=lambda x: x.start, reverse=True):
            mask = f"[{m.type.upper()}]" if placeholder is None else placeholder(m)
            result = result[: m.start] + mask + result[m.end :]
        return result
