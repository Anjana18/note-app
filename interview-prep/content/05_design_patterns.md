# Design Principles & Design Patterns

## Explain the SOLID principles with examples.
- **S - Single Responsibility**: a class should have one reason to change. `InvoiceService` should not also format PDFs and send emails.
- **O - Open/Closed**: open for extension, closed for modification. Add a new `PaymentStrategy` class instead of adding another `if/else` to existing code.
- **L - Liskov Substitution**: subtypes must be usable wherever the base type is expected. The classic violation is `Square extends Rectangle`, because setting the width silently changes the height.
- **I - Interface Segregation**: many small, client-specific interfaces are better than one fat interface. Clients should not depend on methods they don't use.
- **D - Dependency Inversion**: depend on abstractions, not concretions. Services depend on a `PaymentGateway` interface, and Spring injects the implementation.
- Related principles: **DRY**, **KISS**, **YAGNI**, **composition over inheritance**, **Law of Demeter**.

## Singleton: how do you implement it correctly? What are its problems?
```
// 1. Enum singleton: thread-safe, and safe against serialization and reflection
public enum AppRegistry { INSTANCE; public void register() { ... } }

// 2. Initialization-on-demand holder: lazy and thread-safe, with no locking
public class Cache {
    private Cache() {}
    private static class Holder { static final Cache INSTANCE = new Cache(); }
    public static Cache getInstance() { return Holder.INSTANCE; }
}
```
- It can be broken by **reflection** (guard in the constructor), **serialization** (add `readResolve`), cloning, and multiple classloaders.
- **Problems**: global state, hidden dependencies, and difficult testing. In Spring, prefer **singleton-scoped beans** injected through DI.

## Factory Method vs Abstract Factory?
- **Factory Method**: a method decides which concrete class to create. The creation logic lives in one place.
- **Abstract Factory**: creates **families of related objects** that belong together (e.g. `AzureCloudFactory` creates an AzureStorage and an AzureQueue, while `AwsCloudFactory` creates the AWS versions).
- In Spring, `BeanFactory` / `FactoryBean` and `@Bean` methods are factories.
```
@Component
class NotificationFactory {
    private final Map<String, NotificationSender> senders; // Spring injects all beans, keyed by bean name
    NotificationFactory(Map<String, NotificationSender> senders) { this.senders = senders; }
    NotificationSender get(Channel c) {
        return Optional.ofNullable(senders.get(c.beanName()))
            .orElseThrow(() -> new IllegalArgumentException("Unknown channel " + c));
    }
}
```

## Builder pattern: when and why?
Use it for objects with **many optional parameters**. It avoids telescoping constructors, makes the calling code readable, and lets you build **immutable** objects with validation in `build()`.
- Examples: `StringBuilder`, `HttpRequest.newBuilder()`, `UriComponentsBuilder`, Lombok's `@Builder`, `WebClient.builder()`.
```
Order order = Order.builder()
    .customerId("C1").item("SKU-9", 2)
    .shippingAddress(addr).priority(Priority.HIGH)
    .build();   // build() validates the required fields
```

## Strategy pattern: give a real-world example.
Define a family of interchangeable algorithms behind one interface and choose one at runtime. It **replaces if/else or switch chains** and follows the Open/Closed principle.
```
interface DiscountStrategy { BigDecimal apply(Order o); }
@Component("FESTIVE") class FestiveDiscount implements DiscountStrategy { ... }
@Component("LOYALTY") class LoyaltyDiscount implements DiscountStrategy { ... }

@Service
class PricingService {
    private final Map<String, DiscountStrategy> strategies;
    PricingService(Map<String, DiscountStrategy> strategies) { this.strategies = strategies; }
    BigDecimal price(Order o) { return strategies.get(o.getPromoType()).apply(o); }
}
```
- Examples in the JDK and Spring: `Comparator`, `ResourceLoader`, `PasswordEncoder` implementations, and payment or shipping providers.

## Observer pattern and how it relates to event-driven systems?
Subjects notify their subscribers when state changes, which gives loose coupling.
- In Java/Spring: `ApplicationEventPublisher` + `@EventListener`, and `@TransactionalEventListener(phase = AFTER_COMMIT)` so the event is published only after the transaction commits.
- At system scale it becomes **pub/sub** over Kafka or Service Bus.
- Reactive Streams (`Publisher` / `Subscriber`) are the observer pattern with backpressure.

## Decorator vs Proxy vs Adapter?
- **Decorator**: wraps an object with the **same interface** to **add behaviour**, and decorators can be stacked. Example: `BufferedInputStream(new FileInputStream(f))`. Or a caching or logging decorator around a repository.
- **Proxy**: same interface, but it **controls access**: lazy loading, security, remote calls, transactions. Spring AOP, `@Transactional` and Hibernate lazy entities are proxies.
- **Adapter**: **converts one interface into another** that the client expects. Examples: `Arrays.asList`, `InputStreamReader`, or wrapping a legacy SOAP client behind a clean domain interface (hexagonal architecture ports and adapters).

## Template Method vs Strategy?
- **Template Method**: an abstract class defines the **skeleton of an algorithm**, and subclasses override specific steps. It is based on **inheritance**. Examples: `JdbcTemplate`, `AbstractController`, and batch jobs with read, process and write steps.
- **Strategy**: the whole algorithm is swapped through **composition**, which is more flexible.

## Chain of Responsibility: where is it used?
A request passes along a chain of handlers. Each handler either handles it or passes it on.
- Examples: **Servlet Filters**, the **Spring Security filter chain**, `HandlerInterceptor`s, and validation pipelines (fraud check -> KYC check -> limit check).

## Command, State and Template patterns in business workflows?
- **Command**: wraps a request as an object, which enables queuing, undo, retry and audit. Examples: `Runnable`, CQRS commands, and messages on a queue.
- **State**: an object changes behaviour when its internal state changes (an order moving through CREATED -> PAID -> SHIPPED -> DELIVERED). It replaces status switch statements. Spring State Machine is one implementation.

## Which design patterns does the Spring Framework use?
- **Singleton** (bean scope), **Factory** (BeanFactory, FactoryBean), **Proxy** (AOP, @Transactional), **Template Method** (JdbcTemplate, RestTemplate, KafkaTemplate), **Observer** (ApplicationEvent), **Strategy** (resource loading, and the many pluggable interfaces), **Adapter** (HandlerAdapter in MVC), **Front Controller** (DispatcherServlet), **Decorator** (BeanPostProcessor wrapping), **Chain of Responsibility** (filters), **Dependency Injection / IoC**.

## What are anti-patterns you have seen and fixed?
- **God class / god service**: split it by responsibility.
- **Anemic domain model**: move behaviour into the entities or aggregates when that makes sense.
- **Distributed monolith**: services that must be deployed together, or that share a DB.
- **Chatty services**: batch calls, or replicate data through events.
- **Shotgun surgery**, **copy-paste code**, **magic numbers**, **catching generic Exception and swallowing it**.
- **Premature optimisation** and **over-engineering** (a pattern where a simple function would do).

## Explain Hexagonal / Clean Architecture.
- The **domain core** holds entities and use cases, and has **no framework dependencies**.
- **Ports** are interfaces defined by the core, both inbound (use cases) and outbound (repositories, gateways).
- **Adapters** implement the ports: REST controllers and Kafka listeners (inbound), JPA repositories and HTTP clients (outbound).
- **Dependencies point inward**. The payoffs are testability, swappable infrastructure, and business logic isolated from framework churn.
