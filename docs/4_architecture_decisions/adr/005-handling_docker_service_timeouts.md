# Docker Timeout Solutions for Sentilyzer

Bu dokuman, Sentilyzer projesinde Docker build sırasında yaşanan timeout sorunlarını ve çözümlerini açıklar.

## 🚨 Sorun Açıklaması

Docker build sırasında büyük ML paketleri (PyTorch, Transformers) indirilirken timeout hataları yaşanıyor:

```
TimeoutError: The read operation timed out
pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Read timed out.
```

## 🔧 Uygulanan Çözümler

### 1. Dockerfile Optimizasyonları

#### Timeout ve Retry Ayarları
```dockerfile
# Environment variables for pip optimization
ENV PIP_DEFAULT_TIMEOUT=1000 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_RETRIES=5
```

#### CPU-Only PyTorch Kullanımı
```dockerfile
# Install ML dependencies with CPU-only PyTorch
RUN pip install --no-cache-dir \
    --timeout=1000 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.1+cpu
```

### 2. Pip Konfigürasyonu

`pip.conf` dosyası ile global ayarlar:
```ini
[global]
timeout = 1000
retries = 5
no-cache-dir = true
extra-index-url = https://download.pytorch.org/whl/cpu
```

### 3. Build Script ile Retry Logic

`scripts/build_with_retry.sh` scripti:
- 3 kez deneme
- Her denemede 30 saniye bekleme
- Docker environment temizleme
- Colored output ile durum takibi

### 4. Docker Compose Optimizasyonları

```yaml
services:
  sentiment_processor:
    build:
      context: .
      dockerfile: services/sentiment_processor/Dockerfile
      args:
        BUILDKIT_INLINE_CACHE: 1
      target: application
```

## 🚀 Kullanım

### 1. Optimize Edilmiş Build Script Kullanımı

```bash
# Tüm servisleri build et
./scripts/build_with_retry.sh

# Sadece sentiment processor'ı build et
./scripts/build_with_retry.sh -s sentiment-processor

# Docker environment'ı optimize et ve build et
./scripts/build_with_retry.sh -o -a
```

### 2. Manuel Docker Build

```bash
# Docker BuildKit ile optimize build
DOCKER_BUILDKIT=1 docker build \
  --progress=plain \
  --no-cache \
  --pull \
  --build-arg PIP_DEFAULT_TIMEOUT=1000 \
  --build-arg PIP_RETRIES=5 \
  -f services/sentiment_processor/Dockerfile \
  -t sentilyzer-sentiment-processor:latest \
  .
```

### 3. Docker Compose ile Build

```bash
# Optimize edilmiş compose build
docker-compose build --no-cache --pull sentiment_processor
```

## 📊 Performans İyileştirmeleri

### Önceki Durum:
- ❌ Build süresi: 40+ dakika (timeout ile başarısız)
- ❌ İmaj boyutu: ~9.74GB (CUDA paketleri ile)
- ❌ Sürekli timeout hataları

### Sonraki Durum:
- ✅ Build süresi: 10-15 dakika
- ✅ İmaj boyutu: ~1.74GB (CPU-only)
- ✅ Güvenilir build süreci
- ✅ Retry logic ile hata toleransı

## 🛠️ Troubleshooting

### Build Hala Timeout Alıyorsa:

1. **Internet bağlantısını kontrol edin:**
```bash
# DNS test
nslookup files.pythonhosted.org
nslookup download.pytorch.org
```

2. **Docker resources'ları artırın:**
   - Docker Desktop > Settings > Resources
   - Memory: En az 4GB
   - CPU: En az 2 core

3. **Alternatif PyPI mirror kullanın:**
```bash
pip install --index-url https://pypi.douban.com/simple/ torch
```

4. **Docker system temizliği:**
```bash
docker system prune -a -f
docker builder prune -a -f
```

### Specific Error Solutions:

#### "Read timed out" Error:
```bash
# Timeout'u artır
export PIP_DEFAULT_TIMEOUT=2000
```

#### "No space left on device" Error:
```bash
# Docker temizliği
docker system prune -a -f --volumes
```

#### "Connection reset by peer" Error:
```bash
# Retry count'u artır
export PIP_RETRIES=10
```

## 🔍 Monitoring ve Logging

### Build Progress Takibi:
```bash
# Detaylı build log
DOCKER_BUILDKIT=1 docker build --progress=plain .
```

### Resource Usage Monitoring:
```bash
# Docker stats
docker stats --no-stream

# System resources
htop
```

## 📝 Best Practices

1. **Always use CPU-only packages** for production deployments
2. **Implement retry logic** for network operations
3. **Use multi-stage builds** to reduce final image size
4. **Clean up Docker environment** regularly
5. **Monitor build resources** during development
6. **Use .dockerignore** to reduce build context
7. **Set appropriate timeouts** based on network conditions

## 🔗 Useful Links

- [PyTorch CPU Installation](https://pytorch.org/get-started/locally/)
- [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Pip Configuration](https://pip.pypa.io/en/stable/topics/configuration/)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)

## 📞 Support

Timeout sorunları devam ederse:
1. Bu dokümandaki troubleshooting adımlarını takip edin
2. Build script'i `-o` flag ile çalıştırın
3. Docker environment'ı temizleyip tekrar deneyin
4. Network bağlantınızı kontrol edin
