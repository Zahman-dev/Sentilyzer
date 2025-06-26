# Sentilyzer - Finansal Duygu Analizi ve Geri Test Platformu

## Proje Vizyonu

Finansal metin verilerini, işlenebilir stratejik içgörülere dönüştüren, ölçeklenebilir, bakımı kolay ve genişletilebilir bir platform yaratmak. Sistem, bir "veri fabrikası" gibi çalışmalıdır; bir uçtan ham madde (metin) girer, montaj hatlarından (servisler) geçer ve diğer uçtan değerli bir ürün (analiz/strateji sonucu) çıkar.

## Temel Mimari

Sistem, **Olay Güdümlü (Event-Driven)** ve **Servis Odaklı (Service-Oriented)** bir mimariye dayanır. Servisler birbirlerini doğrudan çağırmazlar; bunun yerine veritabanındaki durum değişikliklerine (olaylara) tepki verirler. Bu, sistemin esnekliğini ve dayanıklılığını (resilience) en üst düzeye çıkarır.

## Temel Tasarım Kararları ve Gerekçeleri

Bu proje, sadece belirli teknolojileri kullanmakla kalmaz, aynı zamanda bu seçimlerin arkasındaki felsefeyi de benimser. Her bir teknoloji ve mimari desen, platformun uzun vadeli hedefleri olan **ölçeklenebilirlik**, **bakım kolaylığı** ve **dayanıklılığı (resilience)** desteklemek için dikkatle seçilmiştir.

*   **Neden Servis Odaklı Mimari (Service-Oriented Architecture)?**
    *   **Hata İzolasyonu:** Bir servis (örn: `sentiment_processor`) çökse bile, sistemin geri kalanı (örn: `data_ingestor`, `signals_api`) çalışmaya devam eder.
    *   **Bağımsız Ölçeklendirme:** Eğer duygu analizi işlemi yavaşlarsa, sadece o işi yapan `celery_worker` sayısını artırırız. Tüm platformu yatayda büyütmek zorunda kalmayız.
    *   **Teknoloji Özgürlüğü:** Gelecekte duygu analizi modelini Python yerine Rust ile yazmak istersek, bunu diğer servisleri etkilemeden yapabiliriz.

*   **Neden Veritabanı Üzerinden Olay Güdümlü İletişim?**
    *   **Dayanıklılık:** Veri toplayıcı servis, veriyi veritabanına yazdığı an görevini tamamlamış sayılır. Analiz servisi o an çalışmıyor olsa bile veri kaybolmaz; servis ayağa kalktığında kaldığı yerden devam eder.
    *   **Basitlik ve Ayrıklık (Decoupling):** Servislerin birbirlerinin ağ adresini veya API'ını bilmesi gerekmez. Tek iletişim noktası veritabanıdır. Bu, sistemi çok daha basit ve yönetilebilir kılar.

*   **Neden Celery & Redis ile Asenkron Görev Yönetimi?**
    *   **API'ın Tıkanmasını Önleme:** Bir kullanıcının API isteğiyle 10 dakika sürecek bir rapor oluşturmak, kullanıcıyı bekletir ve sistemi yorar. Celery ile bu işi anında arka plana atıp kullanıcıya "işleminiz alındı, tamamlanınca haber vereceğiz" yanıtı dönebiliriz.
    *   **Ölçeklenebilir İş Yükü:** Günde 100 haber işlerken 1 `worker` yeterliyken, 1 milyon haber işlerken `worker` sayısını 50'ye çıkararak aynı hızda çalışmaya devam edebiliriz. Bu esneklik, `APScheduler` gibi servis-içi bir kütüphane ile mümkün değildir.
    *   **Güvenilir Zamanlama:** Periyodik veri toplama görevleri, uygulama kodundan bağımsız, merkezi bir `Celery Beat` servisi tarafından yönetilir. Bu, zamanlamanın daha güvenilir ve yönetilebilir olmasını sağlar.

*   **Neden Alembic ile Veritabanı Versiyonlama?**
    *   **"Kod Olarak Şema" (Schema as Code):** Veritabanı şemasını (tablolar, sütunlar) kod gibi Git ile versiyonlamamızı sağlar.
    *   **Tutarlılık ve Güvenlik:** Her geliştiricinin bilgisayarında ve production ortamında aynı veritabanı şemasının olmasını garanti eder. Manuel, hataya açık `ALTER TABLE...` komutlarını çalıştırma riskini ortadan kaldırır.

*   **Neden Her Şey için Docker?**
    *   **"Benim Makinemde Çalışıyordu" Sorununu Çözmek:** Bir geliştiricinin makinesinde çalışan kodun, başka bir geliştiricinin makinesinde veya sunucuda da birebir aynı şekilde çalışacağını garanti eder.
    *   **İzolasyon ve Kolay Kurulum:** Projenin tüm bağımlılıkları (PostgreSQL, Redis, Python kütüphaneleri) konteynerler içinde izole edilir. Yeni bir geliştirici, sadece `docker-compose up` komutuyla tüm platformu 5 dakika içinde çalışır hale getirebilir.

```
+---------------------------+
|      DIŞ DÜNYA (SOURCES)  |
| - Reuters, Bloomberg (RSS)|
| - Twitter API             |
| - SEC Filings (EDGAR)     |
+-------------|-------------+
              |
              ▼ (1. Veri Alımı)
+---------------------------+
|    SERVICE 1:             |
|    DATA INGESTOR          |  <<-- (Periyodik olarak tetiklenir: CRON/Scheduler)
|---------------------------|
| Sorumluluk: Veriyi ham     |
| ve değişmemiş olarak     |
| standart bir formatta     |
| sisteme almak.            |
|                           |
| Çıktı: "raw_articles"     |
| tablosuna yeni kayıt.     |
+-------------|-------------+
              |
              ▼ (2. OLAY: Yeni Ham Veri Eklendi)
+---------------------------+
|    VERİTABANI (PostgreSQL)|
|      - TEK GERÇEK KAYNAĞI - |
+---------------------------+
| - raw_articles            |
| - sentiment_scores        |
| - backtest_results        |
| - (Gelecekte) price_data  |
+-------------|-------------+
              ▲
              | (3. OLAY: Yeni Ham Veri Bekleniyor)
              |
+-------------|-------------+
|    SERVICE 2:             |
|    SENTIMENT PROCESSOR    | <<-- (Sürekli veritabanını dinler: Polling)
|---------------------------|
| Sorumluluk: Ham metni      |
| alıp, zenginleştirmek     |
| (duygu analizi).          |
|                           |
| Çıktı: "sentiment_scores" |
| tablosuna yeni kayıt.     |
+-------------|-------------+
              ▲
              | (4. OLAY: Analiz Sonucu Bekleniyor)
              |
+-------------|-------------+
|    SERVICE 3:             |
|    SIGNALS API            | <<-- (Kullanıcı tarafından tetiklenir: HTTP Request)
| (MVP'de "Duygu Veri Sağlayıcı") |
|---------------------------|
| Sorumluluk: Analiz edilmiş|
| duygu skorlarını ve ilgili|
| verileri, isteğe bağlı   |
| olarak sunmak.            |
|                           |
| Çıktı: JSON response.     |
+-------------|-------------+
              |
              ▼ (5. API Çağrısı)
+---------------------------+
|    SERVICE 4:             |
|    DASHBOARD              |
|---------------------------|
| Sorumluluk: İnsan-bilgisayar|
| etkileşimini sağlamak.    |
|                           |
| Çıktı: Görsel arayüz.      |
+-------------|-------------+
              |
              ▼
+---------------------------+
|        KULLANICI          |
+---------------------------+
```

### Problem
Docker containers often face Python import path issues when sharing modules between microservices, especially in development environments where linters show import errors.

### Solution
We implement industry best practices for Docker Python module management:

#### 1. Multi-Stage Docker Builds
```dockerfile
FROM python:3.10.17-slim as base
ENV PYTHONPATH=/app

FROM base as dependencies
# Install dependencies first for better caching

FROM dependencies as application
# Copy modules with proper structure
COPY services/common/app /app/common
COPY services/service_name/app /app/service_name
```

#### 2. Proper Python Package Structure
```
/app/
├── __init__.py
├── common/
│   ├── __init__.py
│   ├── db/
│   └── schemas/
└── service_name/
    ├── __init__.py
    └── main.py
```

#### 3. Import Strategy
```python
# Production Docker container path
from common.db.session import create_db_session
from common.db.models import RawArticle
```

#### 4. Development Environment Configuration
VS Code settings in `.vscode/settings.json`:
```json
{
    "python.analysis.extraPaths": [
        "./services/common/app",
        "./services/sentiment_processor/app"
    ],
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingImports": "none"
    }
}
```

## Development Setup

### Prerequisites
- Docker and Docker Compose
- VS Code (recommended) with Python extension
- Minimum 4GB RAM for Docker
- Stable internet connection for ML package downloads

### Quick Start

#### Option 1: Using Optimized Build Script (Recommended)
```bash
# Build all services with timeout optimization
./scripts/build_with_retry.sh

# Or build specific service
./scripts/build_with_retry.sh -s sentiment-processor

# Start services
docker-compose up
```

#### Option 2: Standard Docker Compose
```bash
# Build and start services
docker-compose up --build
```

#### Option 3: Manual Build with Optimization
```bash
# Build with timeout settings
DOCKER_BUILDKIT=1 docker-compose build --no-cache --pull
docker-compose up
```

### 🚨 Docker Timeout Issues?
If you encounter timeout errors during build, see [DOCKER_TIMEOUT_SOLUTIONS.md](./DOCKER_TIMEOUT_SOLUTIONS.md) for comprehensive solutions.

### Access Points
- Dashboard: `http://localhost:8501`
- API endpoints: `http://localhost:8888`

### Development Environment
For development with proper import resolution:

1. Open the project in VS Code
2. The `.vscode/settings.json` is pre-configured for Docker development
3. Linter errors for Docker-specific imports are suppressed in development
4. All imports work correctly in production containers

### Container Structure Benefits
- **Isolation**: Each service runs in its own container
- **Scalability**: Services can be scaled independently
- **Consistency**: Same environment in development and production
- **Performance**: Multi-stage builds optimize image size and build time

## Services

### Sentiment Processor
Advanced sentiment analysis using FinBERT model with batch processing capabilities.

**Features:**
- FinBERT model for financial text analysis
- Batch processing for high throughput
- Celery-based asynchronous processing
- Fallback keyword-based analysis

### Data Ingestor
Automated data collection from financial news sources.

**Features:**
- RSS feed processing
- Scheduled data collection
- Duplicate detection
- Error handling and recovery

### Signals API
RESTful API for accessing sentiment data and analytics.

**Endpoints:**
- `/api/v1/sentiment/latest` - Latest sentiment scores
- `/api/v1/sentiment/history` - Historical data
- `/api/v1/analytics/summary` - Aggregated analytics

## Deployment

### Production Deployment
1. Set environment variables in `docker-compose.prod.yml`
2. Deploy using:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `API_SECRET_KEY`: API authentication key
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

## Monitoring and Logging

All services use structured JSON logging for easy parsing and monitoring. Logs are available through Docker Compose:

```bash
docker-compose logs -f service_name
```

## Contributing

1. Follow the established Docker Python import patterns
2. Add new services using the multi-stage Dockerfile template
3. Update VS Code settings for new service paths
4. Ensure all services follow the common package structure

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues related to Docker Python imports or development environment setup, please check the troubleshooting section in the documentation.
