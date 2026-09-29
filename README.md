# HatırAjan

Gazi Üniversitesi duyuru sayfalarını her gün kontrol eder. Takip ettiğin konuda (İŞKUR Gençlik Programı, Erasmus dil sınavı…) yeni bir duyuru çıktığında tarihleri ayıklayıp **Telegram'dan** haber verir ve son başvuru / sınav öncesi **hatırlatma** gönderir. Görevleri ve hatırlatmaları **web panelinden** yönetirsin.

Tamamen ücretsizdir: GitHub Actions (zamanlayıcı) + GitHub Pages (panel) + Telegram Bot API. Yapay zeka API'si kullanılmaz.

## Nasıl çalışır

```
GitHub Actions ── 08:00 ve 17:00 ──► python -m hatirajan kontrol
                                       ├─ config/gorevler.json'daki kaynak sayfaları okur
                                       ├─ yeni + anahtar kelimeyle eşleşen duyuruyu açar
                                       ├─ Türkçe tarihleri ayıklar (başvuru, sınav, sonuç)
                                       ├─ Telegram'a bildirir
                                       └─ data/durum.json'a yazar, repoya commit eder
               ── her saat xx:20 ──► python -m hatirajan hatirlat
                                       ├─ zamanı gelen hatırlatmaları gönderir
                                       └─ Pazar 20:00 haftalık özet
GitHub Pages (docs/) ── panel: görev ekle, hatırlatma kuralı ekle/sil, bulunan tarihleri gör
```

## Kurulum (bir kerelik)

### 1. Telegram botu
1. Telegram'da **@BotFather**'ı aç → `/newbot` yaz.
2. Bir ad (ör. `HatırAjan`) ve `bot` ile biten bir kullanıcı adı (ör. `hatirajan_feti_bot`) ver.
3. BotFather'ın verdiği **token**'ı kaydet (`123456:ABC-…` gibi). Kimseyle paylaşma.
4. Yeni botunu aç, **Başlat**'a bas ve herhangi bir mesaj yaz.
5. Tarayıcıda `https://api.telegram.org/bot<TOKEN>/getUpdates` adresini aç, yanıttaki `"chat":{"id": 123456789` sayısını kaydet. Bu senin **chat ID**'in.

### 2. Yerelde deneme (isteğe bağlı)
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env      # sonra .env içine token ve chat ID'yi yaz
.venv\Scripts\python -m hatirajan test-telegram
```
Telefonuna "bağlantı testi başarılı" mesajı gelmeli.

### 3. GitHub reposu ve gizli bilgiler
1. Kodu **herkese açık** `hatirajan` reposuna gönder. Panel ücretsiz GitHub Pages ile çalıştığı için repo açık olmalı; token'lar koda girmez.
2. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TELEGRAM_BOT_TOKEN` = BotFather token'ı
   - `TELEGRAM_CHAT_ID` = chat ID
3. Repo → **Settings → Pages** → *Source: Deploy from a branch* → Branch `main`, klasör `/docs` → Save.
   Panel birkaç dakika içinde `https://<kullanıcı-adın>.github.io/hatirajan/` adresinde yayına girer.

### 4. Panel için erişim anahtarı
Paneli **okumak** için anahtar gerekmez. **Düzenlemek** için bir kez anahtar girersin:
1. https://github.com/settings/personal-access-tokens/new adresine git (*Fine-grained token*).
2. *Repository access*: **Only select repositories** → `hatirajan`.
3. *Permissions → Repository permissions*:
   - **Contents: Read and write** (görevleri kaydetmek için)
   - **Actions: Read and write** ("Şimdi kontrol et" düğmesi için)
4. Oluştur, anahtarı kopyala → paneldeki **Bağlantı** kutusuna yapıştır → *Kaydet ve yükle*.
   Anahtar yalnızca o cihazın tarayıcısında saklanır; süresi dolunca yenisini girersin.

### 5. İlk çalıştırma
Repo → **Actions → HatırAjan → Run workflow**:
1. `test-telegram` ile bir kez çalıştır: Telegram'a test mesajı gelmeli.
2. `kontrol` ile bir kez çalıştır. İlk taramada eski duyurular sessizce "görüldü" sayılır. Yalnızca tarihi henüz geçmemiş ilgili bir duyuru varsa bildirim gelir.

Bundan sonra her şey otomatik.

## Panel kullanımı
- **Yaklaşan**: bütün görevlerdeki gelecek tarihler.
- **Hatırlatma kuralları**: her satır bir mesaj. Örneğin *Son başvuru · 7 gün önce · 10:00* satırını eklersen, o olay için bir hatırlatma daha gelir. **Planlanan hatırlatmalar** listesi, kaydetmeden önce sonucu gösterir.
- **Özel hatırlatmalar**: serbest tarih, saat ve not ile tek seferlik mesaj.
- **Takip ayarları**:
  - *Kaynak sayfalar*: duyuru listesi linkleri. Gazi'nin `…/view/announcement-list/1?Type=1` sayfaları ve `?SearchString=` arama sayfaları doğrudan çalışır.
  - *Anahtar kelimeler*: duyuru başlığında aranır. `erasmus & dil sınav` yazarsan ikisinin birden geçmesi gerekir.
- **Genel ayarlar**: *Her taramadan sonra rapor* açıkken 08:00 ve 17:00'de "yeni bilgi yok" dahil kısa bir rapor gelir; kapatırsan yalnızca yeni duyuru ve hatırlatmalar gelir.
- **Yeni görev**: kaynak ve anahtar kelime ekleyip kaydet; bir sonraki kontrolde devreye girer.

## Komutlar
```bash
python -m hatirajan kontrol --kuru     # Telegram'a göndermeden, durumu kaydetmeden dene
python -m hatirajan hatirlat --kuru --simdi 2026-10-21T09:30
python -m hatirajan ozet --kuru
python -m unittest -v                  # testler (internet gerekmez)
```
Paneli yerelde denemek için proje kökünde `python -m http.server 8765` çalıştırıp `http://localhost:8765/docs/?yerel=ornek` adresini aç.

## Sınırlar
- GitHub'ın zamanlayıcısı yoğun saatlerde birkaç dakika (bazen daha fazla) gecikebilir.
- Tarihler kurallarla ayıklanır. Alışılmadık yazımlarda tarih bulunamazsa yine de "yeni duyuru var" mesajı ve link gelir.
- Bir site bot doğrulaması (CAPTCHA) isterse sistem onu aşmaya çalışmaz, Telegram'dan "elle kontrol et" uyarısı gönderir.
