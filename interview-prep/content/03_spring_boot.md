# Spring & Spring Boot

## What is Spring Boot and how does auto-configuration work?
Spring Boot is an opinionated layer on top of Spring. It gives you **starters** (curated dependency sets), **auto-configuration**, an **embedded server** (Tomcat, Jetty or Undertow), **externalised configuration** and **Actuator**.
- `@SpringBootApplication` = `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`.
- Auto-config classes are listed in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (Boot 3; Boot 2 used `spring.factories`).
- Each one is guarded by **conditions**: `@ConditionalOnClass` (a library is on the classpath), `@ConditionalOnMissingBean` (you haven't defined your own), `@ConditionalOnProperty`, `@ConditionalOnWebApplication`.
- So if you define your own `DataSource` bean, Boot's auto-configured one **backs off**.
- Debug it with `--debug` or `debug=true`, which prints the condition evaluation report, or with Actuator's `/actuator/conditions`.

## Explain IoC and Dependency Injection. Constructor vs field injection?
**Inversion of Control**: the container creates objects and wires their dependencies. Your classes don't use `new` for their collaborators.
- **Constructor injection (recommended)**: dependencies can be `final`, so the object is immutable. They are mandatory and visible. Classes are easy to unit test without Spring. Circular dependencies fail fast at startup. If a class has one constructor, `@Autowired` is optional.
- **Field injection** (`@Autowired` on a field): hides dependencies, cannot be final and makes testing harder. Avoid it.
- **Setter injection**: for optional dependencies.
- Ambiguous beans are resolved with `@Primary`, `@Qualifier("name")`, or by injecting `List<PaymentGateway>` / `Map<String, PaymentGateway>` (the strategy pattern).

## Explain the Spring Bean lifecycle.
1. Instantiate (constructor).
2. Populate properties (DI).
3. Aware callbacks (`BeanNameAware`, `ApplicationContextAware`).
4. `BeanPostProcessor.postProcessBeforeInitialization`.
5. `@PostConstruct`, then `InitializingBean.afterPropertiesSet`, then a custom init-method.
6. `BeanPostProcessor.postProcessAfterInitialization`. **AOP proxies are created here.**
7. The bean is ready to use.
8. On shutdown: `@PreDestroy`, then `DisposableBean.destroy`, then a custom destroy-method.

## Bean scopes? What happens when you inject a prototype into a singleton?
- **singleton** (default: one per container), **prototype** (new instance on every lookup), **request**, **session**, **application**, **websocket**.
- A prototype injected into a singleton is created **only once**, at injection time. To get a fresh instance each time, use `ObjectProvider<T>` / `Provider<T>`, `@Lookup` method injection, or a scoped proxy (`proxyMode = ScopedProxyMode.TARGET_CLASS`).
- Singleton beans are **not thread-safe by default**. Keep them stateless.

## How does @Transactional work? What are the common pitfalls?
Spring wraps the bean in an **AOP proxy** (JDK dynamic proxy or CGLIB). The proxy opens a transaction, calls the method, then commits, or rolls back if an exception is thrown.
- **Pitfall 1: self-invocation.** Calling `this.otherTransactionalMethod()` from inside the same class **bypasses the proxy**, so no transaction starts. Fix it by moving the method to another bean or injecting the class's own proxy.
- **Pitfall 2**: only **public** methods are proxied (Spring 6 also allows protected and package-private with CGLIB). Private methods are ignored.
- **Pitfall 3**: rollback happens only for **RuntimeException and Error** by default. Use `rollbackFor = Exception.class`.
- **Pitfall 4**: if you catch the exception inside the method, the proxy never sees it, so nothing rolls back.
- **Pitfall 5**: long transactions that include remote calls hold DB connections and cause pool exhaustion.
- `readOnly = true` lets Hibernate skip dirty checking and lets the routing layer send the query to a read replica.

## Explain transaction propagation and isolation levels.
**Propagation**:
- **REQUIRED** (default): join the existing transaction or create one.
- **REQUIRES_NEW**: suspend the current transaction and start a new independent one. Used for audit logs that must be saved even if the outer transaction fails.
- **NESTED**: savepoint inside the current transaction.
- **SUPPORTS**, **NOT_SUPPORTED**, **MANDATORY**, **NEVER**.

**Isolation** (what it prevents):
- **READ_UNCOMMITTED**: nothing (dirty reads possible).
- **READ_COMMITTED**: dirty reads. This is the default in PostgreSQL, Oracle and SQL Server.
- **REPEATABLE_READ**: dirty and non-repeatable reads. This is MySQL InnoDB's default.
- **SERIALIZABLE**: dirty reads, non-repeatable reads and phantoms. Safest but slowest.

## What is the N+1 query problem in JPA/Hibernate and how do you fix it?
You load N parent entities with one query, and then accessing a **lazy** association runs **one more query per parent**, N in total.
- Fix with a **JOIN FETCH** in JPQL: `select o from Order o join fetch o.items`.
- Or an **@EntityGraph(attributePaths = "items")** on the repository method.
- Or `@BatchSize(size = 50)` / `hibernate.default_batch_fetch_size`, which loads the association with IN queries.
- Or **DTO projections** when you only need some fields.
- **Detect it** with `spring.jpa.show-sql`, Hibernate statistics, or tests that assert the query count.
- Also: keep associations **LAZY** (make `@ManyToOne` explicitly LAZY, since it defaults to EAGER) and turn off `spring.jpa.open-in-view` in APIs.

## Optimistic vs pessimistic locking?
- **Optimistic**: add a `@Version` column. An update runs `WHERE id = ? AND version = ?`. If 0 rows change, you get `OptimisticLockException`, and you retry or return 409 to the caller. Best when conflicts are rare and reads are frequent.
- **Pessimistic**: `@Lock(PESSIMISTIC_WRITE)` issues `SELECT ... FOR UPDATE`. Rows stay locked until commit. Use it when there is high contention on critical rows (e.g. inventory or wallet balances), and watch for deadlocks.

## How do you handle exceptions globally in a REST API?
Use `@RestControllerAdvice` with `@ExceptionHandler` methods. Return a consistent error body. Spring 6 supports RFC 7807 **ProblemDetail**.
```
@RestControllerAdvice
public class GlobalErrors {
    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail notFound(OrderNotFoundException ex) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        pd.setProperty("errorCode", "ORDER_404");
        return pd;
    }
    @ExceptionHandler(MethodArgumentNotValidException.class)
    ProblemDetail invalid(MethodArgumentNotValidException ex) { ... }
}
```

## How does Spring AOP work? Where have you used it?
- Terms: **Aspect** (the module), **Advice** (the code: `@Before`, `@After`, `@AfterReturning`, `@AfterThrowing`, `@Around`), **Pointcut** (where it applies), **JoinPoint** (a method execution).
- Spring AOP is **proxy-based and applies at runtime**, to Spring beans and method calls only. AspectJ weaves at compile or load time and can intercept fields and constructors.
- Typical uses: logging, metrics and timing, auditing, security (`@PreAuthorize`), transactions, caching (`@Cacheable`), retry (`@Retryable`), and custom annotations such as `@Idempotent`.
```
@Around("@annotation(com.app.Timed)")
public Object time(ProceedingJoinPoint pjp) throws Throwable {
    long t = System.nanoTime();
    try { return pjp.proceed(); }
    finally { log.info("{} took {} ms", pjp.getSignature(), (System.nanoTime() - t) / 1_000_000); }
}
```

## How do you manage configuration across environments?
- `application.yml` plus **profiles** (`application-dev.yml`, `application-prod.yml`), activated with `spring.profiles.active`.
- **Precedence** (highest first): command-line args > environment variables > profile-specific files > application.yml > defaults.
- Use type-safe `@ConfigurationProperties` records with validation instead of scattering `@Value` everywhere.
- **Secrets never go in git**. Load them from Azure Key Vault (the `spring-cloud-azure-starter-keyvault` property source), Kubernetes Secrets or environment variables.
- Centralised config: Spring Cloud Config Server or **Azure App Configuration**, with refresh via `@RefreshScope`.

## What does Spring Boot Actuator give you?
Production endpoints: `/health` (with **liveness and readiness groups** for Kubernetes probes), `/metrics`, `/prometheus`, `/info`, `/env`, `/loggers` (change log levels at runtime), `/threaddump`, `/heapdump`.
- **Micrometer** is the metrics facade. It exports to Prometheus, Azure Monitor, Datadog and others.
- **Secure the endpoints**: expose only what is needed, and serve them on a separate management port.

## How do you secure a Spring Boot microservice (JWT / OAuth2)?
- Use **Spring Security 6** with a `SecurityFilterChain` bean. `WebSecurityConfigurerAdapter` has been removed.
- The service is an **OAuth2 Resource Server**. It validates the JWT's signature (through JWKS), expiry, issuer and audience. Tokens are issued by an identity provider such as **Microsoft Entra ID (Azure AD)**, Keycloak or Okta.
- Authorisation: scopes and roles map to authorities, enforced with `@PreAuthorize("hasAuthority('SCOPE_orders.write')")`.
- Service-to-service calls use the **client credentials** flow, or managed identity on Azure.
- Also: HTTPS everywhere, CORS configuration, CSRF off only for stateless APIs, input validation, rate limiting at the gateway, and OWASP dependency scanning.
```
@Bean
SecurityFilterChain api(HttpSecurity http) throws Exception {
    return http.csrf(c -> c.disable())
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(a -> a
            .requestMatchers("/actuator/health/**").permitAll()
            .anyRequest().authenticated())
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .build();
}
```

## How do you test Spring Boot applications?
- **Unit tests**: JUnit 5 + Mockito, with no Spring context. This is quick and should be the majority of tests.
- **Slice tests**: `@WebMvcTest` (controllers + MockMvc), `@DataJpaTest` (repositories), `@JsonTest`.
- **Integration tests**: `@SpringBootTest` with **Testcontainers** (real Postgres, Kafka, Redis in Docker). Prefer them to H2 so tests match production.
- **Contract tests**: Spring Cloud Contract or Pact between consumer and provider.
- **Stub HTTP dependencies** with WireMock. `@MockitoBean` (Boot 3.4+) replaces `@MockBean`.

## How does Spring's REST client story look today (RestTemplate, WebClient, RestClient)?
- **RestTemplate**: blocking and in maintenance mode.
- **WebClient**: reactive and non-blocking (WebFlux). It can also be used in a blocking way.
- **RestClient** (Spring 6.1): a modern, fluent, synchronous client. Recommended for MVC apps, especially with virtual threads.
- **HTTP Interface** (`@HttpExchange`): declarative clients like Feign, built into Spring.
- Always configure **connect and read timeouts**, connection pooling, retries with backoff, and circuit breakers.

## Spring MVC vs WebFlux? When would you choose reactive?
- **MVC**: thread-per-request, blocking, with the Servlet stack. Simple to write and debug. With virtual threads it now scales very well.
- **WebFlux**: event loop (Netty), non-blocking, Reactor (`Mono` / `Flux`). Good for streaming, many concurrent slow I/O calls, and backpressure.
- Reactive only pays off if the **entire chain is non-blocking** (R2DBC, reactive drivers). It costs complexity and makes debugging harder. Since Java 21, many teams choose MVC + virtual threads.

## How do you implement caching in Spring Boot?
- `@EnableCaching` with `@Cacheable`, `@CachePut` and `@CacheEvict`.
- Providers: Caffeine (local, in-process) or **Redis** (distributed; Azure Cache for Redis).
- Watch out for: TTL and eviction, **cache stampede** (fix with `sync = true`, locks or early refresh), stale data, cache keys, and serialisation.
- Choose between **cache-aside**, write-through and write-behind strategies.

## How do you improve Spring Boot startup time and memory?
- Use lazy initialisation where it fits, trim unused starters, and use **Class Data Sharing (CDS)** or **CRaC**.
- **GraalVM native image** (Spring AOT) starts in milliseconds and uses little memory. Good for serverless or Azure Functions. The trade-offs are long builds and reflection configuration.
- Use layered jars / Buildpacks for efficient Docker layers, and tune JVM memory flags for containers.
