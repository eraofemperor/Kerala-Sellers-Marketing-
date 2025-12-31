from rest_framework import serializers
from .models import Order, ReturnRequest, SupportConversation, SupportMessage, Policy


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ['created_at']


class ReturnRequestSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    
    class Meta:
        model = ReturnRequest
        fields = ['return_id', 'order_id', 'status', 'refund_amount', 'refund_date']
        read_only_fields = ['return_id', 'status']


class ReturnRequestCreateSerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=50)
    product_id = serializers.CharField(max_length=50)
    reason = serializers.ChoiceField(choices=ReturnRequest.REASON_CHOICES)
    refund_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(order_id=value)
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order with this ID does not exist.")

    def validate(self, data):
        order = data['order_id']
        product_id = data['product_id']
        
        # Check if a return request already exists for this order and product
        if ReturnRequest.objects.filter(order=order, product_id=product_id).exists():
            raise serializers.ValidationError(
                "A return request already exists for this product in this order."
            )
        
        return data


class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = '__all__'
        read_only_fields = ['created_at']


class SupportConversationSerializer(serializers.ModelSerializer):
    messages = SupportMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportConversation
        fields = '__all__'
        read_only_fields = ['session_id', 'started_at']


class PolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
