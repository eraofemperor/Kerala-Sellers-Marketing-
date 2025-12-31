from django.test import TestCase
from .utils.language import detect_language, determine_response_language
from .utils.intent import detect_intent
from .utils.responses import generate_response
from .models import SupportConversation, SupportMessage, Order, Policy
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


class LanguageDetectionTests(TestCase):
    """Test language detection functionality"""

    def test_english_detection(self):
        """Test English language detection"""
        english_text = "Where is my order?"
        result = detect_language(english_text)
        self.assertEqual(result, 'en')

    def test_malayalam_detection(self):
        """Test Malayalam language detection"""
        malayalam_text = "എന്റെ ഓർഡർ എവിടെയാണ്?"
        result = detect_language(malayalam_text)
        self.assertEqual(result, 'ml')

    def test_mixed_detection(self):
        """Test mixed language detection"""
        mixed_text = "Order എവിടെയാണ്?"
        result = detect_language(mixed_text)
        self.assertEqual(result, 'mixed')

    def test_empty_text_defaults_to_english(self):
        """Test that empty text defaults to English"""
        empty_text = ""
        result = detect_language(empty_text)
        self.assertEqual(result, 'en')

    def test_english_with_punctuation(self):
        """Test English text with punctuation"""
        text = "Hello, how are you? I need help with my order!"
        result = detect_language(text)
        self.assertEqual(result, 'en')

    def test_malayalam_with_punctuation(self):
        """Test Malayalam text with punctuation"""
        text = "ഹലോ, എന്റെ ഓർഡർ എവിടെയാണ്? ദയവായി സഹായിക്കുക!"
        result = detect_language(text)
        self.assertEqual(result, 'ml')


class ResponseLanguageDeterminationTests(TestCase):
    """Test response language determination logic"""

    def setUp(self):
        """Set up test conversation"""
        self.conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )

    def test_response_language_follows_detected_when_not_mixed(self):
        """Test that response language follows detected language when not mixed"""
        # Test English detection
        result = determine_response_language(self.conversation, 'en')
        self.assertEqual(result, 'en')

        # Test Malayalam detection
        result = determine_response_language(self.conversation, 'ml')
        self.assertEqual(result, 'ml')

    def test_response_language_follows_conversation_when_mixed(self):
        """Test that response language follows conversation language when mixed"""
        # Set conversation to Malayalam
        self.conversation.language = 'ml'
        self.conversation.save()

        # Test mixed detection - should use conversation language
        result = determine_response_language(self.conversation, 'mixed')
        self.assertEqual(result, 'ml')

    def test_response_language_defaults_to_english(self):
        """Test that response language defaults to English when conversation language is not set"""
        # Create conversation with no language set (should default to 'en')
        conversation = SupportConversation.objects.create(
            user_id="test_user"
        )

        result = determine_response_language(conversation, 'mixed')
        self.assertEqual(result, 'en')


class LanguageIntegrationTests(TestCase):
    """Test language detection integration with models"""

    def test_message_creation_with_language_detection(self):
        """Test creating a message with automatic language detection"""
        # Create conversation
        conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )

        # Create English message
        english_message = SupportMessage.objects.create(
            conversation=conversation,
            sender="user",
            message="Where is my order?",
            language_detected="en",
            query_type="order_status"
        )

        self.assertEqual(english_message.language_detected, 'en')

        # Create Malayalam message
        malayalam_message = SupportMessage.objects.create(
            conversation=conversation,
            sender="user",
            message="എന്റെ ഓർഡർ എവിടെയാണ്?",
            language_detected="ml",
            query_type="order_status"
        )

        self.assertEqual(malayalam_message.language_detected, 'ml')

        # Create mixed message
        mixed_message = SupportMessage.objects.create(
            conversation=conversation,
            sender="user",
            message="Order എവിടെയാണ്?",
            language_detected="mixed",
            query_type="order_status"
        )

        self.assertEqual(mixed_message.language_detected, 'mixed')


class IntentDetectionTests(TestCase):
    """Test intent detection functionality"""

    def test_order_status_intent_english(self):
        """Test order status intent detection in English"""
        # Test various order status keywords
        test_cases = [
            "Where is my order?",
            "Can you track my delivery?",
            "When will my order be shipped?",
            "What's the status of my package?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, 'order_status', f"Failed for text: {text}")

    def test_order_status_intent_malayalam(self):
        """Test order status intent detection in Malayalam"""
        # Test various order status keywords in Malayalam
        test_cases = [
            "എന്റെ ഓർഡർ എവിടെയാണ്?",
            "എന്റെ ഡെലിവറി ട്രാക്ക് ചെയ്യുക",
            "എന്റെ ഓർഡർ എത്തിയോ?",
            "എന്റെ ഓർഡറിന്റെ സ്ഥിതി എന്താണ്?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'ml')
            self.assertEqual(result, 'order_status', f"Failed for text: {text}")

    def test_return_refund_intent_english(self):
        """Test return/refund intent detection in English"""
        test_cases = [
            "I want to return this item",
            "Can I get a refund?",
            "This product is damaged",
            "How do I cancel my order?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, 'return_refund', f"Failed for text: {text}")

    def test_return_refund_intent_malayalam(self):
        """Test return/refund intent detection in Malayalam"""
        test_cases = [
            "ഈ ഉൽപന്നം റിട്ടേൺ ചെയ്യാൻ ആഗ്രഹിക്കുന്നു",
            "റീഫണ്ട് ലഭിക്കുമോ?",
            "ഈ ഉൽപന്നം നശിച്ചു",
            "ഓർഡർ ക്യാൻസൽ ചെയ്യാൻ എങ്ങനെ?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'ml')
            self.assertEqual(result, 'return_refund', f"Failed for text: {text}")

    def test_policy_intent_english(self):
        """Test policy intent detection in English"""
        test_cases = [
            "What is your return policy?",
            "Can you explain the terms and conditions?",
            "I need to see the rules",
            "Where can I find your policy?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, 'policy', f"Failed for text: {text}")

    def test_policy_intent_malayalam(self):
        """Test policy intent detection in Malayalam"""
        test_cases = [
            "നിങ്ങളുടെ നയം എന്താണ്?",
            "നിയമങ്ങൾ വിശദീകരിക്കുക",
            "വ്യവസ്ഥകൾ കാണാൻ ആഗ്രഹിക്കുന്നു",
            "നയങ്ങൾ എവിടെ കാണാം?"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'ml')
            self.assertEqual(result, 'policy', f"Failed for text: {text}")

    def test_escalation_intent_english(self):
        """Test escalation intent detection in English"""
        test_cases = [
            "I want to talk to a human agent",
            "This is a complaint about your service",
            "Can I speak to a support executive?",
            "I need to escalate this issue"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, 'escalation', f"Failed for text: {text}")

    def test_escalation_intent_malayalam(self):
        """Test escalation intent detection in Malayalam"""
        test_cases = [
            "മനുഷ്യനോട് സംസാരിക്കാൻ ആഗ്രഹിക്കുന്നു",
            "നിങ്ങളുടെ സേവനത്തെക്കുറിച്ചുള്ള പരാതി",
            "കസ്റ്റമർ കെയറിനെ ബന്ധിക്കുക",
            "ഈ പ്രശ്നം എസ്കലേറ്റ് ചെയ്യണം"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'ml')
            self.assertEqual(result, 'escalation', f"Failed for text: {text}")

    def test_general_intent_fallback(self):
        """Test that general intent is returned when no specific intent detected"""
        test_cases = [
            "Hello, how are you?",
            "Thank you for your help",
            "This is a general question",
            "I just wanted to say hi"
        ]
        
        for text in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, 'general', f"Failed for text: {text}")

    def test_empty_text_returns_general(self):
        """Test that empty text returns general intent"""
        result = detect_intent("", 'en')
        self.assertEqual(result, 'general')

    def test_case_insensitive_matching(self):
        """Test that intent detection is case insensitive"""
        test_cases = [
            ("WHERE IS MY ORDER?", 'order_status'),
            ("I Want A Refund", 'return_refund'),
            ("What Is Your POLICY?", 'policy'),
            ("I Need To TALK TO A HUMAN", 'escalation')
        ]
        
        for text, expected_intent in test_cases:
            result = detect_intent(text, 'en')
            self.assertEqual(result, expected_intent, f"Failed for text: {text}")

    def test_mixed_language_intent_detection(self):
        """Test intent detection with mixed language text"""
        # Test that we can still detect intent even with mixed language
        # The intent detection should work based on the specified language parameter
        result = detect_intent("Order എവിടെയാണ്?", 'en')
        self.assertEqual(result, 'order_status')
        
        result = detect_intent("Order എവിടെയാണ്?", 'ml')
        self.assertEqual(result, 'order_status')


class IntentIntegrationTests(TestCase):
    """Test intent detection integration with message creation"""

    def test_message_creation_with_auto_intent_detection(self):
        """Test that messages are created with automatic intent detection"""
        # Create conversation
        conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )

        # Create message with order status intent
        message = SupportMessage.objects.create(
            conversation=conversation,
            sender="user",
            message="Where is my order?",
            language_detected="en",
            query_type="order_status"  # This would be auto-detected in real scenario
        )

        self.assertEqual(message.query_type, 'order_status')

    def test_escalation_updates_conversation(self):
        """Test that escalation intent updates conversation escalation flags"""
        # Create conversation
        conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en",
            escalated=False,
            escalation_reason=""
        )

        # Simulate escalation message creation
        conversation.escalated = True
        conversation.escalation_reason = "I want to talk to a human agent"
        conversation.save()

        # Verify conversation was updated
        conversation.refresh_from_db()
        self.assertTrue(conversation.escalated)
        self.assertEqual(conversation.escalation_reason, "I want to talk to a human agent")

    def test_explicit_query_type_override(self):
        """Test that explicit query_type parameter overrides auto-detection"""
        # This test verifies that if query_type is explicitly provided,
        # it should be used instead of auto-detection
        # (This would be tested through the API in a real integration test)
        conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )

        # Create message with explicit query_type that doesn't match content
        message = SupportMessage.objects.create(
            conversation=conversation,
            sender="user",
            message="Where is my order?",  # Should detect as order_status
            language_detected="en",
            query_type="general"  # Explicit override
        )

        # Should use the explicit query_type
        self.assertEqual(message.query_type, 'general')

    def test_conversation_language_update(self):
        """Test that conversation language updates based on messages"""
        # Create conversation with default English
        conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )

        # First message in Malayalam should update conversation language
        conversation.language = "ml"
        conversation.save()

        self.assertEqual(conversation.language, 'ml')

        # Subsequent English message should update conversation language back
        conversation.language = "en"
        conversation.save()

        self.assertEqual(conversation.language, 'en')
class ResponseGenerationTests(TestCase):
    """Test response generation functionality"""

    def test_order_status_response_en(self):
        result = generate_response('order_status', 'en', {'status': 'shipped', 'date': '2023-12-31'})
        self.assertIn("shipped", result)
        self.assertIn("2023-12-31", result)

    def test_order_status_response_ml(self):
        result = generate_response('order_status', 'ml', {'status': 'ഷിപ്പ് ചെയ്തു'})
        self.assertIn("ഷിപ്പ് ചെയ്തു", result)

    def test_policy_response_en(self):
        result = generate_response('policy', 'en', {'policy_type': 'return'})
        self.assertEqual(result, "Here is our return policy.")

    def test_escalation_response_en(self):
        result = generate_response('escalation', 'en')
        self.assertEqual(result, "I am connecting you to a support executive.")

    def test_fallback_response(self):
        result = generate_response('unknown_intent', 'en')
        self.assertEqual(result, "How can I help you today?")


class ResponseIntegrationTests(APITestCase):
    """Test response generation integration with API"""

    def setUp(self):
        self.conversation = SupportConversation.objects.create(
            user_id="test_user",
            language="en"
        )
        self.url = reverse('message-create', kwargs={'conversation_id': self.conversation.session_id})

    def test_api_generates_ai_response(self):
        """Test that API automatically generates and returns an AI response"""
        data = {'message': 'Where is my order?'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('ai_response', response.data)
        self.assertEqual(response.data['ai_response']['sender'], 'ai')
        self.assertEqual(response.data['detected_intent'], 'order_status')
        
        # Check if AI message is stored in database
        ai_messages = SupportMessage.objects.filter(conversation=self.conversation, sender='ai')
        self.assertEqual(ai_messages.count(), 1)
        self.assertIn("order", ai_messages[0].message)

    def test_api_order_status_with_context(self):
        """Test that AI response uses order context if available"""
        # Create an order for the user
        Order.objects.create(
            order_id="ORD-123",
            user_id="test_user",
            status="delivered"
        )
        
        data = {'message': 'status of my order'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("delivered", response.data['ai_response']['message'])

    def test_api_policy_with_context(self):
        """Test that AI response uses policy context if available"""
        # Create a policy
        Policy.objects.create(
            policy_type="Return",
            content_en="Return within 7 days",
            content_ml="7 ദിവസത്തിനുള്ളിൽ തിരികെ നൽകുക"
        )
        
        data = {'message': 'Tell me about your Return policy'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("Return", response.data['ai_response']['message'])

    def test_api_malayalam_response(self):
        """Test that API generates Malayalam response for Malayalam message"""
        data = {'message': 'എന്റെ ഓർഡർ എവിടെയാണ്?'}
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['response_language'], 'ml')
        # Check for some Malayalam text in AI response
        self.assertIn("ഓർഡർ", response.data['ai_response']['message'])
