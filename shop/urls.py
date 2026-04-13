from django.urls import path
from .import views
# from django.views import View

urlpatterns = [
    path("", views.landing, name="landing"),
    path("shop/", views.shop, name="shop"),
    path("auth/", views.auth_page, name="auth"),
    path("checkout/", views.checkout_page, name="checkout-page"),
    path("profile/", views.profile_page, name="profile-page"),
    path("api/products/", views.products, name="api-products"),
    path("api/checkout/", views.checkout, name="api-checkout"),
    path("api/signup/", views.user_signup, name="api-signup"),
    path("api/login/", views.user_login, name="api-login"),
    path("api/logout/", views.user_logout, name="api-logout"),
    path("api/auth-check/", views.check_auth, name="api-auth-check"),
    path("api/sync-cart/", views.sync_cart, name="api-sync-cart"),
    path("api/orders/", views.get_orders, name="api-orders"),
    path("api/fetch-category/", views.fetch_category_products, name="api-fetch-category"),
    path("api/external-search/", views.external_search, name="api-external-search"),
    path("api/verify-2fa/", views.verify_2fa, name="api-verify-2fa"),
    path("api/forgot-password/", views.request_password_reset, name="api-forgot-password"),
    path("api/reset-password/<str:token>/", views.reset_password, name="api-reset-password"),
]