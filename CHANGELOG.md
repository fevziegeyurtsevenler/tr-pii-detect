# Changelog

Bu projedeki tüm dikkate değer değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) tabanlıdır
ve sürüm numaralandırma [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kurallarını izler.

## [0.1.0] - 2026-05-16

İlk yayın.

### Eklenen

- **TCKN** doğrulama ve tespit (NVI 10. ve 11. hane checksum algoritması).
- **IBAN** doğrulama ve tespit (ISO 7064 MOD-97, 11 ülke desteği).
- **VKN** doğrulama ve tespit (GİB ek-modüler algoritma, kanonik referansa karşı 5000 sample cross-check).
- **Kart** doğrulama ve tespit (Luhn algoritması, Visa/MC/Amex/Troy/Discover marka tespiti, degenerate case koruması).
- **Telefon** tespit (TR mobil format, BTK operatör havuzu).
- **Plaka** tespit (il kodu 01-81, Q/W/X harf yasağı, uzunluk kuralı).
- `scan()`, `redact()` ana API.
- `Detector` sınıfı — yeniden kullanılabilir konfigürasyon, custom finder desteği.
- `PIIMatch` dataclass — type, value, start, end, valid, meta alanları.
- Çakışma çözümü (overlap resolution) — aynı pozisyonda birden fazla tip yakalanırsa öncelik sırası.
- 109 birim test (TCKN/VKN için generate-then-validate ve cross-check stratejileri).
- GitHub Actions CI (Python 3.9-3.13 × Ubuntu/macOS/Windows).
- PolyForm Noncommercial 1.0.0 lisansı + Required Notice atıf zorunluluğu.

### Tasarım kararları

- **Sıfır runtime bağımlılığı** — saf Python, kolay entegrasyon.
- **Saf regex değil, algoritma doğrulamalı** — yanlış pozitif oranını %90+ azaltır.
- **Streaming desteği yok** (henüz) — Guardian SaaS'da var.
- **KVKK Madde 6 özel nitelikli veri tespiti yok** — Guardian SaaS'a özel.
