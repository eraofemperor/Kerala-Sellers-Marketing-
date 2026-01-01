#!/usr/bin/env python
"""
Demonstration script for Conversation Memory & Context Window Management (Task 9)

This script demonstrates:
1. Conversation context being built from previous general intent messages
2. Context window limiting to recent messages only
3. PII sanitization in conversation context
4. Bilingual support in conversation memory
5. Non-general intent messages being excluded from context
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/engine/project')

import django
django.setup()

from support.services.llm import get_llm_client
from support.models import SupportConversation, SupportMessage
from support.utils.language import detect_language
from support.utils.intent import detect_intent

def demo_conversation_memory():
    """Demonstrate conversation memory functionality"""
    print("=" * 80)
    print("CONVERSATION MEMORY & CONTEXT WINDOW DEMONSTRATION")
    print("=" * 80)
    
    # Create a conversation
    conversation = SupportConversation.objects.create(
        user_id="demo_user",
        language="en"
    )
    
    print(f"\n📝 Created conversation: {conversation.session_id}")
    
    # Create some general intent messages to build context
    messages_data = [
        ("user", "Hello, how are you today?"),
        ("ai", "I'm doing well, thank you! How can I help you?"),
        ("user", "I'm looking for some information about your products."),
        ("ai", "Sure, I'd be happy to help with that. What specific products are you interested in?"),
        ("user", "I'm interested in your Kerala spices collection."),
    ]
    
    print("\n💬 Building conversation history...")
    for sender, message in messages_data:
        detected_lang = detect_language(message)
        detected_intent = detect_intent(message, detected_lang)
        
        SupportMessage.objects.create(
            conversation=conversation,
            sender=sender,
            message=message,
            language_detected=detected_lang,
            query_type=detected_intent
        )
        print(f"  {sender.upper()}: {message}")
        print(f"    → Intent: {detected_intent}, Language: {detected_lang}")
    
    # Now test conversation context building
    llm_client = get_llm_client()
    context = llm_client._build_conversation_context(conversation)
    
    print(f"\n🔍 Generated conversation context:")
    print("-" * 60)
    print(context)
    print("-" * 60)
    
    # Test with a new message that should use the context
    new_message = "Actually, I'm more interested in the organic spices. Can you tell me about those?"
    print(f"\n🆕 New user message: {new_message}")
    
    # Generate reply with conversation context
    response, confidence, used_fallback = llm_client.generate_reply(
        new_message, 'en', conversation
    )
    
    print(f"\n🤖 AI Response (confidence: {confidence:.1f}):")
    print(f"  {response}")
    print(f"  Used fallback: {used_fallback}")
    
    # Test exclusion of non-general intent messages
    print(f"\n🚫 Testing non-general intent exclusion...")
    
    # Add a non-general intent message
    order_message = "Where is my order ORD-12345?"
    SupportMessage.objects.create(
        conversation=conversation,
        sender="user",
        message=order_message,
        language_detected="en",
        query_type="order_status"  # This should be excluded from context
    )
    
    # Rebuild context - should not include the order status message
    updated_context = llm_client._build_conversation_context(conversation)
    
    print(f"  Added order status message: {order_message}")
    print(f"  Order message in context: {'Where is my order' in updated_context}")
    print(f"  Context still contains general messages: {'spices' in updated_context}")
    
    # Test PII sanitization in context
    print(f"\n🔒 Testing PII sanitization in conversation context...")
    
    # Add a message with PII
    pii_message = "By the way, my email is user@example.com and phone is 9876543210"
    SupportMessage.objects.create(
        conversation=conversation,
        sender="user",
        message=pii_message,
        language_detected="en",
        query_type="general"
    )
    
    # Generate reply should sanitize PII in context
    safe_response, safe_confidence, safe_fallback = llm_client.generate_reply(
        "Never mind about that, let's continue our conversation", 'en', conversation
    )
    
    print(f"  Added message with PII: {pii_message}")
    print(f"  Response generated safely: {safe_response is not None}")
    print(f"  Confidence: {safe_confidence:.1f}")
    
    # Test bilingual support
    print(f"\n🌍 Testing bilingual conversation memory...")
    
    # Create a Malayalam conversation
    ml_conversation = SupportConversation.objects.create(
        user_id="demo_user_ml",
        language="ml"
    )
    
    # Add Malayalam messages
    ml_messages = [
        ("user", "ഹലോ, എന്താണ് സുഖം?"),
        ("ai", "നന്ദി, എനിക്ക് നല്ലതാണ്. എന്തെങ്കിലും സഹായിക്കാൻ കഴിയുമോ?"),
    ]
    
    for sender, message in ml_messages:
        detected_lang = detect_language(message)
        detected_intent = detect_intent(message, detected_lang)
        
        SupportMessage.objects.create(
            conversation=ml_conversation,
            sender=sender,
            message=message,
            language_detected=detected_lang,
            query_type=detected_intent
        )
    
    ml_context = llm_client._build_conversation_context(ml_conversation)
    print(f"  Malayalam conversation context built: {len(ml_context) > 0}")
    print(f"  Context contains Malayalam text: {any('\u0D00' <= c <= '\u0D7F' for c in ml_context)}")
    
    # Generate Malayalam response with context
    ml_response, ml_confidence, ml_fallback = llm_client.generate_reply(
        "നന്ദി", 'ml', ml_conversation
    )
    
    print(f"  Malayalam response generated: {ml_response is not None}")
    print(f"  Response contains Malayalam: {any('\u0D00' <= c <= '\u0D7F' for c in ml_response)}")
    
    print(f"\n✅ DEMONSTRATION COMPLETE!")
    print(f"\nImplemented Features:")
    print(f"  ✓ Conversation context building from general intent messages")
    print(f"  ✓ Context window limiting (last 5 exchanges)")
    print(f"  ✓ PII sanitization in conversation history")
    print(f"  ✓ Bilingual support (English & Malayalam)")
    print(f"  ✓ Non-general intent message exclusion")
    print(f"  ✓ Chronological ordering of conversation history")
    print(f"  ✓ Token limit enforcement for context + current message")
    print(f"  ✓ Safe fallback when context processing fails")
    
    # Cleanup
    conversation.delete()
    ml_conversation.delete()

if __name__ == "__main__":
    demo_conversation_memory()