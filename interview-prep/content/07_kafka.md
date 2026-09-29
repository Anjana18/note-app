# Apache Kafka

## Explain Kafka's architecture.
Kafka is a **distributed, partitioned, replicated commit log** used for event streaming.
- **Broker**: a Kafka server. A **cluster** has many brokers.
- **Topic**: a named stream of records. It is split into **partitions**, which are ordered, append-only logs.
- **Offset**: the sequential position of a record within its partition.
- **Replication**: each partition has one **leader** and several **followers**. The **ISR** (in-sync replicas) are the followers that are caught up with the leader.
- **Producers** write to the leader of a partition. **Consumers** in a **consumer group** split the partitions between them.
- **Controller**: manages the cluster metadata. **KRaft** mode (the Raft protocol) replaced **ZooKeeper**. KRaft has been production-ready since 3.3, and Kafka 4.0 removed ZooKeeper completely.
- Kafka is fast because of **sequential disk I/O**, the **OS page cache**, **zero-copy** (`sendfile`), batching and compression.

## How do partitions and consumer groups work? How does Kafka guarantee ordering?
- **Ordering is guaranteed only within a partition**. Records with the **same key** go to the same partition (by default `hash(key) % numPartitions`). So key by `orderId` to keep all events for one order in order.
- Within a consumer group, **each partition is assigned to exactly one consumer**. Extra consumers beyond the number of partitions sit idle, so **the partition count caps parallelism**.
- Different consumer groups each receive **all** messages independently (pub/sub).
- **Increasing the partition count** changes the key-to-partition mapping and breaks ordering for existing keys. Plan the count up front.

## Explain delivery semantics: at-most-once, at-least-once, exactly-once.
- **At-most-once**: commit the offset **before** processing. A crash loses messages.
- **At-least-once** (the most common): process first, **then** commit. A crash causes duplicates, so **consumers must be idempotent**.
- **Exactly-once (EOS)**: an **idempotent producer** (`enable.idempotence=true`, which uses producer ID and sequence numbers to drop duplicates on retry) plus **transactions** (`transactional.id`) plus consumers with `isolation.level=read_committed`. It covers read-process-write **within Kafka** (e.g. Kafka Streams with `processing.guarantee=exactly_once_v2`).
- For side effects **outside** Kafka (DB writes, REST calls), you still need idempotency or the outbox/inbox patterns.

## Which producer configurations matter for reliability?
- `acks=all`: the leader waits for all ISR replicas. Combine it with `min.insync.replicas=2` and `replication.factor=3`, so writes survive one broker failure.
- `enable.idempotence=true` (the default since Kafka 3.0), `retries` (effectively unlimited), `delivery.timeout.ms`.
- `max.in.flight.requests.per.connection <= 5` keeps ordering when idempotence is on.
- Throughput: `batch.size`, `linger.ms` (e.g. 5-20 ms), `compression.type=lz4` or `zstd`.
- `unclean.leader.election.enable=false`, so a replica that is out of sync never becomes leader and loses data.

## Explain consumer offsets, commits and rebalancing.
- Committed offsets are stored in the internal topic `__consumer_offsets`.
- **Auto commit** (`enable.auto.commit=true`, every 5 s) can lose or duplicate messages. Prefer **manual commits** after processing (`commitSync` or `commitAsync`, or Spring's `AckMode.MANUAL` / `RECORD` / `BATCH`).
- A **rebalance** happens when consumers join or leave, or when `max.poll.interval.ms` is exceeded (slow processing). Partitions are reassigned. With eager rebalancing, all consumption stops during it.
- **Improvements**: the **CooperativeStickyAssignor** (incremental rebalancing), **static group membership** (`group.instance.id`) to avoid rebalances on rolling restarts, and the new consumer rebalance protocol (KIP-848).
- Tune `max.poll.records` and `max.poll.interval.ms` so that one batch always finishes processing within the interval.

## How do you handle failures and poison messages? (Retry + DLT)
- A **poison pill** is a message that always fails (bad format, bad data). If you don't handle it, the consumer retries it forever and **blocks the partition**.
- Spring Kafka's `DefaultErrorHandler` retries with a backoff, then hands the record to a `DeadLetterPublishingRecoverer` which sends it to `topic.DLT`.
- **Non-blocking retries** (`@RetryableTopic`) send failed records to retry topics with increasing delays, so the main topic keeps flowing. The trade-off is that ordering is lost.
- Mark exceptions as **non-retryable** (e.g. validation or deserialisation errors), use `ErrorHandlingDeserializer`, and monitor and replay the DLT.
```
@RetryableTopic(attempts = "4", backoff = @Backoff(delay = 1000, multiplier = 2),
                exclude = ValidationException.class)
@KafkaListener(topics = "orders", groupId = "billing")
public void onOrder(OrderEvent e) { billing.process(e); }

@DltHandler
public void dlt(OrderEvent e, @Header(KafkaHeaders.EXCEPTION_MESSAGE) String err) {
    alerting.notify(e, err);
}
```

## What is consumer lag and how do you fix a growing lag?
Lag = the log-end offset minus the committed offset. A growing lag means consumers can't keep up.
- **Monitor it**: Burrow, Kafka Exporter -> Prometheus, Confluent Control Center, Azure Monitor.
- **Fixes**: add consumers (up to the partition count), add partitions (with care for ordering), speed up processing (batch DB writes, async I/O, remove slow calls), tune `max.poll.records` and fetch sizes, and scale automatically on lag with **KEDA**.

## Retention vs log compaction?
- **Retention** (`retention.ms` / `retention.bytes`): delete old segments by time or size. Kafka is **not** a queue, so messages stay after they are consumed and can be **replayed**.
- **Log compaction** (`cleanup.policy=compact`): keep **only the latest value per key**. A null value (**tombstone**) deletes the key. Use it for changelog and state topics such as customer profiles and KTable backing topics.

## What is Schema Registry and why use Avro or Protobuf?
- Schema Registry stores versioned schemas. Messages carry only a small **schema ID** instead of the full schema.
- It enforces **compatibility** (BACKWARD, FORWARD, FULL), so producers cannot break consumers.
- Avro and Protobuf are compact binary formats with clear rules for evolving schemas (add fields with defaults, never reuse field IDs).
- Options: Confluent Schema Registry, or **Azure Schema Registry** in Event Hubs.

## Kafka vs RabbitMQ vs Azure Service Bus vs Event Hubs?
- **Kafka**: a high-throughput, replayable log. Streaming, event sourcing, CDC pipelines. Consumers pull.
- **RabbitMQ**: a traditional broker with smart routing (exchanges). Messages are deleted once acknowledged. Task queues and RPC.
- **Azure Service Bus**: an enterprise broker with **queues and topics/subscriptions**, **sessions** (FIFO per session ID), **duplicate detection**, **scheduled messages**, a **built-in DLQ** and transactions. Best for **commands and business workflows**.
- **Azure Event Hubs**: big-data **event streaming** (telemetry, logs). It exposes a **Kafka-compatible endpoint**, so existing Kafka clients work by only changing configuration.

## What is Kafka Streams / Kafka Connect?
- **Kafka Streams**: a Java library for stateful stream processing (joins, windowed aggregations, KStream / KTable). State is kept in RocksDB and backed up to changelog topics. It supports exactly-once, and needs no separate cluster.
- **Kafka Connect**: a framework for moving data in and out of Kafka without writing code. **Source** connectors (e.g. **Debezium CDC** from Postgres or MySQL) and **Sink** connectors (Elasticsearch, S3, Blob Storage, JDBC).

## How do you produce and consume with Spring Kafka?
```
@Service
class OrderEventPublisher {
    private final KafkaTemplate<String, OrderEvent> kafka;
    OrderEventPublisher(KafkaTemplate<String, OrderEvent> kafka) { this.kafka = kafka; }

    void publish(OrderEvent e) {
        kafka.send("orders", e.orderId(), e)             // key = orderId keeps its events ordered
             .whenComplete((res, ex) -> {
                 if (ex != null) log.error("Publish failed", ex);
             });
    }
}

@KafkaListener(topics = "orders", groupId = "inventory", concurrency = "3")
public void consume(ConsumerRecord<String, OrderEvent> rec, Acknowledgment ack) {
    inventory.reserve(rec.value());   // idempotent
    ack.acknowledge();                // manual commit after success
}
```

## How would you size a Kafka topic (partitions)?
- Partitions = max(target throughput / producer throughput per partition, target throughput / consumer throughput per partition). For example, 100 MB/s ÷ 10 MB/s per consumer = at least 10 partitions. Add headroom for growth.
- Too many partitions mean more open files, longer leader elections and more memory. Aim for thousands per broker at most.
- Key choice matters too: a skewed key (one huge customer) creates a **hot partition**.
