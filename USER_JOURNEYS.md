# Leisuretimez Platform -- User Journey Documentation

> Complete guide to every user journey on the Leisuretimez travel booking platform API.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Complete User Journey Map](#3-complete-user-journey-map)
4. [What Changed -- New Features Summary](#4-what-changed----new-features-summary)
5. [Carousel to Form Routing Diagram](#5-carousel-to-form-routing-diagram)
6. [Detailed Journey Flows](#6-detailed-journey-flows)
   - 6.1 [New User Registration & Onboarding](#61-new-user-registration--onboarding)
   - 6.2 [Package Booking Journey](#62-package-booking-journey)
   - 6.3 [Personalised Booking Journey](#63-personalised-booking-journey-new)
   - 6.4 [Cruise Booking Journey](#64-cruise-booking-journey-new--rewired)
   - 6.5 [Wallet & Payment Journey](#65-wallet--payment-journey)
   - 6.6 [Blog Engagement Journey](#66-blog-engagement-journey)
   - 6.7 [Support & Account Management](#67-support--account-management)
7. [API Endpoints Reference Table](#7-api-endpoints-reference-table)
8. [Postman Test Journeys](#8-postman-test-journeys)

---

## 1. Overview

Leisuretimez is a **travel booking platform** that connects customers with curated travel
packages, personalised events, and cruise experiences. The API powers both a mobile app and
a web frontend, providing:

- **Packages** -- Pre-built travel packages that customers can browse, book, and pay for
  through an automated pipeline (invoice generation, Stripe/wallet payment, PDF receipts).

- **Personalised Events** -- Custom event requests (birthday parties, weddings, corporate
  events, anniversaries, holidays) submitted via a form. An admin reviews and responds to
  each request.

- **Cruise Bookings** -- Boat cruise requests with cruise-specific fields (cruise type,
  duration in hours, onboard services). Uses the same model as personalised events but with
  `event_type` locked to `cruise`.

- **Carousel-driven Navigation** -- The homepage carousel determines which booking flow the
  user enters. Each carousel item carries a `category` field (`personalise`, `cruise`, or
  `packages`) that tells the app which form to render.

Supporting features include a digital **wallet** with Stripe-backed deposits, **blog** with
threaded comments and reactions, **support tickets**, **notifications**, **promo codes**,
**reviews**, and full **account lifecycle** management (registration, email verification,
password reset, profile editing, soft-delete).

---

## 2. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│                                                                              │
│     ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│     │ Mobile App  │          │  Web App    │          │  Postman    │        │
│     │ (iOS/Andr.) │          │ (Browser)   │          │  (Testing)  │        │
│     └──────┬──────┘          └──────┬──────┘          └──────┬──────┘        │
└────────────┼────────────────────────┼────────────────────────┼───────────────┘
             │                        │                        │
             │         HTTPS + Token Auth (Authorization: Token xxx)
             │                        │                        │
┌────────────▼────────────────────────▼────────────────────────▼───────────────┐
│                          DJANGO REST FRAMEWORK                               │
│                                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ auth_views  │  │   views.py   │  │wallet_views  │  │ blog_views   │      │
│  │             │  │              │  │              │  │              │      │
│  │ Register    │  │ Packages     │  │ Wallet CRUD  │  │ Posts CRUD   │      │
│  │ Login       │  │ Bookings     │  │ Deposit      │  │ Comments     │      │
│  │ Logout      │  │ Invoices     │  │ Withdraw     │  │ Reactions    │      │
│  │ Password    │  │ Payments     │  │ Transfer     │  │              │      │
│  │ Delete Acct │  │ Reviews      │  │ Transactions │  │              │      │
│  │             │  │ Promo Codes  │  │              │  │              │      │
│  │             │  │ Carousel     │  │              │  │              │      │
│  │             │  │ Personalised │  │              │  │              │      │
│  │             │  │ Cruise       │  │              │  │              │      │
│  │             │  │ Notifications│  │              │  │              │      │
│  │             │  │ Support      │  │              │  │              │      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘      │
│         │                │                │                │              │
│         └────────┬───────┴────────┬───────┴────────┬───────┘              │
│                  │                │                │                      │
│           ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐              │
│           │   Models    │  │  Webhook   │  │   Utils     │              │
│           │ (20 models) │  │ (Stripe)   │  │ (Email,     │              │
│           │             │  │            │  │  Notifs,    │              │
│           │             │  │            │  │  Activation)│              │
│           └──────┬──────┘  └─────┬──────┘  └──────┬──────┘              │
└──────────────────┼───────────────┼────────────────┼──────────────────────┘
                   │               │                │
     ┌─────────────▼───────┐   ┌──▼──────────┐  ┌──▼──────────────┐
     │  MySQL Database     │   │   Stripe    │  │  SMTP Server    │
     │  (via SSH Tunnel)   │   │   API       │  │  (Emails)       │
     │                     │   │             │  │                 │
     │  sshtunnel +        │   │ - Checkout  │  │  - Activation   │
     │  paramiko           │   │ - Payment   │  │  - Password     │
     │                     │   │   Intents   │  │    Reset        │
     │                     │   │ - Webhooks  │  │  - Invoices     │
     └─────────────────────┘   └─────────────┘  └─────────────────┘
                                                        │
                                                 ┌──────▼──────┐
                                                 │  PDFShift   │
                                                 │  (Invoice   │
                                                 │   PDF Gen)  │
                                                 └─────────────┘
```

---

## 3. Complete User Journey Map

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            LEISURETIMEZ USER JOURNEY MAP                            │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   USER LANDS     │
                              │   ON THE APP     │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │  GET /index/     │
                              │  (Homepage Data) │
                              │  Packages,       │
                              │  Destinations,   │
                              │  Events,         │
                              │  Carousel        │
                              └────────┬────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
  ┌────────▼─────────┐     ┌──────────▼──────────┐    ┌──────────▼──────────┐
  │ EXISTING USER    │     │  NEW USER           │    │ BROWSE AS GUEST     │
  │                  │     │                     │    │                     │
  │ POST /auth/      │     │ POST /auth/         │    │ GET /packages/      │
  │      login/      │     │      register/      │    │ GET /packages/<id>/ │
  │                  │     │                     │    │ GET /events/        │
  │ Returns:         │     │ Returns:            │    │ GET /blog/          │
  │  - token         │     │  - user + token     │    │                     │
  │  - profile       │     │  - activation email │    │ (No auth needed)    │
  │  - wallet balance│     │    sent             │    │                     │
  └────────┬─────────┘     └──────────┬──────────┘    └─────────────────────┘
           │                          │
           │               ┌──────────▼──────────┐
           │               │ CHECK EMAIL         │
           │               │ Click activation    │
           │               │ link                │
           │               │                     │
           │               │ GET /activate/      │
           │               │     <utoken>/<tok>/ │
           │               └──────────┬──────────┘
           │                          │
           │               ┌──────────▼──────────┐
           │               │ LOGIN               │
           │               │ POST /auth/login/   │
           │               └──────────┬──────────┘
           │                          │
           └──────────┬───────────────┘
                      │
             ┌────────▼────────┐
             │  AUTHENTICATED  │
             │  USER HOME      │
             └────────┬────────┘
                      │
    ┌────────┬────────┼────────┬────────┬────────┬────────┐
    │        │        │        │        │        │        │
    ▼        ▼        ▼        ▼        ▼        ▼        ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│CAROUSEL││PACKAGES││ WALLET ││  BLOG  ││SUPPORT ││NOTIFS  ││PROFILE │
│        ││BROWSE  ││        ││        ││        ││        ││        │
└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘└───┬────┘
    │         │         │         │         │         │         │
    │         │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼         ▼

 See Sec.5  See 6.2   See 6.5   See 6.6  See 6.7   See 6.7   See 6.7


═══════════════════════════════════════════════════════════════════════════
                      CAROUSEL-DRIVEN BOOKING PATHS
═══════════════════════════════════════════════════════════════════════════

  Carousel Item                    Booking Path
  (category field)
  ─────────────                    ────────────

  ┌──────────────┐      ┌──────────────────────────────────────────────┐
  │ "personalise"│─────→│  PERSONALISED BOOKING (Section 6.3)         │
  │              │      │  POST /personalised-bookings/               │
  │              │      │  Event form: type, dates, services, etc.    │
  │              │      │  Admin reviews → status updates             │
  └──────────────┘      └──────────────────────────────────────────────┘

  ┌──────────────┐      ┌──────────────────────────────────────────────┐
  │   "cruise"   │─────→│  CRUISE BOOKING (Section 6.4)               │
  │              │      │  POST /cruise-bookings/                     │
  │              │      │  Cruise form: cruise_type, hours, services  │
  │              │      │  event_type auto-set to "cruise"            │
  │              │      │  Admin reviews → status updates             │
  └──────────────┘      └──────────────────────────────────────────────┘

  ┌──────────────┐      ┌──────────────────────────────────────────────┐
  │  "packages"  │─────→│  PACKAGE BOOKING (Section 6.2)              │
  │              │      │  Browse → Select → Book → Pay → Invoice     │
  │              │      │  Full automated payment pipeline             │
  └──────────────┘      └──────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                      PACKAGE BOOKING PIPELINE
═══════════════════════════════════════════════════════════════════════════

  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────────┐
  │ Browse   │───→│ Select   │───→│ Book     │───→│ Choose Payment   │
  │ Packages │    │ Package  │    │ Package  │    │ Mode             │
  │          │    │          │    │          │    │                  │
  │GET       │    │GET       │    │POST      │    │GET /booking-     │
  │/packages/│    │/packages/│    │/book-    │    │payment/<id>/     │
  │          │    │ <pid>/   │    │package/  │    │<mode>/           │
  │          │    │          │    │<pid>/    │    │                  │
  └──────────┘    └──────────┘    └──────────┘    └────────┬─────────┘
                                                           │
                       ┌───────────────┬───────────────────┤
                       │               │                   │
                ┌──────▼──────┐ ┌──────▼──────┐  ┌────────▼────────┐
                │   WALLET    │ │   STRIPE    │  │     SPLIT       │
                │   mode      │ │   mode      │  │     mode        │
                │             │ │             │  │                 │
                │ Deduct from │ │ Stripe      │  │ Deduct wallet   │
                │ wallet      │ │ Checkout    │  │ balance, then   │
                │ balance     │ │ Session     │  │ Stripe Checkout │
                │             │ │ redirect    │  │ for remainder   │
                └──────┬──────┘ └──────┬──────┘  └────────┬────────┘
                       │               │                   │
                       └───────────────┼───────────────────┘
                                       │
                              ┌────────▼────────┐
                              │ CONFIRM BOOKING  │
                              │                  │
                              │ POST /booking-   │
                              │ confirm/         │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │ INVOICE PIPELINE │
                              │                  │
                              │ 1. Create Invoice│
                              │    (INV-000001)  │
                              │ 2. Record Payment│
                              │ 3. Generate PDF  │
                              │    (PDFShift)    │
                              │ 4. Email Invoice │
                              │ 5. Notify User   │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │ BOOKING COMPLETE │
                              │ Status: "paid"   │
                              └─────────────────┘
```

---

## 4. What Changed -- New Features Summary

| Feature | Endpoint | Method | What It Does |
|---------|----------|--------|--------------|
| **Carousel** | `GET /carousel/` | GET | Homepage banners ordered by position. Each item has a `category` field (`personalise`, `cruise`, `packages`) that determines which booking form the client app renders. |
| **Carousel Filter** | `GET /carousel/?category=cruise` | GET | Filter carousel items by category. |
| **Personalised Booking** | `/personalised-bookings/` | CRUD | Custom event request form. User selects event type (birthday, wedding, corporate, anniversary, holiday, cruise, other), dates, location, guest count, and services (catering, bar, decoration, security, photography, entertainment). Admin reviews and updates status. |
| **Cruise Booking** | `/cruise-bookings/` | CRUD | Dedicated cruise booking endpoint. Uses the same `PersonalisedBooking` model but auto-sets `event_type=cruise`. Includes cruise-specific fields: `cruise_type` (luxury, standard, budget, river, expedition) and `duration_hours`. |
| **Homepage Carousel Data** | `GET /index/` | GET | Now includes `carousel` array alongside packages, destinations, and events. |

### How the Three Booking Paths Compare

| Aspect | Package Booking | Personalised Booking | Cruise Booking |
|--------|----------------|---------------------|---------------|
| **Model** | `Booking` | `PersonalisedBooking` | `PersonalisedBooking` |
| **Endpoint** | `/book-package/<pid>/` | `/personalised-bookings/` | `/cruise-bookings/` |
| **Payment** | Automated (wallet/stripe/split) | Admin-managed | Admin-managed |
| **Invoice** | Auto-generated | Not applicable | Not applicable |
| **Status Flow** | pending -> invoiced -> paid | pending -> reviewed -> approved/rejected -> completed | pending -> reviewed -> approved/rejected -> completed |
| **event_type** | N/A | User selects (birthday, wedding, etc.) | Auto-set to `cruise` |
| **Carousel category** | `packages` | `personalise` | `cruise` |

---

## 5. Carousel to Form Routing Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       HOMEPAGE CAROUSEL                             │
│                                                                     │
│  GET /carousel/  or  included in GET /index/ response               │
│                                                                     │
│  Each item has: title, subtitle, image, cta_text, category          │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │  "Plan Your     │  │  "Set Sail on   │  │  "Explore Our   │     │
│  │   Dream Event"  │  │   a Cruise"     │  │   Packages"     │     │
│  │                 │  │                 │  │                 │     │
│  │  category:      │  │  category:      │  │  category:      │     │
│  │  "personalise"  │  │  "cruise"       │  │  "packages"     │     │
│  │                 │  │                 │  │                 │     │
│  │  [Explore ->]   │  │  [Book Now ->]  │  │  [View All ->]  │     │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘     │
└───────────┼─────────────────────┼─────────────────────┼─────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌───────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
│ PERSONALISED      │ │ CRUISE BOOKING    │ │ PACKAGE LIST          │
│ EVENT FORM        │ │ FORM              │ │                       │
│                   │ │                   │ │ GET /packages/        │
│ Full event form:  │ │ Cruise-specific   │ │                       │
│ - event_type      │ │ form:             │ │ Browse → Select →     │
│   (birthday,      │ │ - cruise_type     │ │ Book → Pay → Invoice  │
│    wedding,       │ │   (luxury,        │ │                       │
│    corporate,     │ │    standard,      │ │ Filters:              │
│    anniversary,   │ │    budget,        │ │ - search, continent,  │
│    holiday,       │ │    river,         │ │   country, category,  │
│    cruise,        │ │    expedition)    │ │   price range,        │
│    other)         │ │ - duration_hours  │ │   duration range,     │
│ - date_from/to    │ │ - date_from/to   │ │   sort_by             │
│ - location        │ │ - location       │ │                       │
│ - guests/adults/  │ │ - guests/adults/ │ │                       │
│   children        │ │   children       │ │                       │
│ - services        │ │ - services       │ │                       │
│   (catering, bar, │ │   (catering,     │ │                       │
│    decoration,    │ │    bar, etc.)    │ │                       │
│    security,      │ │ - comments       │ │                       │
│    photography,   │ │                  │ │                       │
│    entertainment) │ │ event_type is    │ │                       │
│ - comments        │ │ AUTO-SET to      │ │                       │
│                   │ │ "cruise"         │ │                       │
│ POST              │ │                  │ │                       │
│ /personalised-    │ │ POST             │ │                       │
│ bookings/         │ │ /cruise-         │ │                       │
│                   │ │ bookings/        │ │                       │
└─────────┬─────────┘ └─────────┬────────┘ └───────────┬───────────┘
          │                     │                       │
          ▼                     ▼                       ▼
┌───────────────────────────────────────┐   ┌───────────────────────┐
│ ADMIN REVIEW PIPELINE                 │   │ AUTOMATED PAYMENT     │
│                                       │   │ PIPELINE              │
│ Status: pending → reviewed →          │   │                       │
│         approved/rejected → completed │   │ Wallet / Stripe /     │
│                                       │   │ Split → Invoice →     │
│ Admin updates status and admin_notes  │   │ PDF → Email → Done    │
│ via PUT /personalised-bookings/<id>/  │   │                       │
│  or PUT /cruise-bookings/<id>/        │   │                       │
└───────────────────────────────────────┘   └───────────────────────┘
```

---

## 6. Detailed Journey Flows

### 6.1 New User Registration & Onboarding

```
Step  Action                          Endpoint                        Notes
────  ──────                          ────────                        ─────
 1    Register                        POST /auth/register/            Body: email, password,
                                                                      firstname, lastname
                                                                      Creates user + profile +
                                                                      auth token

 2    Receive activation email        (SMTP / console in dev)         Contains link:
                                                                      /activate/<utoken>/<token>/

 3    Click activation link           GET /activate/<utoken>/<token>/ Sets is_active=True
                                                                      (In dev mode with
                                                                      AUTO_ACTIVATE_USERS=True,
                                                                      this step is skipped)

 4    Login                           POST /auth/login/               Body: email, password
                                                                      Returns: token, user data,
                                                                      wallet balance, profile image
                                                                      Also creates Wallet +
                                                                      Stripe customer if needed

 5    (Optional) Complete profile     POST /profile/                  Body: phone, address, city,
                                      PUT /profile/                   state, country, date_of_birth,
                                      PATCH /profile/                 marital_status, profession,
                                                                      gender

 6    (Optional) Upload avatar        POST /profile/image/            Multipart form: image file
                                                                      Accepts: JPEG, PNG, GIF, WebP
                                                                      Max size: 5 MB
```

**Resend Activation Email:**
```
POST /resend-activation-email/     Body: { "email": "user@example.com" }
                                   Always returns same response (prevents account enumeration)
```

**Brute Force Protection:**
- 5 failed login attempts from the same IP triggers a 15-minute lockout
- Returns HTTP 429 during lockout period

---

### 6.2 Package Booking Journey

This is the original, fully-automated booking pipeline. Unchanged by recent additions.

```
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: BROWSE & DISCOVER                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GET /packages/                    List all active packages              │
│    ?search=safari                  Keyword search (name/description)     │
│    ?continent=Africa               Filter by continent                   │
│    ?country=Kenya                  Filter by country                     │
│    ?category=adventure             Filter by category                    │
│    ?min_price=100&max_price=5000   Price range filter                    │
│    ?min_duration=3&max_duration=14 Duration range filter                 │
│    ?sort_by=-price                 Sort: price, -price, duration,        │
│                                    -duration, name, -name, newest        │
│                                                                         │
│  GET /packages/<pid>/              Single package details                │
│                                    Returns: package, images, guest imgs  │
│                                                                         │
│  GET /packages/<pid>/reviews/      Package reviews + average rating      │
│                                                                         │
│  GET /search-locations/            Search by country/state/type          │
│  GET /search-countries-locations/  Search by country code + place types  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: SAVE PACKAGES (optional)                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /packages/save/<package_id>/     Save to favourites               │
│  POST /packages/unsave/<package_id>/   Remove from favourites           │
│  GET  /saved-packages/                 View all saved packages           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: CHECK PRICING                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GET /check-offer/<pid>/?adult=2&children=1                             │
│                                                                         │
│  For packages with tiered pricing (discount_price), returns the         │
│  matching price tier based on adult/children counts.                     │
│  Fixed-price packages return the fixed_price directly.                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: CREATE BOOKING                                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /book-package/<pid>/                                              │
│                                                                         │
│  Body: purpose, datefrom, dateto, continent, travelcountry,            │
│        travelstate, destinations, guests, duration, adult, children,    │
│        service, lastname, firstname, profession, email, phone,          │
│        gender, country, address, city, state, comment                   │
│                                                                         │
│  Returns: { booking_id: "BKN-XXXXXX" }                                 │
│  Status: "pending"                                                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4b: APPLY PROMO CODE (optional)                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /bookings/<booking_id>/apply-promo/                               │
│  Body: { "code": "SUMMER20" }                                           │
│                                                                         │
│  Validates code, calculates discount (percentage or fixed amount),      │
│  updates booking price. Only works on pending bookings.                  │
│                                                                         │
│  POST /bookings/<booking_id>/remove-promo/   (to undo)                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4c: MODIFY BOOKING (optional, only while pending)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /bookings/<booking_id>/modify/                                    │
│  Body: { "datefrom": "...", "dateto": "...", "adult": 3, ... }         │
│                                                                         │
│  Updates dates, guest counts, recalculates price.                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 5: PAY FOR BOOKING                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GET /booking-payment/<booking_id>/<mode>/                              │
│                                                                         │
│  mode = "wallet"                                                        │
│    Deducts full amount from wallet balance.                             │
│    Immediate completion.                                                │
│                                                                         │
│  mode = "stripe"                                                        │
│    Creates Stripe Checkout Session.                                     │
│    Returns checkout_url for redirect.                                   │
│    User completes payment on Stripe-hosted page.                        │
│                                                                         │
│  mode = "split"                                                         │
│    Deducts wallet balance first (whatever is available).                │
│    Creates Stripe Checkout Session for the remainder.                   │
│    If wallet covers full amount, processes as wallet payment.           │
│    If wallet is empty, returns error (use "stripe" mode instead).       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 6: CONFIRM BOOKING                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  POST /booking-confirm/                                                 │
│  Body: { "identifier": "<booking_id or session_id>", "mode": "..." }   │
│                                                                         │
│  Wallet mode:  identifier = booking_id                                  │
│  Stripe mode:  identifier = stripe session_id                           │
│  Split mode:   identifier = booking_id                                  │
│                                                                         │
│  Verifies payment, then triggers the invoice pipeline:                  │
│  1. Create Invoice (INV-000001, sequential with atomic retry)           │
│  2. Record Payment (PMT-XXXXXX)                                        │
│  3. Generate PDF via PDFShift                                           │
│  4. Email invoice PDF to customer                                       │
│  5. Create notifications (payment_received + booking_confirmed)         │
│  6. Set booking status = "paid"                                         │
│                                                                         │
│  Alternative: GET /bookings/complete/<booking_id>/                      │
│  (For Stripe redirect callback -- verifies session and runs pipeline)   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 7: POST-BOOKING                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  GET  /booking-history/              View all bookings                   │
│  GET  /bookings/<booking_id>/        View single booking details         │
│  GET  /preview-invoice/<inv>/        Preview invoice                     │
│  GET  /invoices/<inv>/download/      Download invoice PDF                │
│  POST /packages/<pid>/reviews/       Leave a review (1-5 stars + text)  │
│  POST /bookings/<booking_id>/cancel/ Cancel with refund policy          │
│                                                                         │
│  Cancellation refund policy:                                            │
│    7+ days before travel  → 100% refund to wallet                      │
│    3-7 days before        → 50% refund to wallet                       │
│    < 3 days before        → No refund                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 6.3 Personalised Booking Journey (NEW)

This is a **request-based** flow -- there is no automated payment. The user submits a
custom event request and an admin reviews it.

```
Step  Action                          Endpoint                            Notes
────  ──────                          ────────                            ─────
 1    User taps "personalise"         (Client-side routing)               Carousel item with
      carousel item                                                       category="personalise"

 2    Fill event form                 (Client-side UI)                    Fields: event_type,
                                                                          date_from, date_to,
                                                                          duration_hours/days,
                                                                          continent, country,
                                                                          state, destination,
                                                                          guests, adults, children,
                                                                          services (booleans),
                                                                          additional_comments

 3    Submit request                  POST /personalised-bookings/        Auth required
                                                                          event_type choices:
                                                                          birthday_party, wedding,
                                                                          corporate_event,
                                                                          anniversary, holiday,
                                                                          cruise, other

 4    View my requests                GET /personalised-bookings/         Returns user's own
                                                                          requests only

 5    View single request             GET /personalised-bookings/<id>/    Status + admin_notes

 6    Update request                  PUT /personalised-bookings/<id>/    While still pending
      (if needed)

 7    Admin reviews                   (Admin panel or API for staff)      Admin updates:
                                      PUT /personalised-bookings/<id>/    - status (pending →
                                                                            reviewed → approved/
                                                                            rejected → completed)
                                                                          - admin_notes

 8    User checks status              GET /personalised-bookings/<id>/    User sees updated
                                                                          status and admin notes
```

**Event Type Options:**
| Value | Description |
|-------|-------------|
| `birthday_party` | Birthday Party |
| `wedding` | Wedding |
| `corporate_event` | Corporate Event |
| `anniversary` | Anniversary |
| `holiday` | Holiday |
| `cruise` | Cruise |
| `other` | Other |

**Service Toggles (boolean fields):**
`catering`, `bar_attendance`, `decoration`, `special_security`, `photography`, `entertainment`

---

### 6.4 Cruise Booking Journey (NEW -- Rewired)

The cruise booking uses the **same model** (`PersonalisedBooking`) as personalised bookings
but with a dedicated endpoint that auto-sets `event_type=cruise`. This provides a
cruise-specific experience with relevant fields.

```
Step  Action                          Endpoint                            Notes
────  ──────                          ────────                            ─────
 1    User taps "cruise"              (Client-side routing)               Carousel item with
      carousel item                                                       category="cruise"

 2    Fill cruise form                (Client-side UI)                    Fields:
                                                                          - cruise_type (luxury,
                                                                            standard, budget,
                                                                            river, expedition)
                                                                          - duration_hours
                                                                          - date_from, date_to
                                                                          - continent, country
                                                                          - guests, adults,
                                                                            children
                                                                          - services (booleans)
                                                                          - additional_comments

 3    Submit cruise request           POST /cruise-bookings/              Auth required.
                                                                          event_type is AUTO-SET
                                                                          to "cruise" by the
                                                                          server (perform_create)

 4    View my cruise bookings         GET /cruise-bookings/               Filters to only show
                                                                          PersonalisedBooking
                                                                          records where
                                                                          event_type="cruise"

 5    View single cruise              GET /cruise-bookings/<id>/          Status + admin_notes

 6    Admin reviews                   PUT /cruise-bookings/<id>/          Admin updates status
                                                                          and admin_notes

 7    User checks status              GET /cruise-bookings/<id>/          User sees updated
                                                                          status and notes
```

**Cruise Type Options:**
| Value | Description |
|-------|-------------|
| `luxury` | Luxury Cruise |
| `standard` | Standard Cruise |
| `budget` | Budget Cruise |
| `river` | River Cruise |
| `expedition` | Expedition Cruise |

**Key Difference from Personalised Bookings:**
- `event_type` is automatically set to `cruise` -- the user does not choose it
- The endpoint filters to only show cruise bookings (`event_type='cruise'`)
- The form emphasizes `cruise_type` and `duration_hours` instead of generic event fields

---

### 6.5 Wallet & Payment Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          WALLET LIFECYCLE                                │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────┐
  │ WALLET CREATION      │
  │                      │
  │ Automatic on login   │  Created during POST /auth/login/ if not exists
  │ Manual:              │  POST /wallets/        (if not auto-created)
  │                      │  Also creates Stripe customer
  └──────────┬───────────┘
             │
  ┌──────────▼───────────┐
  │ VIEW WALLET          │
  │                      │
  │ GET /wallets/        │  Returns wallet balance and details
  │ GET /transactions/   │  Full transaction history
  │     wallettransactions│  Wallet + transactions in one call
  └──────────┬───────────┘
             │
     ┌───────┼───────┬───────────┐
     │       │       │           │
     ▼       ▼       ▼           ▼
  ┌──────┐┌──────┐┌──────┐  ┌──────┐
  │DEPOS.││WITH- ││TRANS-│  │VERIFY│
  │      ││DRAW  ││FER   │  │      │
  └──┬───┘└──┬───┘└──┬───┘  └──┬───┘
     │       │       │          │
     ▼       ▼       ▼          ▼

  DEPOSIT (two paths):

    Path A: Stripe Checkout (default)
      POST /wallets/deposit/
      Body: { "amount": 100.00, "success_url": "...", "cancel_url": "..." }
      Returns: checkout_url, session_id, transaction_id
      → User redirects to Stripe
      → Webhook (checkout.session.completed) credits wallet

    Path B: Payment Intent (with saved payment method)
      POST /wallets/deposit/
      Body: { "amount": 100.00, "payment_method_id": "pm_xxx" }
      Returns: transaction data (if succeeded immediately)
              or client_secret (if 3D Secure required)

  WITHDRAW:
    POST /wallets/<wallet_id>/withdraw/
    Body: { "amount": 50.00 }
    Uses select_for_update() for concurrency safety

  TRANSFER:
    POST /wallets/<wallet_id>/transfer/
    Body: { "recipient_id": "<wallet-uuid>", "amount": 25.00 }
    Atomic: deducts sender, credits recipient in one transaction

  VERIFY STRIPE PAYMENT:
    GET /verify-payment/<session_id>/
    Checks Stripe session status. IDOR-protected (user must own session).
```

**Webhook Flow (Stripe --> Server):**
```
  Stripe                          POST /paynotifier/              Server
  ─────                           ──────────────────              ──────

  payment_intent.succeeded    →   Find Transaction by PI ID   →  Credit wallet
  payment_intent.payment_failed → Find Transaction by PI ID   →  Mark as failed
  checkout.session.completed  →   Find Transaction by session  →  Credit wallet
  checkout.session.expired    →   If split_booking_payment     →  Refund wallet portion
                                  (expired Stripe checkout        to user, reset booking
                                   for split payment)             to pending

  All events: idempotency check via ProcessedStripeEvent model
  Signature verification via STRIPE_WEBHOOK_SECRET
```

---

### 6.6 Blog Engagement Journey

```
  ┌────────────────────────────────────────────────────────────────────┐
  │ BROWSE BLOG                                                        │
  │                                                                    │
  │ GET /blog/                         List published posts            │
  │                                    (staff see all statuses)        │
  │                                    Sorted by published_at          │
  │                                                                    │
  │ GET /blog/<slug>/                  Read single post                │
  │                                    Returns: title, content,        │
  │                                    excerpt, cover_image, tags,     │
  │                                    author, published_at,           │
  │                                    comment_count, reaction_summary │
  └───────────────────────────────────────┬────────────────────────────┘
                                          │
            ┌─────────────────────────────┼───────────────────┐
            │                             │                   │
            ▼                             ▼                   ▼
  ┌──────────────────┐      ┌──────────────────┐   ┌──────────────────┐
  │ COMMENT          │      │ REACT            │   │ MANAGE POSTS     │
  │ (Auth required)  │      │ (Auth required)  │   │ (Staff only)     │
  │                  │      │                  │   │                  │
  │ GET /blog/<slug>/│      │ POST /blog/      │   │ POST /blog/      │
  │   comments/      │      │   <slug>/react/  │   │ PUT /blog/<slug>/│
  │   (list, public) │      │                  │   │ DELETE /blog/    │
  │                  │      │ Body:            │   │   <slug>/        │
  │ POST /blog/      │      │ { "reaction_type"│   │                  │
  │   <slug>/        │      │   : "like" }     │   │ Statuses:        │
  │   comments/      │      │                  │   │ draft, published,│
  │                  │      │ Types: like,     │   │ archived         │
  │ Body:            │      │ love, insightful,│   │                  │
  │ { "content":     │      │ celebrate        │   │ Publishing       │
  │   "Great post!", │      │                  │   │ triggers notif   │
  │   "parent": null │      │ Toggle behavior: │   │ to all users     │
  │ }                │      │ Same reaction →  │   │                  │
  │                  │      │   remove (unreact)│  │                  │
  │ Threaded:        │      │ Diff reaction →  │   │                  │
  │ Set parent=<id>  │      │   update type    │   │                  │
  │ for replies      │      │ No reaction →    │   │                  │
  │                  │      │   create new     │   │                  │
  │ PUT /blog/       │      │                  │   │                  │
  │  comments/<id>/  │      │ GET /blog/       │   │                  │
  │ DELETE /blog/    │      │  <slug>/         │   │                  │
  │  comments/<id>/  │      │  reactions/      │   │                  │
  │ (own only)       │      │  (summary+list)  │   │                  │
  └──────────────────┘      └──────────────────┘   └──────────────────┘

  Notifications generated:
  - New blog post published → all active users notified
  - Comment on a post → post author notified
  - Reaction on a post → post author notified
```

---

### 6.7 Support & Account Management

#### Support Tickets

```
Step  Action                          Endpoint                            Notes
────  ──────                          ────────                            ─────
 1    Create ticket                   POST /support/                      Body: subject, message,
                                                                          priority (low/medium/high)
                                                                          Creates ticket + initial
                                                                          message

 2    View my tickets                 GET /support/                       List all user's tickets

 3    View single ticket              GET /support/<id>/                  Includes all messages

 4    Reply to ticket                 POST /support/<id>/reply/           Body: { "message": "..." }
                                                                          Cannot reply to closed
                                                                          tickets

 5    Close ticket                    POST /support/<id>/close/           Sets status to "closed"

Ticket statuses: open → in_progress → resolved → closed
```

#### Notifications

```
  GET  /notifications/                    List all notifications (paginated)
  GET  /notifications/unread_count/       Get unread count
  POST /notifications/<id>/read/          Mark single as read
  POST /notifications/mark-all-read/      Mark all as read

  Notification types:
    booking_confirmed, payment_received, trip_reminder,
    booking_cancelled, refund_processed, promo, system,
    new_blog_post, blog_comment, blog_reaction
```

#### Profile Management

```
  GET    /profile/                        Retrieve profile
  PUT    /profile/                        Full update
  PATCH  /profile/                        Partial update
  POST   /profile/                        Partial update (convenience)
  POST   /profile/image/                  Upload profile image
  POST   /update_display_picture/         Alternative image upload
  GET    /account-settings/               Profile + booking history
  GET    /personal-booking/               Customer profile data
```

#### Password Management

```
  POST /change-password/                  Body: old_password, new_password
                                          Revokes old token, returns new one

  POST /reset-password/                   Body: { "email": "..." }
                                          Sends reset email (always same
                                          response to prevent enumeration)

  POST /reset-password-confirm/           Body: { "new_password": "..." }
       <utoken>/<token>/                  Uses token from email link
```

#### Account Deletion (Soft Delete)

```
  DELETE /delete-account/                 Body: { "password": "..." }

  What happens:
  1. AccountDeletionLog created (preserves original identity for auditing)
  2. Auth token revoked
  3. User deactivated (is_active=False)
  4. User email → "deleted_<pk>@deactivated.local"
  5. Name → "Deleted User"
  6. Password set to unusable
  7. Profile anonymized (phone, address, DOB cleared)
  8. Wallet deactivated (balance preserved for audit)
  9. Booking/invoice/transaction records preserved (no cascade delete)
```

#### Contact Form

```
  POST /contact/                          Body: fullname, subject, email, message
                                          No auth required
                                          Sends notification email to admin
```

---

## 7. API Endpoints Reference Table

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register/` | No | Register new user account |
| POST | `/auth/login/` | No | Login and receive auth token |
| POST | `/auth/logout/` | Yes | Revoke auth token |
| GET | `/activate/<utoken>/<token>/` | No | Activate account from email link |
| POST | `/resend-activation-email/` | No | Resend activation email |
| POST | `/change-password/` | Yes | Change password (returns new token) |
| POST | `/reset-password/` | No | Request password reset email |
| POST | `/reset-password-confirm/<utoken>/<token>/` | No | Set new password from reset link |
| DELETE | `/delete-account/` | Yes | Soft-delete account (password required) |

### Homepage & Packages

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/index/` | No | Homepage data (packages, destinations, events, carousel) |
| GET | `/packages/` | No | List packages with search, filter, sort |
| GET | `/packages/<pid>/` | No | Package details with images |
| GET | `/events/` | No | List active events (filterable by country) |
| GET | `/events/<id>/` | No | Single event details |
| GET | `/carousel/` | No | List active carousel items |
| GET | `/carousel/?category=cruise` | No | Filter carousel by category |

### Package Save/Unsave

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/packages/save/<package_id>/` | Yes | Save package to favourites |
| POST | `/packages/unsave/<package_id>/` | Yes | Remove from favourites |
| GET | `/saved-packages/` | Yes | View saved packages |

### Bookings

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/book-package/<pid>/` | Yes | Create booking for a package |
| GET | `/bookings/` | Yes | List user's bookings (staff see all) |
| GET | `/bookings/<booking_id>/` | Yes | Single booking details |
| POST | `/bookings/<booking_id>/modify/` | Yes | Modify pending booking |
| POST | `/bookings/<booking_id>/cancel/` | Yes | Cancel booking with refund |
| GET | `/booking-history/` | Yes | User's booking history |
| GET | `/check-offer/<pid>/?adult=N&children=N` | Yes | Check tiered pricing |

### Payments

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/booking-payment/<booking_id>/<mode>/` | Yes | Pay booking (wallet/stripe/split) |
| POST | `/booking-confirm/` | Yes | Confirm payment and run invoice pipeline |
| GET | `/bookings/complete/<booking_id>/` | Yes | Complete booking after Stripe redirect |
| POST | `/make-payment/<inv>/` | Yes | Record payment for an invoice |
| GET | `/verify-payment/<session_id>/` | Yes | Verify Stripe checkout session |
| POST | `/paynotifier/` | No* | Stripe webhook receiver (*signature verified) |

### Invoices

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/preview-invoice/<inv>/` | Yes | Preview invoice data |
| GET | `/print-invoice/<invoice_id>/` | No | Render invoice HTML (for PDFShift) |
| GET | `/invoices/<invoice_id>/download/` | Yes | Download invoice PDF |

### Promo Codes

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/bookings/<booking_id>/apply-promo/` | Yes | Apply promo code to pending booking |
| POST | `/bookings/<booking_id>/remove-promo/` | Yes | Remove applied promo code |

### Reviews

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/packages/<pid>/reviews/` | No | List reviews with average rating |
| POST | `/packages/<pid>/reviews/` | Yes | Create review (must have paid booking) |
| PUT | `/reviews/<review_id>/` | Yes | Update own review |
| DELETE | `/reviews/<review_id>/` | Yes | Delete own review |

### Personalised Bookings (NEW)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/personalised-bookings/` | Yes | List user's requests (staff see all) |
| POST | `/personalised-bookings/` | Yes | Create personalised event request |
| GET | `/personalised-bookings/<id>/` | Yes | View single request |
| PUT | `/personalised-bookings/<id>/` | Yes | Update request / admin status update |
| DELETE | `/personalised-bookings/<id>/` | Yes | Delete request |

### Cruise Bookings (NEW)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/cruise-bookings/` | Yes | List user's cruise requests (staff see all) |
| POST | `/cruise-bookings/` | Yes | Create cruise request (event_type auto=cruise) |
| GET | `/cruise-bookings/<id>/` | Yes | View single cruise request |
| PUT | `/cruise-bookings/<id>/` | Yes | Update request / admin status update |
| DELETE | `/cruise-bookings/<id>/` | Yes | Delete request |

### Wallet

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/wallets/` | Yes | View wallet |
| POST | `/wallets/` | Yes | Create wallet (if not auto-created) |
| POST | `/wallets/deposit/` | Yes | Deposit via Stripe |
| POST | `/wallets/<id>/withdraw/` | Yes | Withdraw from wallet |
| POST | `/wallets/<id>/transfer/` | Yes | Transfer to another wallet |
| GET | `/wallets/<id>/transactions/` | Yes | Wallet transaction history |
| GET | `/transactions/` | Yes | Transaction list (completed/failed) |
| GET | `/transactions/wallettransactions/` | Yes | Wallet + transactions combined |

### Notifications

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/notifications/` | Yes | List notifications |
| GET | `/notifications/<id>/` | Yes | Single notification |
| GET | `/notifications/unread_count/` | Yes | Unread count |
| POST | `/notifications/<id>/read/` | Yes | Mark as read |
| POST | `/notifications/mark-all-read/` | Yes | Mark all as read |

### Support Tickets

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/support/` | Yes | List user's tickets |
| POST | `/support/` | Yes | Create ticket with initial message |
| GET | `/support/<id>/` | Yes | View ticket with messages |
| POST | `/support/<id>/reply/` | Yes | Reply to ticket |
| POST | `/support/<id>/close/` | Yes | Close ticket |

### Blog

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/blog/` | No | List published posts |
| GET | `/blog/<slug>/` | No | Read single post |
| POST | `/blog/` | Staff | Create post |
| PUT | `/blog/<slug>/` | Staff | Update post |
| PATCH | `/blog/<slug>/` | Staff | Partial update post |
| DELETE | `/blog/<slug>/` | Staff | Delete post |
| GET | `/blog/<slug>/reactions/` | No | Reaction summary for post |
| GET | `/blog/<slug>/comments/` | No | List comments (threaded) |
| POST | `/blog/<slug>/comments/` | Yes | Add comment |
| PUT | `/blog/comments/<id>/` | Yes | Edit own comment |
| DELETE | `/blog/comments/<id>/` | Yes | Delete own comment |
| POST | `/blog/<slug>/react/` | Yes | React/unreact to post |

### Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/profile/` | Yes | Get profile |
| PUT | `/profile/` | Yes | Full profile update |
| PATCH | `/profile/` | Yes | Partial profile update |
| POST | `/profile/` | Yes | Partial profile update (convenience) |
| POST | `/profile/image/` | Yes | Upload profile image |
| POST | `/update_display_picture/` | Yes | Alternative image upload |
| GET | `/account-settings/` | Yes | Profile + booking history |
| GET | `/personal-booking/` | Yes | Customer profile data |

### Search

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/search-locations/` | No | Search by country/state/type |
| GET | `/search-countries-locations/` | No | Search by country code + place types |

### Contact

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/contact/` | No | Submit contact form |

---

## 8. Postman Test Journeys

The following 18 test journeys cover the full API surface. Each journey is designed to be
run in sequence within a Postman collection.

| # | Journey Name | Description | Key Endpoints Tested |
|---|-------------|-------------|---------------------|
| 1 | **New User Registration** | Register, receive token, verify activation email is sent | `POST /auth/register/` |
| 2 | **Account Activation** | Activate account via email link, confirm user is now active | `GET /activate/<utoken>/<token>/` |
| 3 | **Login & Token** | Login with valid credentials, verify token and profile data returned | `POST /auth/login/` |
| 4 | **Brute Force Lockout** | Attempt 5+ failed logins, verify 429 lockout response | `POST /auth/login/` (x6) |
| 5 | **Browse Homepage** | Load homepage data, verify packages, destinations, events, carousel returned | `GET /index/` |
| 6 | **Package Discovery** | Search, filter, sort packages. Check pricing tiers. View package details and reviews | `GET /packages/`, `GET /packages/<pid>/`, `GET /check-offer/<pid>/`, `GET /packages/<pid>/reviews/` |
| 7 | **Save/Unsave Packages** | Save a package, verify it appears in saved list, unsave it | `POST /packages/save/<id>/`, `GET /saved-packages/`, `POST /packages/unsave/<id>/` |
| 8 | **Package Booking (Wallet)** | Create booking, apply promo code, pay with wallet, confirm, verify invoice | `POST /book-package/<pid>/`, `POST .../apply-promo/`, `GET /booking-payment/.../wallet/`, `POST /booking-confirm/` |
| 9 | **Package Booking (Stripe)** | Create booking, pay with Stripe checkout, complete booking | `POST /book-package/<pid>/`, `GET /booking-payment/.../stripe/`, `GET /bookings/complete/<id>/` |
| 10 | **Package Booking (Split)** | Create booking, pay with split (wallet + Stripe), confirm | `POST /book-package/<pid>/`, `GET /booking-payment/.../split/`, `POST /booking-confirm/` |
| 11 | **Booking Modification & Cancellation** | Modify a pending booking, cancel a paid booking, verify refund | `POST .../modify/`, `POST .../cancel/` |
| 12 | **Personalised Booking** | Create personalised event request, view it, simulate admin status update | `POST /personalised-bookings/`, `GET /personalised-bookings/`, `PUT /personalised-bookings/<id>/` |
| 13 | **Cruise Booking** | Create cruise request, verify event_type=cruise auto-set, view it | `POST /cruise-bookings/`, `GET /cruise-bookings/`, `GET /cruise-bookings/<id>/` |
| 14 | **Wallet Operations** | Deposit (Stripe checkout), withdraw, transfer between wallets, view transactions | `POST /wallets/deposit/`, `POST /wallets/<id>/withdraw/`, `POST /wallets/<id>/transfer/`, `GET /transactions/wallettransactions/` |
| 15 | **Blog Full Cycle** | Browse posts, read post, comment (with reply), react (add/change/remove) | `GET /blog/`, `GET /blog/<slug>/`, `POST /blog/<slug>/comments/`, `POST /blog/<slug>/react/` |
| 16 | **Support Tickets** | Create ticket, view it, reply, close | `POST /support/`, `GET /support/<id>/`, `POST /support/<id>/reply/`, `POST /support/<id>/close/` |
| 17 | **Notifications** | Check unread count, list notifications, mark as read, mark all as read | `GET /notifications/unread_count/`, `GET /notifications/`, `POST /notifications/<id>/read/`, `POST /notifications/mark-all-read/` |
| 18 | **Account Lifecycle** | Update profile, change password, reset password flow, delete account | `PATCH /profile/`, `POST /change-password/`, `POST /reset-password/`, `DELETE /delete-account/` |

### Running the Collection

1. **Environment Variables**: Set `base_url`, `auth_token`, `test_email`, `test_password`
2. **Order**: Run journeys 1-3 first to establish a user and token
3. **Dependencies**: Journey 8-10 require a wallet with balance (run journey 14 first)
4. **Admin Tests**: Journeys 12-13 (status updates) require a staff user token
5. **Webhook Tests**: Journey 14 deposit completion requires a Stripe webhook or manual
   verification via `GET /verify-payment/<session_id>/`

---

*Document generated from source code analysis of the Leisuretimez API codebase.*
