# High-Level Architecture

The system is based on an **Event-Driven** and **Service-Oriented** architecture. Services do not directly call each other; instead, they react to state changes (events) in the database. This maximizes the system's flexibility and resilience.

This approach can best be explained with a "data factory" analogy: raw material (text) enters from one end, passes through assembly lines (services), and a valuable product (analysis/strategy result) emerges from the other end.

## Data Flow Diagram

```
+---------------------------+
|      EXTERNAL WORLD (SOURCES)|
| - Reuters, Bloomberg (RSS)|
| - Twitter API             |
| - SEC Filings (EDGAR)     |
+-------------|-------------+
              |
              ▼ (1. Data Ingestion)
+---------------------------+
|    SERVICE 1:             |
|    DATA INGESTOR          |  <<-- (Periodically triggered: CRON/Scheduler)
|---------------------------|
| Responsibility: Ingest    |
| data in raw and          |
| unchanged format in a     |
| standardized way.         |
|                          |
| Output: New record in    |
| "raw_articles" table.    |
+-------------|-------------+
              |
              ▼ (2. EVENT: New Raw Data Added)
+---------------------------+
|    DATABASE (PostgreSQL)  |
|    - SINGLE SOURCE OF TRUTH -|
+---------------------------+
| - raw_articles           |
| - sentiment_scores       |
| - backtest_results       |
| - (Future) price_data    |
+-------------|-------------+
              ▲
              | (3. EVENT: New Raw Data Expected)
              |
+-------------|-------------+
|    SERVICE 2:             |
|    SENTIMENT PROCESSOR    | <<-- (Continuously monitors database: Polling)
|---------------------------|
| Responsibility: Take raw  |
| text and enrich it       |
| (sentiment analysis).    |
|                          |
| Output: New record in    |
| "sentiment_scores" table.|
+-------------|-------------+
              ▲
              | (4. EVENT: Analysis Result Expected)
              |
+-------------|-------------+
|    SERVICE 3:             |
|    SIGNALS API            | <<-- (Triggered by user: HTTP Request)
| (MVP: "Sentiment Data Provider")|
|---------------------------|
| Responsibility: Provide   |
| analyzed sentiment scores |
| and related data on      |
| demand.                  |
|                          |
| Output: JSON response.    |
+-------------|-------------+
              |
              ▼ (5. API Call)
+---------------------------+
|    SERVICE 4:             |
|    DASHBOARD              |
|---------------------------|
| Responsibility: Enable    |
| human-computer           |
| interaction.             |
|                          |
| Output: Visual interface. |
+-------------|-------------+
              |
              ▼
+---------------------------+
|         USER              |
+---------------------------+
```
