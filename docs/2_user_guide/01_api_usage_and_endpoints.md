# API Usage Guide and Endpoints

This document explains how to use the Sentilyzer Signals API.

## Authentication

All requests to the API must be authenticated with a valid API Key. The key should be sent as a `Bearer` token in the HTTP `Authorization` header.

**Example:**
`Authorization: Bearer <YOUR_API_KEY>`

## Rate Limiting

Rate limiting is applied to API endpoints to prevent abuse and ensure service quality. When the limit is exceeded, you will receive a `429 Too Many Requests` error.

## Main Endpoints

### 1. `/v1/signals` (POST)

Retrieves sentiment analysis signals for a specific stock (ticker) within the specified date range.

**Request Body (`SignalsRequest`):**
```json
{
  "ticker": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

**Successful Response (`SignalsResponse`):**
```json
{
  "data": [
    {
      "article_url": "https://example.com/news/123",
      "headline": "Apple reports record profits...",
      "published_at": "2024-01-15T10:00:00Z",
      "sentiment_score": 0.85,
      "sentiment_label": "positive"
    }
  ],
  "total_count": 1
}
```

### 2. `/v1/stats` (GET)

Returns basic statistics about the data in the system.

### 3. `/v1/sources` (GET)

Returns a list of data sources being collected in the system.
