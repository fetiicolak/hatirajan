"""Duyuru metninden Türkçe tarihleri ayıklayıp türlerine (başvuru, sınav, sonuç...) göre sınıflar.

Yakalanan biçimler:
  "13-17 Ekim 2025", "03 Kasım – 24 Mayıs 2026", "5 Kasım 2025", "5 Kasım",
  "13.10.2025", "13.10.2025 - 17.10.2025"
Her tarihin türü, çevresindeki (aynı cümledeki) en yakın anahtar kelimeye göre belirlenir.
"""

import re
from datetime import date

from .metin import tr_kucuk

AYLAR = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
    "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
    "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}
_AY = "(" + "|".join(AYLAR) + ")"
_AYRAC = r"\s*(?:[-–—]|ile)\s*"

# Sıra önemli: önce aralıklar, sonra tekil tarihler (yakalanan bölgeler maskelenir)
DESENLER = [
    ("aralik_iki_ay", re.compile(rf"\b(\d{{1,2}})\s+{_AY}{_AYRAC}(\d{{1,2}})\s+{_AY}(?:\s+(\d{{4}}))?")),
    ("aralik_ay", re.compile(rf"\b(\d{{1,2}}){_AYRAC}(\d{{1,2}})\s+{_AY}(?:\s+(\d{{4}}))?")),
    ("aralik_sayi", re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})" + _AYRAC + r"(\d{1,2})[./](\d{1,2})[./](\d{4})\b")),
    ("tek_ay", re.compile(rf"\b(\d{{1,2}})\s+{_AY}(?:\s+(\d{{4}}))?")),
    ("tek_sayi", re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b")),
]

SAAT_DESENI = re.compile(r"saat\s*:?\s*(\d{1,2})[.:](\d{2})|\b(\d{1,2})[.:](\d{2})\s*['’]?\s*(?:da|de|ta|te)\b")

# Tür -> çevrede aranacak (küçük harf, Türkçe) kelime kökleri
TUR_KELIMELERI = {
    "basvuru": ("başvur", "kayıt", "kayit", "müracaat"),
    "sonuc": ("sonuç", "sonuc", "kura", "ilan edil", "açıklan"),
    "sinav": ("sınav", "sinav"),
    "diger": ("uygulan", "yayım", "tören", "toplantı", "dönem"),
}

TUR_ADLARI = {
    "basvuru_baslangic": "Başvuru başlangıcı",
    "basvuru_bitis": "Son başvuru",
    "sinav": "Sınav",
    "sonuc": "Sonuç ilanı",
    "diger": "Diğer tarih",
}


def _yil_tamamla(gun: int, ay: int, yil: str | None, referans: date) -> date | None:
    """Yılı yazılmamış tarihe yıl verir (referanstan çok gerideyse ertesi yıl)."""
    try:
        if yil:
            return date(int(yil), ay, gun)
        aday = date(referans.year, ay, gun)
        if (referans - aday).days > 60:
            aday = date(referans.year + 1, ay, gun)
        return aday
    except ValueError:
        return None


def _eslesmeleri_bul(kucuk: str, referans: date) -> list[tuple[int, int, date, date | None]]:
    """(başlangıç, bitiş, tarih1, tarih2|None) listesi; metindeki sıraya göre."""
    maske = list(kucuk)
    sonuc = []
    for ad, desen in DESENLER:
        for m in desen.finditer("".join(maske)):
            g = m.groups()
            if ad == "aralik_iki_ay":
                t2 = _yil_tamamla(int(g[2]), AYLAR[g[3]], g[4], referans)
                t1 = _yil_tamamla(int(g[0]), AYLAR[g[1]], str(t2.year) if t2 else None, referans)
            elif ad == "aralik_ay":
                t2 = _yil_tamamla(int(g[1]), AYLAR[g[2]], g[3], referans)
                t1 = _yil_tamamla(int(g[0]), AYLAR[g[2]], str(t2.year) if t2 else None, referans)
            elif ad == "aralik_sayi":
                t1 = _yil_tamamla(int(g[0]), int(g[1]), g[2], referans) if 1 <= int(g[1]) <= 12 else None
                t2 = _yil_tamamla(int(g[3]), int(g[4]), g[5], referans) if 1 <= int(g[4]) <= 12 else None
            elif ad == "tek_ay":
                t1, t2 = _yil_tamamla(int(g[0]), AYLAR[g[1]], g[2], referans), None
            else:
                t1 = _yil_tamamla(int(g[0]), int(g[1]), g[2], referans) if 1 <= int(g[1]) <= 12 else None
                t2 = None
            if not t1:
                continue
            if t2 and t2 < t1:  # "03 Kasım – 24 Mayıs 2026": başlangıç bir önceki yıl
                t1 = t1.replace(year=t1.year - 1)
            sonuc.append((m.start(), m.end(), t1, t2))
            for i in range(m.start(), m.end()):
                maske[i] = "#"
    return sorted(sonuc, key=lambda x: x[0])


def _tur_bul(kucuk: str, bas: int, son: int) -> str:
    """Tarihin bulunduğu cümlede tarihe en yakın anahtar kelimenin türü."""
    nokta = kucuk.rfind(". ", 0, bas)
    sol = max(nokta + 2 if nokta != -1 else 0, bas - 160, 0)
    sag_nokta = kucuk.find(". ", son)
    sag = min(sag_nokta if sag_nokta != -1 else len(kucuk), son + 100)
    en_iyi, en_yakin = "diger", 10**9
    for tur, kelimeler in TUR_KELIMELERI.items():
        for kelime in kelimeler:
            for m in re.finditer(re.escape(kelime), kucuk[sol:sag]):
                konum = sol + m.start()
                # tarihten önce gelen kelimeler biraz daha güçlü sayılır
                uzaklik = (bas - konum) if konum < bas else (konum - son) * 1.5
                if tur == "diger":  # belirli türler varken "diğer" zayıf kalsın
                    uzaklik *= 2
                if uzaklik < en_yakin:
                    en_iyi, en_yakin = tur, uzaklik
    return en_iyi


def _saat_bul(kucuk: str, son: int, sinir: int) -> str | None:
    m = SAAT_DESENI.search(kucuk, son, min(sinir, son + 220))
    if not m:
        return None
    s, d = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
    if int(s) > 23 or int(d) > 59:
        return None
    return f"{int(s):02d}:{d}"


BITIS_IZI = re.compile(r"son (?:gün|tarih|başvuru)|kadar|bitiş|sona")


def _baslangic_mi(kucuk: str, bas: int, son: int) -> bool:
    """Tek başvuru tarihi başlangıç mı? Tarihe en yakın ipucu karar verir ("başla" ↔ "son başvuru/kadar")."""
    sol, sag = kucuk[max(0, bas - 80):bas], kucuk[son:son + 40]
    ipuclari = []  # (uzaklık, başlangıç mı)
    for desen, baslangic in ((BITIS_IZI, False), (re.compile("başla"), True)):
        ipuclari += [(len(sol) - m.end(), baslangic) for m in desen.finditer(sol)]
        ipuclari += [(m.start() * 1.5, baslangic) for m in desen.finditer(sag)]
    return bool(ipuclari) and min(ipuclari)[1]


def tarihleri_ayikla(metin: str, referans: date) -> list[dict]:
    """Metindeki tarihleri [{tur, tarih, saat, alinti}] olarak döndürür.

    referans: yılı yazılmamış tarihler için dayanak (genelde duyurunun yayım tarihi).
    """
    metin = re.sub(r"\s+", " ", metin)
    kucuk = tr_kucuk(metin)
    eslesmeler = _eslesmeleri_bul(kucuk, referans)
    olaylar: dict[tuple[str, str], dict] = {}

    for i, (bas, son, t1, t2) in enumerate(eslesmeler):
        sonraki = eslesmeler[i + 1][0] if i + 1 < len(eslesmeler) else len(kucuk)
        tur = _tur_bul(kucuk, bas, son)
        saat = _saat_bul(kucuk, son, sonraki)
        alinti = metin[max(0, bas - 60):min(len(metin), son + 60)].strip()

        if tur == "basvuru":
            if t2:
                kayitlar = [("basvuru_baslangic", t1), ("basvuru_bitis", t2)]
            elif _baslangic_mi(kucuk, bas, son):
                kayitlar = [("basvuru_baslangic", t1)]
            else:
                kayitlar = [("basvuru_bitis", t1)]
        else:
            kayitlar = [(tur, t1)]

        for olay_turu, gun in kayitlar:
            anahtar = (olay_turu, gun.isoformat())
            if anahtar in olaylar:
                if saat and not olaylar[anahtar]["saat"]:
                    olaylar[anahtar]["saat"] = saat
                continue
            olaylar[anahtar] = {"tur": olay_turu, "tarih": gun.isoformat(),
                                "saat": saat if olay_turu != "basvuru_baslangic" else None,
                                "alinti": alinti}
    # Makul aralık dışındaki tarihler (kanun/yönetmelik tarihleri vb.) ve
    # belirli türde bir olayla aynı güne düşen "diğer" tarihler atılır
    en_erken = date.fromordinal(referans.toordinal() - 120).isoformat()
    en_gec = date.fromordinal(referans.toordinal() + 400).isoformat()
    belirli_gunler = {o["tarih"] for o in olaylar.values() if o["tur"] != "diger"}
    sonuc = [o for o in olaylar.values()
             if en_erken <= o["tarih"] <= en_gec
             and not (o["tur"] == "diger" and o["tarih"] in belirli_gunler)]
    return sorted(sonuc, key=lambda o: (o["tarih"], o["tur"]))


def yayim_tarihi(metin: str) -> date | None:
    """'24 Ekim 2025 | 14:38' ya da '03.10.2026' gibi bir başlıktan yayım tarihini okur."""
    m = re.search(rf"\b(\d{{1,2}})\s+{_AY}\s+(\d{{4}})", tr_kucuk(metin))
    s = None if m else re.search(r"\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b", metin)
    try:
        if m:
            return date(int(m.group(3)), AYLAR[m.group(2)], int(m.group(1)))
        if s:
            return date(int(s.group(3)), int(s.group(2)), int(s.group(1)))
    except ValueError:
        pass
    return None
