"""
URL configuration for the Admin API.

All endpoints require IsAdminStaff permission (is_staff=True).
Prefix: /admin-api/v1/
"""

from django.urls import path

from .views import (
    # Dashboard
    dashboard,
    # Users
    users,
    # Bookings
    bookings,
    # Personalised Bookings
    personalised_bookings,
    # Quotations
    quotations,
    # Invoices
    invoices,
    # Payments
    payments,
    # Support
    support,
    # Content
    content,
    # Lookups
    lookups,
    # Notifications
    notifications,
    # Contacts
    contacts,
    # Security
    security,
)

app_name = 'admin_api'

urlpatterns = [
    # -----------------------------------------------------------------------
    # Dashboard
    # -----------------------------------------------------------------------
    path('dashboard/', dashboard.AdminDashboardView.as_view(), name='dashboard'),

    # -----------------------------------------------------------------------
    # User Management
    # -----------------------------------------------------------------------
    path('users/', users.AdminUserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', users.AdminUserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/activate/', users.AdminUserActivateView.as_view(), name='user-activate'),
    path('users/<int:pk>/deactivate/', users.AdminUserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<int:pk>/bookings/', users.AdminUserBookingsView.as_view(), name='user-bookings'),
    path('users/<int:pk>/personalised-bookings/', users.AdminUserPersonalisedBookingsView.as_view(), name='user-personalised-bookings'),
    path('users/<int:pk>/transactions/', users.AdminUserTransactionsView.as_view(), name='user-transactions'),

    # -----------------------------------------------------------------------
    # Booking Management (legacy)
    # -----------------------------------------------------------------------
    path('bookings/', bookings.AdminBookingListView.as_view(), name='booking-list'),
    path('bookings/<str:booking_id>/', bookings.AdminBookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<str:booking_id>/cancel/', bookings.AdminBookingCancelView.as_view(), name='booking-cancel'),
    path('bookings/<str:booking_id>/activity/', bookings.AdminBookingActivityView.as_view(), name='booking-activity'),

    # -----------------------------------------------------------------------
    # Personalised Booking Management
    # -----------------------------------------------------------------------
    path('personalised-bookings/', personalised_bookings.AdminPBListView.as_view(), name='pb-list'),
    path('personalised-bookings/<int:pk>/', personalised_bookings.AdminPBDetailView.as_view(), name='pb-detail'),
    path('personalised-bookings/<int:pk>/transition/', personalised_bookings.AdminPBTransitionView.as_view(), name='pb-transition'),
    path('personalised-bookings/<int:pk>/assign/', personalised_bookings.AdminPBAssignView.as_view(), name='pb-assign'),
    path('personalised-bookings/<int:pk>/messages/', personalised_bookings.AdminPBMessagesView.as_view(), name='pb-messages'),
    path('personalised-bookings/<int:pk>/messages/create/', personalised_bookings.AdminPBMessageCreateView.as_view(), name='pb-message-create'),
    path('personalised-bookings/<int:pk>/activity/', personalised_bookings.AdminPBActivityView.as_view(), name='pb-activity'),

    # -----------------------------------------------------------------------
    # Quotation Management
    # -----------------------------------------------------------------------
    path('quotations/', quotations.AdminQuotationListView.as_view(), name='quotation-list'),
    path('quotations/create/', quotations.AdminQuotationCreateView.as_view(), name='quotation-create'),
    path('quotations/<int:pk>/', quotations.AdminQuotationDetailView.as_view(), name='quotation-detail'),
    path('quotations/<int:pk>/update/', quotations.AdminQuotationUpdateView.as_view(), name='quotation-update'),
    path('quotations/<int:pk>/send/', quotations.AdminQuotationSendView.as_view(), name='quotation-send'),
    path('quotations/<int:pk>/revise/', quotations.AdminQuotationReviseView.as_view(), name='quotation-revise'),

    # -----------------------------------------------------------------------
    # Invoice Management — Legacy (from Booking)
    # -----------------------------------------------------------------------
    path('invoices/legacy/', invoices.AdminLegacyInvoiceListView.as_view(), name='legacy-invoice-list'),
    path('invoices/legacy/<str:invoice_id>/', invoices.AdminLegacyInvoiceDetailView.as_view(), name='legacy-invoice-detail'),

    # -----------------------------------------------------------------------
    # Invoice Management — Personalised Booking
    # -----------------------------------------------------------------------
    path('invoices/', invoices.AdminPBInvoiceListView.as_view(), name='pb-invoice-list'),
    path('invoices/from-quotation/', invoices.AdminInvoiceFromQuotationView.as_view(), name='invoice-from-quotation'),
    path('invoices/<int:pk>/', invoices.AdminPBInvoiceDetailView.as_view(), name='pb-invoice-detail'),
    path('invoices/<int:pk>/adjust/', invoices.AdminPBInvoiceAdjustView.as_view(), name='pb-invoice-adjust'),
    path('invoices/<int:pk>/cancel/', invoices.AdminPBInvoiceCancelView.as_view(), name='pb-invoice-cancel'),
    path('invoices/<int:pk>/mark-paid/', invoices.AdminPBInvoiceMarkPaidView.as_view(), name='pb-invoice-mark-paid'),

    # -----------------------------------------------------------------------
    # Payment Management — Legacy
    # -----------------------------------------------------------------------
    path('payments/legacy/', payments.AdminLegacyPaymentListView.as_view(), name='legacy-payment-list'),
    path('payments/legacy/<int:pk>/', payments.AdminLegacyPaymentDetailView.as_view(), name='legacy-payment-detail'),

    # -----------------------------------------------------------------------
    # Payment Management — Personalised Booking
    # -----------------------------------------------------------------------
    path('payments/', payments.AdminPBPaymentListView.as_view(), name='pb-payment-list'),
    path('payments/record/', payments.AdminRecordPaymentView.as_view(), name='record-payment'),
    path('payments/<int:pk>/', payments.AdminPBPaymentDetailView.as_view(), name='pb-payment-detail'),

    # -----------------------------------------------------------------------
    # Payment Schedules
    # -----------------------------------------------------------------------
    path('payment-schedules/', payments.AdminPaymentScheduleListView.as_view(), name='payment-schedule-list'),
    path('payment-schedules/create/', payments.AdminPaymentScheduleCreateView.as_view(), name='payment-schedule-create'),
    path('payment-schedules/<int:pk>/', payments.AdminPaymentScheduleUpdateView.as_view(), name='payment-schedule-update'),

    # -----------------------------------------------------------------------
    # Support Tickets
    # -----------------------------------------------------------------------
    path('support-tickets/', support.AdminSupportTicketListView.as_view(), name='support-ticket-list'),
    path('support-tickets/<int:pk>/', support.AdminSupportTicketDetailView.as_view(), name='support-ticket-detail'),
    path('support-tickets/<int:pk>/reply/', support.AdminSupportReplyView.as_view(), name='support-ticket-reply'),
    path('support-tickets/<int:pk>/close/', support.AdminSupportCloseView.as_view(), name='support-ticket-close'),

    # -----------------------------------------------------------------------
    # Content — Packages
    # -----------------------------------------------------------------------
    path('packages/', content.AdminPackageListCreateView.as_view(), name='package-list'),
    path('packages/<int:pk>/', content.AdminPackageDetailView.as_view(), name='package-detail'),

    # -----------------------------------------------------------------------
    # Content — Destinations
    # -----------------------------------------------------------------------
    path('destinations/', content.AdminDestinationListCreateView.as_view(), name='destination-list'),
    path('destinations/<int:pk>/', content.AdminDestinationDetailView.as_view(), name='destination-detail'),

    # -----------------------------------------------------------------------
    # Content — Events
    # -----------------------------------------------------------------------
    path('events/', content.AdminEventListCreateView.as_view(), name='event-list'),
    path('events/<int:pk>/', content.AdminEventDetailView.as_view(), name='event-detail'),

    # -----------------------------------------------------------------------
    # Content — Carousel
    # -----------------------------------------------------------------------
    path('carousel/', content.AdminCarouselListCreateView.as_view(), name='carousel-list'),
    path('carousel/<int:pk>/', content.AdminCarouselDetailView.as_view(), name='carousel-detail'),

    # -----------------------------------------------------------------------
    # Content — Blog
    # -----------------------------------------------------------------------
    path('blog/', content.AdminBlogPostListCreateView.as_view(), name='blog-list'),
    path('blog/<int:pk>/', content.AdminBlogPostDetailView.as_view(), name='blog-detail'),

    # -----------------------------------------------------------------------
    # Content — Promo Codes
    # -----------------------------------------------------------------------
    path('promo-codes/', content.AdminPromoCodeListCreateView.as_view(), name='promo-code-list'),
    path('promo-codes/<int:pk>/', content.AdminPromoCodeDetailView.as_view(), name='promo-code-detail'),

    # -----------------------------------------------------------------------
    # Lookup Tables
    # -----------------------------------------------------------------------
    path('event-types/', lookups.AdminEventTypeListCreateView.as_view(), name='event-type-list'),
    path('event-types/<int:pk>/', lookups.AdminEventTypeDetailView.as_view(), name='event-type-detail'),
    path('cruise-types/', lookups.AdminCruiseTypeListCreateView.as_view(), name='cruise-type-list'),
    path('cruise-types/<int:pk>/', lookups.AdminCruiseTypeDetailView.as_view(), name='cruise-type-detail'),
    path('service-catalog/', lookups.AdminServiceCatalogListCreateView.as_view(), name='service-catalog-list'),
    path('service-catalog/<int:pk>/', lookups.AdminServiceCatalogDetailView.as_view(), name='service-catalog-detail'),

    # -----------------------------------------------------------------------
    # Notifications
    # -----------------------------------------------------------------------
    path('notifications/', notifications.AdminNotificationListView.as_view(), name='notification-list'),
    path('notifications/send/', notifications.AdminSendNotificationView.as_view(), name='notification-send'),

    # -----------------------------------------------------------------------
    # Contact Submissions
    # -----------------------------------------------------------------------
    path('contacts/', contacts.AdminContactListView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', contacts.AdminContactUpdateView.as_view(), name='contact-update'),

    # -----------------------------------------------------------------------
    # Security — Throttle / Rate-Limit Reset
    # -----------------------------------------------------------------------
    path('security/throttle-reset/', security.AdminThrottleResetView.as_view(), name='throttle-reset'),

    # -----------------------------------------------------------------------
    # Security — Activity Logs
    # -----------------------------------------------------------------------
    path('security/activity-logs/', security.AdminActivityLogListView.as_view(), name='activity-log-list'),
    path('security/users/<int:pk>/activity-logs/', security.AdminUserActivityLogView.as_view(), name='user-activity-logs'),

    # -----------------------------------------------------------------------
    # Security — Active Sessions
    # -----------------------------------------------------------------------
    path('security/sessions/', security.AdminActiveSessionListView.as_view(), name='session-list'),
    path('security/users/<int:pk>/sessions/', security.AdminUserSessionsView.as_view(), name='user-sessions'),
    path('security/sessions/revoke/', security.AdminRevokeSessionView.as_view(), name='session-revoke'),

    # -----------------------------------------------------------------------
    # Security — Dashboard / Alerts
    # -----------------------------------------------------------------------
    path('security/dashboard/', security.AdminSecurityDashboardView.as_view(), name='security-dashboard'),
]
