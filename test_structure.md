# Sentilyzer Test Mimarisi ve Yol Haritası

## 1. Felsefe ve Strateji

Mevcut test altyapısındaki `ImportError` ve `path` sorunları, testlerin merkezi ve standart bir yapıya sahip olmamasından kaynaklanmaktadır. Bu döküman, projeyi her ortamda (yerel makine, CI/CD pipeline) tutarlı bir şekilde test edilebilir hale getirecek modern bir test mimarisi sunar.

Test stratejimiz üç katmanlıdır:

1.  **Unit Tests (Birim Testleri):** Hızlı, izole ve her bir parçanın mantığını doğrulayan testler. Dış bağımlılık (DB, API) yoktur.
2.  **Integration Tests (Entegrasyon Testleri):** Servislerin birbiriyle ve altyapı (PostgreSQL, Redis) ile doğru konuşup konuşmadığını test eder.
3.  **E2E Pipeline Test (Uçtan Uca Test):** Sistemin ana iş akışını (veri alımı -> analiz -> API) baştan sona test eder.

## 2. Yeni `tests` Klasör Yapısı

Mevcut yapı yerine, `services` klasörünü yansıtan, daha temiz ve ölçeklenebilir bir yapı önerilmektedir:

```
tests/
├── __init__.py
├── conftest.py             # Merkezi fixtürler (DB session, API client)
|
├── unit/
│   ├── __init__.py
│   ├── test_common_utils.py
│   ├── test_data_ingestor.py
│   └── test_sentiment_processor.py
|
└── integration/
    ├── __init__.py
    ├── conftest.py         # Sadece entegrasyon testleri için fixtürler
    ├── test_api_auth.py    # Kimlik doğrulama, API anahtarları
    ├── test_api_endpoints.py # API endpoint'lerinin işlevselliği
    └── test_data_pipeline.py # Verinin sisteme girip işlenmesi
```

## 3. Anahtar Test Dosyaları ve İçerikleri

### `tests/conftest.py`
Bu dosya, tüm testlerde kullanılacak temel ve paylaşılan "fixture"ları (test hazırlık araçları) barındırır.

- **`db_session` fixture'ı:** Her test için temiz bir veritabanı oturumu oluşturur ve test bittiğinde oturumu kapatır. Testler için ayrı bir test veritabanı kullanır.
- **`api_client` fixture'ı:** `signals_api` için bir `TestClient` oluşturur. Bu, API'ye programatik olarak HTTP istekleri göndermemizi sağlar.
- **`test_user` ve `api_key` fixture'ları:** Testlerde kullanılmak üzere geçici bir kullanıcı ve ona ait geçerli bir API anahtarı oluşturur.

### `tests/unit/test_sentiment_processor.py` (Birim Testi)
`FinBERTBatchAnalyzer` sınıfının mantığını test eder.

- `test_fallback_sentiment_logic`: ML modeli olmadan, anahtar kelime tabanlı `_fallback_sentiment` fonksiyonunun doğru çalışıp çalışmadığını test eder.
- `test_batch_processing_with_mock_model`: Gerçek bir ML modeli yerine sahte (mock) bir model kullanarak `predict_batch` fonksiyonunun metinleri doğru gruplayıp sonuçları doğru formatta döndürdüğünü test eder.
- `test_model_loading_failure`: Model yüklenirken bir hata oluşursa, sınıfın çökmediğini ve fallback moduna geçtiğini doğrular.

### `tests/unit/test_data_ingestor.py` (Birim Testi)
`TickerExtractor` sınıfının doğruluğunu test eder.

- `test_ticker_extraction_from_map`: Metin içinde geçen şirket isminden (`"apple"`) doğru sembolü (`"AAPL"`) bulduğunu test eder.
- `test_ticker_extraction_from_regex`: Farklı regex formatlarını (`$TSLA`, `(MSFT)`, `NYSE: GE`) doğru şekilde yakaladığını test eder.
- `test_ticker_false_positives`: `THE`, `AND` gibi yaygın kelimeleri yanlışlıkla sembol olarak algılamadığını doğrular.

### `tests/integration/test_api_auth.py` (Entegrasyon Testi)
API kimlik doğrulama mekanizmasını test eder.

- `test_access_with_valid_key`: Geçerli bir API anahtarı ile korumalı bir endpoint'e erişilebildiğini (`200 OK`) doğrular.
- `test_access_with_invalid_key`: Geçersiz bir API anahtarı ile erişimin engellendiğini (`401 Unauthorized`) doğrular.
- `test_access_with_expired_key`: Süresi dolmuş bir API anahtarı ile erişimin engellendiğini (`401 Unauthorized`) doğrular.
- `test_access_with_inactive_user_key`: Pasif bir kullanıcıya ait anahtar ile erişimin engellendiğini (`401 Unauthorized`) doğrular.

### `tests/integration/test_data_pipeline.py` (Uçtan Uca Test)
Sistemin en önemli iş akışını test eder.

- `test_full_pipeline`:
    1.  **Adım (Ingestion):** Test veritabanına manuel olarak yeni bir `RawArticle` eklenir.
    2.  **Adım (Processing):** `process_sentiment_batch` Celery görevi, bu makalenin ID'si ile doğrudan çağrılır.
    3.  **Adım (Verification):** Görev tamamlandıktan sonra, veritabanında bu `RawArticle` için yeni bir `SentimentScore` kaydının doğru analiz sonucuyla oluşup oluşmadığı kontrol edilir.

## 4. Uygulama Planı

1.  Mevcut `tests` klasöründeki tüm dosyalar silinir.
2.  Yukarıda önerilen yeni klasör yapısı oluşturulur.
3.  `test_structure.md` dosyasında ana hatları çizilen test dosyaları ve içerikleri, adım adım kodlanır.
4.  `pyproject.toml` dosyasındaki test yolları (`testpaths`) yeni yapıya göre güncellenir.
5.  CI/CD pipeline (eğer varsa), `docker-compose exec test_runner_service pytest` gibi bir komutla testleri çalıştıracak şekilde yeniden yapılandırılır.
