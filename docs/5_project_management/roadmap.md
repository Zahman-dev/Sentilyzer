# Sentilyzer - Technical and Operational Master Plan

**Document Purpose:** This document serves as the single, central reference source that defines all aspects of the development, deployment, and operation processes of the Sentilyzer platform. It acts as the main roadmap for the development team.

---

## Section 1: Strategic Framework and Roadmap

### 1.1. Project Vision and Architectural Philosophy

**Vision:** Create a scalable, maintainable, and extensible platform that transforms financial text data into actionable strategic insights. The system should work like a "data factory."

**Architectural Philosophy:** The system is based on an **Event-Driven** and **Service-Oriented** architecture. Services don't directly call each other; instead, they react to state changes (events) in the database. This maximizes the system's flexibility, resilience, and scalability.

### 1.2. Project Phasing and Milestones

The project will be developed with an agile approach in three main phases, each with clear deliverables.

**Phase 1: Minimum Viable Product (MVP) - (Target: First 4 Weeks)**
*   **Definition:** Version where the system's core data processing pipeline (RSS -> Analysis -> API) works end-to-end with a single basic strategy.
*   **Primary Goal:** Early validation of the biggest technical risk by testing FinBERT model's performance, cost, and latency in a live environment.
*   **Milestones:**
    *   **Week 1:** Core infrastructure (Database, service skeletons, **Celery/Redis infrastructure for asynchronous tasks**, central Alembic configuration in `common`).
    *   **Week 2:** Data flow (Creating Celery tasks for collecting and processing data from RSS).
    *   **Week 3:** Analysis and presentation (Sentiment Data API (`signals_api`) and text-based dashboard).
    *   **Week 4:** End-to-end testing, demo, and **completion of developer productivity scripts (`local_rebuild.sh`, `seed_database.py`).**

**Phase 2: Production Hardening - (Target: MVP + 6 Weeks)**
*   **Purpose:** Transform the MVP into a secure, monitorable, scalable, and reliable service.
*   **Milestones:**
    *   **Weeks 5-6:** Security (User-based API key management, secrets management).
    *   **Weeks 7-8:** Operational visibility (Centralized logging, metric monitoring).
    *   **Weeks 9-10:** CI/CD and test automation (70%+ code coverage).

**Phase 3: Feature Expansion - (Continuous)**
*   **Purpose:** Add new features that add value to the product (e.g., Twitter integration, advanced strategies, model explainability).

---

## Section 2: Detailed System Architecture and Design Decisions

### 2.1. Conceptual Architectural Diagram

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

### 2.2. Strategic Design Decisions and Justifications

| Decision                               | Justification                                                                                                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Service-Oriented Architecture**            | **Decoupled Scaling:** We only strengthen the slow-running service (e.g., `sentiment_processor`). **Technology Freedom:** We can rewrite a service with a different technology without affecting others. **Error Isolation:** If a service crashes, the rest of the system continues to work. |
| **Asynchronous Task Queue Communication** | **Resilience:** Tasks that need to be processed even if the processing service (`sentiment_processor`) is down will not be lost, they will wait in the queue. **Backpressure:** System does not get blocked in high data flow, `worker`s consume tasks at their own pace. **Separation of Responsibilities:** The service generating the task (`data_ingestor`) and the service consuming the task (`sentiment_processor`) are completely unaware of each other. |
| **API and Interface Separation**        | **Channel Diversity:** We can use the same API for different channels like web, mobile, B2B. **Parallel Development:** Backend and frontend teams can work without interfering with each other. |
| **Central Common Library (`common`)** | **Code Repetition Prevention:** We collect code that will be used by multiple services in one place to reduce maintenance costs and ensure consistency. |
| **Central Alembic Configuration (`common` in)** | **Developer Experience and Consistency:** `alembic.ini` and related scripts in the `services/common` folder are centrally managed, which allows for the versioning and management of the entire database schema in one place, version controlled. This ensures that migration commands can be run consistently and simply from either docker-compose or local environment, eliminating the complexity of separate migration configurations for each service. |

### 2.3. Platform Technologies: Selection and Alternatives

| Category      | Selected Technology | Justification                                                                                                     | Evaluated Alternatives          | Why Not Selected?                                                                                             |
|---------------|-------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| **API Framework** | FastAPI           | Automatic data validation (Pydantic), high performance (async), modern and easy to learn API. **Strategy:** FastAPI's automatic interactive API documentation (`/docs`, `/redoc`) feature, it will be actively used from the beginning of the development process and will be considered the primary API reference. | **Flask, Django REST Framework (DRF)**   | Flask: Requires additional libraries for data validation and documentation. DRF: More suitable for larger and more complex projects, overkill for this project. |
| **Database**    | PostgreSQL        | Powerful relational structure, transaction security (ACID), rich data types (JSONB), mature and stable.    | **MongoDB**                              | Our data is mostly structured and relational. MongoDB's flexible schema structure is an advantage, but it also risks data inconsistency. |
| **Asynchronous Tasks / Queue** | Celery & Redis | For managing long-running and asynchronous tasks like periodic data collection and high data processing, it provides a scalable and resilient solution. Allows for horizontal scaling and prevents a single point of failure (SPOF) in the system. | **`APScheduler` (in-service)** | It prevents horizontal scaling because it runs in the service, making it unsuitable for large-scale systems. |
| **Database Migration** | Alembic | Manage database schema as code, version, and deploy. Eliminates operational risks from manual database changes. | **Manual SQL Scripts** | It's error-prone, difficult to track, and not suitable for a modern CI/CD process. |
| **Deployment**    | Docker Compose (Faz 1-2) -> Kubernetes (Faz 3+) | **Compose:** Excellent for quick start and local development. **K8s:** Provides service discovery, self-healing, and advanced scaling for real production environment. | **Only Docker Compose**                | Production environment does not have automatic service restart, central configuration management, etc. It's not reliable. |

### 2.4. Local Development Environment (Local Development Setup)

Although the project's Dockerized isolated operation is the goal, the correct setup of the local environment is critical for an efficient development process (linting, test, script execution).

*   **Virtual Environment (Virtual Environment):** A virtual environment must be created in the project root directory. This provides a project-specific package management that is independent of the system's general Python setup.
    ```bash
    # In the project root directory
    python3 -m venv .venv
    source .venv/bin/activate
    ```
*   **Dependency Installation:** Each service's own `requirements.txt` file will be used. The common library (`common`) and other services' dependencies must be installed in the development environment to run local tests and scripts.
    ```bash
    # For example, dependencies for the common library and other services
    pip install -r services/common/requirements.txt
    pip install -r services/data_ingestor/requirements.txt
    # ... other services
    ```
*   **`.gitignore`:** The virtual environment directory (`.venv/`) must be added to the `.gitignore file. This ensures that the project repository remains clean. (This rule already exists in the existing `.gitignore` file).
*   **Note:** This setup is only for local development and test processes. The project itself will be run in Docker containers using docker-compose. Containers will install dependencies using their own `requirements.txt` files.

---

## Section 3: Technical and Operational Specifications

### 3.1. Database Schema (Data Contract)

*   **Engine:** PostgreSQL 14
*   **Time Scale:** `TIMESTAMP WITH TIME ZONE (TIMESTAMPTZ)` for all date/time fields.
*   **Schema Management:** All schema changes will be versioned and managed using the **Alembic** configuration in the project root directory.
*   **`users` Table (To be added in Faz 2):**
    *   `id`: `PRIMARY KEY`
    *   `email`: `VARCHAR`, `UNIQUE`
    *   `hashed_password`: `VARCHAR` (password is never stored directly)
    *   `is_active`: `BOOLEAN`
    *   `created_at`, `updated_at`: `TIMESTAMPTZ`
*   **`api_keys` Table (To be added in Faz 2):**
    *   `id`: `PRIMARY KEY`
    *   `key_hash`: `VARCHAR`, `UNIQUE` (hash of the API key)
    *   `user_id`: `FOREIGN KEY` to `users` table
    *   `is_active`: `BOOLEAN`
    *   `created_at`, `expires_at`: `TIMESTAMPTZ`
*   **`raw_articles` Table:**
    *   `id`: `PRIMARY KEY`
    *   `source`: `VARCHAR` (e.g., 'reuters', 'investing.com')
    *   `article_url`: `VARCHAR`, with `UNIQUE` constraint.
    *   `headline`: `TEXT`
    *   `article_text`: `TEXT`
    *   `published_at`: `TIMESTAMPTZ`
    *   `is_processed`: `BOOLEAN`, `DEFAULT false`
    *   `has_error`: `BOOLEAN`, `DEFAULT false`
    *   `created_at`, `updated_at`: `TIMESTAMPTZ`
*   **`sentiment_scores` Table:**
    *   `id`: `PRIMARY KEY`
    *   `article_id`: `FOREIGN KEY` to `raw_articles` table
    *   `model_version`: `VARCHAR` (Used for model versioning, e.g., 'prosusai/finbert-v1.0').
    *   `sentiment_score`: `FLOAT`
    *   `sentiment_label`: `VARCHAR` (e.g., 'positive', 'negative', 'neutral')
    *   `processed_at`: `TIMESTAMPTZ`

### 3.2. API Contract (API Contract) - `signals_api`

*   **`GET /health`**: Checks the status of the service. Returns `{"status": "ok"}`.
*   **`POST /v1/signals`**:
    *   **Purpose:** Lists analyzed sentiment data for a specified stock and date range. This is not a "Buy/Sell" recommendation, it's an analytical data dump.
    *   **Request Body (Validated with Pydantic):** `{ "ticker": "AAPL", "start_date": "2023-01-01T00:00:00Z", "end_date": "2023-01-31T23:59:59Z" }` (Note: `ticker` is placeholder for future use).
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
    *   **Response (4xx/5xx):** Standard HTTP error codes.

### 3.3. Service Specifications

#### 3.3.1. `data_ingestor`
*   **Responsibility:** Periodically collects data from external sources (e.g., RSS) and stores it in the `raw_articles` table in the database. At the end of the cycle, it will **collect all new and unprocessed article IDs** and send **a single batch processing task (`batch-processing-task`)** to the message queue (Redis) containing this list.
*   **Trigger:** The service's internal scheduler (`APScheduler` or similar) will trigger the data collection and task sending process at regular intervals. This interval can be configured with an environment variable `DATA_INGESTION_INTERVAL_SECONDS` (Default Value: `300`).
*   **Resilience:** The service should be designed with a **defensive** approach against potentially broken or unexpected format data from external sources (e.g., RSS). Data collection and parsing should be done in `try-except` blocks.
*   **Error Handling:** If an article fails to parse or process, it is logged and the `has_error` field in the related `raw_articles` record is marked as `True`. This "poison pill" mechanism prevents a single bad data from blocking the entire system.
*   **Retry Mechanism:** An exponential backoff retry mechanism will be implemented using the `tenacity` library for temporary issues like network connection errors.

#### 3.3.2. `sentiment_processor`
*   **Architecture:** This service works based on the **Scheduler/Worker** model and has a single responsibility: processing **batch processing tasks** from the message queue (Redis). It does not deal with scheduling or data collection.
*   **Working Principle:** The service runs as one or more `worker` processes. Each `worker` continuously listens to the queue. When a new task (a list of `article_id`s) appears in the queue, it processes the task, fetches all articles from the database at once for sentiment analysis to the model **in batch**, and writes the results to the `sentiment_scores` table.
*   **Error Handling (Poison Pill Prevention):** The entire processing logic must be in a `try-except` block. If a problem occurs during batch processing (e.g., from the model itself), the `worker` logs the error, updates the `has_error` field in the related part to `True`, and then considers the task **successfully completed** and removes it from the queue. This strategy prevents a single bad article from blocking the entire processing pipeline.
*   **Loading Strategy:** The model is **only loaded once** into memory when each `worker` process starts and is kept in memory while processing tasks.
*   **Scalability:** When the workload increases, the number of running `worker` container can be increased horizontally (`--scale` command) to easily increase the system's analysis capacity.
*   **Resource Allocation:** Minimum **4 GB RAM** and **2 vCPU** will be allocated for the `sentiment_processor` worker container at startup.

---

## Section 4: Security, Operations, and CI/CD

### 4.1. Security Design

*   **API Authentication (Faz 2):** All endpoints except `/health` will be protected with `Authorization: Bearer <API_KEY>`.
    *   **Key Validation:** The incoming API key will be compared with the hashed keys stored in the `api_keys` table in the database. Only keys with `is_active=true` and not expired (`expires_at`) will be accepted.
    *   **User Relationship:** Each API key will be associated with a user (`users` table). This will allow for future user-based authorization and quota management.
    *   **Secure Key Generation:** The `scripts/generate_api_key.py` script will generate a cryptographically secure, random key, hash it with `bcrypt`, and **only print the original key once to the terminal**. The script will not take any arguments.
    *   **Rate Limiting:** A rate limit will be applied based on the API key to prevent misuse.
    *   **Secret Management:** Sensitive information like database passwords, JWT secrets, etc. will not be in code or image; **environment variables** or tools like Vault will be used.

### 4.2. CI/CD Pipeline (GitHub Actions)

1.  **Commit:** Developer code is sent to GitHub.
2.  **CI (Automated):**
    *   Linting (`flake8`) and formatting (`black`) checks.
    *   Unit and integration tests (`pytest`) are run.
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
