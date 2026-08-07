# Thulya — User Flow Diagrams

Three roles: **Customer**, **Boutique Admin**, **Tailor/Master**. Diagrams below are
Mermaid — they render on GitHub and in the Artifact preview.

---

## 1. Authentication (all roles)
```mermaid
flowchart TD
    A[Open App] --> B{Signed in?}
    B -- No --> C[Choose method]
    C --> D[Phone OTP]
    C --> E[Google Sign-In]
    D --> F[Firebase verifies]
    E --> F
    F --> G[Exchange Firebase token for app JWT]
    G --> H{Role}
    H -- customer --> I[Home / Shop]
    H -- admin --> J[Admin Dashboard]
    H -- tailor --> K[Tailor Dashboard]
    B -- Yes --> H
```

## 2. Customer — Browse to Delivery
```mermaid
flowchart TD
    H[Home: hero, sections, search] --> S[Shop / Category filter]
    S --> P[Product detail: images, zoom, video, specs]
    P --> W[Add to Wishlist]
    P --> C[Add to Cart / Buy Now]
    P --> WA[Share on WhatsApp]
    C --> CART[Cart: qty, coupon, GST]
    CART --> CO[Checkout]
    CO --> PAY{Payment}
    PAY --> UPI[UPI / GPay / PhonePe]
    PAY --> CARD[Card]
    PAY --> COD[Cash on Delivery]
    PAY --> ADV[Advance + Balance]
    UPI & CARD & COD & ADV --> ORD[Order created]
    ORD --> TRK[Track: 9-stage timeline]
    TRK --> NOTIF[WhatsApp/Push at each stage]
    NOTIF --> DEL[Delivered → Review + Loyalty points]
```

## 3. Customer — Tailoring + Measurement
```mermaid
flowchart TD
    T[Tailoring Services] --> SEL[Pick service + see price]
    SEL --> BK[Book Measurement]
    BK --> MODE{Mode}
    MODE --> DOOR[Doorstep]
    MODE --> STORE[Boutique Visit]
    MODE --> VID[Video Call]
    DOOR & STORE & VID --> SLOT[Pick available slot on calendar]
    SLOT --> FORM[Name, phone, address, date, time, dress type, notes]
    FORM --> CONF[Confirmation + WhatsApp message]
    CONF --> REM[Reminder 1 day before]
    REM --> MEAS[Measurements saved to profile]
    MEAS --> JOB[Tailoring order → fulfilment pipeline]
```

## 4. Order fulfilment pipeline (Admin + Tailor)
```mermaid
flowchart LR
    OR[Order Received] --> MC[Measurement Completed]
    MC --> CUT[Cutting] --> ST[Stitching] --> EMB[Embroidery]
    EMB --> QC[Quality Check] --> RD[Ready] --> DIS[Dispatched] --> DL[Delivered]
    ST -. progress photos .-> APP[(App timeline updates)]
    RD -. WhatsApp: order_ready .-> CUST[Customer]
    DIS -. WhatsApp: dispatch .-> CUST
    DL -. WhatsApp: delivered .-> CUST
```

## 5. Boutique Admin
```mermaid
flowchart TD
    AD[Admin Dashboard] --> AN[Analytics: orders, revenue, bookings]
    AD --> INV[Inventory: stock, fabric, low-stock alerts]
    AD --> PRD[Products: add/edit, pricing, offers]
    AD --> COUP[Coupons: festival, bulk, referral]
    AD --> APPT[Appointments: assign, calendar config]
    AD --> ASSIGN[Assign orders to tailors]
    AD --> CAMP[WhatsApp campaigns + customer DB]
    AD --> REP[Export reports]
    PRD --> GST[GST + special customer pricing]
```

## 6. Tailor / Master
```mermaid
flowchart TD
    TD[Tailor Dashboard] --> JOBS[Today's jobs + priority queue]
    JOBS --> DUE[Sort by due date]
    JOBS --> M[View customer measurements]
    JOBS --> UP[Upload progress photos]
    UP --> STG[Update stage]
    STG --> DONE[Mark complete]
    DONE --> NEXT[Auto-notify customer + next in queue]
```

## 7. Notification engine (cross-cutting)
```mermaid
flowchart LR
    EV[Event: booking / stage change / offer / birthday] --> ROUTER{Channel routing}
    ROUTER --> PUSH[FCM Push]
    ROUTER --> WAP[WhatsApp Business API]
    ROUTER --> SMS[SMS]
    ROUTER --> EM[Email]
    WAP --> TPL[Template: confirmation, reminder, ready, dispatch, offer]
```

---

### Screen inventory (Flutter)
`Splash → Auth → Home → Search → Category → Product Detail → Cart → Checkout → Payment →
Order Success → Track Order → Tailoring → Book Measurement → Calendar → Customer Dashboard
(Orders, Measurements, Wishlist, Appointments, Invoices, Addresses, Loyalty) → Gallery →
Offers → Notifications → Profile/Settings (Dark Mode)`.

Admin & Tailor run as the **React + Material UI** web panel and the role-gated Flutter web build.
