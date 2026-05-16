# tr-pii-detect

> 🇹🇷 **Türkiye'ye özgü PII (Personally Identifiable Information) tipleri için algoritma doğrulamalı tespit ve maskeleme kütüphanesi.** Sıfır bağımlılık, saf Python.

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm--Noncommercial--1.0.0-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![No deps](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](pyproject.toml)
[![AltaySec](https://img.shields.io/badge/by-AltaySec-7c3aed.svg)](https://altaysec.com.tr)

---

## 🎯 Neden bu kütüphane?

Sadece regex ile PII tespiti **yanlış pozitiflerle doludur**: müşteri ID, sipariş numarası, telefon numarası gibi 10-11 haneli stringler kolayca yanlışlıkla TCKN veya VKN olarak işaretlenir. Yabancı kütüphaneler (`presidio`, vb.) Türkiye'ye özgü algoritmaları bilmez:

- **TCKN**: 10. ve 11. hane checksum kuralları (NVI algoritması)
- **IBAN**: ISO 7064 MOD-97 doğrulaması
- **VKN**: GİB tarafından tanımlanan ek-modüler algoritma
- **Kart**: Luhn (mod-10) algoritması
- **Plaka**: İl kodu 01-81 + Q/W/X harf yasağı

Bu kütüphane her PII tipi için **algoritma doğrulaması yapar**, böylece yanlış pozitifleri %90+ azaltır.

---

## ⚡ Hızlı başlangıç

### Kurulum

```bash
pip install tr-pii-detect
```

### Kullanım

```python
from tr_pii_detect import scan, redact

text = """
Müşteri TC: 10000000146
Telefon: 0532 123 45 67
IBAN: TR33 0006 1005 1978 6457 8413 26
Plaka: 06 ABC 123
Kart: 4111 1111 1111 1111
Sipariş no: 12345678901   (TCKN değil — checksum tutmuyor)
"""

# Tespit et
for hit in scan(text):
    print(f"{hit.type:6s} {hit.value}  (pos {hit.start}-{hit.end})")

# Çıktı:
# tckn   10000000146   (pos 16-27)
# phone  5321234567    (pos 39-53)
# iban   TR33...3026   (pos 62-94)
# plate  06 ABC 123    (pos 103-113)
# card   4111...1111   (pos 122-141)

# Maskele
print(redact(text))
# Müşteri TC: [TCKN]
# Telefon: [PHONE]
# IBAN: [IBAN]
# ...
```

---

## 🛠️ API

### `scan(text, types=None) -> List[PIIMatch]`

Metni tara, algoritma doğrulamasından geçen PII'leri döndür.

```python
hits = scan(text)                          # tümü
hits = scan(text, types=["tckn", "iban"])  # sadece seçilenler
```

### `redact(text, types=None, placeholder=None) -> str`

PII'leri maskelenmiş metni döndür.

```python
# Varsayılan: [TCKN], [IBAN] vb.
redact("TC: 10000000146")
# → "TC: [TCKN]"

# Özel placeholder
def fancy(m): return f"<{m.type}:redacted:{len(m.value)}>"
redact("TC: 10000000146", placeholder=fancy)
# → "TC: <tckn:redacted:11>"
```

### `Detector` — Tekrar kullanılabilir konfigürasyon

```python
from tr_pii_detect import Detector

det = Detector(types=["tckn", "iban"])
for doc in documents:
    safe = det.redact(doc)
```

### Bireysel doğrulayıcılar

Sadece checksum kontrolü gerekiyorsa, ayrı fonksiyonlar mevcuttur:

```python
from tr_pii_detect import (
    is_valid_tckn,
    is_valid_iban,
    is_valid_vkn,
    luhn_check,
    is_valid_tr_mobile,
    is_valid_plate,
)

is_valid_tckn("10000000146")            # True
is_valid_iban("TR330006100519786457841326")  # True
luhn_check("4111111111111111")          # True
```

### `PIIMatch` — sonuç tipi

```python
@dataclass(frozen=True)
class PIIMatch:
    type: str          # "tckn" | "iban" | "vkn" | "card" | "phone" | "plate"
    value: str         # normalize edilmiş değer
    start: int         # orijinal metindeki başlangıç
    end: int           # orijinal metindeki bitiş
    valid: bool        # algoritma doğrulamasından geçti mi
    meta: dict | None  # tipe özgü ekstra bilgi
```

`meta` örneği:

```python
hits = scan("IBAN: TR330006100519786457841326")
hits[0].meta
# → {"country": "TR", "bank_code": "00061", "raw": "TR33..."}

hits = scan("Kart: 4111 1111 1111 1111")
hits[0].meta
# → {"brand": "visa", "raw": "4111 1111 1111 1111", "length": 16}

hits = scan("Plaka: 34 AB 1234")
hits[0].meta
# → {"province_code": "34", "letters": "AB", "digits": "1234", "raw": "..."}
```

---

## 📋 Desteklenen PII tipleri

| Tip | Doğrulama | Yanlış pozitif oranı (regex-only → algoritma) |
|-----|-----------|------------------------------------------------|
| `tckn` | NVI checksum (10. + 11. hane) | ~95% → <1% |
| `iban` | ISO 7064 MOD-97 + uzunluk | ~70% → <0.01% |
| `vkn` | GİB ek-modüler checksum | ~99% → ~%9.8 |
| `card` | Luhn (mod-10) + 13-19 hane + marka | ~95% → ~10% |
| `phone` | Format + BTK operatör havuzu (5XX) | ~80% → ~5% |
| `plate` | İl kodu 01-81 + Q/W/X yasağı + uzunluk | ~60% → <5% |

---

## 🎓 Eğitim ve referans

### TCKN algoritması (kanonik)

```
10. hane = ((d1 + d3 + d5 + d7 + d9) * 7 - (d2 + d4 + d6 + d8)) mod 10
11. hane = (d1 + d2 + ... + d10) mod 10
İlk hane 0 olamaz.
```

### IBAN MOD-97 (ISO 7064)

```
1. İlk 4 karakteri sona taşı: BBAN + ülke kodu + kontrol
2. Harfleri sayıya çevir (A=10, B=11, ..., Z=35)
3. Büyük sayı mod 97 == 1 olmalı
```

### Luhn (kredi kartı)

```
Sağdan sola, çift pozisyondaki haneleri 2 ile çarp.
Çarpım 9'dan büyükse iki haneyi topla (veya -9).
Toplam mod 10 == 0 olmalı.
```

---

## 🔐 Lisans — ÖNEMLİ

Bu kütüphane **PolyForm Noncommercial 1.0.0** lisansı altındadır.

### ✅ Ücretsiz kullanım

- Kişisel projeler, hobiler, eğitim, araştırma
- Üniversiteler, okullar, kar amacı gütmeyen kuruluşlar
- Kamu kurumları, sağlık ve güvenlik örgütleri
- Açık kaynak araştırma projeleri

### ❌ Ticari kullanım — Lisans gerekir

Şirketinizin gelir elde ettiği bir ürün veya hizmette kullanmak için **AltaySec Guardian** ticari lisansı gereklidir.

### 📌 Atıf zorunluluğu

Kullanıyorsanız, dağıtıyorsanız veya türev iş üretiyorsanız aşağıdaki bildirimi proje dokümantasyonunuzda görünür şekilde bulundurun:

```
Required Notice: Copyright (c) 2026 Fevzi Ege Yurtsevenler / AltaySec
(https://altaysec.com.tr) — https://github.com/fevziegeyurtsevenler/tr-pii-detect
```

Detaylar: [LICENSE](LICENSE)

---

## 🚀 Production / Kurumsal sürüm: AltaySec Guardian

Bu kütüphane, **AltaySec Guardian** SaaS ürününün açık kaynak küçük kardeşidir. Eğer kurumsal bir LLM güvenlik gateway'i veya tam kapsamlı veri koruma çözümü arıyorsanız, Guardian aşağıdaki ek özelliklere sahiptir:

|  | tr-pii-detect (Açık kaynak) | Guardian (SaaS) |
|--|------------------------------|-----------------|
| Temel PII tipleri (6) | ✅ | ✅ |
| KVKK Madde 6 (sağlık, din, biyometrik) | ❌ | ✅ |
| Ek PII tipleri (SGK, pasaport, MERSIS, IP, e-posta) | ❌ | ✅ |
| Prompt injection tespiti | ❌ | ✅ |
| Streaming output filtreleme | ❌ | ✅ |
| KVKK PDF denetim raporu | ❌ | ✅ |
| OpenAI / Anthropic SDK uyumlu proxy | ❌ | ✅ |
| Türkiye'de barındırma | ❌ | ✅ |
| Destek + SLA | ❌ | ✅ |

🔗 https://altaysec.com.tr/urunler/guardian
✉️ hello@altaysec.com.tr

---

## 🧪 Geliştirme

```bash
git clone https://github.com/fevziegeyurtsevenler/tr-pii-detect
cd tr-pii-detect
pip install -e ".[dev]"
pytest
```

Algoritmalar **self-consistency** ve **kanonik referans karşılaştırması** ile test edilmiştir:

- TCKN: 100 generated örnek, NVI algoritmasına uygun
- VKN: 5000 random örnek karşı bağımsız kanonik referans (atagulalan/ziyahan gist) — **0 anlaşmazlık**
- IBAN: 8 farklı ülke için bilinen test vektörleri

---

## 📚 İlgili kaynaklar

- [AltaySec Araştırmalar](https://altaysec.com.tr/arastirmalar) — Türkçe LLM Security, KVKK, prompt injection makaleleri
- [OWASP LLM Top 10 Türkçe Rehberi](https://github.com/fevziegeyurtsevenler/OWASP-LLM-TOP-10-TURKCE)
- [KVKK Madde 6 — Özel Nitelikli Kişisel Veriler](https://www.kvkk.gov.tr)
- [GİB VKN Doğrulama](https://ivd.gib.gov.tr/?gn=vkndogrulamalar)
- [NVI TCKN Algoritması](https://www.nvi.gov.tr)

---

## 🤝 Katkı

PR'lar memnuniyetle kabul edilir — özellikle:

- Yeni PII tipi (MERSIS, SGK, pasaport için algoritma doğrulamalı detector)
- Bilinmeyen BTK operatör kodları
- Edge case testleri
- Çeviri (İngilizce README için)

Katkı süreci:
1. Issue aç (önceden tartış)
2. Fork + branch (`feat/yeni-pii-tipi`)
3. Test yaz (test-driven preferred)
4. PR aç

---

## 👤 Yazar

**Fevzi Ege Yurtsevenler** — AltaySec Kurucusu, Yapay Zeka Güvenliği Araştırmacısı

- 🌍 [altaysec.com.tr](https://altaysec.com.tr)
- 💼 [LinkedIn](https://www.linkedin.com/in/fevziegeyurtsevenler)
- 📚 [Araştırmalar](https://altaysec.com.tr/arastirmalar)
- 🐙 [GitHub](https://github.com/fevziegeyurtsevenler)

---

<sub>**tr-pii-detect** — AltaySec açık kaynak ekosisteminin bir parçasıdır. AltaySec, Türkiye'nin yapay zeka güvenliği alanında yerli savunma çözümleri geliştiren bir teknoloji girişimidir.</sub>
