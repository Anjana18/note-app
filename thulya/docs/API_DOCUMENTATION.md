# Thulya — REST API Documentation

Backend: **Spring Boot 3 (Java 17)** · Base URL: `https://api.thulya.app/api/v1`
Auth: **Firebase ID token → verified server-side → app JWT** (Bearer).
All responses are JSON and wrapped:

```jsonc
{ "success": true, "data": { ... }, "message": null, "meta": { "page":0, "size":20, "total":248 } }
// error
{ "success": false, "data": null, "message": "PRODUCT_NOT_FOUND", "errors": [ ... ] }
```

Money in request/response is in **₹ (rupees, decimal)** at the API boundary; stored as paise internally.
Role-gated endpoints are marked `[ADMIN]` / `[TAILOR]`. Everything else needs a valid customer token unless marked `[PUBLIC]`.

---

## Auth

| Method | Path | Body / Notes |
|---|---|---|
| `POST` | `/auth/firebase` | `{ "idToken": "<firebase-id-token>" }` → exchanges for app JWT `{ accessToken, refreshToken, user }` |
| `POST` | `/auth/refresh` | `{ "refreshToken": "..." }` |
| `GET`  | `/auth/me` | Current user profile |
| `POST` | `/auth/logout` | Invalidates refresh token |
| `POST` | `/auth/fcm-token` | `{ "token": "..." }` register device for push |

`POST /auth/firebase` — sample response:
```json
{ "success": true, "data": {
    "accessToken": "eyJ...", "refreshToken": "eyJ...",
    "user": { "id":"...", "name":"Divya", "role":"customer", "loyaltyTier":"gold" } } }
```

---

## Catalogue `[PUBLIC]`

| Method | Path | Query params |
|---|---|---|
| `GET` | `/categories` | tree of categories |
| `GET` | `/products` | `category`, `sub`, `q`, `tags`, `minPrice`, `maxPrice`, `sort` (`popular\|new\|price_asc\|price_desc`), `page`, `size` |
| `GET` | `/products/{slugOrId}` | full product detail |
| `GET` | `/products/{id}/related` | related products |
| `GET` | `/products/{id}/reviews` | `page`, `size` |

`GET /products?category=sarees&sub=kanjivaram&sort=popular` →
```jsonc
{ "success":true, "data":[
  { "id":"...", "sku":"THU-KJV-001", "name":"Kanjivaram Royal Silk",
    "priceOffer":8499, "priceMrp":12999, "discountPct":35,
    "rating":{"avg":4.9,"count":214}, "image":"https://cdn/…1.jpg", "tags":["new"] }
], "meta":{ "page":0,"size":20,"total":38 } }
```

---

## Cart & Wishlist

| Method | Path | Body |
|---|---|---|
| `GET` | `/cart` | current cart with computed pricing |
| `POST` | `/cart/items` | `{ "productId":"...","size":"M","qty":1 }` |
| `PATCH` | `/cart/items/{itemId}` | `{ "qty":2 }` |
| `DELETE` | `/cart/items/{itemId}` | remove |
| `POST` | `/cart/apply-coupon` | `{ "code":"THULYA10" }` |
| `GET` | `/wishlist` | list |
| `POST` | `/wishlist/{productId}` | add |
| `DELETE` | `/wishlist/{productId}` | remove |

---

## Tailoring

| Method | Path | Notes |
|---|---|---|
| `GET` | `/tailoring/services` `[PUBLIC]` | grouped editable price list |
| `PUT` | `/tailoring/services/{itemCode}` `[ADMIN]` | `{ "price": 750 }` update price |
| `POST` | `/tailoring/quote` | `{ "serviceCode":"blouse_designer","addons":["embroidery"] }` → itemised quote |

---

## Measurements & Appointments

| Method | Path | Body |
|---|---|---|
| `GET` | `/measurements` | user's saved measurements |
| `POST` | `/measurements` | `{ "dressType":"blouse","values":{...} }` |
| `GET` | `/appointments/slots` `[PUBLIC]` | `?date=2026-08-08` available slots (respects `calendarConfig`) |
| `POST` | `/appointments` | `{ "mode":"doorstep","dressType":"lehenga","slot":{...},"addressId":"...","notes":"..." }` |
| `GET` | `/appointments` | user's bookings |
| `PATCH` | `/appointments/{id}` `[ADMIN]` | update status |
| `GET` | `/calendar/config` `[ADMIN]` / `PUT` | working hours, holidays, slot caps |

`POST /appointments` triggers a WhatsApp `booking_confirmation` template and schedules a `measurement_reminder`.

---

## Orders & Tracking

| Method | Path | Body / Notes |
|---|---|---|
| `POST` | `/orders` | create from cart `{ "addressId":"...","paymentKind":"advance" }` |
| `GET` | `/orders` | user's orders `?status=` |
| `GET` | `/orders/{orderNo}` | detail incl. `fulfilment.history` timeline |
| `GET` | `/orders/{orderNo}/track` `[PUBLIC-with-token]` | lightweight timeline for tracking page |
| `PATCH` | `/orders/{orderNo}/stage` `[ADMIN][TAILOR]` | `{ "stage":"stitching","photos":[...],"note":"..." }` — appends to history + fires WhatsApp update |
| `PATCH` | `/orders/{orderNo}/assign` `[ADMIN]` | `{ "tailorId":"..." }` |

Stage transition fires the matching notification: `stitching→…`, `ready`→`order_ready`, `dispatched`→`dispatch_notification`, `delivered`→`delivery_confirmation`.

---

## Payments (Razorpay)

| Method | Path | Body |
|---|---|---|
| `POST` | `/payments/create-order` | `{ "orderNo":"THU-2048","kind":"advance" }` → `{ razorpayOrderId, amount, currency, key }` |
| `POST` | `/payments/verify` | `{ razorpayOrderId, razorpayPaymentId, signature }` (HMAC verified) |
| `POST` | `/payments/webhook` `[PUBLIC-signed]` | Razorpay webhook (captured/failed/refund) |
| `GET` | `/payments/{orderNo}/invoice` | GST invoice PDF (Firebase Storage URL) |

---

## Reviews, Loyalty, Notifications

| Method | Path | Body |
|---|---|---|
| `POST` | `/products/{id}/reviews` | `{ "rating":5,"text":"...","images":[...] }` (verifiedPurchase auto-checked) |
| `GET` | `/loyalty` | tier, points, referral code, ledger |
| `POST` | `/loyalty/redeem` | `{ "points":500 }` → coupon |
| `GET` | `/notifications` | in-app feed |
| `POST` | `/whatsapp/send` `[ADMIN]` | `{ "template":"festival_offer","segment":{...} }` |

---

## Admin

| Method | Path | Notes |
|---|---|---|
| `GET` | `/admin/analytics` | `{ ordersToday, revenueToday, bookingsToday, pendingStitching, popularProducts[], lowStock[] }` |
| `POST` `PUT` `DELETE` | `/admin/products` `/admin/products/{id}` | CRUD catalogue |
| `GET` `POST` `PUT` | `/admin/coupons` | manage offers / festival sales / bulk discounts |
| `GET` `PATCH` | `/admin/inventory` | stock, fabric, threads, laces + low-stock alerts |
| `GET` | `/admin/customers` | customer database `?q=&tier=` |
| `POST` | `/admin/reports/export` | `{ "type":"orders","range":{...},"format":"csv" }` |
| `PATCH` | `/admin/customers/{id}/pricing` | special customer pricing |
| `PUT` | `/admin/settings/gst` | `{ "apparelPct":5 }` |

## Tailor

| Method | Path | Notes |
|---|---|---|
| `GET` | `/tailor/jobs` | today's jobs, priority, due dates |
| `PATCH` | `/orders/{orderNo}/stage` | update progress (shared with admin) |
| `POST` | `/tailor/jobs/{orderNo}/photos` | upload progress photos → Firebase Storage |

---

## Integrations summary
| Concern | Provider | Where |
|---|---|---|
| Auth | Firebase (Phone OTP + Google) | `/auth/firebase` |
| Storage | Firebase Storage | product media, invoices, progress photos |
| Push | Firebase Cloud Messaging | `/auth/fcm-token`, stage/appointment events |
| Payments | Razorpay | `/payments/*` |
| WhatsApp | WhatsApp Business API | templates on booking / stage / campaigns |
| Calendar | Google Calendar API | appointment sync for admin/tailor |
| Maps | Google Maps API | doorstep address geo + routing |

## Conventions
- **Pagination**: `page` (0-based), `size` (default 20, max 100); totals in `meta`.
- **Errors**: HTTP status + machine `message` code (e.g. `SLOT_UNAVAILABLE`, `COUPON_EXPIRED`, `OUT_OF_STOCK`).
- **Idempotency**: `POST /orders` and `/payments/verify` accept an `Idempotency-Key` header.
- **RBAC**: enforced via Spring Security method annotations (`@PreAuthorize("hasRole('ADMIN')")`).
- **Rate limits**: 60 req/min public, 300 req/min authenticated (per user).
