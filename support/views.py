from django.utils import timezone
from datetime import timedelta
import random
import string
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, ReturnRequest, SupportConversation, SupportMessage, Policy
from .serializers import (
    OrderSerializer,
    ReturnRequestSerializer,
    ReturnRequestCreateSerializer,
    SupportConversationSerializer,
    SupportMessageSerializer,
    PolicySerializer
)


def generate_return_id():
    """Generate a unique return ID like RET-XXXXX"""
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"RET-{suffix}"


def check_return_eligibility(order):
    """
    Check if an order is eligible for return.
    Rules:
    - Order status = delivered
    - Within 7 days of delivered_at
    """
    if order.status != 'delivered':
        return False, "Return is allowed only if order status is delivered."

    if not order.delivered_at:
        return False, "Delivery timestamp missing for the order."

    # Check if within 7 days
    delivery_date = order.delivered_at
    expiry_date = delivery_date + timedelta(days=7)

    if timezone.now() > expiry_date:
        return False, "Return window expired"

    return True, "Order eligible for return"


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


class ReturnEligibilityView(APIView):
    """
    API View to check return eligibility for an order.
    GET /api/v1/returns/check-eligibility/{order_id}/
    """

    def get(self, request, order_id, format=None):
        try:
            order = Order.objects.get(order_id=order_id)
            eligible, reason = check_return_eligibility(order)
            return Response({
                'order_id': order.order_id,
                'eligible': eligible,
                'reason': reason
            }, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ReturnRequestView(APIView):
    """
    API View for creating and retrieving return requests.
    POST /api/v1/returns/
    GET /api/v1/returns/{return_id}/
    """

    def post(self, request, format=None):
        serializer = ReturnRequestCreateSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.validated_data['order_id']
            
            # Check eligibility again before creating
            eligible, reason = check_return_eligibility(order)
            if not eligible:
                return Response({
                    'eligible': False,
                    'reason': reason
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate return_id
            return_id = generate_return_id()
            while ReturnRequest.objects.filter(return_id=return_id).exists():
                return_id = generate_return_id()

            return_request = ReturnRequest.objects.create(
                return_id=return_id,
                order=order,
                product_id=serializer.validated_data['product_id'],
                reason=serializer.validated_data['reason'],
                refund_amount=serializer.validated_data['refund_amount'],
                status='requested'
            )

            return Response({
                'return_id': return_request.return_id,
                'status': return_request.status
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, return_id=None, format=None):
        if return_id:
            try:
                return_request = ReturnRequest.objects.get(return_id=return_id)
                serializer = ReturnRequestSerializer(return_request)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ReturnRequest.DoesNotExist:
                return Response(
                    {'error': 'Return request not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {'error': 'Return ID is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
