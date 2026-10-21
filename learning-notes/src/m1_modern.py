"""Modern Java language features (Java 8 → 25), spliced into Module 1."""

TOPICS = [
    # ------------------------------------------------------------------ Lambdas
    {
        "title": "Java 8: Lambdas, Functional Interfaces & Method References",
        "blocks": [
            ("analogy", "Before Java 8, passing behaviour was like hiring a **full-time employee** (an anonymous "
                        "class with boilerplate) just to do one small job. A **lambda** is a **sticky note with "
                        "instructions**: \"sort these by price\". You hand over just the instructions, nothing else."),
            ("h", "From anonymous class to lambda to method reference"),
            ("code", """
// Before Java 8
Collections.sort(products, new Comparator<Product>() {
    @Override
    public int compare(Product a, Product b) { return a.price().compareTo(b.price()); }
});

// Lambda: (parameters) -> expression
products.sort((a, b) -> a.price().compareTo(b.price()));

// Method reference + Comparator combinators: reads like English
products.sort(Comparator.comparing(Product::price).thenComparing(Product::name).reversed());
"""),
            ("h", "Built-in functional interfaces (java.util.function)"),
            ("table", [["Interface", "Method", "Shape", "Example"],
                       ["`Function<T,R>`", "`apply`", "T → R", "`Order::total`"],
                       ["`Predicate<T>`", "`test`", "T → boolean", "`o -> o.total() > 1000`"],
                       ["`Supplier<T>`", "`get`", "() → T", "`UUID::randomUUID`"],
                       ["`Consumer<T>`", "`accept`", "T → void", "`log::info`"],
                       ["`BiFunction<T,U,R>`", "`apply`", "(T, U) → R", "`Money::add`"],
                       ["`UnaryOperator<T>` / `BinaryOperator<T>`", "`apply`", "T → T / (T, T) → T", "`String::trim` / `Integer::sum`"]],
             [0.32, 0.12, 0.22, 0.34]),
            ("p", "A **functional interface** has exactly one abstract method; any lambda with the matching "
                  "shape fits it. Annotate your own with `@FunctionalInterface` so the compiler enforces it."),
            ("code", """
@FunctionalInterface
public interface DiscountRule {
    Money apply(Order order);

    default DiscountRule andThen(DiscountRule next) {          // Java 8: default methods
        return order -> this.apply(order).add(next.apply(order));
    }
}

DiscountRule festive = order -> order.total().percent(10);
DiscountRule loyalty = order -> order.customer().isGold() ? Money.of(200) : Money.ZERO;
Money discount = festive.andThen(loyalty).apply(order);       // behaviour composed like data
"""),
            ("table", [["Method reference kind", "Syntax", "Equivalent lambda"],
                       ["Static method", "`Integer::parseInt`", "`s -> Integer.parseInt(s)`"],
                       ["Instance method of a particular object", "`log::info`", "`msg -> log.info(msg)`"],
                       ["Instance method of an arbitrary object", "`String::toUpperCase`", "`s -> s.toUpperCase()`"],
                       ["Constructor", "`ArrayList::new`", "`() -> new ArrayList<>()`"]],
             [0.38, 0.26, 0.36]),
            ("warn", "Trying to modify a local variable inside a lambda: `int count = 0; list.forEach(x -> count++);` "
                     "does not compile. Captured locals must be **effectively final**. Don't hack around it with "
                     "`int[] count = {0}`; use a stream terminal operation such as `.count()` or `.sum()`."),
            ("key", ["Lambda = an implementation of a single-method interface, written inline.",
                     "Know the six core functional interfaces by heart.",
                     "Prefer method references and `Comparator.comparing(...)` for readability."]),
        ],
        "questions": [
            "Mini-challenge: write a `Predicate<Order>` named `isLargeDomestic` that combines `isLarge` "
            "(total > 5000) and `isDomestic` (country is \"IN\") using `Predicate`'s default methods.",
        ],
        "answer": [
            ("code", """
Predicate<Order> isLarge    = o -> o.total().compareTo(new BigDecimal("5000")) > 0;
Predicate<Order> isDomestic = o -> "IN".equals(o.country());
Predicate<Order> isLargeDomestic = isLarge.and(isDomestic);   // also: .or(...), .negate()
"""),
        ],
    },
    # ------------------------------------------------------------------ Streams
    {
        "title": "Java 8: The Streams API",
        "blocks": [
            ("analogy", "A stream is a **factory conveyor belt**. Items flow past stations (filter, map, sort). "
                        "Nothing moves until someone at the end **presses start** (the terminal operation), and "
                        "each item travels the whole belt before the next one starts (lazy, one at a time)."),
            ("code", """
 source           intermediate ops (lazy, return a Stream)          terminal op (runs everything)
 ──────           ────────────────────────────────────────          ─────────────────────────────
 orders.stream() ─► filter(paid) ─► map(Order::total) ─► sorted() ─► collect / sum / count / forEach
"""),
            ("code", """
// Revenue per category for PAID orders, highest first
Map<String, BigDecimal> revenueByCategory = orders.stream()
    .filter(o -> o.status() == Status.PAID)
    .flatMap(o -> o.items().stream())                                  // Stream<Order> → Stream<Item>
    .collect(Collectors.groupingBy(
            Item::category,
            Collectors.reducing(BigDecimal.ZERO, Item::lineTotal, BigDecimal::add)));

// Top 3 customers by number of orders
List<String> top3 = orders.stream()
    .collect(Collectors.groupingBy(Order::customerId, Collectors.counting()))
    .entrySet().stream()
    .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
    .limit(3)
    .map(Map.Entry::getKey)
    .toList();                                                         // Java 16+, unmodifiable
"""),
            ("h", "Collectors you'll use every week"),
            ("table", [["Collector", "Result"],
                       ["`toList()`, `toSet()`", "Collections"],
                       ["`toMap(Order::id, Function.identity())`", "Map by key; **throws on duplicate keys** unless you pass a merge function"],
                       ["`groupingBy(f)` / `groupingBy(f, downstream)`", "`Map<K, List<V>>` or `Map<K, aggregated>`"],
                       ["`partitioningBy(predicate)`", "`Map<Boolean, List<V>>`: two buckets"],
                       ["`joining(\", \")`", "Concatenated String"],
                       ["`summingInt`, `averagingDouble`, `counting`", "Numbers"]],
             [0.48, 0.52]),
            ("h", "Primitive streams avoid boxing"),
            ("code", """
int totalQty = items.stream().mapToInt(Item::qty).sum();              // IntStream: no Integer boxing
IntSummaryStatistics stats = items.stream().mapToInt(Item::qty).summaryStatistics();
IntStream.rangeClosed(1, 5).forEach(System.out::println);
"""),
            ("ul", ["A stream can be consumed **only once**: reusing it throws `IllegalStateException`.",
                    "Keep lambdas **side-effect free**: don't `add` to an outside list in `forEach`; collect instead.",
                    "`parallelStream()` uses the shared common ForkJoinPool. It helps only for large, CPU-bound, "
                    "stateless work; **never** for blocking I/O inside a web request.",
                    "Java 24 adds **Stream Gatherers** (`stream.gather(...)`) for custom intermediate operations "
                    "like sliding windows."]),
            ("warn", "Using `Collectors.toMap` on data with duplicate keys, e.g. mapping customers by email "
                     "when two records share one. It throws `IllegalStateException: Duplicate key` in production. "
                     "Supply a merge function: `toMap(Customer::email, c -> c, (first, second) -> first)`."),
            ("key", ["Intermediate ops are lazy; nothing happens without a terminal op.",
                     "`groupingBy` + downstream collectors replace most hand-written loops with maps.",
                     "No side effects in lambdas; be very careful with `parallelStream()`."]),
        ],
        "questions": [
            "Mini-challenge: given `List<Employee>` (name, department, salary), produce `Map<String, Optional<Employee>>` "
            "of the highest-paid employee per department. Then change it to return just the names.",
        ],
        "answer": [
            ("code", """
Map<String, Optional<Employee>> top = employees.stream()
    .collect(groupingBy(Employee::department, maxBy(comparing(Employee::salary))));

Map<String, String> topNames = employees.stream()
    .collect(groupingBy(Employee::department,
             collectingAndThen(maxBy(comparing(Employee::salary)),
                               e -> e.map(Employee::name).orElse("-"))));
"""),
        ],
    },
    # ------------------------------------------------------------------ Optional & time
    {
        "title": "Java 8: Optional, java.time & Interface Default Methods",
        "blocks": [
            ("analogy", "`Optional` is a **gift box** that may be empty. Instead of handing someone a box and "
                        "letting them discover it's empty (`NullPointerException`), the label says \"might be "
                        "empty\", so they must decide what to do before opening it."),
            ("h", "Optional: use it as a return type"),
            ("code", """
public Optional<Customer> findByEmail(String email) { ... }      // ✔ "may not exist" is explicit

String city = customerRepo.findByEmail(email)
    .map(Customer::address)                    // Optional<Address>
    .map(Address::city)                        // Optional<String>
    .orElse("Unknown");

Customer c = customerRepo.findById(id)
    .orElseThrow(() -> new CustomerNotFoundException(id));     // → 404 via @ControllerAdvice

customerRepo.findByEmail(email).ifPresentOrElse(              // Java 9
    this::sendWelcomeBack, () -> log.info("new visitor"));
"""),
            ("table", [["Do", "Don't"],
                       ["Return `Optional<T>` from finders", "Use `Optional` as a field, method parameter or in collections"],
                       ["`map` / `flatMap` / `filter` / `orElseThrow`", "Call `optional.get()` without checking (it's just a disguised NPE)"],
                       ["`orElseGet(() -> expensive())`", "`orElse(expensive())`: the argument is **always** evaluated"],
                       ["Return an empty `List`, not `Optional<List>`", "Return `null` from a method declared to return `Optional`"]],
             [0.5, 0.5]),
            ("h", "java.time: the date/time API that finally works"),
            ("p", "The old `Date`/`Calendar`/`SimpleDateFormat` were mutable and not thread-safe. `java.time` "
                  "types are **immutable and thread-safe**."),
            ("table", [["Type", "Represents", "Use for"],
                       ["`Instant`", "A point on the UTC timeline", "**Timestamps**: createdAt, event times (store these)"],
                       ["`LocalDate`", "Date without time/zone", "Birthdays, delivery dates"],
                       ["`LocalDateTime`", "Date + time, **no zone**", "Rarely in backends: ambiguous across zones"],
                       ["`ZonedDateTime`", "Date + time + zone (`Asia/Kolkata`)", "Display to users, scheduling in a zone"],
                       ["`Duration` / `Period`", "Time-based / date-based amounts", "Timeouts, TTLs / \"30 days\" subscriptions"]],
             [0.22, 0.36, 0.42]),
            ("code", """
Instant createdAt = Instant.now();
ZonedDateTime local = createdAt.atZone(ZoneId.of("Asia/Kolkata"));
LocalDate deliveryBy = LocalDate.now(clock).plusDays(5);         // inject a Clock → testable!
boolean late = Duration.between(createdAt, Instant.now()).toHours() > 48;
String label = DateTimeFormatter.ofPattern("dd MMM yyyy").format(deliveryBy);   // thread-safe
"""),
            ("h", "Default & static methods in interfaces"),
            ("p", "Java 8 let interfaces ship method bodies (`default`), so libraries could evolve without "
                  "breaking implementers. That's how `List.sort`, `Map.computeIfAbsent` and `Iterable.forEach` "
                  "were added. Java 9 added `private` interface methods for sharing code between defaults."),
            ("warn", "Storing `LocalDateTime` for events in a system with users or servers in different "
                     "zones. \"2026-03-08 02:30\" means different moments in different places, and may not "
                     "exist at all during a DST change. Store **`Instant`** (Postgres `timestamptz`), and convert "
                     "to a zone only for display."),
            ("key", ["`Optional` = explicit \"may be absent\" return type; never call bare `get()`.",
                     "`orElseGet` for expensive defaults; `orElse` evaluates eagerly.",
                     "Store `Instant` in UTC; inject a `Clock` so time-based code is testable."]),
        ],
        "questions": [
            "What's printed? `Optional.of(\"cached\").orElse(loadFromDb())`, where `loadFromDb()` prints "
            "\"DB HIT\" and returns a value. How would you fix it?",
        ],
        "answer": "\"DB HIT\" **is printed**: `orElse`'s argument is evaluated before the call, even though the "
                  "Optional has a value. Fix: `orElseGet(() -> loadFromDb())` (or `orElseGet(this::loadFromDb)`), "
                  "which calls the supplier only when the Optional is empty.",
    },
    # ------------------------------------------------------------------ 9-17
    {
        "title": "Java 9 → 17: var, Records, Text Blocks, Switch Expressions, Sealed Classes",
        "blocks": [
            ("analogy", "Java 8 → 17 is like a car going from **manual to automatic**: same engine (JVM), "
                        "but far less ceremony to drive. Records alone remove the hundreds of lines of "
                        "getters, `equals`, `hashCode` and `toString` you used to write for every DTO."),
            ("h", "Feature map"),
            ("table", [["Version", "Feature", "One-line summary"],
                       ["9", "`List.of`, `Set.of`, `Map.of`", "Compact **immutable** collections (no nulls allowed)"],
                       ["9", "JPMS modules, JShell", "`module-info.java`; a REPL for quick experiments"],
                       ["10", "`var`", "Local variable type inference"],
                       ["11 (LTS)", "`HttpClient`, `String.isBlank/strip/lines/repeat`, `Files.readString`", "Standard HTTP/2 client; handy String & file helpers"],
                       ["14", "Switch expressions", "`switch` returns a value, arrow labels, no fall-through"],
                       ["14", "Helpful NullPointerExceptions", "Message names exactly which reference was null"],
                       ["15", "Text blocks", "Multi-line strings with `\"\"\"`"],
                       ["16", "Records, pattern matching for `instanceof`, `Stream.toList()`", "Data carriers; no more cast after instanceof"],
                       ["17 (LTS)", "Sealed classes", "Restrict which classes may extend a type"]],
             [0.13, 0.42, 0.45]),
            ("h", "Records: immutable data carriers"),
            ("code", """
public record OrderDto(String id, String customerId, BigDecimal total, List<ItemDto> items) {
    public OrderDto {                                   // compact constructor: validation
        Objects.requireNonNull(id);
        if (total.signum() < 0) throw new IllegalArgumentException("negative total");
        items = List.copyOf(items);                     // defensive copy → truly immutable
    }
    public boolean isLarge() { return total.compareTo(BigDecimal.valueOf(5000)) > 0; }
}
// Generated: constructor, accessors id()/total()..., equals, hashCode, toString
"""),
            ("h", "var, text blocks and switch expressions"),
            ("code", """
var orders = new HashMap<String, List<Order>>();      // type obvious from the right side ✔
var result = service.process();                       // ✘ type hidden: avoid

String sql = \"\"\"
        SELECT o.id, o.total
        FROM orders o
        WHERE o.customer_id = ? AND o.status = 'PAID'
        \"\"\";

int deliveryDays = switch (shippingType) {            // expression: returns a value
    case EXPRESS          -> 1;
    case STANDARD, ECO    -> 5;
    case INTERNATIONAL    -> {
        log.info("customs check");
        yield 14;                                     // yield from a block
    }
};                                                    // enum fully covered → no default needed
"""),
            ("h", "Sealed classes + pattern matching instanceof"),
            ("code", """
public sealed interface PaymentMethod permits Card, Upi, Wallet {}
public record Card(String last4, String network) implements PaymentMethod {}
public record Upi(String vpa)                    implements PaymentMethod {}
public record Wallet(String provider)            implements PaymentMethod {}

if (method instanceof Card card && card.network().equals("AMEX")) {   // Java 16: bind + use
    applyAmexFee(card);
}
"""),
            ("warn", "Treating `List.of(...)` results as mutable: `List.of(1, 2).add(3)` throws "
                     "`UnsupportedOperationException`, and `List.of(null)` / `Map.of(\"k\", null)` throw NPE. Same "
                     "for `Stream.toList()` (unmodifiable), unlike `collect(Collectors.toList())`."),
            ("key", ["Records for DTOs, events, value objects and map keys: immutable and correct by default.",
                     "Switch expressions + sealed types = the compiler checks you've handled every case.",
                     "`var` for obvious types only; readability beats brevity."]),
        ],
        "questions": [
            "Mini-challenge: convert this class into a record that also rejects a blank `sku`: "
            "`class Item { private final String sku; private final int qty; /* ctor, getters, equals, hashCode, toString */ }`",
        ],
        "answer": [
            ("code", """
public record Item(String sku, int qty) {
    public Item {
        if (sku == null || sku.isBlank()) throw new IllegalArgumentException("sku required");
        if (qty <= 0) throw new IllegalArgumentException("qty must be positive");
    }
}
"""),
        ],
    },
    # ------------------------------------------------------------------ 21-25
    {
        "title": "Java 21 → 25: Pattern Matching for switch, Record Patterns & What's New",
        "blocks": [
            ("analogy", "Pattern matching is a **mail-sorting machine**: it looks at each parcel's shape "
                        "(type), opens it to read the label inside (deconstruction), and routes it, and the "
                        "machine refuses to start if there's a parcel shape it has no chute for."),
            ("h", "Java 21 (LTS): pattern matching for switch + record patterns"),
            ("code", """
// Works with the sealed PaymentMethod hierarchy from the previous topic
public BigDecimal fee(PaymentMethod method, BigDecimal amount) {
    return switch (method) {
        case Card(var last4, var network) when network.equals("AMEX")
                                    -> amount.multiply(new BigDecimal("0.035"));
        case Card c                 -> amount.multiply(new BigDecimal("0.02"));
        case Upi u                  -> BigDecimal.ZERO;
        case Wallet(var provider)   -> provider.equals("PAYTM") ? new BigDecimal("2") : BigDecimal.ONE;
    };   // no default: the compiler knows the sealed type is fully covered
}
// Add a new PaymentMethod (e.g. NetBanking) → this switch stops compiling until you handle it ✔
"""),
            ("h", "Java 21: sequenced collections"),
            ("code", """
List<Order> recent = ...;
Order newest = recent.getLast();                 // was: recent.get(recent.size() - 1)
Order oldest = recent.getFirst();
List<Order> newestFirst = recent.reversed();     // a view, no copy
LinkedHashMap<String, Order> byId = ...;  byId.firstEntry();  byId.pollLastEntry();
"""),
            ("h", "Java 22 → 25 highlights (Java 25 is the current LTS)"),
            ("table", [["Version", "Feature (final)", "Why you care"],
                       ["21", "Virtual threads (covered in its own topic)", "Massive I/O concurrency with simple code"],
                       ["22", "Unnamed variables `_`", "`catch (NumberFormatException _)`, `case Card(_, var net)`"],
                       ["24", "Stream Gatherers", "Custom intermediate ops: windows, scans"],
                       ["24", "Synchronized without pinning virtual threads (JEP 491)", "`synchronized` is safe with virtual threads again"],
                       ["25 (LTS)", "Scoped Values", "Safer, cheaper alternative to `ThreadLocal` for virtual threads"],
                       ["25", "Flexible constructor bodies", "Validate arguments *before* calling `super(...)`"],
                       ["25", "Compact source files & instance `main`", "`void main() { IO.println(\"Hi\"); }` for scripts & learning"],
                       ["25", "Module import declarations", "`import module java.base;`"]],
             [0.13, 0.42, 0.45]),
            ("p", "**Which version should you use?** New services: **Java 21 or 25 (LTS)**. Spring Boot 3.x "
                  "requires Java 17+, and LTS releases get years of updates. Avoid running production on "
                  "non-LTS versions unless you upgrade every six months."),
            ("warn", "Adding a `default ->` branch to a switch over a **sealed** type \"just in case\". It "
                     "silences the compiler, so when someone adds a new subtype it silently falls into "
                     "`default` instead of failing the build. Leave it exhaustive without `default`."),
            ("key", ["Sealed types + records + pattern-matching switch = type-safe domain modelling.",
                     "`getFirst()` / `getLast()` / `reversed()` on lists, deques and linked maps (Java 21).",
                     "Target an LTS (17, 21, 25); prefer Java 21+ for virtual threads."]),
        ],
        "questions": [
            "Mini-challenge: model a `sealed interface Shipment` with records `Domestic(String pincode)` and "
            "`International(String country, double weightKg)`. Write a pattern-matching `switch` returning "
            "the shipping cost: domestic ₹50; international ₹500 + ₹200/kg, but ₹0 extra per kg to \"NP\" or \"BT\".",
        ],
        "answer": [
            ("code", """
sealed interface Shipment permits Domestic, International {}
record Domestic(String pincode) implements Shipment {}
record International(String country, double weightKg) implements Shipment {}

static double cost(Shipment s) {
    return switch (s) {
        case Domestic _                                   -> 50;
        case International(var c, var kg) when Set.of("NP", "BT").contains(c) -> 500;
        case International(var c, var kg)                 -> 500 + 200 * kg;
    };
}
"""),
            "(`Domestic _` needs Java 22+; on Java 21 write `case Domestic d`.)",
        ],
    },
]
