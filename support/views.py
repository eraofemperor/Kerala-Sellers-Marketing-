from django.utils import timezone
from django.core.cache import cache
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
from .utils.language import detect_language, determine_response_language
from .utils.intent import detect_intent
from .utils.responses import generate_response
from .services.llm import get_llm_client


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


class PolicyListView(APIView):
    """
    API View for listing all policies with their types and versions.
    
    GET /api/v1/policies/
    """
    
    def get(self, request, format=None):
        """
        Retrieve list of all policies.
        
        Returns:
            Response: JSON response with policy types and versions
        """
        # Try to get from cache first
        cache_key = 'policy_list'
        cached_policies = cache.get(cache_key)
        
        if cached_policies is not None:
            return Response(cached_policies, status=status.HTTP_200_OK)
        
        # If not in cache, fetch from database
        policies = Policy.objects.all()
        policy_list = []
        
        for policy in policies:
            policy_list.append({
                'policy_type': policy.policy_type,
                'version': policy.version
            })
        
        # Cache the result for 5 minutes
        cache.set(cache_key, policy_list, 300)
        
        return Response(policy_list, status=status.HTTP_200_OK)


class PolicyDetailView(APIView):
    """
    API View for retrieving policy by type.
    
    GET /api/v1/policies/{policy_type}/
    """
    
    def get(self, request, policy_type, format=None):
        """
        Retrieve policy by type with bilingual content.
        
        Args:
            request: HTTP request
            policy_type: Policy type identifier
            
        Returns:
            Response: JSON response with policy content
        """
        # Try to get from cache first
        cache_key = f'policy_{policy_type}'
        cached_policy = cache.get(cache_key)
        
        if cached_policy is not None:
            return Response(cached_policy, status=status.HTTP_200_OK)
        
        # If not in cache, fetch from database
        try:
            policy = Policy.objects.get(policy_type=policy_type)
            
            policy_data = {
                'policy_type': policy.policy_type,
                'version': policy.version,
                'content_en': policy.content_en,
                'content_ml': policy.content_ml
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, policy_data, 300)
            
            return Response(policy_data, status=status.HTTP_200_OK)
            
        except Policy.DoesNotExist:
            return Response(
                {'error': 'Policy not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class PolicyModelAdmin:
    """
    Custom admin integration for cache invalidation.
    This class provides methods to be called from admin.py to invalidate cache when policies are updated.
    """

    @staticmethod
    def invalidate_policy_cache():
        """
        Invalidate all policy-related cache entries.
        Called when policies are updated through admin interface.
        """
        # Clear specific policy cache entries
        policies = Policy.objects.all()
        for policy in policies:
            cache_key = f'policy_{policy.policy_type}'
            cache.delete(cache_key)

        # Clear policy list cache
        cache.delete('policy_list')


class SupportMessageView(APIView):
    """
    API View for creating support messages with language detection and intent classification.

    POST /api/v1/conversations/{conversation_id}/messages/
    """

    def post(self, request, conversation_id, format=None):
        """
        Create a new support message with automatic language detection and intent classification.

        Args:
            request: HTTP request with message data
            conversation_id: Conversation ID

        Returns:
            Response: JSON response with created message details
        """
        try:
            # Get the conversation
            conversation = SupportConversation.objects.get(session_id=conversation_id)

            # Get message data from request
            message_text = request.data.get('message', '')
            sender = request.data.get('sender', 'user')
            query_type = request.data.get('query_type', None)

            if not message_text:
                return Response(
                    {'error': 'Message text is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Detect language
            detected_language = detect_language(message_text)

            # Detect intent if query_type not explicitly provided
            if query_type is None:
                detected_intent = detect_intent(message_text, detected_language)
                query_type = detected_intent
            else:
                detected_intent = query_type

            # Determine response language
            response_language = determine_response_language(conversation, detected_language)

            # Update conversation language if this is the first message or user switched language
            if conversation.message_count == 0:
                # First message - set conversation language
                conversation.language = detected_language
            else:
                # Subsequent message - update if user switched to a non-mixed language
                if detected_language != 'mixed':
                    conversation.language = detected_language

            # Handle escalation logic
            if detected_intent == 'escalation':
                conversation.escalated = True
                conversation.escalation_reason = message_text

            # Save conversation
            conversation.message_count += 1
            conversation.save()

            # Create the message
            message = SupportMessage.objects.create(
                conversation=conversation,
                sender=sender,
                message=message_text,
                language_detected=detected_language,
                query_type=query_type
            )

            # Generate AI response if the message is from a user
            ai_message_data = None
            if sender == 'user':
                ai_response_text = None
                ai_confidence = None

                # Use LLM only for general intent, deterministic responses for others
                if detected_intent == 'general':
                    # Use LLM for general queries
                    try:
                        llm_client = get_llm_client()
                        ai_response_text, ai_confidence, used_fallback = llm_client.generate_reply(
                            message_text,
                            response_language
                        )

                        if used_fallback:
                            # Log that fallback was used
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.info("LLM fallback used for general intent")

                    except Exception as e:
                        # Fallback to template-based response on any error
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"LLM error, using fallback: {str(e)}")

                        ai_response_text = generate_response('general', response_language, {})
                        ai_confidence = 0.5
                else:
                    # Use deterministic template-based responses for non-general intents
                    context = {}
                    if detected_intent == 'order_status':
                        # Try to find the latest order for this user
                        latest_order = Order.objects.filter(user_id=conversation.user_id).first()
                        if latest_order:
                            context['status'] = latest_order.status
                            if latest_order.estimated_delivery:
                                context['date'] = latest_order.estimated_delivery.strftime('%Y-%m-%d')

                    elif detected_intent == 'policy':
                        # Try to identify policy type from message
                        all_policies = Policy.objects.all()
                        for p in all_policies:
                            if p.policy_type.lower() in message_text.lower():
                                context['policy_type'] = p.policy_type
                                break

                    # Generate deterministic response
                    ai_response_text = generate_response(detected_intent, response_language, context)
                    ai_confidence = 1.0  # Deterministic responses have high confidence

                # Create AI message
                ai_message = SupportMessage.objects.create(
                    conversation=conversation,
                    sender='ai',
                    message=ai_response_text,
                    language_detected=response_language,
                    query_type=detected_intent,
                    ai_confidence=ai_confidence
                )

                # Update conversation message count for AI message
                conversation.message_count += 1
                conversation.save()

                ai_message_data = {
                    'message_id': ai_message.id,
                    'message': ai_message.message,
                    'sender': 'ai',
                    'query_type': ai_message.query_type,
                    'ai_confidence': ai_confidence,
                    'created_at': ai_message.created_at.isoformat() + 'Z'
                }

            # Return response with language and intent information
            response_data = {
                'message_id': message.id,
                'conversation_id': conversation.session_id,
                'detected_language': detected_language,
                'response_language': response_language,
                'detected_intent': detected_intent,
                'message': message_text,
                'sender': sender,
                'query_type': query_type,
                'created_at': message.created_at.isoformat() + 'Z'
            }
            
            if ai_message_data:
                response_data['ai_response'] = ai_message_data

            return Response(response_data, status=status.HTTP_201_CREATED)

        except SupportConversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error creating message: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class SupportConversationView(APIView):
    """
    API View for creating support conversations.

    POST /api/v1/conversations/
    GET /api/v1/conversations/{conversation_id}/
    """

    def post(self, request, format=None):
        """
        Create a new support conversation.

        Args:
            request: HTTP request with conversation data

        Returns:
            Response: JSON response with created conversation details
        """
        try:
            user_id = request.data.get('user_id')

            if not user_id:
                return Response(
                    {'error': 'user_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create conversation with default language (English)
            conversation = SupportConversation.objects.create(
                user_id=user_id,
                language='en'  # Default to English, will be updated on first message
            )

            response_data = {
                'conversation_id': conversation.session_id,
                'user_id': conversation.user_id,
                'language': conversation.language,
                'started_at': conversation.started_at.isoformat() + 'Z',
                'message_count': conversation.message_count
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error creating conversation: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, conversation_id=None, format=None):
        """
        Retrieve conversation details.

        Args:
            request: HTTP request
            conversation_id: Conversation ID

        Returns:
            Response: JSON response with conversation details
        """
        if conversation_id:
            try:
                conversation = SupportConversation.objects.get(session_id=conversation_id)
                serializer = SupportConversationSerializer(conversation)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except SupportConversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # List all conversations (for admin purposes)
            conversations = SupportConversation.objects.all()
            serializer = SupportConversationSerializer(conversations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
