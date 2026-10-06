# HatırAjan

Belirli web sayfalarını her gün otomatik kontrol eden, beklenen bir duyuru/başvuru tarihi yayımlandığında kullanıcıya Telegram'dan haber veren kişisel takip ajanı.

> Bu dosya projenin tek doğruluk kaynağıdır. Her karar, değişiklik ve tamamlanan maddeden sonra güncellenir.

## Durum
**Aşama:** ✅ Kurulum tamamlandı, sistem canlıda (2026-09-29).
- ✅ Adım 1 — Telegram botu açıldı (2026-09-29).
- ✅ Adım 2 — Yerel `.env` dolduruldu (token + chat ID), `python -m hatirajan test-telegram` başarıyla gönderdi.
- ✅ Adım 3 — Repo oluşturuldu ve gönderildi: https://github.com/fetiicolak/hatirajan (public, `main`).
- ✅ Adım 4 — Secrets kullanıcı tarafından `gh secret set -f .env` ile girildi; Pages açıldı: https://fetiicolak.github.io/hatirajan/
- ✅ Actions'ta `test-telegram` Telegram'a ulaştı; "Durumu kaydet" adımı `data/` yokken düşüyordu → workflow düzeltildi (`[ -d data ] || exit 0`).
- ✅ Adım 5 — Panel fine-grained token girildi; panelden kaydetme repoya commit düştü; Actions'ta ilk `kontrol` 7 kaynağın hepsini okudu.
- ✅ Uçtan uca test — panelden eklenen özel hatırlatma (18:00) elle tetiklenen `hatirlat` ile Telegram'a ulaştı.
- ✅ `otomatik` telafi modu canlıda doğrulandı (30 Eyl – 6 Eki): her gün iki tarama raporu geldi, 4 Ekim haftalık özeti geldi. Hiçbir tarama atlanmadı.
- ⚠️ GitHub günde 48 zamanlanmış çalıştırmanın yalnızca 4–6'sını başlatıyor. Bu yüzden raporlar 08:00/17:00 yerine 1–6 saat gecikmeli geliyor (ör. 6 Eki 13:45, 30 Eyl 21:25).
**Son güncelleme:** 2026-10-06

## Gereksinimler (kullanıcının istekleri)
✅ = kodlandı ve test edildi · ✅✅ = canlıda doğrulandı · ✅🔲 = canlı doğrulama bekliyor
- ✅✅ R1 — Belirlenen sayfalar her gün otomatik kontrol edilsin (08:00 / 17:00 TR; saatte 2 kez çalışan `otomatik` atlanan taramayı telafi eder; GitHub yüzünden 1–6 saat gecikme olabiliyor).
- ✅🔲 R2 — Beklenen tarih/duyuru yayımlandığında bildirim gönderilsin.
- ✅ R3 — İŞKUR Gençlik Programı takibi (görev `iskur-genclik`).
- ✅ R4 — Gazi Erasmus Yabancı Dil Yeterlik Sınavı takibi (görev `gazi-erasmus-dil`).
- ✅ R5 — Yeni görevler kod yazmadan eklenebilsin (`config/gorevler.json` + panel).
- ✅✅ R6 — Bildirim kanalı Telegram (yeni ayrı bot).
- ✅✅ R7 — GitHub Actions'ta çalışsın.
- ✅ R8 — Tamamen ücretsiz; yapay zeka API'si yok, kural tabanlı ayıklama.
- ✅ R9 — Sitelere nazik istemci (bekleme, gerçekçi başlıklar, Retry-After, CAPTCHA aşılmaz → uyarı).
- ✅ R10 — Güncel CLAUDE.md.
- ✅ R11 — Kurulum öncesi tüm noktalar konuşuldu; kurulum kullanıcının "kuruluma başlayalım" demesiyle başladı.
- ✅ R12 — Son başvurudan 3 gün ve 1 gün önce hatırlatma.
- ✅✅ R13 — Kontrol paneli (GitHub Pages): görev ekle/sil, hatırlatma kuralları, özel hatırlatmalar, bulunan tarihler, "Şimdi kontrol et".
- ✅ R14 — Görev ekleme Telegram'dan değil (Telegram yalnızca bildirim).
- ✅ R15 — Haftalık özet (Pazar 20:00, panelden değiştirilebilir).
- ✅ R16 — Başvuru, sınav, sınav yeri/salon, sonuç/kura duyurularının hepsi bildirilir (kategori simgeleriyle).
- ✅ R17 — Görev başına hatırlatma sayısı panelden serbestçe artırılıp azaltılır (her satır = bir mesaj).
- ✅ R18 — Hiçbir maddi yük yok (otel-fiyat-takip ile aynı yaklaşım).
- ✅ R19 — Varsayılan kurallar: başvuru başlangıcı olay günü 09:00, son başvuru 3 ve 1 gün önce 09:00, sınav 1 gün önce 20:00.
- ✅ R20 — Her taramadan sonra (08:00 / 17:00) kısa rapor, yeni bilgi yoksa da gelir ("yeni bilgi yok"); panelden kapatılabilir (`ayarlar.tarama_raporu.aktif`, 2026-09-29).

## Alınan kararlar
| Konu | Karar |
|---|---|
| Dil / ortam | Python 3.12 (Actions) / 3.13 (yerel `.venv`); bağımlılıklar yalnızca `requests`, `beautifulsoup4` |
| Bildirim | Telegram Bot API; env `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Zamanlama | `.github/workflows/hatirajan.yml`: `7,37 * * * *` → `otomatik` (08:00/17:00 TR geçmiş ve `son_kontrol` o saatten eskiyse önce kontrol; her seferinde hatırlat + haftalık özet). Sebep: GitHub zamanlanmış çalıştırmaları sık atlıyor (30 Eylül 05:00 UTC kontrolü hiç başlamadı); `workflow_dispatch` (kontrol/hatirlat/ozet/test-telegram) |
| Yapay zeka | **Yok.** İleride gerekirse ücretsiz Gemini (`gemini-2.5-flash`), Groq yedek (KPSS-Uygulamasi `supabase/functions/ai-proxy/index.ts` ile aynı ikili) |
| Telegram | Yeni, ayrı bot (otel botundan bağımsız) |
| Panel | GitHub Pages `docs/`; okuma anahtarsız, yazma fine-grained token ile (yalnızca kullanıcının tarayıcısında, localStorage) |
| Repo | `hatirajan`, **public** (Pages ücretsiz olsun diye); gizli bilgiler yalnızca Secrets'ta |
| Görev tanımı | `config/gorevler.json` (panel yazar) |
| Durum | `data/durum.json` (Actions yazar ve commit eder; panel okur) |
| Saat dilimi | Sabit UTC+3 (`hatirajan/zaman.py`), tzdata bağımlılığı yok |
| Tarama raporu | `ayarlar.tarama_raporu.aktif` (config'te açık; anahtar yoksa kapalı). Görev başına yeni duyuru sayısı + okunamayan kaynak sayısı |
| İlk tarama | Kaynağın ilk taramasında eski duyurular sessizce "görüldü" sayılır; yalnızca gelecek tarihli ilgili duyuru bildirilir |
| Kurulum sırası | 1) Claude kodu yazdı + yerel test ✅ 2) Kullanıcı: bot, repo, Secrets, Pages, panel anahtarı 3) Birlikte uçtan uca test |

## Kod haritası
```
hatirajan/__main__.py    # CLI: otomatik | kontrol | hatirlat | ozet | test-telegram | chat-id  [--kuru] [--simdi ISO]
hatirajan/kontrol.py     # kaynak tarama, yeni ilgili duyuru → detay → tarih → mesaj; kaynak hata uyarısı (3. denemede bir kez); tarama raporu
hatirajan/cekici.py      # nazik HTTP (Oturum), Gazi liste sayfalaması (2 sayfa), detay (.subpage-content-txt), CAPTCHA tespiti, Playwright yedeği
hatirajan/tarihler.py    # Türkçe tarih regex'leri + en yakın anahtar kelimeyle tür sınıflama + makul aralık süzgeci
hatirajan/metin.py       # Türkçe küçük harf/sadeleştirme, anahtar kelime ("a & b") eşleşmesi, başlıktan kategori
hatirajan/hatirlatma.py  # kural planlama, vadesi gelen hatırlatma (36 saat tolerans, olay başına tek mesaj), haftalık özet
hatirajan/bildirim.py    # Telegram (otel-fiyat-takip/src/bildirim.py'den uyarlandı)
hatirajan/depo.py        # config/gorevler.json ve data/durum.json okuma/yazma
docs/                    # panel: index.html, app.js (planla() Python ile aynı mantık), style.css
tests/test_hatirajan.py  # 23 test; tests/ornekler/ gerçek Gazi duyuru metinleri + panel_durum.json (panel önizleme)
.claude/launch.json      # "panel" önizleme sunucusu (http://localhost:8765/docs/?yerel=ornek)
```

## Referans proje: otel-fiyat-takip
Yol: `C:\Projeler\Fiyat Takip Uygulaması` · GitHub: `fetiicolak/otel-fiyat-takip`. Yapay zeka kullanmıyor; Python + Playwright + regex + Telegram + Actions + Pages. `bildirim.py`, workflow commit adımı, "hata yalnızca ilk oluştuğunda bildir" deseni ve Playwright ayarları buradan alındı. Kod stili: Türkçe adlar.

## Kaynaklar (araştırıldı ve canlı doğrulandı, 2026-09-23)
Gazi'nin tüm birim siteleri aynı CMS: liste `…/view/announcement-list/1?Type=1` (sayfa başına 6 duyuru; sayfa N: `?id=N&type=1`), arama `?id=1&type=1&SearchString=<kelime>`, detay `/view/announcement/<id>`. Statik HTML, ETag/Last-Modified yok.
- **İŞKUR Gençlik Programı**: mediko, odm, gazi.edu.tr ana liste + `mediko…SearchString=işkur`. Anahtar: `iskur`, `gençlik programı`. Gazi, başvuru/kura/sonuç duyurularını SKS (mediko) sitesinde yayımlıyor. `genclik.iskur.gov.tr` yerelden çözümlenmedi, kaynak değil.
- **Erasmus dil sınavı**: ydyo, erasmus + `ydyo…SearchString=erasmus`. Anahtar: `yabancı dil yeterlik & değişim`, `yabancı dil yeterlik & erasmus`, `erasmus & dil sınav`. Sınav yılda 2 kez (Mart, Kasım); başvuru formu linki duyurunun içinde (drive.gazi.edu.tr).
- Geçmiş duyurularla benzetim: sınav tarih+saat, İŞKUR başvuru aralığı, salon/sonuç duyuruları doğru ayıklandı.

## Site korumalarına karşı ilkeler
- İstekler arası 3–8 sn rastgele bekleme, paralel istek yok, gerçekçi Chrome başlıkları, oturum çerezleri.
- 429/503 → `Retry-After` (en çok 120 sn), 3 deneme; 403 veya küçük CAPTCHA sayfası → `EngelHatasi` → Telegram'a "elle kontrol et".
- Kaynak `{"url": …, "tarayici": true}` yazılırsa Playwright kullanılır (workflow bunu görünce Playwright kurar).
- **Yapılmayacak:** CAPTCHA çözme, bot-tespiti atlatma.
- Koşullu istek (ETag) planlanmıştı; Gazi sunucusu bu başlıkları göndermediği için uygulanmadı.

## Bilinen sınırlar / ileride
- GitHub cron çalıştırmaların çoğunu atlıyor (günde 4–6 çalıştırma). Tarama 08:00/17:00'den sonraki ilk gerçekleşen çalıştırmada yapılıyor ve bu genelde 1–6 saat sonra. Hatırlatmalar da aynı gecikmeyle geliyor.
- Haftalık özet ancak Pazar 20:00–24:00 arasında bir çalıştırma olursa gider; bu aralıkta hiç çalıştırma olmazsa o haftanın özeti atlanır.
- Kesin saat istenirse ücretsiz bir dış zamanlayıcı (ör. cron-job.org) 08:00 ve 17:00'de `workflow_dispatch` tetikleyebilir. Bunun için yalnızca Actions yetkili bir token o servise girilmeli; henüz uygulanmadı.
- Duyuru içindeki PDF'ler okunmaz (link olarak mesaja eklenir).
- Türü belirlenemeyen tarihler "diger" olarak saklanır, hatırlatma kurulmaz.
- Başvuru süresi uzatılırsa (60 gün içinde daha geç bir son başvuru tarihi) eski tarih `gecersiz` olur.

## Çalışma kuralları (Claude için)
- Her karar/değişiklikten sonra bu dosyadaki Durum, Gereksinimler ve Kararlar bölümlerini güncelle.
- Kullanıcıyla Türkçe konuş.
- Ücretli servis önerme; her şey ücretsiz katmanlarda kalmalı (Claude API kullanılmaz).
- API anahtarı / token gibi gizli bilgileri asla koda veya repoya yazma; GitHub Secrets ve yerel `.env` (gitignore'da) kullan. Token'ları kullanıcı kendisi girer.
- Commit/push ve repo oluşturma gibi dışa dönük işlemler için kullanıcıdan onay al.
- Değişiklikten sonra `python -m unittest` çalıştır.
