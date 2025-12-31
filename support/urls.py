from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderStatusView

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('v1/orders/<str:order_id>/status/', OrderStatusView.as_view(), name='order-status'),
]
