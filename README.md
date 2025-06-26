# Sentilyzer

Finansal metinleri işleyip stratejik içgörüye dönüştüren, ölçeklenebilir ve modüler bir platform.

---

## 🚀 Proje Özeti
Sentilyzer; haber, sosyal medya ve finansal kaynaklardan gelen metinleri analiz ederek, duygu skorları ve stratejik sinyaller üretir. Modern mikroservis mimarisi, kolay bakım ve yüksek ölçeklenebilirlik sağlar.

---

## 🏗️ Mimari ve Temel Bileşenler

- **Event-Driven & Service-Oriented**: Servisler birbirinden bağımsız, olay tabanlı çalışır.
- **Veritabanı Merkezli Olaylar**: Tüm servisler PostgreSQL üzerinden haberleşir.
- **Celery & Redis**: Asenkron görev yönetimi ve batch işleme.
- **Docker**: Tüm bağımlılıklar izole, kolay kurulum ve dağıtım.
- **Alembic**: Veritabanı şema yönetimi.

### Servis Akışı
```
[Kaynaklar] → [Data Ingestor] → [PostgreSQL] → [Sentiment Processor] → [PostgreSQL] → [Signals API] → [Dashboard]
```

---

## ⚡️ Hızlı Başlangıç

### Gereksinimler
- Docker & Docker Compose
- VS Code (önerilir)
- 4GB+ RAM, stabil internet

### Kurulum

**1. Tüm servisleri optimize build ile başlat:**
```bash
./scripts/build_with_retry.sh
# veya sadece bir servis için:
./scripts/build_with_retry.sh -s sentiment-processor
```

**2. Servisleri başlat:**
```bash
docker-compose up
```

**3. Erişim:**
- Dashboard: [http://localhost:8501](http://localhost:8501)
- API: [http://localhost:8888](http://localhost:8888)

**Timeout sorunu yaşarsan:**
- [DOCKER_TIMEOUT_SOLUTIONS.md](./DOCKER_TIMEOUT_SOLUTIONS.md) dosyasına bak.

---

## 🧩 Servisler

### 1. Sentiment Processor
- **Amaç:** Finansal metinlerde duygu analizi (FinBERT tabanlı, batch işleme)
- **Özellikler:**
  - Yüksek verimli batch işleme
  - Celery ile asenkron görevler
  - Fallback keyword analiz

### 2. Data Ingestor
- **Amaç:** Haber ve veri kaynaklarından otomatik veri toplama
- **Özellikler:**
  - RSS/Feed işleme
  - Zamanlanmış görevler
  - Hata yönetimi

### 3. Signals API
- **Amaç:** Duygu skorları ve analiz sonuçlarını REST API ile sunmak
- **Örnek Endpointler:**
  - `/api/v1/sentiment/latest` — Son skorlar
  - `/api/v1/sentiment/history` — Tarihsel veriler
  - `/api/v1/analytics/summary` — Özet analiz

### 4. Dashboard
- **Amaç:** Sonuçların görsel arayüzde sunulması
- **Teknoloji:** Streamlit

---

## 🚢 Deployment

### Production
1. Ortam değişkenlerini `.env` veya `docker-compose.prod.yml` ile ayarla
2. Başlat:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Temel Ortam Değişkenleri
- `DATABASE_URL`: PostgreSQL bağlantı adresi
- `REDIS_URL`: Redis bağlantı adresi
- `API_SECRET_KEY`: API anahtarı
- `LOG_LEVEL`: Log seviyesi (INFO, DEBUG, ERROR)

---

## 📈 Monitoring & Logging
- Tüm servisler structured JSON log üretir
- Logları izlemek için:
```bash
docker-compose logs -f <servis_adi>
```

---

## 🤝 Katkı & Geliştirme
1. Docker ve Python import standartlarına uy
2. Yeni servis eklerken multi-stage Dockerfile şablonunu kullan
3. VS Code ayarlarını güncelle
4. Ortak paket yapısını koru

---

## 📄 Lisans
MIT License — Ayrıntılar için `LICENSE` dosyasına bakın.

---

## 💬 Destek
- Docker/Python import veya geliştirme ortamı sorunları için dökümantasyondaki troubleshooting bölümüne bak.
- Ek destek için GitHub Issues üzerinden iletişime geçebilirsin.
