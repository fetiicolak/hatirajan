"""Sitelere nazik davranan sayfa çekici: duyuru listesi ve duyuru detayı.

İlkeler (bkz. CLAUDE.md "Site korumalarına karşı ilkeler"):
- İstekler arası rastgele bekleme, paralel istek yok, gerçekçi tarayıcı başlıkları.
- 429/503'te Retry-After'a uyulur; engel/CAPTCHA sayfası görülürse aşılmaya
  çalışılmaz, EngelHatasi fırlatılır ve kullanıcıya "elle kontrol et" bildirimi gider.
- Playwright kuruluysa (kaynakta "tarayici": true) sayfa gerçek tarayıcıyla açılır.
"""

import random
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .tarihler import yayim_tarihi

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
BASLIKLAR = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.6",
}
ENGEL_IZLERI = ("captcha", "cf-challenge", "just a moment", "access denied", "erişim engellendi")
ICERIK_SECICILERI = (".subpage-content-txt", "article", "main", "#content", ".content")


class CekmeHatasi(Exception):
    pass


class EngelHatasi(CekmeHatasi):
    """Site bot koruması / CAPTCHA gösterdi — elle kontrol gerekir."""


@dataclass
class Duyuru:
    url: str
    baslik: str


@dataclass
class DuyuruDetayi:
    baslik: str
    metin: str
    yayim: str | None  # ISO tarih
    ekler: list[str]


def _kaynak(kaynak) -> dict:
    """Kaynak düz URL ya da {"url", "link_deseni", "sayfa_sayisi", "tarayici"} olabilir."""
    k = {"url": kaynak} if isinstance(kaynak, str) else dict(kaynak)
    gazi = urlparse(k["url"]).netloc.endswith("gazi.edu.tr")
    k.setdefault("link_deseni", "/view/announcement/" if gazi else "")
    k.setdefault("sayfa_sayisi", 2 if gazi else 1)
    k.setdefault("tarayici", False)
    return k


def _sayfa_url(url: str, sayfa: int) -> str:
    """Gazi CMS liste sayfalaması: /view/announcement-list?id=<sayfa>&type=1"""
    if sayfa == 1:
        return url
    p = urlparse(url)
    sorgu = {k: v[0] for k, v in parse_qs(p.query).items() if k.lower() != "id"}
    if not any(k.lower() == "type" for k in sorgu):
        sorgu["type"] = "1"
    sorgu = {"id": str(sayfa), **sorgu}
    return f"{p.scheme}://{p.netloc}/view/announcement-list?{urlencode(sorgu)}"


class Oturum:
    def __init__(self, bekleme=(3.0, 8.0)):
        self.http = requests.Session()
        self.http.headers.update(BASLIKLAR)
        self.bekleme = bekleme
        self._son_istek: dict[str, float] = {}
        self._onbellek: dict[str, list[Duyuru]] = {}

    def _bekle(self, alan: str) -> None:
        onceki = self._son_istek.get(alan)
        if onceki is not None:
            gerekli = random.uniform(*self.bekleme) - (time.monotonic() - onceki)
            if gerekli > 0:
                time.sleep(gerekli)
        self._son_istek[alan] = time.monotonic()

    def html_al(self, url: str, tarayici: bool = False) -> str:
        alan = urlparse(url).netloc
        if tarayici:
            self._bekle(alan)
            return _tarayici_ile_al(url)
        for deneme in range(3):
            self._bekle(alan)
            try:
                yanit = self.http.get(url, timeout=30, headers={"Referer": f"https://{alan}/"})
            except requests.RequestException as e:
                if deneme == 2:
                    raise CekmeHatasi(f"bağlantı hatası: {type(e).__name__}") from e
                time.sleep(10 * (deneme + 1))
                continue
            if yanit.status_code in (429, 503):
                bekle = min(int(yanit.headers.get("Retry-After", "30") or 30), 120)
                time.sleep(bekle)
                continue
            if yanit.status_code == 403:
                raise EngelHatasi("site erişimi reddetti (403)")
            if yanit.status_code >= 400:
                raise CekmeHatasi(f"HTTP {yanit.status_code}")
            if not yanit.encoding or yanit.encoding.lower() == "iso-8859-1":
                yanit.encoding = yanit.apparent_encoding
            html = yanit.text
            if engel_sayfasi_mi(html):
                raise EngelHatasi("site bot doğrulaması (CAPTCHA) istiyor")
            return html
        raise CekmeHatasi("site çok fazla istek uyarısı verdi (429/503)")

    def duyurulari_listele(self, kaynak) -> list[Duyuru]:
        k = _kaynak(kaynak)
        if k["url"] in self._onbellek:
            return self._onbellek[k["url"]]
        duyurular: dict[str, Duyuru] = {}
        for sayfa in range(1, k["sayfa_sayisi"] + 1):
            url = _sayfa_url(k["url"], sayfa)
            corba = BeautifulSoup(self.html_al(url, k["tarayici"]), "html.parser")
            for a in corba.find_all("a", href=True):
                href = urljoin(url, a["href"])
                if k["link_deseni"] and k["link_deseni"] not in href:
                    continue
                baslik = a.get_text(" ", strip=True)
                if len(baslik) < 8 or href.startswith(("mailto:", "javascript:")):
                    continue
                duyurular.setdefault(duyuru_kimligi(href), Duyuru(href, baslik))
        if not duyurular:
            raise CekmeHatasi("sayfada duyuru bulunamadı (site tasarımı değişmiş olabilir)")
        sonuc = list(duyurular.values())
        self._onbellek[k["url"]] = sonuc
        return sonuc

    def duyuru_detayi(self, duyuru: Duyuru, tarayici: bool = False) -> DuyuruDetayi:
        corba = BeautifulSoup(self.html_al(duyuru.url, tarayici), "html.parser")
        icerik = next((corba.select_one(s) for s in ICERIK_SECICILERI if corba.select_one(s)), corba.body)
        tarih_kutusu = corba.select_one(".subpage-date-div")
        yayim = yayim_tarihi(tarih_kutusu.get_text(" ", strip=True)[:40]) if tarih_kutusu else None
        ekler = [urljoin(duyuru.url, a["href"]) for a in icerik.find_all("a", href=True)
                 if not a["href"].startswith("mailto:")] if icerik else []
        return DuyuruDetayi(
            baslik=duyuru.baslik,
            metin=icerik.get_text(" ", strip=True) if icerik else "",
            yayim=yayim.isoformat() if yayim else None,
            ekler=list(dict.fromkeys(ekler)),
        )


def duyuru_kimligi(url: str) -> str:
    """Aynı duyurunun farklı sorgu parametreli linklerini birleştirir (Gazi: /view/announcement/<id>)."""
    p = urlparse(url)
    return f"{p.netloc}{p.path}" if "/view/announcement/" in p.path else url


def engel_sayfasi_mi(html: str) -> bool:
    """Bot doğrulama sayfaları küçük olur; normal sayfalardaki reCAPTCHA betiği yanlış alarm vermesin."""
    return len(html) < 30_000 and any(iz in html[:5000].lower() for iz in ENGEL_IZLERI)


def _tarayici_ile_al(url: str) -> str:
    """JS gerektiren siteler için headless Chromium (otel-fiyat-takip/src/siteler/ortak.py deseni)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise CekmeHatasi("bu kaynak tarayıcı gerektiriyor ama Playwright kurulu değil") from e
    with sync_playwright() as p:
        tarayici = p.chromium.launch(headless=True)
        baglam = tarayici.new_context(user_agent=UA, locale="tr-TR", timezone_id="Europe/Istanbul",
                                      viewport={"width": 1366, "height": 768})
        sayfa = baglam.new_page()
        sayfa.goto(url, wait_until="domcontentloaded", timeout=60_000)
        sayfa.wait_for_timeout(5000)
        html = sayfa.content()
        tarayici.close()
    if engel_sayfasi_mi(html):
        raise EngelHatasi("site bot doğrulaması (CAPTCHA) istiyor")
    return html
