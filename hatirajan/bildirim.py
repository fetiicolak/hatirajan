"""Telegram Bot API ile bildirim gönderimi (otel-fiyat-takip/src/bildirim.py'den uyarlandı).

Gerekli ortam değişkenleri (yerelde .env dosyasından da okunur):
  TELEGRAM_BOT_TOKEN : BotFather'dan alınan token
  TELEGRAM_CHAT_ID   : mesajların gideceği chat ID (birden fazlaysa virgülle ayrık)
"""

import os
import time
from pathlib import Path

import requests

API = "https://api.telegram.org/bot{token}/sendMessage"


def _env_yukle() -> None:
    """Yerel geliştirme için basit .env okuyucu."""
    env = Path(__file__).resolve().parent.parent / ".env"
    if not env.exists():
        return
    for satir in env.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if satir and not satir.startswith("#") and "=" in satir:
            anahtar, _, deger = satir.partition("=")
            os.environ.setdefault(anahtar.strip(), deger.strip())


def gonder(mesaj: str) -> None:
    """Mesajı tanımlı tüm chat ID'lere gönderir."""
    _env_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_ids = [c.strip() for c in os.environ.get("TELEGRAM_CHAT_ID", "").split(",") if c.strip()]
    if not token or not chat_ids:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID tanımlı değil")

    for chat_id in chat_ids:
        for deneme in range(3):
            yanit = requests.post(
                API.format(token=token),
                json={"chat_id": chat_id, "text": mesaj[:4000], "parse_mode": "HTML",
                      "disable_web_page_preview": True},
                timeout=30,
            )
            if yanit.status_code == 429 and deneme < 2:  # Telegram hız sınırı
                time.sleep(yanit.json().get("parameters", {}).get("retry_after", 5))
                continue
            if not yanit.ok:
                raise RuntimeError(f"Telegram hatası ({yanit.status_code}): {yanit.text[:200]}")
            break


def sohbetleri_bul() -> list[tuple[int, str]]:
    """Bota mesaj yazan sohbetlerin (chat ID, ad) listesi — kurulumda chat ID'yi bulmak için.

    Token ekrana yazılmaz; yalnızca .env / ortam değişkeninden okunur.
    """
    _env_yukle()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN tanımlı değil (.env dosyasına yaz)")
    yanit = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
    if not yanit.ok:
        raise RuntimeError(f"Telegram hatası ({yanit.status_code}) — token doğru mu?")
    sohbetler = {}
    for guncelleme in yanit.json().get("result", []):
        sohbet = (guncelleme.get("message") or guncelleme.get("my_chat_member") or {}).get("chat")
        if sohbet:
            ad = " ".join(filter(None, [sohbet.get("first_name"), sohbet.get("last_name")])) or sohbet.get("title", "")
            sohbetler[sohbet["id"]] = ad
    return list(sohbetler.items())


def konsola_yaz(mesaj: str) -> None:
    """--kuru modunda Telegram yerine konsola yazar."""
    print("─" * 60)
    print(mesaj)
