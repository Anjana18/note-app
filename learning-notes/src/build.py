"""Build the complete course PDF.

Usage: python3 build.py ../Java-Backend-Complete-Course.pdf
"""
import importlib
import sys

from reportlab.platypus import PageBreak, Spacer
from engine import P, build, table, render_block, toc_para

MODULE_NAMES = ["m1", "m2", "m3", "m4", "m5", "m6", "m7"]
modules = []
for name in MODULE_NAMES:
    try:
        modules.append(importlib.import_module(name).MODULE)
    except ModuleNotFoundError:
        pass

front = [
    Spacer(1, 120),
    P("Java, Spring Boot, Microservices & Cloud-Native Backend", "cover_t"),
    Spacer(1, 16),
    P("The Complete Course: from JVM internals to Kubernetes", "cover_s"),
    Spacer(1, 40),
    P(f"{len(modules)} modules · {sum(len(m['topics']) for m in modules)} topics · analogies, diagrams, "
      "production code, common mistakes, check-in questions and an answer key", "cover_s"),
    PageBreak(),
    P("How to Use This Course", "mod"),
    P("Every topic follows the same rhythm, designed so you learn one idea at a time:"),
    *render_block(("ol", [
        "**Real-world analogy:** build intuition before any code.",
        "**Diagram & production-grade code:** see how it actually works.",
        "**Common mistake:** what juniors get wrong and how to debug it.",
        "**Key takeaways:** the three points to remember.",
        "**Check for understanding:** answer it *before* turning to the Answer Key at the end.",
    ])),
    P("Learning path", "h"),
    table([["Module", "Focus", "Why it matters"],
           ["1. Java Core", "JVM, GC, collections, Java 8 → 25 features (lambdas, streams, Optional, records, sealed, pattern matching), threads, virtual threads", "The language and runtime under everything"],
           ["2. SQL", "Indexes, ACID, isolation levels", "Correct, fast transactional data"],
           ["3. MongoDB", "Document modelling, embed vs reference", "Flexible schemas, read-optimised data"],
           ["4. Redis", "Cache-aside, avalanche/penetration/breakdown", "Speed and protecting the database"],
           ["5. Spring Boot", "Auto-config, @Transactional proxies, Resilience4j", "The framework you ship with"],
           ["6. Microservices", "Kafka partitions, consumer groups, Saga, outbox", "Scaling teams and systems"],
           ["7. Cloud-Native", "Docker multi-stage, Kubernetes, probes, troubleshooting", "Running it in production"]],
          [0.2, 0.45, 0.35]),
    P("Versions: examples target **Java 21 (LTS)** (Java 25 LTS notes included) and **Spring Boot 3.x**, PostgreSQL 16, MongoDB 7, "
      "Redis 7, Kafka 3.x and Kubernetes 1.30+."),
    P("Tip: type out the code yourself rather than copy-pasting. Muscle memory matters."),
    PageBreak(),
]

B = render_block
back = [
    toc_para("Capstone: E-Commerce Order Management System", "mod", 0, "capstone"),
    P("Put every module to work by building a production-style system, one milestone at a time. Finish "
      "each milestone with tests passing before moving on."),
    *B(("code", """
                         ┌────────────────┐
  Client ──────────────► │  API Gateway   │ (Spring Cloud Gateway: JWT auth, rate limit)
                         └───────┬────────┘
       ┌─────────────────┬───────┴─────────┬──────────────────┐
       ▼                 ▼                 ▼                  ▼
 ┌───────────┐    ┌────────────┐    ┌────────────┐    ┌──────────────┐
 │ Order     │    │ Catalog    │    │ Payment    │    │ Inventory    │
 │ Postgres  │    │ MongoDB    │    │ Postgres   │    │ Postgres     │
 │ + Outbox  │    │ + Redis    │    │ + Resil4j  │    │              │
 └─────┬─────┘    └────────────┘    └─────┬──────┘    └──────┬───────┘
       └──────────────── Kafka: orders / payments / inventory ┘
                                   │
                          ┌────────▼────────┐
                          │ Notification    │
                          └─────────────────┘
""")),
    *B(("table", [["Service", "Store", "Why this choice"],
                  ["Order", "PostgreSQL", "Money & state transitions need ACID, constraints, `@Version`"],
                  ["Catalog", "MongoDB + Redis", "Varied product attributes; read-heavy, so cache-aside with jitter"],
                  ["Payment", "PostgreSQL", "Ledger integrity; Resilience4j around the external gateway"],
                  ["Inventory", "PostgreSQL", "Atomic `UPDATE ... WHERE stock > 0` for flash sales"],
                  ["Sessions / cart", "Redis", "Short-lived, high-frequency, TTL-based"]],
                 [0.18, 0.22, 0.60])),
    P("Milestones", "h"),
    *B(("table", [["#", "Milestone", "Modules applied", "Done when…"],
                  ["1", "Order Service: Spring Boot 3 + PostgreSQL + Flyway; REST CRUD; layered (controller → service → repository); DTO records; validation; global `@RestControllerAdvice`",
                   "1, 2, 5", "Integration tests with Testcontainers pass; `EXPLAIN` shows index scans"],
                  ["2", "Catalog Service: MongoDB documents, ESR indexes, search & aggregation", "3", "Category filter + sort served by IXSCAN"],
                  ["3", "Redis cache-aside on product reads; TTL jitter; null caching", "4", "p95 latency drops; DB QPS falls on load test"],
                  ["4", "Payment client with timeouts, Retry + CircuitBreaker + fallback", "5", "Killing the fake gateway doesn't take Order down"],
                  ["5", "Kafka events with Outbox; choreographed Saga with compensations; idempotent consumers; DLT", "6", "Kill a consumer mid-flow → no duplicates, no lost orders"],
                  ["6", "Dockerfiles (multi-stage), docker-compose for local; K8s manifests with probes, resources, ConfigMaps/Secrets", "7", "Rolling update with zero failed requests"],
                  ["7", "Observability: Micrometer + Prometheus, OpenTelemetry tracing, correlation IDs in logs", "All", "One trace shows an order across all services"]],
                 [0.05, 0.47, 0.16, 0.32])),
    P("Beginner mistakes to watch for in the project", "h"),
    *B(("ul", ["**Connection leaks / pool exhaustion:** set `spring.datasource.hikari.leak-detection-threshold=20000` "
               "in dev; never hold a transaction across a remote call.",
               "**N+1 queries:** enable SQL logging in dev and use `JOIN FETCH` / `@EntityGraph` for lists.",
               "**Missing indexes:** run `EXPLAIN ANALYZE` on every query in the hot path.",
               "**Kafka rebalancing storms:** keep listeners fast; watch for repeated \"Revoking partitions\" logs.",
               "**Wrong probes:** no DB checks in liveness; add a startup probe."])),
    *B(("p", "Suggested prompt for a step-by-step build session: *\"Act as a Senior Tech Lead and guide me through "
             "Milestone 1: setting up the Spring Boot Order Service with PostgreSQL.\"*")),
    PageBreak(),
]

if __name__ == "__main__":
    build(sys.argv[1], modules, front, back)
