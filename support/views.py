from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, ReturnRequest, SupportConversation, SupportMessage, Policy
from .serializers import (
    OrderSerializer,
    ReturnRequestSerializer,
    SupportConversationSerializer,
    SupportMessageSerializer,
    PolicySerializer
)


def generate_order_timeline(order):
    """
    Generate a timeline of order status changes based on available timestamps.
    
    Args:
        order: Order model instance
        
    Returns:
        list: Timeline entries with status and timestamp
    """
    timeline = []
    
    # Add placed status (always available via created_at)
    if order.created_at:
        timeline.append({
            'status': 'placed',
            'timestamp': order.created_at.isoformat() + 'Z'
        })
    
    # Add packed status if available
    if order.packed_at:
        timeline.append({
            'status': 'packed',
            'timestamp': order.packed_at.isoformat() + 'Z'
        })
    
    # Add shipped status if available
    if order.shipped_at:
        timeline.append({
            'status': 'shipped',
            'timestamp': order.shipped_at.isoformat() + 'Z'
        })
    
    # Add delivered status if available
    if order.delivered_at:
        timeline.append({
            'status': 'delivered',
            'timestamp': order.delivered_at.isoformat() + 'Z'
        })
    
    return timeline


class OrderStatusView(APIView):
    """
    API View for retrieving order status and timeline.
    
    GET /api/v1/orders/{order_id}/status
    """
    
    def get(self, request, order_id, format=None):
        """
        Retrieve order status and generate timeline.
        
        Args:
            request: HTTP request
            order_id: Order ID to look up
            
        Returns:
            Response: JSON response with order status and timeline
        """
        try:
            order = Order.objects.get(order_id=order_id)
            
            # Generate timeline
            timeline = generate_order_timeline(order)
            
            # Build response data
            response_data = {
                'order_id': order.order_id,
                'status': order.status,
                'timeline': timeline
            }
            
            # Add optional fields if available
            if order.tracking_number:
                response_data['tracking_number'] = order.tracking_number
            
            if order.estimated_delivery:
                response_data['estimated_delivery'] = order.estimated_delivery.isoformat() + 'Z'
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found. Please check your order ID.'},
                status=status.HTTP_404_NOT_FOUND
            )
