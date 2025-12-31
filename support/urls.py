from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderStatusView, ReturnEligibilityView, ReturnRequestView

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('v1/orders/<str:order_id>/status/', OrderStatusView.as_view(), name='order-status'),
    path('v1/returns/check-eligibility/<str:order_id>/', ReturnEligibilityView.as_view(), name='return-eligibility'),
    path('v1/returns/', ReturnRequestView.as_view(), name='return-list'),
    path('v1/returns/<str:return_id>/', ReturnRequestView.as_view(), name='return-detail'),
]
