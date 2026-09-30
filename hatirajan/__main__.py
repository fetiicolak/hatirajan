"""HatırAjan komut satırı.

  python -m hatirajan otomatik         # zamanlanmış çalıştırma: vakti geldiyse kontrol, sonra hatirlat
  python -m hatirajan kontrol          # kaynakları tara, yeni duyuruları bildir
  python -m hatirajan hatirlat         # zamanı gelen hatırlatmalar + (Pazar 20:00) haftalık özet
  python -m hatirajan ozet             # haftalık özeti hemen gönder
  python -m hatirajan test-telegram    # tek bir deneme mesajı gönder
  python -m hatirajan chat-id          # bota yazan sohbetlerin chat ID'sini göster (kurulum)

  --kuru              Telegram yerine konsola yaz, durum dosyasını KAYDETME
  --simdi 2026-10-21T09:30   Saati elle ver (hatırlatma denemeleri için)
"""

import argparse
import sys
from datetime import datetime

from . import bildirim, depo, hatirlatma, kontrol
from .zaman import TR, simdi as simdi_al


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ayrac = argparse.ArgumentParser(prog="hatirajan", description="HatırAjan duyuru takip ajanı")
    ayrac.add_argument("islem", choices=["otomatik", "kontrol", "hatirlat", "ozet", "test-telegram", "chat-id"])
    ayrac.add_argument("--kuru", action="store_true", help="Telegram'a gönderme, durumu kaydetme")
    ayrac.add_argument("--simdi", help="ISO tarih-saat (TR), ör. 2026-10-21T09:30")
    arg = ayrac.parse_args()

    simdi = datetime.fromisoformat(arg.simdi).replace(tzinfo=TR) if arg.simdi else simdi_al()
    gonder = bildirim.konsola_yaz if arg.kuru else bildirim.gonder

    if arg.islem == "chat-id":
        sohbetler = bildirim.sohbetleri_bul()
        if not sohbetler:
            print("Hiç mesaj bulunamadı. Botu açıp Başlat'a bas, bir mesaj yaz ve tekrar dene.")
        for kimlik, ad in sohbetler:
            print(f"chat ID: {kimlik}   ({ad})")
        return 0

    if arg.islem == "test-telegram":
        gonder("✅ <b>HatırAjan</b> bağlantı testi başarılı. Bildirimler bu sohbete gelecek.")
        return 0

    ayar = depo.gorevleri_yukle()
    durum = depo.durumu_yukle()

    if arg.islem == "kontrol" or (arg.islem == "otomatik" and kontrol.kontrol_zamani_mi(durum, simdi)):
        kontrol.calistir(ayar, durum, simdi, gonder)
        print(f"Kontrol tamamlandı: {simdi:%Y-%m-%d %H:%M}")
    if arg.islem in ("hatirlat", "otomatik"):
        sayi = hatirlatma.hatirlatmalari_isle(ayar, durum, simdi, gonder)
        print(f"{sayi} hatırlatma gönderildi.")
        if hatirlatma.haftalik_ozet_zamani_mi(ayar, durum, simdi):
            gonder(hatirlatma.haftalik_ozet(ayar, durum, simdi))
            hatirlatma.ozet_gonderildi(durum, simdi)
            print("Haftalık özet gönderildi.")
    elif arg.islem == "ozet":
        gonder(hatirlatma.haftalik_ozet(ayar, durum, simdi))

    if arg.kuru:
        print("\n(--kuru: durum kaydedilmedi)")
    else:
        depo.durumu_kaydet(durum)
    return 0


if __name__ == "__main__":
    sys.exit(main())
