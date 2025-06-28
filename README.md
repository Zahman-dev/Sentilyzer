# Sentilyzer - Finansal Duygu Analizi Platformu

[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Finansal metin verilerini, işlenebilir stratejik içgörülere dönüştüren, ölçeklenebilir, bakımı kolay ve genişletilebilir bir platform.

## Projeye Genel Bakış

Sentilyzer, finansal haberler ve sosyal medya metinleri gibi yapılandırılmamış verileri toplayan, bunlar üzerinde **FinBERT** modeli ile duygu analizi yapan ve sonuçları güvenli bir API üzerinden sunan, mikroservis tabanlı bir sistemdir.

**Daha fazla bilgi için, projenin kapsamlı dokümantasyonunu inceleyin:**

> ### 📚 [Detaylı Dokümantasyon için buraya tıklayın](./docs/README.md)

## Hızlı Kurulum ve Çalıştırma

Tüm platformu (PostgreSQL, Redis, tüm servisler) Docker Compose ile hızla ayağa kaldırabilirsiniz:

```bash
# Servisleri build et ve arka planda başlat
docker-compose up --build -d
```

**Erişim Noktaları:**
- **Dashboard**: `http://localhost:8501`
- **Signals API Docs**: `http://localhost:8080/docs`

Geliştirme ortamı kurulumu, mimari detaylar, API kullanımı ve daha fazlası için lütfen [ana dokümantasyon sayfamızı](./docs/README.md) ziyaret edin.

## Temel Teknolojiler

- **Python**
- **FastAPI** (API için)
- **Celery & Redis** (Asenkron görevler için)
- **PostgreSQL & Alembic** (Veritabanı ve migrasyonlar için)
- **Transformers & PyTorch** (Duygu analizi için)
- **Docker & Docker Compose** (Konteynerizasyon için)
- **Ruff & Pytest** (Kod kalitesi ve test için)
