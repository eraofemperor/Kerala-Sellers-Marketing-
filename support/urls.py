from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrderStatusView,
    ReturnEligibilityView,
    ReturnRequestView,
    PolicyListView,
    PolicyDetailView,
    SupportConversationView,
    SupportMessageView,
    EscalateConversationView,
    AssignAgentView,
    AgentMessageView,
    ResolveConversationView
)

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('v1/orders/<str:order_id>/status/', OrderStatusView.as_view(), name='order-status'),
    path('v1/returns/check-eligibility/<str:order_id>/', ReturnEligibilityView.as_view(), name='return-eligibility'),
    path('v1/returns/', ReturnRequestView.as_view(), name='return-list'),
    path('v1/returns/<str:return_id>/', ReturnRequestView.as_view(), name='return-detail'),
    path('v1/policies/', PolicyListView.as_view(), name='policy-list'),
    path('v1/policies/<str:policy_type>/', PolicyDetailView.as_view(), name='policy-detail'),
    path('v1/conversations/', SupportConversationView.as_view(), name='conversation-list'),
    path('v1/conversations/<uuid:conversation_id>/', SupportConversationView.as_view(), name='conversation-detail'),
    path('v1/conversations/<uuid:conversation_id>/messages/', SupportMessageView.as_view(), name='message-create'),
    path('v1/conversations/<uuid:conversation_id>/escalate/', EscalateConversationView.as_view(), name='escalate-conversation'),
    path('v1/conversations/<uuid:conversation_id>/assign/', AssignAgentView.as_view(), name='assign-agent'),
    path('v1/conversations/<uuid:conversation_id>/agent/messages/', AgentMessageView.as_view(), name='agent-message'),
    path('v1/conversations/<uuid:conversation_id>/resolve/', ResolveConversationView.as_view(), name='resolve-conversation'),
]
