"""Hatırlatma planlama/gönderme ve haftalık özet.

Görev yapılandırmasındaki kural örneği:
  {"olay": "basvuru_bitis", "gun_once": 3, "saat": "09:00"}
Özel (tek seferlik) hatırlatma:
  {"id": "a1b2", "tarih": "2026-10-20", "saat": "10:00", "not": "Belgeleri hazırla"}
"""

import html
from datetime import datetime, timedelta

from .tarihler import TUR_ADLARI
from .zaman import AY_ADLARI, okunur_tarih, tarih_saat

GECIKME_TOLERANSI = timedelta(hours=36)  # kaçırılan hatırlatma en fazla bu kadar geç gönderilir


def _kalan(gun: str, simdi: datetime) -> str:
    fark = (datetime.fromisoformat(gun).date() - simdi.date()).days
    return {0: "bugün", 1: "yarın"}.get(fark, f"{fark} gün sonra" if fark > 0 else "geçti")


def planla(gorev: dict, olaylar: list[dict]) -> list[dict]:
    """Görevin bütün hatırlatmalarını zamanlarıyla döndürür (geçmiş dahil)."""
    plan = []
    for olay in olaylar:
        if olay.get("gecersiz"):
            continue
        for kural in gorev.get("hatirlatmalar", []):
            if kural.get("olay") != olay["tur"]:
                continue
            gun_once = int(kural.get("gun_once", 0))
            saat = kural.get("saat") or "09:00"
            zaman = tarih_saat(olay["tarih"], saat) - timedelta(days=gun_once)
            plan.append({
                "anahtar": f"{gorev['id']}|{olay['tur']}|{olay['tarih']}|{gun_once}|{saat}",
                "olay_anahtari": f"{olay['tur']}|{olay['tarih']}",
                "zaman": zaman, "olay": olay,
            })
    for ozel in gorev.get("ozel_hatirlatmalar", []):
        if not ozel.get("tarih"):
            continue
        plan.append({
            "anahtar": f"{gorev['id']}|ozel|{ozel.get('id') or ozel['tarih']}|{ozel.get('saat', '09:00')}",
            "olay_anahtari": f"ozel|{ozel.get('id') or ozel['tarih']}",
            "zaman": tarih_saat(ozel["tarih"], ozel.get("saat") or "09:00"), "ozel": ozel,
        })
    return sorted(plan, key=lambda p: p["zaman"])


def plan_ozeti(gorev: dict, olaylar: list[dict], simdi: datetime) -> list[str]:
    """Duyuru bildirimine eklenecek 'kurulan hatırlatmalar' satırları."""
    return [f"{p['zaman'].day} {AY_ADLARI[p['zaman'].month]} {p['zaman']:%H:%M}"
            for p in planla(gorev, olaylar) if "olay" in p and p["zaman"] > simdi]


def _mesaj(gorev: dict, p: dict, simdi: datetime) -> str:
    baslik = f"⏰ <b>{html.escape(gorev['ad'])}</b>"
    if "ozel" in p:
        oz = p["ozel"]
        return f"{baslik}\n📌 {html.escape(oz.get('not') or 'Özel hatırlatma')}"
    olay = p["olay"]
    gun = datetime.fromisoformat(olay["tarih"]).date()
    satir = f"{TUR_ADLARI.get(olay['tur'], olay['tur'])}: <b>{_kalan(olay['tarih'], simdi)}</b> — {okunur_tarih(gun)}"
    if olay.get("saat"):
        satir += f", {olay['saat']}"
    mesaj = f"{baslik}\n{satir}"
    if olay.get("duyuru_baslik"):
        mesaj += f"\n📄 {html.escape(olay['duyuru_baslik'])}"
    if olay.get("duyuru_url"):
        mesaj += f"\n🔗 {olay['duyuru_url']}"
    return mesaj


def hatirlatmalari_isle(ayar: dict, durum: dict, simdi: datetime, gonder) -> int:
    """Zamanı gelen hatırlatmaları gönderir; gönderilen sayısını döndürür.

    Aynı olay için birden çok hatırlatma aynı anda vadesi gelmişse (ör. tarih geç
    bulunduysa) yalnızca en günceli gönderilir, diğerleri gönderilmiş sayılır.
    """
    gonderilen = durum["gonderilen_hatirlatmalar"]
    sayi = 0
    for gorev in ayar["gorevler"]:
        if not gorev.get("aktif", True):
            continue
        olaylar = durum["gorevler"].get(gorev["id"], {}).get("olaylar", [])
        vadesi_gelen: dict[str, list[dict]] = {}
        for p in planla(gorev, olaylar):
            if p["anahtar"] not in gonderilen and p["zaman"] <= simdi < p["zaman"] + GECIKME_TOLERANSI:
                vadesi_gelen.setdefault(p["olay_anahtari"], []).append(p)
        for grup in vadesi_gelen.values():
            gonder(_mesaj(gorev, grup[-1], simdi))
            sayi += 1
            for p in grup:
                gonderilen[p["anahtar"]] = simdi.isoformat(timespec="minutes")

    sinir = (simdi - timedelta(days=120)).isoformat()
    for anahtar in [a for a, z in gonderilen.items() if z < sinir]:
        del gonderilen[anahtar]
    return sayi


def haftalik_ozet_zamani_mi(ayar: dict, durum: dict, simdi: datetime) -> bool:
    oz = ayar.get("ayarlar", {}).get("haftalik_ozet", {})
    if not oz.get("aktif", True):
        return False
    gun = int(oz.get("gun", 6))  # 0=Pazartesi ... 6=Pazar
    saat, dakika = map(int, (oz.get("saat") or "20:00").split(":"))
    hafta = "{}-W{:02d}".format(*simdi.isocalendar()[:2])
    return (simdi.weekday() == gun and (simdi.hour, simdi.minute) >= (saat, dakika)
            and durum.get("son_ozet_haftasi") != hafta)


def haftalik_ozet(ayar: dict, durum: dict, simdi: datetime) -> str:
    satirlar = ["📋 <b>HatırAjan haftalık özet</b>"]
    son = durum.get("son_kontrol")
    if son:
        son_dt = datetime.fromisoformat(son)
        uyari = " ⚠️ (2 günden eski — kontrol çalışmıyor olabilir)" if simdi - son_dt > timedelta(days=2) else " ✅"
        satirlar.append(f"Son kontrol: {son_dt.day} {AY_ADLARI[son_dt.month]} {son_dt:%H:%M}{uyari}")
    else:
        satirlar.append("Son kontrol: henüz yapılmadı ⚠️")

    hafta_once = (simdi - timedelta(days=7)).isoformat()
    for gorev in ayar["gorevler"]:
        if not gorev.get("aktif", True):
            continue
        gd = durum["gorevler"].get(gorev["id"], {})
        yeni = [d for d in gd.get("duyurular", []) if d.get("bulundu", "") >= hafta_once]
        yaklasan = sorted((o for o in gd.get("olaylar", [])
                           if not o.get("gecersiz") and o["tarih"] >= simdi.date().isoformat()),
                          key=lambda o: o["tarih"])
        satirlar.append(f"\n<b>{html.escape(gorev['ad'])}</b>")
        satirlar.append(f"  Bu hafta: {len(yeni)} yeni duyuru" if yeni else "  Bu hafta: yeni duyuru yok")
        for o in yaklasan[:4]:
            gun = datetime.fromisoformat(o["tarih"]).date()
            satirlar.append(f"  • {TUR_ADLARI.get(o['tur'], o['tur'])}: {okunur_tarih(gun)} ({_kalan(o['tarih'], simdi)})")
        if not yaklasan:
            satirlar.append("  Yaklaşan tarih yok — takipte.")

    hatali = [url for url, k in durum.get("kaynaklar", {}).items() if k.get("hata_sayisi", 0) > 0]
    if hatali:
        satirlar.append("\n⚠️ Okunamayan kaynaklar:\n" + "\n".join(f"  • {u}" for u in hatali))
    return "\n".join(satirlar)


def ozet_gonderildi(durum: dict, simdi: datetime) -> None:
    durum["son_ozet_haftasi"] = "{}-W{:02d}".format(*simdi.isocalendar()[:2])
