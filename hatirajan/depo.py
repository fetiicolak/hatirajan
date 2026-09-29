"""Görev yapılandırması (config/gorevler.json) ve çalışma durumu (data/durum.json) okuma/yazma.

config/gorevler.json : kullanıcının panelden düzenlediği görevler ve ayarlar
data/durum.json      : sistemin yazdığı her şey (görülen duyurular, bulunan tarihler,
                       gönderilen hatırlatmalar, kaynak hataları, son çalışma zamanları)
"""

import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
GOREVLER = KOK / "config" / "gorevler.json"
DURUM = KOK / "data" / "durum.json"


def gorevleri_yukle() -> dict:
    ayar = json.loads(GOREVLER.read_text(encoding="utf-8"))
    ayar.setdefault("ayarlar", {})
    ayar.setdefault("gorevler", [])
    return ayar


def durumu_yukle() -> dict:
    durum = json.loads(DURUM.read_text(encoding="utf-8")) if DURUM.exists() else {}
    durum.setdefault("gorevler", {})
    durum.setdefault("kaynaklar", {})
    durum.setdefault("gonderilen_hatirlatmalar", {})
    return durum


def gorev_durumu(durum: dict, gorev_id: str) -> dict:
    gd = durum["gorevler"].setdefault(gorev_id, {})
    gd.setdefault("gorulen", {})        # duyuru kimliği -> ilk görüldüğü gün
    gd.setdefault("taranan_kaynaklar", [])  # ilk (sessiz) taraması yapılmış kaynaklar
    gd.setdefault("duyurular", [])      # bildirilen ilgili duyurular (yeniden eskiye)
    gd.setdefault("olaylar", [])        # bulunan tarihler
    return gd


def durumu_kaydet(durum: dict) -> None:
    DURUM.parent.mkdir(parents=True, exist_ok=True)
    DURUM.write_text(json.dumps(durum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
