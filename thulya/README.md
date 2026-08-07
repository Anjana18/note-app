# Thulya — Tailor Made For You ✦

A **premium boutique application** for handpicked sarees, designer blouses, aari
artistry and bespoke tailoring. This directory contains a **high-fidelity,
interactive web prototype** of the customer/admin/tailor experience plus the
**architecture & API documentation** for the full production build.

> Brand: Royal Blue · Blush Pink · White · Gold · Playfair Display + Poppins.
> Look & feel inspired by Sabyasachi / House of Masaba / Myntra Luxury — elegant,
> minimal, premium, with soft shadows, rounded cards, glassmorphism and subtle gold accents.

---

## What's in here

| Path | What it is |
|---|---|
| `index.html` | **Working single-file prototype** — no build step, open in any browser |
| `docs/DATABASE_SCHEMA.md` | MongoDB collections, fields, indexes, modelling notes |
| `docs/API_DOCUMENTATION.md` | REST API (Spring Boot) — all endpoints, roles, payloads |
| `docs/USER_FLOWS.md` | Mermaid user-flow diagrams for all three roles |

### Try the prototype
```bash
# from this directory
open thulya/index.html          # macOS
xdg-open thulya/index.html      # Linux
# or just double-click the file
```
No dependencies — fonts load from Google Fonts, everything else is inline.

---

## Prototype feature coverage

The prototype is fully interactive (cart, wishlist and theme persist in `localStorage`):

- **Home** — hero banner, category strip, New Arrivals / Trending / Designer Blouses /
  Featured sections, festival offer banner, AI-styling grid, reviews, loyalty tiers.
- **Shop** — category filter tabs, live search, responsive product grid.
- **Product detail** — gallery + thumbnails, "hover to zoom", specs (fabric, wash care,
  SKU, delivery, stock, offer price), size selector, Add to Cart / Buy Now / Wishlist /
  WhatsApp share, related products.
- **Tailoring** — six service groups with transparent, **admin-editable** pricing
  (double-click a price on the Tailoring page).
- **Book Measurement** — doorstep / boutique / video modes, full booking form, weekly
  slot calendar respecting availability, confirmation flow.
- **Track Order** — 9-stage progress timeline with active-stage highlight and assigned master.
- **Dashboards** — role switcher for **Customer** (orders, measurements, wishlist,
  appointments, invoices, loyalty), **Boutique Admin** (analytics, popular products,
  low-stock alerts, appointments, campaigns, exports) and **Tailor** (job queue, progress
  updates, photo upload, mark complete).
- **WhatsApp** integration hooks (floating chat, share, order, support), **dark mode**,
  smooth reveal-on-scroll animations, fully responsive down to mobile.

---

## Full production architecture (target)

```
Flutter (Android · iOS · Web)  ─┐
React + Material UI (Admin)    ─┼─▶  Spring Boot 3 REST API  ─▶  MongoDB
                                │        │  Firebase Auth (Phone OTP + Google)
                                │        │  Firebase Storage (media, invoices)
                                │        │  Firebase Cloud Messaging (push)
                                │        │  Razorpay (payments)
                                │        │  WhatsApp Business API (templates + campaigns)
                                │        │  Google Calendar (appointments)
                                │        └─ Google Maps (doorstep geo)
                                └─────────────────────────────  Hosted on AWS
```

**Security & performance targets:** JWT auth, role-based access control, encrypted
payments, dark mode, offline support, lazy/fast image loading, SEO-friendly web,
accessibility support, responsive design.

See `docs/` for the concrete schema, endpoints and flows that implement this.

---

## Scope note

This deliverable is a **design-complete, interactive prototype + architecture docs** —
the fastest way to validate the experience and hand engineering a precise spec. The full
platform (Flutter apps, Spring Boot services, all third-party integrations, tests, CI/CD,
AWS deployment) is a multi-month build; the schema and API docs here are written to be
implemented directly against.
