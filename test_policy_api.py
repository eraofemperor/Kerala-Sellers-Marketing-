#!/usr/bin/env python3
"""
Comprehensive test script for the Policy API endpoints.
Tests all functionality including caching behavior.
"""

import requests
import time
import json
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, method="GET", url="", data=None, expected_status=200):
    """Test an API endpoint and return results."""
    print(f"\n🧪 Testing: {name}")
    print(f"   {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{url}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{url}", json=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ SUCCESS")
        else:
            print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
        
        # Pretty print JSON response
        try:
            json_data = response.json()
            print(f"   Response: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
            return json_data, response.status_code
        except:
            print(f"   Response: {response.text}")
            return response.text, response.status_code
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return None, None

def test_policy_apis():
    """Test all Policy API endpoints."""
    print("🚀 Starting Policy API Tests")
    print("=" * 50)
    
    # Test 1: List all policies
    test_endpoint(
        "List All Policies",
        "GET",
        "/policies/",
        expected_status=200
    )
    
    # Test 2: Get specific policy by type
    test_endpoint(
        "Get Refund Policy",
        "GET", 
        "/policies/refund_policy/",
        expected_status=200
    )
    
    test_endpoint(
        "Get Return Policy",
        "GET",
        "/policies/return_policy/", 
        expected_status=200
    )
    
    test_endpoint(
        "Get Shipping Policy",
        "GET",
        "/policies/shipping_policy/",
        expected_status=200
    )
    
    # Test 3: Test error handling
    test_endpoint(
        "Get Non-existent Policy (should return 404)",
        "GET",
        "/policies/nonexistent_policy/",
        expected_status=404
    )
    
    print("\n" + "=" * 50)
    print("🎯 Caching Performance Tests")
    print("=" * 50)
    
    # Test 4: Performance test - first call should be slower (database)
    print("\n📊 Testing cache performance...")
    
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/policies/refund_policy/")
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/policies/refund_policy/")
    second_call_time = time.time() - start_time
    
    print(f"   First call (DB): {first_call_time:.4f} seconds")
    print(f"   Second call (Cache): {second_call_time:.4f} seconds")
    
    if second_call_time < first_call_time:
        print("   ✅ Cache is working - second call is faster!")
    else:
        print("   ⚠️  Cache may not be working as expected")
    
    # Test 5: List endpoint caching
    start_time = time.time()
    response3 = requests.get(f"{BASE_URL}/policies/")
    first_list_time = time.time() - start_time
    
    start_time = time.time()
    response4 = requests.get(f"{BASE_URL}/policies/")
    second_list_time = time.time() - start_time
    
    print(f"\n   List API - First call: {first_list_time:.4f} seconds")
    print(f"   List API - Second call: {second_list_time:.4f} seconds")
    
    if second_list_time < first_list_time:
        print("   ✅ List cache is working!")
    else:
        print("   ⚠️  List cache may not be working as expected")
    
    print("\n" + "=" * 50)
    print("🔍 Response Format Validation")
    print("=" * 50)
    
    # Test 6: Validate response formats
    policy_response = requests.get(f"{BASE_URL}/policies/refund_policy/").json()
    
    required_fields = ['policy_type', 'version', 'content_en', 'content_ml']
    print(f"\n📋 Validating refund policy response...")
    
    for field in required_fields:
        if field in policy_response:
            print(f"   ✅ {field}: Present")
        else:
            print(f"   ❌ {field}: Missing")
    
    # Test list response format
    list_response = requests.get(f"{BASE_URL}/policies/").json()
    print(f"\n📋 Validating policy list response...")
    
    if isinstance(list_response, list):
        print(f"   ✅ Response is a list")
        if len(list_response) > 0:
            first_item = list_response[0]
            list_required_fields = ['policy_type', 'version']
            for field in list_required_fields:
                if field in first_item:
                    print(f"   ✅ {field}: Present in list items")
                else:
                    print(f"   ❌ {field}: Missing in list items")
    else:
        print(f"   ❌ Response is not a list")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)

def test_existing_order_apis():
    """Test existing order APIs to ensure they still work."""
    print("\n🔄 Testing existing Order APIs...")
    
    # Test order status (should work with existing data)
    test_endpoint(
        "Order Status API",
        "GET", 
        "/orders/nonexistent_order/status/",
        expected_status=404
    )

if __name__ == "__main__":
    test_policy_apis()
    test_existing_order_apis()
    
    print(f"\n🏁 Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")