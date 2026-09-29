# Microservices Architecture & Patterns

## Monolith vs microservices: when would you NOT use microservices?
Microservices are **independently deployable services, each organised around a business capability, each owning its own data**.
- **Benefits**: independent deployment and scaling, team autonomy (fits Conway's law), fault isolation, and freedom of technology per service.
- **Costs**: distributed-systems complexity (network failures, latency, eventual consistency), operational overhead (CI/CD, observability, Kubernetes), harder testing and debugging, and data consistency across services.
- **Avoid them** for a small team, an unclear domain or an early-stage product. Start with a **modular monolith** with clean boundaries, and extract services when a real need appears (scale, release cadence, team growth).
> A 9+ year answer shows judgement: "Microservices are an organisational scaling tool first and a technical one second."

## How do you decide service boundaries? (Domain-Driven Design)
- Use **DDD bounded contexts**. Each context has its own ubiquitous language and model. For example "Product" means different things in Catalog, Inventory and Shipping.
- Find the contexts through **Event Storming** with domain experts, looking at business capabilities and subdomains (core, supporting, generic).
- **Aggregates** are consistency boundaries. One transaction should change one aggregate.
- **Signs of bad boundaries**: chatty synchronous calls between services, services that must always be deployed together (a distributed monolith), and shared databases.

## Explain the API Gateway pattern.
One entry point for clients. It handles **routing, authentication (JWT validation), rate limiting, SSL termination, request aggregation, CORS, caching and API versioning**.
- Options: Spring Cloud Gateway, **Azure API Management**, Kong, NGINX, Azure Application Gateway (L7 load balancer + WAF).
- **BFF (Backend for Frontend)**: a separate gateway per client type (web, mobile), shaped to what each needs.
- Keep **business logic out** of the gateway.

## Service discovery: client-side vs server-side?
- **Client-side**: the client asks a registry (Eureka, Consul) and load-balances itself (Spring Cloud LoadBalancer).
- **Server-side**: the client calls a stable name and the platform routes it. In **Kubernetes**, a Service's DNS name (`orders-svc.namespace.svc.cluster.local`) goes through kube-proxy to the pods. On Kubernetes you usually **don't need Eureka**.

## Synchronous vs asynchronous communication between services?
- **Synchronous** (REST, gRPC): simple request/response with immediate consistency. But it creates **temporal coupling** (both services must be up) and latency adds up along the chain.
- **Asynchronous** (Kafka, Azure Service Bus, RabbitMQ): loose coupling, buffering and resilience, and easy fan-out to many consumers. The costs are eventual consistency, harder tracing, and the need for idempotency and message ordering.
- **Rule of thumb**: queries that need an answer now are synchronous. **Commands and state-change notifications are asynchronous** through events. gRPC is a good fit for high-throughput internal calls.

## Explain the Circuit Breaker pattern (Resilience4j).
It stops calls to a failing dependency so failures don't cascade and exhaust threads.
- **CLOSED**: calls pass through and failures are counted over a sliding window.
- **OPEN**: once the failure rate exceeds a threshold (e.g. 50%), calls **fail fast** or go to a fallback, for a wait period.
- **HALF_OPEN**: a few trial calls are allowed. If they succeed the breaker goes back to CLOSED, otherwise back to OPEN.
- Combine it with **timeouts, retries with exponential backoff and jitter, bulkheads** (isolated thread pools or semaphores per dependency) and **rate limiters**.
```
@CircuitBreaker(name = "inventory", fallbackMethod = "stockFallback")
@Retry(name = "inventory")
@TimeLimiter(name = "inventory")
public CompletableFuture<Stock> getStock(String sku) { ... }

resilience4j.circuitbreaker.instances.inventory:
  slidingWindowSize: 20
  failureRateThreshold: 50
  waitDurationInOpenState: 30s
```
> Retry only **idempotent** operations. Retry storms can take down a service that is trying to recover.

## How do you handle distributed transactions? Explain the Saga pattern.
2PC/XA does not scale and does not fit microservices, where each service has its own DB, often a NoSQL store or a broker. A **Saga** is a sequence of **local transactions**. Each step publishes an event or command. If a step fails, **compensating transactions** undo the earlier steps.
- **Choreography**: services react to each other's events. There is no central coordinator. It works for simple flows, but becomes hard to follow as the flow grows.
- **Orchestration**: a central orchestrator (a state machine, Temporal, Camunda or Azure Durable Functions) tells each service what to do. The flow is explicit and easier to monitor.
- Example (orders): `OrderCreated` -> PaymentService charges -> `PaymentCompleted` -> InventoryService reserves stock -> if that fails, `InventoryFailed` -> **refund the payment** -> cancel the order.
- Sagas give no isolation, so handle anomalies with **semantic locks** (e.g. status PENDING), commutative updates and re-reading values.

## What is the Transactional Outbox pattern and why do you need it?
**The dual-write problem**: saving to the DB and publishing to Kafka are two separate systems. If one succeeds and the other fails, they become inconsistent.
- **Outbox**: in the **same local DB transaction**, write the business row **and** an `outbox` row holding the event.
- A separate relay publishes the outbox rows to Kafka. Either a **poller**, or better, **CDC with Debezium** reading the DB transaction log.
- This gives **at-least-once** delivery, so consumers must be **idempotent**.
- The mirror image is the **Inbox pattern**: consumers store processed message IDs to deduplicate.

## Explain CQRS and Event Sourcing.
- **CQRS**: separate the **write model** (commands, a normalised and validated domain) from the **read model** (queries, denormalised views such as Elasticsearch, Cosmos DB or a Redis projection). The two can scale separately. The read model is updated from events and is eventually consistent.
- **Event Sourcing**: store **every state change as an immutable event** instead of the current state. State is rebuilt by replaying events (use snapshots for speed). You get a full audit trail, time travel and replay into new projections.
- **Costs**: complexity, schema evolution of events, and eventual consistency. Use them for audit-heavy domains (banking, ledgers, orders), not for simple CRUD.

## How do you make APIs and consumers idempotent?
Retries and at-least-once delivery mean the **same request or message can arrive more than once**.
- The client sends an **Idempotency-Key** header (like Stripe). The server stores the key and its response, and returns the stored response for a repeated key.
- Consumers keep a `processed_messages` table (message ID with a unique constraint) or make **natural idempotent updates** (`SET status = 'PAID'` rather than `balance = balance - x`).
- Use DB unique constraints and upserts. PUT and DELETE are idempotent by definition. POST is not, unless you add a key.

## Database per service: how do you run queries that span services?
- Each service **owns its data**. No other service reads its tables directly.
- For cross-service queries: **API composition** (an aggregator calls several services), a **CQRS read model** built from events, or **data replication through events** (keep a local copy of the data you need).
- Reporting and analytics: stream events into a data lake or warehouse (e.g. Azure Synapse or Fabric).

## How do you implement observability in microservices?
The **three pillars**:
- **Logs**: structured JSON logs with a **correlation / trace ID** in every line (MDC). Centralise them in ELK or Azure Log Analytics.
- **Metrics**: RED (Rate, Errors, Duration) and USE (Utilisation, Saturation, Errors). Micrometer -> Prometheus -> Grafana, or Azure Monitor.
- **Traces**: distributed tracing with **OpenTelemetry** (W3C traceparent header). In Spring Boot 3 this is Micrometer Tracing. Export to Jaeger, Zipkin or **Application Insights**.
- Also: health checks, SLOs and SLIs with error budgets, and alerts on symptoms (latency, error rate) rather than causes.

## How do you version APIs and avoid breaking consumers?
- URI versioning (`/v1/orders`), header versioning or media-type versioning. URI versioning is the most practical.
- Prefer **backward-compatible changes**: add optional fields, never rename or remove fields, follow the tolerant-reader principle.
- Use **consumer-driven contract tests** (Pact) in CI, and announce deprecations with sunset headers.
- For events, use a **Schema Registry** with compatibility rules (BACKWARD or FULL).

## What is the Strangler Fig pattern? How would you migrate a monolith?
Gradually replace pieces of the monolith. Put a **facade or gateway** in front of it, route one capability at a time to the new service, and retire the old code.
1. Identify seams and bounded contexts. Start with a low-risk, high-value capability.
2. Add an anti-corruption layer that translates between the old and new models.
3. Split the data: sync with CDC or events, then move ownership to the new service.
4. Run in parallel and compare (dark launches, feature flags), then cut over and delete the old code.

## What other microservice patterns should you know?
- **Sidecar / Service Mesh** (Istio, Linkerd, Dapr): mTLS, retries, traffic shifting and telemetry without changing application code.
- **Bulkhead**: isolate resources per dependency so one failure doesn't drain everything.
- **Anti-Corruption Layer**: protect your domain model from legacy or external models.
- **Backends for Frontends**, **Aggregator**, **Ambassador**.
- **Health Check API**, **Externalised Configuration**, **Log Aggregation**.
- **Competing Consumers**, **Claim Check** (store a large payload in blob storage and send only a reference through the broker).

## How do you secure service-to-service communication?
- **mTLS** through a service mesh, or with certificates.
- **OAuth2 client credentials**, or **Azure Managed Identity**, with no secrets in code. Pass the user context along as a JWT (token exchange / on-behalf-of flow).
- Network policies (Kubernetes NetworkPolicy), private endpoints, and zero-trust principles.
- Secrets in Key Vault, rotated automatically.
