#!/usr/bin/env python3
"""
Av. Baran Doğan makale arşivi derleyicisi.

Kaynak : https://barandogan.av.tr
İzin   : Av. Baran Doğan, atıf şartıyla kullanım izni vermiştir (bkz. IZIN.md).

İki aşamada çalışır:
  1. tara   : sitemap + blog kategori sayfaları + makale içi bağlantılar taranır,
              ham sayfalar .onbellek/ klasörüne kaydedilir.
  2. derle  : önbellekteki sayfalar Markdown'a çevrilir, hukuk alanlarına göre
              sınıflandırılır ve derleme dosyaları üretilir.

Kullanım:
    pip install -r requirements.txt
    python scraper.py                    # tara + derle
    python scraper.py --limit 10         # deneme
    python scraper.py --yalniz-derle     # siteye gitmeden yeniden derle
    python scraper.py --yenile           # önbelleği yok sayıp tüm sayfaları yeniden indir
    python scraper.py --mevzuat          # /blog/mevzuat/ madde notlarını da dahil et
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

from siniflandirma import ALANLAR, GRUP_SIRASI, siniflandir

SITE = "https://barandogan.av.tr"
HOST = "barandogan.av.tr"
AUTHOR = "Av. Baran Doğan"
USER_AGENT = "BaranDoganArsivBot/1.0 (+izinli, atifli, ticari olmayan arsiv; X: @isthis_legal)"
DELAY = 1.5

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".onbellek"
OUT = ROOT / "makaleler"
BUILD = ROOT / "derlemeler"

HARIC = {
    "", "/hakkimizda", "/iletisim", "/faaliyet-alanlarimiz", "/blog",
    "/gizlilik-politikasi", "/kvkk-aydinlatma-metni",
    "/avukat-baran-dogan-nerelidir-ve-kimdir",
    "/turk-ceza-kanunu", "/5271-sayili-ceza-muhakemesi-kanunu-cmk",
}
DOSYA_UZANTILARI = re.compile(r"\.(jpe?g|png|gif|webp|svg|pdf|docx?|xlsx?|zip|css|js|ico|xml|txt|mp4|mp3)$", re.I)

ATIF_NOTU = (
    "> **Kaynak ve atıf:** Bu metin {author} tarafından kaleme alınmış olup orijinali "
    "<{url}> adresinde yayımlanmaktadır. Yazarın izniyle, atıflı ve ticari olmayan amaçla "
    "arşivlenmiştir. Tüm hakları yazara aittir.\n>\n"
    "> **Uyarı:** Metin, yayım veya son güncelleme tarihindeki mevzuat ve içtihada dayanmaktadır; "
    "güncel mevzuat ve içtihatla teyit edilmeden kullanılmamalıdır. Hukuki mütalaa niteliği taşımaz."
)

ATIF_DESENI = re.compile(
    r"\b(TCK|CMK|HMK|TMK|TBK|TTK|İİK|IIK|İYUK|IYUK|VUK|AİHS|AIHS|CGTİK|KVKK|AY)\s*"
    r"(?:m\.|md\.|madde(?:si)?|maddesi)?\s*(\d{1,4}(?:/\d+)?)",
)


# ----------------------------------------------------------------- yardımcılar
def normalize(url: str) -> str | None:
    p = urlparse(url)
    if p.scheme not in ("http", "https") or p.netloc.lower().removeprefix("www.") != HOST:
        return None
    path = re.sub(r"/+$", "", re.sub(r"\.html?$", "", p.path, flags=re.I))
    if DOSYA_UZANTILARI.search(path):
        return None
    return f"{SITE}{path}"


def aday_mi(url: str, mevzuat: bool) -> tuple[str, str] | None:
    """Makale adayıysa (site_kategori, slug) döner."""
    path = urlparse(url).path
    if path in HARIC:
        return None
    parts = [x for x in path.split("/") if x]
    if parts and parts[0] == "blog":
        if len(parts) < 3:
            return None
        if parts[1] == "mevzuat" and not mevzuat:
            return None
        return parts[1], parts[-1]
    if len(parts) == 1:
        return "diger", parts[0]
    return None


def onbellek_yolu(url: str) -> Path:
    return CACHE / "sayfalar" / (hashlib.sha1(url.encode()).hexdigest() + ".html")


class Tarayici:
    def __init__(self, yenile: bool):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "tr-TR,tr;q=0.9"})
        self.yenile = yenile
        self.son = 0.0

    def getir(self, url: str, onbellek: bool = True) -> str | None:
        yol = onbellek_yolu(url)
        if onbellek and yol.exists() and not self.yenile:
            return yol.read_text(encoding="utf-8")
        for deneme in range(1, 4):
            bekle = DELAY - (time.time() - self.son)
            if bekle > 0:
                time.sleep(bekle)
            try:
                r = self.s.get(url, timeout=30)
                self.son = time.time()
                if r.status_code == 200:
                    r.encoding = r.apparent_encoding if not r.encoding else r.encoding
                    if onbellek:
                        yol.parent.mkdir(parents=True, exist_ok=True)
                        yol.write_text(r.text, encoding="utf-8")
                    return r.text
                if r.status_code in (404, 410):
                    return None
            except requests.RequestException as exc:
                print(f"  ! {url} ({deneme}): {exc}", file=sys.stderr)
            time.sleep(DELAY * deneme * 2)
        return None


def baglantilar(html: str, taban: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    out = set()
    for a in soup.find_all("a", href=True):
        u = normalize(urljoin(taban, a["href"]).split("#")[0].split("?")[0])
        if u:
            out.add(u)
    return out


# ----------------------------------------------------------------------- tara
def tara(limit: int, mevzuat: bool, yenile: bool) -> None:
    t = Tarayici(yenile)
    durum_yolu = CACHE / "durum.json"
    durum = json.loads(durum_yolu.read_text(encoding="utf-8")) if durum_yolu.exists() else {}
    adaylar: dict[str, dict] = {}

    # 1) sitemap
    xml_text = t.getir(f"{SITE}/sitemap.xml", onbellek=False)
    if not xml_text:
        sys.exit("Sitemap alınamadı.")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for node in ET.fromstring(xml_text).findall("sm:url", ns):
        u = normalize((node.findtext("sm:loc", "", ns) or "").strip())
        if u and aday_mi(u, mevzuat):
            adaylar[u] = {"lastmod": (node.findtext("sm:lastmod", "", ns) or "")[:10], "kaynak": "sitemap"}
    print(f"Sitemap: {len(adaylar)} aday")

    # 2) blog ana ve kategori sayfaları
    liste_sayfalari = {f"{SITE}/blog"}
    ana = t.getir(f"{SITE}/blog", onbellek=False) or ""
    liste_sayfalari |= {u for u in baglantilar(ana, SITE) if re.fullmatch(rf"{re.escape(SITE)}/blog/[^/]+", u)}
    for ls in sorted(liste_sayfalari):
        html = t.getir(ls, onbellek=False)
        if not html:
            continue
        for u in baglantilar(html, ls):
            if aday_mi(u, mevzuat) and u not in adaylar:
                adaylar[u] = {"lastmod": "", "kaynak": "kategori"}
    print(f"Kategori sayfalarıyla: {len(adaylar)} aday")

    # 3) makaleleri indir; içlerindeki bağlantılardan yeni adaylar keşfet
    sira = sorted(adaylar)
    islenen = set()
    i = 0
    while sira:
        url = sira.pop(0)
        if url in islenen:
            continue
        islenen.add(url)
        i += 1
        if limit and i > limit:
            break
        onceden = onbellek_yolu(url).exists() and not yenile
        if not onceden:
            print(f"[{i}] {url}")
        html = t.getir(url)
        kayit = adaylar[url]
        kayit["durum"] = "ok" if html else "hata"
        durum[url] = kayit
        if not html:
            continue
        for u in baglantilar(html, url):
            if u not in adaylar and aday_mi(u, mevzuat):
                adaylar[u] = {"lastmod": "", "kaynak": "ic-baglanti"}
                sira.append(u)
                print(f"   + yeni aday: {u}")

    # sitede artık bulunmayanları işaretle
    for u in list(durum):
        if u not in adaylar:
            durum[u]["durum"] = "kaldirilmis"
    durum_yolu.parent.mkdir(parents=True, exist_ok=True)
    durum_yolu.write_text(json.dumps(durum, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    c = Counter(v["kaynak"] for v in durum.values() if v.get("durum") == "ok")
    print(f"Tarama tamam: {sum(c.values())} sayfa ({dict(c)})")


# ---------------------------------------------------------------------- derle
def yaml_str(s: str) -> str:
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def cikar(html: str, url: str) -> dict | None:
    govde = trafilatura.extract(
        html, url=url, output_format="markdown", include_tables=True, include_links=False,
        include_images=False, include_comments=False, favor_recall=True, deduplicate=False,
    )
    if not govde or len(govde.strip()) < 300:
        return None
    meta = trafilatura.extract_metadata(html, default_url=url)
    baslik = (meta.title if meta and meta.title else "").strip()
    baslik = re.sub(r"\s*[|\-–—]\s*(Av\.?\s*)?(Avukat\s*)?Baran Doğan.*$", "", baslik, flags=re.I).strip()
    govde = govde.strip()
    ilk, _, kalan = govde.partition("\n")
    if ilk.startswith("# "):
        h1 = ilk[2:].strip()
        if not baslik:
            baslik = h1
        if h1.casefold() == baslik.casefold():
            govde = kalan.strip()
    # sitenin şablon metinlerini temizle
    govde = "\n\n".join(
        par for par in govde.split("\n\n")
        if not re.search(r"avukatbd@gmail\.com|Web sitemizdeki tüm makale ve içeriklerin telif hakkı", par)
        and not re.fullmatch(r"[#*\s]*(UYARI|Uyarı|Makale Yazarlığı İçin|MAKALE YAZARLIĞI İÇİN)[*\s:]*", par)
    )
    for _ in range(3):
        govde = re.sub(r"\n\s*(UYARI|Makale Yazarlığı İçin)\s*$", "", govde.rstrip())
    tarih = (meta.date if meta and meta.date else "") or ""
    return {"baslik": baslik or url.rsplit("/", 1)[-1], "govde": govde.strip(), "tarih": tarih[:10]}


def atiflar(metin: str, en_cok: int = 12) -> list[str]:
    say = Counter()
    for kanun, madde in ATIF_DESENI.findall(metin):
        kanun = {"IIK": "İİK", "IYUK": "İYUK", "AIHS": "AİHS"}.get(kanun, kanun)
        say[f"{kanun} {madde}"] += 1
    return [k for k, _ in say.most_common(en_cok)]


def derle(mevzuat: bool) -> None:
    durum_yolu = CACHE / "durum.json"
    if not durum_yolu.exists():
        sys.exit("Önce tarama yapılmalı (önbellek boş).")
    durum = json.loads(durum_yolu.read_text(encoding="utf-8"))

    if OUT.exists():
        shutil.rmtree(OUT)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    OUT.mkdir()
    BUILD.mkdir()

    kayitlar, hatalar, kisa, mukerrer = [], [], [], []
    gorulen_ozet: dict[str, str] = {}
    for url in sorted(durum):
        bilgi = durum[url]
        if bilgi.get("durum") != "ok":
            if bilgi.get("durum") == "hata":
                hatalar.append(url)
            continue
        a = aday_mi(url, mevzuat)
        if not a:
            continue
        site_kat, slug = a
        yol = onbellek_yolu(url)
        if not yol.exists():
            hatalar.append(url)
            continue
        c = cikar(yol.read_text(encoding="utf-8"), url)
        if not c:
            kisa.append(url)
            continue
        ozet = hashlib.sha1(re.sub(r"\s+", " ", c["govde"]).encode()).hexdigest()
        if ozet in gorulen_ozet:
            mukerrer.append((url, gorulen_ozet[ozet]))
            continue
        gorulen_ozet[ozet] = url
        alan, gerekce = siniflandir(slug, site_kat)
        kayitlar.append({**c, "url": url, "slug": slug, "site_kategori": site_kat, "alan": alan,
                         "gerekce": gerekce, "lastmod": bilgi.get("lastmod", ""),
                         "atiflar": atiflar(c["govde"])})

    # dosya adı çakışmalarını çöz
    adlar = Counter((k["alan"], k["slug"]) for k in kayitlar)
    for k in kayitlar:
        k["dosya_adi"] = k["slug"] if adlar[(k["alan"], k["slug"])] == 1 else f"{k['site_kategori']}--{k['slug']}"

    for k in kayitlar:
        klasor, alan_adi, grup = ALANLAR[k["alan"]]
        yol = OUT / klasor / f"{k['dosya_adi']}.md"
        yol.parent.mkdir(parents=True, exist_ok=True)
        k["dosya"] = yol.relative_to(ROOT).as_posix()
        on = [
            "---",
            f"baslik: {yaml_str(k['baslik'])}",
            f"yazar: {yaml_str(AUTHOR)}",
            f"hukuk_alani: {yaml_str(alan_adi)}",
            f"ust_grup: {yaml_str(grup)}",
            f"site_kategorisi: {k['site_kategori']}",
            f"kaynak_url: {k['url']}",
        ]
        if k["tarih"]:
            on.append(f"yayim_tarihi: {k['tarih']}")
        on += [
            f"son_guncelleme: {k['lastmod'] or 'bilinmiyor'}",
            "anilan_maddeler: [" + ", ".join(yaml_str(a) for a in k["atiflar"]) + "]",
            "lisans: Yazarın izniyle, atıflı ve ticari olmayan kullanım (bkz. IZIN.md)",
            "---",
        ]
        yol.write_text(
            "\n".join(on) + f"\n\n# {k['baslik']}\n\n" + ATIF_NOTU.format(author=AUTHOR, url=k["url"])
            + f"\n\n{k['govde']}\n\n---\n*Kaynak: {AUTHOR} — {k['url']}*\n",
            encoding="utf-8",
        )

    _derlemeler(kayitlar)
    _rapor(kayitlar, hatalar, kisa, mukerrer)


def _blok(k: dict) -> str:
    return (f"\n\n---\n\n## {k['baslik']}\n\n*Kaynak: {AUTHOR} — {k['url']}"
            f" (son güncelleme: {k['lastmod'] or 'bilinmiyor'})*\n\n{k['govde']}\n")


def _ust_bilgi(baslik: str, adet: int) -> str:
    return (f"# {AUTHOR} — {baslik}\n\n"
            f"Bu derleme, {AUTHOR}'ın {SITE} adresinde yayımlanan {adet} yazısını içermektedir. "
            "Yazarın izniyle, atıflı ve ticari olmayan amaçla oluşturulmuştur; tüm hakları yazara aittir. "
            "Her yazının başında orijinal kaynak bağlantısı yer almaktadır. Metinler yayım veya son güncelleme "
            "tarihindeki mevzuata dayanmaktadır; güncel mevzuat ve içtihatla teyit edilmeden kullanılmamalıdır.\n\n"
            "Yapay zekâ ile kullanırken: yanıtların yalnızca bu metinlere dayanmasını ve her tespitin yanında "
            "ilgili yazının kaynak bağlantısının belirtilmesini isteyiniz.\n")


def _grup_slug(grup: str) -> str:
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return re.sub(r"[^a-z0-9]+", "-", grup.translate(tr).lower()).strip("-")


def _derlemeler(kayitlar: list[dict]) -> None:
    alana_gore: dict[str, list[dict]] = defaultdict(list)
    for k in kayitlar:
        alana_gore[k["alan"]].append(k)
    for v in alana_gore.values():
        v.sort(key=lambda k: k["baslik"].casefold())
    sirali_alanlar = [a for a in ALANLAR if a in alana_gore]

    # alan derlemeleri
    (BUILD / "alanlar").mkdir()
    for a in sirali_alanlar:
        klasor, ad, _ = ALANLAR[a]
        metin = _ust_bilgi(ad, len(alana_gore[a])) + "".join(_blok(k) for k in alana_gore[a])
        (BUILD / "alanlar" / f"{klasor}.md").write_text(metin, encoding="utf-8")

    # üst grup derlemeleri
    (BUILD / "gruplar").mkdir()
    for grup in GRUP_SIRASI:
        alanlar = [a for a in sirali_alanlar if ALANLAR[a][2] == grup]
        if not alanlar:
            continue
        adet = sum(len(alana_gore[a]) for a in alanlar)
        metin = _ust_bilgi(grup, adet)
        for a in alanlar:
            metin += f"\n\n# {ALANLAR[a][1]}\n" + "".join(_blok(k) for k in alana_gore[a])
        (BUILD / "gruplar" / f"{_grup_slug(grup)}.md").write_text(metin, encoding="utf-8")

    # tümü
    metin = _ust_bilgi("Makale Arşivi (Tümü)", len(kayitlar))
    for a in sirali_alanlar:
        metin += f"\n\n# {ALANLAR[a][1]}\n" + "".join(_blok(k) for k in alana_gore[a])
    (BUILD / "TUMU.md").write_text(metin, encoding="utf-8")

    # index.json
    index = [{
        "baslik": k["baslik"], "hukuk_alani": ALANLAR[k["alan"]][1], "ust_grup": ALANLAR[k["alan"]][2],
        "kaynak_url": k["url"], "son_guncelleme": k["lastmod"], "yayim_tarihi": k["tarih"],
        "anilan_maddeler": k["atiflar"], "dosya": k["dosya"],
    } for a in sirali_alanlar for k in alana_gore[a]]
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

    # İÇİNDEKİLER ve llms.txt
    ic = [f"# İçindekiler — {AUTHOR} Makale Arşivi", "", f"Toplam **{len(kayitlar)}** yazı.", ""]
    llms = [f"# {AUTHOR} — Makale Arşivi", "",
            f"> {SITE} kaynaklı, yazar izniyle atıflı arşiv. {len(kayitlar)} yazı, hukuk alanlarına göre sınıflandırılmıştır.",
            "", "Tüm yazılar tek dosyada: derlemeler/TUMU.md", ""]
    for grup in GRUP_SIRASI:
        alanlar = [a for a in sirali_alanlar if ALANLAR[a][2] == grup]
        if not alanlar:
            continue
        ic += [f"## {grup}", ""]
        for a in alanlar:
            klasor, ad, _ = ALANLAR[a]
            ic += [f"### {ad} ({len(alana_gore[a])})", "",
                   f"Derleme: [derlemeler/alanlar/{klasor}.md](derlemeler/alanlar/{klasor}.md)", ""]
            ic += [f"- [{k['baslik']}]({k['dosya']}) — [kaynak]({k['url']})" for k in alana_gore[a]]
            ic.append("")
            llms += [f"## {ad}", f"Derleme: derlemeler/alanlar/{klasor}.md", ""]
            llms += [f"- [{k['baslik']}]({k['dosya']}): {k['url']}" for k in alana_gore[a]]
            llms.append("")
    (ROOT / "ICINDEKILER.md").write_text("\n".join(ic), encoding="utf-8")
    (ROOT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")

    # README istatistik tablosu
    readme = ROOT / "README.md"
    if readme.exists():
        kelime = sum(len(re.findall(r"\w+", k["govde"])) for k in kayitlar)
        yillar = sorted(k["tarih"][:4] for k in kayitlar if k["tarih"])
        aralik = f", yayım yılları {yillar[0]}–{yillar[-1]}" if yillar else ""
        nokta = lambda n: f"{n:,}".replace(",", ".")
        tablo = [f"**{len(kayitlar)} yazı · {nokta(kelime)} kelime · A4 düzeninde yaklaşık {nokta(round(kelime / 500))} sayfa"
                 f" · {len(sirali_alanlar)} hukuk alanı{aralik}**", "",
                 "| Üst grup | Hukuk alanı | Yazı | Derleme |", "|---|---|---:|---|"]
        for grup in GRUP_SIRASI:
            for a in [x for x in sirali_alanlar if ALANLAR[x][2] == grup]:
                klasor, ad, _ = ALANLAR[a]
                tablo.append(f"| {grup} | {ad} | {len(alana_gore[a])} | [{klasor}.md](derlemeler/alanlar/{klasor}.md) |")
        tablo.append(f"| | **Toplam** | **{len(kayitlar)}** | [TUMU.md](derlemeler/TUMU.md) |")
        tablo.append(f"\n*Son güncelleme: {dt.date.today().isoformat()}*")
        s = readme.read_text(encoding="utf-8")
        s = re.sub(r"(<!-- TABLO-BASLA -->).*?(<!-- TABLO-BITIR -->)",
                   lambda m: m.group(1) + "\n" + "\n".join(tablo) + "\n" + m.group(2), s, flags=re.S)
        readme.write_text(s, encoding="utf-8")


def _rapor(kayitlar, hatalar, kisa, mukerrer) -> None:
    varsayilan = [(k["alan"], k["slug"]) for k in kayitlar if k["gerekce"] == "varsayilan"]
    rapor = {
        "toplam_yazi": len(kayitlar),
        "alan_dagilimi": dict(Counter(ALANLAR[k["alan"]][1] for k in kayitlar).most_common()),
        "indirilemeyen": hatalar,
        "icerik_cikarilamayan": kisa,
        "mukerrer_atlanan": mukerrer,
        "varsayilan_ile_siniflanan": varsayilan,
        "atama_listesi": {k["slug"]: k["alan"] for k in kayitlar},
    }
    (CACHE / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    boyut = (BUILD / "TUMU.md").stat().st_size / 1_048_576
    print(f"Derleme tamam: {len(kayitlar)} yazı, {len(rapor['alan_dagilimi'])} alan, TUMU.md ≈ {boyut:.1f} MB")
    print(f"  indirilemeyen: {len(hatalar)}, içerik çıkarılamayan: {len(kisa)}, mükerrer: {len(mukerrer)}, "
          f"varsayılanla sınıflanan: {len(varsayilan)}")


# ----------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--yalniz-derle", action="store_true")
    ap.add_argument("--yenile", action="store_true")
    ap.add_argument("--mevzuat", action="store_true")
    a = ap.parse_args()
    if not a.yalniz_derle:
        tara(a.limit, a.mevzuat, a.yenile)
    derle(a.mevzuat)


if __name__ == "__main__":
    main()
