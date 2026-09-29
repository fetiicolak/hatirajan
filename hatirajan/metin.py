"""Türkçe metin yardımcıları: büyük/küçük harf, sadeleştirme, anahtar kelime eşleşmesi."""

import re

_SADE = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def tr_kucuk(metin: str) -> str:
    """Türkçe kurallarıyla küçük harfe çevirir; karakter sayısı (indeksler) korunur."""
    return metin.replace("I", "ı").replace("İ", "i").lower()


def sadelestir(metin: str) -> str:
    """'İŞKUR Gençlik' -> 'iskur genclik' : aksansız, küçük harf, tek boşluk."""
    metin = tr_kucuk(metin).translate(_SADE)
    return re.sub(r"\s+", " ", metin).strip()


def ilgili_mi(baslik: str, anahtar_kelimeler: list[str], dislanan: list[str] | None = None) -> bool:
    """Başlık anahtar kelimelerden biriyle eşleşiyor mu?

    Her anahtar kelime tek başına yeterlidir. 'erasmus & dil sınavı' yazımı,
    '&' ile ayrılmış parçaların HEPSİNİN geçmesi gerektiği anlamına gelir.
    """
    sade = sadelestir(baslik)
    if any(sadelestir(d) in sade for d in (dislanan or []) if d.strip()):
        return False
    for kelime in anahtar_kelimeler:
        parcalar = [sadelestir(p) for p in kelime.split("&") if p.strip()]
        if parcalar and all(p in sade for p in parcalar):
            return True
    return False


def kategori(baslik: str) -> str:
    """Duyurunun türünü başlığından tahmin eder (bildirim simgesi için)."""
    sade = sadelestir(baslik)
    if any(k in sade for k in ("salon", "sinav yer", "sinav yeri", "derslik")):
        return "sinav_yeri"
    if any(k in sade for k in ("sonuc", "kura", "kazanan", "asil", "yedek")):
        return "sonuc"
    if "basvuru" in sade or "kayit" in sade:
        return "basvuru"
    if "sinav" in sade:
        return "sinav"
    return "duyuru"
