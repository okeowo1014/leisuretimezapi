from django.urls import path, include
from rest_framework.routers import DefaultRouter

from index.utils import activate_account
from .auth_views import (
    AuthViewSet, ChangePasswordView, ResetPasswordView,
    ResetPasswordConfirmView
)
app_name = 'index'

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    # path('', include('dj_rest_auth.urls')),
    path('', include(router.urls)),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password-confirm/', ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('activate/<str:utoken>/<str:token>/', activate_account, name='activate_account'),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    # path('registration/', include('dj_rest_auth.registration.urls')),
]

# from django.urls import path
# from .views import (
#     customer_registration, activate_account, customer_login, logout_customer,
#     password_reset_request, password_reset_confirm, update_password,
#     update_profile, update_display_picture
# )
# from rest_framework.authtoken.views import obtain_auth_token

# urlpatterns = [
#     path('register/', customer_registration, name='customer-register'),
#     path('activate/<uidb64>/<token>/', activate_account, name='activate-account'),
#     path('login/', customer_login, name='customer-login'),
#     path('logout/', logout_customer, name='customer-logout'),

#     path('password-reset-request/', password_reset_request, name='password-reset-request'),
#     path('password-reset/<uidb64>/<token>/', password_reset_confirm, name='password-reset-confirm'),
#     path('update-password/', update_password, name='update-password'),

#     path('update-profile/<str:field>/', update_profile, name='update-profile'),
#     path('update-display-picture/', update_display_picture, name='update-display-picture'),

#     path('api-token-auth/', obtain_auth_token, name='api-token-auth'),
# ]
