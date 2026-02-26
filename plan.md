# Admin API Implementation Plan

## Architecture

New Django app: `admin_api/` with URL prefix `/admin-api/v1/`
- Every endpoint requires `IsAuthenticated` + `IsAdminUser` (is_staff=True)
- Separate serializers for admin read/write (more fields than customer-facing)
- Reuses existing models from `index/`

## Endpoints

### 1. Dashboard (`admin_api/views/dashboard.py`)
- `GET /admin-api/v1/dashboard/` — Aggregated stats:
  - Total users, new users (7d/30d)
  - Total bookings by status (pending/paid/cancelled)
  - Total personalised bookings by status
  - Revenue totals (paid bookings, wallet deposits)
  - Recent activity (last 10 BookingActivityLog entries)
  - Support tickets by status (open/in_progress)
  - Pending quotations count

### 2. User Management (`admin_api/views/users.py`)
- `GET /admin-api/v1/users/` — List all users (search by email/name, filter by is_active/is_staff/date range, paginated)
- `GET /admin-api/v1/users/<id>/` — User detail with profile, wallet balance, booking count, support ticket count
- `PATCH /admin-api/v1/users/<id>/` — Update user (is_active, is_staff, firstname, lastname)
- `POST /admin-api/v1/users/<id>/deactivate/` — Deactivate user account
- `POST /admin-api/v1/users/<id>/activate/` — Reactivate user account
- `GET /admin-api/v1/users/<id>/bookings/` — All bookings for a user
- `GET /admin-api/v1/users/<id>/personalised-bookings/` — All personalised bookings for a user
- `GET /admin-api/v1/users/<id>/transactions/` — Wallet transactions for a user

### 3. Booking Management (`admin_api/views/bookings.py`)
- `GET /admin-api/v1/bookings/` — List all bookings (filter by status/payment_status/date range/customer, search by booking_id/email)
- `GET /admin-api/v1/bookings/<booking_id>/` — Booking detail with customer, invoice, payment info
- `PATCH /admin-api/v1/bookings/<booking_id>/` — Update booking (status, payment_status, admin notes)
- `POST /admin-api/v1/bookings/<booking_id>/cancel/` — Admin cancel with refund options
- `POST /admin-api/v1/bookings/<booking_id>/refund/` — Process refund (amount, refund to wallet)
- `GET /admin-api/v1/bookings/<booking_id>/activity/` — Activity log for booking

### 4. Personalised Booking Management (`admin_api/views/personalised_bookings.py`)
- `GET /admin-api/v1/personalised-bookings/` — List all (filter by status/event_type/assigned_to/date range)
- `GET /admin-api/v1/personalised-bookings/<id>/` — Full detail with services, messages, attachments, quotations, invoices, activity log
- `PATCH /admin-api/v1/personalised-bookings/<id>/` — Update (status, assigned_to, admin_notes, quote_amount, rejection_reason)
- `POST /admin-api/v1/personalised-bookings/<id>/assign/` — Assign to staff member
- `POST /admin-api/v1/personalised-bookings/<id>/transition/` — Change status (uses allowed transitions)
- `GET /admin-api/v1/personalised-bookings/<id>/messages/` — All messages
- `POST /admin-api/v1/personalised-bookings/<id>/messages/` — Send message as admin
- `GET /admin-api/v1/personalised-bookings/<id>/activity/` — Activity log

### 5. Quotation Management (`admin_api/views/quotations.py`)
- `GET /admin-api/v1/quotations/` — List all quotations (filter by status/booking)
- `POST /admin-api/v1/quotations/` — Create quotation for a personalised booking (with line items)
- `GET /admin-api/v1/quotations/<id>/` — Quotation detail with line items
- `PATCH /admin-api/v1/quotations/<id>/` — Update draft quotation
- `POST /admin-api/v1/quotations/<id>/send/` — Send quotation to customer (status → sent)
- `POST /admin-api/v1/quotations/<id>/revise/` — Create new version (supersedes current)

### 6. Invoice Management (`admin_api/views/invoices.py`)
- `GET /admin-api/v1/invoices/` — List all invoices (legacy + personalised, filter by status/date range)
- `GET /admin-api/v1/invoices/<invoice_id>/` — Invoice detail
- `POST /admin-api/v1/invoices/from-quotation/` — Create invoice from accepted quotation
- `PATCH /admin-api/v1/invoices/<id>/` — Adjust invoice (amount, notes)
- `POST /admin-api/v1/invoices/<id>/cancel/` — Cancel invoice
- `POST /admin-api/v1/invoices/<id>/mark-paid/` — Manually mark as paid
- `GET /admin-api/v1/invoices/<id>/payments/` — List payments for invoice

### 7. Payment Management (`admin_api/views/payments.py`)
- `GET /admin-api/v1/payments/` — List all payments (filter by status/method/date range)
- `GET /admin-api/v1/payments/<id>/` — Payment detail
- `POST /admin-api/v1/payments/<id>/record/` — Manually record a payment (bank transfer, etc.)
- `GET /admin-api/v1/payment-schedules/` — List all payment schedules
- `POST /admin-api/v1/payment-schedules/` — Create payment schedule for a personalised booking
- `PATCH /admin-api/v1/payment-schedules/<id>/` — Update schedule milestone

### 8. Support Ticket Management (`admin_api/views/support.py`)
- `GET /admin-api/v1/support-tickets/` — List all tickets (filter by status/priority/assigned, search by subject/email)
- `GET /admin-api/v1/support-tickets/<id>/` — Ticket detail with all messages
- `PATCH /admin-api/v1/support-tickets/<id>/` — Update status/priority
- `POST /admin-api/v1/support-tickets/<id>/reply/` — Post admin reply
- `POST /admin-api/v1/support-tickets/<id>/close/` — Close ticket

### 9. Content Management (`admin_api/views/content.py`)
- Packages: full CRUD (`/admin-api/v1/packages/`)
- Destinations: full CRUD (`/admin-api/v1/destinations/`)
- Events: full CRUD (`/admin-api/v1/events/`)
- Carousel: full CRUD (`/admin-api/v1/carousel/`)
- Blog: full CRUD (`/admin-api/v1/blog/`)
- Promo Codes: full CRUD (`/admin-api/v1/promo-codes/`)

### 10. Lookup Table Management (`admin_api/views/lookups.py`)
- EventTypes: full CRUD (`/admin-api/v1/event-types/`)
- CruiseTypes: full CRUD (`/admin-api/v1/cruise-types/`)
- ServiceCatalog: full CRUD (`/admin-api/v1/service-catalog/`)

### 11. Notifications (`admin_api/views/notifications.py`)
- `POST /admin-api/v1/notifications/send/` — Send notification to user(s)
- `GET /admin-api/v1/notifications/` — List all notifications (filter by type/user)

### 12. Contact Submissions (`admin_api/views/contacts.py`)
- `GET /admin-api/v1/contacts/` — List contact submissions (filter by status)
- `PATCH /admin-api/v1/contacts/<id>/` — Update status (pending → resolved)

## File Structure

```
admin_api/
├── __init__.py
├── apps.py
├── permissions.py          # IsAdminStaff permission class
├── serializers/
│   ├── __init__.py
│   ├── users.py
│   ├── bookings.py
│   ├── personalised_bookings.py
│   ├── quotations.py
│   ├── invoices.py
│   ├── payments.py
│   ├── support.py
│   ├── content.py
│   ├── lookups.py
│   └── dashboard.py
├── views/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── users.py
│   ├── bookings.py
│   ├── personalised_bookings.py
│   ├── quotations.py
│   ├── invoices.py
│   ├── payments.py
│   ├── support.py
│   ├── content.py
│   ├── lookups.py
│   ├── notifications.py
│   └── contacts.py
├── urls.py
└── filters.py              # Shared django-filter FilterSets
```

## Implementation Order

1. App scaffold + permissions + urls wiring
2. Dashboard (quick wins, verifies setup)
3. User management (core admin need)
4. Booking management (legacy bookings)
5. Personalised booking management (with status transitions)
6. Quotation management
7. Invoice management
8. Payment management + schedules
9. Support ticket management
10. Content management (packages, destinations, events, carousel, blog, promo codes)
11. Lookup tables (event types, cruise types, service catalog)
12. Notifications + contacts
13. Postman tests for all admin endpoints
