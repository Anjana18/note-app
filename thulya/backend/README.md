# Thulya Backend — Spring Boot + MongoDB

Production-style REST API for the Thulya boutique: catalogue, cart, wishlist,
tailoring pricing, orders + 9-stage tracking, measurements, appointments with
slot availability, and role dashboards (Customer / Admin / Tailor). JWT auth with
role-based access control, clean layered architecture, and a data seeder so the
API is usable the moment it starts.

- **Java 17** · **Spring Boot 3.2** · **Spring Data MongoDB** · **Spring Security** · **JWT (jjwt)**
- Layered: `web` (controllers) → `service` → `repository` → `domain`, with `dto`, `security`, `common`, `config`.

## Prerequisites
- JDK 17+ (tested on 21)
- Maven 3.9+ (or use `./mvnw` from a Spring Initializr wrapper)
- MongoDB running locally (`mongodb://localhost:27017/thulya`) — or point `MONGODB_URI` elsewhere

```bash
# quick Mongo via Docker
docker run -d --name thulya-mongo -p 27017:27017 mongo:6
```

## Run
```bash
cd thulya/backend
mvn spring-boot:run
# or
mvn -DskipTests package && java -jar target/thulya-backend-0.1.0.jar
```
On first start with an empty database, `DataSeeder` loads 8 categories, 12
products, the full tailoring price list, a `THULYA10` coupon, calendar config,
and three demo users (customer / admin / tailor). Disable with `THULYA_SEED=false`.

## Test
```bash
mvn test        # 12 unit tests, no MongoDB required (pricing, JWT, mappers)
```

## Configuration (`application.properties`, override via env)
| Property | Env | Default |
|---|---|---|
| `spring.data.mongodb.uri` | `MONGODB_URI` | `mongodb://localhost:27017/thulya` |
| `thulya.jwt.secret` | `THULYA_JWT_SECRET` | dev secret (rotate in prod) |
| `thulya.seed.enabled` | `THULYA_SEED` | `true` |

## Auth model
- **Dev login** (`POST /api/v1/auth/login`) issues a JWT directly from a phone number so the API is runnable without Firebase. Pass `"role":"admin"` / `"tailor"` to get those authorities.
- **Production path** (`POST /api/v1/auth/firebase`) is stubbed to show where Firebase ID-token verification plugs in — token issuance is identical once the verified identity is known.
- Access tokens carry `sub`, `role`, `name`; the `JwtAuthFilter` populates the `SecurityContext`; RBAC is enforced by URL rules + `@PreAuthorize`.

## Quick tour (curl)
```bash
BASE=http://localhost:8080/api/v1

# public catalogue
curl -s $BASE/categories | jq
curl -s "$BASE/products?category=Sarees&sort=popular" | jq
curl -s $BASE/tailoring/services | jq

# login as customer -> capture token
TOKEN=$(curl -s -X POST $BASE/auth/login -H 'Content-Type: application/json' \
  -d '{"phone":"+919000000001","name":"Divya","role":"customer"}' | jq -r .data.accessToken)
AUTH="Authorization: Bearer $TOKEN"

# add first product to cart, view totals (GST + coupon aware)
PID=$(curl -s $BASE/products | jq -r '.data[0].id')
curl -s -X POST $BASE/cart/items -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"productId\":\"$PID\",\"qty\":1}" | jq
curl -s -X POST $BASE/cart/apply-coupon -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"code":"THULYA10"}' | jq

# place order, then track its timeline
ORDER=$(curl -s -X POST $BASE/orders -H "$AUTH" -H 'Content-Type: application/json' -d '{"paymentKind":"advance"}' | jq -r .data.orderNo)
curl -s $BASE/orders/$ORDER/track -H "$AUTH" | jq

# admin: analytics + edit a tailoring price
ATOKEN=$(curl -s -X POST $BASE/auth/login -H 'Content-Type: application/json' \
  -d '{"phone":"+919000000002","role":"admin"}' | jq -r .data.accessToken)
curl -s $BASE/admin/analytics -H "Authorization: Bearer $ATOKEN" | jq
curl -s -X PUT $BASE/tailoring/services/blouse_dart -H "Authorization: Bearer $ATOKEN" \
  -H 'Content-Type: application/json' -d '{"price":699}' | jq
```

## Endpoint map
| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/firebase`, `POST /auth/refresh`, `GET /auth/me` |
| Catalogue (public GET) | `/categories`, `/products`, `/products/{slugOrId}`, `/products/{id}/related`, `/products/{id}/reviews` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH/DELETE /cart/items/{id}`, `POST /cart/apply-coupon` |
| Wishlist | `GET /wishlist`, `POST/DELETE /wishlist/{productId}` |
| Tailoring | `GET /tailoring/services` (public), `PUT /tailoring/services/{code}` (admin) |
| Orders | `POST /orders`, `GET /orders`, `GET /orders/{no}`, `GET /orders/{no}/track`, `PATCH /orders/{no}/stage` (admin/tailor), `PATCH /orders/{no}/assign` (admin) |
| Measurements | `GET/POST /measurements` |
| Appointments | `GET /appointments/slots` (public), `POST /appointments`, `GET /appointments` |
| Admin | `GET /admin/analytics` |
| Tailor | `GET /tailor/jobs` |

All responses use the envelope `{ success, data, message, meta }`. Money is stored
internally in paise and exposed at the API boundary in whole rupees.

## Design notes
- **Money in paise** (`common/Money`) throughout the domain; DTO mappers convert to rupees.
- **Order fulfilment** is an append-only `history[]`; the tracking timeline is derived, never overwritten. Stage transitions to `READY`/`DISPATCHED`/`DELIVERED` fire a (logged) WhatsApp notification via `NotificationService` — the integration point for the WhatsApp Business API and FCM.
- **Pricing** (`service/PricingService`) is persistence-free and unit-tested: coupon %/flat, max-cap, min-order, GST on the discounted amount.
- **Seeder** mirrors the web prototype's catalogue so the app and API line up.

## Not yet wired (next slices)
Razorpay charge/verify, Firebase Auth + Storage, FCM push, WhatsApp Business API,
Google Calendar sync, invoice PDF generation, inventory/loyalty endpoints. Each has
a clear seam in this codebase (`NotificationService`, `/auth/firebase`, payment DTOs).
