"""
URL configuration for the index (main) app.

Routes API endpoints for authentication, packages, bookings,
invoices, wallets, events, profiles, and more.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from index import wallet_views
from index.utils import activate_account
from index.webhook import stripe_webhook

from .auth_views import (
    AuthViewSet, ChangePasswordView, ResendConfirmationView,
    ResetPasswordConfirmView, ResetPasswordView,
)
from .views import (
    BookPackageView, BookingViewSet, CheckOfferView, CruiseBookingViewSet,
    CustomerProfileDetailView, CustomerProfileImageUpdateView, EventViewSet,
    MakePaymentView, PreviewInvoiceView, SearchCountriesLocationsView,
    booking_complete, confirm_booking, contact_submit, index, package_details,
    package_list, pay_booking, personal_booking, booking_history,
    account_settings, save_package, search_locations,
    unsave_package, update_display_picture, view_saved_packages,
)

app_name = 'index'

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'events', EventViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'wallets', wallet_views.WalletViewSet, basename='wallet')
router.register(r'transactions', wallet_views.TransactionViewSet, basename='transaction')
router.register(r'cruise-bookings', CruiseBookingViewSet, basename='cruise_booking')

# ---------------------------------------------------------------------------
# URL patterns
# ---------------------------------------------------------------------------

urlpatterns = [
    # Router URLs (auth, events, bookings, wallets, transactions)
    path('', include(router.urls)),

    # Authentication
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('resend-activation-email/', ResendConfirmationView.as_view(), name='resend-activation'),
    path(
        'reset-password-confirm/<str:utoken>/<str:token>/',
        ResetPasswordConfirmView.as_view(),
        name='reset-password-confirm',
    ),
    path('activate/<str:utoken>/<str:token>/', activate_account, name='activate-account'),

    # Homepage & Packages
    path('index/', index, name='api-index'),
    path('packages/', package_list, name='api-packages'),
    path('packages/<str:pid>/', package_details, name='api-package-details'),

    # Profile & Account
    path('personal-booking/', personal_booking, name='api-personal-booking'),
    path('booking-history/', booking_history, name='api-booking-history'),
    path('account-settings/', account_settings, name='api-account-settings'),
    path('profile/', CustomerProfileDetailView.as_view(), name='customer-profile'),
    path('profile/image/', CustomerProfileImageUpdateView.as_view(), name='profile-image-update'),
    path('update_display_picture/', update_display_picture, name='update-display-picture'),

    # Search
    path('search-locations/', search_locations, name='api-search-locations'),
    path('search-countries-locations/', SearchCountriesLocationsView.as_view(), name='search-countries-locations'),

    # Bookings & Payments
    path('book-package/<str:pid>/', BookPackageView.as_view(), name='book-package'),
    path('preview-invoice/<str:inv>/', PreviewInvoiceView.as_view(), name='preview-invoice'),
    path('check-offer/<str:pid>/', CheckOfferView.as_view(), name='check-offer'),
    path('make-payment/<str:inv>/', MakePaymentView.as_view(), name='make-payment'),
    path('bookings/complete/<str:booking_id>/', booking_complete, name='booking-complete'),
    path('booking-payment/<str:booking_id>/<str:mode>/', pay_booking, name='booking-payment'),
    path('booking-confirm/', confirm_booking, name='booking-confirm'),

    # Saved Packages
    path('packages/save/<str:package_id>/', save_package, name='save-package'),
    path('packages/unsave/<str:package_id>/', unsave_package, name='unsave-package'),
    path('saved-packages/', view_saved_packages, name='saved-packages'),

    # Contact
    path('contact/', contact_submit, name='api-contact-submit'),

    # Stripe
    path('paynotifier/', stripe_webhook, name='pay-notifier'),
    path('verify-payment/<str:session_id>/', wallet_views.verify_stripe_payment, name='verify-stripe-payment'),
]
