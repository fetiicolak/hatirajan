"""HatırAjan testleri — internet gerektirmez.  Çalıştırma:  python -m unittest -v"""

import unittest
from datetime import date, datetime
from pathlib import Path

from hatirajan import depo, hatirlatma, kontrol
from hatirajan.cekici import CekmeHatasi, Duyuru, DuyuruDetayi, engel_sayfasi_mi
from hatirajan.metin import ilgili_mi, kategori
from hatirajan.tarihler import tarihleri_ayikla
from hatirajan.zaman import TR

ORNEKLER = Path(__file__).parent / "ornekler"
ERASMUS_ANAHTAR = ["yabancı dil yeterlik & değişim", "yabancı dil yeterlik & erasmus", "erasmus & dil sınav"]
KURALLAR = [
    {"olay": "basvuru_baslangic", "gun_once": 0, "saat": "09:00"},
    {"olay": "basvuru_bitis", "gun_once": 3, "saat": "09:00"},
    {"olay": "basvuru_bitis", "gun_once": 1, "saat": "09:00"},
    {"olay": "sinav", "gun_once": 1, "saat": "20:00"},
]


def ornek(ad: str) -> tuple[str, date, str]:
    baslik, yayim, icerik = (ORNEKLER / ad).read_text(encoding="utf-8").split("\n", 2)
    return baslik, date.fromisoformat(yayim), icerik


def ozet(olaylar):
    return [(o["tur"], o["tarih"], o["saat"]) for o in olaylar]


class TarihAyiklama(unittest.TestCase):
    def test_gercek_erasmus_duyurusu(self):
        baslik, yayim, icerik = ornek("erasmus_dil_sinavi_2025.txt")
        self.assertEqual(ozet(tarihleri_ayikla(f"{baslik}. {icerik}", yayim)),
                         [("sinav", "2025-11-05", "09:30")])

    def test_gercek_iskur_duyurusu(self):
        baslik, yayim, icerik = ornek("iskur_basvuru_2025.txt")
        olaylar = ozet(tarihleri_ayikla(f"{baslik}. {icerik}", yayim))
        self.assertIn(("basvuru_baslangic", "2025-10-13", None), olaylar)
        self.assertIn(("basvuru_bitis", "2025-10-17", None), olaylar)
        self.assertNotIn("sinav", [o[0] for o in olaylar])

    def test_sayisal_aralik_ve_son_gun(self):
        metin = "Başvurular 20.10.2026 - 24.10.2026 tarihleri arasında alınacaktır. Sınav 5 Kasım 2026 saat 10:00'da yapılacaktır."
        self.assertEqual(ozet(tarihleri_ayikla(metin, date(2026, 10, 1))), [
            ("basvuru_baslangic", "2026-10-20", None),
            ("basvuru_bitis", "2026-10-24", None),
            ("sinav", "2026-11-05", "10:00"),
        ])

    def test_yilsiz_tarih_ve_son_basvuru(self):
        metin = "Son başvuru tarihi 3 Ocak'tır."
        self.assertEqual(ozet(tarihleri_ayikla(metin, date(2026, 12, 20))),
                         [("basvuru_bitis", "2027-01-03", None)])

    def test_iki_ayli_aralik(self):
        metin = "Program 03 Kasım – 24 Mayıs 2026 tarihleri arasında uygulanacaktır."
        self.assertEqual(ozet(tarihleri_ayikla(metin, date(2025, 10, 13))), [("diger", "2025-11-03", None)])

    def test_alakasiz_eski_tarih_atilir(self):
        metin = "08.03.2012 tarihli yönetmelik uyarınca sonuçlar 20 Ekim 2026'da ilan edilecektir."
        self.assertEqual(ozet(tarihleri_ayikla(metin, date(2026, 10, 1))), [("sonuc", "2026-10-20", None)])


class Metin(unittest.TestCase):
    def test_iskur_eslesmesi(self):
        self.assertTrue(ilgili_mi("İŞKUR Gençlik Programı Başvuruları Başladı", ["iskur"]))
        self.assertFalse(ilgili_mi("TEKNOFEST'te Katılacak Takımlar", ["iskur", "gençlik programı"]))

    def test_erasmus_eslesmesi(self):
        self.assertTrue(ilgili_mi("3 Mart 2026 Değişim Programları (Erasmus vb.) Yabancı Dil Yeterlik Sınavı", ERASMUS_ANAHTAR))
        self.assertFalse(ilgili_mi("22 Eylül 2026 DGS ... Hazırlık Yeterlik (Muafiyet) Sınavı Salonları", ERASMUS_ANAHTAR))
        self.assertFalse(ilgili_mi("2025 Erasmus KA131 Personel Hareketliliği Sonuçları", ERASMUS_ANAHTAR))

    def test_dislanan(self):
        self.assertFalse(ilgili_mi("İŞKUR Gençlik Programı Sigorta İşlemleri", ["iskur"], ["sigorta"]))

    def test_kategori(self):
        self.assertEqual(kategori("... Yabancı Dil Yeterlik Sınavı Salonları"), "sinav_yeri")
        self.assertEqual(kategori("İŞKUR Gençlik Programı Sonuçları"), "sonuc")
        self.assertEqual(kategori("İŞKUR Gençlik Programı Başvuruları Başladı"), "basvuru")

    def test_engel_sayfasi(self):
        self.assertTrue(engel_sayfasi_mi("<html><title>Just a moment...</title></html>"))
        self.assertFalse(engel_sayfasi_mi("<script src='recaptcha'></script>" + "x" * 40_000))


class Hatirlatma(unittest.TestCase):
    def setUp(self):
        self.gorev = {"id": "g", "ad": "Deneme", "hatirlatmalar": KURALLAR, "ozel_hatirlatmalar": []}
        self.ayar = {"gorevler": [self.gorev], "ayarlar": {}}
        self.durum = {"gorevler": {"g": {"olaylar": [
            {"tur": "basvuru_bitis", "tarih": "2026-10-24", "saat": None},
            {"tur": "sinav", "tarih": "2026-11-05", "saat": "09:30"},
        ]}}, "kaynaklar": {}, "gonderilen_hatirlatmalar": {}}
        self.giden = []

    def isle(self, *zaman):
        return hatirlatma.hatirlatmalari_isle(self.ayar, self.durum, datetime(*zaman, tzinfo=TR), self.giden.append)

    def test_uc_gun_ve_bir_gun_once(self):
        self.assertEqual(self.isle(2026, 10, 21, 8, 59), 0)
        self.assertEqual(self.isle(2026, 10, 21, 9, 20), 1)
        self.assertIn("3 gün sonra", self.giden[-1])
        self.assertEqual(self.isle(2026, 10, 21, 10, 20), 0)  # ikinci kez gönderilmez
        self.assertEqual(self.isle(2026, 10, 23, 9, 20), 1)
        self.assertIn("yarın", self.giden[-1])

    def test_dorduncu_hatirlatma_eklenebilir(self):
        self.gorev["hatirlatmalar"] = KURALLAR + [{"olay": "basvuru_bitis", "gun_once": 7, "saat": "10:00"}]
        self.assertEqual(self.isle(2026, 10, 17, 10, 20), 1)
        self.assertIn("7 gün sonra", self.giden[-1])

    def test_gec_bulunan_tarihte_tek_mesaj(self):
        # 3 gün ve 1 gün önceki hatırlatmaların ikisi de vadesi geçmiş: yalnızca biri gider
        self.assertEqual(self.isle(2026, 10, 23, 12, 0), 1)
        self.assertEqual(self.isle(2026, 10, 23, 13, 0), 0)

    def test_sinav_saati(self):
        self.isle(2026, 11, 4, 20, 20)
        self.assertIn("09:30", self.giden[-1])

    def test_ozel_hatirlatma(self):
        self.gorev["ozel_hatirlatmalar"] = [{"id": "x", "tarih": "2026-10-10", "saat": "18:00", "not": "Belgeleri hazırla"}]
        self.assertEqual(self.isle(2026, 10, 10, 18, 20), 1)
        self.assertIn("Belgeleri hazırla", self.giden[-1])

    def test_haftalik_ozet_pazar_20(self):
        self.assertFalse(hatirlatma.haftalik_ozet_zamani_mi(self.ayar, self.durum, datetime(2026, 9, 27, 19, 20, tzinfo=TR)))
        pazar = datetime(2026, 9, 27, 20, 20, tzinfo=TR)
        self.assertTrue(hatirlatma.haftalik_ozet_zamani_mi(self.ayar, self.durum, pazar))
        hatirlatma.ozet_gonderildi(self.durum, pazar)
        self.assertFalse(hatirlatma.haftalik_ozet_zamani_mi(self.ayar, self.durum, datetime(2026, 9, 27, 21, 20, tzinfo=TR)))


class SahteOturum:
    """İnternetsiz kontrol testi için site taklidi."""

    def __init__(self, liste, detaylar, hatali=()):
        self.liste, self.detaylar, self.hatali = liste, detaylar, set(hatali)

    def duyurulari_listele(self, kaynak):
        if kaynak in self.hatali:
            raise CekmeHatasi("HTTP 500")
        return self.liste

    def duyuru_detayi(self, d):
        metin, yayim = self.detaylar[d.url]
        return DuyuruDetayi(d.baslik, metin, yayim, [])


class Kontrol(unittest.TestCase):
    KAYNAK = "https://ydyo.gazi.edu.tr/view/announcement-list/1?Type=1"

    def setUp(self):
        self.ayar = {"ayarlar": {}, "gorevler": [{
            "id": "erasmus", "ad": "Erasmus Dil", "kaynaklar": [self.KAYNAK],
            "anahtar_kelimeler": ERASMUS_ANAHTAR, "hatirlatmalar": KURALLAR}]}
        self.durum = {"gorevler": {}, "kaynaklar": {}, "gonderilen_hatirlatmalar": {}}
        self.giden = []
        self.eski = Duyuru("https://ydyo.gazi.edu.tr/view/announcement/1", "Oryantasyon Programı")

    def calistir(self, oturum, *zaman):
        kontrol.calistir(self.ayar, self.durum, datetime(*zaman, tzinfo=TR), self.giden.append, oturum)

    def test_ilk_tarama_sessiz_sonra_yeni_duyuru_bildirilir(self):
        self.calistir(SahteOturum([self.eski], {}), 2026, 9, 23, 8)
        self.assertEqual(self.giden, [])

        yeni = Duyuru("https://ydyo.gazi.edu.tr/view/announcement/2?title=x",
                      "4 Kasım 2026 Değişim Programları (Erasmus vb.) Yabancı Dil Yeterlik Sınavı")
        detay = ("Başvurular 20-24 Ekim 2026 tarihleri arasında alınacaktır. Sınav saat 09.30'da başlayacaktır.", "2026-10-15")
        self.calistir(SahteOturum([yeni, self.eski], {yeni.url: detay}), 2026, 10, 15, 17)
        self.assertEqual(len(self.giden), 1)
        mesaj = self.giden[0]
        self.assertIn("Son başvuru: 24 Ekim", mesaj)
        self.assertIn("Sınav: 4 Kasım", mesaj)
        self.assertIn("⏰ Hatırlatmalar: 20 Ekim 09:00, 21 Ekim 09:00, 23 Ekim 09:00, 3 Kasım 20:00", mesaj)

        # aynı duyuru tekrar görülünce bildirim yok
        self.calistir(SahteOturum([yeni, self.eski], {yeni.url: detay}), 2026, 10, 16, 8)
        self.assertEqual(len(self.giden), 1)

    def test_ilk_taramada_gelecek_tarihli_duyuru_bildirilir(self):
        d = Duyuru("https://ydyo.gazi.edu.tr/view/announcement/3", "Değişim Programları (Erasmus vb.) Yabancı Dil Yeterlik Sınavı")
        self.calistir(SahteOturum([d], {d.url: ("Sınav 4 Kasım 2026 tarihinde yapılacaktır.", "2026-09-20")}), 2026, 9, 23, 8)
        self.assertEqual(len(self.giden), 1)

    def test_kaynak_hatasi_ucuncu_denemede_bir_kez_uyarir(self):
        oturum = SahteOturum([], {}, hatali=[self.KAYNAK])
        for saat in (8, 17, 8, 17):
            self.calistir(oturum, 2026, 9, 23, saat)
        self.assertEqual(len(self.giden), 1)
        self.assertIn("Kaynak okunamıyor", self.giden[0])
        self.calistir(SahteOturum([self.eski], {}), 2026, 9, 24, 8)
        self.assertIn("yeniden okunabiliyor", self.giden[-1])

    def test_kontrol_zamani_atlanan_taramayi_telafi_eder(self):
        z = lambda s: datetime.fromisoformat(s).replace(tzinfo=TR)
        self.assertFalse(kontrol.kontrol_zamani_mi({}, z("2026-09-30T07:40")))
        self.assertTrue(kontrol.kontrol_zamani_mi({"son_kontrol": "2026-09-29T17:10+03:00"}, z("2026-09-30T08:37")))
        self.assertTrue(kontrol.kontrol_zamani_mi({"son_kontrol": "2026-09-29T17:10+03:00"}, z("2026-09-30T11:07")))
        self.assertFalse(kontrol.kontrol_zamani_mi({"son_kontrol": "2026-09-30T08:07+03:00"}, z("2026-09-30T16:37")))
        self.assertTrue(kontrol.kontrol_zamani_mi({"son_kontrol": "2026-09-30T08:07+03:00"}, z("2026-09-30T17:07")))

    def test_tarama_raporu_acikken_her_taramada_gelir(self):
        self.ayar["ayarlar"]["tarama_raporu"] = {"aktif": True}
        self.calistir(SahteOturum([self.eski], {}), 2026, 9, 23, 8)
        self.assertEqual(len(self.giden), 1)
        self.assertIn("Tarama tamamlandı", self.giden[0])
        self.assertIn("Erasmus Dil: yeni bilgi yok", self.giden[0])

        yeni = Duyuru("https://ydyo.gazi.edu.tr/view/announcement/2", "Değişim Programları (Erasmus vb.) Yabancı Dil Yeterlik Sınavı")
        detay = ("Sınav 4 Kasım 2026 tarihinde yapılacaktır.", "2026-10-15")
        self.calistir(SahteOturum([yeni, self.eski], {yeni.url: detay}), 2026, 10, 15, 17)
        self.assertEqual(len(self.giden), 3)  # duyuru + rapor
        self.assertIn("1 yeni duyuru", self.giden[-1])


class Yapilandirma(unittest.TestCase):
    def test_gorevler_dosyasi_gecerli(self):
        ayar = depo.gorevleri_yukle()
        kimlikler = [g["id"] for g in ayar["gorevler"]]
        self.assertEqual(len(kimlikler), len(set(kimlikler)))
        for g in ayar["gorevler"]:
            self.assertTrue(g["kaynaklar"] and g["anahtar_kelimeler"] and g["ad"])


if __name__ == "__main__":
    unittest.main()
