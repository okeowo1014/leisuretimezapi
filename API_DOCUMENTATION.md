# Leisuretimez API Documentation

REST API for the Leisuretimez travel and leisure booking platform. Built with Django REST Framework.

**Base URL:** `https://api.leisuretimez.com/`

## Authentication

All protected endpoints require Token authentication.

```
Authorization: Token <your-auth-token>
```

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Packages](#2-packages)
3. [Bookings](#3-bookings)
4. [Invoices & Payments](#4-invoices--payments)
5. [Profile & Account](#5-profile--account)
6. [Search](#6-search)
7. [Saved Packages](#7-saved-packages)
8. [Events](#8-events)
9. [Wallets & Transactions](#9-wallets--transactions)
10. [Contact](#10-contact)
11. [Webhooks](#11-webhooks)
12. [Data Models](#12-data-models)

---

## 1. Authentication

### Register

Create a new user account. Sends a verification email.

```
POST /auth/register/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address |
| firstname | string | Yes | First name |
| lastname | string | Yes | Last name |
| password | string | Yes | Account password |

**Response:** `201 Created`
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "firstname": "John",
    "lastname": "Doe"
  },
  "token": "abc123..."
}
```

### Login

Authenticate and receive an auth token.

```
POST /auth/login/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| password | string | Yes | User's password |

**Response:** `200 OK`
```json
{
  "token": "abc123...",
  "id": 1,
  "email": "user@example.com",
  "firstname": "John",
  "lastname": "Doe",
  "wallet": "100.00",
  "image": "/profile/images/avatar.jpg"
}
```

### Logout

Invalidate the current auth token.

```
POST /auth/logout/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out."
}
```

### Activate Account

Activate a user account via the emailed verification link.

```
GET /activate/<utoken>/<token>/
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| utoken | string | Base64-encoded user ID |
| token | string | Verification token |

**Response:** Redirects to frontend login page.

### Resend Activation Email

```
POST /resend-activation-email/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email address |

**Response:** `200 OK`
```json
{
  "message": "Activation email sent. Please check your inbox."
}
```

### Change Password

```
POST /change-password/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| old_password | string | Yes | Current password |
| new_password | string | Yes | New password |

**Response:** `200 OK`
```json
{
  "message": "Password updated successfully",
  "token": "new-token..."
}
```

### Reset Password (Request)

Send a password reset email.

```
POST /reset-password/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Account email address |

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent"
}
```

### Reset Password (Confirm)

Set a new password using the reset token.

```
POST /reset-password-confirm/<utoken>/<token>/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | Reset token |
| new_password | string | Yes | New password |

**Response:** `200 OK`
```json
{
  "message": "Password has been reset successfully"
}
```

---

## 2. Packages

### List All Packages

Get all active travel packages.

```
GET /packages/
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "package_id": "PKG001",
    "name": "Tropical Paradise",
    "category": "beach",
    "vat": "7.50",
    "price_option": "fixed",
    "fixed_price": "1500.00",
    "discount_price": null,
    "date_from": "2025-06-01",
    "date_to": "2025-06-15",
    "duration": 14,
    "availability": 50,
    "country": "Maldives",
    "continent": "Asia",
    "description": "...",
    "main_image": "/package/main_images/tropical.jpg",
    "destinations": "...",
    "services": "...",
    "status": "active",
    "is_saved": false,
    "package_images": [...]
  }
]
```

### Get Package Details

Get detailed information about a specific package.

```
GET /packages/<pid>/
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| pid | string | Package ID |

**Response:** `200 OK`
```json
{
  "package": { ... },
  "package_images": [...],
  "guest_images": [...]
}
```

### Homepage Data

Get homepage data including packages, destinations, and events.

```
GET /index/
```

**Response:** `200 OK`
```json
{
  "packages": [...],
  "destinations": [...],
  "events": [...]
}
```

### Check Offer

Check pricing offers for a package based on guest counts.

```
GET /check-offer/<pid>/?adult=2&children=1
```

**Auth required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| adult | integer | Number of adults |
| children | integer | Number of children |

**Response:** `200 OK`
```json
{
  "adult": 2,
  "children": 1,
  "price": 2500
}
```

---

## 3. Bookings

### Book a Package

Create a new booking for a specific package.

```
POST /book-package/<pid>/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| purpose | string | Yes | Purpose of trip |
| datefrom | date | Yes | Start date (YYYY-MM-DD) |
| dateto | date | Yes | End date (YYYY-MM-DD) |
| continent | string | Yes | Destination continent |
| travelcountry | string | Yes | Destination country |
| travelstate | string | Yes | Destination state/region |
| destinations | string | Yes | Specific destinations |
| duration | integer | Yes | Trip duration in days |
| adult | integer | Yes | Number of adults |
| children | integer | No | Number of children (default: 0) |
| service | string | Yes | Selected services |
| lastname | string | Yes | Guest last name |
| firstname | string | Yes | Guest first name |
| profession | string | Yes | Guest profession |
| email | string | Yes | Guest email |
| phone | string | Yes | Guest phone |
| country | string | Yes | Guest country |
| address | string | Yes | Guest address |
| city | string | Yes | Guest city |
| state | string | Yes | Guest state |

**Response:** `201 Created`
```json
{
  "message": "Booking successful"
}
```

### Booking History

Get the authenticated user's booking history.

```
GET /booking-history/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
[
  {
    "booking_id": "BKN1A2B3C",
    "package": "PKG001",
    "purpose": "tourism",
    "datefrom": "2025-06-01",
    "dateto": "2025-06-15",
    "status": "confirmed",
    ...
  }
]
```

### Pay for Booking

Process payment for a booking via wallet, Stripe checkout, or split (wallet + Stripe).

```
GET /booking-payment/<booking_id>/<mode>/
```

**Auth required:** Yes

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| booking_id | string | Booking ID |
| mode | string | Payment mode: `wallet`, `stripe`, or `split` |

**Mode details:**
| Mode | Description |
|------|-------------|
| `wallet` | Full payment deducted from wallet balance. Requires sufficient balance. |
| `stripe` | Full payment via Stripe Checkout. Creates a checkout session. |
| `split` | Deducts entire wallet balance first, charges the remainder via Stripe Checkout. If wallet covers the full amount, behaves like `wallet` mode. If wallet is empty, returns an error. |

**Response (wallet):** `200 OK`
```json
{
  "status": "successful",
  "booking_id": "BKN1A2B3C",
  "mode": "wallet"
}
```

**Response (stripe):** `200 OK`
```json
{
  "status": "successful",
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "mode": "checkout"
}
```

**Response (split):** `200 OK`
```json
{
  "status": "successful",
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "mode": "split",
  "wallet_amount": "200.00",
  "stripe_amount": "300.00",
  "booking_id": "BKN1A2B3C"
}
```

**Response (split — wallet covers full amount):** `200 OK`
```json
{
  "status": "successful",
  "booking_id": "BKN1A2B3C",
  "mode": "wallet",
  "message": "Wallet balance covered the full amount."
}
```

**Split payment flow:**
1. Client calls `/booking-payment/<booking_id>/split/`
2. API deducts wallet balance and creates a Stripe Checkout session for the remainder
3. Client redirects user to the `checkout_url` for Stripe payment
4. After Stripe payment succeeds, client calls `/booking-confirm/` with `mode: "split"` and `identifier: "<booking_id>"`
5. If the Stripe Checkout session expires without payment, the wallet amount is automatically refunded via webhook

### Confirm Booking

Confirm a booking after payment.

```
POST /booking-confirm/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier | string | Yes | Booking ID (for `wallet`/`split`) or Stripe session ID (for `stripe`) |
| mode | string | Yes | `wallet`, `stripe`, or `split` |

**Response:** `200 OK`
```json
{
  "status": "successful",
  "booking_id": "BKN1A2B3C",
  "mode": "split"
}
```

### Complete Booking

Handle booking completion after Stripe checkout.

```
GET /bookings/complete/<booking_id>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Payment processed successfully"
}
```

---

## 4. Invoices & Payments

### Preview Invoice

View an invoice by its ID.

```
GET /preview-invoice/<inv>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "invoice_id": "INV-000001",
  "booking": 1,
  "status": "paid",
  "items": "[...]",
  "subtotal": "1500.00",
  "tax": "7.50",
  "tax_amount": "112.50",
  "admin_percentage": "0.00",
  "admin_fee": "0.00",
  "total": "1612.50",
  "paid": true,
  "transaction_id": "TXN..."
}
```

### Make Payment

Record a payment for an invoice.

```
POST /make-payment/<inv>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Payment successful"
}
```

### Verify Stripe Payment

Verify the status of a Stripe checkout session.

```
GET /verify-payment/<session_id>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "payment_successful": true,
  "session_id": "cs_...",
  "customer_email": "user@example.com",
  "amount_total": 161250,
  "currency": "usd"
}
```

---

## 5. Profile & Account

### Get Profile

Retrieve the authenticated user's profile.

```
GET /profile/
```

**Auth required:** Yes

**Response:** `200 OK`
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
  "country": "US",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-15",
  "image": "/profile/images/avatar.jpg",
  "status": "active"
}
```

### Update Profile

Update profile fields (excluding image).

```
PUT /profile/
POST /profile/
PATCH /profile/
```

**Auth required:** Yes

**Request Body:** Any combination of profile fields (address, city, state, country, phone, date_of_birth, marital_status, profession, gender).

### Update Profile Image

Upload a new profile image.

```
POST /profile/image/
```

**Auth required:** Yes

**Request Body:** `multipart/form-data`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | file | Yes | Image file |

### Update Display Picture

Alternative endpoint for updating display picture.

```
POST /update_display_picture/
```

**Auth required:** Yes

**Request Body:** `multipart/form-data`
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Image file |

**Response:** `200 OK`
```json
{
  "image_url": "/profile/images/new-avatar.jpg"
}
```

### Account Settings

Get profile and booking history together.

```
GET /account-settings/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "profile": { ... },
  "booking_histories": [...]
}
```

---

## 6. Search

### Search Locations

Search locations by country, state, and type.

```
GET /search-locations/?country=US&state=California&type=beach
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| country | string | Yes | Country name |
| state | string[] | No | State/region name(s) |
| type | string | Yes | Location type |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "title": "Santa Monica Beach",
    "type": "beach",
    "city": "Santa Monica",
    "state": "California",
    "country": "United States"
  }
]
```

### Search Countries and Locations

Search locations by ISO country code and place types.

```
GET /search-countries-locations/?country=US&places=beach,mountain
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| country | string | Yes | ISO2 country code |
| places | string | Yes | Comma-separated place types |

**Response:** `200 OK`
```json
{
  "locations": [
    { "title": "Santa Monica Beach", "state": "California" },
    { "title": "Rocky Mountain Park", "state": "Colorado" }
  ]
}
```

---

## 7. Saved Packages

### Save Package

Add a package to the user's saved list.

```
POST /packages/save/<package_id>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Package \"Tropical Paradise\" saved successfully"
}
```

### Unsave Package

Remove a package from the user's saved list.

```
POST /packages/unsave/<package_id>/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Package \"Tropical Paradise\" unsaved successfully"
}
```

### View Saved Packages

Get all saved packages.

```
GET /saved-packages/
```

**Auth required:** Yes

**Response:** `200 OK` (array of package objects)

---

## 8. Events

### List Events

Get all active events (supports filtering by country).

```
GET /events/
GET /events/?country=Maldives
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| country | string | No | Filter by country |

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Beach Festival",
    "country": "Maldives",
    "continent": "Asia",
    "description": "...",
    "main_image": "/event/main_images/festival.jpg",
    "services": "...",
    "status": "active",
    "event_images": [...]
  }
]
```

### Get Event Details

```
GET /events/<id>/
```

---

## 9. Wallets & Transactions

### Create Wallet

Create a wallet for the authenticated user (one per user).

```
POST /wallets/
```

**Auth required:** Yes

**Response:** `201 Created`
```json
{
  "id": "uuid...",
  "user": { "id": 1, "email": "user@example.com" },
  "balance": "0.00",
  "created_at": "2025-01-15T10:30:00Z",
  "is_active": true
}
```

### Get Wallet

```
GET /wallets/
```

**Auth required:** Yes

### Deposit (Stripe Checkout)

Add funds to wallet via Stripe.

```
POST /wallets/deposit/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | decimal | Yes | Amount to deposit (min: 1.00) |
| success_url | URL | No | Redirect URL on success |
| cancel_url | URL | No | Redirect URL on cancel |
| payment_method_id | string | No | Stripe payment method ID (for direct charge) |

**Response (checkout):** `200 OK`
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_...",
  "transaction_id": "uuid..."
}
```

### Withdraw

Withdraw funds from wallet.

```
POST /wallets/<id>/withdraw/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| amount | decimal | Yes | Amount to withdraw (min: 1.00) |

**Response:** `200 OK`
```json
{
  "detail": "Withdrawal successful",
  "transaction": { ... }
}
```

### Transfer

Transfer funds to another user's wallet.

```
POST /wallets/<id>/transfer/
```

**Auth required:** Yes

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recipient_id | UUID | Yes | Recipient's wallet ID |
| amount | decimal | Yes | Amount to transfer (min: 1.00) |

**Response:** `200 OK`
```json
{
  "detail": "Transfer successful",
  "transaction": { ... }
}
```

### Transaction History

Get the user's transaction history.

```
GET /transactions/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
[
  {
    "id": "uuid...",
    "amount": "100.00",
    "transaction_type": "deposit",
    "status": "completed",
    "recipient": null,
    "description": null,
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

### Wallet and Transactions

Get wallet info and transactions together.

```
GET /transactions/wallettransactions/
```

**Auth required:** Yes

**Response:** `200 OK`
```json
{
  "wallet": {
    "id": "uuid...",
    "balance": "500.00",
    "is_active": true
  },
  "transactions": [...]
}
```

---

## 10. Contact

### Submit Contact Form

Send a contact form message.

```
POST /contact/
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fullname | string | Yes | Sender's full name |
| email | string | Yes | Sender's email |
| subject | string | Yes | Message subject |
| message | string | Yes | Message body |

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Your message has been sent successfully. We will contact you soon."
}
```

---

## 11. Webhooks

### Stripe Webhook

```
POST /paynotifier/
```

Handles the following Stripe events:
- `payment_intent.succeeded` - Marks transactions as completed, credits wallet
- `payment_intent.payment_failed` - Marks transactions as failed
- `checkout.session.completed` - Processes completed checkout sessions, credits wallet
- `checkout.session.expired` - Refunds wallet amount for expired split payment sessions

---

## 12. Data Models

### CustomUser

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Primary key |
| email | string | Unique email (used as username) |
| firstname | string | First name |
| lastname | string | Last name |
| is_active | boolean | Account activation status |
| is_staff | boolean | Admin status |
| date_joined | datetime | Registration date |
| saved_packages | M2M | Saved travel packages |

### CustomerProfile

| Field | Type | Description |
|-------|------|-------------|
| user | FK(CustomUser) | Linked user account |
| address | string | Street address |
| city | string | City |
| state | string | State/region |
| country | string | Country |
| phone | string | Phone number |
| date_of_birth | date | Date of birth |
| marital_status | string | Marital status |
| profession | string | Profession |
| image | image | Profile picture |
| gender | string | Gender (male/female) |

### Package

| Field | Type | Description |
|-------|------|-------------|
| package_id | string | Unique package identifier |
| name | string | Package name |
| category | string | Package category |
| vat | decimal | VAT percentage |
| price_option | string | `fixed` or `variable` |
| fixed_price | decimal | Fixed price (if applicable) |
| discount_price | text | Comma-separated pricing tiers |
| date_from | date | Start date |
| date_to | date | End date |
| duration | integer | Duration in days |
| availability | integer | Number of spots available |
| country | string | Destination country |
| continent | string | Destination continent |
| description | text | Package description |
| main_image | image | Primary image |

### Booking

| Field | Type | Description |
|-------|------|-------------|
| booking_id | string | Unique booking ID (BKN prefix) |
| package | string | Package ID |
| customer | FK(CustomerProfile) | Customer who booked |
| purpose | text | Trip purpose |
| datefrom / dateto | date | Travel dates |
| duration | integer | Days |
| adult / children | integer | Guest counts |
| price | decimal | Total price |
| status | string | pending / invoiced / paid / confirmed |
| payment_status | string | Payment status |
| payment_method | string | wallet / stripe / split |
| wallet_amount_paid | decimal | Amount paid from wallet (for split payments) |
| stripe_amount_due | decimal | Amount charged via Stripe (for split payments) |
| checkout_session_id | string | Stripe session ID |

### Invoice

| Field | Type | Description |
|-------|------|-------------|
| invoice_id | string | Unique invoice ID (INV- prefix) |
| booking | FK(Booking) | Associated booking |
| items | text | JSON-encoded line items |
| subtotal | decimal | Subtotal amount |
| tax / tax_amount | decimal | Tax rate and amount |
| admin_fee | decimal | Service charge |
| total | decimal | Grand total |
| paid | boolean | Payment status |

### Wallet

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user | FK(CustomUser) | Wallet owner |
| balance | decimal | Current balance |
| stripe_customer_id | string | Stripe customer ID |
| is_active | boolean | Active status |

### Transaction

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| wallet | FK(Wallet) | Associated wallet |
| amount | decimal | Transaction amount |
| transaction_type | string | deposit / withdrawal / transfer |
| status | string | pending / completed / failed |
| recipient | FK(CustomUser) | Transfer recipient (if applicable) |
| stripe_payment_intent_id | string | Stripe payment ID |

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Description of what went wrong"
}
```

**Common HTTP status codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 404 | Not Found |
| 409 | Conflict - Duplicate operation |
