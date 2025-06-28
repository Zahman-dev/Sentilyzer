# ADR 001: Service-Oriented Architecture

**Date:** 2024-05-23

**Status:** Accepted

## Context

The project's long-term goals include scalability, maintainability, and resilience. As the application grows, it is anticipated that a monolithic structure would make it difficult to achieve these goals. Different functions (data collection, analysis, API presentation) will have different resource needs and development cycles.

## Decision

The project will adopt a **Service-Oriented Architecture (SOA)** that organizes its core functions (data collection, sentiment analysis, API presentation, etc.) as independent, loosely coupled services. Each service will be responsible for a specific business domain and will run as a Docker container.

## Rationale

- **Error Isolation:** A failure or malfunction in one service (e.g., `sentiment_processor`) does not directly affect other parts of the system (e.g., `data_ingestor`, `signals_api`). This increases the overall resilience of the system.

- **Independent Scaling:** If sentiment analysis processing becomes a bottleneck, only the number of workers for the `sentiment_processor` service can be increased. There's no need to scale the entire platform horizontally, ensuring efficient resource utilization.

- **Technology Freedom:** Each service can use its own technology stack. For example, if we want to rewrite the sentiment analysis model in Rust or Go instead of Python in the future, we can do so without affecting other services.

- **Parallel Development:** Different teams or developers can work independently on their own services without needing to know the internal workings of other services.
