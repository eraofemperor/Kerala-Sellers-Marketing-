#!/usr/bin/env python3

import requests
import json
import uuid

# Base URL for the API
BASE_URL = "http://localhost:8000/api"


def test_language_detection_api():
    """Test the language detection API endpoints"""
    
    print("Testing Language Detection API...")
    print("=" * 50)
    
    # Test 1: Create a conversation
    print("\n1. Creating a new conversation...")
    conversation_data = {
        "user_id": "test_user_123"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/conversations/",
            json=conversation_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            conversation_data = response.json()
            conversation_id = conversation_data["conversation_id"]
            print(f"✓ Conversation created: {conversation_id}")
            print(f"  User ID: {conversation_data['user_id']}")
            print(f"  Language: {conversation_data['language']}")
        else:
            print(f"✗ Failed to create conversation: {response.status_code}")
            print(f"  Response: {response.text}")
            return
            
    except Exception as e:
        print(f"✗ Error creating conversation: {e}")
        return
    
    # Test 2: Send English message
    print("\n2. Sending English message...")
    english_message = {
        "message": "Where is my order?",
        "sender": "user",
        "query_type": "order_status"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/conversations/{conversation_id}/messages/",
            json=english_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            message_data = response.json()
            print(f"✓ English message sent successfully")
            print(f"  Detected language: {message_data['detected_language']}")
            print(f"  Response language: {message_data['response_language']}")
            print(f"  Message: {message_data['message']}")
        else:
            print(f"✗ Failed to send English message: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error sending English message: {e}")
    
    # Test 3: Send Malayalam message
    print("\n3. Sending Malayalam message...")
    malayalam_message = {
        "message": "എന്റെ ഓർഡർ എവിടെയാണ്?",
        "sender": "user",
        "query_type": "order_status"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/conversations/{conversation_id}/messages/",
            json=malayalam_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            message_data = response.json()
            print(f"✓ Malayalam message sent successfully")
            print(f"  Detected language: {message_data['detected_language']}")
            print(f"  Response language: {message_data['response_language']}")
            print(f"  Message: {message_data['message']}")
        else:
            print(f"✗ Failed to send Malayalam message: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error sending Malayalam message: {e}")
    
    # Test 4: Send mixed message
    print("\n4. Sending mixed language message...")
    mixed_message = {
        "message": "Order എവിടെയാണ്?",
        "sender": "user",
        "query_type": "order_status"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/conversations/{conversation_id}/messages/",
            json=mixed_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            message_data = response.json()
            print(f"✓ Mixed message sent successfully")
            print(f"  Detected language: {message_data['detected_language']}")
            print(f"  Response language: {message_data['response_language']}")
            print(f"  Message: {message_data['message']}")
        else:
            print(f"✗ Failed to send mixed message: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error sending mixed message: {e}")
    
    # Test 5: Get conversation details
    print("\n5. Getting conversation details...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/v1/conversations/{conversation_id}/",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            conversation_details = response.json()
            print(f"✓ Conversation details retrieved")
            print(f"  Conversation ID: {conversation_details['session_id']}")
            print(f"  User ID: {conversation_details['user_id']}")
            print(f"  Current Language: {conversation_details['language']}")
            print(f"  Message Count: {conversation_details['message_count']}")
            print(f"  Messages: {len(conversation_details['messages'])} messages in conversation")
        else:
            print(f"✗ Failed to get conversation details: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Error getting conversation details: {e}")
    
    print("\n" + "=" * 50)
    print("Language Detection API Testing Complete!")


if __name__ == "__main__":
    test_language_detection_api()