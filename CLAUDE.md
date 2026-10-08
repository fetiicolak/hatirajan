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
- ✅ cron-job.org dış zamanlayıcı canlıda doğrulandı (2026-10-07). Gece boyunca her xx:05/xx:35 çalıştırması dakikasında geldi; sabah taraması 08:05'te yapıldı. Gecikme sorunu çözüldü, GitHub cron'u yedek olarak kalıyor.
- ✅🔲 BELTEK görevi eklendi (2026-10-07). Canlı kuru denemede takvim doğru okundu; ilk gerçek taramada tek "Kayıt takvimi" mesajı bekleniyor.
- ✅🔲 TEKNOFEST görevi eklendi (2026-10-08). Canlı kuru denemede 13 duyuru okundu, ilk tarama sessiz geçti.
  - Aynı değişiklikle tarih ayıklayıcı düzeltildi: tek başvuru tarihinde tarihe en yakın "başla" ya da "son başvuru/kadar" ipucu karar veriyor.
  - Yayım tarihi kutusu artık metinden çıkarılıyor; sayısal biçim (`gg.aa.yyyy`) de okunuyor.
**Son güncelleme:** 2026-10-08

## Gereksinimler (kullanıcının istekleri)
✅ = kodlandı ve test edildi · ✅✅ = canlıda doğrulandı · ✅🔲 = canlı doğrulama bekliyor
- ✅✅ R1 — Belirlenen sayfalar her gün otomatik kontrol edilsin (08:00 / 17:00 TR; saatte 2 kez çalışan `otomatik` atlanan taramayı telafi eder; cron-job.org ile tarama 08:05/17:05'te).
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
- ✅ R21 — BELTEK kurs kayıt tarihleri takibi (görev `beltek`, 2026-10-07): kayıt takvimi tablosu okunur, yeni/değişen dönemler tek mesajda bildirilir, kayıt başlangıcından 1 gün önce 20:00 ve o gün 08:30 hatırlatılır (kontenjan sırayla dolduğu için).
- ✅ R22 — TEKNOFEST üniversite öğrencisi yarışmaları başvuru takibi (görev `teknofest`, 2026-10-08): duyurularda "başvuru" / "üniversite öğrencileri" geçenler bildirilir. Hatırlatmalar: başlangıç günü 09:00, son başvurudan 7, 3 ve 1 gün önce 09:00.
- ✅ R20 — Her taramadan sonra (08:00 / 17:00) kısa rapor, yeni bilgi yoksa da gelir ("yeni bilgi yok"); panelden kapatılabilir (`ayarlar.tarama_raporu.aktif`, 2026-09-29).

## Alınan kararlar
| Konu | Karar |
|---|---|
| Dil / ortam | Python 3.12 (Actions) / 3.13 (yerel `.venv`); bağımlılıklar yalnızca `requests`, `beautifulsoup4` |
| Bildirim | Telegram Bot API; env `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Zamanlama | `.github/workflows/hatirajan.yml`: `7,37 * * * *` → `otomatik` (08:00/17:00 TR geçmiş ve `son_kontrol` o saatten eskiyse önce kontrol; her seferinde hatırlat + haftalık özet). Sebep: GitHub zamanlanmış çalıştırmaları sık atlıyor (30 Eylül 05:00 UTC kontrolü hiç başlamadı); `workflow_dispatch` (kontrol/otomatik/hatirlat/ozet/test-telegram; `otomatik` cron-job.org için) |
| Yapay zeka | **Yok.** İleride gerekirse ücretsiz Gemini (`gemini-2.5-flash`), Groq yedek (KPSS-Uygulamasi `supabase/functions/ai-proxy/index.ts` ile aynı ikili) |
| Telegram | Yeni, ayrı bot (otel botundan bağımsız) |
| Panel | GitHub Pages `docs/`; okuma anahtarsız, yazma fine-grained token ile (yalnızca kullanıcının tarayıcısında, localStorage) |
| Repo | `hatirajan`, **public** (Pages ücretsiz olsun diye); gizli bilgiler yalnızca Secrets'ta |
| Görev tanımı | `config/gorevler.json` (panel yazar) |
| Durum | `data/durum.json` (Actions yazar ve commit eder; panel okur) |
| Saat dilimi | Sabit UTC+3 (`hatirajan/zaman.py`), tzdata bağımlılığı yok |
| Tarama raporu | `ayarlar.tarama_raporu.aktif` (config'te açık; anahtar yoksa kapalı). Görev başına yeni duyuru sayısı + okunamayan kaynak sayısı |
| Takvim kaynağı | `{"url": …, "tur": "takvim"}`: sayfadaki tablo satırlarından ilk iki tarih kayıt başlangıcı/bitişi sayılır (`cekici.takvim_satirlari`). Dönem başına tarihler `gorevler.<id>.takvim`'de saklanır; değişirse eski tarih `gecersiz`. Duyuru yolundaki "60 gün içinde uzatma" kuralı burada uygulanmaz, çünkü ardışık dönemleri yanlışlıkla geçersiz sayardı. İlk taramada da gelecek dönemler bildirilir |
| İlk tarama | Kaynağın ilk taramasında eski duyurular sessizce "görüldü" sayılır; yalnızca gelecek tarihli ilgili duyuru bildirilir |
| Kurulum sırası | 1) Claude kodu yazdı + yerel test ✅ 2) Kullanıcı: bot, repo, Secrets, Pages, panel anahtarı 3) Birlikte uçtan uca test |

## Kod haritası
```
hatirajan/__main__.py    # CLI: otomatik | kontrol | hatirlat | ozet | test-telegram | chat-id  [--kuru] [--simdi ISO]
hatirajan/kontrol.py     # kaynak tarama, yeni ilgili duyuru → detay → tarih → mesaj; kaynak hata uyarısı (3. denemede bir kez); tarama raporu
hatirajan/cekici.py      # nazik HTTP (Oturum), Gazi liste sayfalaması (2 sayfa), detay (Gazi .subpage-content-txt / TEKNOFEST .borderCardMob), kayıt takvimi tablosu, CAPTCHA tespiti, Playwright yedeği
hatirajan/tarihler.py    # Türkçe tarih regex'leri + en yakın anahtar kelimeyle tür sınıflama + makul aralık süzgeci
hatirajan/metin.py       # Türkçe küçük harf/sadeleştirme, anahtar kelime ("a & b") eşleşmesi, başlıktan kategori
hatirajan/hatirlatma.py  # kural planlama, vadesi gelen hatırlatma (36 saat tolerans, olay başına tek mesaj), haftalık özet
hatirajan/bildirim.py    # Telegram (otel-fiyat-takip/src/bildirim.py'den uyarlandı)
hatirajan/depo.py        # config/gorevler.json ve data/durum.json okuma/yazma
docs/                    # panel: index.html, app.js (planla() Python ile aynı mantık), style.css
tests/test_hatirajan.py  # 27 test; tests/ornekler/ gerçek Gazi duyuru metinleri, beltek_takvim.html + panel_durum.json (panel önizleme)
.claude/launch.json      # "panel" önizleme sunucusu (http://localhost:8765/docs/?yerel=ornek)
```

## Referans proje: otel-fiyat-takip
Yol: `C:\Projeler\Fiyat Takip Uygulaması` · GitHub: `fetiicolak/otel-fiyat-takip`. Yapay zeka kullanmıyor; Python + Playwright + regex + Telegram + Actions + Pages. `bildirim.py`, workflow commit adımı, "hata yalnızca ilk oluştuğunda bildir" deseni ve Playwright ayarları buradan alındı. Kod stili: Türkçe adlar.

## Kaynaklar (araştırıldı ve canlı doğrulandı, 2026-09-23)
Gazi'nin tüm birim siteleri aynı CMS: liste `…/view/announcement-list/1?Type=1` (sayfa başına 6 duyuru; sayfa N: `?id=N&type=1`), arama `?id=1&type=1&SearchString=<kelime>`, detay `/view/announcement/<id>`. Statik HTML, ETag/Last-Modified yok.
- **İŞKUR Gençlik Programı**: mediko, odm, gazi.edu.tr ana liste + `mediko…SearchString=işkur`. Anahtar: `iskur`, `gençlik programı`. Gazi, başvuru/kura/sonuç duyurularını SKS (mediko) sitesinde yayımlıyor. `genclik.iskur.gov.tr` yerelden çözümlenmedi, kaynak değil.
- **Erasmus dil sınavı**: ydyo, erasmus + `ydyo…SearchString=erasmus`. Anahtar: `yabancı dil yeterlik & değişim`, `yabancı dil yeterlik & erasmus`, `erasmus & dil sınav`. Sınav yılda 2 kez (Mart, Kasım); başvuru formu linki duyurunun içinde (drive.gazi.edu.tr).
- **BELTEK** (Gazi Mesleki Teknik Eğitim Kursları, ücretsiz; 2026-10-07 incelendi): ayrı site `beltek.gazi.edu.tr`, farklı CMS.
  - Yıllık takvim `…/Content/Index/Kurs-Takvimi` sayfasında tablo olarak yayımlanıyor.
  - 2 aylık dönemler: 127 (kayıt 9–17 Kas 2026), 128 (11–19 Oca 2027), 129 (15–23 Mar 2027), 130 (3–11 May 2027).
  - 3 aylık dönemler: 80 (14–22 Ara 2026), 81 (22–30 Mar 2027).
  - Kayıt: siteden "Kursiyer Ön Bilgi Girişi" (`/PreRegistration/Home`) + kayıt bürosunda kesin kayıt (kimlik + öğrenim belgesi). Önce gelen alınır.
  - Duyurular ana sayfada (`/Announcement/Content/<guid>`).
- **TEKNOFEST** (2026-10-08 incelendi):
  - Duyuru listesi `teknofest.org/tr/content/announcements/`, detaylar `/tr/duyurular/<slug>/`. Metin `.borderCardMob` içinde, yayım tarihi `.dateText` içinde (`03.10.2026`).
  - Yarışma takvimi yalnızca görsel olarak yayımlanıyor (okunamıyor). Yarışmalar sayfasında 2026 başvurularının hepsi "Başvuru Tamamlandı" durumunda.
  - 2026 dönemi: başvurular Ocak 2026'da açıldı (TÜBİTAK haberi 23 Oca), son başvuru 20 Şubat 2026. 2027 başvurularının da benzer şekilde Aralık–Ocak'ta açılması bekleniyor.
- Geçmiş duyurularla benzetim: sınav tarih+saat, İŞKUR başvuru aralığı, salon/sonuç duyuruları doğru ayıklandı.

## Site korumalarına karşı ilkeler
- İstekler arası 3–8 sn rastgele bekleme, paralel istek yok, gerçekçi Chrome başlıkları, oturum çerezleri.
- 429/503 → `Retry-After` (en çok 120 sn), 3 deneme; 403 veya küçük CAPTCHA sayfası → `EngelHatasi` → Telegram'a "elle kontrol et".
- Kaynak `{"url": …, "tarayici": true}` yazılırsa Playwright kullanılır (workflow bunu görünce Playwright kurar).
- **Yapılmayacak:** CAPTCHA çözme, bot-tespiti atlatma.
- Koşullu istek (ETag) planlanmıştı; Gazi sunucusu bu başlıkları göndermediği için uygulanmadı.

## Bilinen sınırlar / ileride
- GitHub cron çalıştırmaların çoğunu atlıyor (günde 4–6). Yalnız kalırsa tarama ve hatırlatmalar 1–6 saat gecikir. Haftalık özet de Pazar 20:00–24:00 arasında hiç çalıştırma olmazsa atlanır.
- Çözüm: cron-job.org saatte 2 kez (xx:05/xx:35) `workflow_dispatch` ile `islem=otomatik` tetikliyor. Kurulum 2026-10-07'de yapıldı ve canlıda doğrulandı. Token yalnızca `hatirajan` reposu ve Actions yetkili, kullanıcı tarafından girildi. cron-job.org durursa sistem GitHub cron'una, yani gecikmeli çalışmaya geri döner. Header: `Authorization: Bearer …`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`. Bu sürüm GitHub'da kullanımdan kalkıyor, sunset 2028-03-10. **Token 2027-10-05'te sona eriyor; yenilenmeli.**
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
