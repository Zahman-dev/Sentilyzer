# ADR 002: Event-Driven Communication Through Database

**Date:** 2024-05-23

**Status:** Accepted

## Context

In a Service-Oriented Architecture, how services communicate with each other is a critical design decision. Various patterns exist, such as direct HTTP calls or a message queue. However, these approaches can increase system complexity and may require managing an additional "broker" component (e.g., RabbitMQ, Kafka).

## Decision

Inter-service communication will be handled **indirectly through state changes (events) in the database** rather than direct calls. When a service completes its task, it writes the result to a specific table in the database. This state change serves as an "event" to trigger the next service. For example, `data_ingestor` adds a new article to the `raw_articles` table; `sentiment_processor` periodically checks this table for records with `is_processed=False` to initiate its own task.

## Rationale

- **Resilience:** This is the biggest advantage of this approach. The data collector service is considered complete as soon as it writes the data to the database. Even if the analysis service is not running at that moment, the data is not lost. When the service comes back up, it can find the records waiting to be processed in the database and continue from where it left off. This increases the system's resistance to interruptions.

- **Simplicity and Decoupling:** Services don't need to know each other's network addresses, API contracts, or even existence. The database is the only common point that all services know about. This makes the system much simpler, more manageable, and less coupled.

- **Single Source of Truth:** Since all data and states are centralized (in the database), it's easier to understand the overall system state and debug issues.
