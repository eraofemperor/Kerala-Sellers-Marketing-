#!/usr/bin/env python3
"""
Test script for intent classification API integration.
Tests the SupportMessageView with automatic intent detection.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/home/engine/project')
django.setup()

from django.test import Client

def test_intent_detection_api():
    """Test the intent detection through the API"""
    client = Client()
    
    # Create a conversation first
    response = client.post('/api/v1/conversations/', 
                          data={'user_id': 'test_user_123'},
                          content_type='application/json')
    
    if response.status_code != 201:
        print(f"Failed to create conversation: {response.content}")
        return False
    
    conversation_data = response.json()
    conversation_id = conversation_data['conversation_id']
    print(f"Created conversation: {conversation_id}")
    
    # Test cases for different intents
    test_cases = [
        {
            'message': 'Where is my order?',
            'expected_intent': 'order_status',
            'language': 'en'
        },
        {
            'message': 'I want to return this damaged product',
            'expected_intent': 'return_refund',
            'language': 'en'
        },
        {
            'message': 'What is your refund policy?',
            'expected_intent': 'policy',
            'language': 'en'
        },
        {
            'message': 'I need to talk to a human agent immediately!',
            'expected_intent': 'escalation',
            'language': 'en'
        },
        {
            'message': 'Hello, how are you?',
            'expected_intent': 'general',
            'language': 'en'
        },
        {
            'message': 'എന്റെ ഓർഡർ എവിടെയാണ്?',
            'expected_intent': 'order_status',
            'language': 'ml'
        },
        {
            'message': 'ഈ ഉൽപന്നം നശിച്ചു, റിട്ടേൺ ചെയ്യാൻ ആഗ്രഹിക്കുന്നു',
            'expected_intent': 'return_refund',
            'language': 'ml'
        },
        {
            'message': 'നിങ്ങളുടെ നയം എന്താണ്?',
            'expected_intent': 'policy',
            'language': 'ml'
        },
        {
            'message': 'മനുഷ്യനോട് സംസാരിക്കാൻ ആഗ്രഹിക്കുന്നു',
            'expected_intent': 'escalation',
            'language': 'ml'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case['message']
        expected_intent = test_case['expected_intent']
        
        # Create message via API
        response = client.post(f'/api/v1/conversations/{conversation_id}/messages/',
                              data={'message': message, 'sender': 'user'},
                              content_type='application/json')
        
        if response.status_code != 201:
            print(f"Test {i} FAILED: API request failed - {response.content}")
            all_passed = False
            continue
        
        response_data = response.json()
        detected_intent = response_data.get('detected_intent', 'unknown')
        query_type = response_data.get('query_type', 'unknown')
        
        print(f"Test {i}: '{message[:30]}...' -> Detected: {detected_intent}, Query Type: {query_type}, Expected: {expected_intent}")
        
        if detected_intent == expected_intent and query_type == expected_intent:
            print(f"  ✓ PASSED")
        else:
            print(f"  ✗ FAILED - Expected {expected_intent}, got {detected_intent}/{query_type}")
            all_passed = False
    
    return all_passed

def test_escalation_conversation_update():
    """Test that escalation intent updates conversation flags"""
    client = Client()
    
    # Create a conversation
    response = client.post('/api/v1/conversations/', 
                          data={'user_id': 'test_user_escalation'},
                          content_type='application/json')
    
    if response.status_code != 201:
        print(f"Failed to create conversation: {response.content}")
        return False
    
    conversation_data = response.json()
    conversation_id = conversation_data['conversation_id']
    
    # Send a regular message first
    response = client.post(f'/api/v1/conversations/{conversation_id}/messages/',
                          data={'message': 'Hello, I have a question', 'sender': 'user'},
                          content_type='application/json')
    
    if response.status_code != 201:
        print(f"Failed to send regular message: {response.content}")
        return False
    
    # Send an escalation message
    response = client.post(f'/api/v1/conversations/{conversation_id}/messages/',
                          data={'message': 'I need to talk to a human agent now!', 'sender': 'user'},
                          content_type='application/json')
    
    if response.status_code != 201:
        print(f"Failed to send escalation message: {response.content}")
        return False
    
    # Check the conversation status
    response = client.get(f'/api/v1/conversations/{conversation_id}/')
    
    if response.status_code != 200:
        print(f"Failed to get conversation: {response.content}")
        return False
    
    conversation_data = response.json()
    escalated = conversation_data.get('escalated', False)
    escalation_reason = conversation_data.get('escalation_reason', '')
    
    print(f"Escalation test - Escalated: {escalated}, Reason: '{escalation_reason[:30]}...'")
    
    if escalated and 'human agent' in escalation_reason:
        print("  ✓ PASSED - Conversation properly escalated")
        return True
    else:
        print("  ✗ FAILED - Conversation not properly escalated")
        return False

if __name__ == '__main__':
    print("Testing Intent Classification API Integration...")
    print("=" * 60)
    
    print("\n1. Testing Intent Detection:")
    print("-" * 40)
    intent_tests_passed = test_intent_detection_api()
    
    print("\n2. Testing Escalation Logic:")
    print("-" * 40)
    escalation_test_passed = test_escalation_conversation_update()
    
    print("\n" + "=" * 60)
    if intent_tests_passed and escalation_test_passed:
        print("🎉 ALL TESTS PASSED! Intent classification is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)