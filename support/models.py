import uuid
from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Placed'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True, help_text="Unique order identifier")
    user_id = models.CharField(max_length=100, help_text="User identifier")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    packed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.order_id


class ReturnRequest(models.Model):
    REASON_CHOICES = [
        ('damaged', 'Damaged'),
        ('unwanted', 'Unwanted'),
        ('defective', 'Defective'),
    ]
    
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    ]
    
    return_id = models.CharField(max_length=50, unique=True, help_text="Unique return identifier")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='returns')
    product_id = models.CharField(max_length=50, help_text="Product identifier")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        
    def __str__(self):
        return self.return_id


class SupportConversation(models.Model):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ml', 'Malayalam'),
    ]
    
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_id = models.CharField(max_length=100)
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default='en')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    message_count = models.IntegerField(default=0)
    escalated = models.BooleanField(default=False)
    escalation_reason = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.session_id} - {self.language}"


class SupportMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    
    QUERY_TYPE_CHOICES = [
        ('order_status', 'Order Status'),
        ('return_refund', 'Return/Refund'),
        ('policy', 'Policy'),
        ('general', 'General'),
        ('escalation', 'Escalation'),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ml', 'Malayalam'),
    ]
    
    conversation = models.ForeignKey(
        SupportConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    language_detected = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    query_type = models.CharField(max_length=20, choices=QUERY_TYPE_CHOICES)
    ai_confidence = models.FloatField(null=True, blank=True, help_text="AI confidence score (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"{self.conversation.session_id} - {self.sender}"


class Policy(models.Model):
    policy_type = models.CharField(max_length=100, unique=True, help_text="Policy type identifier")
    content_en = models.TextField(help_text="Policy content in English")
    content_ml = models.TextField(help_text="Policy content in Malayalam")
    version = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['policy_type']
        verbose_name_plural = 'Policies'
        
    def __str__(self):
        return f"{self.policy_type} v{self.version}"
