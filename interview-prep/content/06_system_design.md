# System Design

## How do you approach a system design interview? (Framework)
1. **Clarify requirements** (5 min). Functional: what does the system do? Non-functional: scale, latency, availability, consistency, durability, security, cost.
2. **Estimate** (back-of-the-envelope): DAU, QPS (average and peak), storage per year, bandwidth, read/write ratio.
3. **API design**: the key endpoints or events.
4. **Data model** and database choice (SQL vs NoSQL, and why).
5. **High-level design**: clients -> CDN -> load balancer / gateway -> services -> cache -> DB -> queues -> workers.
6. **Deep dive** into the bottlenecks: sharding, caching, hot keys, consistency, failure handling.
7. **Trade-offs, monitoring, security** and how the design evolves.
> Talk through your trade-offs out loud. Interviewers score your reasoning, not a "correct" diagram.

## Explain the CAP theorem and PACELC.
- **CAP**: during a **network Partition**, a distributed system must choose between **Consistency** (every read sees the latest write) and **Availability** (every request gets a response). Partitions are unavoidable, so the real choice is **CP or AP**.
- **CP** examples: ZooKeeper, etcd, HBase, and banking ledgers. **AP** examples: Cassandra, DynamoDB (by default), Cosmos DB with eventual consistency, and shopping carts.
- **PACELC**: if Partitioned, choose A or C; **E**lse (normal operation), choose between **L**atency and **C**onsistency.
- **Cosmos DB** offers five consistency levels: Strong, Bounded Staleness, **Session** (the default), Consistent Prefix and Eventual.

## SQL vs NoSQL: how do you choose?
- **SQL** (PostgreSQL, Azure SQL): ACID, joins, strong consistency, complex queries, a stable schema. Use it for financial data, orders and anything relational.
- **NoSQL**:
- **Key-value** (Redis): caches and sessions.
- **Document** (MongoDB, Cosmos DB): flexible schema, aggregate-shaped data.
- **Wide-column** (Cassandra): huge write throughput and time-series data.
- **Graph** (Neo4j): relationships and recommendations.
- **Search** (Elasticsearch): full text search.
- Scaling: SQL is usually scaled up plus read replicas, then sharded. NoSQL is built to scale out.
- Many systems are **polyglot**: pick the store per use case.

## How do you scale a database?
- **Indexing** and query optimisation first (check `EXPLAIN` plans, covering indexes, avoid `SELECT *`).
- **Read replicas** for heavy read traffic. Watch replication lag, and route read-your-own-writes queries to the primary.
- **Caching** (Redis) in front of the DB.
- **Vertical partitioning** (split tables or columns) and **sharding** (horizontal partitioning by shard key: hash, range or directory based).
- Choosing a **shard key**: high cardinality, even distribution, and it matches your query pattern. Avoid monotonically increasing keys with range sharding, because they create hot spots.
- **Consistent hashing** reduces data movement when nodes are added or removed (virtual nodes smooth the distribution).
- **Connection pooling** (HikariCP sizing, PgBouncer).

## Explain caching strategies and cache invalidation.
- **Cache-aside (lazy loading)**: the app reads the cache, and on a miss reads the DB and fills the cache. This is the most common strategy.
- **Read-through / Write-through**: the cache sits in front of the DB and writes go to both. Consistent, but writes are slower.
- **Write-behind**: writes go to the cache and are flushed to the DB asynchronously. Fast, but data can be lost.
- **Eviction**: LRU, LFU, TTL.
- **Problems and fixes**:
- **Cache stampede** (many misses at once): locking or single-flight, request coalescing, early probabilistic refresh.
- **Cache penetration** (queries for keys that don't exist): cache null results, or use a Bloom filter.
- **Hot keys**: local L1 caches, key replication.
- **Invalidation**: short TTLs plus event-driven eviction (a DB change event evicts the key).
- Layers: browser -> **CDN** (Azure Front Door) -> gateway -> app (Caffeine) -> distributed (Redis) -> DB.

## Design a URL shortener (like bit.ly).
- **Requirements**: 100M new URLs per month, a read:write ratio of 100:1, low-latency redirects, custom aliases, expiry, analytics.
- **Estimates**: about 40 writes/sec and about 4,000 reads/sec (plan for 10x peak). About 6B URLs over 5 years x 500 bytes = about 3 TB.
- **Key generation**: **Base62** of a unique ID (7 characters = 62^7, about 3.5 trillion). Get the IDs from a **distributed ID generator** (Snowflake, or pre-allocated ranges from a counter service in ZooKeeper or a DB) so there are no collisions. Hashing (MD5) plus collision checks also works.
- **Storage**: a key-value / NoSQL store (Cosmos DB, Cassandra, DynamoDB) keyed by the short code.
- **Read path**: CDN/edge -> Redis cache (the hot 20% of URLs) -> DB. Return **301** (cacheable, fewer hits to your servers) or **302** (so every click can be tracked).
- **Analytics**: publish click events to **Kafka** asynchronously, then stream-process them into an OLAP store.
- **Other points**: rate limiting, abuse / malware URL checks, and a TTL cleanup job.

## Design a rate limiter.
- **Algorithms**:
- **Token Bucket**: tokens refill at rate r and the bucket holds up to b. Allows bursts. This is the most common.
- **Leaky Bucket**: a smooth, constant outflow.
- **Fixed Window Counter**: simple, but allows bursts at window edges.
- **Sliding Window Log**: accurate, but uses a lot of memory.
- **Sliding Window Counter**: a good approximation of the log.
- **Where**: at the API gateway (APIM `rate-limit-by-key`, Spring Cloud Gateway's RedisRateLimiter) or in a service.
- **Distributed**: keep the counters in **Redis** with atomic **Lua scripts** or `INCR` + `EXPIRE`, keyed by user, API key or IP.
- **Response**: HTTP **429** with `Retry-After` and `X-RateLimit-Remaining` headers.
- **Failure mode**: decide whether to fail open or fail closed if Redis is down.

## Design a notification system (email / SMS / push).
- Services publish `NotificationRequested` events to **Kafka** or Service Bus.
- The **Notification service** validates the request, checks user preferences and opt-outs, renders templates, and deduplicates with an idempotency key.
- There is **one queue or topic per channel** (email, SMS, push). Workers call providers (SendGrid, Twilio, FCM/APNs, Azure Communication Services).
- **Retries with exponential backoff**, a **DLQ** for poison messages, and provider failover.
- **Rate limit** per user and per provider. Scheduling and quiet hours.
- Track delivery status (sent, delivered, opened) in a store, and expose it through an API.

## Design an e-commerce order and payment system.
- Services: Catalog, Cart, **Order**, **Payment**, **Inventory**, Shipping, Notification.
- **Checkout flow** as a **Saga**: Create Order (PENDING) -> Reserve Inventory -> Charge Payment (idempotency key with the payment provider) -> Confirm Order -> Ship. Compensations: release the stock, refund the payment.
- Use the **Outbox** pattern for reliable events, and make every consumer idempotent.
- **Inventory contention** (flash sales): reserve with a TTL. Use atomic decrements in Redis, then sync to the DB. Put a queue in front to smooth the traffic spike.
- **Read side**: order history through CQRS projections, search through Elasticsearch.
- Security: PCI-DSS means you **never store card data** (use tokenisation).

## Design a chat / messaging system (like WhatsApp).
- Persistent **WebSocket** connections to chat servers. A **connection registry** in Redis maps each user to a server.
- Message flow: sender -> chat server -> persisted to a store (Cassandra, partitioned by conversation ID and ordered by time) -> routed to the recipient's server -> delivered. If the recipient is offline, send a push notification and deliver on reconnect.
- **Ordering**: a per-conversation sequence number. **Delivery receipts**: sent, delivered, read.
- **Group chat**: fan-out on write for small groups and fan-out on read for very large ones.
- **Presence**: heartbeats with a TTL in Redis.
- **End-to-end encryption** (Signal protocol) if required.

## How do you design for high availability and disaster recovery?
- **Remove single points of failure**: multiple instances behind a load balancer, spread across **Availability Zones**.
- **Multi-region**: active-passive (cheaper, RTO in minutes) or active-active (complex, conflict resolution). Use Azure Front Door or Traffic Manager for global routing.
- Define **RTO** (recovery time objective) and **RPO** (recovery point objective), and choose the replication mode to match (async vs sync, geo-redundant storage).
- **Test it**: backups with restore drills, chaos engineering (Azure Chaos Studio), runbooks.
- **Graceful degradation**: feature flags, fallbacks, serving stale cache data.

## How do you generate unique IDs in a distributed system?
- **UUID v4**: random, with no coordination needed, but 128 bits long and it fragments B-tree indexes. **UUID v7** is time-ordered and index-friendly.
- **Snowflake**: 64 bits = timestamp (41) + machine ID (10) + sequence (12). Sortable by time, and gives millions of IDs per second. Watch for clock skew.
- **DB sequences with range allocation (hi/lo)**: each node takes a block of IDs at a time.

## Explain load balancing algorithms and L4 vs L7.
- **L4** (transport layer, e.g. Azure Load Balancer): routes by IP and port. Very fast, and cannot see content.
- **L7** (application layer, e.g. Application Gateway, NGINX, Front Door): routes by path, headers or cookies. Handles TLS termination, WAF and sticky sessions.
- **Algorithms**: round robin, weighted round robin, least connections, least response time, IP hash / consistent hashing (session affinity).
- Health checks remove unhealthy instances from rotation.

## How do you handle backpressure and traffic spikes?
- **Queue-based load leveling**: put a queue in front of workers and scale the workers on queue depth (**KEDA** on AKS).
- Rate limiting and load shedding (reject low-priority traffic first), and autoscaling (HPA on CPU or custom metrics).
- Bounded thread pools and queues so memory cannot blow up, plus circuit breakers.
- Pre-scale for known events (sales), and use a CDN for static content.
