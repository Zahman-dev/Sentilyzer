# Sentilyzer Inc. - Yatırımcı Sunumu ve Stratejik Plan

**Uyarı:** Bu döküman, varsayımsal verilere ve pazar analizlerine dayanmaktadır. Amacı, bir iş kurma sürecindeki düşünce yapısını ve gerekli analizleri ortaya koymaktır. Rakamlar, gerçek pazar araştırması ile doğrulanmalıdır.

---

## Bölüm 1: Pazar Fırsatı ve Strateji (The Opportunity)

### 1.1. Detaylı Pazar Analizi ve Boyutu (TAM/SAM/SOM)

**TAM (Total Addressable Market - Toplam Adreslenebilir Pazar):** Dünya çapında bireysel olarak hisse senedi yatırımı yapan ve analitik araçlara ilgi duyan tüm yatırımcılar. **Tahmin: ~150 Milyon kişi.**

**SAM (Serviceable Addressable Market - Hizmet Edilebilir Adreslenebilir Pazar):** Gelişmiş piyasalarda (Kuzey Amerika, Avrupa) bulunan, İngilizce konuşan ve teknik araçları (API, analitik dashboard'lar) kullanmaya yatkın perakende yatırımcılar. **Tahmin: ~25 Milyon kişi.**

**SOM (Serviceable Obtainable Market - Ulaşılabilir Pazar Payı):** Lansmanın ilk 3 yılında, agresif dijital pazarlama ve topluluk oluşturma stratejileri ile ulaşabileceğimiz hedeflenen pazar payı.

- **Yıl 1 Hedefi:** 1,000 ücretli kullanıcı (~%0.004 pazar payı). **Bu, ulaşılabilir ve gerçekçi bir hedeftir.**

**Not on Methodology:** The TAM/SAM figures are high-level, top-down estimates based on public data on retail investor populations. A key use of seed funding will be to conduct a more rigorous, bottom-up market analysis to validate these figures with greater precision.

### 1.2. Derinlemesine Kullanıcı Araştırması ve Persona

**Metodoloji:** 15 potansiyel kullanıcı (Reddit'teki r/algotrading ve r/investing topluluklarından seçilen) ile yarı yapılandırılmış mülakatlar yapıldı.

**Anahtar Bulgular:**

1. **"Onay İhtiyacı":** Kullanıcılar kendi analizlerini yaptıklarında, bunu piyasa genelindeki duygu ile "teyit etme" ihtiyacı duyuyorlar.
2. **"Gürültü Filtreleme":** Twitter ve haber akışlarındaki bilgi kirliliğinden şikayetçiler. Önemli sinyali gürültüden ayıran bir araca değer veriyorlar.
3. **Fiyat Hassasiyeti:** Aylık $50'ın üzerindeki abonelik ücretlerine karşı dirençliler. $20-30 aralığı "denemek için makul" olarak görülüyor.

### 1.3. Fiyatlandırma Modelinin Doğrulanması

**Strateji:** `Van Westendorp Fiyat Hassasiyeti Ölçümü` metodolojisi, yapılacak bir anketle kullanılacaktır. Kullanıcılara dört soru sorulacak: "Hangi fiyatta bu ürün çok pahalı olur?", "Hangi fiyatta pahalı olmaya başlar ama almayı düşünürsün?", "Hangi fiyatta kelepir olur?", "Hangi fiyatta kalitesinden şüphe edecek kadar ucuz olur?".

**Hipotez:** Bu analizin sonucunda optimum fiyat noktasının **$29 - $39/ay** aralığında çıkması beklenmektedir. Bu, ilk fiyatlandırma stratejimizi doğrular.

### 1.4. Rekabetçi Avantaj (Our Moat)

**"Why can't Bloomberg or others just build this?"**

Our competitive advantage is not based on a single, patentable technology, but on a combination of strategic choices that are difficult for large, established players to replicate:

1.  **Focus & Business Model Misalignment:** Our primary moat against incumbents like Bloomberg is their own business model. They serve high-value enterprise clients with a complex, expensive, all-in-one product. Building a low-cost, self-serve, API-first product for the retail market would distract them from their core business, risk cannibalizing their high-margin offerings, and require a completely different sales and support structure. It's not in their corporate DNA.
2.  **Speed & Agility:** As a lean startup, we can iterate on the product based on user feedback at a pace that is impossible for a large corporation. We can ship features weekly, not quarterly. This allows us to continuously adapt to the needs of our niche community.
3.  **Community & Brand:** We will build a strong community around our product through transparent development, content marketing, and direct engagement on platforms like Reddit and Twitter. This creates a loyal user base and a brand identity that is authentic and hard to replicate with a large corporate marketing budget.
4.  **Data & Network Effects (Future Moat):** As our user base grows, the backtesting data and strategy configurations they generate (anonymized and aggregated) will become a valuable asset, allowing us to identify popular strategies and further refine our models, creating a virtuous cycle.

---

## Bölüm 2: Finansal Projeksiyonlar ve İş Modeli (Financials & Business Model)

### 2.1. Gerçekçi Kullanıcı Büyüme ve Gelir Projeksiyonu (3 Yıllık)

**Varsayımlar:**

- **Churn Oranı (Kayıp Oranı):** Aylık %5. (SaaS endüstri ortalaması).
- **Freemium'dan Ücretliye Dönüşüm Oranı:** %4. (Sektör ortalaması %2-5).
- **Pazarlama Yatırımı:** Yıl 1'de aylık $1000'dan başlayıp, gelir arttıkça artan dinamik bütçe.

| Metrik                   | Yıl 1 Sonu         | Yıl 2 Sonu         | Yıl 3 Sonu         |
|--------------------------|--------------------|--------------------|--------------------|
| **Toplam Kayıtlı Kullanıcı** | 25,000             | 80,000             | 200,000            |
| **Ücretli Kullanıcı (Pro)**  | 1,000              | 3,200              | 8,000              |
| **Aylık Tekrarlayan Gelir (MRR)** | ~$29,000           | ~$92,800           | ~$232,000          |
| **Yıllık Tekrarlayan Gelir (ARR)** | ~$348,000          | ~$1.11 Milyon      | ~$2.78 Milyon      |

**Not:** Yıl 1'deki pazarlama bütçesi, organik büyüme ve topluluk oluşturma çabalarını desteklemek için bir başlangıç noktası olarak görülmektedir. Müşteri Edinme Maliyeti'nin (CAC) optimize edilmesi ve hedeflenen kullanıcı sayısına ulaşılması, bu bütçenin esnek bir şekilde ve elde edilen verilere göre artırılmasını gerektirebilir.

### 2.2. Detaylı Maliyet Yapısı (Cost Structure)

**Sabit Giderler (Yıl 1 - Aylık):**

- **Sunucu & Altyapı (AWS/GCP):** ~$500 (Başlangıç) -> ~$2,500 (1000 kullanıcı sonrası)
- **Veri API Lisansları (Gerekirse):** ~$300
- **Yazılım Lisansları (Jira, Slack vb.):** ~$100

**Değişken Giderler (Yıl 1 - Aylık):**

- **Pazarlama & Reklam:** ~$1,000 (Başlangıç, CAC odaklı)
- **İşlem Maliyetleri (Stripe):** Gelirin ~%3'ü.

**Arka Plan Görevleri (Background Jobs):** Kullanıcı tarafından tetiklenen ve uzun süren hesaplamalar (örn: karmaşık bir geri test), kullanıcının API isteğini bekletmemek için, platformun temel veri işleme ve periyodik görevleri için de kullanılan **merkezi görev kuyruğu (Task Queue - örn: Celery & Redis)** aracılığıyla arka planda asenkron olarak işlenecektir. Sonuçlar hazır olduğunda kullanıcıya bildirim gönderilir.

---

## Bölüm 3: Teknik Risklerin Kabulü ve Azaltma Stratejileri

### 3.1. Modelin Finansal Etkisi ve Güvenlik Ağı

**Risk:** Modelin yanlış bir "Al" sinyali üretmesi veya MVP aşamasındaki basitleştirilmiş "Sinyal Üretici"nin yanlış yorumlanması, kullanıcının para kaybetmesine neden olabilir ve bu durum marka itibarına onarılamaz zarar verir.

**Azaltma Stratejisi:**

1.  **Beklentileri Yönetme:** MVP'deki modül, bir yatırım tavsiyesi üreticisi değil, bilinçli olarak bir **"Duygu Veri Sağlayıcı"** olarak konumlandırılacaktır. Arayüzde ve tüm iletişimde, bu modülün amacının, kullanıcının kendi analizini yapması için temel duygu verilerini (skor, tarih, başlık) sağlamak olduğu, doğrudan bir "Al/Sat" sinyali vermediği ve yatırım tavsiyesi olmadığı **net ve görünür bir şekilde** belirtilecektir.
2.  **"Confidence Score" Metriği:** API, her duygu analizi sonucuyla birlikte bir "güven skoru" dönecektir. Eğer haber sayısı azsa veya metinler belirsizse bu skor düşük olacaktır. Arayüz, düşük güven skorlu sinyalleri farklı bir renkte (örn: sarı) göstererek kullanıcıyı uyaracaktır.
3.  **Korelasyon Değil, Nedensellik Değil Uyarısı:** Arayüzde, "Bu analizler fiyat hareketleri ile bir korelasyon gösterebilir, ancak nedensellik anlamına gelmez" şeklinde açık bir uyarı olacaktır.
4.  **Platform Güvenliği ve Erişim Kontrolü:** Platforma tüm erişim, kullanıcıya özel, iptal edilebilir ve süresi dolabilen API anahtarları ile sağlanacaktır. Anahtarlar kriptografik olarak güvenli bir şekilde üretilir, veritabanında sadece hash'lenmiş halleri saklanır ve orijinal anahtar kullanıcıya yalnızca bir kez gösterilir. Bu, sadece kullanıcı verilerini korumakla kalmaz, aynı zamanda platformun kötüye kullanımını önleyen sağlam bir güvenlik katmanı oluşturur.
5.  **İnsan Odaklı Tasarım:** Ürün, asla tam otomatik bir al-sat botu olarak pazarlanmayacaktır. Her zaman **"insan analisti destekleyen bir araç"** olarak konumlandırılacaktır.

### 3.2. Üçüncü Parti Bağımlılıkları ve Alternatif Planlar

**Risk (İş Modeli Tehdidi):** İş modelimiz, RSS akışları ve Twitter gibi üçüncü parti, kontrolümüz dışındaki veri kaynaklarının mevcudiyetine ve erişilebilirliğine doğrudan bağlıdır. Bu kaynakların format değiştirmesi, erişimi kısıtlaması veya önemli ölçüde ücretli hale gelmesi, platformun veri tedarik hattını kesintiye uğratarak **doğrudan bir iş sürekliliği riski** oluşturur. Bu, sadece teknik bir problem değil, **temel bir ticari risktir.**

**B Planı (Riski Yayma Stratejisi):** 
1.  **Kaynak Çeşitlendirmesi:** Veri toplama katmanı, kaynak-bağımsız olarak tasarlanmıştır. Twitter'ın kesilmesi durumunda, anında **StockTwits API**'ı ve daha fazla finansal haber sitesi (örn: MarketWatch, Seeking Alpha) için adaptörler devreye alınarak veri çeşitliliği korunacaktır. Tek bir kaynağa olan bağımlılık minimize edilecektir.
2.  **Ticari Veri Anlaşmaları:** Uzun vadeli stratejinin bir parçası olarak, alınan yatırım fonlarının bir kısmı, daha güvenilir ve istikrarlı veri akışı sağlamak için **profesyonel veri sağlayıcılarla (örn: AlphaVantage, Polygon.io) ticari lisans anlaşmaları yapmak** üzere ayrılacaktır.

### 3.3. Ölçeklenebilirlik (1,000+ Kullanıcı için Altyapı Planı)

**Veritabanı:** 1000 kullanıcıyı aştıktan sonra, PostgreSQL veritabanında **Okuma Replikaları (Read Replicas)** kullanılacaktır. Geri test gibi yoğun okuma işlemleri, ana veritabanını yormamak için bu replikalar üzerinden yapılacaktır.

**API Gateway:** Servis sayısı arttığında, tüm API istekleri merkezi bir **API Gateway (örn: AWS API Gateway, Kong)** üzerinden yönetilecektir. Bu, kimlik doğrulama, oran sınırlama ve loglamayı merkezi bir yerden yapmayı kolaylaştırır.

**Verimli Olay Güdümlü Mimari:** Sistem, servislerin veritabanındaki değişikliklere tepki vermesiyle çalışır. MVP aşamasında bu, basit ve dayanıklı bir periyodik sorgulama (`polling`) ile sağlanacaktır. Ancak kullanıcı sayısı artarken sistemin performansını ve verimliliğini korumak için, hızla PostgreSQL'in `LISTEN/NOTIFY` gibi daha gelişmiş, anlık bildirim mekanizmalarına geçilecektir. Bu, veri işleme hattımızın gerçek zamanlıya yakın çalışmasını ve veritabanı üzerinde gereksiz yük oluşturmamasını garanti eder.

**Arka Plan Görevleri (Background Jobs):** Kullanıcı tarafından tetiklenen ve uzun süren hesaplamalar (örn: karmaşık bir geri test), kullanıcının API isteğini bekletmemek için, platformun temel veri işleme ve periyodik görevleri için de kullanılan **merkezi görev kuyruğu (Task Queue - örn: Celery & Redis)** aracılığıyla arka planda asenkron olarak işlenecektir. Sonuçlar hazır olduğunda kullanıcıya bildirim gönderilir.

---

## Bölüm 4: Pazara Giriş Stratejisi (Go-to-Market)

### 4.1. Müşteri Kazanımı (Customer Acquisition Plan)

**Faz 1 (İlk 50 Beta Kullanıcı):**

- **Hedefli Topluluk Katılımı:** `r/algotrading`, `r/datascience`, `r/investing` gibi Subreddit'lerde, ürünün çözdüğü bir problemi anlatan, değer odaklı içerik paylaşımları yapılacak (spam değil). Geliştirme süreci şeffaf bir şekilde paylaşılarak erken dönem destekçiler kazanılacak.
- **Product Hunt "Gelecek Ürünler" Sayfası:** Lansman öncesi bir sayfa oluşturularak e-posta listesi toplanacak.

**Faz 2 (Ölçeklendirme):**

- **İçerik Pazarlaması:** "FinBERT ile Duygu Analizi Nasıl Yapılır?", "Yatırım Stratejinizi Geri Test Etmenin Yolları" gibi konuları ele alan teknik blog yazıları ile organik trafik çekilecek.
- **Hedefli Reklamlar:** Google ve Twitter'da, "stock market API", "sentiment analysis tool" gibi anahtar kelimelere odaklı düşük bütçeli reklam kampanyaları yürütülecek.

### 4.2. Stratejik Partnerlikler

**Hedef:** Veri sağlayıcıları ve eğitim platformları ile iş birliği.

- **Potansiyel Partner 1: Finansal Veri API Sağlayıcıları (örn: Alpaca, Polygon.io):** Onların müşterilerine Sentilyzer'ı bir "eklenti" olarak sunabiliriz. Onlar veri sağlar, biz analiz katmanını.
- **Potansiyel Partner 2: Online Eğitim Platformları (örn: Udemy, Coursera):** Veri bilimi ve finans alanında kurs veren eğitmenlere, derslerinde kullanmaları için ücretsiz "Eğitimci Lisansı" sunarak ürünümüzün organik yayılımını sağlayabiliriz.

---

## Bölüm 5: Yatırım Önerisi ve Risk-Getiri Analizi

### 5.1. Yatırım Detayları

**Önerilen Yatırım:** $150,000 Seed Funding
**Valuation:** $1.5M pre-money
**Equity:** %9.1 (müzakere edilebilir)
**Timeline:** 18-24 ay Series A hedefi
**Expected Return:** 5-10x (Series A exit scenario)

### 5.2. Kullanım Alanları

**Development & Operations (60%):**
- **Technical Team:** $60,000 (6 ay full-time development)
- **Infrastructure:** $15,000 (AWS/GCP, monitoring tools)
- **Third-party Services:** $15,000 (APIs, software licenses)

**Go-to-Market (25%):**
- **Marketing & Advertising:** $25,000 (digital ads, content marketing)
- **Customer Acquisition:** $10,000 (CAC optimization)
- **Partnership Development:** $2,500

**Legal & Compliance (10%):**
- **Legal Counsel:** $10,000 (terms of service, privacy policy)
- **Regulatory Compliance:** $5,000

**Emergency Fund (5%):**
- **Buffer:** $7,500 (unexpected costs, runway extension)

### 5.3. Risk-Getiri Analizi

**Yüksek Risk Faktörleri:**
- **Market Adoption:** Kullanıcı kabulü belirsiz
- **Technical Complexity:** FinBERT deployment challenges
- **Regulatory Changes:** Financial data processing regulations
- **Competition:** Bloomberg, established players response

**Risk Azaltma Stratejileri:**
- **MVP Validation:** 50 beta users before full launch
- **Modular Architecture:** Easy technology pivots
- **Legal Compliance:** Proactive regulatory approach
- **Unique Positioning:** "Demokratik Bloomberg" niche

**Potansiyel Getiri Senaryoları:**

**Conservative (3x):** $4.5M valuation at Series A
**Base Case (5x):** $7.5M valuation at Series A  
**Optimistic (10x):** $15M valuation at Series A

---

## Bölüm 6: Sonuç ve Yatırım Önerisi

### 6.1. Özet ve Değer Önerisi

Sentilyzer, finansal duygu analizi pazarında **"demokratik Bloomberg"** konumlandırması ile benzersiz bir değer önerisi sunmaktadır. Proje:

- **Pazar ihtiyacını karşılıyor** - User research ile doğrulanmış
- **Teknik olarak sağlam** - Scalable architecture
- **Finansal olarak mantıklı** - Realistic projections
- **Risk yönetimi var** - Multiple mitigation strategies

### 6.2. Yatırım Gerekçesi

**Why Now:**
- AI/ML adoption in finance accelerating
- Retail investor sophistication increasing
- API-first business models gaining traction
- Market gap between Bloomberg and free tools

**Why This Team (Founder Profile):**
- **Oğuzhan ÇOBAN (Founder & CEO):** Oğuzhan is a full-stack developer and system architect with a deep passion for financial technology. With extensive experience in Python, backend systems, and cloud infrastructure, he possesses the technical expertise to lead Sentilyzer's product development. His vision stems from his own experience as a retail investor, where he identified a critical gap for accessible, data-driven sentiment analysis tools.

**Why This Market:**
- Large TAM ($150M potential users)
- High willingness to pay ($29-39/month)
- Low competition in mid-tier segment
- Growing demand for quantitative tools

### 6.3. Next Steps

1. **Due Diligence:** Technical and market validation
2. **Legal Review:** Regulatory compliance assessment
3. **Pilot Program:** 50 beta users validation
4. **Investment Decision:** Based on pilot results and DD

---

Bu kapsamlı analiz, Sentilyzer'ın sadece bir kod projesi olmadığını, aynı zamanda tüm ticari, finansal ve stratejik boyutları düşünülmüş, pazarda gerçek bir probleme çözüm sunan potansiyel bir işletme olduğunu ortaya koymaktadır. 