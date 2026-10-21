MODULE = {
    "title": "Spring Boot Core & Resiliency",
    "intro": "Spring Boot feels like magic until it misbehaves. This module removes the magic: how beans are "
             "wired, how auto-configuration decides what to create, why `@Transactional` sometimes silently "
             "does nothing, and how Resilience4j keeps one slow service from taking down the rest.",
    "topics": [
        # ------------------------------------------------------------------ 5.1
        {
            "title": "IoC, Dependency Injection & Auto-Configuration",
            "blocks": [
                ("analogy", "**Inversion of Control** is a **hotel**: you don't build your own bed or hire your "
                            "own cleaner; you declare what you need and the hotel provides it. "
                            "**Auto-configuration** is a **smart hotel** that sees you brought a surfboard and "
                            "automatically books you a beach locker, unless you've already booked one yourself."),
                ("h", "Constructor injection (the right way)"),
                ("code", """
@Service
public class OrderService {
    private final OrderRepository orders;          // final → immutable, never null
    private final PaymentClient payments;

    public OrderService(OrderRepository orders, PaymentClient payments) {   // single ctor: no @Autowired needed
        this.orders = orders;
        this.payments = payments;
    }
}
// Testable without Spring: new OrderService(mockRepo, mockClient)
"""),
                ("h", "What @SpringBootApplication really is"),
                ("code", """
@SpringBootApplication  =  @SpringBootConfiguration   (this class can define @Beans)
                         + @ComponentScan             (find @Component/@Service/... in this package & below)
                         + @EnableAutoConfiguration   (load auto-config classes, below)

 spring-boot-autoconfigure.jar
   META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
     ├─ DataSourceAutoConfiguration
     ├─ RedisAutoConfiguration
     ├─ KafkaAutoConfiguration   ...  (~150 candidates, each guarded by conditions)
"""),
                ("code", """
// Simplified version of what Boot ships:
@AutoConfiguration
@ConditionalOnClass(DataSource.class)                 // only if JDBC is on the classpath
@EnableConfigurationProperties(DataSourceProperties.class)
public class DataSourceAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean                         // back off if YOU defined a DataSource
    DataSource dataSource(DataSourceProperties props) {
        return props.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    }
}
"""),
                ("p", "**Debug it:** run with `--debug` (or `debug=true`) to print the **Conditions Evaluation "
                      "Report**: which auto-configs matched, which didn't, and why. The `/actuator/conditions` "
                      "endpoint shows the same at runtime."),
                ("h", "Type-safe configuration"),
                ("code", """
@ConfigurationProperties(prefix = "orders")
@Validated
public record OrderProperties(@NotNull Duration paymentTimeout, @Min(1) int maxItems) {}

# application.yml
orders:
  payment-timeout: 3s
  max-items: 50
"""),
                ("warn", "**Field injection** (`@Autowired private Repo repo;`). It hides dependencies, "
                         "allows `null` in unit tests, and makes circular dependencies easy to create. Spring "
                         "Boot 2.6+ fails on circular references by default, and constructor injection exposes "
                         "the cycle so you redesign instead of hiding it."),
                ("key", ["Constructor injection with `final` fields, always.",
                         "Auto-config = classpath + conditions + \"back off if user defined it\".",
                         "`--debug` shows why a bean was or wasn't created."]),
            ],
            "questions": [
                "You define your own `@Bean ObjectMapper` with custom settings. Why does Spring Boot's default "
                "`ObjectMapper` not get created as well?",
            ],
            "answer": "Jackson's auto-configuration declares its `ObjectMapper` bean with "
                      "`@ConditionalOnMissingBean`. Your bean already exists, so the condition fails and the "
                      "auto-config backs off. (Tip: to *tweak* Boot's mapper rather than replace it, define a "
                      "`Jackson2ObjectMapperBuilderCustomizer` bean.)",
        },
        # ------------------------------------------------------------------ 5.2
        {
            "title": "@Transactional & the Proxy Trap",
            "blocks": [
                ("analogy", "`@Transactional` works through a **receptionist** (a proxy). Visitors who come "
                            "through the front desk get signed in and out (BEGIN/COMMIT). But if someone already "
                            "inside the building walks to another office down the hall, **the receptionist never "
                            "sees them**, so nothing gets logged."),
                ("code", """
  Controller ──calls──► [ OrderService$$SpringCGLIB PROXY ] ──► real OrderService
                          │ 1. get connection, BEGIN
                          │ 2. invoke real method
                          │ 3. COMMIT, or ROLLBACK on RuntimeException
                          ▼
  Inside the real object, `this.otherMethod()` bypasses the proxy entirely.
"""),
                ("h", "Pitfall 1: self-invocation"),
                ("code", """
@Service
public class OrderService {
    public void placeOrders(List<OrderRequest> reqs) {
        reqs.forEach(this::placeOne);        // ✘ `this` = real object → @Transactional IGNORED
    }

    @Transactional
    public void placeOne(OrderRequest r) { ... }
}

// ✔ Fix: move placeOne() to another bean (cleanest), or use TransactionTemplate:
private final TransactionTemplate tx;
public void placeOrders(List<OrderRequest> reqs) {
    reqs.forEach(r -> tx.executeWithoutResult(status -> placeOne(r)));
}
"""),
                ("h", "Pitfall 2: checked exceptions don't roll back"),
                ("code", """
@Transactional                                   // rolls back on RuntimeException and Error only
public void importFile(...) throws IOException {
    repo.save(a);
    parser.parse(file);                         // throws IOException → transaction COMMITS a! ✘
}

@Transactional(rollbackFor = Exception.class)    // ✔ explicit
"""),
                ("h", "Pitfall 3: swallowing the exception"),
                ("code", """
@Transactional
public void pay(...) {
    try { ledger.debit(...); }
    catch (Exception e) { log.error("failed", e); }   // ✘ proxy never sees the exception → COMMIT
}
"""),
                ("h", "Propagation in one table"),
                ("table", [["Propagation", "Behaviour", "Typical use"],
                           ["`REQUIRED` (default)", "Join existing transaction or start one", "Almost everything"],
                           ["`REQUIRES_NEW`", "Suspend outer, run in a brand-new transaction", "Audit log that must persist even if outer rolls back"],
                           ["`MANDATORY`", "Fail if no transaction exists", "Repository-style methods that must be called inside one"],
                           ["`NOT_SUPPORTED`", "Suspend transaction, run without", "Long read-only reports / external calls"]],
                 [0.24, 0.42, 0.34]),
                ("p", "Use `@Transactional(readOnly = true)` on query methods: Hibernate skips dirty checking and "
                      "the driver can route to replicas."),
                ("warn", "Putting `@Transactional` on a **private** method or calling it from the same class "
                         "and \"testing\" it by eye. Verify by enabling "
                         "`logging.level.org.springframework.transaction.interceptor=TRACE`: you will see "
                         "\"Getting transaction for [...]\" only when the proxy is actually involved."),
                ("key", ["Transactions are applied by a proxy, so only calls *through the proxy* count.",
                         "Default rollback: unchecked exceptions only. Use `rollbackFor` for checked ones.",
                         "Don't swallow exceptions inside a transactional method."]),
            ],
            "questions": [
                "`AuditService.log()` is annotated `@Transactional(propagation = REQUIRES_NEW)` and is called "
                "from `OrderService.place()` (a separate bean). `place()` then throws. Is the audit row saved? "
                "What if `log()` were a method *inside* `OrderService`?",
            ],
            "answer": "Separate bean: **yes, saved**. The call goes through `AuditService`'s proxy, which "
                      "suspends the outer transaction and commits its own. Same class: **no**. Self-invocation "
                      "bypasses the proxy, so `REQUIRES_NEW` is ignored; the insert runs in the outer "
                      "transaction and is rolled back with it.",
        },
        # ------------------------------------------------------------------ 5.3
        {
            "title": "Resilience4j: Circuit Breaker, Retry, Timeouts & Bulkheads",
            "blocks": [
                ("analogy", "A **circuit breaker** is the **electrical fuse** in your house. When a faulty "
                            "appliance draws too much current, the fuse trips and cuts power to that circuit, "
                            "protecting the whole house from fire. After a while you try switching it back on; "
                            "if the fault persists, it trips again."),
                ("code", """
                 failure rate ≥ 50% (over sliding window)
     ┌────────┐ ─────────────────────────────────────► ┌────────┐
     │ CLOSED │                                        │  OPEN  │  calls fail fast →
     │ normal │ ◄──────────┐                           │        │  fallback (no remote call)
     └────────┘   trial    │                           └───┬────┘
                  calls OK │   ┌───────────┐  wait 30s     │
                           └── │ HALF_OPEN │ ◄─────────────┘
                               │ 5 trial   │ ──trial calls fail──► back to OPEN
                               └───────────┘
"""),
                ("h", "Setup"),
                ("code", """
<!-- pom.xml -->
<dependency><groupId>io.github.resilience4j</groupId>
            <artifactId>resilience4j-spring-boot3</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-aop</artifactId></dependency>

# application.yml
resilience4j:
  circuitbreaker:
    instances:
      payment:
        sliding-window-size: 20
        minimum-number-of-calls: 10
        failure-rate-threshold: 50
        slow-call-duration-threshold: 2s
        slow-call-rate-threshold: 50
        wait-duration-in-open-state: 30s
        permitted-number-of-calls-in-half-open-state: 5
  retry:
    instances:
      payment:
        max-attempts: 3
        wait-duration: 200ms
        enable-exponential-backoff: true
        retry-exceptions: [java.io.IOException, java.util.concurrent.TimeoutException]
"""),
                ("code", """
@Service
@RequiredArgsConstructor
public class PaymentGateway {
    private final PaymentClient client;

    @Retry(name = "payment")
    @CircuitBreaker(name = "payment", fallbackMethod = "paymentUnavailable")
    public PaymentResult charge(ChargeRequest req) {
        return client.charge(req);        // HTTP client MUST have its own connect/read timeouts
    }

    // same signature + the exception as last parameter
    private PaymentResult paymentUnavailable(ChargeRequest req, Throwable t) {
        return PaymentResult.pending(req.orderId(), "Payment service busy, will retry");
    }
}
"""),
                ("table", [["Pattern", "Protects against", "Analogy"],
                           ["**Timeout**", "Hanging forever on a slow dependency", "Hanging up after 10 rings"],
                           ["**Retry** (with backoff)", "Brief, transient glitches", "Redialling a dropped call"],
                           ["**Circuit breaker**", "Hammering a service that is down", "Electrical fuse"],
                           ["**Bulkhead**", "One slow dependency eating all threads", "Ship's watertight compartments"],
                           ["**Rate limiter**", "Overwhelming a dependency or yourself", "Club bouncer"]],
                 [0.24, 0.43, 0.33]),
                ("p", "Default aspect order: `Retry ( CircuitBreaker ( RateLimiter ( TimeLimiter ( Bulkhead ( call ) ) ) ) )`. "
                      "Each retry attempt is counted by the circuit breaker, and once it opens retries fail fast."),
                ("warn", "**Retrying non-idempotent calls** (e.g. \"charge card\") without an idempotency key, "
                         "so the customer gets charged twice when the first call actually succeeded but timed out. "
                         "Always send an `Idempotency-Key` header, or retry only safe operations."),
                ("key", ["Every remote call needs a timeout. That comes before any other pattern.",
                         "Circuit breaker: CLOSED → OPEN (fail fast) → HALF_OPEN (probe).",
                         "Retries must use backoff and be idempotent; fallbacks should degrade gracefully."]),
            ],
            "questions": [
                "The inventory service is down. Without a circuit breaker, your order service has 200 Tomcat "
                "threads and each inventory call waits 30 s to time out. Describe what happens to your "
                "service, and how the circuit breaker changes it.",
            ],
            "answer": "Within seconds all 200 threads are stuck waiting, so your order service stops answering "
                      "*every* endpoint, even ones not needing inventory: a **cascading failure**. With a breaker "
                      "(+ a short timeout), after ~10 failures it opens, later calls fail fast in microseconds "
                      "with a fallback (e.g. \"accept order, reserve stock later\"), threads stay free, and "
                      "HALF_OPEN probes detect recovery automatically.",
        },
    ],
}
