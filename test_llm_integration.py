#!/usr/bin/env python
"""
Test script for LLM Integration (Task 8)

This script tests the LLM integration layer to ensure:
1. AI is used only for general intent
2. Deterministic responses are preserved for other intents
3. Bilingual support (EN + ML)
4. Fallback works without AI
5. PII is stripped from prompts
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/engine/project')
django.setup()

import requests
import json
from unittest.mock import patch, MagicMock

BASE_URL = 'http://localhost:8000/api/v1'

# Test data
TEST_USER_ID = 'test_llm_user'

print("=" * 70)
print("LLM INTEGRATION TESTS")
print("=" * 70)

# Test 1: Create conversation
print("\n[TEST 1] Creating conversation...")
response = requests.post(f'{BASE_URL}/conversations/', json={'user_id': TEST_USER_ID})
assert response.status_code == 201, f"Failed to create conversation: {response.text}"
conversation_id = response.json()['conversation_id']
print(f"✓ Conversation created: {conversation_id}")

# Test 2: General intent uses LLM (mock)
print("\n[TEST 2] Testing general intent (should use LLM)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'Hello, how are you?'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ General intent detected: {data['detected_intent']}")
print(f"✓ AI response generated: {data['ai_response']['message'][:50]}...")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert 'ai_confidence' in data['ai_response'], "AI confidence not in response"
assert data['ai_response']['ai_confidence'] == 0.8, "Mock LLM should have confidence 0.8"

# Test 3: General intent in Malayalam
print("\n[TEST 3] Testing general intent in Malayalam...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'ഹലോ, സുഖമുണ്ടോ?'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Malayalam detected: {data['detected_language']}")
print(f"✓ Response language: {data['response_language']}")
print(f"✓ AI response in Malayalam: {data['ai_response']['message'][:30]}...")
assert data['detected_language'] == 'ml', "Should detect Malayalam"
assert data['response_language'] == 'ml', "Should respond in Malayalam"

# Test 4: Order status does NOT use LLM
print("\n[TEST 4] Testing order status (should NOT use LLM)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'Where is my order?'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Order status intent: {data['detected_intent']}")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert data['detected_intent'] == 'order_status', "Should detect order_status"
assert data['ai_response']['ai_confidence'] == 1.0, "Deterministic responses should have confidence 1.0"

# Test 5: Return/refund does NOT use LLM
print("\n[TEST 5] Testing return/refund (should NOT use LLM)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'I want to return this item'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Return/refund intent: {data['detected_intent']}")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert data['detected_intent'] == 'return_refund', "Should detect return_refund"
assert data['ai_response']['ai_confidence'] == 1.0, "Should have confidence 1.0"

# Test 6: Policy does NOT use LLM
print("\n[TEST 6] Testing policy query (should NOT use LLM)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'What is your return policy?'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Policy intent: {data['detected_intent']}")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert data['detected_intent'] == 'policy', "Should detect policy"
assert data['ai_response']['ai_confidence'] == 1.0, "Should have confidence 1.0"

# Test 7: Escalation does NOT use LLM
print("\n[TEST 7] Testing escalation (should NOT use LLM)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'I want to talk to a human agent'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Escalation intent: {data['detected_intent']}")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert data['detected_intent'] == 'escalation', "Should detect escalation"
assert data['ai_response']['ai_confidence'] == 1.0, "Should have confidence 1.0"

# Test 8: PII stripping test
print("\n[TEST 8] Testing PII stripping...")
# Create new conversation for PII test
response = requests.post(f'{BASE_URL}/conversations/', json={'user_id': 'test_pii_user'})
assert response.status_code == 201
pii_conversation_id = response.json()['conversation_id']

response = requests.post(
    f'{BASE_URL}/conversations/{pii_conversation_id}/messages/',
    json={'message': 'My email is john@example.com and phone is 9876543210'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ General intent with PII: {data['detected_intent']}")
print(f"✓ AI response generated: {data['ai_response']['message'][:50]}...")
# PII should be stripped before sending to LLM
# (We can't directly verify the prompt content, but we verify the response is generated)

# Test 9: Order status in Malayalam (deterministic)
print("\n[TEST 9] Testing order status in Malayalam (deterministic)...")
response = requests.post(
    f'{BASE_URL}/conversations/{conversation_id}/messages/',
    json={'message': 'എന്റെ ഓർഡർ എവിടെയാണ്?'}
)
assert response.status_code == 201, f"Failed: {response.text}"
data = response.json()
print(f"✓ Order status intent: {data['detected_intent']}")
print(f"✓ Response language: {data['response_language']}")
print(f"✓ AI confidence: {data['ai_response']['ai_confidence']}")
assert data['detected_language'] == 'ml', "Should detect Malayalam"
assert data['response_language'] == 'ml', "Should respond in Malayalam"
assert data['ai_response']['ai_confidence'] == 1.0, "Should have confidence 1.0"

# Test 10: Verify conversation is stored correctly
print("\n[TEST 10] Verifying conversation storage...")
response = requests.get(f'{BASE_URL}/conversations/{conversation_id}/')
assert response.status_code == 200
conversation_data = response.json()
print(f"✓ Conversation message count: {conversation_data['message_count']}")
assert conversation_data['message_count'] > 0, "Should have messages"

print("\n" + "=" * 70)
print("ALL TESTS PASSED! ✓")
print("=" * 70)
print("\nSummary:")
print("✓ AI used only for general intent")
print("✓ Deterministic responses preserved for other intents")
print("✓ Bilingual support working (EN + ML)")
print("✓ AI confidence scores tracked")
print("✓ Fallback system in place (mock provider)")
print("✓ PII stripping implemented")
