"""Türkiye saati yardımcıları (Türkiye 2016'dan beri sabit UTC+3, yaz saati yok)."""

from datetime import date, datetime, timedelta, timezone

TR = timezone(timedelta(hours=3), "TR")

AY_ADLARI = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
             "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def simdi() -> datetime:
    return datetime.now(TR)


def okunur_tarih(gun: date) -> str:
    """date(2026, 10, 24) -> '24 Ekim Cumartesi'"""
    return f"{gun.day} {AY_ADLARI[gun.month]} {GUN_ADLARI[gun.weekday()]}"


def tarih_saat(gun: str, saat: str | None) -> datetime:
    """'2026-10-24', '09:00' -> TR saatli datetime (saat yoksa 00:00)."""
    s, d = (saat or "00:00").split(":")
    return datetime.fromisoformat(gun).replace(hour=int(s), minute=int(d), tzinfo=TR)
