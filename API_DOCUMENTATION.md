# Leisuretimez API Documentation

> **Base URL:** `https://api.leisuretimez.com`
> **Authentication:** Token-based (`Authorization: Token <token>`)
> **Content-Type:** `application/json` (unless uploading files)

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [Authentication & Token Management](#authentication--token-management)
3. [User Journeys (End-to-End Flows)](#user-journeys)
4. [API Endpoint Reference](#api-endpoint-reference)
   - [Auth Endpoints](#auth-endpoints)
   - [Profile & Account](#profile--account)
   - [Packages & Browsing](#packages--browsing)
   - [Bookings](#bookings)
   - [Payments](#payments)
   - [Invoices](#invoices)
   - [Reviews](#reviews)
   - [Promo Codes](#promo-codes)
   - [Wallet](#wallet)
   - [Notifications](#notifications)
   - [Support Tickets](#support-tickets)
   - [Saved Packages](#saved-packages)
   - [Search](#search)
   - [Events](#events)
   - [Contact](#contact)
   - [Webhooks (Server-side)](#webhooks)
5. [Data Models](#data-models)
6. [Status Codes & Error Handling](#status-codes--error-handling)
7. [Booking Status State Machine](#booking-status-state-machine)

---

## Platform Overview

Leisuretimez is a travel booking platform where users can:
- Browse and search travel packages (tourism, hotel, cruises)
- Book packages with flexible payment options (wallet, Stripe, or split)
- Manage a digital wallet (deposit, withdraw, transfer)
- Cancel/modify bookings with time-based refund policy
- Leave reviews on completed trips
- Apply promo codes for discounts
- Receive in-app + email notifications
- Contact support via tickets
- Download PDF invoices

---

## Authentication & Token Management

All authenticated endpoints require the header:
```
Authorization: Token <your_token_here>
```

The token is returned on **register** and **login**. It persists until **logout** or **password change** (which rotates the token).

---

## User Journeys

### Journey 1: New User Registration & First Booking

```
1. POST /auth/register/          -- Create account (email + password)
2. GET  /activate/<utoken>/<token>/  -- Click email link to verify account
3. POST /auth/login/             -- Login, receive token + profile data
4. GET  /packages/               -- Browse available packages
5. GET  /packages/<pid>/         -- View package details
6. POST /book-package/<pid>/     -- Create a booking
7. GET  /booking-payment/<booking_id>/stripe/  -- Get Stripe checkout URL
8. [User completes Stripe payment externally]
9. POST /booking-confirm/        -- Confirm payment (mode: stripe, identifier: session_id)
10. GET /invoices/<invoice_id>/download/  -- Download PDF invoice
```

### Journey 2: Returning User with Wallet Payment

```
1. POST /auth/login/              -- Login
2. GET  /transactions/wallettransactions/  -- Check wallet balance
3. POST /wallets/deposit/         -- Add funds via Stripe Checkout
4. GET  /verify-payment/<session_id>/  -- Verify deposit completed
5. GET  /packages/?continent=Europe&sort_by=-price  -- Search packages
6. POST /book-package/<pid>/      -- Create booking
7. POST /bookings/<id>/apply-promo/  -- Apply discount code
8. GET  /booking-payment/<id>/wallet/  -- Pay entirely from wallet
9. POST /booking-confirm/         -- Confirm wallet payment
10. GET /notifications/           -- See booking + payment notifications
```

### Journey 3: Split Payment (Wallet + Stripe)

```
1. POST /auth/login/
2. GET  /packages/<pid>/
3. POST /book-package/<pid>/
4. GET  /booking-payment/<id>/split/   -- Wallet deducted, Stripe checkout URL returned
5. [User completes remaining amount on Stripe]
6. POST /booking-confirm/              -- Confirm split (mode: split, identifier: booking_id)
7. GET  /notifications/
```

### Journey 4: Booking Cancellation & Refund

```
1. GET  /booking-history/              -- View past bookings
2. POST /bookings/<id>/cancel/         -- Cancel with reason
   Response includes refund_amount & refund_status based on policy:
   - 7+ days before travel: 100% refund to wallet
   - 3-7 days: 50% refund
   - <3 days: no refund
3. GET  /notifications/                -- Cancellation + refund notifications
4. GET  /transactions/wallettransactions/  -- See refund in wallet history
```

### Journey 5: Booking Modification

```
1. GET  /bookings/<booking_id>/        -- View booking details
2. POST /bookings/<id>/modify/         -- Change dates/guests (pending only)
   Price auto-recalculates if guest count changes
```

### Journey 6: Review After Trip

```
1. GET  /packages/<pid>/reviews/       -- See existing reviews
2. POST /packages/<pid>/reviews/       -- Submit review (rating 1-5 + comment)
   (Only if user has a paid booking for this package)
3. PUT  /reviews/<review_id>/          -- Update your review
4. DELETE /reviews/<review_id>/        -- Delete your review
```

### Journey 7: Support Ticket Flow

```
1. POST /support/                      -- Create ticket (subject + message + priority)
2. GET  /support/                      -- List your tickets
3. GET  /support/<id>/                 -- View ticket with all messages
4. POST /support/<id>/reply/           -- Add a reply
5. POST /support/<id>/close/           -- Close the ticket
```

### Journey 8: Wallet Management

```
1. POST /wallets/                      -- Create wallet (first time)
2. POST /wallets/deposit/              -- Deposit via Stripe
3. POST /wallets/<id>/withdraw/        -- Withdraw funds
4. POST /wallets/<id>/transfer/        -- Transfer to another user
5. GET  /wallets/<id>/transactions/    -- View transaction history
6. GET  /transactions/wallettransactions/  -- Wallet + recent transactions
```

### Journey 9: Profile & Account Management

```
1. GET  /profile/                      -- View full profile
2. POST /profile/                      -- Update profile fields
3. POST /profile/image/                -- Upload profile image
4. POST /change-password/              -- Change password (returns new token)
5. DELETE /delete-account/             -- Soft-delete (password required)
```

### Journey 10: Password Recovery

```
1. POST /reset-password/               -- Request reset email
2. POST /reset-password-confirm/<utoken>/<token>/  -- Set new password
3. POST /auth/login/                   -- Login with new password
```

---

## API Endpoint Reference

### Auth Endpoints

#### Register
```
POST /auth/register/
```
**Auth:** None

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "firstname": "John",
  "lastname": "Doe"
}
```
**Response (201):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe"
  },
  "token": "abc123tokenhere"
}
```
**Side effects:** Sends verification email. Account is inactive until verified.

---

#### Login
```
POST /auth/login/
```
**Auth:** None

**Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```
**Response (200):**
```json
{
  "token": "abc123tokenhere",
  "id": 1,
  "email": "user@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "wallet": "150.00",
  "image": "/media/profile/images/photo.jpg"
}
```
**Notes:** Creates wallet and Stripe customer on first login if they don't exist.

---

#### Logout
```
POST /auth/logout/
```
**Auth:** Required

**Response (200):**
```json
{
  "message": "Successfully logged out."
}
```

---

#### Activate Account
```
GET /activate/<utoken>/<token>/
```
**Auth:** None

**Notes:** Link from verification email. Redirects to `{FRONTEND_URL}/login?activated=true` on success. Token expires after 24 hours.

---

#### Resend Activation Email
```
POST /resend-activation-email/
```
**Auth:** None

**Body:**
```json
{
  "email": "user@example.com"
}
```

---

#### Change Password
```
POST /change-password/
```
**Auth:** Required

**Body:**
```json
{
  "old_password": "OldPass123",
  "new_password": "NewPass456"
}
```
**Response (200):**
```json
{
  "message": "Password updated successfully",
  "token": "new_token_here"
}
```
**Notes:** Old token is invalidated. Use the new token for subsequent requests.

---

#### Reset Password (Request)
```
POST /reset-password/
```
**Auth:** None

**Body:**
```json
{
  "email": "user@example.com"
}
```

---

#### Reset Password (Confirm)
```
POST /reset-password-confirm/<utoken>/<token>/
```
**Auth:** None

**Body:**
```json
{
  "token": "<token_from_url>",
  "new_password": "NewPassword123"
}
```

---

#### Delete Account (Soft Delete)
```
DELETE /delete-account/
```
**Auth:** Required

**Body:**
```json
{
  "password": "YourPassword123"
}
```
**Response (200):**
```json
{
  "status": "success",
  "message": "Your account has been deleted and personal data anonymized"
}
```
**Notes:** Does NOT permanently delete. Deactivates account, anonymizes personal data (email, name, phone, address), preserves all booking/invoice/transaction records. Creates an `AccountDeletionLog` audit record before anonymizing.

---

### Profile & Account

#### Get Profile
```
GET /profile/
```
**Auth:** Required

**Response (200):**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe"
  },
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "marital_status": "single",
  "profession": "Engineer",
  "image": "/media/profile/images/photo.jpg",
  "status": "active",
  "gender": "male"
}
```

---

#### Update Profile
```
POST /profile/   (partial update)
PUT  /profile/   (full update)
```
**Auth:** Required

**Body (JSON):**
```json
{
  "address": "456 Oak Ave",
  "city": "Los Angeles",
  "state": "CA",
  "country": "USA",
  "phone": "+1987654321",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "profession": "Designer"
}
```

---

#### Upload Profile Image
```
POST /profile/image/
```
**Auth:** Required

**Content-Type:** `multipart/form-data`

**Body:** `image` file field

---

#### Update Display Picture (Alternative)
```
POST /update_display_picture/
```
**Auth:** Required

**Content-Type:** `multipart/form-data`

**Body:** `file` file field

**Response (200):**
```json
{
  "image_url": "/media/profile/images/new_photo.jpg"
}
```

---

#### Account Settings
```
GET /account-settings/
```
**Auth:** Required

**Response:** Returns profile + booking history combined.
```json
{
  "profile": { "...CustomerProfile fields..." },
  "booking_histories": [ "...array of Booking objects..." ]
}
```

---

#### Personal Booking Profile
```
GET /personal-booking/
```
**Auth:** Required

**Returns:** Customer profile data.

---

#### Booking History
```
GET /booking-history/
```
**Auth:** Required

**Returns:** Array of all user's bookings.

---

### Packages & Browsing

#### Homepage
```
GET /index/
```
**Auth:** Optional (affects `is_saved` field)

**Response (200):**
```json
{
  "packages": [ "...active packages..." ],
  "destinations": [ "...active destinations..." ],
  "events": [ "...active events..." ]
}
```

---

#### List Packages (with Filtering & Sorting)
```
GET /packages/
```
**Auth:** Optional

**Query Parameters:**

| Parameter      | Type    | Description                                              |
|---------------|---------|----------------------------------------------------------|
| `search`      | string  | Keyword search on name and description                   |
| `continent`   | string  | Filter by continent (e.g., "Europe", "Africa")           |
| `country`     | string  | Filter by country                                        |
| `category`    | string  | Filter by category (e.g., "tourism", "hotel")            |
| `min_price`   | decimal | Minimum price                                            |
| `max_price`   | decimal | Maximum price                                            |
| `min_duration`| integer | Minimum duration in days                                 |
| `max_duration`| integer | Maximum duration in days                                 |
| `sort_by`     | string  | Sort: `price`, `-price`, `duration`, `-duration`, `name`, `-name`, `newest` |

**Example:**
```
GET /packages/?continent=Europe&min_price=100&max_price=5000&sort_by=-price
```

**Response:** Array of package objects, each with an `is_saved` boolean.

---

#### Package Details
```
GET /packages/<package_id>/
```
**Auth:** Optional

**Response (200):**
```json
{
  "package": {
    "id": 1,
    "package_id": "PKG001",
    "name": "Paris Getaway",
    "category": "tourism",
    "vat": 5.00,
    "price_option": "fixed",
    "fixed_price": 2500.00,
    "discount_price": null,
    "max_adult_limit": 4,
    "max_child_limit": 2,
    "date_from": "2026-06-01",
    "date_to": "2026-06-10",
    "duration": 10,
    "availability": 20,
    "country": "France",
    "continent": "Europe",
    "description": "A beautiful trip to Paris...",
    "main_image": "/media/package/main_images/paris.jpg",
    "destinations": "Eiffel Tower, Louvre, Versailles",
    "services": "Hotel, Transport, Meals",
    "featured_events": "Seine River Cruise",
    "featured_guests": "",
    "status": "active",
    "package_images": [],
    "is_saved": false
  },
  "package_images": [],
  "guest_images": []
}
```

---

#### Check Offer / Dynamic Pricing
```
GET /check-offer/<package_id>/?adult=2&children=1
```
**Auth:** Required

**Response (200):**
```json
{
  "adult": 2,
  "children": 1,
  "price": 3500
}
```
**Notes:** Only for packages with `price_option != "fixed"`. Returns matching tier from the `discount_price` field.

---

### Bookings

#### Create Booking
```
POST /book-package/<package_id>/
```
**Auth:** Required

**Body:**
```json
{
  "purpose": "tourism",
  "datefrom": "2026-07-01",
  "dateto": "2026-07-10",
  "continent": "Europe",
  "travelcountry": "France",
  "travelstate": "Ile-de-France",
  "destinations": "Paris, Versailles",
  "guests": 3,
  "duration": 10,
  "adult": 2,
  "children": 1,
  "service": "Hotel, Transport",
  "price": 2500.00,
  "lastname": "Doe",
  "firstname": "John",
  "profession": "Engineer",
  "email": "john@example.com",
  "phone": "+1234567890",
  "gender": "male",
  "country": "USA",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "comment": "Anniversary trip"
}
```
**Response (201):**
```json
{
  "message": "Booking successful"
}
```
**Notes:** Generates a unique `booking_id` (e.g., `BKN1A2B3C`). Status starts as `pending`.

---

#### List/Detail Bookings (ViewSet)
```
GET    /bookings/                       -- List all user's bookings
GET    /bookings/<booking_id>/          -- Single booking detail
PUT    /bookings/<booking_id>/          -- Update booking
DELETE /bookings/<booking_id>/          -- Delete booking
```
**Auth:** Required. Staff sees all bookings; regular users see only their own.

**Lookup field:** `booking_id`

---

#### Cruise Bookings (ViewSet)
```
GET    /cruise-bookings/
POST   /cruise-bookings/
GET    /cruise-bookings/<booking_id>/
PUT    /cruise-bookings/<booking_id>/
DELETE /cruise-bookings/<booking_id>/
```
**Auth:** Required. Same as BookingViewSet but for cruise-type bookings.

---

#### Cancel Booking
```
POST /bookings/<booking_id>/cancel/
```
**Auth:** Required

**Body:**
```json
{
  "reason": "Change of plans"
}
```
**Response (200):**
```json
{
  "status": "success",
  "message": "Booking cancelled",
  "booking_id": "BKN1A2B3C",
  "refund_amount": "2500.00",
  "refund_status": "processed"
}
```
**Cancellation Refund Policy:**

| Time Before Travel | Refund |
|-------------------|--------|
| 7+ days           | 100%   |
| 3-7 days          | 50%    |
| < 3 days          | 0%     |

**Status requirements:** Only `pending`, `paid`, or `invoiced` bookings can be cancelled.

**Side effects:** Refund deposited to wallet, notification + email sent.

---

#### Modify Booking
```
POST /bookings/<booking_id>/modify/
```
**Auth:** Required

**Body (all fields optional):**
```json
{
  "datefrom": "2026-08-01",
  "dateto": "2026-08-12",
  "adult": 3,
  "children": 0,
  "guests": 3
}
```
**Response (200):**
```json
{
  "status": "success",
  "message": "Booking updated",
  "booking": { "...full booking object..." }
}
```
**Notes:** Only `pending` bookings can be modified. Price auto-recalculates if guest counts change.

---

### Payments

#### Pay Booking (Initiate Payment)
```
GET /booking-payment/<booking_id>/<mode>/
```
**Auth:** Required

**Modes:**

| Mode     | Description                                       |
|----------|--------------------------------------------------|
| `wallet` | Full payment from wallet balance                  |
| `stripe` | Full payment via Stripe Checkout redirect         |
| `split`  | Wallet balance deducted first, remainder via Stripe |

**Response for `wallet` mode (200):**
```json
{
  "status": "success",
  "booking_id": "BKN1A2B3C",
  "mode": "wallet"
}
```

**Response for `stripe` mode (200):**
```json
{
  "status": "success",
  "checkout_url": "https://checkout.stripe.com/pay/...",
  "session_id": "cs_live_...",
  "mode": "stripe",
  "booking_id": "BKN1A2B3C"
}
```

**Response for `split` mode (200):**
```json
{
  "status": "success",
  "checkout_url": "https://checkout.stripe.com/pay/...",
  "session_id": "cs_live_...",
  "mode": "split",
  "wallet_amount": "500.00",
  "stripe_amount": "2000.00",
  "booking_id": "BKN1A2B3C"
}
```

---

#### Confirm Booking Payment
```
POST /booking-confirm/
```
**Auth:** Required

**Body:**
```json
{
  "identifier": "<booking_id or session_id>",
  "mode": "wallet|stripe|split"
}
```

| Mode     | `identifier` value          |
|----------|-----------------------------|
| `wallet` | The `booking_id`            |
| `stripe` | The Stripe `session_id`     |
| `split`  | The `booking_id`            |

**Response (200):**
```json
{
  "status": "success",
  "booking_id": "BKN1A2B3C",
  "mode": "wallet"
}
```
**Side effects:** Creates invoice, records payment, sends invoice email with PDF, creates notifications (payment_received + booking_confirmed).

---

#### Booking Complete (Stripe redirect callback)
```
GET /bookings/complete/<booking_id>/
```
**Auth:** Required

**Notes:** Alternative endpoint for Stripe redirect. Verifies the checkout session and processes the invoice pipeline. Used when the frontend redirects from Stripe success URL.

---

#### Preview Invoice
```
GET /preview-invoice/<invoice_id>/
```
**Auth:** Required

**Response:** Full invoice object with all fields.

---

#### Make Payment (Direct invoice payment)
```
POST /make-payment/<invoice_id>/
```
**Auth:** Required

**Response (200):**
```json
{
  "status": "success",
  "message": "Payment successful"
}
```
**Notes:** Returns 409 if invoice already paid.

---

### Invoices

#### Download Invoice PDF
```
GET /invoices/<invoice_id>/download/
```
**Auth:** Required (must own the invoice)

**Response (200):**
```json
{
  "status": "success",
  "invoice_id": "INV-000001",
  "download_url": "https://media.leisuretimez.com/customer/invoices/BKN1A2B3C.pdf"
}
```
**Notes:** Regenerates PDF if file is missing on server.

---

### Reviews

#### List Package Reviews
```
GET /packages/<package_id>/reviews/
```
**Auth:** None

**Response (200):**
```json
{
  "reviews": [
    {
      "id": 1,
      "user_email": "john@example.com",
      "user_name": "John Doe",
      "package": 1,
      "rating": 5,
      "comment": "Amazing experience!",
      "created_at": "2026-01-15T10:30:00Z",
      "updated_at": "2026-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "average_rating": 5.0
}
```

---

#### Create Review
```
POST /packages/<package_id>/reviews/
```
**Auth:** Required

**Body:**
```json
{
  "rating": 5,
  "comment": "Amazing experience!"
}
```
**Validation:** User must have a `paid` booking for this package. One review per package per user.

**Response (201):**
```json
{
  "status": "success",
  "review": { "...review object..." }
}
```

---

#### Update Review
```
PUT /reviews/<review_id>/
```
**Auth:** Required (must be review author)

**Body:**
```json
{
  "rating": 4,
  "comment": "Updated review"
}
```

---

#### Delete Review
```
DELETE /reviews/<review_id>/
```
**Auth:** Required (must be review author)

**Response (200):**
```json
{
  "status": "success",
  "message": "Review deleted"
}
```

---

### Promo Codes

#### Apply Promo Code
```
POST /bookings/<booking_id>/apply-promo/
```
**Auth:** Required

**Body:**
```json
{
  "code": "SUMMER25"
}
```
**Response (200):**
```json
{
  "status": "success",
  "message": "Promo code applied. You save 625.00!",
  "original_price": "2500.00",
  "discount": "625.00",
  "new_price": "1875.00"
}
```
**Validation:** Booking must be `pending`. Code must be active, within date range, under usage limit. Minimum order amount must be met.

---

#### Remove Promo Code
```
POST /bookings/<booking_id>/remove-promo/
```
**Auth:** Required

**Response (200):**
```json
{
  "status": "success",
  "message": "Promo code removed",
  "price": "2500.00"
}
```

---

### Wallet

#### Create Wallet
```
POST /wallets/
```
**Auth:** Required

**Response (201):** Wallet object. One wallet per user.

---

#### Get Wallet
```
GET /wallets/
```
**Auth:** Required

**Response:** Array with user's wallet (typically 1 item).

---

#### Deposit (via Stripe Checkout)
```
POST /wallets/deposit/
```
**Auth:** Required

**Body:**
```json
{
  "amount": 500.00,
  "success_url": "https://www.leisuretimez.com/wallet/success",
  "cancel_url": "https://www.leisuretimez.com/wallet/cancel"
}
```
**Response (200):**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/...",
  "session_id": "cs_live_...",
  "transaction_id": "uuid-here"
}
```

---

#### Deposit (via Payment Method ID)
```
POST /wallets/deposit/
```
**Body:**
```json
{
  "amount": 500.00,
  "payment_method_id": "pm_card_visa"
}
```

---

#### Withdraw
```
POST /wallets/<wallet_id>/withdraw/
```
**Auth:** Required

**Body:**
```json
{
  "amount": 100.00
}
```
**Response (200):**
```json
{
  "detail": "Withdrawal successful",
  "transaction": { "...transaction object..." }
}
```

---

#### Transfer
```
POST /wallets/<wallet_id>/transfer/
```
**Auth:** Required

**Body:**
```json
{
  "recipient_id": "uuid-of-recipient-wallet",
  "amount": 50.00
}
```

---

#### Wallet Transactions
```
GET /wallets/<wallet_id>/transactions/?type=deposit
```
**Auth:** Required

**Query params:** `type` (optional) - filter by `deposit`, `withdrawal`, `transfer`

---

#### Wallet + Transactions (Combined)
```
GET /transactions/wallettransactions/
```
**Auth:** Required

**Response (200):**
```json
{
  "wallet": {
    "id": "uuid",
    "balance": "1500.00",
    "updated_at": "2026-01-15T10:30:00Z",
    "is_active": true
  },
  "transactions": []
}
```

---

#### Transaction History
```
GET /transactions/
```
**Auth:** Required

**Returns:** All completed/failed transactions for the user.

---

#### Verify Stripe Payment
```
GET /verify-payment/<session_id>/
```
**Auth:** Required

**Response (200):**
```json
{
  "payment_successful": true,
  "session_id": "cs_live_...",
  "customer_email": "user@example.com",
  "amount_total": 50000,
  "currency": "usd"
}
```

---

### Notifications

#### List Notifications
```
GET /notifications/
```
**Auth:** Required

**Response:** Array of notification objects (newest first).
```json
[
  {
    "id": 1,
    "notification_type": "booking_confirmed",
    "title": "Booking Confirmed",
    "message": "Your booking BKN1A2B3C has been confirmed...",
    "is_read": false,
    "booking": 5,
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

**Notification Types:**

| Type                | Trigger                       |
|--------------------|-------------------------------|
| `booking_confirmed` | Payment confirmed             |
| `payment_received`  | Payment processed             |
| `booking_cancelled` | Booking cancelled             |
| `refund_processed`  | Refund credited to wallet     |
| `trip_reminder`     | Upcoming trip reminder        |
| `promo`            | Promotional notification      |
| `system`           | System announcements          |

---

#### Get Single Notification
```
GET /notifications/<id>/
```
**Auth:** Required

---

#### Get Unread Count
```
GET /notifications/unread_count/
```
**Auth:** Required

**Response:**
```json
{
  "unread_count": 3
}
```

---

#### Mark Single as Read
```
POST /notifications/<id>/read/
```
**Auth:** Required

---

#### Mark All as Read
```
POST /notifications/mark-all-read/
```
**Auth:** Required

**Response:**
```json
{
  "status": "success",
  "message": "5 notifications marked as read"
}
```

---

### Support Tickets

#### Create Ticket
```
POST /support/
```
**Auth:** Required

**Body:**
```json
{
  "subject": "Payment issue with booking BKN1A2B3C",
  "priority": "high",
  "message": "I was charged twice for my booking..."
}
```
**Priority options:** `low`, `medium` (default), `high`

**Response (201):** Full ticket object with initial message.

---

#### List Tickets
```
GET /support/
```
**Auth:** Required

**Response:** Array of user's support tickets.

---

#### View Ticket Detail
```
GET /support/<id>/
```
**Auth:** Required

**Response:**
```json
{
  "id": 1,
  "subject": "Payment issue",
  "status": "open",
  "priority": "high",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T11:00:00Z",
  "messages": [
    {
      "id": 1,
      "sender_email": "user@example.com",
      "message": "I was charged twice...",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ]
}
```

---

#### Reply to Ticket
```
POST /support/<id>/reply/
```
**Auth:** Required

**Body:**
```json
{
  "message": "Here is my transaction ID: TXN123..."
}
```
**Notes:** Cannot reply to closed tickets.

---

#### Close Ticket
```
POST /support/<id>/close/
```
**Auth:** Required

---

### Saved Packages

#### Save a Package
```
POST /packages/save/<package_id>/
```
**Auth:** Required

**Response (200):** `{"message": "Package \"Paris Getaway\" saved successfully"}`

**Returns 208** if already saved.

---

#### Unsave a Package
```
POST /packages/unsave/<package_id>/
```
**Auth:** Required

---

#### View Saved Packages
```
GET /saved-packages/
```
**Auth:** Required

**Response:** Array of saved package objects.

---

### Search

#### Search Locations
```
GET /search-locations/?country=France&state=Paris&type=hotel
```
**Auth:** None

**Query params:** `country`, `state` (multiple allowed), `type`

---

#### Search Countries & Locations
```
GET /search-countries-locations/?country=FR&places=hotel,restaurant
```
**Auth:** None

**Response (200):**
```json
{
  "locations": [
    {"title": "Hotel Le Marais", "state": "Ile-de-France"}
  ]
}
```

---

### Events

#### List Events
```
GET /events/?country=France
```
**Auth:** None

**Query params:** `country` (optional)

**Response:** Array of event objects with nested images.

#### Event Detail
```
GET /events/<id>/
```

---

### Contact

#### Submit Contact Form
```
POST /contact/
```
**Auth:** None

**Body:**
```json
{
  "fullname": "Jane Smith",
  "subject": "Partnership inquiry",
  "email": "jane@example.com",
  "message": "I'd like to discuss a partnership..."
}
```
**Side effects:** Sends notification emails to both admin and the submitter.

---

### Webhooks

#### Stripe Webhook (Server-side only)
```
POST /paynotifier/
```
**Auth:** Stripe signature verification

**Handled events:**
- `payment_intent.succeeded` - Credits wallet for deposits
- `payment_intent.payment_failed` - Marks transaction as failed
- `checkout.session.completed` - Credits wallet for checkout deposits
- `checkout.session.expired` - Refunds wallet for expired split payments

**Note:** This endpoint is not called by the frontend. Stripe sends events to it directly.

---

## Data Models

### User (CustomUser)
| Field          | Type     | Notes                        |
|---------------|----------|------------------------------|
| id            | integer  | Auto-generated PK            |
| email         | string   | Unique, used as username     |
| firstname     | string   |                              |
| lastname      | string   |                              |
| is_active     | boolean  | False until email verified   |
| date_joined   | datetime | Auto-set                     |
| saved_packages| M2M      | Packages saved by user       |

### CustomerProfile
| Field          | Type     | Notes                        |
|---------------|----------|------------------------------|
| user          | FK       | OneToOne to CustomUser       |
| address       | string   | Optional                     |
| city          | string   | Optional                     |
| state         | string   | Optional                     |
| country       | string   | Optional                     |
| phone         | string   | Optional                     |
| date_of_birth | date     | Optional                     |
| marital_status| string   | Optional                     |
| profession    | string   | Optional                     |
| image         | file     | Profile picture              |
| gender        | string   | male/female                  |
| status        | string   | active/deleted               |

### Package
| Field          | Type     | Notes                              |
|---------------|----------|------------------------------------|
| package_id    | string   | Unique identifier                  |
| name          | string   |                                    |
| category      | string   | tourism, hotel, etc.               |
| vat           | decimal  | Tax percentage                     |
| price_option  | string   | "fixed" or "dynamic"               |
| fixed_price   | decimal  | For fixed pricing                  |
| discount_price| text     | Tiered pricing (format: "adult,children,price-...") |
| date_from     | date     | Package start date                 |
| date_to       | date     | Package end date                   |
| duration      | integer  | Days                               |
| availability  | integer  | Spots remaining                    |
| country       | string   |                                    |
| continent     | string   |                                    |
| main_image    | file     |                                    |
| destinations  | text     | Comma-separated                    |
| services      | text     | Comma-separated                    |

### Booking
| Field              | Type     | Notes                              |
|-------------------|----------|------------------------------------|
| booking_id        | string   | Unique (e.g., "BKN1A2B3C")        |
| package           | string   | package_id reference               |
| customer          | FK       | CustomerProfile                    |
| status            | string   | pending/invoiced/paid/cancelled    |
| price             | decimal  | After discounts                    |
| payment_method    | string   | wallet/stripe/split                |
| wallet_amount_paid| decimal  | Amount from wallet                 |
| stripe_amount_due | decimal  | Amount via Stripe                  |
| cancelled_at      | datetime | When cancelled                     |
| cancellation_reason| text    | User-provided reason               |
| refund_amount     | decimal  | Amount refunded                    |
| refund_status     | string   | pending/processed/denied           |
| promo_code        | FK       | Applied PromoCode                  |
| discount_amount   | decimal  | Discount from promo code           |
| datefrom          | date     | Travel start date                  |
| dateto            | date     | Travel end date                    |
| adult             | integer  | Number of adults                   |
| children          | integer  | Number of children                 |
| guests            | integer  | Total guests                       |

### Invoice
| Field      | Type    | Notes                          |
|-----------|---------|--------------------------------|
| invoice_id| string  | Unique (e.g., "INV-000001")    |
| booking   | FK      | Related booking                |
| items     | text    | JSON string of line items      |
| subtotal  | decimal |                                |
| tax       | decimal | VAT percentage                 |
| tax_amount| decimal | Computed tax                   |
| admin_fee | decimal | Service charge                 |
| total     | decimal | Grand total                    |
| paid      | boolean |                                |
| transaction_id| string | Payment transaction ID      |

### Wallet
| Field              | Type    | Notes                   |
|-------------------|---------|-------------------------|
| id                | UUID    | Primary key             |
| user              | FK      | One per user            |
| balance           | decimal | Current balance         |
| stripe_customer_id| string  | Stripe customer ID      |
| is_active         | boolean | False after account deletion |

### Transaction
| Field                    | Type    | Notes                     |
|-------------------------|---------|---------------------------|
| id                      | UUID    |                           |
| wallet                  | FK      |                           |
| amount                  | decimal |                           |
| transaction_type        | string  | deposit/withdrawal/transfer|
| status                  | string  | pending/completed/failed  |
| stripe_payment_intent_id| string  |                           |
| reference               | string  | e.g., booking_id          |
| description             | string  |                           |

### PromoCode
| Field            | Type    | Notes                          |
|-----------------|---------|--------------------------------|
| code            | string  | Unique, case-insensitive match |
| discount_type   | string  | percentage/fixed               |
| discount_value  | decimal | % value or fixed amount        |
| min_order_amount| decimal | Minimum order to qualify       |
| max_uses        | integer | 0 = unlimited                  |
| current_uses    | integer | Tracks usage count             |
| valid_from      | datetime| Start of validity              |
| valid_to        | datetime| End of validity                |
| is_active       | boolean |                                |

### Review
| Field   | Type    | Notes                          |
|--------|---------|--------------------------------|
| user   | FK      | Reviewer                       |
| package| FK      |                                |
| rating | integer | 1-5 (validated)                |
| comment| text    | Optional                       |

**Constraint:** One review per user per package (`unique_together`).

### Notification
| Field             | Type    | Notes                      |
|------------------|---------|----------------------------|
| user             | FK      |                            |
| notification_type| string  | See types table above      |
| title            | string  |                            |
| message          | text    |                            |
| is_read          | boolean | Default false              |
| booking          | FK      | Optional relation          |

### SupportTicket
| Field    | Type   | Notes                              |
|---------|--------|------------------------------------|
| user    | FK     |                                    |
| subject | string |                                    |
| status  | string | open/in_progress/resolved/closed   |
| priority| string | low/medium/high                    |

### SupportMessage
| Field   | Type | Notes            |
|--------|------|------------------|
| ticket | FK   | Parent ticket    |
| sender | FK   | User who sent it |
| message| text |                  |

### AccountDeletionLog (Internal audit only)
| Field                    | Type    | Notes                              |
|-------------------------|---------|--------------------------------------|
| user_id                 | integer | Original PK of deleted user          |
| email                   | string  | Original email before anonymization  |
| firstname               | string  | Original name                        |
| lastname                | string  | Original name                        |
| phone                   | string  | Original phone                       |
| date_joined             | datetime| Original registration date           |
| deleted_at              | datetime| When the deletion occurred           |
| reason                  | text    | Deletion reason                      |
| wallet_balance_at_deletion| decimal| Balance at time of deletion         |

---

## Status Codes & Error Handling

### Standard Response Format
**Success:**
```json
{
  "status": "success",
  "message": "Human-readable message"
}
```

**Error:**
```json
{
  "status": "error",
  "message": "What went wrong"
}
```

### Common HTTP Status Codes
| Code | Meaning                                          |
|------|--------------------------------------------------|
| 200  | Success                                          |
| 201  | Created (new resource)                           |
| 400  | Bad request / validation error                   |
| 401  | Not authenticated                                |
| 403  | Forbidden (not authorized to access resource)    |
| 404  | Resource not found                               |
| 208  | Already reported (e.g., package already saved)   |
| 409  | Conflict (duplicate action, already paid, etc.)  |
| 500  | Server error                                     |

---

## Booking Status State Machine

```
                    +-----------+
                    |  pending  |
                    +-----+-----+
                          |
            +-------------+-------------+
            |             |             |
      (pay wallet)  (pay stripe)  (cancel)
            |             |             |
            v             v             v
       +--------+   +---------+   +-----------+
       |  paid  |   |invoiced |   | cancelled |
       +--------+   +----+----+   +-----------+
                          |
                    (payment confirmed)
                          |
                          v
                     +--------+
                     |  paid  |
                     +--------+
```

**Valid transitions:**
- `pending` -> `invoiced` (invoice created)
- `pending` -> `paid` (wallet payment)
- `pending` -> `cancelled` (user cancels)
- `invoiced` -> `paid` (payment confirmed)
- `paid` -> `cancelled` (user cancels, refund policy applies)
- `invoiced` -> `cancelled` (user cancels, refund policy applies)
