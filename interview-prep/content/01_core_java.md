# Core Java & Java 8+ Features

## What changed in Java 8 and why does it matter for a senior developer?
Java 8 moved Java towards a **functional style**. The key additions are:
- **Lambda expressions**: short anonymous functions, e.g. `(a, b) -> a + b`.
- **Functional interfaces**: interfaces with exactly one abstract method (`Function`, `Predicate`, `Supplier`, `Consumer`, `BiFunction`, `UnaryOperator`).
- **Stream API**: declarative pipelines over data (filter, map, reduce) that can run in parallel.
- **Optional**: an explicit container for "value may be absent", which reduces NullPointerExceptions.
- **Default and static methods in interfaces**: APIs can grow without breaking existing implementations.
- **java.time API**: immutable, thread-safe dates (`LocalDate`, `ZonedDateTime`, `Instant`, `Duration`).
- **CompletableFuture**: composable asynchronous programming.
- **Method references**: `String::toUpperCase`, `System.out::println`.
- **Metaspace** replaced PermGen for class metadata.
> Senior angle: don't just list features. Say how they changed your code, for example "we replaced nested loops over DTOs with streams and Collectors.groupingBy, and made our service layer return Optional instead of null".

## What happened after Java 8 (Java 9 to 21+)? Which features have you used?
- **Java 9**: Module system (JPMS), `List.of()` / `Map.of()` immutable factories, JShell, private interface methods.
- **Java 10**: `var` for local variable type inference.
- **Java 11 (LTS)**: `HttpClient`, the String methods `isBlank()`, `strip()`, `lines()` and `repeat()`, and running single-file programs with `java File.java`.
- **Java 14-16**: Switch expressions, **Records** (immutable data carriers), pattern matching for `instanceof`, text blocks.
- **Java 17 (LTS)**: **Sealed classes** (`sealed ... permits`), which limit which classes can extend a type.
- **Java 21 (LTS)**: **Virtual threads** (Project Loom), pattern matching for switch, record patterns, sequenced collections (`getFirst()`, `getLast()`, `reversed()`).
```
// Record + sealed interface + pattern matching switch (Java 21)
sealed interface Shape permits Circle, Square {}
record Circle(double r) implements Shape {}
record Square(double side) implements Shape {}

double area(Shape s) {
    return switch (s) {
        case Circle c -> Math.PI * c.r() * c.r();
        case Square sq -> sq.side() * sq.side();
    };   // no default needed: the compiler knows every subtype
}
```

## Explain functional interfaces and the main built-in ones.
A functional interface has **exactly one abstract method** (SAM). It can still have default and static methods. You can mark it with `@FunctionalInterface` so the compiler enforces the rule.
- `Predicate<T>`: T -> boolean (used by `filter`)
- `Function<T,R>`: T -> R (used by `map`)
- `Consumer<T>`: T -> void (used by `forEach`)
- `Supplier<T>`: () -> T (lazy creation, `orElseGet`)
- `BiFunction<T,U,R>`, `UnaryOperator<T>`, `BinaryOperator<T>`
- Primitive specialisations (`IntPredicate`, `ToIntFunction`) avoid boxing overhead.
```
Predicate<String> notEmpty = s -> !s.isEmpty();
Function<String, Integer> len = String::length;
Function<String, Integer> lenTimes2 = len.andThen(x -> x * 2);
Predicate<String> valid = notEmpty.and(s -> s.length() < 50);
```

## How do Streams work internally? What are intermediate and terminal operations?
A stream is a **lazy pipeline**. It has a source, zero or more **intermediate operations** (filter, map, sorted, distinct, flatMap, peek) and one **terminal operation** (collect, forEach, reduce, count, findFirst, anyMatch).
- Nothing runs until the terminal operation is called.
- Elements are processed **one at a time through the whole pipeline** (vertical processing), not stage by stage. This allows **short-circuiting**: `findFirst()` stops as soon as one element matches.
- **Stateless** operations (map, filter) are cheap. **Stateful** ones (sorted, distinct) must buffer elements.
- A stream **cannot be reused** after its terminal operation. Doing so throws `IllegalStateException`.
```
Map<String, Double> avgSalaryByDept = employees.stream()
    .filter(e -> e.getSalary() > 50_000)
    .collect(Collectors.groupingBy(Employee::getDept,
             Collectors.averagingDouble(Employee::getSalary)));

// Top 3 highest paid names
List<String> top3 = employees.stream()
    .sorted(Comparator.comparingDouble(Employee::getSalary).reversed())
    .limit(3).map(Employee::getName).toList();
```

## map vs flatMap? reduce vs collect?
- **map** transforms each element one-to-one: `Stream<List<String>>` stays a stream of lists.
- **flatMap** turns each element into a stream and **flattens** them: `Stream<List<String>>` becomes `Stream<String>`.
- **reduce** combines elements into one immutable value (sum, max). Use it for immutable reduction.
- **collect** is a **mutable reduction** into a container (List, Map, StringBuilder). It is more efficient for building collections.
```
List<String> allSkills = employees.stream()
    .flatMap(e -> e.getSkills().stream()).distinct().toList();
int total = orders.stream().map(Order::getQty).reduce(0, Integer::sum);
```

## When should you NOT use parallel streams?
Parallel streams use the **common ForkJoinPool**, which has (number of cores - 1) threads and is shared by the whole JVM.
- **Avoid** them for I/O or blocking work (DB, REST calls). They block the shared pool and slow down the whole application.
- **Avoid** them for small datasets. Splitting and merging costs more than you gain.
- **Avoid** them with sources that split badly (`LinkedList`, `Stream.iterate`) or with order-dependent operations (`findFirst`, `limit` on ordered streams).
- **Avoid** them with shared mutable state. That causes race conditions.
- **Good fit**: large, CPU-bound, stateless work over `ArrayList` or arrays.

## How should Optional be used correctly?
- Use Optional as a **return type** to show a value may be absent, e.g. `Optional<User> findById(id)`.
- **Do not** use it for fields, method parameters or collections (return an empty list instead). Optional is not Serializable.
- Prefer `orElseGet(() -> expensive())` over `orElse(expensive())`. `orElse` **always** evaluates its argument.
- Avoid `optional.get()` without a check. Use `orElseThrow()`, `map`, `ifPresentOrElse`.
```
String city = userRepo.findById(id)
    .map(User::getAddress)
    .map(Address::getCity)
    .orElse("UNKNOWN");
```

## Explain JVM memory areas.
- **Heap**: all objects. It is shared by all threads and managed by the GC. It is split into the **Young generation** (Eden plus two Survivor spaces) and the **Old generation** (tenured).
- **Stack**: one per thread. Holds frames with local variables and partial results. `StackOverflowError` comes from deep recursion.
- **Metaspace** (Java 8+): class metadata in native memory. It replaced PermGen, and its size is limited with `-XX:MaxMetaspaceSize`.
- **PC register** and **native method stack** are per thread.
- **Code cache**: JIT-compiled native code.
> Common OutOfMemoryErrors: "Java heap space" (a leak or undersized heap), "Metaspace" (classloader leaks, often from repeated hot redeploys), "GC overhead limit exceeded", and "unable to create native thread".

## How does Garbage Collection work? Compare G1, ZGC and Parallel GC.
Objects that can no longer be reached from **GC roots** (thread stacks, static fields, JNI refs) are collected. Most objects die young (the **generational hypothesis**), so the JVM collects the Young generation often (minor GC) and the Old generation rarely (major/full GC).
- **Serial**: single-threaded. For small heaps and client apps.
- **Parallel GC**: multi-threaded and throughput-focused. Pauses can be long. Good for batch jobs.
- **G1** (default since Java 9): the heap is divided into regions and the collector cleans the regions with the most garbage first. You set a pause target with `-XX:MaxGCPauseMillis=200`. A good general default for services.
- **ZGC / Shenandoah**: concurrent, low-latency collectors with sub-millisecond pauses even on multi-terabyte heaps. Generational ZGC is available from Java 21. Use them for latency-sensitive APIs.
> Tuning story for interviews: set `-Xms` equal to `-Xmx` in containers (or use `-XX:MaxRAMPercentage=75`), turn on GC logs with `-Xlog:gc*`, analyse them with GCeasy, take a heap dump on OOM with `-XX:+HeapDumpOnOutOfMemoryError`, and use Eclipse MAT to find leaks.

## What is the Java Memory Model? Explain volatile, happens-before and visibility.
The JMM defines when a write made by one thread becomes **visible** to another thread. CPUs and the JIT reorder instructions and cache values in registers or CPU caches, so without synchronisation a thread may never see another thread's update.
- **volatile** guarantees **visibility** and **ordering**: reads and writes go to main memory and cannot be reordered around it. It does **not** give atomicity, so `count++` is still unsafe.
- **Happens-before rules**: unlocking a monitor happens-before a later lock of it; a volatile write happens-before later reads of it; `Thread.start()` happens-before actions in the started thread; actions in a thread happen-before another thread's `join()` returns.
- **synchronized** gives both **atomicity** (mutual exclusion) and **visibility**.
```
// Double-checked locking singleton needs volatile
public class Config {
    private static volatile Config instance;
    public static Config get() {
        if (instance == null) {
            synchronized (Config.class) {
                if (instance == null) instance = new Config();
            }
        }
        return instance;
    }
}
```

## synchronized vs ReentrantLock vs atomic classes?
- **synchronized**: simple and scoped to a block, and the lock is released automatically. You cannot use a timeout or interrupt a thread waiting for it.
- **ReentrantLock**: `tryLock(timeout)`, interruptible locking, fairness policy, and multiple `Condition`s. You **must** unlock in `finally`.
- **ReadWriteLock / StampedLock**: many readers or one writer. StampedLock also supports optimistic reads.
- **AtomicInteger / AtomicLong / AtomicReference**: lock-free CAS (compare-and-swap). The best choice for counters. For very high contention use **LongAdder**.
- **Java 21 note**: with virtual threads, long blocking inside `synchronized` could **pin** the carrier thread (fixed in JDK 24). ReentrantLock avoids this.

## Explain the ExecutorService, thread pools and how you size them.
Creating threads is expensive, so pools reuse them. `ThreadPoolExecutor(core, max, keepAlive, queue, threadFactory, rejectionHandler)`.
- A task is submitted -> if fewer than core threads exist, a new thread starts -> otherwise the task is queued -> if the queue is full and there are fewer than max threads, a new thread starts -> otherwise the **RejectedExecutionHandler** runs (Abort, CallerRuns, Discard, DiscardOldest).
- **Avoid** `Executors.newFixedThreadPool` and `newCachedThreadPool` in production. The first uses an **unbounded queue**, which risks OOM. The second allows **unbounded threads**.
- **Sizing**: for CPU-bound work, threads = number of cores (+1). For I/O-bound work, threads = cores x (1 + wait time / compute time).
- Always shut down gracefully with `shutdown()`, `awaitTermination()` and then `shutdownNow()`.
- Name your threads with a custom ThreadFactory. It makes thread dumps much easier to read.

## How does CompletableFuture work? Give a real example.
CompletableFuture lets you compose async stages without blocking.
- `supplyAsync` / `runAsync` start the work. Always pass your **own executor**, otherwise the common ForkJoinPool is used.
- `thenApply` (map), `thenCompose` (flatMap, for dependent async calls), `thenCombine` (joins two independent futures), `allOf` / `anyOf`.
- Error handling: `exceptionally`, `handle`, `whenComplete`. Timeouts: `orTimeout`, `completeOnTimeout` (Java 9+).
```
CompletableFuture<User> userF = supplyAsync(() -> userClient.get(id), pool);
CompletableFuture<List<Order>> ordersF = supplyAsync(() -> orderClient.get(id), pool);

Dashboard d = userF.thenCombine(ordersF, Dashboard::new)
    .orTimeout(2, TimeUnit.SECONDS)
    .exceptionally(ex -> Dashboard.fallback(id))
    .join();
```
> This cuts latency from t1 + t2 to max(t1, t2). It is a common way to aggregate data in a BFF or API-composition layer.

## What are virtual threads and when would you use them?
Virtual threads (Java 21) are **lightweight threads managed by the JVM**, not the OS. Millions of them can exist. When a virtual thread blocks on I/O, the JVM **unmounts** it from its carrier (platform) thread, so the carrier is free to run other work.
- They are ideal for **thread-per-request, I/O-heavy** services. You can write simple blocking code and get throughput close to reactive code.
- They don't make CPU-bound code faster. Don't pool them. Be careful with `ThreadLocal`-heavy code, because there can be millions of copies.
- Spring Boot 3.2+: set `spring.threads.virtual.enabled=true`.
```
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> executor.submit(() -> callApi(i)));
}
```

## What causes deadlock and how do you detect and prevent it?
Deadlock happens when four conditions hold: mutual exclusion, hold-and-wait, no preemption and **circular wait**. For example, thread A holds lock 1 and wants lock 2, while thread B holds lock 2 and wants lock 1.
- **Prevent** it by always acquiring locks in a **global order**, using `tryLock` with a timeout, keeping lock scopes small and preferring higher-level concurrency utilities.
- **Detect** it with `jstack <pid>` or `jcmd <pid> Thread.print` (prints "Found one Java-level deadlock"), VisualVM or JMC, or `ThreadMXBean.findDeadlockedThreads()` in code.
- Related problems: **livelock** (threads keep reacting to each other and make no progress) and **starvation**.

## Why must you override equals() and hashCode() together?
The contract says: if `a.equals(b)` then `a.hashCode() == b.hashCode()`. The reverse does not have to hold.
- Hash-based collections find the **bucket by hashCode** and then compare with **equals**. If you override only equals, two "equal" objects land in different buckets, so the HashSet keeps duplicates and `map.get()` fails.
- Use the **same immutable fields** in both methods. If a field used in hashCode changes after the object is inserted into a HashMap, the entry is effectively lost.
- Records generate correct equals and hashCode automatically.

## How do you design an immutable class?
- Make the class `final` (or give it private constructors) so no one can subclass it.
- Make all fields `private final`.
- Provide no setters.
- **Defensively copy** mutable inputs and outputs, e.g. `List.copyOf(list)` or `new Date(d.getTime())`.
- Return new objects from "modifier" methods, e.g. `withSalary()`.
- Benefits: thread-safe without locks, safe to use as HashMap keys, safe to cache, easy to reason about. `String`, `Integer` and `LocalDate` are immutable.
```
public final class Money {
    private final BigDecimal amount; private final String currency;
    public Money(BigDecimal amount, String currency) {
        this.amount = Objects.requireNonNull(amount);
        this.currency = Objects.requireNonNull(currency);
    }
    public Money add(Money o) { return new Money(amount.add(o.amount), currency); }
}
// Or simply: public record Money(BigDecimal amount, String currency) {}
```

## Why is String immutable? String pool, StringBuilder vs StringBuffer?
- **Security**: strings are used for class names, URLs, DB credentials and file paths.
- **String pool**: literals are interned and shared, which saves memory. This is only safe because strings are immutable.
- **Caching hashCode**: this makes String a fast HashMap key.
- **Thread safety**.
- `new String("a")` creates a new heap object. The literal `"a"` comes from the pool, so `"a" == "a"` is true while `new String("a") == "a"` is false. Always compare with `equals`.
- **StringBuilder**: mutable and not synchronized, so it's fast. **StringBuffer**: synchronized and legacy. Use StringBuilder when concatenating in loops.
- Java 9+ **compact strings** store Latin-1 text as one byte per character.

## Checked vs unchecked exceptions? Best practices?
- **Checked** exceptions (subclasses of `Exception`, e.g. `IOException`) must be handled or declared. **Unchecked** exceptions (`RuntimeException`, e.g. `NullPointerException`, `IllegalArgumentException`) do not.
- `Error` (OOM, StackOverflow) should not be caught.
- **Best practices**: throw early and catch late. Never swallow exceptions. Wrap them and keep the cause (`new ServiceException("msg", e)`). Use try-with-resources for anything `AutoCloseable`. Build a custom exception hierarchy for the domain. In Spring, map exceptions to HTTP responses centrally with `@ControllerAdvice`.
- Spring's `@Transactional` **rolls back only on unchecked exceptions by default**. Use `rollbackFor = Exception.class` if you also need rollback on checked ones.

## Difference between abstract class and interface after Java 8?
- An **interface** can have default, static and private methods, but **no instance state** (only constants). A class can implement many interfaces. Use one to define a **capability or contract**.
- An **abstract class** can have state, constructors and protected members. A class can extend only one. Use it to share **common base behaviour and state**.
- **Diamond problem**: if two interfaces provide the same default method, the class must override it and choose, e.g. `A.super.method()`.

## Explain ClassLoaders and how they delegate.
- **Bootstrap** (core JDK) -> **Platform/Extension** -> **Application/System** (the classpath) -> custom loaders.
- **Parent delegation**: a loader first asks its parent, and only loads the class itself if the parent cannot. This prevents core classes like `java.lang.String` from being spoofed.
- A class is identified by **(class name + classloader)**. The same class loaded by two loaders gives `ClassCastException`. This is common in app servers and during hot redeploys, and a leaked classloader causes Metaspace OOM.

## What is serialization? What are its risks?
Serialization turns an object into bytes (`Serializable`). `transient` fields are skipped. `serialVersionUID` controls version compatibility.
- **Risk**: deserializing untrusted data can lead to **remote code execution** through gadget chains. Prefer JSON (Jackson) or Protobuf/Avro for data crossing a boundary, and use serialization filters (`ObjectInputFilter`) if Java serialization cannot be avoided.

## How do you troubleshoot a slow or high-CPU Java service in production?
1. Check the metrics first: CPU, heap, GC pause time, thread count, and p99 latency in App Insights, Grafana or Prometheus.
2. **High CPU**: run `top -H -p <pid>` to find the hot thread, convert its id to hex, then find it in `jstack` output. Or use async-profiler or JFR to get flame graphs.
3. **Memory**: look at the GC logs, take a heap dump with `jcmd <pid> GC.heap_dump`, and use MAT's dominator tree.
4. **Latency**: use distributed tracing to find the slow downstream call. Check the DB slow query log, connection pool (HikariCP) waits and thread pool saturation.
5. Fix it, add a regression test or alert, and write a blameless postmortem.
> Interviewers at 9+ years expect a **structured method** backed by a real incident story.
