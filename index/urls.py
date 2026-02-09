from django.urls import path, include
from rest_framework.routers import DefaultRouter

from index import wallet_views
from index.utils import activate_account
from index.webhook import stripe_webhook
from .auth_views import (
    AuthViewSet, ChangePasswordView, ResendConfirmationView, ResetPasswordView,
    ResetPasswordConfirmView
)
from .views import (
    BookPackageView, BookingViewSet, CheckOfferView, CruiseBookingViewSet, CustomerProfileDetailView, CustomerProfileImageUpdateView, EventViewSet, MakePaymentView, PreviewInvoiceView, SearchCountriesLocationsView, booking_complete, confirm_booking, contact_submit, index, package_list, package_details, pay_booking, personal_booking,
    booking_history, account_settings, publish_invoice, save_package, search_locations, unsave_package, update_display_picture, view_saved_packages
)
app_name = 'index'

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'events', EventViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'wallets', wallet_views.WalletViewSet, basename='wallet')
router.register(r'transactions', wallet_views.TransactionViewSet, basename='transaction')
router.register(r'cruise-bookings', CruiseBookingViewSet, basename='cruise_booking')
urlpatterns = [
    # path('', include('dj_rest_auth.urls')),
    path('', include(router.urls)),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('resend-activation-email/',
         ResendConfirmationView.as_view(), name='reset-password'),
    path('reset-password-confirm/<str:utoken>/<str:token>/',
         ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('activate/<str:utoken>/<str:token>/',
         activate_account, name='activate_account'),
    path('index/', index, name='api-index'),
    path('packages/', package_list, name='api-packages'),
    path('packages/<str:pid>/', package_details, name='api-package-details'),
    path('personal-booking/', personal_booking, name='api-personal-booking'),
    path('booking-history/', booking_history, name='api-booking-history'),
    path('account-settings/', account_settings, name='api-account-settings'),
    path('search-locations/', search_locations, name='api-search-locations'),
    path('book-package/<str:pid>/', BookPackageView.as_view(), name='book-package'),
    path('preview-invoice/<str:inv>/',
         PreviewInvoiceView.as_view(), name='preview-invoice'),
    path('check-offer/<str:pid>/', CheckOfferView.as_view(), name='check-offer'),
    path('make-payment/<str:inv>/', MakePaymentView.as_view(), name='make-payment'),
    path('search-countries-locations/',
         SearchCountriesLocationsView.as_view(), name='search-locations'),
    path('update_display_picture/', update_display_picture,
         name='update_display_picture'),
    # path('payments/create-intent/',create_payment_intent),
    # path('payments/create-checkout-session/', create_checkout_session),
    path('bookings/complete/<str:booking_id>/', booking_complete),
    path('invoices/<str:invoice_id>/publish/', publish_invoice),
    path('contact/', contact_submit, name='api-contact-submit'),
        path('profile/', 
         CustomerProfileDetailView.as_view(), 
         name='customer-profile'),
    path('profile/image/', 
         CustomerProfileImageUpdateView.as_view(), 
         name='profile-image-update'),
     path('paynotifier/', stripe_webhook, name='pay-notifier'),
     path('verify-payment/<str:session_id>/', wallet_views.verify_stripe_payment, name='verify_stripe_payment'),
     path('packages/save/<str:package_id>/', save_package, name='save_package'),
     path('packages/unsave/<str:package_id>/', unsave_package, name='unsave_package'),
     path('saved-packages/', view_saved_packages, name='view_saved_packages'),
     path('booking-payment/<str:booking_id>/<str:mode>/', pay_booking, name='booking-payment'),
     path('booking-confirm/', confirm_booking, name='booking-confirm'),

]
