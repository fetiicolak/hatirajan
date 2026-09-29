"use strict";

// HatırAjan paneli — config/gorevler.json'u GitHub API ile okur/yazar, data/durum.json'u gösterir.

const TUR = {
  basvuru_baslangic: "Başvuru başlangıcı",
  basvuru_bitis: "Son başvuru",
  sinav: "Sınav",
  sonuc: "Sonuç ilanı",
  diger: "Diğer tarih",
};
const KURAL_OLAYLARI = ["basvuru_baslangic", "basvuru_bitis", "sinav", "sonuc"];
const AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
const GUNLER = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];
const WORKFLOW = "hatirajan.yml";

const S = { repo: "", token: "", cfg: null, sha: null, orijinal: "", durum: {}, acik: new Set() };
const $ = (sec) => document.querySelector(sec);

// ---------- yardımcılar ----------
function depola(anahtar, deger) {
  try { deger == null ? localStorage.removeItem(anahtar) : localStorage.setItem(anahtar, deger); } catch (_) {}
}
function oku(anahtar) {
  try { return localStorage.getItem(anahtar) || ""; } catch (_) { return ""; }
}
function kacis(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function b64Coz(s) {
  return new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, "")), (c) => c.charCodeAt(0)));
}
function b64Kodla(s) {
  let ikili = "";
  new TextEncoder().encode(s).forEach((b) => (ikili += String.fromCharCode(b)));
  return btoa(ikili);
}
function sade(s) {
  return s.replace(/I/g, "ı").replace(/İ/g, "i").toLowerCase()
    .replace(/[çğıöşü]/g, (c) => ({ ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u" }[c]));
}
function tarihTR(iso) {
  // "2026-10-24" -> Date (TR yerel gece yarısı, UTC+3)
  return new Date(`${iso}T00:00:00+03:00`);
}
function okunur(d, saatli = false) {
  const tr = new Date(d.getTime() + 3 * 3600e3); // UTC+3 bileşenleri
  let s = `${tr.getUTCDate()} ${AYLAR[tr.getUTCMonth()]} ${GUNLER[tr.getUTCDay()]}`;
  if (saatli) s += ` ${String(tr.getUTCHours()).padStart(2, "0")}:${String(tr.getUTCMinutes()).padStart(2, "0")}`;
  return s;
}
function kalan(iso) {
  const bugun = tarihTR(new Date(Date.now() + 3 * 3600e3).toISOString().slice(0, 10));
  const fark = Math.round((tarihTR(iso) - bugun) / 864e5);
  return fark === 0 ? "bugün" : fark === 1 ? "yarın" : fark > 0 ? `${fark} gün` : "geçti";
}
function bildir(mesaj) {
  const el = document.createElement("div");
  el.className = "bildirim";
  el.textContent = mesaj;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
function uyari(mesaj) {
  const el = $("#uyari");
  el.hidden = !mesaj;
  el.textContent = mesaj || "";
}

// ---------- GitHub API ----------
async function api(yol, secenek = {}) {
  const basliklar = { Accept: "application/vnd.github+json" };
  if (S.token) basliklar.Authorization = `Bearer ${S.token}`;
  return fetch(`https://api.github.com/repos/${S.repo}/${yol}`, {
    ...secenek, cache: "no-store", headers: { ...basliklar, ...(secenek.headers || {}) },
  });
}
async function dosyaOku(yol) {
  const r = await api(`contents/${yol}`);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${yol} okunamadı (HTTP ${r.status}). Repo adı ve anahtar doğru mu?`);
  const j = await r.json();
  return { icerik: JSON.parse(b64Coz(j.content)), sha: j.sha };
}

// Geliştirme: proje kökünü yerel sunucuyla açıp /docs/?yerel (veya ?yerel=ornek) ile dene; kaydetme kapalı
const YEREL = new URLSearchParams(location.search).get("yerel");
async function yerelOku(yol) {
  const r = await fetch(`../${yol}`, { cache: "no-store" });
  return r.ok ? { icerik: await r.json(), sha: "yerel" } : null;
}

async function yukle() {
  uyari("");
  try {
    const [cfg, durum] = YEREL != null
      ? await Promise.all([yerelOku("config/gorevler.json"),
          yerelOku(YEREL === "ornek" ? "tests/ornekler/panel_durum.json" : "data/durum.json")])
      : await Promise.all([dosyaOku("config/gorevler.json"), dosyaOku("data/durum.json")]);
    if (!cfg) throw new Error(`${S.repo} reposunda config/gorevler.json bulunamadı.`);
    S.cfg = cfg.icerik;
    S.sha = cfg.sha;
    S.orijinal = JSON.stringify(S.cfg);
    S.durum = durum ? durum.icerik : {};
    ciz();
  } catch (e) {
    uyari(e.message);
    $("#durum-satiri").textContent = "Veri yüklenemedi";
  }
}

// ---------- hatırlatma planı (hatirajan/hatirlatma.py planla() ile aynı mantık) ----------
function planla(gorev, olaylar) {
  const plan = [];
  for (const o of olaylar) {
    if (o.gecersiz) continue;
    for (const k of gorev.hatirlatmalar || []) {
      if (k.olay !== o.tur) continue;
      const [s, d] = (k.saat || "09:00").split(":").map(Number);
      const zaman = new Date(tarihTR(o.tarih).getTime() - (Number(k.gun_once) || 0) * 864e5 + (s * 60 + d) * 6e4);
      plan.push({ zaman, metin: `${TUR[o.tur]} (${okunur(tarihTR(o.tarih))})` });
    }
  }
  for (const oz of gorev.ozel_hatirlatmalar || []) {
    if (!oz.tarih) continue;
    const [s, d] = (oz.saat || "09:00").split(":").map(Number);
    plan.push({ zaman: new Date(tarihTR(oz.tarih).getTime() + (s * 60 + d) * 6e4), metin: `📌 ${oz.not || "Özel hatırlatma"}` });
  }
  return plan.filter((p) => p.zaman > new Date()).sort((a, b) => a.zaman - b.zaman);
}
function gorevDurumu(id) {
  return (S.durum.gorevler || {})[id] || {};
}

// ---------- çizim ----------
function ciz() {
  const son = S.durum.son_kontrol;
  $("#durum-satiri").textContent =
    (son ? `Son kontrol: ${okunur(new Date(son), true)}` : "Henüz kontrol yapılmadı") +
    (S.token ? "" : " · Salt okunur (düzenlemek için Bağlantı'dan anahtar gir)");
  $("#btn-kontrol").disabled = !S.token;
  cizYaklasan();
  cizGorevler();
  cizAyarlar();
  kirliMi();
}

function cizYaklasan() {
  const bugun = new Date(Date.now() + 3 * 3600e3).toISOString().slice(0, 10);
  const satirlar = [];
  for (const g of S.cfg.gorevler) {
    if (g.aktif === false) continue;
    for (const o of gorevDurumu(g.id).olaylar || []) {
      if (!o.gecersiz && o.tur !== "diger" && o.tarih >= bugun) satirlar.push({ g, o });
    }
  }
  satirlar.sort((a, b) => a.o.tarih.localeCompare(b.o.tarih));
  $("#yaklasan").innerHTML = satirlar.length
    ? satirlar.slice(0, 8).map(({ g, o }) => `<li><span><b>${kacis(TUR[o.tur])}</b> · ${kacis(g.ad)}</span>
        <span class="sag">${okunur(tarihTR(o.tarih))}${o.saat ? " " + o.saat : ""} · ${kalan(o.tarih)}</span></li>`).join("")
    : `<li class="bos">Henüz açıklanmış bir tarih yok — sistem takipte.</li>`;
}

function planHTML(g) {
  const plan = planla(g, gorevDurumu(g.id).olaylar || []);
  return plan.length
    ? plan.slice(0, 10).map((p) => `<li><span>${kacis(p.metin)}</span><span class="sag">${okunur(p.zaman, true)}</span></li>`).join("")
    : `<li class="bos">Tarih açıklanınca kurallara göre burada listelenir.</li>`;
}

function cizGorevler() {
  $("#gorevler").innerHTML = S.cfg.gorevler.map((g, i) => {
    const gd = gorevDurumu(g.id);
    const olaylar = (gd.olaylar || []).filter((o) => o.tur !== "diger").slice(-8).reverse();
    const duyurular = (gd.duyurular || []).slice(0, 5);
    const kaynaklar = (g.kaynaklar || []).map((k) => (typeof k === "string" ? k : k.url)).join("\n");
    const secenekler = (secili) => KURAL_OLAYLARI.map((t) =>
      `<option value="${t}"${t === secili ? " selected" : ""}>${TUR[t]}</option>`).join("");
    return `
    <details class="gorev" data-g="${i}"${S.acik.has(g.id) ? " open" : ""}>
      <summary>
        <div>
          <div class="gorev-ad">${kacis(g.ad || "Adsız görev")}</div>
          <div class="rozet${g.aktif === false ? " pasif" : ""}">${g.aktif === false ? "Duraklatıldı"
            : `${(g.hatirlatmalar || []).length} hatırlatma kuralı · ${(g.kaynaklar || []).length} kaynak`}</div>
        </div>
      </summary>
      <div class="gorev-govde">
        <div class="izgara" style="margin-top:14px">
          <label>Görev adı <input data-f="ad" value="${kacis(g.ad)}"></label>
          <label class="yatay"><input type="checkbox" data-f="aktif"${g.aktif === false ? "" : " checked"}> Takip açık</label>
        </div>

        <h3>Bulunan tarihler</h3>
        <ul class="liste">${olaylar.length ? olaylar.map((o) => `
          <li class="${o.gecersiz ? "gecersiz" : ""}"><span>${kacis(TUR[o.tur] || o.tur)}${o.gecersiz ? " (güncellendi)" : ""}
            ${o.duyuru_url ? `· <a href="${kacis(o.duyuru_url)}" target="_blank" rel="noopener">duyuru</a>` : ""}</span>
            <span class="sag">${okunur(tarihTR(o.tarih))}${o.saat ? " " + o.saat : ""}</span></li>`).join("")
          : `<li class="bos">Henüz tarih bulunmadı.</li>`}</ul>

        <h3>Planlanan hatırlatmalar</h3>
        <ul class="liste" data-plan="${i}">${planHTML(g)}</ul>

        <h3>Hatırlatma kuralları</h3>
        <div class="kural kural-baslik"><span>Olay</span><span>Kaç gün önce</span><span>Saat</span><span></span></div>
        <div data-liste="hatirlatmalar">${(g.hatirlatmalar || []).map((k, j) => `
          <div class="kural" data-i="${j}">
            <select data-k="olay" aria-label="Olay">${secenekler(k.olay)}</select>
            <label class="gun"><input type="number" min="0" max="90" data-k="gun_once" value="${Number(k.gun_once) || 0}" aria-label="Kaç gün önce"><span>gün önce</span></label>
            <input type="time" data-k="saat" value="${kacis(k.saat || "09:00")}" aria-label="Saat">
            <button class="sil" data-sil="hatirlatmalar" title="Sil" aria-label="Kuralı sil">×</button>
          </div>`).join("")}</div>
        <button class="metin" data-ekle="hatirlatmalar">+ Hatırlatma ekle</button>
        <p class="soluk kucuk">0 gün = olayın kendi günü. Her satır bir Telegram mesajı demek.</p>

        <h3>Özel hatırlatmalar</h3>
        <div data-liste="ozel_hatirlatmalar">${(g.ozel_hatirlatmalar || []).map((oz, j) => `
          <div class="kural ozel" data-i="${j}">
            <input type="date" data-k="tarih" value="${kacis(oz.tarih)}" aria-label="Tarih">
            <input type="time" data-k="saat" value="${kacis(oz.saat || "09:00")}" aria-label="Saat">
            <input data-k="not" value="${kacis(oz.not)}" placeholder="Not (ör. belgeleri hazırla)" aria-label="Not">
            <button class="sil" data-sil="ozel_hatirlatmalar" title="Sil" aria-label="Özel hatırlatmayı sil">×</button>
          </div>`).join("")}</div>
        <button class="metin" data-ekle="ozel_hatirlatmalar">+ Özel hatırlatma ekle</button>

        <h3>Son duyurular</h3>
        <ul class="liste">${duyurular.length ? duyurular.map((d) => `
          <li><a href="${kacis(d.url)}" target="_blank" rel="noopener">${kacis(d.baslik)}</a>
            <span class="sag">${d.bulundu ? okunur(new Date(d.bulundu)) : ""}</span></li>`).join("")
          : `<li class="bos">Henüz bildirilen duyuru yok.</li>`}</ul>

        <h3>Takip ayarları</h3>
        <label>Kaynak sayfalar (her satıra bir link)
          <textarea data-f="kaynaklar" spellcheck="false">${kacis(kaynaklar)}</textarea></label>
        <label>Anahtar kelimeler (her satıra bir tane; “a &amp; b” = ikisi birden geçmeli)
          <textarea data-f="anahtar_kelimeler">${kacis((g.anahtar_kelimeler || []).join("\n"))}</textarea></label>
        <label>Dışlanan kelimeler (başlıkta geçerse yok sayılır)
          <textarea data-f="dislanan_kelimeler">${kacis((g.dislanan_kelimeler || []).join("\n"))}</textarea></label>
        <button class="tehlike" data-gorev-sil>Görevi sil</button>
      </div>
    </details>`;
  }).join("");
}

function cizAyarlar() {
  const oz = ((S.cfg.ayarlar ||= {}).haftalik_ozet ||= { aktif: true, gun: 6, saat: "20:00" });
  document.querySelector('[data-ayar="aktif"]').checked = oz.aktif !== false;
  document.querySelector('[data-ayar="gun"]').value = String(oz.gun ?? 6);
  document.querySelector('[data-ayar="saat"]').value = oz.saat || "20:00";
}

function kirliMi() {
  const kirli = S.cfg && JSON.stringify(S.cfg) !== S.orijinal;
  $("#kaydet-cubugu").hidden = !kirli;
  return kirli;
}

// ---------- düzenleme ----------
function satirlar(metin) {
  return metin.split("\n").map((s) => s.trim()).filter(Boolean);
}

document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.dataset.ayar) {
    const oz = S.cfg.ayarlar.haftalik_ozet;
    oz[el.dataset.ayar] = el.type === "checkbox" ? el.checked : el.dataset.ayar === "gun" ? Number(el.value) : el.value;
    return kirliMi();
  }
  const kart = el.closest("[data-g]");
  if (!kart) return;
  const g = S.cfg.gorevler[Number(kart.dataset.g)];
  if (el.dataset.f) {
    const f = el.dataset.f;
    if (el.type === "checkbox") g[f] = el.checked;
    else if (f === "kaynaklar") {
      const eski = Object.fromEntries((g.kaynaklar || []).filter((k) => typeof k !== "string").map((k) => [k.url, k]));
      g.kaynaklar = satirlar(el.value).map((u) => eski[u] || u);
    } else if (el.tagName === "TEXTAREA") g[f] = satirlar(el.value);
    else g[f] = el.value;
  } else if (el.dataset.k) {
    const liste = el.closest("[data-liste]").dataset.liste;
    const oge = g[liste][Number(el.closest("[data-i]").dataset.i)];
    oge[el.dataset.k] = el.dataset.k === "gun_once" ? Math.max(0, Number(el.value) || 0) : el.value;
    const planEl = document.querySelector(`[data-plan="${kart.dataset.g}"]`);
    if (planEl) planEl.innerHTML = planHTML(g);
  }
  kirliMi();
});
document.addEventListener("toggle", (e) => {
  const kart = e.target.closest?.("details.gorev");
  if (!kart) return;
  const id = S.cfg.gorevler[Number(kart.dataset.g)].id;
  kart.open ? S.acik.add(id) : S.acik.delete(id);
}, true);

document.addEventListener("click", (e) => {
  const el = e.target;
  const kart = el.closest("[data-g]");
  if (!kart) return;
  const g = S.cfg.gorevler[Number(kart.dataset.g)];
  if (el.dataset.ekle) {
    const liste = (g[el.dataset.ekle] ||= []);
    if (el.dataset.ekle === "hatirlatmalar") liste.push({ olay: "basvuru_bitis", gun_once: 2, saat: "09:00" });
    else liste.push({ id: Math.random().toString(36).slice(2, 8), tarih: "", saat: "09:00", not: "" });
  } else if (el.dataset.sil) {
    g[el.dataset.sil].splice(Number(el.closest("[data-i]").dataset.i), 1);
  } else if ("gorevSil" in el.dataset) {
    if (!confirm(`“${g.ad}” görevi silinsin mi? (Kaydet'e basınca kalıcı olur)`)) return;
    S.cfg.gorevler.splice(Number(kart.dataset.g), 1);
  } else return;
  cizGorevler();
  kirliMi();
});

$("#btn-yeni").addEventListener("click", () => {
  const varsayilan = S.cfg.ayarlar?.varsayilan_hatirlatmalar || [];
  let id = "gorev-" + Math.random().toString(36).slice(2, 7);
  S.cfg.gorevler.push({
    id, ad: "Yeni görev", aktif: true, kaynaklar: [], anahtar_kelimeler: [], dislanan_kelimeler: [],
    hatirlatmalar: JSON.parse(JSON.stringify(varsayilan)), ozel_hatirlatmalar: [],
  });
  S.acik.add(id);
  cizGorevler();
  kirliMi();
  document.querySelector(`[data-g="${S.cfg.gorevler.length - 1}"]`).scrollIntoView({ behavior: "smooth" });
});

function dogrula() {
  const hatalar = [];
  const kimlikler = new Set();
  for (const g of S.cfg.gorevler) {
    const ad = g.ad || "Adsız görev";
    if (!g.ad?.trim()) hatalar.push("Bir görevin adı boş.");
    if (g.id.startsWith("gorev-") && g.ad && g.ad !== "Yeni görev" && !gorevDurumu(g.id).olaylar) {
      // yeni görevlere okunur bir kimlik ver (henüz durumu yokken değiştirmek güvenli)
      let yeni = sade(g.ad).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || g.id;
      while (kimlikler.has(yeni) || S.cfg.gorevler.some((x) => x !== g && x.id === yeni)) yeni += "-2";
      g.id = yeni;
    }
    kimlikler.add(g.id);
    if (!(g.kaynaklar || []).length) hatalar.push(`“${ad}”: en az bir kaynak link gerekli.`);
    if ((g.kaynaklar || []).some((k) => !/^https?:\/\//.test(typeof k === "string" ? k : k.url)))
      hatalar.push(`“${ad}”: kaynaklar http:// veya https:// ile başlamalı.`);
    if (!(g.anahtar_kelimeler || []).length) hatalar.push(`“${ad}”: en az bir anahtar kelime gerekli.`);
    if ((g.ozel_hatirlatmalar || []).some((o) => !o.tarih)) hatalar.push(`“${ad}”: özel hatırlatmada tarih boş.`);
  }
  return hatalar;
}

$("#btn-kaydet").addEventListener("click", async () => {
  if (YEREL != null) return bildir("Yerel deneme modu: kaydetme kapalı.");
  if (!S.token) return bildir("Kaydetmek için önce Bağlantı'dan erişim anahtarı gir.");
  const hatalar = dogrula();
  if (hatalar.length) return alert("Kaydedilemedi:\n\n" + hatalar.join("\n"));
  const btn = $("#btn-kaydet");
  btn.disabled = true;
  try {
    const r = await api("contents/config/gorevler.json", {
      method: "PUT",
      body: JSON.stringify({
        message: "Panel: görevler güncellendi",
        content: b64Kodla(JSON.stringify(S.cfg, null, 2) + "\n"),
        sha: S.sha,
      }),
    });
    if (r.status === 409 || r.status === 422) throw new Error("Dosya başka bir yerden değişmiş. Sayfayı yenileyip tekrar dene.");
    if (r.status === 401 || r.status === 403) throw new Error("Anahtar reddedildi. Contents: Read and write izni var mı?");
    if (!r.ok) throw new Error(`Kaydedilemedi (HTTP ${r.status}).`);
    S.sha = (await r.json()).content.sha;
    S.orijinal = JSON.stringify(S.cfg);
    cizGorevler();
    kirliMi();
    bildir("Kaydedildi ✓ Bir sonraki kontrolde geçerli olur.");
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
  }
});

$("#btn-vazgec").addEventListener("click", () => {
  S.cfg = JSON.parse(S.orijinal);
  ciz();
});

$("#btn-kontrol").addEventListener("click", async () => {
  const btn = $("#btn-kontrol");
  btn.disabled = true;
  try {
    const repo = await (await api("")).json();
    const r = await api(`actions/workflows/${WORKFLOW}/dispatches`, {
      method: "POST",
      body: JSON.stringify({ ref: repo.default_branch || "main", inputs: { islem: "kontrol" } }),
    });
    if (!r.ok) throw new Error(r.status === 403 ? "Anahtarın Actions: Read and write izni yok." : `Başlatılamadı (HTTP ${r.status}).`);
    bildir("Kontrol başlatıldı. Yeni duyuru varsa birkaç dakikada Telegram'a düşer.");
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
  }
});

$("#btn-ayarlar").addEventListener("click", () => {
  const kutu = $("#ayarlar");
  kutu.hidden = !kutu.hidden;
  $("#btn-ayarlar").setAttribute("aria-expanded", String(!kutu.hidden));
});
$("#btn-baglan").addEventListener("click", () => {
  S.repo = $("#inp-repo").value.trim() || S.repo;
  S.token = $("#inp-token").value.trim();
  depola("hatirajan_repo", S.repo);
  depola("hatirajan_token", S.token || null);
  $("#ayarlar").hidden = true;
  yukle();
});
$("#btn-cikis").addEventListener("click", () => {
  depola("hatirajan_token", null);
  S.token = "";
  $("#inp-token").value = "";
  bildir("Anahtar bu cihazdan silindi.");
  ciz();
});

window.addEventListener("beforeunload", (e) => {
  if (kirliMi()) e.preventDefault();
});

// ---------- başlat ----------
(function baslat() {
  const tahmin = location.hostname.endsWith(".github.io")
    ? `${location.hostname.split(".")[0]}/${location.pathname.split("/")[1] || "hatirajan"}`
    : "fetiicolak/hatirajan";
  S.repo = oku("hatirajan_repo") || tahmin;
  S.token = oku("hatirajan_token");
  $("#inp-repo").value = S.repo;
  $("#inp-token").value = S.token;
  if (!S.token && YEREL == null) $("#ayarlar").hidden = false;
  yukle();
})();
