# Sentilyzer - Teknik ve Operasyonel Master Plan

**Döküman Amacı:** Bu döküman, Sentilyzer platformunun geliştirme, dağıtım ve operasyon süreçlerini tüm boyutlarıyla tanımlayan tek ve merkezi referans kaynağıdır. Geliştirme ekibi için ana yol haritası görevi görür.

---

## Bölüm 1: Stratejik Çerçeve ve Yol Haritası

### 1.1. Proje Vizyonu ve Mimari Felsefesi

**Vizyon:** Finansal metin verilerini, işlenebilir stratejik içgörülere dönüştüren, ölçeklenebilir, bakımı kolay ve genişletilebilir bir platform yaratmak. Sistem, bir "veri fabrikası" gibi çalışmalıdır.

**Mimari Felsefesi:** Sistem, **Olay Güdümlü (Event-Driven)** ve **Servis Odaklı (Service-Oriented)** bir mimariye dayanır. Servisler birbirlerini doğrudan çağırmazlar; bunun yerine veritabanındaki durum değişikliklerine (olaylara) tepki verirler. Bu, sistemin esnekliğini, dayanıklılığını ve ölçeklenebilirliğini en üst düzeye çıkarır.

### 1.2. Proje Fazlandırması ve Kilometre Taşları

Proje, çevik (agile) bir yaklaşımla, her biri net çıktılara sahip üç ana fazda geliştirilecektir.

**Faz 1: Minimum Değerli Ürün (MVP) - (Hedef: İlk 4 Hafta)**
*   **Tanım:** Sistemin çekirdek veri işleme hattının (RSS -> Analiz -> API), tek bir temel strateji ile uçtan uca çalıştığı versiyon.
*   **Birincil Hedef:** FinBERT modelinin canlı ortamdaki performansını, maliyetini ve gecikme süresini (latency) test ederek en büyük teknik riski erkenden doğrulamak.
*   **Kilometre Taşları:**
    *   **Hafta 1:** Çekirdek altyapı (Veritabanı, servis iskeletleri, **asenkron görevler için Celery/Redis altyapısı**, `common` içinde merkezi Alembic yapılandırması).
    *   **Hafta 2:** Veri akışı (RSS'den veri toplama ve işleme için Celery görevlerinin oluşturulması).
    *   **Hafta 3:** Analiz ve sunum (Duygu Veri API'ı (`signals_api`) ve metin tabanlı dashboard).
    *   **Hafta 4:** Uçtan uca test, demo ve **geliştirici verimlilik script'lerinin (`local_rebuild.sh`, `seed_database.py`) tamamlanması.**

**Faz 2: Üretim Hazırlığı (Production Hardening) - (Hedef: MVP + 6 Hafta)**
*   **Amaç:** MVP'yi güvenli, izlenebilir, ölçeklenebilir ve güvenilir bir servis haline getirmek.
*   **Kilometre Taşları:**
    *   **Hafta 5-6:** Güvenlik (Kullanıcı tabanlı API anahtar yönetimi, sır yönetimi).
    *   **Hafta 7-8:** Operasyonel görünürlük (Merkezi loglama, metrik izleme).
    *   **Hafta 9-10:** CI/CD ve test otomasyonu (%70+ kod kapsamı).

**Faz 3: Yetenek Genişletme (Feature Expansion) - (Sürekli)**
*   **Amaç:** Ürüne değer katacak yeni özellikler eklemek (örn: Twitter entegrasyonu, gelişmiş stratejiler, model açıklanabilirliği).

---

## Bölüm 2: Detaylı Sistem Mimarisi ve Tasarım Kararları

### 2.1. Kavramsal Mimari Şeması

```
+---------------------------+
|      DIŞ DÜNYA (SOURCES)  |
| - RSS Feeds, Twitter API  |
+-------------|-------------+
              |
              ▼ (1. Veri Alımı)
+---------------------------+
|    SERVICE 1: DATA INGESTOR |
+-------------|-------------+
              |
              ▼ (2. OLAY: Yeni Ham Veri Eklendi)
+---------------------------+
|    VERİTABANI (PostgreSQL)|
+-------------|-------------+
              ▲
              | (3. OLAY: Yeni Ham Veri Bekleniyor)
              |
+-------------|-------------+
|    SERVICE 2: SENTIMENT PROC. |
+-------------|-------------+
              ▲
              | (4. OLAY: Analiz Sonucu Bekleniyor)
              |
+-------------|-------------+
|    SERVICE 3: SIGNALS API   |
+-------------|-------------+
              |
              ▼ (5. API Çağrısı)
+---------------------------+
|    SERVICE 4: DASHBOARD/UI |
+-------------|-------------+
```

### 2.2. Stratejik Tasarım Kararları ve Gerekçeleri

| Karar                               | Gerekçe                                                                                                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Servis Odaklı Mimari**            | **Bağımsız Ölçeklendirme:** Sadece yavaşlayan servisi (örn: `sentiment_processor`) güçlendiririz. **Teknoloji Özgürlüğü:** Bir servisi, diğerlerini etkilemeden farklı bir teknoloji ile yeniden yazabiliriz. **Hata İzolasyonu:** Bir servis çökerse, sistemin geri kalanı çalışmaya devam eder. |
| **Asenkron Görev Kuyruğu ile İletişim** | **Dayanıklılık:** İşleyici servis (`sentiment_processor`) kapalıyken bile işlenmesi gereken görevler kaybolmaz, kuyrukta bekler. **Geri Basınç (Backpressure):** Yoğun veri akışında sistem tıkanmaz, `worker`'lar görevleri kendi hızında tüketir. **Sorumlulukların Ayrılması:** Görev üreten servis (`data_ingestor`) ile görevi tüketen servis (`sentiment_processor`) birbirinden tamamen habersizdir. |
| **API ve Arayüzün Ayrılması**        | **Kanal Çeşitliliği:** Aynı API'ı web, mobil, B2B gibi farklı kanallar için kullanabiliriz. **Paralel Geliştirme:** Backend ve frontend ekipleri birbirini engellemeden çalışabilir. |
| **Merkezi Ortak Kütüphane (`common`)** | **Kod Tekrarını Önleme:** Veritabanı modelleri, bağlantı mantığı (`session`), Pydantic şemaları gibi birden fazla servis tarafından kullanılacak kodları tek bir yerde toplayarak bakım maliyetini düşürmek ve tutarlılığı garanti altına almak. |
| **Merkezi Alembic Yapılandırması (`common` içinde)** | **Geliştirici Deneyimi ve Tutarlılık:** `alembic.ini` ve ilgili script'lerin `services/common` klasöründe merkezi olarak yönetilmesi, tüm veritabanı şemasının tek bir yerden, versiyon kontrollü bir şekilde yönetilmesini sağlar. Bu, migrasyon komutlarının `docker-compose` içinden veya yerel ortamdan tutarlı ve basit bir şekilde çalıştırılmasını garanti eder ve her servis için ayrı migrasyon yapılandırmalarının karmaşıklığını önler. |

### 2.3. Platform Teknolojileri: Seçimler ve Alternatifler

| Kategori      | Seçilen Teknoloji | Gerekçe                                                                                                     | Değerlendirilen Alternatif(ler)          | Neden Seçilmedi?                                                                                             |
|---------------|-------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **API Framework** | FastAPI           | Otomatik veri doğrulama (Pydantic), yüksek performans (async), modern ve kolay öğrenilebilir API. **Strateji:** FastAPI'nin otomatik interaktif API dokümantasyonu (`/docs`, `/redoc`) özelliği, geliştirme sürecinin başından itibaren aktif olarak kullanılacak ve birincil API referansı olarak kabul edilecektir. | **Flask, Django REST Framework (DRF)**   | Flask: Veri doğrulama ve dökümantasyon için ek kütüphaneler gerektirir. DRF: Daha büyük ve karmaşık projeler için daha uygun, bu proje için fazla ağır (overkill). |
| **Veritabanı**    | PostgreSQL        | Güçlü ilişkisel yapı, transaction güvenliği (ACID), zengin veri tipleri (JSONB), olgun ve kararlı.    | **MongoDB**                              | Verilerimiz yüksek oranda yapısal ve ilişkiseldir. MongoDB'nin esnek şema yapısı bu projede bir avantajdan çok, veri tutarsızlığı riski yaratabilir. |
| **Asenkron Görevler / Kuyruk** | Celery & Redis | Periyodik veri toplama, yoğun veri işleme gibi uzun süren ve asenkron çalışması gereken görevleri yönetmek için ölçeklenebilir ve dayanıklı bir çözüm sunar. Yatay ölçeklendirmeye olanak tanır ve sistemin genelinde tek bir hata noktası oluşmasını engeller. | **`APScheduler` (servis-içi)** | Servis içinde çalıştığı için yatay ölçeklendirmeyi imkansız kılar, bu da onu büyük ölçekli sistemler için bir darboğaz (bottleneck) ve tek bir hata noktası (SPOF) haline getirir. |
| **Veritabanı Migrasyonu** | Alembic | Veritabanı şemasını kod olarak (`Schema as Code`) yönetmek, versiyonlamak ve tutarlı bir şekilde dağıtmak. Manuel veritabanı değişikliklerinin yaratacağı operasyonel riskleri ortadan kaldırır. | **Manuel SQL Scriptleri** | Hataya açık, takibi zor ve otomatikleştirilmesi güç. Modern bir CI/CD sürecine uygun değil. |
| **Deployment**    | Docker Compose (Faz 1-2) -> Kubernetes (Faz 3+) | **Compose:** Hızlı başlangıç ve yerel geliştirme için mükemmel. **K8s:** Gerçek production ortamı için servis keşfi, kendini iyileştirme ve gelişmiş ölçeklendirme sağlar. | **Sadece Docker Compose**                | Production ortamında servislerin otomatik olarak yeniden başlatılması, merkezi konfigürasyon yönetimi gibi hayati operasyonel yeteneklerden yoksundur. Güvenilmezdir. |

### 2.4. Yerel Geliştirme Ortamı (Local Development Setup)

Projenin Docker ile izole bir şekilde çalışması hedeflense de, verimli bir geliştirme süreci (linting, test, script çalıştırma) için yerel ortamın doğru kurulması kritik öneme sahiptir.

*   **Sanal Ortam (Virtual Environment):** Proje kök dizininde bir sanal ortam oluşturulması zorunludur. Bu, sistemin genel Python kurulumundan bağımsız, projeye özel bir paket yönetimi sağlar.
    ```bash
    # Proje kök dizininde
    python3 -m venv .venv
    source .venv/bin/activate
    ```
*   **Bağımlılıkların Kurulumu:** Her servisin kendi `requirements.txt` dosyası olacaktır. Ortak kütüphane (`common`) dahil olmak üzere, yerel test ve script'lerin çalıştırılabilmesi için bu bağımlılıkların geliştirme ortamına kurulması gerekir.
    ```bash
    # Örnek olarak, ortak kütüphane ve diğer servislerin bağımlılıkları
    pip install -r services/common/requirements.txt
    pip install -r services/data_ingestor/requirements.txt
    # ... diğer servisler
    ```
*   **`.gitignore`:** Sanal ortam klasörü (`.venv/`) `.gitignore` dosyasına eklenmelidir. Bu, proje repozitorisinin temiz kalmasını sağlar. (Mevcut `.gitignore` dosyasında bu kural zaten bulunmaktadır).
*   **Not:** Bu kurulum, yalnızca yerel geliştirme ve test süreçleri içindir. Projenin kendisi `docker-compose` aracılığıyla, Docker konteynerleri içinde çalıştırılacaktır. Konteynerler, kendi içlerinde `requirements.txt` dosyalarını kullanarak bağımlılıkları kurarlar.

---

## Bölüm 3: Teknik ve Operasyonel Spesifikasyonlar

### 3.1. Veritabanı Şeması (Data Contract)

*   **Motor:** PostgreSQL 14
*   **Zaman Dilimi:** Tüm tarih/saat alanları için `TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ)`.
*   **Şema Yönetimi:** Tüm şema değişiklikleri, proje kök dizinindeki **Alembic** yapılandırması kullanılarak versiyonlanacak ve yönetilecektir.
*   **`users` Tablosu (Faz 2'de eklenecek):**
    *   `id`: `PRIMARY KEY`
    *   `email`: `VARCHAR`, `UNIQUE`
    *   `hashed_password`: `VARCHAR` (doğrudan şifre asla saklanmaz)
    *   `is_active`: `BOOLEAN`
    *   `created_at`, `updated_at`: `TIMESTAMPTZ`
*   **`api_keys` Tablosu (Faz 2'de eklenecek):**
    *   `id`: `PRIMARY KEY`
    *   `key_hash`: `VARCHAR`, `UNIQUE` (API anahtarının hash'lenmiş hali)
    *   `user_id`: `users` tablosuna `FOREIGN KEY`
    *   `is_active`: `BOOLEAN`
    *   `created_at`, `expires_at`: `TIMESTAMPTZ`
*   **`raw_articles` Tablosu:**
    *   `id`: `PRIMARY KEY`
    *   `source`: `VARCHAR` (örn: 'reuters', 'investing.com')
    *   `article_url`: `VARCHAR`, `UNIQUE` kısıtlaması olacak.
    *   `headline`: `TEXT`
    *   `article_text`: `TEXT`
    *   `published_at`: `TIMESTAMPTZ`
    *   `is_processed`: `BOOLEAN`, `DEFAULT false`
    *   `has_error`: `BOOLEAN`, `DEFAULT false`
    *   `created_at`, `updated_at`: `TIMESTAMPTZ`
*   **`sentiment_scores` Tablosu:**
    *   `id`: `PRIMARY KEY`
    *   `article_id`: `raw_articles` tablosuna `FOREIGN KEY` ile bağlanacak.
    *   `model_version`: `VARCHAR` (Model versiyonlaması için kullanılacak, örn: 'prosusai/finbert-v1.0').
    *   `sentiment_score`: `FLOAT`
    *   `sentiment_label`: `VARCHAR` (örn: 'positive', 'negative', 'neutral')
    *   `processed_at`: `TIMESTAMPTZ`

### 3.2. API Sözleşmesi (API Contract) - `signals_api`

*   **`GET /health`**: Servisin durumunu kontrol eder. `{"status": "ok"}` döner.
*   **`POST /v1/signals`**:
    *   **Amaç:** Belirtilen bir hisse senedi ve tarih aralığı için analiz edilmiş duygu verilerini listeler. Bu bir "Al/Sat" tavsiyesi değil, analitik bir veri dökümüdür.
    *   **Request Body (Pydantic ile doğrulanır):** `{ "ticker": "AAPL", "start_date": "2023-01-01T00:00:00Z", "end_date": "2023-01-31T23:59:59Z" }` (Not: `ticker` şu an için kullanılmayacak, gelecek için yer tutucudur).
    *   **Response (200):** 
        ```json
        {
          "data": [
            {
              "article_url": "http://...",
              "headline": "Apple a new high...",
              "published_at": "2023-01-15T10:00:00Z",
              "sentiment_score": 0.85,
              "sentiment_label": "positive"
            }
          ]
        }
        ```
    *   **Response (4xx/5xx):** Standart HTTP hata kodları.

### 3.3. Servis Spesifikasyonları

#### 3.3.1. `data_ingestor`
*   **Sorumluluk:** Periyodik olarak çalışarak dış kaynaklardan (örn: RSS) ham verileri çeker, veritabanındaki `raw_articles` tablosuna kaydeder. Döngünün sonunda, o döngüde eklenen **tüm yeni ve işlenmemiş makale ID'lerini bir liste olarak toplar** ve bu listeyi içeren **tek bir toplu işleme görevini (`batch-processing-task`)** mesaj kuyruğuna (Redis) gönderir.
*   **Tetikleme:** Servisin içindeki bir zamanlayıcı (`APScheduler` veya benzeri), veri toplama ve görev gönderme işlemini düzenli aralıklarla tetikler. Bu aralık, `DATA_INGESTION_INTERVAL_SECONDS` adında bir ortam değişkeni ile yapılandırılabilir olmalıdır (Varsayılan Değer: `300`).
*   **Dayanıklılık (Resilience):** Servis, dış kaynaklardan (RSS) gelebilecek bozuk veya beklenmedik formattaki verilere karşı **savunmacı (defensive)** bir yaklaşımla tasarlanmalıdır. Veri çekme ve ayrıştırma işlemleri `try-except` blokları içinde yapılmalıdır.
*   **Hata Yönetimi:** Bir makale ayrıştırılırken veya işlenirken hata oluşursa, bu hata loglanır ve ilgili `raw_articles` kaydındaki `has_error` alanı `True` olarak işaretlenir. Bu "zehirli hap" (poison pill) mekanizması, tek bir bozuk verinin tüm sistemi tıkamasını önler.
*   **Yeniden Deneme (Retry):** Ağ bağlantısı hataları gibi geçici sorunlar için, `tenacity` kütüphanesi kullanılarak **üstel geri çekilme (exponential backoff)** stratejisi ile yeniden deneme mantığı eklenecektir.

#### 3.3.2. `sentiment_processor`
*   **Mimari:** Bu servis, **Scheduler/Worker** modeline göre çalışır ve tek bir sorumluluğu vardır: mesaj kuyruğundan (Redis) gelen **toplu işleme görevlerini** işlemek. Zamanlama veya veri toplama ile ilgilenmez.
*   **Çalışma Prensibi:** Servis, bir veya daha fazla `worker` prosesi olarak çalışır. Her `worker`, mesaj kuyruğunu sürekli dinler. Kuyrukta yeni bir görev (bir liste dolusu `article_id` içeren) belirdiğinde, görevi alır, listedeki tüm makaleleri veritabanından tek seferde çeker, duygu analizi için modele **toplu halde (batch)** sunar ve sonuçları `sentiment_scores` tablosuna yazar.
*   **Hata Yönetimi (Poison Pill Prevention):** Görev işleme mantığının tamamı bir `try-except` bloğu içinde çalışmalıdır. Eğer toplu işleme sırasında (örneğin modelin kendisinden kaynaklanan) bir hata oluşursa, `worker` bu hatayı loglar, ilgili partideki tüm makalelerin `has_error` alanını `True` olarak günceller ve ardından görevi **başarıyla tamamlanmış** kabul ederek kuyruktan siler. Bu strateji, tek bir bozuk makalenin tüm işleme hattını tıkamasını engeller.
*   **Yükleme Stratejisi:** Model, her bir `worker` prosesi başladığında **sadece bir kez belleğe yüklenir** ve görevleri işlerken sürekli bellekte tutulur.
*   **Ölçeklenebilirlik:** İş yükü arttığında, çalışan `worker` konteyner sayısı yatay olarak artırılarak (`--scale` komutu ile) sistemin analiz kapasitesi kolayca yükseltilebilir.
*   **Kaynak Tahsisi:** `sentiment_processor` görevlerini çalıştıran `worker` konteynerine başlangıç için minimum **4 GB RAM** ve **2 vCPU** tahsis edilecektir.

---

## Bölüm 4: Güvenlik, Operasyonlar ve CI/CD

### 4.1. Güvenlik Tasarımı

*   **API Kimlik Doğrulama (Faz 2):** `/health` dışındaki tüm endpoint'ler `Authorization: Bearer <API_KEY>` başlığı ile korunacaktır.
    *   **Anahtar Doğrulama:** Gelen API anahtarı, veritabanındaki `api_keys` tablosunda hash'lenmiş olarak saklanan anahtarlarla karşılaştırılacaktır. Sadece `is_active=true` ve `expires_at` tarihi geçmemiş anahtarlar kabul edilecektir.
    *   **Kullanıcı İlişkisi:** Her API anahtarı bir kullanıcıya (`users` tablosu) bağlı olacaktır. Bu, gelecekte kullanıcı bazlı yetkilendirme ve kota yönetimine olanak tanır.
    *   **Güvenli Anahtar Üretimi:** `scripts/generate_api_key.py` script'i, kriptografik olarak güvenli, rastgele bir anahtar üretecek, bu anahtarı `bcrypt` ile hash'leyecek ve **orijinal anahtarı (örn: `sntzr_...`) sadece bir kez terminale basacaktır**. Script, anahtarı argüman olarak almayacaktır.
    *   **Oran Sınırlama (Rate Limiting):** Kötüye kullanımı önlemek için API anahtarı bazında oran sınırlaması (örn: 60 istek/dakika) uygulanacaktır.
    *   **Sır Yönetimi (Secret Management):** Veritabanı şifreleri, JWT gizli anahtarları gibi hassas bilgiler kodda veya imajda yer almayacak; **ortam değişkenleri (environment variables)** veya Vault gibi bir araç ile yönetilecektir.

### 4.2. CI/CD Pipeline (GitHub Actions)

1.  **Commit:** Geliştirici kodu GitHub'a gönderir.
2.  **CI (Otomatik):**
    *   Linting (`flake8`) ve formatlama (`black`) kontrolü.
    *   Birim ve entegrasyon testleri (`pytest`) çalıştırılır.
        *   **Test Stratejisi:** Testler `tests/unit` ve `tests/integration` olarak ayrılacaktır. Entegrasyon testleri, `testcontainers` kütüphanesi kullanılarak her test çalıştığında sıfırdan, geçici bir PostgreSQL konteyneri üzerinde çalıştırılarak, testlerin tutarlı ve izole bir ortamda gerçekleşmesi sağlanacaktır. Bu kurulumun karmaşıklığı nedeniyle, geliştiricilere yol göstermesi için `TESTING.md` adında ayrı bir döküman oluşturulması ve hem yerel hem de CI ortamı için detaylı konfigürasyon adımlarının belgelenmesi hedeflenecektir.
    *   Başarılı ise, her servis için yeni bir Docker imajı oluşturulur ve container registry'e gönderilir.
3.  **CD (Otomatik/Manuel):**
    *   `staging` ortamına otomatik dağıtım.
    *   `production` ortamına dağıtım **manuel onay** ile yapılır.
*   **Migrasyon Stratejisi:** `docker-compose` içinde servisler başlamadan önce veritabanı migrasyonlarını (`alembic upgrade head`) çalıştıran bir `entrypoint` script'i kullanılacaktır. Bu script, migrasyonun başarılı veya başarısız olduğunu **net bir şekilde loglamalıdır**, böylece geliştiriciler olası başlangıç problemlerini kolayca teşhis edebilir.

### 4.3. İzleme ve Kayıt Tutma (Monitoring & Logging)

*   **İzleme (Prometheus & Grafana):**
    *   **White-box:** Her servis, `/metrics` endpoint'i üzerinden standart metrikleri (istek sayısı/süresi, hata oranları vb.) yayınlayacaktır.
    *   **Black-box:** API'ın `/health` endpoint'i dışarıdan periyodik olarak kontrol edilecektir.
*   **Kayıt Tutma (Loki veya ELK Stack):**
    *   Tüm servisler, makine tarafından okunabilir **JSON formatında** log üretecektir.
    *   Loglar merkezi bir sistemde toplanacak ve analiz edilecektir. Geliştiriciler logları okumak için sunucuya SSH yapmayacaktır.
    *   **Geliştirici Ortamı Tavsiyesi:** Geliştirme sürecini kolaylaştırmak için, `docker-compose.yml` dosyasına `Loki` ve `Promtail` servislerinin eklenmesi, geliştiricilerin logları merkezi ve canlı olarak takip etme alışkanlığı kazanmasını sağlayacaktır.

### 4.4. Yedekleme ve Kurtarma (Backup & Recovery)

*   **Veritabanı:** Günde bir kez otomatik olarak yedeklenecek (snapshot) ve yedekler farklı bir coğrafi bölgede saklanacaktır.
*   **Kurtarma Planı:** Felaket kurtarma senaryosu (disaster recovery) dökümante edilecek ve periyodik olarak test edilecektir.

---

## Bölüm 5: Risk Yönetimi ve Geleceğe Yönelik Planlama

### 5.1. Teknik Riskler ve Azaltma Stratejileri

| Risk                                    | Azaltma Stratejisi                                                                                                                                                                                                   |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Veri Kaynağı Bağımlılığı (İş Riski)** | Bu, teknik bir problemden öte, temel bir **iş sürekliliği riskidir**. Azaltma stratejisi iki yönlüdür: **1) Teknik Esneklik:** `data_ingestor` içinde **Adaptör Tasarım Deseni** kullanılır. Her kaynak kendi modülüne sahip olur, böylece yeni kaynaklar eklemek veya mevcutları değiştirmek kolaylaşır. **2) Ticari Güvence:** Uzun vadede, işin sürekliliğini garanti altına almak için ücretsiz kaynaklara olan bağımlılık, profesyonel veri sağlayıcılarla yapılacak **ticari lisans anlaşmaları** ile azaltılacaktır. |
| **Veri Kalitesi Sorunları (Poison Pill)** | `data_ingestor` servisi, dış kaynaklardan gelen verileri **savunmacı programlama** ilkeleriyle işleyecek. Pydantic ile doğrulanamayan veya ayrıştırma sırasında sürekli hataya neden olan veriler, loglandıktan sonra `raw_articles` tablosunda `has_error=True` olarak işaretlenerek "karantinaya" alınır ve sistemin geri kalanının tıkanması önlenir. |
| **Servis Çökmeleri**                    | Docker Compose'da `restart: always` politikası kullanılacak. Kubernetes'e geçildiğinde ise Kubernetes'in kendi **"self-healing"** mekanizmasından faydalanılacak.                                                         |
| **Asenkron Görev Sistemi Riski** | Celery'nin `Redis` gibi kalıcı bir `broker` ile kullanılması, görevlerin durumunun korunmasını sağlar. Ancak bu durum, `broker`'ın kendisini bir "tek hata noktası" haline getirir. Bu nedenle `Redis` servisinin yüksek erişilebilirliği (high availability) ve metriklerinin izlenmesi kritik önem taşır. |
| **Geçici Hatalar (örn: DB bağlantı kopması)** | Servis içinde **üstel geri çekilme (exponential backoff)** ile yeniden deneme mantığı (`tenacity` kütüphanesi ile) implemente edilecek.                                                                           |

### 5.2. Geleceğe Yönelik Genişletme Senaryoları

Bu mimari, gelecekteki değişikliklere kolayca uyum sağlamak üzere tasarlanmıştır:

*   **Yeni Veri Kaynağı Ekleme:** Sadece yeni bir "adaptör" ile yeni bir `collector` servisi oluşturulur. Sistemin geri kalanında sıfır değişiklik gerekir.
*   **Yeni Analiz Modeli Ekleme:** `sentiment_processor`, her makale için birden fazla model skoru hesaplayacak şekilde güncellenebilir. `sentiment_scores` tablosundaki `model_version` sütunu bu ayrımı yönetir.
*   **Performans Artışı Gereksinimi:** Yoğun kullanılan bir servisin (örn: `signals_api`) çalışan sayısı artırılabilir veya Redis gibi bir **önbellekleme (caching)** katmanı eklenebilir.
*   **Yeni Özellik: "Geçmiş Testleri Kaydetme"**: Veritabanına `backtest_results` adında yeni bir tablo eklenir. `signals_api` bu tabloya yazmaz; bu işlevsellik, gelecekteki gerçek bir geri test motoru tarafından kullanılır ve sonuçlar yeni bir `/history` endpoint'i ile sunulur. Diğer servisler etkilenmez.
*   **Analiz Modelinin Veriminin Artırılması (Batch Processing):** FinBERT gibi Transformer tabanlı modellerin işlem süresi, veri akış hızının gerisinde kalabilir. Bu riski azaltmak için, `sentiment_processor` servisi Faz 2'de gerçek model entegrasyonu sırasında makaleleri tek tek değil, **toplu olarak (in batches)** işleyecek şekilde tasarlanacaktır. Bu, modelin verimini (throughput) önemli ölçüde artıracaktır.
*   **"Duygu Sağlayıcı"dan "Geri Test Motoru"na Evrim:** MVP'deki `signals_api`, temel duygu verilerini sunarak strateji validasyonu için bir başlangıç noktası sağlar. Platformun asıl değerini ortaya koyacak olan gelişmiş geri test motoru, önemli bir mühendislik eforu gerektiren bir sonraki adımdır. Bu motorun; işlem maliyetleri, slipaj (slippage), temettüler ve sermaye yönetimi gibi faktörleri hesaba katan daha sofistike bir yapıya dönüştürülmesi hedeflenmektedir. Bu, aynı zamanda hisse senedi fiyat verilerini içerecek yeni bir `price_data` tablosunun ve bu veriyi temin edecek bir servisin eklenmesini gerektirecek büyük bir iş paketidir.
*   **Veritabanı Yükünün Yönetimi (Polling Optimizasyonu):** Mevcut olay güdümlü mimari, MVP'de `polling` ile başlar. Bu, basit ve dayanıklı bir başlangıç olsa da, veri hacmi arttığında veritabanı üzerinde gereksiz yük oluşturur. Bu nedenle **Faz 2 kapsamında yapılacak ilk ve en önemli iyileştirme**, `sentiment_processor` servisinin `PostgreSQL LISTEN/NOTIFY` mekanizmasını kullanacak şekilde güncellenmesidir. Hibrit bir yaklaşım (öncelikli olarak `LISTEN/NOTIFY` kullanmak, ancak servis başlangıcında veya belirli aralıklarla "kaçırılmış olabilecek" olayları yakalamak için `polling` de yapmak) sistemin hem verimli hem de son derece dayanıklı olmasını garantileyecektir. Faz 3 ve sonrası için ise, sistemin ihtiyaçlarına göre RabbitMQ veya AWS SQS gibi tam teşekküllü bir mesajlaşma kuyruğuna geçiş değerlendirilebilir.
*   **Geliştirici Deneyimi (Developer Experience - Faz 1 Önceliği):** Geliştirme sürecini hızlandırmak ve kolaylaştırmak için `scripts/` dizini altında yardımcı script'ler oluşturulacaktır. Bunlar arasında, `common` kütüphanesinde yapılan değişikliklerden sonra tüm servis imajlarını yeniden inşa eden `local_rebuild.sh` gibi derleme script'leri ve veritabanını test verileriyle doldurarak API'ların (`signals_api` gibi) bağımsız olarak test edilmesini sağlayan `seed_database.py` gibi veri hazırlama script'leri yer alacaktır. Bu script'ler, geliştirme döngüsünü kısaltmak için **Faz 1 kapsamında geliştirilecektir.** 