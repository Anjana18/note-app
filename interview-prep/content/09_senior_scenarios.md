# Senior-Level Scenario & Coding Questions

## Write a thread-safe, generic, bounded producer-consumer without BlockingQueue.
```
class BoundedBuffer<T> {
    private final Deque<T> items = new ArrayDeque<>();
    private final int capacity;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();

    BoundedBuffer(int capacity) { this.capacity = capacity; }

    void put(T t) throws InterruptedException {
        lock.lock();
        try {
            while (items.size() == capacity) notFull.await();   // while, not if: spurious wakeups
            items.addLast(t);
            notEmpty.signal();
        } finally { lock.unlock(); }
    }

    T take() throws InterruptedException {
        lock.lock();
        try {
            while (items.isEmpty()) notEmpty.await();
            T t = items.removeFirst();
            notFull.signal();
            return t;
        } finally { lock.unlock(); }
    }
}
```

## Common Stream coding questions (write them live).
```
// 1. Frequency of each character
Map<Character, Long> freq = s.chars().mapToObj(c -> (char) c)
    .collect(Collectors.groupingBy(Function.identity(), LinkedHashMap::new, Collectors.counting()));

// 2. First non-repeating character
Optional<Character> first = freq.entrySet().stream()
    .filter(e -> e.getValue() == 1).map(Map.Entry::getKey).findFirst();

// 3. Second highest salary
Optional<Double> second = emps.stream().map(Employee::getSalary).distinct()
    .sorted(Comparator.reverseOrder()).skip(1).findFirst();

// 4. Partition into even and odd numbers
Map<Boolean, List<Integer>> parts = nums.stream().collect(Collectors.partitioningBy(n -> n % 2 == 0));

// 5. Highest-paid employee per department
Map<String, Optional<Employee>> top = emps.stream().collect(Collectors.groupingBy(
    Employee::getDept, Collectors.maxBy(Comparator.comparingDouble(Employee::getSalary))));

// 6. Find duplicates
Set<Integer> seen = new HashSet<>();
Set<Integer> dups = nums.stream().filter(n -> !seen.add(n)).collect(Collectors.toSet());

// 7. Join names, comma separated
String names = emps.stream().map(Employee::getName).collect(Collectors.joining(", ", "[", "]"));
```

## Production incident: latency spikes every few minutes. How do you investigate?
- **Correlate the timing** with GC logs (long full GCs?), cron or batch jobs, cache TTL expiry (stampede), autoscaling events, and DB maintenance or vacuum.
- Check thread pools and connection pools (Hikari `pending` threads), and downstream latency in distributed traces.
- Check the Kafka consumer rebalance logs, and whether pods are restarting (OOMKilled).
- Fix the root cause, add dashboards and alerts, and write a blameless postmortem with action items.

## Your service must handle 10x traffic next month. What do you do?
1. **Measure the baseline**: load test (Gatling, k6) against production-like data. Find the bottleneck (CPU, DB, locks, downstream dependencies).
2. **Scale horizontally**: stateless services, HPA/KEDA, a larger cluster, more DB read replicas.
3. **Reduce load**: caching, CDN, batching, asynchronous work through queues, pagination.
4. **Protect the system**: rate limiting, circuit breakers, bulkheads, load shedding, graceful degradation.
5. **Capacity plan** the DB (connections, IOPS, partitioning), Kafka partitions and cost. Run a game day or chaos test before the event.

## How do you ensure data consistency between the Order service DB and Kafka events?
Use the **Transactional Outbox**: write the order and an outbox event in one local ACID transaction. Debezium CDC or a poller publishes the outbox rows to Kafka with at-least-once delivery. Consumers deduplicate on the event ID (inbox table or unique constraint). Key messages by `orderId` so each order's events stay in order.

## How do you mentor developers and drive technical decisions? (Leadership)
- Write **ADRs** (Architecture Decision Records) that give the context, the options, the decision and the consequences.
- Run design reviews and RFCs. Give **code reviews** that teach, pair programming, and brown-bag sessions.
- Set standards: coding guidelines, shared libraries and templates (a golden-path starter), CI quality gates.
- Balance tech debt against features. Put debt in the backlog, argue for it with data (incident counts, lead time), and reserve around 20% of capacity for it.
- Use the **STAR** format (Situation, Task, Action, Result) for behavioural answers, with numbers where you have them: "cut p99 latency from 1.2 s to 180 ms", "reduced cloud cost by 30%".

## Rapid-fire questions to revise the night before.
- **Can we override static methods?** No. They are hidden, not overridden, and resolved at compile time.
- **Is Java pass-by-value?** Always. For objects, the reference is passed by value.
- **Why is `wait()` in Object and not Thread?** Because monitors belong to objects. Any object can be a lock.
- **What does `final`, `finally`, `finalize` mean?** A modifier, a cleanup block, and a deprecated GC hook (use Cleaner or try-with-resources instead).
- **Can a constructor be synchronized?** No. The object is not yet visible to other threads.
- **What is a marker interface?** An interface with no methods (Serializable, Cloneable). Today annotations are usually preferred.
- **What does `transient` do?** The field is skipped during serialization.
- **Difference between `@Component`, `@Service`, `@Repository`, `@Controller`?** All are stereotypes. `@Repository` adds exception translation to Spring's `DataAccessException`.
- **`@RestController` vs `@Controller`?** `@RestController` = `@Controller` + `@ResponseBody`.
- **Why can't we have a HashMap with primitive keys?** Generics need objects, so keys are autoboxed.
- **Kafka: can two consumers in the same group read the same partition?** No. Only one consumer per partition within a group.
- **Kubernetes: what gets a pod restarted, and what removes it from load balancing?** A failed liveness probe restarts it. A failed readiness probe removes it from the Service.
