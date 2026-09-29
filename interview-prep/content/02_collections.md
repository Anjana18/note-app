# Collections Framework (In Depth)

## Explain the Collections Framework hierarchy.
- **Iterable** -> **Collection** -> **List** (ArrayList, LinkedList, Vector/Stack, CopyOnWriteArrayList)
- **Collection** -> **Set** (HashSet, LinkedHashSet, **SortedSet/NavigableSet**: TreeSet, plus EnumSet and CopyOnWriteArraySet)
- **Collection** -> **Queue** (PriorityQueue, **Deque**: ArrayDeque and LinkedList, **BlockingQueue**: ArrayBlockingQueue, LinkedBlockingQueue, PriorityBlockingQueue, DelayQueue, SynchronousQueue)
- **Map** is a **separate hierarchy** and does not extend Collection: HashMap, LinkedHashMap, TreeMap (SortedMap/NavigableMap), Hashtable, ConcurrentHashMap, WeakHashMap, IdentityHashMap, EnumMap, ConcurrentSkipListMap.
- Utility classes: `Collections` (sort, unmodifiableX, synchronizedX) and `Arrays`.
- Java 21 **SequencedCollection / SequencedMap** add `getFirst()`, `getLast()` and `reversed()` to ordered collections.

## How does HashMap work internally? (The most-asked collections question)
- It is backed by an **array of buckets** (`Node<K,V>[] table`). The default capacity is **16** and the **load factor is 0.75**.
- **put(k, v)**: compute `hash = h ^ (h >>> 16)` (this spreads the high bits into the low bits), then `index = (n - 1) & hash`. Capacity is always a power of two, so this equals `hash % n` but is faster.
- If the bucket is empty, store a new node. Otherwise walk the bucket: if a key is `equals`, replace its value; if not, append to the chain.
- **Treeification (Java 8)**: when one bucket's chain grows beyond **8** nodes **and** the table capacity is at least **64**, the chain becomes a **red-black tree**. Worst-case lookup improves from O(n) to O(log n). It turns back into a list when it shrinks to **6**.
- **Resize**: when size > capacity x load factor (12 for the default), the table **doubles**. Every entry either stays at index `i` or moves to `i + oldCap`, decided by a single bit. Java 8 keeps the order, which fixed the infinite-loop problem Java 7 had during concurrent resize.
- One **null key** is allowed (it always goes to bucket 0), and many null values are allowed.
- **Not thread-safe**.
```
// Performance tip: pre-size when the count is known, to avoid rehashing
Map<String, User> map = new HashMap<>((int) (expected / 0.75f) + 1);
// Java 19+: HashMap.newHashMap(expected)
```
> Follow-up: "What if all keys return the same hashCode?" Everything goes into one bucket. Before Java 8 that meant O(n) lookups. From Java 8 it becomes a tree with O(log n) lookups, provided the keys are Comparable. This was the fix for **hash-flooding DoS** attacks.

## HashMap vs Hashtable vs ConcurrentHashMap vs Collections.synchronizedMap?
- **HashMap**: not synchronized. Allows one null key and null values. The fastest option for a single thread.
- **Hashtable**: legacy. Every method is synchronized (one lock for the whole table). No nulls.
- **synchronizedMap**: a wrapper with one lock around every method. Iterating over it still needs a manual `synchronized(map)` block.
- **ConcurrentHashMap**: high concurrency. **No null keys or values**, because a null `get` would be ambiguous between "absent" and "mapped to null". Its iterators are weakly consistent.

## How does ConcurrentHashMap achieve thread safety?
- **Java 7**: **Segments** (16 by default), each one a ReentrantLock guarding its own mini-table. This was lock striping.
- **Java 8+**: no segments. Inserting into an **empty bucket uses CAS** (no lock). A non-empty bucket is locked with `synchronized` **on the bucket's first node**, so only that bucket is locked. **Reads are lock-free** because node values and next pointers are volatile.
- **Resizing is cooperative**: threads that call `put` while a resize is running help move buckets (`ForwardingNode`).
- `size()` uses a counter-cell design like LongAdder. On big maps use `mappingCount()`.
- **Atomic compound operations**: `putIfAbsent`, `computeIfAbsent`, `compute`, `merge`. Never write check-then-act code like `if (!map.containsKey(k)) map.put(k, v)`.
```
ConcurrentHashMap<String, LongAdder> hits = new ConcurrentHashMap<>();
hits.computeIfAbsent(url, k -> new LongAdder()).increment();

Map<String, Integer> wordCount = new ConcurrentHashMap<>();
words.forEach(w -> wordCount.merge(w, 1, Integer::sum));
```

## ArrayList vs LinkedList? When would you use each?
- **ArrayList**: a dynamic array. `get(i)` is **O(1)**. Adding at the end is amortised O(1). Inserting or removing in the middle is O(n) because elements shift. Growth is 1.5x (`newCap = old + old >> 1`). It is **cache-friendly** because elements are contiguous.
- **LinkedList**: a doubly linked list. `get(i)` is O(n). Insert and remove are O(1) **only if you already hold the node** (through an iterator). Every node has extra memory overhead and poor cache locality.
- **In practice, ArrayList wins almost always**. For queue or stack use, prefer **ArrayDeque** to LinkedList.
- `Vector` is a synchronized, legacy version of ArrayList. `Stack` is legacy too, so use `ArrayDeque` instead.

## HashSet, LinkedHashSet and TreeSet: how are they implemented?
- **HashSet** is backed by a **HashMap**: the element is the key and a dummy `PRESENT` object is the value. O(1) operations, no ordering.
- **LinkedHashSet** is backed by a LinkedHashMap and keeps **insertion order**.
- **TreeSet** is backed by a **TreeMap** (red-black tree). Elements are **sorted**, operations are O(log n), and it offers navigation methods: `floor`, `ceiling`, `headSet`, `tailSet`, `first`, `last`.
- TreeSet decides uniqueness with **compareTo/compare**, not `equals`. Keep compareTo consistent with equals, or elements will silently go missing.

## How does LinkedHashMap work? Build an LRU cache.
LinkedHashMap is a HashMap plus a **doubly linked list** through its entries. It keeps **insertion order**, or **access order** when you pass `accessOrder=true`. Override `removeEldestEntry` and you have an LRU cache.
```
class LruCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;
    LruCache(int capacity) {
        super(capacity, 0.75f, true);   // true = access order
        this.capacity = capacity;
    }
    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity;
    }
}
// Not thread-safe: wrap it, or use Caffeine in production.
```

## TreeMap internals and when to use it?
TreeMap is a **red-black tree**, a self-balancing BST. `get`, `put` and `remove` are O(log n). Keys are kept sorted by natural order or by a Comparator. No null keys (with natural ordering).
- **Use it for**: range queries (`subMap`, `headMap`, `tailMap`), nearest lookups (`floorKey`, `ceilingKey`), time-bucketed data, leaderboards and consistent-hashing rings.
- For concurrent use there is **ConcurrentSkipListMap**.

## Comparable vs Comparator?
- **Comparable** (`compareTo`) is the **natural ordering** and lives inside the class. There is one per class.
- **Comparator** (`compare`) is an **external ordering strategy**. You can have many. Java 8 made them easy to compose:
```
employees.sort(Comparator.comparing(Employee::getDept)
    .thenComparing(Employee::getSalary, Comparator.reverseOrder())
    .thenComparing(Employee::getName, Comparator.nullsLast(String::compareTo)));
```
> Never compare by subtraction (`a - b`). It overflows. Use `Integer.compare(a, b)`.

## Fail-fast vs fail-safe iterators?
- **Fail-fast** (ArrayList, HashMap): the collection has a `modCount`. If the collection is modified structurally during iteration (except through `iterator.remove()`), the next call throws **ConcurrentModificationException**. This is best-effort and happens even with a single thread.
- **Fail-safe / weakly consistent** (ConcurrentHashMap, CopyOnWriteArrayList): no exception. They iterate over a snapshot (CopyOnWrite) or a weakly consistent view (CHM), so they may not show recent changes.
```
// Wrong: throws ConcurrentModificationException
for (String s : list) if (s.isEmpty()) list.remove(s);
// Right
list.removeIf(String::isEmpty);
```

## What is CopyOnWriteArrayList and when should you use it?
Every write (add or set) **copies the whole underlying array**. Reads need no locks and iterators use a snapshot.
- **Use it** when reads vastly outnumber writes, e.g. listener or observer lists and rarely changing configuration.
- **Avoid it** when writes are frequent or the list is large. Each write is O(n) and creates garbage.

## Explain BlockingQueue implementations and the producer-consumer pattern.
- `put()` blocks when the queue is full and `take()` blocks when it is empty. `offer` and `poll` accept timeouts.
- **ArrayBlockingQueue**: bounded, array-backed, one lock.
- **LinkedBlockingQueue**: optionally bounded (unbounded by default, so be careful), with separate put and take locks for higher throughput.
- **PriorityBlockingQueue**: unbounded and ordered by priority.
- **DelayQueue**: elements become available only after their delay expires. Useful for scheduled retries.
- **SynchronousQueue**: no capacity, every put waits for a take. Used by cached thread pools.
```
BlockingQueue<Order> q = new ArrayBlockingQueue<>(1000);
// producer
q.put(order);
// consumer
while (running) { Order o = q.take(); process(o); }
```

## PriorityQueue: how does it work? Solve "top K".
It is a **binary min-heap** stored in an array. `offer` and `poll` are O(log n), `peek` is O(1). Iteration order is **not** sorted.
```
// Top K largest numbers: keep a min-heap of size K -> O(n log k)
PriorityQueue<Integer> heap = new PriorityQueue<>();
for (int n : nums) {
    heap.offer(n);
    if (heap.size() > k) heap.poll();
}
```

## WeakHashMap, IdentityHashMap and EnumMap: use cases?
- **WeakHashMap**: keys are held through **WeakReferences**. An entry disappears once its key is no longer strongly referenced anywhere else. Used for metadata caches keyed by objects with a lifecycle. Keys such as String literals never get collected.
- **IdentityHashMap**: compares keys with `==` instead of equals. Used for graph traversal, serialization and proxies.
- **EnumMap / EnumSet**: backed by an array or bit vector, so they are very fast and compact. Always prefer them when the keys are enums.

## Unmodifiable vs immutable collections?
- `Collections.unmodifiableList(list)` is a **read-only view**. Changes to the underlying list still show through it.
- `List.of()`, `Set.of()`, `Map.of()` and `List.copyOf()` (Java 9/10) are **truly immutable**. They reject nulls, and `Set.of` / `Map.of` throw on duplicates. Iteration order of `Set.of` and `Map.of` is unspecified.
- `stream.toList()` (Java 16) returns an unmodifiable list. `Collectors.toList()` makes no such guarantee (it is an ArrayList in practice).

## Big-O cheat sheet for common collections.
- **ArrayList**: get O(1), add O(1) amortised, insert/remove in the middle O(n), contains O(n).
- **LinkedList**: get O(n), add/remove at the ends O(1), contains O(n).
- **HashMap / HashSet**: get/put/remove O(1) on average, O(log n) worst case (tree bins, Java 8+).
- **TreeMap / TreeSet**: O(log n).
- **PriorityQueue**: offer/poll O(log n), peek O(1).
- **ArrayDeque**: add/remove at both ends O(1).

## Can a mutable object be used as a HashMap key? What happens?
Technically yes, but it is dangerous. If you change a field used in hashCode after inserting the key, the entry stays in the **old bucket**. Both `get()` and `remove()` then fail and the entry leaks. **Always use immutable keys** (String, Integer, records, value objects).
