"""tr-pii-detect quickstart örneği.

Çalıştırma:
    python examples/quickstart.py
"""
from tr_pii_detect import scan, redact, Detector

SAMPLE_TEXT = """
Müşteri bilgileri:
- Ad Soyad: Ahmet Yılmaz
- TC Kimlik No: 10000000146
- Telefon: 0532 123 45 67
- IBAN: TR33 0006 1005 1978 6457 8413 26
- Plaka: 06 ABC 123
- Kart: 4111 1111 1111 1111
- Sipariş No: 12345678901 (TCKN değil — checksum tutmuyor)
- Sokak no: 12345 / Mahalle
"""


def main() -> None:
    print("=" * 60)
    print("Orijinal metin:")
    print("=" * 60)
    print(SAMPLE_TEXT)

    print("=" * 60)
    print("Tespit edilen PII'ler:")
    print("=" * 60)
    for hit in scan(SAMPLE_TEXT):
        print(f"  {hit.type:6s}  {hit.value!r:35s}  pos={hit.start}-{hit.end}")
        if hit.meta:
            print(f"          meta={hit.meta}")

    print()
    print("=" * 60)
    print("Maskelenmiş metin (redact):")
    print("=" * 60)
    print(redact(SAMPLE_TEXT))

    print("=" * 60)
    print("Sadece TCKN ve IBAN'ı maskele:")
    print("=" * 60)
    print(redact(SAMPLE_TEXT, types=["tckn", "iban"]))

    print("=" * 60)
    print("Özel placeholder ile maskele:")
    print("=" * 60)

    def fancy(m):
        return f"<{m.type.upper()}:{'*' * min(len(m.value), 10)}>"

    print(redact(SAMPLE_TEXT, placeholder=fancy))

    print("=" * 60)
    print("Yeniden kullanılabilir Detector:")
    print("=" * 60)
    det = Detector(types=["tckn", "phone"])
    for line in SAMPLE_TEXT.strip().split("\n"):
        if det.scan(line):
            print(f"  REDACT: {det.redact(line)}")
        else:
            print(f"  KEEP:   {line}")


if __name__ == "__main__":
    main()
