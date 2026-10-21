MODULE = {
    "title": "SQL & Relational Databases",
    "intro": "PostgreSQL is the backbone of most transactional systems: orders, payments, inventory. Three "
             "ideas decide whether it is fast and correct under load: **indexes**, **ACID transactions** and "
             "**isolation levels**.",
    "topics": [
        # ------------------------------------------------------------------ 2.1
        {
            "title": "Indexes: B-Trees, Composite Indexes & EXPLAIN",
            "blocks": [
                ("analogy", "An index is the **index at the back of a textbook**. Without it you flip through every "
                            "page to find \"Garbage Collection\" (a **sequential scan**). With it you jump to the "
                            "right page directly. But every time the book is edited, the index must be updated "
                            "too, so indexes speed up reads and slow down writes."),
                ("h", "B-tree: the default index"),
                ("code", """
                        [ 40 | 80 ]                      ← root
               ┌───────────┼───────────┐
          [10|25]       [50|65]       [90|120]            ← internal nodes
          ┌──┼──┐       ┌──┼──┐       ┌──┼──┐
        leaf leaf leaf leaf leaf ... leaf leaf leaf      ← sorted keys + pointers to rows
          ◄──────────── leaves linked: fast range scans ────────────►

 Finding 1 row among 10 million ≈ 3–4 page reads instead of ~100,000.
"""),
                ("h", "Creating the right index"),
                ("code", """
-- Query the app runs constantly:
SELECT * FROM orders
WHERE customer_id = 42 AND status = 'PAID'
ORDER BY created_at DESC LIMIT 20;

-- Composite index matching filter columns first, then the sort column
CREATE INDEX idx_orders_customer_status_created
    ON orders (customer_id, status, created_at DESC);

-- Verify with the real execution plan
EXPLAIN ANALYZE SELECT ...;
--  Index Scan using idx_orders_customer_status_created on orders
--  (actual time=0.031..0.090 rows=20)        ✔  was: Seq Scan ... (actual time=812 ms)
"""),
                ("h", "The leftmost-prefix rule"),
                ("p", "A composite index on `(a, b, c)` is sorted by `a`, then `b`, then `c`, like a phone book "
                      "sorted by last name, then first name. It can serve queries that use the **leftmost columns**:"),
                ("table", [["Query filters on", "Uses index (a, b, c)?"],
                           ["`a`", "Yes"], ["`a, b`", "Yes"], ["`a, b, c`", "Yes"],
                           ["`b` or `c` only", "No: like searching a phone book by first name"],
                           ["`a, c`", "Partially (only `a` narrows the search)"]],
                 [0.4, 0.6]),
                ("h", "Things that silently kill an index"),
                ("ul", ["Wrapping the column in a function: `WHERE LOWER(email) = ?`. Fix: an expression index "
                        "`CREATE INDEX ON users (LOWER(email))`.",
                        "Leading wildcard: `LIKE '%son'` can't use a B-tree (`LIKE 'son%'` can).",
                        "Type mismatch: comparing a `varchar` column to a number forces a cast.",
                        "Low selectivity: an index on `is_active` (two values) is rarely used; the planner prefers a scan."]),
                ("warn", "**Missing index on foreign keys.** PostgreSQL does *not* auto-index FK columns. "
                         "`orders.customer_id` without an index makes every join and every `DELETE` of a customer "
                         "scan the whole orders table. Rule of thumb: index every FK you join or filter on."),
                ("key", ["Index the columns in your `WHERE`, `JOIN` and `ORDER BY`, and order composite columns deliberately.",
                         "Always confirm with `EXPLAIN ANALYZE`; never guess.",
                         "Each index costs write speed and disk. Drop unused ones (`pg_stat_user_indexes`)."]),
            ],
            "questions": [
                "You have an index on `(status, customer_id)`. A query filters only by `customer_id`. Will the "
                "index be used efficiently? How would you fix it?",
            ],
            "answer": "No. `customer_id` is not the leftmost column, so the index can't seek on it (at best a "
                      "full index scan). Either add an index on `(customer_id)` or reorder to "
                      "`(customer_id, status)` if that also serves your other queries. `customer_id` is usually "
                      "the more selective column anyway.",
        },
        # ------------------------------------------------------------------ 2.2
        {
            "title": "ACID Transactions",
            "blocks": [
                ("analogy", "A **bank transfer** of ₹500 from Asha to Ravi. Taking money from Asha and adding it "
                            "to Ravi must happen **together or not at all**. If the power fails in between, "
                            "money must not vanish. That all-or-nothing guarantee is a transaction."),
                ("table", [["Letter", "Guarantee", "How Postgres achieves it"],
                           ["**A**tomicity", "All statements succeed or all are rolled back",
                            "Undo on `ROLLBACK` or crash"],
                           ["**C**onsistency", "Data always satisfies constraints",
                            "`PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, `NOT NULL`"],
                           ["**I**solation", "Concurrent transactions don't see each other's half-done work",
                            "MVCC snapshots + locks (next topic)"],
                           ["**D**urability", "Once committed, it survives a crash",
                            "Write-Ahead Log (WAL) flushed to disk on commit"]],
                 [0.17, 0.43, 0.40]),
                ("code", """
BEGIN;
  UPDATE accounts SET balance = balance - 500 WHERE id = 'asha';
  UPDATE accounts SET balance = balance + 500 WHERE id = 'ravi';
  -- CHECK (balance >= 0) constraint fails?  → whole transaction rolls back
COMMIT;
"""),
                ("h", "In Spring Boot"),
                ("code", """
@Service
@RequiredArgsConstructor
public class TransferService {
    private final AccountRepository accounts;

    @Transactional                                   // BEGIN ... COMMIT / ROLLBACK
    public void transfer(String from, String to, BigDecimal amount) {
        Account source = accounts.findById(from).orElseThrow();
        Account target = accounts.findById(to).orElseThrow();
        source.withdraw(amount);                     // throws InsufficientFundsException
        target.deposit(amount);
    }   // dirty-checking flushes both UPDATEs here; any RuntimeException → rollback
}
"""),
                ("h", "Keep transactions short"),
                ("p", "A transaction holds a database connection and row locks until it ends. Long ones block "
                      "other users and drain the connection pool."),
                ("warn", "Calling a slow **external API inside `@Transactional`**. The DB connection sits idle "
                         "for seconds while waiting on HTTP. Under load the Hikari pool (default 10 connections) "
                         "runs dry: `Connection is not available, request timed out after 30000ms`. Do remote calls "
                         "*before* or *after* the transaction, not inside."),
                ("key", ["Atomicity = all-or-nothing; Durability = WAL; Consistency = constraints.",
                         "Put business invariants in DB constraints too, not only in Java.",
                         "Short transactions; no network calls inside them."]),
            ],
            "questions": [
                "Your `placeOrder()` is `@Transactional` and calls the payment gateway (2 s) in the middle. "
                "Why is that dangerous, and how would you restructure it?",
            ],
            "answer": [
                "The DB connection and row locks are held for the full 2 s. Under load this exhausts the "
                "connection pool, and if the transaction rolls back *after* the payment succeeded, money was "
                "charged with no order. Restructure:",
                "1) Short transaction: save order as `PENDING_PAYMENT`. 2) Call the gateway outside any "
                "transaction (with idempotency key + timeout). 3) Short transaction: mark `PAID` or `FAILED`. "
                "For cross-service flows, this becomes a **Saga** (Module 6).",
            ],
        },
        # ------------------------------------------------------------------ 2.3
        {
            "title": "Isolation Levels & Concurrency Anomalies",
            "blocks": [
                ("analogy", "Several people editing a **shared Google Sheet**. Do you see others' typing as "
                            "it happens (dirty), only after they press save (read committed), or a frozen copy "
                            "from when you opened it (snapshot)? Isolation levels pick which view you get, "
                            "trading safety against speed."),
                ("h", "The anomalies"),
                ("table", [["Anomaly", "What happens"],
                           ["**Dirty read**", "You read another transaction's uncommitted change, which is later rolled back"],
                           ["**Non-repeatable read**", "You read a row twice and get different values (someone committed in between)"],
                           ["**Phantom read**", "You run the same `WHERE` query twice and new rows appear"],
                           ["**Lost update**", "Two transactions read-modify-write the same row; one overwrite is lost"],
                           ["**Write skew**", "Two transactions each check a condition, then write different rows, breaking a rule together"]],
                 [0.25, 0.75]),
                ("h", "The levels (PostgreSQL behaviour)"),
                ("table", [["Level", "Dirty", "Non-repeatable", "Phantom", "Notes"],
                           ["Read Uncommitted", "No*", "Possible", "Possible", "*Postgres treats it as Read Committed"],
                           ["**Read Committed** (default)", "No", "Possible", "Possible", "Each *statement* sees a fresh snapshot"],
                           ["Repeatable Read", "No", "No", "No*", "One snapshot per *transaction*; *Postgres prevents phantoms too"],
                           ["Serializable", "No", "No", "No", "Also prevents write skew; may abort with a serialization error"]],
                 [0.24, 0.1, 0.16, 0.12, 0.38]),
                ("h", "Fixing the lost update"),
                ("code", """
 T1: SELECT stock → 5            T2: SELECT stock → 5
 T1: UPDATE stock = 5 - 1 = 4    T2: UPDATE stock = 5 - 1 = 4      ⇒ 2 items sold, stock shows 4 ✘
"""),
                ("code", """
-- Option A: atomic update, the database does the math
UPDATE products SET stock = stock - 1 WHERE id = :id AND stock > 0;   -- check rows affected

-- Option B: pessimistic lock, others wait for the row
SELECT * FROM products WHERE id = :id FOR UPDATE;
"""),
                ("code", """
// Option C: optimistic locking in JPA, best for low-contention updates
@Entity
public class Product {
    @Id private Long id;
    private int stock;
    @Version private long version;    // UPDATE ... SET version = v+1 WHERE id = ? AND version = v
}
// a concurrent change → 0 rows updated → ObjectOptimisticLockingFailureException → retry
"""),
                ("warn", "Raising everything to `SERIALIZABLE` \"to be safe\" without handling failures. "
                         "Postgres then aborts conflicting transactions with `could not serialize access`, and "
                         "your app must **retry** them. Higher isolation = more aborts or waiting, so use it "
                         "only where the invariant needs it."),
                ("key", ["Postgres default is Read Committed: no dirty reads, but lost updates are possible.",
                         "Fix lost updates with atomic SQL, `SELECT ... FOR UPDATE`, or `@Version`.",
                         "Serializable is the strongest; be ready to retry."]),
            ],
            "questions": [
                "Flash sale: 1,000 users buy the last 10 units at the same moment. Which locking strategy would "
                "you choose and why: optimistic `@Version` or an atomic `UPDATE ... WHERE stock > 0`?",
            ],
            "answer": "The **atomic conditional UPDATE**. With very high contention on one row, optimistic locking "
                      "makes almost every transaction fail and retry (a retry storm). "
                      "`UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0` is a single "
                      "statement: the row lock serialises the buyers briefly, exactly 10 succeed (1 row "
                      "updated) and the rest see 0 rows and get \"sold out\". Optimistic locking shines when "
                      "conflicts are *rare*.",
        },
    ],
}
