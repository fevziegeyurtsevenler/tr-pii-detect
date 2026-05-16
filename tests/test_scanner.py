"""Scanner ve redact API entegrasyon testleri."""
from __future__ import annotations

import random

import pytest

from tr_pii_detect import scan, redact, Detector, PIIMatch
from tests.test_tckn import _generate_valid_tckn
from tests.test_vkn import _generate_valid_vkn


class TestScan:
    def test_mixed_content(self):
        random.seed(42)
        tc = _generate_valid_tckn()
        text = (
            f"Müşteri TC: {tc}\n"
            f"Telefon: 0532 111 22 33\n"
            f"IBAN: TR330006100519786457841326\n"
            f"Plaka: 34 AB 1234\n"
            f"Kart: 4111 1111 1111 1111\n"
        )
        hits = scan(text)
        types_found = {h.type for h in hits}
        assert types_found == {"tckn", "phone", "iban", "plate", "card"}

    def test_empty_text(self):
        assert scan("") == []
        assert scan(None) == []  # type: ignore[arg-type]

    def test_no_pii_in_text(self):
        text = "Bu metin hiçbir kişisel veri içermez."
        assert scan(text) == []

    def test_type_filter(self):
        text = "TC: 10000000146 ve telefon: 0532 111 22 33"
        hits = scan(text, types=["tckn"])
        assert len(hits) == 1
        assert hits[0].type == "tckn"

    def test_unknown_type_ignored(self):
        text = "TC: 10000000146"
        hits = scan(text, types=["nonexistent", "tckn"])
        assert len(hits) == 1

    def test_results_sorted_by_position(self):
        text = "İlk telefon 0532 111 22 33, sonra TC 10000000146"
        hits = scan(text)
        positions = [h.start for h in hits]
        assert positions == sorted(positions)


class TestRedact:
    def test_basic_redaction(self):
        out = redact("TC: 10000000146")
        assert "[TCKN]" in out
        assert "10000000146" not in out

    def test_multiple_pii_types(self):
        text = "TC: 10000000146 ve Tel: 0532 111 22 33"
        out = redact(text)
        assert "[TCKN]" in out
        assert "[PHONE]" in out
        assert "10000000146" not in out
        assert "0532" not in out

    def test_custom_placeholder(self):
        def replace(m: PIIMatch) -> str:
            return f"<{m.type}:redacted>"
        out = redact("TC: 10000000146", placeholder=replace)
        assert "<tckn:redacted>" in out

    def test_type_filter_in_redact(self):
        text = "TC: 10000000146 ve Tel: 0532 111 22 33"
        out = redact(text, types=["tckn"])
        assert "[TCKN]" in out
        assert "0532 111 22 33" in out  # telefon kalmalı


class TestDetector:
    def test_reusable_instance(self):
        d = Detector(types=["tckn"])
        random.seed(1)
        t1 = _generate_valid_tckn()
        t2 = _generate_valid_tckn()
        assert len(d.scan(f"TC: {t1}")) == 1
        assert len(d.scan(f"TC: {t2}")) == 1

    def test_redact_via_detector(self):
        d = Detector(types=["tckn", "iban"])
        out = d.redact("TC: 10000000146")
        assert "[TCKN]" in out

    def test_custom_finder(self):
        """Kullanıcı kendi finder'ını ekleyebilmeli."""
        def find_x(text):
            import re
            for m in re.finditer(r"\bXXX-\d{3}\b", text):
                yield PIIMatch(
                    type="custom",
                    value=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    valid=True,
                )

        d = Detector(custom_finders={"custom": find_x})
        hits = d.scan("Kod: XXX-123")
        types_found = {h.type for h in hits}
        assert "custom" in types_found


class TestOverlapResolution:
    def test_no_double_match_at_same_position(self):
        """Aynı pozisyonda hem 10 hane (telefonsuz 5-prefix) hem
        VKN yakalanmamalı; bir tanesi seçilmeli."""
        # Numara 10 hane ama 5 ile başlamıyor — VKN olabilir, telefon olamaz
        random.seed(99)
        v = _generate_valid_vkn()
        # Eğer VKN 5 ile başlıyorsa farklı bir tane üret
        while v.startswith("5"):
            v = _generate_valid_vkn()
        text = f"Kayıt: {v}"
        hits = scan(text)
        # En fazla 1 match (telefon değil, VKN)
        assert len(hits) <= 1
