#!/usr/bin/env python
"""
Comprehensive test for LLM Integration API (Task 8)

This script demonstrates:
1. AI is used only for general intent
2. Deterministic responses for other intents
3. Bilingual support (EN + ML)
4. AI confidence scores
5. Fallback mechanism
"""

import os
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/engine/project')

import django
django.setup()

from support.tests import LLMClientTests, LLMIntegrationTests
from django.test.utils import get_runner
from django.conf import settings

# Create a test runner
TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

print("=" * 80)
print("LLM INTEGRATION TESTS - COMPREHENSIVE")
print("=" * 80)

# Run LLMClient tests
print("\n[PART 1] LLM Client Unit Tests")
print("-" * 80)
failures = test_runner.run_tests(['support.tests.LLMClientTests'])

# Run LLMIntegration tests
print("\n[PART 2] LLM API Integration Tests")
print("-" * 80)
failures += test_runner.run_tests(['support.tests.LLMIntegrationTests'])

print("\n" + "=" * 80)
if failures == 0:
    print("ALL LLM INTEGRATION TESTS PASSED! ✓")
    print("=" * 80)
    print("\nImplemented Features:")
    print("✓ LLM client with OpenAI/Anthropic/Mock support")
    print("✓ AI used ONLY for general intent queries")
    print("✓ Deterministic responses for order_status, return_refund, policy, escalation")
    print("✓ Bilingual support (English & Malayalam)")
    print("✓ AI confidence scoring (0.0 - 1.0)")
    print("✓ Safe fallback mechanism when AI fails")
    print("✓ PII stripping (emails, phone numbers, credit cards)")
    print("✓ Token limit enforcement")
    print("✓ Timeout handling")
    sys.exit(0)
else:
    print(f"TESTS FAILED: {failures} failures")
    print("=" * 80)
    sys.exit(1)
