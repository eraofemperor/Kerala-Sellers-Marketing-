from django.contrib import admin
from django.core.cache import cache
from .models import Order, ReturnRequest, SupportConversation, SupportMessage, Policy


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user_id', 'status', 'created_at', 'estimated_delivery']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user_id', 'tracking_number']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'user_id', 'status', 'tracking_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'packed_at', 'shipped_at', 'delivered_at', 'estimated_delivery')
        }),
    )


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['return_id', 'order', 'product_id', 'reason', 'status', 'refund_amount', 'requested_at']
    list_filter = ['status', 'reason', 'requested_at']
    search_fields = ['return_id', 'order__order_id', 'product_id']
    readonly_fields = ['requested_at']
    ordering = ['-requested_at']
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Return Information', {
            'fields': ('return_id', 'order', 'product_id', 'reason', 'status')
        }),
        ('Refund Details', {
            'fields': ('refund_amount', 'refund_date')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'approved_at')
        }),
    )


@admin.register(SupportConversation)
class SupportConversationAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user_id', 'language', 'status', 'message_count', 'escalated', 'assigned_agent', 'started_at']
    list_filter = ['language', 'status', 'escalated', 'started_at']
    search_fields = ['session_id', 'user_id', 'assigned_agent']
    readonly_fields = ['session_id', 'started_at', 'escalated_at', 'resolved_at']
    ordering = ['-started_at']
    date_hierarchy = 'started_at'

    fieldsets = (
        ('Conversation Information', {
            'fields': ('session_id', 'user_id', 'language', 'status', 'message_count')
        }),
        ('Escalation', {
            'fields': ('escalated', 'escalation_reason', 'escalated_at')
        }),
        ('Agent Assignment', {
            'fields': ('assigned_agent',)
        }),
        ('Resolution', {
            'fields': ('resolved_at',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'ended_at')
        }),
    )


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'query_type', 'language_detected', 'ai_confidence', 'created_at']
    list_filter = ['sender', 'query_type', 'language_detected', 'created_at']
    search_fields = ['conversation__session_id', 'message']
    readonly_fields = ['created_at']
    ordering = ['created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Message Information', {
            'fields': ('conversation', 'sender', 'message')
        }),
        ('Classification', {
            'fields': ('query_type', 'language_detected', 'ai_confidence')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['policy_type', 'version', 'updated_at', 'created_at']
    list_filter = ['version', 'updated_at', 'created_at']
    search_fields = ['policy_type', 'content_en', 'content_ml']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['policy_type']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('policy_type', 'version')
        }),
        ('Content', {
            'fields': ('content_en', 'content_ml')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Override save_model to invalidate cache when policy is updated.
        """
        super().save_model(request, obj, form, change)
        
        # Invalidate specific policy cache
        cache_key = f'policy_{obj.policy_type}'
        cache.delete(cache_key)
        
        # Invalidate policy list cache
        cache.delete('policy_list')
        
    def delete_model(self, request, obj):
        """
        Override delete_model to invalidate cache when policy is deleted.
        """
        # Invalidate specific policy cache before deletion
        cache_key = f'policy_{obj.policy_type}'
        cache.delete(cache_key)
        
        # Invalidate policy list cache
        cache.delete('policy_list')
        
        super().delete_model(request, obj)
