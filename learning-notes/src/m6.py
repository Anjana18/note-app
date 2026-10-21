MODULE = {
    "title": "Microservices & Event Streaming",
    "intro": "Microservices let teams ship independently, but they turn method calls into network calls and "
             "one database transaction into many. Kafka and the Saga pattern are the standard tools for "
             "keeping a distributed system consistent and decoupled.",
    "topics": [
        # ------------------------------------------------------------------ 6.1
        {
            "title": "Microservice Architecture Fundamentals",
            "blocks": [
                ("analogy", "A monolith is **one big restaurant kitchen**: easy to coordinate, but one grease "
                            "fire closes everything. Microservices are a **food court**: each stall (service) "
                            "has its own kitchen and pantry (database), stalls can open, close or renovate "
                            "independently, but customers now walk between stalls and stalls must talk."),
                ("code", """
                         ┌──────────────┐
   Mobile / Web ───────► │ API Gateway  │  auth, rate limiting, routing
                         └──────┬───────┘
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ┌─────────────┐       ┌─────────────┐       ┌──────────────┐
   │ Order Svc   │       │ Catalog Svc │       │ Payment Svc  │
   │ PostgreSQL  │       │ MongoDB     │       │ PostgreSQL   │   ← database per service
   └──────┬──────┘       └──────┬──────┘       └──────┬───────┘
          │ publish events      │ Redis cache         │
          ▼                     ▼                     ▼
   ════════════════════ Apache Kafka (event backbone) ════════════════════
          ▲                                           ▲
   ┌──────┴───────┐                           ┌───────┴──────────┐
   │ Inventory Svc│                           │ Notification Svc │
   └──────────────┘                           └──────────────────┘
"""),
                ("h", "Core principles"),
                ("ul", ["**Database per service.** No other service reads your tables; they call your API or "
                        "consume your events.",
                        "**Bounded contexts** (from DDD): split by business capability (Orders, Payments), not by "
                        "technical layer (\"DB service\").",
                        "**Sync vs async:** use REST/gRPC when you need an answer *now* (price lookup); use events "
                        "when others just need to *know* something happened (OrderPlaced).",
                        "**Observability is mandatory:** correlation IDs, distributed tracing (OpenTelemetry), "
                        "centralised logs and metrics."]),
                ("table", [["", "Synchronous (REST)", "Asynchronous (Kafka events)"],
                           ["Coupling", "Caller depends on callee being up", "Producer doesn't know consumers"],
                           ["Latency", "Adds up along the call chain", "Caller returns immediately"],
                           ["Consistency", "Immediate", "Eventual"],
                           ["Failure", "Cascades without circuit breakers", "Events wait in Kafka until consumers recover"]],
                 [0.18, 0.41, 0.41]),
                ("warn", "The **distributed monolith**: services that share one database, or must all be deployed "
                         "together, or form long synchronous chains (A→B→C→D). You pay the cost of microservices "
                         "without the benefits. Start with a well-modularised monolith and split when a "
                         "boundary is clear."),
                ("key", ["Each service owns its data and can be deployed independently.",
                         "Prefer events for propagating state changes; sync calls for queries needing an answer.",
                         "Microservices are an organisational scaling tool. Don't start with 20."]),
            ],
            "questions": [
                "After an order is placed you must: reserve stock, send a confirmation email, and update a "
                "sales dashboard. Which should be synchronous calls and which async events? Why?",
            ],
            "answer": "Publish one `OrderPlaced` event. Email and dashboard are clearly **async**: the user "
                      "shouldn't wait for them and they can catch up later. Stock reservation can be async too, "
                      "as a step in a **Saga** (next topics). Make it a sync call only if the UI must show "
                      "\"in stock\" before confirming, and even then, protect it with a timeout and a circuit breaker.",
        },
        # ------------------------------------------------------------------ 6.2
        {
            "title": "Kafka: Topics, Partitions & Consumer Groups",
            "blocks": [
                ("analogy", "A Kafka **topic** is a **bank** with several **teller queues** (partitions). Each "
                            "customer (message) with the same account number (key) always joins the **same "
                            "queue**, so their transactions are processed in order. A **consumer group** is the "
                            "team of tellers: each queue is served by exactly one teller, but one teller can "
                            "handle several queues. Hire more tellers than queues and the extras stand idle."),
                ("code", """
 Topic "orders" (3 partitions)                   Consumer group "inventory-svc"
 ─────────────────────────────                   ──────────────────────────────
 P0: [o1][o4][o7][o9] ───────────────────────►  Consumer A  (P0)
 P1: [o2][o5][o8]     ───────────────────────►  Consumer B  (P1, P2)
 P2: [o3][o6]         ──────────────────────┘

 partition = hash(key) % 3     → same orderId ⇒ same partition ⇒ ordered
 offsets: each group tracks its own position per partition (P0 @ 4, P1 @ 2 ...)

 Another group "notification-svc" reads the SAME messages independently (pub/sub).
"""),
                ("table", [["Concept", "Rule to remember"],
                           ["Ordering", "Guaranteed **only within a partition**, so pick the key that needs ordering (orderId, customerId)"],
                           ["Parallelism", "Max active consumers in a group = **number of partitions**"],
                           ["Retention", "Messages stay for the retention period even after being read; consumers can replay"],
                           ["Rebalance", "When consumers join/leave/crash, partitions are reassigned; consumption pauses briefly"]],
                 [0.2, 0.8]),
                ("h", "Producer (Spring Kafka)"),
                ("code", """
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      acks: all                        # wait for all in-sync replicas
      properties:
        enable.idempotence: true       # no duplicates on producer retry
    consumer:
      group-id: inventory-svc
      auto-offset-reset: earliest
      enable-auto-commit: false        # Spring commits after the listener succeeds

@Service
@RequiredArgsConstructor
public class OrderEventPublisher {
    private final KafkaTemplate<String, OrderPlaced> kafka;

    public void publish(OrderPlaced event) {
        kafka.send("orders", event.orderId(), event);      // key = orderId → ordering per order
    }
}
"""),
                ("h", "Consumer"),
                ("code", """
@Component
@RequiredArgsConstructor
public class InventoryListener {
    private final InventoryService inventory;

    @KafkaListener(topics = "orders", concurrency = "3")    // 3 consumer threads ≤ 3 partitions
    public void onOrderPlaced(OrderPlaced event) {
        inventory.reserve(event.orderId(), event.items());  // must be idempotent (see 6.4)
    }
}
"""),
                ("warn", "**Endless rebalancing.** A listener does slow work (e.g. 10 min batch) and exceeds "
                         "`max.poll.interval.ms` (default 5 min). Kafka assumes the consumer is dead, rebalances, "
                         "another consumer re-reads the same messages, also times out... Fix: keep processing "
                         "fast, reduce `max.poll.records`, or increase the interval. Watch logs for "
                         "\"Revoking partitions\" / \"rebalance\"."),
                ("key", ["Key → partition → ordering. No key = round-robin, no ordering.",
                         "Partitions cap parallelism; plan partition count for future scale.",
                         "Each consumer group gets every message; consumers within a group share partitions."]),
            ],
            "questions": [
                "A topic has 4 partitions. You scale your consumer service to 6 pods (same group). How many "
                "pods actually consume? What would you change to use all 6?",
            ],
            "answer": "Only **4** consume; 2 sit idle because each partition is assigned to one consumer in a "
                      "group. To use 6, increase the topic to ≥ 6 partitions. Note: adding partitions changes "
                      "`hash(key) % n`, so key-to-partition mapping changes for future messages. Plan ahead.",
        },
        # ------------------------------------------------------------------ 6.3
        {
            "title": "The Saga Pattern & Transactional Outbox",
            "blocks": [
                ("analogy", "Booking a **holiday**: flight, hotel and car from three different companies. There's "
                            "no single \"undo\" button across companies. If the car rental fails, you **cancel** "
                            "the hotel and the flight yourself. A Saga is a sequence of local transactions where "
                            "each step has a **compensating action** that undoes it."),
                ("code", """
 HAPPY PATH (choreography: services react to each other's events)
 Order Svc ──OrderCreated──► Payment Svc ──PaymentCompleted──► Inventory Svc ──StockReserved──► Order Svc
   PENDING                                                                                 → CONFIRMED

 FAILURE + COMPENSATION
 Order Svc ──OrderCreated──► Payment Svc ──PaymentCompleted──► Inventory Svc
                                   ▲                                │ out of stock
                                   └────────── StockFailed ◄────────┘
                              refund (compensate)
 Order Svc ◄─── PaymentRefunded ───┘        → order CANCELLED
"""),
                ("table", [["", "Choreography", "Orchestration"],
                           ["How", "Each service listens & reacts to events", "A central orchestrator sends commands step by step"],
                           ["Pros", "Loose coupling, simple for 2–4 steps", "Flow is explicit in one place; easier to monitor/change"],
                           ["Cons", "Flow is implicit, hard to trace as it grows", "Orchestrator is extra component; risk of \"god service\""],
                           ["Tools", "Kafka + listeners", "Temporal, Camunda, or a custom state machine"]],
                 [0.12, 0.44, 0.44]),
                ("h", "The dual-write problem"),
                ("code", """
@Transactional
public void createOrder(...) {
    orderRepo.save(order);                       // 1. DB write
    kafka.send("orders", new OrderCreated(...)); // 2. Kafka write ✘
}
// Kafka succeeds but DB rolls back → phantom event.  DB commits but app crashes → lost event.
"""),
                ("h", "Fix: Transactional Outbox"),
                ("code", """
 ┌───────────── one DB transaction ─────────────┐
 │  INSERT INTO orders ...                      │
 │  INSERT INTO outbox (aggregate_id, type,     │      ┌──────────────┐
 │                      payload, created_at)    │ ───► │ Relay / CDC  │ ──► Kafka
 └──────────────────────────────────────────────┘      │ (poller or   │
                                                       │  Debezium)   │
                                                       └──────────────┘
"""),
                ("code", """
@Transactional
public Order createOrder(CreateOrder cmd) {
    Order order = orderRepo.save(Order.pending(cmd));
    outboxRepo.save(OutboxEvent.of("Order", order.getId(), "OrderCreated", toJson(order)));
    return order;                     // both rows commit or neither does
}

@Scheduled(fixedDelay = 1000)        // simple poller; Debezium CDC is the production-grade option
@Transactional
public void relay() {
    for (OutboxEvent e : outboxRepo.findTop100ByPublishedFalseOrderByIdAsc()) {
        kafka.send("orders", e.aggregateId(), e.payload()).join();
        e.markPublished();
    }
}
"""),
                ("warn", "Forgetting that compensations are **business actions, not rollbacks**. You can't "
                         "\"un-send\" an email; you send a cancellation. Design each step's compensation up front, "
                         "and make it idempotent, because it may run more than once."),
                ("key", ["Saga = local transactions + compensating actions; eventual consistency.",
                         "Choreography for small flows, orchestration for complex ones.",
                         "Use the Outbox pattern to atomically save state *and* publish events."]),
            ],
            "questions": [
                "Mini-challenge: list the Saga steps and compensations for \"Place Order\" involving Order, "
                "Payment and Inventory services. Which step should be last, and why?",
            ],
            "answer": [
                "1. Order: create `PENDING` (compensate: mark `CANCELLED`).",
                "2. Inventory: reserve stock (compensate: release reservation).",
                "3. Payment: charge card (compensate: refund).",
                "4. Order: mark `CONFIRMED`.",
                "Put the step that is **hardest or most costly to compensate** (charging money, since refunds "
                "take days and annoy customers) as late as possible, after cheap, reversible steps like stock "
                "reservation have succeeded.",
            ],
        },
        # ------------------------------------------------------------------ 6.4
        {
            "title": "Delivery Guarantees, Idempotency & Dead-Letter Topics",
            "blocks": [
                ("analogy", "A **courier who might ring twice**. If they're unsure you received the parcel, they "
                            "deliver again. Your job is to check the tracking number and say \"already got it, "
                            "thanks\" instead of paying twice. That's an **idempotent consumer**."),
                ("table", [["Guarantee", "Meaning", "Reality"],
                           ["At-most-once", "Commit offset before processing; may lose messages", "Rarely acceptable"],
                           ["**At-least-once**", "Commit after processing; may get duplicates", "**The practical default**"],
                           ["Exactly-once", "Kafka transactions (read-process-write within Kafka)",
                            "Doesn't cover side effects outside Kafka (DB, email, HTTP)"]],
                 [0.2, 0.45, 0.35]),
                ("h", "Idempotent consumer"),
                ("code", """
CREATE TABLE processed_events (event_id UUID PRIMARY KEY, processed_at TIMESTAMPTZ NOT NULL);

@KafkaListener(topics = "payments")
@Transactional
public void onPaymentCompleted(PaymentCompleted e) {
    if (processedRepo.existsById(e.eventId())) return;          // duplicate → ignore
    orderService.markPaid(e.orderId());
    processedRepo.save(new ProcessedEvent(e.eventId(), Instant.now()));
    // same DB transaction: both happen or neither. The PK also blocks concurrent duplicates.
}
"""),
                ("h", "Retries and Dead-Letter Topics"),
                ("code", """
@Bean
DefaultErrorHandler errorHandler(KafkaTemplate<Object, Object> template) {
    var recoverer = new DeadLetterPublishingRecoverer(template);         // → "<topic>-dlt"
    var backoff = new ExponentialBackOffWithMaxRetries(3);
    backoff.setInitialInterval(500); backoff.setMultiplier(2.0);
    var handler = new DefaultErrorHandler(recoverer, backoff);
    handler.addNotRetryableExceptions(ValidationException.class);       // poison: straight to DLT
    return handler;
}
"""),
                ("warn", "A **poison message** (malformed JSON, invalid data) with infinite retries blocks the "
                         "whole partition: every message behind it waits forever. Always configure bounded "
                         "retries + a DLT, alert on DLT growth, and build a way to inspect and replay it."),
                ("key", ["Assume at-least-once: every consumer must handle duplicates.",
                         "Idempotency via unique event IDs, upserts or natural keys.",
                         "Bounded retries with backoff, then a dead-letter topic."]),
            ],
            "questions": [
                "Your consumer charges a loyalty-points bonus on `OrderDelivered`. The pod crashes after "
                "adding points but before the offset commit. What happens on restart, and how do you prevent "
                "double points?",
            ],
            "answer": "The offset wasn't committed, so the message is **redelivered** and points are added "
                      "again. Prevent it by storing the `eventId` in a `processed_events` table in the "
                      "**same DB transaction** as the points update (or use a unique constraint like "
                      "`(order_id, bonus_type)`), and skip when it already exists.",
        },
    ],
}
