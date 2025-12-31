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
        fields = '__all__'
        read_only_fields = ['requested_at']


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
