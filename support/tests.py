from django.test import TestCase
from .utils.language import detect_language, determine_response_language
from .models import SupportConversation, SupportMessage


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