"""
Hukuk alanı sınıflandırması.

Makaleler, adres kısaltmalarındaki (slug) anahtar ifadelere ve sitedeki
kategoriye göre aşağıdaki alanlardan birine atanır. Kurallar yukarıdan aşağıya
denenir; ilk eşleşen kural uygulanır. Yanlış sınıflanan bir yazı için
ELLE_ATAMA sözlüğüne "slug": "alan_kodu" eklenmesi yeterlidir.
"""
from __future__ import annotations

import re

# kod: (klasör, görünen ad, üst grup)
ALANLAR: dict[str, tuple[str, str, str]] = {
    "ceza_genel":      ("01-ceza-genel-hukumler", "Ceza Hukuku — Genel Hükümler ve Yaptırımlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "hayat_vucut":     ("02-hayata-ve-vucut-dokunulmazligina-karsi-suclar", "Hayata ve Vücut Dokunulmazlığına Karşı Suçlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "cinsel":          ("03-cinsel-suclar-ve-mustehcenlik", "Cinsel Suçlar ve Müstehcenlik", "Ceza ve Ceza Muhakemesi Hukuku"),
    "hurriyet":        ("04-hurriyet-seref-ozel-hayat-ve-aile-duzenine-karsi-suclar", "Hürriyete, Şerefe, Özel Hayata ve Aile Düzenine Karşı Suçlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "malvarligi":      ("05-malvarligina-karsi-suclar", "Malvarlığına Karşı Suçlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "bilisim":         ("06-bilisim-suclari-ve-internet-hukuku", "Bilişim Suçları ve İnternet Hukuku", "Ceza ve Ceza Muhakemesi Hukuku"),
    "uyusturucu":      ("07-uyusturucu-suclari", "Uyuşturucu ve Uyarıcı Madde Suçları", "Ceza ve Ceza Muhakemesi Hukuku"),
    "kamu_guveni":     ("08-kamu-guveni-ve-genel-guvenlige-karsi-suclar", "Kamu Güvenine, Genel Güvenliğe ve Çevreye Karşı Suçlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "kamu_idaresi":    ("09-kamu-idaresi-ve-adliyeye-karsi-suclar", "Kamu İdaresinin Güvenilirliğine ve Adliyeye Karşı Suçlar", "Ceza ve Ceza Muhakemesi Hukuku"),
    "devlet":          ("10-devlet-guvenligi-kamu-baris-ve-teror-suclari", "Devlet Güvenliği, Kamu Barışı ve Terör Suçları", "Ceza ve Ceza Muhakemesi Hukuku"),
    "ekonomik":        ("11-ekonomik-suclar-ve-ozel-ceza-kanunlari", "Ekonomik Suçlar ve Özel Ceza Kanunları", "Ceza ve Ceza Muhakemesi Hukuku"),
    "uluslararasi":    ("12-uluslararasi-ceza-hukuku", "Uluslararası Suçlar ve Uluslararası Ceza Hukuku", "Ceza ve Ceza Muhakemesi Hukuku"),
    "ceza_ozel_diger": ("13-diger-suc-tipleri", "Diğer Suç Tipleri", "Ceza ve Ceza Muhakemesi Hukuku"),
    "muhakeme":        ("14-ceza-muhakemesi-hukuku", "Ceza Muhakemesi Hukuku", "Ceza ve Ceza Muhakemesi Hukuku"),
    "infaz":           ("15-infaz-hukuku", "İnfaz Hukuku", "Ceza ve Ceza Muhakemesi Hukuku"),
    "aile":            ("16-aile-ve-kisiler-hukuku", "Aile ve Kişiler Hukuku", "Özel Hukuk"),
    "miras":           ("17-miras-hukuku", "Miras Hukuku", "Özel Hukuk"),
    "esya":            ("18-esya-ve-gayrimenkul-hukuku", "Eşya ve Gayrimenkul Hukuku", "Özel Hukuk"),
    "borclar":         ("19-borclar-ve-tazminat-hukuku", "Borçlar ve Tazminat Hukuku", "Özel Hukuk"),
    "is":              ("20-is-ve-sosyal-guvenlik-hukuku", "İş ve Sosyal Güvenlik Hukuku", "Özel Hukuk"),
    "ticaret":         ("21-ticaret-ve-sirketler-hukuku", "Ticaret ve Şirketler Hukuku", "Özel Hukuk"),
    "medeni_usul":     ("22-medeni-usul-ve-arabuluculuk", "Medeni Usul Hukuku ve Arabuluculuk", "Usul ve İcra-İflas Hukuku"),
    "icra":            ("23-icra-ve-iflas-hukuku", "İcra ve İflas Hukuku", "Usul ve İcra-İflas Hukuku"),
    "idare":           ("24-idare-ve-vergi-hukuku", "İdare ve Vergi Hukuku", "Kamu Hukuku ve İnsan Hakları"),
    "anayasa":         ("25-anayasa-bireysel-basvuru-ve-aihm", "Anayasa Hukuku, Bireysel Başvuru ve AİHM", "Kamu Hukuku ve İnsan Hakları"),
    "dilekce":         ("26-dilekce-ve-form-ornekleri", "Dilekçe ve Form Örnekleri", "Uygulama Araçları"),
    "avukatlik":       ("27-avukatlik-ve-meslek-hukuku", "Avukatlık ve Meslek Hukuku", "Uygulama Araçları"),
    "mevzuat":         ("28-mevzuat-notlari", "Mevzuat Notları", "Uygulama Araçları"),
    "diger":           ("29-diger", "Diğer", "Uygulama Araçları"),
}

GRUP_SIRASI = [
    "Ceza ve Ceza Muhakemesi Hukuku",
    "Özel Hukuk",
    "Usul ve İcra-İflas Hukuku",
    "Kamu Hukuku ve İnsan Hakları",
    "Uygulama Araçları",
]

# Elle düzeltmeler: "slug": "alan_kodu"
ELLE_ATAMA: dict[str, str] = {
    "hirsizlik-zimmet-gasp-sucu-malin-degerinin-azligi-nedeniyle-ceza-indirimi": "malvarligi",
    "basit-ve-nitelikli-bankacilik-zimmeti-sucu-cezasi": "ekonomik",
    "uluslararasi-suclarda-hukuka-uygunluk-nedenleri": "uluslararasi",
    "cinsel-suclarda-magdur-sikayetci-beyaninin-delil-degeri": "muhakeme",
    "banka-veya-kredi-kartinin-kotuye-kullanilmasi-sucunda-delillerin-arastirilmasi": "malvarligi",
    "durusmada-video-ses-veya-fotograf-cekme-suc-ve-yasak-midir": "muhakeme",
    "ses-ve-fotograf-goruntu-kaydi-karsilastirma-ve-analizi": "muhakeme",
    "avukatin-konutunun-ve-ofis-burosunun-aranmasi-ve-arama-karari-nasil-uygulanir": "avukatlik",
    "kisisel-saglik-verilerinin-korunmasi": "anayasa",
    "ic-guvenlik-paketi": "ceza_genel",
    "idari-para-cezasi": "ceza_genel",
    "cezayi-aleyhe-degistirme-yasagi": "muhakeme",
    "cocugun-sikayet-hakki-ve-diger-haklarinin-kullanilmasi": "muhakeme",
    "devletin-guvenligine-iliskin-belgeleri-yok-etme-tahrip-etme-veya-sahtecilik": "devlet",
    "yasaklanan-bilgileri-veya-askeri-casusluk-maksadiyla-aciklama": "devlet",
    "faydasiz-sahtecilik-nedir-nasil-olusur": "kamu_guveni",
    "sahte-belge-veya-muhteviyati-itibariyle-yaniltici-belge-duzenleme-ve-kullanma": "ekonomik",
    "gecici-nedenler-alkol-veya-uyusturucu-madde-etkisinde-olma-uyusturucu-bagimliligi": "ceza_genel",
    "saglik-icin-tehlikeli-madde-temini-sucu": "kamu_guveni",
    "hukumlu-tutuklu-gozaltina-alinanin-kacmasina-imkan-saglama-yardim-etme": "kamu_idaresi",
    "ilgilinin-veya-magdurun-rizasi-nedir-tck-26": "ceza_genel",
    "mesru-mudafaa-mesru-savunma-nedir": "ceza_genel",
    "guvenlik-tedbiri-karari-nedir": "ceza_genel",
    "durusmalarda-avukatin-ayaga-kalkmasi": "avukatlik",
    "baskasina-ait-kimlik-bilgilerinin-kullanilmasi-sucu": "kamu_idaresi",
    "hile-aldatma-nedir-tbk": "borclar",
    "mirasta-mal-paylasimi-ve-mirascilik-nedir": "miras",
    "muvazaa-davasi-nedir": "borclar",
    "27-mayis-1960-darbesi-magdurlari-ve-mirascilarina-maddi-manevi-tazminat": "borclar",
    "zorunlu-arabuluculuk-sartlari-menfi-tespit-ve-tasarrufun-iptali-davalarinda-zorunlu-arabuluculuk": "medeni_usul",
    "tam-yargi-davasi-ve-idareye-tazminat-davasi-nasil-acilir": "idare",
    "ticari-isletmenin-devri-sozlesmesi": "ticaret",
}

SUC = re.compile(r"(^|-)(suc|sucu|suclar|suclari|sucun|sucunun|sucuna|sucunda|cezasi)(-|$)"
                 r"|tck-(7[6-9]|[89]\d|[1-3]\d\d)(-|$)")

# (alan, desen, yalnızca suç yazılarında mı, sınırlı site kategorileri veya None)
KURALLAR: list[tuple[str, str, bool, set[str] | None]] = [
    # 1. Dilekçe ve form örnekleri
    ("dilekce", r"dilekce(si)?-ornegi|dilekcesi(-|$)|basvuru-formu|tutanagi$", False, None),

    # 2. Adında "suç" geçen ama genel hükümlere / usule ilişkin yazılar
    ("ceza_genel", r"suca-istirak|suca-tesebbus|suc-ve-cezanin-sahsiligi|katalog-suc|zincirleme-suc|neticesi-sebebiyle|"
                   r"yuz-kizartici|sikayete-bagli-suclar|gorunuste-ictima", False, None),
    ("muhakeme", r"mahkemesinin-gorevi|mahkemesi-gorevi|suclari-mahkemesi|suc-vasfina|sucu-ikrar|"
                 r"mahkemesi-gorevine", False, {"ceza-hukuku"}),

    # 3. Suç tipleri (yalnızca adında suç/ceza geçen yazılar)
    ("uluslararasi", r"soykirim|insanliga-karsi|savas-suclari|uluslararasi-ceza|suclularin-iadesi|yurtdisinda|"
                     r"yabancinin|gocmen-kacakciligi|insan-ticareti", False, None),
    ("cinsel", r"cinsel|mustehcen|fuhus|fuhsa|hayasizca|cocuk-pornografisi|ncmec|crc-cps|genital-muayene|resit-olmayan", False, None),
    ("uyusturucu", r"uyusturucu|esrar|kenevir", False, None),
    ("bilisim", r"bilisim|internet|sosyal-medya|yasadisi-bahis|unutulma-hakki|erisimin-engellenmesi", False, None),
    ("devlet", r"devlet|casusluk|darbe|anayasayi-ihlal|orgut|propaganda|terorizm|silahli-isyan|cumhurbaskanina|"
               r"bayrak|turk-milletini|halki-kin|halki-kanunlara|halki-askerlikten|suc-islemeye-tahrik|sucu-ve-sucluyu-ovme|"
               r"2911|savas-zamaninda|savasta|seferberlik|askeri|askerleri|yabanci-devlet|yabanci-hizmetine|dusman|"
               r"ataturk|nefret|halk-arasinda-korku|suc-icin-anlasma|temel-milli|yasaklanan-bilgi|gizli-kalmasi-gereken|"
               r"kita-sahanligi|ulasim-araclarinin|molotof|tehlikeli-madde|spor-alanlarinda", True, None),
    ("kamu_idaresi", r"zimmet|irtikap|rusvet|gorevi-kotuye|ihaleye-fesat|edimin-ifasina|nufuz-ticareti|iftira|suc-uydurma|"
                     r"yalanci-sahitlik|yalan-yere-yemin|sucu-bildirmeme|bilgi-vermeme|suc-ustlenme|delil|hukumlu|tutuklu|"
                     r"firar|cezaevine|infaz-kurumuna|tutukevine|muhafiz|yediemin|muhur-bozma|sorusturma-isleminin|"
                     r"adil-yargilamayi|yargi-gorevi|gorevi-yaptirmamak|kamu-gorevi|kamu-gorevlisinin|memuriyetin|"
                     r"haksiz-mal-edinme|zor-kullanma|gercege-aykiri|resmen-teslim|kamu-gorevine-ait|ozel-isaret|"
                     r"din-hizmetlerini", True, None),
    ("ekonomik", r"kacakcilig|kacak-sigara|akaryakit|vergi|sahte-fatura|sahte-belge|marka|6136|ruhsatsiz-silah|bicak|"
                 r"karsiliksiz-cek|fikri|haksiz-rekabet|ticari-sir|bankacilik|kara-para|aklanmasi|fiyatlari-etkileme|"
                 r"mal-ve-hizmet|kamuya-gerekli|hayvan-oldurme|defter-kayit", True, None),
    ("kamu_guveni", r"sahtecilik|resmi-belge|ozel-belge|evrak|parada|muhur|damga|genel-guvenlig|trafik-guvenligini|"
                    r"cevrenin|gurultu|imar-kirliligi|zehirli|saglik-icin|gida|bulasici|orman-yangini|radyasyon|atom|"
                    r"insaat|isaret-ve-engel|hayvanin|usulsuz-olu", True, None),
    ("malvarligi", r"hirsizlik|yagma|gasp|dolandiricil|guveni-kotuye|mala-zarar|karsiliksiz-yararlanma|suc-esyasinin|"
                   r"bedelsiz-sene|kredi-karti|aciga-atilan|tefecilik|iflas|sirket-veya-kooperatif|kaybolmus|hakki-olmayan-yere|"
                   r"kisilerin-mallari|ibadethane", True, None),
    ("hayat_vucut", r"oldurme|olume-neden|yaralama|eziyet|iskence|intihar|organ|deney|cocuk-dusurtme|kurtaj|kisirlastirma|"
                    r"terk-sucu|yardim-ve-bildirim|kotu-muamele|akil-hastasi|hekim|taksirli-suc", True, None),
    ("hayat_vucut", r"taksirle-olume|taksirle-oldurme|taksirle-yaralama", False, None),
    ("hurriyet", r"tehdit|santaj|cebir|hurriyetinden|israrli-takip|dokunulmazlig|is-ve-calisma|hakaret|ozel-hayat|"
                 r"haberlesme|kisisel-veri|konusmalarin|goruntulerin|huzur-ve-sukun|inanc|siyasi-haklar|sendikal|"
                 r"dilekce-hakki|egitim-ve-ogretim|kamu-hizmetlerinden|haksiz-arama|hak-kullanimini|hatirasina|"
                 r"birden-cok-evlilik|soybagini|aile-hukukundan|cocugun-kacirilmasi|dilencilik", True, None),

    # 4. İnfaz
    ("infaz", r"infaz|denetimli-serbestlik|acik-cezaevi|kosullu-saliverilme|sartli-tahliye|mahsup|adli-sicil|"
              r"memnu-haklar|umut-hakki|kamuya-yararli-iste", False, {"ceza-hukuku", "diger"}),

    # 5. Ceza muhakemesi
    ("muhakeme", r"cmk|sorusturma|kovusturma|iddianame|supheli|sanik|savcilik|mutalaa|son-savunma|ceza-davasi|"
                 r"ceza-istinaf|durusma|gorevsizlik|gerekceli-karar|kesinlesmis|tevsii-tahkikat|ceza-verilmesine", False, None),
    ("muhakeme", r"delil|tanik|bilirkisi|musteki|magdur|katilan|kamu-davasi|tutuklama|tahliye|gozalti|yakalama|"
                 r"adli-kontrol|imza-atma|ev-hapsi|kelepce|yurtdisina-cikis|guvence|arama|elkoyma|dinlen|iletisimin|"
                 r"takip|gizli-sorusturmaci|kontrollu-teslimat|ifade|sorgu|teshis|zorla-getirme|istinaf|temyiz|"
                 r"yargitay|itiraz|kanun-yararina|yargilamanin-yenilenmesi|uyarlama|uzlas|seri-muhakeme|"
                 r"seri-yargilama|basit-yargilama|hagb|hukmun-aciklanmasinin|beraat|karar|mahkeme|hakim|savunma|"
                 r"tebligname|segbis|kyok|takipsizlik|suphe|maddi-gercek|gozlem-altina|davasiz-yargilama|"
                 r"davanin|ses-|seminer", False, {"ceza-hukuku"}),

    # 6. Ceza genel hükümler
    ("ceza_genel", r"kanunilik|kiyas|taksir|kast|hata-yanilma|mesru|hakkin-kullanilmasi|rizasi|haksiz-tahrik|"
                   r"etkin-pismanlik|takdiri-indirim|temel-cezanin|cezai-ehliyet|akil-hastaligi|sagir|gecici-nedenler|"
                   r"ceza-sorumlulugu|cezasizlik|tekerrur|onodeme|zamanasimi|af-|musadere|guvenlik-tedbiri|hapis-cezasi|"
                   r"para-cezasi|ertelenmesi|ceza-indirimi|ictima|tck", False, {"ceza-hukuku", "diger"}),
    # Hiçbir suç grubuna uymayan suç yazıları
    ("ceza_ozel_diger", r".", True, {"ceza-hukuku"}),

    # 7. Özel hukuk, usul ve kamu hukuku
    ("aile", r"bosanma|nafaka|velayet|evlilig|ziynet|dugun-takilari|soybagi|nesebin|babalik|katilma|katki-payi|"
             r"deger-artis|aile-mahkemesi|aile-konutu|esit-kusur|zina|aldatma|siddetli-gecimsizlik|mal-paylasimi|"
             r"vesayet|vasi-atanmasi|isim-degistirme|soyadi", False, None),
    ("miras", r"miras|vasiyet|tereke|tenkis|sakli-pay|muvazaa|veraset|olunceye-kadar-bakma|iskat|denklestirme", False, None),
    ("anayasa", r"anayasa|aihm|aihs|bireysel-basvuru|khk|adil-yargilanma|ifade-ozgurlugu|aile-hayatina|makul-surede|"
                r"hakkinin-ihlali|isikirik|protokol", False, None),
    ("is", r"kidem|fazla-calisma|mesai|mobbing|is-kazasi|meslek-hastaligi|is-mahkemesi|hizmet-tespiti|kisa-calisma|kalp-krizi", False, None),
    ("icra", r"(^|-)iik-|icra|iflas|haciz|ihalenin-feshi|tasarrufun-iptali|itirazin-iptali|itirazin-kaldirilmasi|odeme-emri", False, None),
    ("esya", r"tapu|ecrimisil|el-atma|sufa|onalim|izale|ortakligin-giderilmesi|kat-karsiligi|arsa-payi|gecit|intifa|"
             r"oturma-hakki|ust-hakki|irtifak|elbirligi|mulkiyet|muhdesat|kamulastirma|tasinmaz|gayrimenkul|harici-satis", False, None),
    ("borclar", r"tazminat|trafik-kazasi|malpraktis|ayipli|kira|menfi-tespit|cek|noter|satis-vaadi|iyiniyet|zamanasimi-defi", False, None),
    ("idare", r"idare|idari|danistay|vergi|imar|memur|disiplin|yurutmenin-durdurulmasi|tam-yargi|gumruk|ihbarname|usulsuzluk", False, None),
    ("ticaret", r"anonim-sirket|asliye-ticaret|ticaret|sirket", False, None),
    ("avukatlik", r"avukat|meslek-kurallari", False, None),
    ("medeni_usul", r"hmk|istinaf|temyiz|yargitay|bolge-adliye|asliye-hukuk|sulh-hukuk|tuketici-mahkemesi|usuli-kazanilmis|"
                    r"ara-karar|nihai-karar|arabuluculuk|tensip|mahkeme", False, None),
]

KATEGORI_VARSAYILAN = {
    "ceza-hukuku": "ceza_genel",
    "medeni-hukuk": "medeni_usul",
    "gayrimenkul-hukuku": "esya",
    "tazminat-hukuku": "borclar",
    "borclar-hukuku": "borclar",
    "vergi-ve-idare-hukuku": "idare",
    "bireysel-basvuru": "anayasa",
    "arabuluculuk": "medeni_usul",
    "mevzuat": "mevzuat",
}

_DERLENMIS = [(alan, re.compile(desen), suc, kats) for alan, desen, suc, kats in KURALLAR]


def siniflandir(slug: str, site_kategori: str) -> tuple[str, str]:
    """(alan_kodu, gerekçe) döner."""
    if slug in ELLE_ATAMA:
        return ELLE_ATAMA[slug], "elle"
    if site_kategori == "mevzuat":
        return "mevzuat", "kategori"
    suc_yazisi = bool(SUC.search(slug))
    for alan, desen, sadece_suc, kats in _DERLENMIS:
        if sadece_suc and not suc_yazisi:
            continue
        if kats is not None and site_kategori not in kats:
            continue
        if desen.search(slug):
            return alan, f"kural:{desen.pattern[:40]}"
    return KATEGORI_VARSAYILAN.get(site_kategori, "diger"), "varsayilan"
