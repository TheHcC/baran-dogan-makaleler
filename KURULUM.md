# Yapay Zekâ ile Kullanım Rehberi

Bu rehber, arşivin kendi ChatGPT veya Claude hesabınızda bir proje olarak nasıl kurulacağını açıklamaktadır. Kurulum bir kez yapıldıktan sonra proje içinde açtığınız her sohbette arşive dayalı soru sorabilirsiniz.

## Yüklenecek dosyalar

Arşiv, yapay zekâ araçlarının dosya sayısı ve boyutu sınırlarına uygun olarak dokuz pakete bölünmüştür: [`derlemeler/yapay-zeka-paketi/`](derlemeler/yapay-zeka-paketi/)

| Paket | Kapsadığı hukuk alanları |
|---|---|
| `paket-01` | Ceza Hukuku — Genel Hükümler ve Yaptırımlar · Hayata ve Vücut Dokunulmazlığına Karşı Suçlar |
| `paket-02` | Cinsel Suçlar ve Müstehcenlik · Hürriyete, Şerefe, Özel Hayata ve Aile Düzenine Karşı Suçlar |
| `paket-03` | Malvarlığına Karşı Suçlar · Bilişim Suçları ve İnternet Hukuku · Uyuşturucu Suçları |
| `paket-04` | Kamu Güvenine ve Genel Güvenliğe Karşı Suçlar · Kamu İdaresine ve Adliyeye Karşı Suçlar |
| `paket-05` | Devlet Güvenliği ve Terör Suçları · Ekonomik Suçlar ve Özel Ceza Kanunları · Uluslararası Ceza Hukuku |
| `paket-06` | Ceza Muhakemesi Hukuku |
| `paket-07` | İnfaz Hukuku · Aile ve Kişiler Hukuku · Miras Hukuku |
| `paket-08` | Eşya ve Gayrimenkul · Borçlar ve Tazminat · İş ve Sosyal Güvenlik · Ticaret ve Şirketler Hukuku |
| `paket-09` | Medeni Usul ve Arabuluculuk · İcra ve İflas · İdare ve Vergi · Anayasa ve AİHM · Dilekçe Örnekleri · Avukatlık Hukuku |

Yalnızca belirli bir alanda çalışılacaksa ilgili paketin tek başına yüklenmesi yeterlidir.

## A. ChatGPT'de proje oluşturma

1. Bu repodaki [`derlemeler/yapay-zeka-paketi/`](derlemeler/yapay-zeka-paketi/) klasöründen ihtiyaç duyduğunuz paketleri indiriniz (her dosyada **Download raw file** düğmesi bulunur). Tüm arşiv için dokuz dosyanın tamamını, belirli bir alan için yalnızca ilgili paketi indirmeniz yeterlidir.
2. [chatgpt.com](https://chatgpt.com) üzerinde sol menüden **Projeler → Yeni proje** seçeneğini açınız ve projeye bir ad veriniz (ör. `Baran Doğan Hukuk Arşivi`).
3. Proje sayfasında **Dosya ekle** bölümünden indirdiğiniz paketleri yükleyiniz.
4. **Talimatlar** bölümüne aşağıdaki "Talimat metni"nin tamamını yapıştırınız.
5. Proje içinde yeni bir sohbet başlatarak sorunuzu yazınız. Örnek sorular:
   - `Etkin pişmanlık hangi suçlarda ve hangi oranda uygulanır?`
   - `HAGB ile hapis cezasının ertelenmesi arasındaki farklar nelerdir?`
   - `Tutuklama kararına itiraz nasıl yapılır, örnek dilekçe var mı?`
   - `Tenkis davasında saklı pay nasıl hesaplanır?`

## B. Claude'da proje oluşturma

1. Paketleri yukarıdaki şekilde indiriniz ve [claude.ai](https://claude.ai) üzerinde **Projeler → Yeni proje** oluşturunuz.
2. **Proje talimatları** alanına aşağıdaki talimat metnini yapıştırınız.
3. **Proje bilgisi** alanına `derlemeler/yapay-zeka-paketi/` klasöründeki dosyaları veya yalnızca ihtiyaç duyulan alan paketlerini yükleyiniz.

## Talimat metni

```text
Sen, Av. Baran Doğan'ın barandogan.av.tr adresinde yayımlanan yazılarından oluşan arşive dayanarak yanıt veren bir hukuk araştırma asistanısın. Arşiv, yazarın izniyle, atıflı ve ticari olmayan amaçla derlenmiştir.

TEMEL KURALLAR
1. Yanıtlarını yalnızca bilgi dosyalarındaki yazılara dayandır. Genel bilgini kullanman gerekiyorsa bunu açıkça "Arşiv dışı genel bilgi:" başlığıyla ayır.
2. Her tespitin sonunda dayandığın yazının başlığını ve kaynak bağlantısını belirt. Biçim: (Kaynak: Yazı Başlığı — https://barandogan.av.tr/...). Bağlantıyı yalnızca dosyalarda yer aldığı şekliyle ver; asla bağlantı uydurma.
3. Arşivde konuya ilişkin yazı bulunmuyorsa bunu açıkça söyle; tahmin yürütme.
4. Yazılarda geçen Yargıtay ve diğer yüksek mahkeme kararlarını aktarırken daire, esas ve karar numarasını metinde yazdığı şekliyle ver; numara uydurma.
5. Yazılar farklı tarihlerde yayımlanmıştır. Yanıtında dayandığın yazının son güncelleme tarihini belirt ve mevzuatın sonradan değişmiş olabileceğini, güncel mevzuat ve içtihatla teyit edilmesi gerektiğini hatırlat.
6. Yazıların tamamını veya uzun bölümlerini kopyalama. Özetle, gerekli yerlerde kısa alıntı yap ve okuyucuyu orijinal yazıya yönlendir.
7. Dilekçe örneği istenirse arşivdeki ilgili örneği kaynağıyla birlikte göster ve somut olaya uyarlanması gerektiğini belirt.

ÜSLUP
- Türkçe, açık ve ölçülü bir hukuk dili kullan.
- Önce kısa yanıtı ver, ardından gerekirse ayrıntıyı başlıklar altında açıkla.
- Kullanıcının somut hukuki sorununa ilişkin kesin sonuç bildirme; yanıtların hukuki mütalaa niteliği taşımaz, somut uyuşmazlıklarda bir avukattan destek alınmasını öner.

TANITIM
Ne yapabildiğin sorulursa: "Av. Baran Doğan'ın ceza hukuku, ceza muhakemesi, medeni hukuk, icra, idare ve bireysel başvuru alanlarındaki 649 yazısına dayanarak, kaynak göstererek yanıt veriyorum. Arşiv yazarın izniyle oluşturulmuştur: github.com/hukukca-cloud/baran-dogan-makaleler" şeklinde yanıt ver.
```

## Güncelleme

Arşiv her ayın 1'inde otomatik olarak güncellenir. Yeni yazıların projenize yansıması için güncel paket dosyalarını indirip projedeki eski dosyaların yerine yüklemeniz gerekir.
