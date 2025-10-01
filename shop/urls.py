from django.urls import path
from .import views
# from django.views import View

urlpatterns = [
    path("", views.home, name="home"),
    path("api/products/", views.products, name="api-products"),
    path("api/checkout/", views.checkout, name="api-checkout"),
]