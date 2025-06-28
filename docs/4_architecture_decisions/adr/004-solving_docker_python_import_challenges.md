# Docker Python Import Path Troubleshooting Guide

## Problem Summary
Docker containers often face Python import path issues when sharing modules between microservices, especially in development environments where linters show import errors.

## Our Solution: Industry Best Practices

### 1. Multi-Stage Docker Builds
```dockerfile
FROM python:3.10.17-slim as base
ENV PYTHONPATH=/app

FROM base as dependencies
# Install dependencies first for better caching

FROM dependencies as application
# Copy modules with proper structure
```

### 2. Proper Python Package Structure
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

### 3. Import Strategy in Python Code
```python
# Production Docker container path (primary)
try:
    from common.db.session import create_db_session
    from common.db.models import RawArticle, SentimentScore
except ImportError:
    # Fallback for development environment
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'common'))
        from app.db.session import create_db_session
        from app.db.models import RawArticle, SentimentScore
    except ImportError as e:
        logging.error(f"Failed to import database modules: {e}")
        # Final fallback
        sys.path.insert(0, '/common')
        from app.db.session import create_db_session
        from app.db.models import RawArticle, SentimentScore
```

### 4. Development Environment Configuration

#### VS Code Settings (`.vscode/settings.json`)
```json
{
    "python.analysis.extraPaths": [
        "./services/common/app",
        "./services/sentiment_processor/app"
    ],
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingImports": "none",
        "reportMissingModuleSource": "none"
    }
}
```

#### Pyright Configuration (`pyrightconfig.json`)
```json
{
    "extraPaths": [
        "./services/common/app",
        "./services/sentiment_processor/app"
    ],
    "reportMissingImports": "none",
    "reportMissingModuleSource": "none"
}
```

## Common Issues and Solutions

### Issue 1: "Module not found" in Development
**Symptoms:** Linter shows import errors but code works in Docker
**Solution:** Add paths to `python.analysis.extraPaths` in VS Code settings

### Issue 2: Requirements.txt with Relative Paths
**Symptoms:** Docker build fails with "No such file or directory"
**Solution:** Remove relative imports like `-r ../common/requirements.txt`

### Issue 3: Import Works in Development but Fails in Production
**Symptoms:** Code works locally but fails in Docker container
**Solution:** Use the multi-fallback import strategy shown above

### Issue 4: Linter Errors for Docker-Only Dependencies
**Symptoms:** VS Code shows errors for packages only available in containers
**Solution:** Set `"reportMissingImports": "none"` in pyrightconfig.json

## Best Practices

### ✅ DO
- Use multi-stage Docker builds for better caching
- Create proper `__init__.py` files for Python packages
- Set `PYTHONPATH=/app` in Docker containers
- Use fallback import strategies for cross-environment compatibility
- Configure development tools to ignore Docker-specific imports

### ❌ DON'T
- Use relative paths in requirements.txt files
- Mix volume mounts with COPY in production Dockerfiles
- Rely on symlinks for import resolution
- Use `sys.path.append()` without proper error handling

## Testing Your Setup

### 1. Test Docker Build
```bash
docker-compose build service_name --no-cache
```

### 2. Test Imports in Container
```bash
docker run --rm service_name python -c "from common.db.session import create_db_session; print('✅ Success!')"
```

### 3. Test Development Environment
Open VS Code and check that linter errors are suppressed for Docker imports.

## Troubleshooting Commands

### Check Python Path in Container
```bash
docker run --rm service_name python -c "import sys; print('\n'.join(sys.path))"
```

### Check File Structure in Container
```bash
docker run --rm service_name find /app -name "*.py" | head -20
```

### Check Environment Variables
```bash
docker run --rm service_name env | grep PYTHON
```

## Additional Resources

- [Docker Best Practices for Python](https://testdriven.io/blog/docker-best-practices/)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [VS Code Python Settings](https://code.visualstudio.com/docs/python/settings-reference)

## Support

If you encounter issues not covered in this guide:
1. Check the Docker build logs for specific error messages
2. Verify file paths match the expected container structure
3. Test imports in a running container to isolate the issue
4. Ensure all `__init__.py` files are present
