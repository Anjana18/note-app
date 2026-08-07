# Thulya — MongoDB Database Schema

Database: `thulya` · Engine: MongoDB 6+. IDs are `ObjectId` unless noted.
Money is stored in **paise** (integer) to avoid float rounding; API layer converts to ₹.
Timestamps are ISO‑8601 UTC (`createdAt`, `updatedAt`) on every collection.

---

## Collection map

| Collection | Purpose | Key relationships |
|---|---|---|
| `users` | Customers, admins, tailors (role‑based) | → orders, measurements, appointments |
| `products` | Catalogue items | → categories, reviews |
| `categories` | Product taxonomy (tree) | self‑referential (`parentId`) |
| `tailoringServices` | Editable stitching price list | — |
| `orders` | Purchases + tailoring jobs | → users, products, tailoringServices |
| `measurements` | Saved body measurements | → users |
| `appointments` | Measurement bookings | → users, slots |
| `calendarConfig` | Working hours, holidays, slot caps | — |
| `carts` | Live cart / saved-for-later | → users, products |
| `wishlists` | Saved designs | → users, products |
| `reviews` | Ratings + photos | → products, users |
| `coupons` | Discounts, festival offers | — |
| `payments` | Razorpay transactions, invoices | → orders |
| `inventory` | Fabric, threads, laces, accessories | → products |
| `loyalty` | Points, tier, referrals | → users |
| `notifications` | Push / WhatsApp / SMS / email log | → users |
| `campaigns` | WhatsApp / marketing blasts | → users (segments) |

---

## `users`
```jsonc
{
  "_id": ObjectId,
  "role": "customer",              // "customer" | "admin" | "tailor"
  "name": "Divya Ramesh",
  "phone": "+919000000001",        // unique, Firebase-verified
  "email": "divya@example.com",    // optional, from Google Sign-In
  "firebaseUid": "abc123",         // unique
  "avatarUrl": "gs://.../a.jpg",
  "addresses": [
    { "_id": ObjectId, "label": "Home", "line1": "...", "city": "Chennai",
      "state": "TN", "pincode": "600001", "isDefault": true, "geo": { "lat": 13.08, "lng": 80.27 } }
  ],
  "loyaltyTier": "gold",           // silver | gold | platinum
  "loyaltyPoints": 1240,
  "specialPricing": { "enabled": false, "discountPct": 0 },  // admin per-customer pricing
  "tailorProfile": {               // only when role === "tailor"
    "rating": 4.9, "jobsCompleted": 320, "skills": ["aari","zardozi","bridal"]
  },
  "fcmTokens": ["..."],            // for push
  "createdAt": ISODate, "updatedAt": ISODate
}
```
Indexes: `{ phone: 1 } unique`, `{ firebaseUid: 1 } unique`, `{ role: 1 }`, `{ email: 1 } sparse unique`.

## `categories`
```jsonc
{ "_id": ObjectId, "name": "Sarees", "slug": "sarees", "parentId": null,
  "icon": "🥻", "order": 1, "isActive": true }
// Sub-categories reference parent: { name:"Kanjivaram", parentId: <Sarees._id> }
```
Indexes: `{ slug: 1 } unique`, `{ parentId: 1 }`.

## `products`
```jsonc
{
  "_id": ObjectId,
  "sku": "THU-KJV-001",            // unique, human-readable
  "name": "Kanjivaram Royal Silk",
  "slug": "kanjivaram-royal-silk",
  "categoryId": ObjectId,          // → categories (leaf)
  "categoryPath": ["Sarees","Kanjivaram"],  // denormalised for fast filter
  "description": "Handwoven Kanjivaram…",
  "media": {
    "images": ["gs://.../1.jpg","gs://.../2.jpg"],
    "video": "gs://.../reel.mp4",
    "zoomImages": ["gs://.../1-hd.jpg"]
  },
  "fabric": "Pure Mulberry Silk",
  "washCare": "Dry clean only",
  "sizes": [ { "label": "5.5m", "stock": 12 } ],   // per-size stock
  "priceMrp": 1299900,             // paise
  "priceOffer": 849900,            // paise
  "gstPct": 5,
  "expectedDeliveryDays": [3,5],
  "stock": 12,                     // aggregate
  "tags": ["new","trending","festival"],
  "rating": { "avg": 4.9, "count": 214 },
  "relatedProductIds": [ObjectId],
  "isActive": true,
  "createdAt": ISODate, "updatedAt": ISODate
}
```
Indexes: `{ sku:1 } unique`, `{ slug:1 } unique`, `{ categoryId:1 }`, `{ tags:1 }`,
`{ name:"text", description:"text", fabric:"text" }` (search), `{ "rating.avg":-1 }`.

## `tailoringServices` (Admin-editable pricing)
```jsonc
{ "_id": ObjectId, "group": "Blouse Stitching", "icon":"👚",
  "items": [
    { "code":"blouse_normal", "name":"Normal Blouse", "price": 35000, "fromPrice": false },
    { "code":"blouse_dart",   "name":"Dart Blouse",   "price": 65000 },
    { "code":"blouse_designer","name":"Designer Blouse","price": 75000, "fromPrice": true }
  ],
  "isActive": true, "updatedBy": ObjectId, "updatedAt": ISODate }
```

## `orders`
```jsonc
{
  "_id": ObjectId,
  "orderNo": "THU-2048",           // unique
  "userId": ObjectId,
  "type": "tailoring",             // "product" | "tailoring" | "mixed"
  "items": [
    { "productId": ObjectId, "sku":"THU-ABL-032", "name":"Peacock Aari Blouse",
      "size":"M", "qty":1, "unitPrice":275000,
      "tailoring": { "serviceCode":"blouse_designer", "measurementId": ObjectId, "notes":"..." } }
  ],
  "pricing": { "subtotal":275000, "discount":27500, "gst":13750, "shipping":0, "total":261250,
               "couponCode":"THULYA10" },
  "payment": { "status":"advance_paid", "advance":100000, "balance":161250, "paymentIds":[ObjectId] },
  "fulfilment": {
    "stage": "stitching",          // ordered enum below
    "assignedTailorId": ObjectId,
    "history": [
      { "stage":"order_received", "at":ISODate, "by":ObjectId },
      { "stage":"measurement_completed", "at":ISODate },
      { "stage":"cutting", "at":ISODate },
      { "stage":"stitching", "at":ISODate, "photos":["gs://..."] }
    ],
    "expectedReadyAt": ISODate
  },
  "shippingAddressId": ObjectId,
  "createdAt": ISODate, "updatedAt": ISODate
}
```
Stage enum: `order_received → measurement_completed → cutting → stitching → embroidery → quality_check → ready → dispatched → delivered`.
Indexes: `{ orderNo:1 } unique`, `{ userId:1, createdAt:-1 }`, `{ "fulfilment.stage":1 }`, `{ "fulfilment.assignedTailorId":1 }`.

## `measurements`
```jsonc
{ "_id":ObjectId, "userId":ObjectId, "dressType":"blouse",
  "values": { "bust":36, "waist":30, "shoulder":14, "sleeveLength":8, "unit":"in" },
  "takenBy":"doorstep", "takenAt":ISODate, "isActive":true }
```
Indexes: `{ userId:1, dressType:1 }`.

## `appointments`
```jsonc
{ "_id":ObjectId, "userId":ObjectId, "mode":"doorstep",  // doorstep | boutique | video
  "dressType":"lehenga", "service":"stitching",
  "slot": { "date":"2026-08-08", "start":"15:00", "end":"16:00" },
  "addressId":ObjectId, "notes":"...",
  "status":"confirmed",            // requested | confirmed | completed | cancelled | no_show
  "remindersSent":["confirmation"], "createdAt":ISODate }
```
Indexes: `{ userId:1 }`, `{ "slot.date":1, status:1 }`.

## `calendarConfig`
```jsonc
{ "_id":ObjectId, "workingHours": { "mon":["10:00","19:00"], "sun":null },
  "slotMinutes":60, "maxPerSlot":3,
  "holidays":["2026-08-15"], "blockedDates":["2026-08-10"] }
```

## `carts` & `wishlists`
```jsonc
// carts
{ "_id":ObjectId, "userId":ObjectId,
  "items":[ { "productId":ObjectId, "size":"M", "qty":1, "addedAt":ISODate } ],
  "updatedAt":ISODate }
// wishlists
{ "_id":ObjectId, "userId":ObjectId, "productIds":[ObjectId], "updatedAt":ISODate }
```
Indexes: `{ userId:1 } unique` on both.

## `reviews`
```jsonc
{ "_id":ObjectId, "productId":ObjectId, "userId":ObjectId,
  "rating":5, "text":"…", "images":["gs://…"],
  "verifiedPurchase":true, "orderId":ObjectId, "createdAt":ISODate }
```
Indexes: `{ productId:1, createdAt:-1 }`, `{ userId:1 }`.

## `coupons`
```jsonc
{ "_id":ObjectId, "code":"THULYA10", "type":"percent",  // percent | flat | bulk
  "value":10, "maxDiscount":150000, "minOrder":100000,
  "appliesTo":"all", "festival":"navratri",
  "usageLimit":1000, "usedCount":214, "perUserLimit":1,
  "startsAt":ISODate, "endsAt":ISODate, "isActive":true }
```
Indexes: `{ code:1 } unique`, `{ isActive:1, endsAt:1 }`.

## `payments`
```jsonc
{ "_id":ObjectId, "orderId":ObjectId, "userId":ObjectId,
  "gateway":"razorpay", "method":"upi",   // upi|gpay|phonepe|card|cod
  "razorpayOrderId":"order_...", "razorpayPaymentId":"pay_...",
  "amount":261250, "kind":"advance",       // advance | balance | full | refund
  "status":"captured",                      // created|captured|failed|refunded
  "invoice": { "no":"INV-1188", "url":"gs://.../inv.pdf", "gstBreakup":{...} },
  "createdAt":ISODate }
```
Indexes: `{ orderId:1 }`, `{ razorpayPaymentId:1 } unique sparse`.

## `inventory`
```jsonc
{ "_id":ObjectId, "kind":"fabric",   // fabric|thread|lace|accessory|embroidery
  "name":"Kanjivaram Zari Border", "unit":"m", "quantity":42,
  "reorderLevel":10, "linkedProductIds":[ObjectId],
  "purchases":[ { "at":ISODate, "qty":50, "cost":2500000, "vendor":"..." } ] }
```
Indexes: `{ kind:1 }`, `{ quantity:1 }` (low-stock scans).

## `loyalty`
```jsonc
{ "_id":ObjectId, "userId":ObjectId, "tier":"gold", "points":1240,
  "ledger":[ { "at":ISODate, "delta":+85, "reason":"order:THU-2048" } ],
  "referralCode":"DIVYA25", "referredCount":3 }
```
Indexes: `{ userId:1 } unique`, `{ referralCode:1 } unique`.

## `notifications` & `campaigns`
```jsonc
// notifications
{ "_id":ObjectId, "userId":ObjectId, "channel":"whatsapp",  // push|whatsapp|sms|email
  "template":"order_ready", "payload":{...}, "status":"sent",
  "sentAt":ISODate }
// campaigns
{ "_id":ObjectId, "name":"Navratri Blast", "channel":"whatsapp",
  "segment":{ "tier":["gold","platinum"] }, "template":"festival_offer",
  "audienceCount":2400, "sentCount":2380, "scheduledAt":ISODate, "status":"completed" }
```

---

## Notes on modelling choices
- **Per-size stock** lives inside `products.sizes[]`; the aggregate `stock` is denormalised for list views and kept in sync on write.
- **Order fulfilment** is an append-only `history[]` — the tracking timeline is derived from it, never overwritten.
- **Money in paise (integer)** everywhere; convert only at the API/UI boundary.
- **Denormalised** `categoryPath` and `rating` on products keep catalogue queries single-collection (no joins) for Flutter list performance.
- Firebase Auth is the identity source of truth; `users` mirrors it via `firebaseUid`.
