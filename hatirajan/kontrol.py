"""Görevlerin kaynaklarını tarar, yeni ilgili duyuruları bulur, tarihleri ayıklar ve bildirir."""

import html
from datetime import date, datetime, timedelta

from . import depo
from .cekici import CekmeHatasi, Duyuru, EngelHatasi, Oturum, duyuru_kimligi
from .hatirlatma import plan_ozeti
from .metin import ilgili_mi, kategori, sadelestir
from .tarihler import TUR_ADLARI, tarihleri_ayikla
from .zaman import okunur_tarih

SIMGELER = {"basvuru": "📝", "sinav": "✏️", "sinav_yeri": "📍", "sonuc": "🏁", "duyuru": "📢"}
KATEGORI_ADLARI = {"basvuru": "Başvuru duyurusu", "sinav": "Sınav duyurusu",
                   "sinav_yeri": "Sınav yeri / saati", "sonuc": "Sonuç duyurusu", "duyuru": "Yeni duyuru"}
HATA_ESIGI = 3  # art arda bu kadar başarısız denemede uyarı (≈1,5 gün)


def _kaynak_url(kaynak) -> str:
    return kaynak if isinstance(kaynak, str) else kaynak["url"]


def _olaylari_birlestir(gd: dict, yeni_olaylar: list[dict], duyuru: dict) -> list[str]:
    """Yeni tarihleri görev durumuna ekler; ertelenen son başvuru tarihlerini işaretler.

    Dönen liste: güncellenen (geçersiz kalan) eski tarihlerin açıklamaları.
    """
    guncellenen = []
    mevcut = {(o["tur"], o["tarih"]): o for o in gd["olaylar"]}
    for olay in yeni_olaylar:
        anahtar = (olay["tur"], olay["tarih"])
        if anahtar in mevcut:
            if olay.get("saat") and not mevcut[anahtar].get("saat"):
                mevcut[anahtar]["saat"] = olay["saat"]
            continue
        # Başvuru süresi uzatıldıysa: başka duyurudaki, en fazla 60 gün önceki son başvuru tarihi geçersiz
        yeni_gun = date.fromisoformat(olay["tarih"])
        for eski in gd["olaylar"]:
            if (olay["tur"] == "basvuru_bitis" and eski["tur"] == "basvuru_bitis"
                    and not eski.get("gecersiz") and eski.get("duyuru_url") != duyuru["url"]
                    and 0 < (yeni_gun - date.fromisoformat(eski["tarih"])).days <= 60):
                eski["gecersiz"] = True
                guncellenen.append(f"{TUR_ADLARI[eski['tur']]} {okunur_tarih(date.fromisoformat(eski['tarih']))}")
        kayit = {k: olay[k] for k in ("tur", "tarih", "saat")}
        kayit.update(duyuru_url=duyuru["url"], duyuru_baslik=duyuru["baslik"], bulundu=duyuru["bulundu"])
        gd["olaylar"].append(kayit)
        mevcut[anahtar] = kayit
    gd["olaylar"].sort(key=lambda o: o["tarih"])
    return guncellenen


def _duyuru_mesaji(gorev: dict, kayit: dict, guncellenen: list[str], hatirlatmalar: list[str]) -> str:
    kat = kayit["kategori"]
    satirlar = [f"{SIMGELER[kat]} <b>{html.escape(gorev['ad'])}</b> · {KATEGORI_ADLARI[kat]}",
                f"<b>{html.escape(kayit['baslik'])}</b>"]
    belirli = [o for o in kayit["olaylar"] if o["tur"] != "diger"]
    gosterilecek = belirli or kayit["olaylar"][:3]
    if gosterilecek:
        for o in gosterilecek:
            gun = date.fromisoformat(o["tarih"])
            ad = TUR_ADLARI[o["tur"]] if o["tur"] != "diger" else "Tarih"
            satirlar.append(f"📅 {ad}: {okunur_tarih(gun)}"
                            + (f", {o['saat']}" if o.get("saat") else ""))
    elif not kayit.get("detay_hatasi"):
        satirlar.append("ℹ️ Metinde tarih bulunamadı — duyuruya göz at.")
    if kayit.get("detay_hatasi"):
        satirlar.append(f"⚠️ Duyuru açılamadı ({html.escape(kayit['detay_hatasi'])}) — linkten kontrol et.")
    if guncellenen:
        satirlar.append("🔄 Güncellenen eski tarih: " + ", ".join(guncellenen))
    satirlar.append(f"🔗 {kayit['url']}")
    for ek in kayit.get("ekler", [])[:3]:
        satirlar.append(f"📎 {ek}")
    if hatirlatmalar:
        satirlar.append("⏰ Hatırlatmalar: " + ", ".join(hatirlatmalar))
    return "\n".join(satirlar)


def _kaynak_hatasi(durum: dict, url: str, hata: CekmeHatasi, simdi: datetime, gonder) -> None:
    kd = durum["kaynaklar"].setdefault(url, {})
    kd["hata_sayisi"] = kd.get("hata_sayisi", 0) + 1
    kd["son_hata"] = str(hata)
    kd["son_hata_zamani"] = simdi.isoformat(timespec="minutes")
    engel = isinstance(hata, EngelHatasi)
    if (engel or kd["hata_sayisi"] >= HATA_ESIGI) and not kd.get("uyari_gonderildi"):
        gonder(f"⚠️ <b>Kaynak okunamıyor</b>\n{html.escape(url)}\nSebep: {html.escape(str(hata))}\n"
               + ("Site bot doğrulaması istiyor; lütfen elle kontrol et." if engel
                  else f"Art arda {kd['hata_sayisi']} deneme başarısız. Sistem denemeye devam ediyor."))
        kd["uyari_gonderildi"] = True


def _kaynak_basarili(durum: dict, url: str, simdi: datetime, gonder) -> None:
    kd = durum["kaynaklar"].setdefault(url, {})
    if kd.get("uyari_gonderildi"):
        gonder(f"✅ <b>Kaynak yeniden okunabiliyor</b>\n{html.escape(url)}")
    kd.update(hata_sayisi=0, uyari_gonderildi=False, son_basari=simdi.isoformat(timespec="minutes"))
    kd.pop("son_hata", None)


def _duyuruyu_isle(oturum: Oturum, gorev: dict, gd: dict, d: Duyuru, ilk_tarama: bool,
                   simdi: datetime, gonder) -> None:
    kayit = {"url": d.url, "baslik": d.baslik, "kategori": kategori(d.baslik),
             "bulundu": simdi.isoformat(timespec="minutes"), "olaylar": [], "ekler": []}
    try:
        detay = oturum.duyuru_detayi(d)
        referans = date.fromisoformat(detay.yayim) if detay.yayim else simdi.date()
        kayit["yayim"] = detay.yayim
        kayit["olaylar"] = tarihleri_ayikla(f"{d.baslik}. {detay.metin}", referans)
        kayit["ekler"] = [e for e in detay.ekler if not e.lower().endswith((".jpg", ".jpeg", ".png"))]
    except CekmeHatasi as e:
        kayit["detay_hatasi"] = str(e)

    bugun = simdi.date().isoformat()
    if ilk_tarama and not any(o["tarih"] >= bugun for o in kayit["olaylar"]):
        return  # sistem ilk kurulduğunda eski/bitmiş duyurular için bildirim atma

    # Aynı duyuru birden fazla birim sitesinde yayımlanabiliyor: 60 gün içinde aynı başlık → tekrar bildirme
    sinir = (simdi - timedelta(days=60)).isoformat()
    sade = sadelestir(d.baslik)
    tekrar = any(sadelestir(x["baslik"]) == sade and x["bulundu"] >= sinir for x in gd["duyurular"])

    guncellenen = _olaylari_birlestir(gd, kayit["olaylar"], kayit)
    for o in kayit["olaylar"]:
        o.pop("alinti", None)
    if tekrar:
        return
    gd["duyurular"].insert(0, kayit)
    del gd["duyurular"][50:]
    yeni_olaylar = [o for o in gd["olaylar"] if o.get("duyuru_url") == d.url]
    gonder(_duyuru_mesaji(gorev, kayit, guncellenen, plan_ozeti(gorev, yeni_olaylar, simdi)))


def calistir(ayar: dict, durum: dict, simdi: datetime, gonder, oturum: Oturum | None = None) -> None:
    oturum = oturum or Oturum()
    bugun = simdi.date().isoformat()
    for gorev in ayar["gorevler"]:
        if not gorev.get("aktif", True):
            continue
        gd = depo.gorev_durumu(durum, gorev["id"])
        for kaynak in gorev.get("kaynaklar", []):
            url = _kaynak_url(kaynak)
            try:
                duyurular = oturum.duyurulari_listele(kaynak)
            except CekmeHatasi as e:
                _kaynak_hatasi(durum, url, e, simdi, gonder)
                continue
            _kaynak_basarili(durum, url, simdi, gonder)
            ilk_tarama = url not in gd["taranan_kaynaklar"]
            for d in reversed(duyurular):  # listeler yeniden eskiye; eskiden yeniye işle
                kimlik = duyuru_kimligi(d.url)
                if kimlik in gd["gorulen"]:
                    continue
                gd["gorulen"][kimlik] = bugun
                if ilgili_mi(d.baslik, gorev.get("anahtar_kelimeler", []), gorev.get("dislanan_kelimeler")):
                    _duyuruyu_isle(oturum, gorev, gd, d, ilk_tarama, simdi, gonder)
            if ilk_tarama:
                gd["taranan_kaynaklar"].append(url)

        # bir yıldan eski "görüldü" kayıtlarını temizle
        sinir = (simdi - timedelta(days=365)).date().isoformat()
        gd["gorulen"] = {k: v for k, v in gd["gorulen"].items() if v >= sinir}

    durum["son_kontrol"] = simdi.isoformat(timespec="minutes")
