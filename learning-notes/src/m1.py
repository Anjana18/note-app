from m1_modern import TOPICS as MODERN_JAVA

MODULE = {
    "title": "Java Core: Internals & Modern Java (8 → 25)",
    "intro": "Everything in the backend stack runs on the JVM. This module covers how memory and collections "
             "really work, the modern language features from Java 8 to Java 25 that every Spring Boot codebase "
             "uses (lambdas, streams, Optional, records, sealed types, pattern matching), and finally "
             "concurrency and virtual threads.",
    "topics": [
        # ------------------------------------------------------------------ 1.1
        {
            "title": "JVM Memory & Garbage Collection",
            "blocks": [
                ("analogy", "The JVM is a **restaurant kitchen**. Each chef has a small private **cutting board** "
                            "(the Stack) that is wiped clean after each dish. All chefs share one big **pantry** "
                            "(the Heap). The **recipe book** on the wall is Metaspace. A **cleaning crew** "
                            "(the Garbage Collector) throws out ingredients nobody can reach anymore. It never "
                            "touches what a chef is still holding."),
                ("table", [["Area", "What lives there", "Lifetime"],
                           ["**Stack** (one per thread)", "Method frames, primitive locals, object *references*",
                            "Freed automatically when the method returns"],
                           ["**Heap** (shared)", "Every object created with `new`, arrays", "Until unreachable, then GC"],
                           ["**Metaspace** (native)", "Class metadata, method bytecode", "Until the class loader is unloaded"]],
                 [0.24, 0.46, 0.30]),
                ("code", r"""
                 ┌──────────────────── JVM Process ──────────────────────┐
 Thread-1 ──► ┌─────────────┐      ┌──────────── HEAP (shared) ───────────┐
              │  STACK      │      │  YOUNG GENERATION                    │
              │ ┌─────────┐ │ ref  │  ┌──────────┬─────────┬─────────┐    │
              │ │ main()  │─┼─────►│  │  Eden    │   S0    │   S1    │    │
              │ │ order   │ │      │  │ (new     │(survivor│(survivor│    │
              │ └─────────┘ │      │  │ objects) │ space)  │ space)  │    │
              │ ┌─────────┐ │      │  └──────────┴─────────┴─────────┘    │
              │ │ calc()  │ │      │        │ survives several GCs        │
              │ │ int x=5 │ │      │        ▼                             │
              │ └─────────┘ │      │  OLD GENERATION                      │
              └─────────────┘      │  long-lived: caches, Spring beans,   │
 Thread-2 ──► ┌─────────────┐      │  connection pools                    │
              │  STACK      │      └──────────────────────────────────────┘
              └─────────────┘         METASPACE (native memory): class metadata
"""),
                ("h", "What goes where?"),
                ("code", """
public class OrderService {
    private static final double TAX_RATE = 0.18;   // constant, part of class data

    public Order createOrder(String customerId) {   // new stack frame pushed
        int quantity = 2;                            // STACK: the value itself
        Order order = new Order(customerId);         // reference on STACK, object on HEAP (Eden)
        return order;
    }                                                // frame popped; object survives while referenced
}
"""),
                ("h", "How the GC decides what to delete"),
                ("p", "The GC starts from **GC Roots** (local variables on live stacks, static fields, active "
                      "threads) and follows every reference. Anything it can't reach is garbage."),
                ("code", """
GC Roots ──► Order ──► Customer        ✔ reachable  → kept
             Cart  ──► Item            ✘ unreachable → collected
"""),
                ("h", "The generational hypothesis"),
                ("ol", ["New objects are allocated in **Eden**.",
                        "Eden full → **Minor GC** (fast, only scans young gen). Survivors move to S0/S1.",
                        "Objects that survive several cycles are **promoted** to **Old Gen**.",
                        "Old Gen full → **Major / Full GC** (expensive, can pause the application)."]),
                ("table", [["Collector", "Best for", "Flag"],
                           ["**G1** (default)", "Most Spring Boot services, balanced", "`-XX:+UseG1GC`"],
                           ["**ZGC**", "Low-latency APIs, sub-millisecond pauses", "`-XX:+UseZGC` (generational by default in Java 23+)"],
                           ["**Parallel**", "Batch jobs, max throughput", "`-XX:+UseParallelGC`"]],
                 [0.18, 0.42, 0.40]),
                ("code", """
java -Xms512m -Xmx512m \\
     -XX:+UseG1GC -XX:MaxGCPauseMillis=200 \\
     -XX:+HeapDumpOnOutOfMemoryError \\
     -Xlog:gc*:file=gc.log \\
     -jar order-service.jar
"""),
                ("warn", "\"Java has GC, so I can't leak memory.\" Wrong. A `static Map` that you only `put()` into "
                         "is always reachable from a GC Root, so it grows until `OutOfMemoryError`. Use a bounded "
                         "cache (Caffeine `maximumSize` / `expireAfterAccess`) or an external store like Redis."),
                ("key", ["Objects on the heap, references and primitives on the stack.",
                         "GC removes only *unreachable* objects. Leaks are references you forgot to drop.",
                         "Most objects die young: cheap Minor GCs. Frequent Full GCs mean something is wrong."]),
            ],
            "questions": [
                "In `for (...) { Order temp = new Order(...); temp.validate(); }`, where does `temp` live and "
                "where do the `Order` objects live?",
                "After each iteration, is the previous `Order` eligible for GC? Why?",
                "Will these short-lived objects most likely be cleaned up by a Minor or Major GC?",
            ],
            "answer": [
                "`temp` is a reference on the thread's **stack**. Each `Order` object is on the **heap** (Eden).",
                "Yes. When `temp` is reassigned, the old object has no references left, so it is unreachable.",
                "**Minor GC.** They die young in Eden and are never promoted. That is exactly what the "
                "generational design optimises for.",
            ],
        },
        # ------------------------------------------------------------------ 1.2
        {
            "title": "Collections Internals: ArrayList, HashMap, ConcurrentHashMap",
            "blocks": [
                ("analogy", "A **HashMap** is a wall of **post-office boxes**. The box number is computed from "
                            "your name (the hash). To find your mail the clerk computes the number and opens one "
                            "box instead of searching the whole office. If two people get the same box (a "
                            "collision), their letters share it and the clerk checks each name (`equals`)."),
                ("h", "HashMap: how `put(key, value)` works"),
                ("code", """
 key.hashCode() ──► spread: h ^ (h >>> 16) ──► index = hash & (capacity - 1)

 table[16]
 ┌───┬───┬───┬───┬───┬─────┬───┐
 │ 0 │ 1 │ 2 │ 3 │ 4 │ ... │15 │
 └───┴─┬─┴───┴───┴─┬─┴─────┴───┘
       ▼           ▼
   [k1,v1]     [k7,v7]──►[k9,v9]     ← collision: linked list in the bucket
                                       (becomes a red-black tree when a bucket has > 8
                                        entries and capacity ≥ 64 → O(log n) worst case)
"""),
                ("ul", ["**Default capacity 16, load factor 0.75.** When size > capacity × 0.75, the table "
                        "doubles and every entry is rehashed (expensive). Pre-size big maps: `new HashMap<>(expected * 4 / 3 + 1)`.",
                        "Average `get`/`put` is **O(1)**; it degrades only with bad `hashCode()`s.",
                        "**Contract:** if `a.equals(b)` then `a.hashCode() == b.hashCode()`. Break it and lookups fail silently."]),
                ("h", "ArrayList vs LinkedList"),
                ("table", [["Operation", "ArrayList", "LinkedList"],
                           ["`get(i)`", "O(1): direct array index", "O(n): walk the nodes"],
                           ["Add at end", "Amortised O(1), grows ~1.5×", "O(1)"],
                           ["Insert in middle", "O(n): shift elements", "O(n) to find + O(1) to link"],
                           ["Memory / CPU cache", "Compact, cache-friendly", "Node object per element, scattered"]],
                 [0.25, 0.37, 0.38]),
                ("p", "In practice **ArrayList wins almost always**. For queues use `ArrayDeque`."),
                ("h", "Concurrent access"),
                ("p", "`HashMap` is not thread-safe: concurrent writes can lose entries. "
                      "`Collections.synchronizedMap` locks the *whole* map. `ConcurrentHashMap` uses CAS and locks only a single "
                      "bucket, so many threads can write at once."),
                ("code", """
// Thread-safe counter per product, no external locking needed
private final ConcurrentHashMap<String, LongAdder> views = new ConcurrentHashMap<>();

public void recordView(String productId) {
    views.computeIfAbsent(productId, id -> new LongAdder()).increment();
}
"""),
                ("warn", "Using a **mutable object as a HashMap key** and changing it after insertion. Its hashCode "
                         "changes, so the entry now sits in the \"wrong\" bucket and `get()` returns `null` even "
                         "though the entry is still there. Use immutable keys: `String`, `record`, `UUID`."),
                ("key", ["HashMap = array of buckets + hashing; good `hashCode`/`equals` are essential.",
                         "Default to `ArrayList`, `HashMap`, `ArrayDeque`; `ConcurrentHashMap` for shared state.",
                         "Java `record`s give you correct `equals`/`hashCode` for free, so they make ideal keys."]),
            ],
            "questions": [
                "You put 1,000,000 entries into a `new HashMap<>()`. Roughly how many resizes happen and how can you avoid them?",
                "Mini-challenge: write a `record` `OrderKey(String customerId, LocalDate date)` and explain why "
                "it is safe as a map key.",
            ],
            "answer": [
                "Capacity doubles from 16 until it exceeds 1,000,000 / 0.75 ≈ 1.33M, so 16 → 2,097,152 is "
                "**17 resizes**, each rehashing every entry. Pre-size with `new HashMap<>(1_400_000)` "
                "(or `HashMap.newHashMap(1_000_000)` in Java 19+).",
                ("code", "public record OrderKey(String customerId, LocalDate date) {}"),
                "Records are immutable (final fields) and generate `equals`/`hashCode` from all components, so the "
                "hash never changes after insertion.",
            ],
        },
        # ------------------------------------------------------------------ 1.3
        {
            "title": "Multithreading & Concurrency",
            "blocks": [
                ("analogy", "Two cashiers updating **one shared paper ledger**. Both read \"balance = 100\", both add "
                            "10, both write \"110\". One sale vanished. That is a **race condition**. A `synchronized` "
                            "block is a **single pen**: only the cashier holding it may write."),
                ("h", "The race condition"),
                ("code", """
class Counter {
    private int count = 0;
    public void increment() { count++; }   // NOT atomic: read → add → write
}
// 2 threads × 1000 increments → often prints ~1700, not 2000
"""),
                ("h", "Three fixes, from simplest to most flexible"),
                ("code", """
// 1. Atomic variable: lock-free, uses CPU compare-and-swap (CAS)
private final AtomicInteger count = new AtomicInteger();
public void increment() { count.incrementAndGet(); }

// 2. synchronized: mutual exclusion + memory visibility
public synchronized void increment() { count++; }

// 3. Explicit lock: tryLock with timeout, fairness, multiple conditions
private final ReentrantLock lock = new ReentrantLock();
public void increment() {
    lock.lock();
    try { count++; } finally { lock.unlock(); }   // ALWAYS unlock in finally
}
"""),
                ("p", "**`volatile`** only guarantees *visibility* (other threads see the latest value). It does "
                      "**not** make `count++` atomic. Use it for flags like `volatile boolean running`."),
                ("h", "Never create raw threads in a server: use executors"),
                ("code", """
ExecutorService pool = Executors.newFixedThreadPool(8);

CompletableFuture<User>    user    = CompletableFuture.supplyAsync(() -> userClient.get(id), pool);
CompletableFuture<List<Order>> orders = CompletableFuture.supplyAsync(() -> orderRepo.find(id), pool);

Dashboard d = user.thenCombine(orders, Dashboard::new)   // run both in parallel, then merge
                  .orTimeout(2, TimeUnit.SECONDS)
                  .join();
"""),
                ("h", "Deadlock"),
                ("code", """
 Thread A: holds lock(account1) ──waits for──► lock(account2)
 Thread B: holds lock(account2) ──waits for──► lock(account1)      ⇒ both wait forever

 Fix: always acquire locks in a global order (e.g. by account id).
"""),
                ("warn", "Sharing a non-thread-safe object across threads, e.g. a `SimpleDateFormat` in a "
                         "Spring singleton bean. Spring beans are singletons by default, so **every request "
                         "thread shares them**. Keep beans stateless, or use thread-safe types (`DateTimeFormatter`)."),
                ("key", ["Shared mutable state + multiple threads = race conditions.",
                         "Prefer immutability, then atomics/concurrent collections, then locks.",
                         "Use `ExecutorService` / `CompletableFuture`, never `new Thread()` per request."]),
            ],
            "questions": [
                "Why doesn't `volatile int count; count++;` fix the race condition?",
                "Your Spring `@Service` has a field `private List<String> errors = new ArrayList<>();` that each "
                "request appends to. What goes wrong under load?",
            ],
            "answer": [
                "`volatile` guarantees visibility, but `count++` is still three steps (read, add, write). Two "
                "threads can read the same value before either writes. You need atomicity: `AtomicInteger` or a lock.",
                "The service is a **singleton**, so all request threads share one `ArrayList`: data from different "
                "users mixes, and concurrent `add` can corrupt the list or throw. Make it a local variable inside the method.",
            ],
        },
        # ------------------------------------------------------------------ 1.4
        {
            "title": "Virtual Threads (Java 21+)",
            "blocks": [
                ("analogy", "Platform threads are like **restaurant tables**: expensive, so you only have 200. A "
                            "guest waiting for food still occupies a table. Virtual threads are **restaurant "
                            "pagers**: cheap and unlimited. A waiting guest just holds a pager while the table "
                            "(the real OS thread, the *carrier*) is used by someone who is actually eating."),
                ("code", """
  Platform thread model                     Virtual thread model
  ─────────────────────                     ────────────────────
  1 Java thread = 1 OS thread (~1 MB)       millions of virtual threads (~few KB)
                                                    │ mounted only while running
  200 threads, 200 blocked on DB            ┌───────▼─────────┐
   → request #201 waits in queue            │ carrier threads │  (≈ number of CPU cores)
                                            └─────────────────┘
                                            on blocking I/O the virtual thread is
                                            UNMOUNTED, so the carrier serves another one
"""),
                ("h", "Using them"),
                ("code", """
// Plain Java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    List<Future<Price>> prices = productIds.stream()
        .map(id -> executor.submit(() -> priceClient.fetch(id)))   // 10,000 tasks? fine
        .toList();
}

# Spring Boot 3.2+  (application.yml): Tomcat & @Async run on virtual threads
spring:
  threads:
    virtual:
      enabled: true
"""),
                ("table", [["Good fit", "Poor fit"],
                           ["I/O-bound work: REST calls, DB queries, Kafka, file I/O",
                            "CPU-bound work (image processing, crypto): use a bounded platform pool"],
                           ["Thread-per-request servers with high concurrency", "Code relying heavily on `ThreadLocal` caches"]],
                 [0.5, 0.5]),
                ("ul", ["**Don't pool virtual threads.** Create one per task; they are cheap.",
                        "**Limit downstream resources, not threads.** 10,000 virtual threads can still exhaust a "
                        "20-connection DB pool. Use a `Semaphore` or rely on the pool's timeout.",
                        "**Pinning:** in Java 21–23 a virtual thread blocking *inside* `synchronized` pins its "
                        "carrier. Prefer `ReentrantLock` there. Java 24 (JEP 491) removed most pinning."]),
                ("warn", "Turning on virtual threads and expecting CPU-heavy endpoints to get faster. Virtual "
                         "threads improve **throughput for waiting** (I/O), not raw computation speed."),
                ("key", ["Virtual threads = cheap, blocking-style code with async-level scalability.",
                         "Keep writing simple synchronous code; the JVM handles the unmounting.",
                         "Bottlenecks move to connection pools and downstream services, so watch those."]),
            ],
            "questions": [
                "Your service makes 3 slow REST calls (300 ms each) per request and gets 2,000 concurrent requests. "
                "Why do virtual threads help here, and what new bottleneck should you watch?",
            ],
            "answer": "Each request mostly *waits* on I/O. With 200 platform threads, requests queue; with virtual "
                      "threads all 2,000 can wait concurrently while a handful of carriers do the actual work. "
                      "The new bottleneck is downstream: HTTP client connection pools, DB pools and the "
                      "called services' capacity. Configure their limits and timeouts.",
        },
    ],
}

# Order: JVM → Collections → Java 8 … 25 language features → Multithreading → Virtual Threads
MODULE["topics"][2:2] = MODERN_JAVA
