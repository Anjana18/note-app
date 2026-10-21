MODULE = {
    "title": "MongoDB & Document Storage",
    "intro": "Some data doesn't fit neatly in rows: product catalogues where a phone and a T-shirt have totally "
             "different attributes, or content that is always read as one whole. MongoDB stores **documents**, "
             "and the most important skill is modelling them around how you *read* the data.",
    "topics": [
        # ------------------------------------------------------------------ 3.1
        {
            "title": "The Document Model & When to Use MongoDB",
            "blocks": [
                ("analogy", "SQL is a **filing cabinet with fixed forms**: every customer form has the same boxes, "
                            "and related info lives in other drawers (tables) linked by ID. MongoDB is a "
                            "**folder per item**: everything about one product (its specs, images, variants) "
                            "sits in one folder, and each folder can hold different papers."),
                ("code", """
// One product document (BSON, stored in the "products" collection)
{
  "_id": ObjectId("665f..."),
  "sku": "PHN-IP15-128",
  "name": "iPhone 15",
  "category": "phones",
  "price": { "amount": 79900, "currency": "INR" },
  "attributes": { "storage": "128GB", "color": "Black", "screen": "6.1in" },
  "images": ["https://cdn/.../1.jpg", "https://cdn/.../2.jpg"],
  "variants": [ { "sku": "PHN-IP15-256", "storage": "256GB", "price": 89900 } ]
}
// A T-shirt document in the same collection can have { "size": "M", "fabric": "cotton" } instead
"""),
                ("h", "Spring Data MongoDB"),
                ("code", """
@Document(collection = "products")
public record Product(
        @Id String id,
        @Indexed(unique = true) String sku,
        String name,
        String category,
        Money price,
        Map<String, Object> attributes,          // flexible, per-category attributes
        List<String> images,
        List<Variant> variants) {}

public interface ProductRepository extends MongoRepository<Product, String> {
    List<Product> findByCategoryAndPriceAmountLessThan(String category, long maxPrice);
}
"""),
                ("table", [["Choose PostgreSQL when…", "Choose MongoDB when…"],
                           ["Strong relations & joins (orders ↔ payments ↔ customers)",
                            "Data is naturally hierarchical and read as a whole (catalogue, CMS, user profile)"],
                           ["Multi-row ACID transactions are central (money, inventory)",
                            "Schema varies per record or evolves fast"],
                           ["Complex ad-hoc reporting with SQL", "Very high write volume, horizontal sharding needed"]],
                 [0.5, 0.5]),
                ("p", "MongoDB *does* support multi-document ACID transactions (since 4.0), but if you need them "
                      "everywhere, that's a signal the data is relational."),
                ("warn", "**Treating MongoDB like SQL**: one collection per \"table\" and `$lookup` joins "
                         "everywhere. You get the downsides of both. Design documents around your **query "
                         "patterns**, not around normalisation."),
                ("key", ["Document = self-contained JSON-like record; collections can hold varied shapes.",
                         "Model for reads: data accessed together should be stored together.",
                         "Polyglot persistence: Postgres for orders, MongoDB for the catalogue is a common pairing."]),
            ],
            "questions": [
                "For an e-commerce app, which store would you choose for (a) the product catalogue, (b) orders "
                "and payments, (c) user shopping-cart sessions? Justify each in one line.",
            ],
            "answer": [
                "(a) **MongoDB**: varied attributes per category, read as whole documents, schema evolves.",
                "(b) **PostgreSQL**: money needs strict ACID, constraints and relational reporting.",
                "(c) **Redis**: short-lived, high-frequency key-value access with TTL (Module 4).",
            ],
        },
        # ------------------------------------------------------------------ 3.2
        {
            "title": "Embedding vs. Referencing",
            "blocks": [
                ("analogy", "**Embedding** is stapling the receipt *to* the order form: one grab gets everything. "
                            "**Referencing** is writing \"see customer file #42\" on the form: less "
                            "duplication, but you need a second trip to the cabinet."),
                ("code", """
 EMBEDDED (one read)                        REFERENCED (two reads / $lookup)
 ┌───────────────────────────┐              ┌──────────────────┐     ┌────────────────┐
 │ order                     │              │ order            │     │ customer       │
 │  _id: 1001                │              │  _id: 1001       │     │  _id: 42       │
 │  items: [ {sku, qty, ₹} ] │              │  customerId: 42 ─┼────►│  name, email   │
 │  shippingAddress: {...}   │              │  items: [...]    │     │  addresses     │
 └───────────────────────────┘              └──────────────────┘     └────────────────┘
"""),
                ("h", "Decision rules"),
                ("table", [["Embed when…", "Reference when…"],
                           ["Child belongs to one parent (**contains** relationship)", "Child is **shared** by many parents"],
                           ["Data is read together almost always", "Child is read/updated independently"],
                           ["Array is **bounded** (an order has ~1–50 items)", "Array is **unbounded** (a product's reviews, logs)"],
                           ["A snapshot is wanted (address at time of order)", "Data must always be current (live stock)"]],
                 [0.5, 0.5]),
                ("h", "Useful patterns"),
                ("ul", ["**Extended reference:** store the ID *plus* the few fields you display, e.g. "
                        "`customer: { id: 42, name: \"Asha\" }`. One read for the common screen; full doc when needed.",
                        "**Subset:** embed only the 10 most recent reviews in the product; keep all reviews in a "
                        "separate `reviews` collection.",
                        "**Bucket:** group time-series events into one document per hour/day instead of one per event."]),
                ("code", """
@Document("products")
public record Product(@Id String id, String name,
                      List<Review> recentReviews,      // SUBSET: capped at 10, embedded
                      int reviewCount, double avgRating) {}

@Document("reviews")
public record Review(@Id String id, @Indexed String productId,   // REFERENCE back to product
                     String userId, int rating, String text, Instant createdAt) {}
"""),
                ("warn", "**Unbounded arrays.** Pushing every review or every event into one document. "
                         "Documents have a **16 MB hard limit**, and long before that every update rewrites a "
                         "huge document and memory usage grows. If an array can grow without limit, reference it."),
                ("key", ["Embed for *contains* + read-together + bounded.",
                         "Reference for shared, independent or unbounded data.",
                         "Duplicating a little data (extended reference) is fine if it saves joins on hot paths."]),
            ],
            "questions": [
                "A blog post has comments. Some viral posts get 200,000 comments. The post page shows the "
                "latest 20. Design the documents.",
            ],
            "answer": "`posts` document embeds `latestComments` (capped at 20, maintained with "
                      "`$push` + `$slice: -20`) plus `commentCount`. All comments live in a separate `comments` "
                      "collection referencing `postId`, with an index on `{postId: 1, createdAt: -1}` for "
                      "pagination. One read renders the page; no 16 MB risk.",
        },
        # ------------------------------------------------------------------ 3.3
        {
            "title": "MongoDB Indexes & Aggregation Pipeline",
            "blocks": [
                ("analogy", "The aggregation pipeline is a **factory assembly line**: documents enter, each "
                            "station (stage) filters, reshapes, groups or sorts them, and a finished report comes "
                            "out the end."),
                ("h", "Compound indexes: the ESR rule"),
                ("p", "Order fields in a compound index as **E**quality → **S**ort → **R**ange."),
                ("code", """
// Query: category = "phones" AND price BETWEEN 10k AND 50k, sorted by rating desc
db.products.createIndex({ category: 1, rating: -1, "price.amount": 1 })
//                         Equality     Sort         Range

db.products.find({ category: "phones", "price.amount": { $gte: 10000, $lte: 50000 } })
           .sort({ rating: -1 }).explain("executionStats")
// look for: stage IXSCAN (good) vs COLLSCAN (bad); totalDocsExamined ≈ nReturned
"""),
                ("h", "Aggregation: top categories by revenue"),
                ("code", """
db.orders.aggregate([
  { $match:  { status: "DELIVERED", createdAt: { $gte: ISODate("2026-01-01") } } },  // filter early
  { $unwind: "$items" },
  { $group:  { _id: "$items.category",
               revenue: { $sum: { $multiply: ["$items.price", "$items.qty"] } },
               orders:  { $addToSet: "$_id" } } },
  { $project: { revenue: 1, orderCount: { $size: "$orders" } } },
  { $sort:  { revenue: -1 } },
  { $limit: 5 }
])
"""),
                ("code", """
// Same thing with Spring Data
Aggregation agg = Aggregation.newAggregation(
    match(Criteria.where("status").is("DELIVERED")),
    unwind("items"),
    group("items.category").sum(ArithmeticOperators.Multiply
            .valueOf("items.price").multiplyBy("items.qty")).as("revenue"),
    sort(Sort.Direction.DESC, "revenue"),
    limit(5));
List<CategoryRevenue> top = mongoTemplate.aggregate(agg, "orders", CategoryRevenue.class)
                                         .getMappedResults();
"""),
                ("warn", "Putting `$match` **after** `$group` or `$unwind`. Indexes can only help stages at the "
                         "start of the pipeline. Filter first so fewer documents flow down the line."),
                ("key", ["Compound index order: Equality, Sort, Range.",
                         "Use `explain(\"executionStats\")`: IXSCAN good, COLLSCAN bad.",
                         "`$match` and `$project` as early as possible in pipelines."]),
            ],
            "questions": [
                "Query: `{ userId: X, status: \"ACTIVE\" }` sorted by `createdAt` desc, with `createdAt > lastWeek`. "
                "Write the ideal compound index.",
            ],
            "answer": "`{ userId: 1, status: 1, createdAt: -1 }`. `userId` and `status` are equality fields; "
                      "`createdAt` serves both the sort and the range, so it goes last.",
        },
    ],
}
