MODULE = {
    "title": "Redis Caching",
    "intro": "A database query takes milliseconds; a Redis lookup takes well under one. Caching is the cheapest "
             "way to make a system fast, and it is also the easiest way to serve stale data or take down your "
             "database when the cache fails. This module covers both sides.",
    "topics": [
        # ------------------------------------------------------------------ 4.1
        {
            "title": "Redis Fundamentals & Data Structures",
            "blocks": [
                ("analogy", "The database is a **warehouse** across town; Redis is the **shelf behind the "
                            "counter**. Popular items sit on the shelf for instant pickup. The shelf is small "
                            "(RAM), so items have expiry labels (TTL) and the shelf may be cleared."),
                ("ul", ["**In-memory** key-value store: sub-millisecond reads.",
                        "Executes commands on a **single thread**, so each command is atomic (`INCR` never races).",
                        "**Persistence** is optional: RDB snapshots and/or AOF append log.",
                        "**TTL** on any key: `SET session:abc ... EX 1800`."]),
                ("table", [["Type", "Example command", "Backend use case"],
                           ["String", "`SET product:42 '{json}' EX 600`", "Cached objects, counters (`INCR`)"],
                           ["Hash", "`HSET cart:u7 sku123 2`", "Shopping cart, user session fields"],
                           ["List", "`LPUSH recent:u7 sku9` + `LTRIM 0 9`", "Recently viewed items"],
                           ["Set", "`SADD online-users u7`", "Unique visitors, tags"],
                           ["Sorted Set", "`ZINCRBY bestsellers 1 sku9`", "Leaderboards, top-N products"],
                           ["Key + `SET NX`", "`SET lock:order:1 me NX EX 10`", "Distributed lock (simple)"]],
                 [0.16, 0.42, 0.42]),
                ("code", """
# Rate limiting: max 100 requests per minute per user (fixed window)
INCR   rate:u7:202610211405        → 1, 2, 3 ...
EXPIRE rate:u7:202610211405 60      (set on first hit)
if value > 100 → HTTP 429
"""),
                ("h", "Spring Boot setup"),
                ("code", """
<!-- pom.xml -->
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

# application.yml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      timeout: 200ms          # fail fast: a slow cache is worse than no cache
"""),
                ("warn", "Running `KEYS *` in production. It scans every key while blocking the single thread, "
                         "so all clients freeze. Use `SCAN` with a cursor instead. The same goes for huge values "
                         "(\"big keys\") and `DEL` on giant collections (use `UNLINK`)."),
                ("key", ["Redis = fast, in-memory, single-threaded command execution, rich data types.",
                         "Always set a TTL on cache keys.",
                         "Avoid blocking commands (`KEYS`, big-key deletes) in production."]),
            ],
            "questions": [
                "Which Redis data structure would you use for a \"Top 10 best-selling products today\" widget, "
                "and which commands?",
            ],
            "answer": "A **Sorted Set** per day: `ZINCRBY bestsellers:2026-10-21 <qty> <sku>` on each sale, "
                      "`ZREVRANGE bestsellers:2026-10-21 0 9 WITHSCORES` to read the top 10, and `EXPIRE` the "
                      "key after a couple of days.",
        },
        # ------------------------------------------------------------------ 4.2
        {
            "title": "The Cache-Aside Pattern",
            "blocks": [
                ("analogy", "A **librarian with a desk drawer**. Someone asks for a book: she checks the drawer "
                            "first (cache). If it's not there, she walks to the stacks (database), hands over the "
                            "book and drops a copy in the drawer for next time. When a book is revised, she "
                            "**throws out the drawer copy** rather than trying to edit it."),
                ("code", """
 READ                                         WRITE
 ────                                         ─────
 App ──1. GET product:42──► Redis             App ──1. UPDATE──► PostgreSQL
  │◄──── hit? return ─────┘                    │
  │ miss                                       └──2. DEL product:42──► Redis
  ├──2. SELECT ... ─────► PostgreSQL
  └──3. SET product:42 (TTL) ─► Redis          (next read repopulates the cache)
"""),
                ("h", "With Spring Cache annotations"),
                ("code", """
@Configuration
@EnableCaching
public class CacheConfig {
    @Bean
    RedisCacheManager cacheManager(RedisConnectionFactory cf) {
        var json = RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer());
        var defaults = RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10))
                .disableCachingNullValues()
                .serializeValuesWith(json);
        return RedisCacheManager.builder(cf).cacheDefaults(defaults).build();
    }
}

@Service
@RequiredArgsConstructor
public class ProductService {
    private final ProductRepository repo;

    @Cacheable(cacheNames = "products", key = "#id")    // cache-aside read
    public ProductDto get(String id) {
        return repo.findById(id).map(ProductDto::from).orElseThrow();
    }

    @Transactional
    @CacheEvict(cacheNames = "products", key = "#id")   // evict after update
    public ProductDto updatePrice(String id, Money price) { ... }
}
"""),
                ("h", "Why delete instead of update the cache?"),
                ("p", "Two concurrent writers can update the DB in order A→B but the cache in order B→A, leaving "
                      "the cache permanently stale. Deleting is idempotent: the next read loads the truth. The "
                      "TTL is your safety net for any remaining race."),
                ("warn", "Caching **JPA entities** directly. Lazy-loaded relations blow up on deserialization "
                         "(`LazyInitializationException`) or pull half the database into Redis. Cache small, "
                         "immutable **DTOs/records** instead."),
                ("key", ["Read: cache → miss → DB → populate with TTL.",
                         "Write: update DB, then **evict** the key.",
                         "Cache DTOs, use JSON serialization, always set TTLs."]),
            ],
            "questions": [
                "Why should the cache eviction happen *after* the DB transaction commits, not before? What "
                "could go wrong otherwise?",
            ],
            "answer": "If you evict first, a concurrent reader may miss the cache, read the **old** value from "
                      "the DB (not yet committed) and re-cache it. The cache then stays stale until TTL. "
                      "Evicting after commit (or evicting twice: before and after, the \"delayed double "
                      "delete\") closes that window.",
        },
        # ------------------------------------------------------------------ 4.3
        {
            "title": "Cache Failure Modes: Avalanche, Penetration, Breakdown",
            "blocks": [
                ("analogy", "The cache is a **dam** protecting a village (the database). **Avalanche**: the whole "
                            "dam opens at once. **Penetration**: water seeps through a hole the dam doesn't cover "
                            "(requests for things that don't exist). **Breakdown**: one critical gate fails and "
                            "a torrent hits one spot (a single hot key expires)."),
                ("table", [["Failure", "Cause", "Fixes"],
                           ["**Avalanche**", "Many keys expire at the same moment (all loaded at startup with "
                            "TTL=10 min), or Redis goes down",
                            "Add random **jitter** to TTLs; Redis HA (Sentinel / Cluster); circuit breaker + "
                            "rate limit on DB fallback"],
                           ["**Penetration**", "Requests for keys that exist in **neither** cache nor DB "
                            "(`/products/-1`, bots), so every request hits the DB",
                            "Validate input; **cache empty results** briefly; **Bloom filter** of valid IDs"],
                           ["**Breakdown** (stampede)", "One **hot key** expires; thousands of concurrent "
                            "misses all query the DB to rebuild it",
                            "**Mutex** so one thread rebuilds; logical expiry / refresh-ahead; never expire hot keys"]],
                 [0.17, 0.43, 0.40]),
                ("h", "Fix 1: TTL jitter (avalanche)"),
                ("code", """
Duration ttl = Duration.ofMinutes(10)
        .plusSeconds(ThreadLocalRandom.current().nextInt(0, 120));   // spread expiry over 2 min
redis.opsForValue().set(key, value, ttl);
"""),
                ("h", "Fix 2: cache the \"not found\" (penetration)"),
                ("code", """
private static final String NULL_MARKER = "__NULL__";

public Optional<ProductDto> find(String id) {
    String cached = redis.opsForValue().get("product:" + id);
    if (NULL_MARKER.equals(cached)) return Optional.empty();          // known miss, skip DB
    if (cached != null) return Optional.of(read(cached));

    Optional<ProductDto> fromDb = repo.findById(id).map(ProductDto::from);
    redis.opsForValue().set("product:" + id,
            fromDb.map(this::write).orElse(NULL_MARKER),
            fromDb.isPresent() ? Duration.ofMinutes(10) : Duration.ofMinutes(1));
    return fromDb;
}
"""),
                ("h", "Fix 3: mutex rebuild (breakdown)"),
                ("code", """
public ProductDto getHot(String id) {
    String key = "product:" + id;
    for (int attempt = 0; attempt < 50; attempt++) {
        String cached = redis.opsForValue().get(key);
        if (cached != null) return read(cached);

        String lockKey = "lock:" + key, token = UUID.randomUUID().toString();
        Boolean locked = redis.opsForValue().setIfAbsent(lockKey, token, Duration.ofSeconds(5));
        if (Boolean.TRUE.equals(locked)) {
            try {
                ProductDto dto = ProductDto.from(repo.findById(id).orElseThrow());
                redis.opsForValue().set(key, write(dto), Duration.ofMinutes(10));
                return dto;
            } finally {
                // release only if we still own it (use a Lua script for atomic check-and-delete)
                if (token.equals(redis.opsForValue().get(lockKey))) redis.delete(lockKey);
            }
        }
        sleepQuietly(50);   // someone else is rebuilding; wait briefly and re-check the cache
    }
    throw new ServiceUnavailableException("cache rebuild timed out");
}
"""),
                ("warn", "Assuming the cache is always up. If Redis is down and every request falls through to "
                         "Postgres, the DB collapses too. Set a short Redis **timeout**, wrap calls in a **circuit "
                         "breaker** (Module 5) and decide deliberately: degrade, serve stale, or rate-limit."),
                ("key", ["Avalanche → jitter TTLs + HA. Penetration → cache nulls / Bloom filter.",
                         "Breakdown → one rebuilder (mutex) or refresh-ahead for hot keys.",
                         "Design for Redis being down: timeouts and circuit breakers."]),
            ],
            "questions": [
                "At midnight, a script warms the cache with 1M product keys, all with TTL = 24h. What happens "
                "the next midnight, which failure mode is it, and how do you fix it in one line of code?",
            ],
            "answer": "All 1M keys expire within seconds of each other, so a wave of misses hits Postgres: a "
                      "**cache avalanche**. Fix: add jitter, e.g. "
                      "`Duration.ofHours(24).plusMinutes(random.nextInt(0, 120))`, so expiries spread over two hours.",
        },
    ],
}
