# SQL & Relational Databases

## What are ACID properties? Explain each with an example.
- **Atomicity**: all or nothing. A money transfer debits A **and** credits B, or neither happens. This is implemented with an undo log / rollback.
- **Consistency**: a transaction moves the DB from one valid state to another, respecting constraints (PK, FK, CHECK, UNIQUE).
- **Isolation**: concurrent transactions don't see each other's partial work. How strictly depends on the isolation level.
- **Durability**: once committed, data survives a crash. This is implemented with the **write-ahead log (WAL / redo log)**, which is flushed to disk before the commit is acknowledged.

## Explain the types of JOINs.
- **INNER JOIN**: only rows that match in both tables.
- **LEFT (OUTER) JOIN**: all rows from the left table, with NULLs where the right side has no match.
- **RIGHT JOIN**: the mirror of LEFT. **FULL OUTER JOIN**: all rows from both sides.
- **CROSS JOIN**: the Cartesian product (every combination).
- **SELF JOIN**: a table joined to itself, e.g. an employee and their manager.
- **Anti-join** (rows with no match): `LEFT JOIN ... WHERE right.id IS NULL`, or `NOT EXISTS`.
```
-- Customers who never placed an order
SELECT c.id, c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL;

-- Employee with manager name (self join)
SELECT e.name AS employee, m.name AS manager
FROM employees e LEFT JOIN employees m ON e.manager_id = m.id;
```

## WHERE vs HAVING? What is the logical order of SQL execution?
- **WHERE** filters **rows before grouping**. **HAVING** filters **groups after aggregation**. HAVING can use aggregates such as `COUNT(*) > 5`.
- **Logical order**: FROM / JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT / OFFSET.
- This explains why a column alias from SELECT usually **cannot** be used in WHERE, but **can** be used in ORDER BY.
```
SELECT dept_id, COUNT(*) AS headcount, AVG(salary) AS avg_sal
FROM employees
WHERE status = 'ACTIVE'
GROUP BY dept_id
HAVING COUNT(*) > 10
ORDER BY avg_sal DESC;
```

## Find the Nth highest salary. (Classic question, three ways.)
```
-- 1. Window function (best: handles ties, easy to read)
SELECT salary FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rnk
    FROM employees
) t WHERE rnk = 3;

-- 2. OFFSET / LIMIT (PostgreSQL, MySQL)
SELECT DISTINCT salary FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 2;

-- 3. Correlated subquery (portable, but slow on large tables)
SELECT DISTINCT salary FROM employees e1
WHERE 2 = (SELECT COUNT(DISTINCT salary) FROM employees e2 WHERE e2.salary > e1.salary);

-- Nth highest salary PER DEPARTMENT
SELECT * FROM (
    SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) AS rnk
    FROM employees e
) t WHERE rnk = 2;
```

## Explain window functions. ROW_NUMBER vs RANK vs DENSE_RANK?
A window function computes a value **across a set of related rows without collapsing them** (unlike GROUP BY). Syntax: `func() OVER (PARTITION BY ... ORDER BY ... ROWS BETWEEN ...)`.
- For salaries 100, 100, 90: **ROW_NUMBER** gives 1, 2, 3 (always unique). **RANK** gives 1, 1, 3 (leaves gaps). **DENSE_RANK** gives 1, 1, 2 (no gaps).
- **LAG / LEAD**: the previous or next row's value (month-over-month change).
- **SUM / AVG OVER**: running totals and moving averages. Also **NTILE**, **FIRST_VALUE** and **LAST_VALUE**.
```
-- Running total and change from previous month
SELECT month, revenue,
       SUM(revenue) OVER (ORDER BY month) AS running_total,
       revenue - LAG(revenue) OVER (ORDER BY month) AS change
FROM monthly_sales;
```

## How do you find and delete duplicate rows?
```
-- Find duplicates
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;

-- Delete duplicates, keeping the lowest id (PostgreSQL / SQL Server style)
WITH ranked AS (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn
    FROM users
)
DELETE FROM users WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
-- Then prevent it from happening again:
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
```

## What are CTEs and recursive CTEs?
A **CTE** (`WITH` clause) is a named temporary result set. It makes complex queries readable and can be referenced several times. A **recursive CTE** walks hierarchies: org charts, category trees, bill of materials.
```
-- All reports under manager 1, at any depth
WITH RECURSIVE org AS (
    SELECT id, name, manager_id, 1 AS level FROM employees WHERE id = 1
    UNION ALL
    SELECT e.id, e.name, e.manager_id, o.level + 1
    FROM employees e JOIN org o ON e.manager_id = o.id
)
SELECT * FROM org;
```

## Subquery vs JOIN vs EXISTS? IN vs EXISTS?
- A **correlated subquery** runs once per outer row, which can be slow. Modern optimisers often rewrite it as a join.
- **EXISTS** stops at the first match and is usually best for "does a related row exist?" checks.
- **NOT IN is a trap**: if the subquery returns any **NULL**, `NOT IN` returns **no rows**. Use `NOT EXISTS` instead.
- **UNION** removes duplicates (so it sorts or hashes). **UNION ALL** keeps them and is faster. Use UNION ALL when duplicates are impossible or acceptable.

## DELETE vs TRUNCATE vs DROP?
- **DELETE**: DML. Removes rows (you can add WHERE), logs each row, fires triggers, and can be rolled back.
- **TRUNCATE**: DDL. Removes all rows quickly by deallocating pages. Minimal logging, resets identity counters, no row triggers. Can be rolled back in PostgreSQL and SQL Server inside a transaction, but not in MySQL or Oracle.
- **DROP**: removes the table itself (structure, data, indexes, constraints).

## How do indexes work? Clustered vs non-clustered?
- Most indexes are **B+ trees**: balanced, sorted, with O(log n) lookup, range scans and ordering. Leaf pages are linked, which makes range scans fast.
- **Clustered index**: the table rows **are stored in index order**, so there is only one per table. In SQL Server and MySQL InnoDB it is usually the primary key.
- **Non-clustered (secondary) index**: a separate structure that stores key -> row pointer (or the PK in InnoDB). A lookup may need an extra **key lookup / bookmark lookup** to fetch the other columns.
- **Covering index**: contains every column the query needs (`INCLUDE` columns), so it avoids the lookup completely.
- Other types: **Hash** (equality only), **GIN / GiST** (PostgreSQL full-text, JSONB, geospatial), **bitmap** (Oracle, low cardinality), **partial / filtered** indexes (`WHERE status = 'ACTIVE'`).
- **The cost**: every index slows INSERT, UPDATE and DELETE and uses storage. Index for your real query patterns, not for every column.

## What is a composite index and the leftmost prefix rule?
An index on `(last_name, first_name, city)` is sorted by last_name first, then first_name, then city.
- It helps queries filtering on `last_name`, on `last_name + first_name`, or on all three.
- It does **not** help a query that filters only on `first_name` or `city`, because the leftmost column is missing.
- **Column order**: put equality filters first and range filters (`>`, `BETWEEN`) last. Put more selective columns earlier when that fits the queries.

## Why might a query NOT use an index?
- A function on the indexed column: `WHERE UPPER(email) = ...` or `WHERE YEAR(created_at) = 2025`. Fix it with a function-based index or rewrite the condition as a range.
- **Implicit type conversion**: comparing a VARCHAR column with a number.
- A leading wildcard: `LIKE '%abc'`. (`LIKE 'abc%'` can use the index.)
- Low selectivity: the optimiser chooses a full scan when most rows match anyway.
- `OR` across different columns, and stale **statistics** (run `ANALYZE` / update statistics).
- Missing the leftmost column of a composite index.

## How do you optimise a slow SQL query?
1. Get the **execution plan**: `EXPLAIN ANALYZE` (PostgreSQL), `EXPLAIN` (MySQL), the actual execution plan (SQL Server).
2. Look for **full table scans**, bad row estimates, nested loops over large sets, sorts that spill to disk, and key lookups.
3. Add or adjust indexes (composite, covering), and make the conditions **sargable** (able to use an index).
4. Select only the columns you need (no `SELECT *`), and paginate with **keyset pagination** (`WHERE id > :lastId LIMIT 50`) instead of a large OFFSET.
5. Fix the N+1 pattern in the application, batch inserts, and keep transactions short.
6. Denormalise, add materialised views, partition large tables, or cache when it's justified.

## Explain normalization (1NF, 2NF, 3NF, BCNF). When do you denormalize?
- **1NF**: atomic values, no repeating groups (no "phone1, phone2" columns and no comma-separated lists).
- **2NF**: 1NF, and every non-key column depends on the **whole** primary key (no partial dependency on part of a composite key).
- **3NF**: 2NF, and **no transitive dependency** (non-key columns depend only on the key). For example, don't store `dept_name` in employees when `dept_id` already determines it.
- **BCNF**: every determinant is a candidate key (a stricter 3NF).
- **Denormalize** for read-heavy workloads, reporting, and to avoid expensive joins: star schemas in warehouses, cached totals, read models in CQRS. The price is duplicated data that must be kept in sync.

## Explain concurrency anomalies and isolation levels in the database.
- **Dirty read**: reading uncommitted data. **Non-repeatable read**: the same row read twice gives different values. **Phantom read**: the same query returns new rows. **Lost update**: two transactions overwrite each other's change.
- **READ COMMITTED** prevents dirty reads. **REPEATABLE READ** also prevents non-repeatable reads. **SERIALIZABLE** prevents everything.
- **MVCC** (PostgreSQL, Oracle, MySQL InnoDB): readers see a **snapshot** and don't block writers, and writers don't block readers. Old row versions are cleaned up later (PostgreSQL VACUUM).
- Prevent lost updates with `SELECT ... FOR UPDATE`, optimistic locking (a version column), or atomic updates: `UPDATE account SET balance = balance - 100 WHERE id = 1 AND balance >= 100`.

## What causes database deadlocks and how do you handle them?
Two transactions lock rows in **opposite order** and each waits for the other. The DB detects the cycle and kills one of them (the victim).
- **Prevention**: access tables and rows in a consistent order, keep transactions short, add the right indexes (without them, updates lock more rows), and use lower isolation where it is safe.
- **Handling**: catch the deadlock error and **retry** the transaction with backoff. In Spring, use `@Retryable` on `DeadlockLoserDataAccessException` / `CannotAcquireLockException`.

## What are views, materialized views, stored procedures and triggers?
- **View**: a saved query. It simplifies access and can restrict columns for security. Normal views store no data.
- **Materialized view**: stores the **result** physically and is refreshed on a schedule or on demand. Fast reads for reports, but the data can be stale.
- **Stored procedure**: logic that runs inside the DB. Fewer round trips, but harder to version, test and scale. In microservices, keep business logic in the application.
- **Trigger**: runs automatically on INSERT, UPDATE or DELETE (audit columns, history tables). Use it sparingly, because hidden side effects surprise developers.

## What is database partitioning and how is it different from sharding?
- **Partitioning**: splits one large table into parts **inside the same DB server**, by **range** (dates), **list** (region) or **hash**. Queries touch only the relevant partitions (**partition pruning**). Old data can be archived quickly by dropping a partition.
- **Sharding**: spreads data across **multiple DB servers**, each holding a subset. It scales writes and storage, but makes cross-shard joins and transactions and rebalancing hard.
- Tools: Citus (PostgreSQL), Vitess (MySQL), Azure SQL Hyperscale, Cosmos DB's built-in partitioning.

## How do you manage database schema changes in microservices?
- Use **Flyway** or **Liquibase**: versioned migration scripts checked into git and run at startup or in the pipeline.
- **Zero-downtime changes (expand and contract)**: add the new column (nullable) -> deploy code that writes to both columns -> backfill -> switch reads -> remove the old column in a later release.
- Never rename or drop a column in the same release that stops using it. Large table changes need online tools (gh-ost, pt-online-schema-change) or batched backfills.

## Practical SQL questions to practise.
```
-- Department with the highest average salary
SELECT dept_id, AVG(salary) avg_sal FROM employees
GROUP BY dept_id ORDER BY avg_sal DESC LIMIT 1;

-- Employees earning more than their manager
SELECT e.name FROM employees e JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;

-- Top 3 products by revenue in each category
SELECT * FROM (
  SELECT p.category, p.name, SUM(oi.qty * oi.price) revenue,
         ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY SUM(oi.qty * oi.price) DESC) rn
  FROM order_items oi JOIN products p ON p.id = oi.product_id
  GROUP BY p.category, p.name
) t WHERE rn <= 3;

-- Users who logged in on 3 consecutive days
SELECT DISTINCT user_id FROM (
  SELECT user_id, login_date,
         login_date - (ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date))::int AS grp
  FROM (SELECT DISTINCT user_id, login_date FROM logins) d
) t GROUP BY user_id, grp HAVING COUNT(*) >= 3;

-- Monthly active users
SELECT DATE_TRUNC('month', login_date) AS month, COUNT(DISTINCT user_id) AS mau
FROM logins GROUP BY 1 ORDER BY 1;
```

## How do you size and tune a JDBC connection pool (HikariCP)?
- **More connections is not faster**. The DB can only run about (cores x 2 + effective spindles) queries in parallel. A small pool (10-20) per instance is typical.
- **Total connections = pool size x number of pods**. With 50 pods x 20 connections = 1,000 connections, which can exceed the DB's limit. Use PgBouncer, or reduce the pool size.
- Key settings: `maximumPoolSize`, `connectionTimeout` (fail fast), `maxLifetime` (shorter than the DB or firewall idle timeout), and `leakDetectionThreshold`.
- Watch the metrics: active and pending connections, and acquire time.

# NoSQL Databases

## What is NoSQL and what types exist?
NoSQL ("not only SQL") databases give up some relational features (joins, fixed schema, sometimes strong consistency) in exchange for **horizontal scale, flexible schemas and high performance** for specific access patterns.
- **Key-value**: Redis, DynamoDB, Azure Cache for Redis. Very fast lookups by key. Caches, sessions, rate limits, leaderboards.
- **Document**: MongoDB, Cosmos DB (NoSQL API), Couchbase. JSON documents with nested data, flexible schema. Catalogs, user profiles, content.
- **Wide-column**: Cassandra, HBase, ScyllaDB, Cosmos DB (Cassandra API). Massive write throughput. Time series, IoT, messaging, event logs.
- **Graph**: Neo4j, Cosmos DB (Gremlin API), Amazon Neptune. Relationships: social networks, fraud rings, recommendations.
- **Search**: Elasticsearch / OpenSearch, Azure AI Search. Full-text search, relevance ranking, log analytics.
- **Time-series**: InfluxDB, TimescaleDB, Azure Data Explorer. Metrics and sensor data.

## When would you choose NoSQL over SQL?
- **Choose NoSQL** when you need huge scale or throughput beyond one server, a flexible or evolving schema, low-latency reads by key, global distribution, or data that is naturally shaped as aggregates (a document).
- **Choose SQL** when you need complex queries and joins, multi-row ACID transactions, strong integrity constraints, ad-hoc reporting, or when the data is highly relational (finance, orders, inventory).
- The key difference: in SQL you **model the data, then write queries**. In NoSQL you **list the queries first, then model the data to serve them** (query-driven design).
> Senior answer: "It is not either/or. We used PostgreSQL for orders and payments, Redis for caching and rate limits, Cosmos DB for the product catalog and Elasticsearch for search: polyglot persistence."

## What is BASE and eventual consistency?
- **BASE**: **B**asically **A**vailable, **S**oft state, **E**ventual consistency. It is the counterpart of ACID for distributed stores that choose availability.
- **Eventual consistency**: if no new writes occur, all replicas **converge** to the same value eventually. Reads may briefly return stale data.
- Stronger options in between: **read-your-writes**, **monotonic reads**, **session consistency** (Cosmos DB's default), **bounded staleness**.
- Conflict resolution for concurrent writes: last-writer-wins (by timestamp), vector clocks, CRDTs, or custom merge logic.

## How do you model data in a document database (MongoDB / Cosmos DB)?
- **Embed** data that is read together and owned by the parent (order + order lines, user + addresses). One read, atomic updates on a single document.
- **Reference** (store an ID) when the related data is large, unbounded (comments on a viral post), shared by many parents, or changes on its own.
- Avoid **unbounded arrays** and huge documents (MongoDB's limit is 16 MB, Cosmos DB's is 2 MB).
- Denormalize for reads (store `customerName` inside the order) and keep copies in sync with events or the change feed.
- Patterns: bucket (time series grouped by hour), subset (embed only the latest 10 reviews), computed (keep pre-aggregated totals), schema versioning (a `schemaVersion` field).
```
// Order document: lines embedded, customer referenced plus a denormalized name
{
  "id": "ord-1001", "customerId": "c-42", "customerName": "Asha",
  "status": "PAID", "total": 149.97,
  "lines": [ { "sku": "SKU-9", "qty": 3, "price": 49.99 } ],
  "createdAt": "2026-09-01T10:15:00Z"
}
```

## How do you choose a partition key in Cosmos DB (or a shard key in general)?
- The partition key decides **how data is spread** across physical partitions and **which queries are cheap**.
- A good key has **high cardinality** (many distinct values), spreads **reads and writes evenly** (no hot partition), and appears in the **WHERE clause of most queries**, so they are single-partition queries.
- Bad keys: `status`, `country` or `date` (few values, or all of today's writes go to one partition). Common good keys: `tenantId`, `userId`, `deviceId`, or **hierarchical partition keys** (tenantId -> userId) for multi-tenant apps.
- Cross-partition queries fan out to every partition and cost more RU. In Cosmos DB, a logical partition holds at most 20 GB, and **the key cannot be changed** later without migrating the data.

## Explain Cosmos DB key concepts: RU/s, consistency levels and change feed.
- **Request Units (RU/s)**: one currency for CPU, memory and I/O. A 1 KB point read by id plus partition key costs about **1 RU**. Queries and writes cost more. Provisioned (manual or autoscale) or serverless throughput. Exceeding it returns **HTTP 429**, and the SDK retries automatically.
- **Five consistency levels**: Strong, Bounded Staleness, **Session** (the default: read your own writes within a session), Consistent Prefix, Eventual. Stronger levels cost more RU and add latency.
- **Change feed**: an ordered log of changes per partition. Use it to build CQRS read models, sync to search, fire events (via Azure Functions), or run an outbox-like flow.
- **Multi-region writes**, automatic indexing (customise the indexing policy to cut RU cost), TTL per item, and APIs for NoSQL, MongoDB, Cassandra, Gremlin and Table.

## How does Cassandra work? What is its data model?
- **Masterless ring**: every node is equal. Data is placed by **consistent hashing** of the **partition key**, and replicated N times (the replication factor).
- **Primary key = partition key + clustering columns**. The partition key picks the node, and clustering columns **sort rows inside the partition**.
- The write path is very fast: commit log -> memtable -> flushed to immutable **SSTables**. Compaction merges them. Deletes write **tombstones**.
- **Tunable consistency**: `ONE`, `QUORUM`, `ALL`. If **R + W > RF** (e.g. QUORUM reads and QUORUM writes with RF = 3), you get strong consistency.
- **Model one table per query**. There are no joins, so data is duplicated across tables on purpose.
```
-- Messages of a conversation, newest first
CREATE TABLE messages_by_conversation (
    conversation_id uuid,
    sent_at timeuuid,
    sender_id uuid,
    body text,
    PRIMARY KEY ((conversation_id), sent_at)
) WITH CLUSTERING ORDER BY (sent_at DESC);
```

## What is Redis and what are its main use cases and data structures?
Redis is an **in-memory** key-value store with rich data structures. It is very fast (sub-millisecond) and runs commands on a single thread, so each command is **atomic**.
- **Strings**: cache values, counters (`INCR`), distributed locks (`SET key val NX PX 30000`).
- **Hashes**: objects and sessions. **Lists**: simple queues. **Sets**: unique items, tags.
- **Sorted sets (ZSET)**: leaderboards, priority queues, sliding-window rate limiting.
- **Streams**: a log with consumer groups (a light alternative to Kafka). **Pub/Sub**: fire-and-forget broadcast.
- **HyperLogLog** (approximate unique counts), **Bitmaps**, **Geo**.
- **Persistence**: RDB snapshots and/or AOF (append-only file). **Scaling**: replicas plus Sentinel for failover, or **Redis Cluster** (16,384 hash slots split across the primaries).
- **Eviction policies**: `allkeys-lru`, `volatile-ttl`, `noeviction`, and others. Always set a TTL on cache keys.
```
// Leaderboard with a sorted set
ZADD game:scores 1500 "asha"
ZINCRBY game:scores 50 "ravi"
ZREVRANGE game:scores 0 9 WITHSCORES   // top 10
```

## How do you implement a distributed lock? What are the pitfalls?
- Redis: `SET lock:order:42 <uniqueToken> NX PX 30000` acquires the lock with an expiry. Release it with a **Lua script** that deletes the key only if the token matches, so you never delete someone else's lock.
- Libraries: **Redisson** (`RLock` with a watchdog that extends the lease), ShedLock (scheduled jobs in a cluster), or DB-based locks.
- **Pitfalls**: a GC pause or slow process can outlive the lease, so two holders exist at once. Use **fencing tokens** (a number that increases with every lock grant, checked by the storage layer) when correctness is critical. Redlock across several Redis nodes is debated. For strict guarantees, use ZooKeeper, etcd or a DB row lock.

## How does Elasticsearch work and when would you use it?
- A distributed **search engine** built on Lucene. Documents are stored in an **inverted index** (term -> list of documents), which makes full-text search fast.
- An index is split into **primary shards** (fixed at creation) plus **replica shards**, spread across nodes.
- Text is **analyzed** (tokenised, lowercased, stemmed) using analyzers. Relevance scoring uses BM25.
- Use it for: product search with filters (facets), autocomplete, log analytics (ELK), geo search.
- **Not a primary database**: it is near-real-time (about a 1 s refresh), has no ACID transactions, and mapping changes need a reindex. Keep the source of truth in SQL/NoSQL and sync with CDC, events or the change feed.

## How do you keep data consistent between a SQL database and a NoSQL / search store?
- **Avoid dual writes** from the application (one write can fail, leaving the stores inconsistent).
- Use **CDC** (Debezium reading the DB log) -> Kafka -> a sink connector or consumer that updates Elasticsearch or Redis.
- Or use the **Transactional Outbox** pattern, or the source store's change feed (Cosmos DB change feed -> Azure Function -> search index).
- Make the updates **idempotent** and version-aware (ignore older versions arriving late). Provide a **full reindex** job for recovery.

## Rapid-fire SQL / NoSQL questions.
- **Primary key vs unique key?** A primary key is unique and NOT NULL, with only one per table (often clustered). A unique key allows NULLs (how many depends on the DB), and a table can have many.
- **What is a foreign key?** It enforces referential integrity between tables. Options: `ON DELETE CASCADE` / `SET NULL`. Index your FK columns.
- **CHAR vs VARCHAR?** CHAR is fixed-length and padded. VARCHAR is variable-length.
- **COUNT(*) vs COUNT(col)?** `COUNT(*)` counts all rows. `COUNT(col)` skips NULLs.
- **What is a surrogate key vs a natural key?** A generated ID (identity, UUID) vs a business value (email, PAN). Prefer surrogate keys, and put a unique constraint on the natural key.
- **OLTP vs OLAP?** Many small transactions (row store, normalised) vs large analytical queries (column store, star schema: Synapse, Fabric, Snowflake).
- **Does MongoDB support transactions?** Yes. Multi-document ACID transactions since 4.0 (replica sets) and 4.2 (sharded clusters). Single-document writes are always atomic.
- **What is a hot partition?** One partition receiving a disproportionate share of traffic, which throttles the whole workload. Fix it with a better key, a synthetic suffix on the key (write sharding), or caching.
- **Spring Data support?** Spring Data JPA (SQL), Spring Data MongoDB, Spring Data Redis, Spring Data Cassandra, Spring Data Elasticsearch, and Spring Cloud Azure's Cosmos DB starter all share the same repository abstraction.
