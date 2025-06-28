# ADR 003: Using Celery & Redis for Asynchronous Task Management

**Date:** 2024-05-23

**Status:** Accepted

## Context

Sentiment analysis operations, by their nature, require intensive computation and can take a long time. Having such operations block user requests (e.g., API calls) or data collection processes synchronously can seriously impact system performance and user experience. Additionally, tasks that need to run periodically (e.g., hourly data collection) need to be managed reliably.

## Decision

**Celery** task queue system will be used for managing long-running and computation-intensive tasks along with periodic operations, with **Redis** serving as the message broker. Services like `sentiment_processor` will fetch data to be processed from the database and send them as Celery tasks to a queue. Independent `Celery workers` will pick up these tasks from the queue and process them asynchronously. For periodic tasks, the `Celery Beat` scheduler will be used.

## Rationale

- **Preventing API and System Bottlenecks:** When an API request triggers an analysis that could take minutes, this work can be immediately offloaded to the background (Celery queue). This allows the API to immediately return a response like "your request has been received" to the user and continue operating smoothly.

- **Scalable Workload Management:** When the workload increases (e.g., going from 100 news articles per day to 1 million), processing capacity can be horizontally scaled by simply increasing the number of `Celery workers` without needing to redesign the system. This is a flexibility that an in-process library like `APScheduler` cannot provide.

- **Reliable and Centralized Scheduling:** Periodic tasks like data collection are managed by a central `Celery Beat` service, independent of the application code. This ensures scheduling is more reliable, traceable, and manageable. Even if the `Beat` service crashes, it will continue scheduling tasks from where it left off when restarted.
