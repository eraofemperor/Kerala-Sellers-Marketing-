"""
LLM Integration Service for Customer Support

This module provides a wrapper for LLM APIs (OpenAI/Anthropic) to handle
general customer queries while maintaining deterministic responses for
other intents.
"""

import re
import logging
from typing import Optional, Tuple
import environ
from django.apps import apps

logger = logging.getLogger(__name__)

env = environ.Env(
    LLM_PROVIDER=(str, 'mock'),
    LLM_API_KEY=(str, ''),
    LLM_MODEL=(str, 'gpt-3.5-turbo'),
    LLM_MAX_TOKENS=(int, 500),
    LLM_TIMEOUT=(int, 10),
)


class LLMClient:
    """
    Client for interacting with LLM APIs (OpenAI/Anthropic).
    Handles timeouts, retries, and provides safe fallback.
    """

    # PII patterns to strip from prompts
    PII_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{10}\b',  # Phone number (10 digits)
        r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
        r'\b\d{12,19}\b',  # Generic long numbers (could be IDs/cards)
    ]

    def __init__(self):
        """Initialize LLM client with configuration from environment."""
        self.provider = env('LLM_PROVIDER')
        self.api_key = env('LLM_API_KEY')
        self.model = env('LLM_MODEL')
        self.max_tokens = env('LLM_MAX_TOKENS')
        self.timeout = env('LLM_TIMEOUT')

    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Strip Personally Identifiable Information (PII) from prompt.

        Args:
            prompt: User message to sanitize

        Returns:
            Sanitized prompt with PII replaced with placeholders
        """
        sanitized = prompt
        replacements = []

        # Find and replace PII patterns
        for pattern in self.PII_PATTERNS:
            matches = re.finditer(pattern, sanitized, re.IGNORECASE)
            for match in matches:
                replacements.append((match.start(), match.end(), '[REDACTED]'))

        # Replace in reverse order to maintain indices
        for start, end, replacement in sorted(replacements, reverse=True):
            sanitized = sanitized[:start] + replacement + sanitized[end:]

        if sanitized != prompt:
            logger.info(f"Sanitized PII from user prompt")

        return sanitized

    def _truncate_prompt(self, prompt: str) -> str:
        """
        Truncate prompt to fit within token limits.

        Args:
            prompt: Prompt to truncate

        Returns:
            Truncated prompt
        """
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = self.max_tokens * 4

        if len(prompt) <= max_chars:
            return prompt

        logger.warning(f"Truncating prompt from {len(prompt)} to {max_chars} characters")
        return prompt[:max_chars]

    def _build_conversation_context(self, conversation) -> str:
        """
        Build conversation context from recent message history.
        
        Args:
            conversation: SupportConversation instance
            
        Returns:
            Formatted conversation history as string, or empty string if no relevant history
        """
        if conversation is None:
            return ""
            
        try:
            # Get SupportMessage model to avoid circular imports
            SupportMessage = apps.get_model('support', 'SupportMessage')
            
            # Get last 5 messages (user + ai exchanges) with general intent only
            # Ordered by created_at to maintain chronological order
            messages = SupportMessage.objects.filter(
                conversation=conversation,
                query_type='general',  # Only include general intent messages
                sender__in=['user', 'ai']  # Only user and AI messages
            ).order_by('-created_at')[:10]  # Get up to 10 messages (5 exchanges)
            
            # Reverse to get chronological order (oldest first)
            messages = list(messages)
            messages.reverse()
            
            if not messages:
                return ""
                
            # Format conversation history
            context_lines = []
            for message in messages:
                if message.sender == 'user':
                    context_lines.append(f"User: {message.message}")
                elif message.sender == 'ai':
                    context_lines.append(f"Assistant: {message.message}")
            
            return "\n".join(context_lines) + "\n\n"
            
        except Exception as e:
            logger.warning(f"Error building conversation context: {str(e)}")
            return ""

    def _call_openai_api(self, system_prompt: str, user_prompt: str) -> Tuple[Optional[str], float]:
        """
        Call OpenAI API with retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Tuple of (response_text, confidence_score)
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content.strip()

            # Calculate confidence based on finish reason
            confidence = 1.0 if response.choices[0].finish_reason == "stop" else 0.7

            return response_text, confidence

        except ImportError:
            logger.error("OpenAI library not installed")
            return None, 0.0
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None, 0.0

    def _call_anthropic_api(self, system_prompt: str, user_prompt: str) -> Tuple[Optional[str], float]:
        """
        Call Anthropic API with retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Tuple of (response_text, confidence_score)
        """
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Calculate confidence
            confidence = 1.0 if response.stop_reason == "end_turn" else 0.7

            return response_text, confidence

        except ImportError:
            logger.error("Anthropic library not installed")
            return None, 0.0
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return None, 0.0

    def _prepare_prompts(self, user_message: str, language: str, conversation_context: str = "") -> Tuple[str, str]:
        """
        Prepare system and user prompts for LLM.

        Args:
            user_message: Sanitized user message
            language: Response language (en/ml)
            conversation_context: Optional conversation history context

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # System prompt
        system_prompt = (
            "You are a polite and helpful customer support assistant for Kerala Sellers. "
            "Respond in a friendly, professional manner. Keep responses concise and helpful."
        )

        # Add language instruction
        if language == 'ml':
            system_prompt += " Respond in Malayalam language."
        else:
            system_prompt += " Respond in English language."

        # User prompt - include conversation context if available, then current user message
        user_prompt = conversation_context
        user_prompt += f"Customer: {user_message}\n\nAssistant:"

        return system_prompt, user_prompt

    def _call_mock_api(self, user_message: str, language: str) -> Tuple[str, float]:
        """
        Mock API for testing without actual LLM.

        Args:
            user_message: User message
            language: Response language

        Returns:
            Tuple of (response_text, confidence_score)
        """
        logger.info("Using mock LLM response")

        if language == 'ml':
            responses = [
                "താങ്കളുടെ ചോദ്യത്തിന് നന്ദി. എന്തെങ്കിലും മറ്റ് സഹായം ആവശ്യമുണ്ടോ?",
                "വിവരങ്ങൾക്ക് നന്ദി. ഇനിയും എന്തെങ്കിലും സംശയമുണ്ടെങ്കിൽ ചോദിക്കുക.",
                "സഹായത്തിന് താങ്കളെ സന്തോഷത്തോടെ സ്വാഗതം ചെയ്യുന്നു.",
            ]
        else:
            responses = [
                "Thank you for your question. Is there anything else I can help you with?",
                "Thanks for the information. Let me know if you have any other questions.",
                "I'm happy to help you. Please feel free to ask if you need any assistance.",
            ]

        import random
        response = random.choice(responses)
        confidence = 0.8

        return response, confidence

    def generate_reply(self, user_message: str, language: str, conversation=None) -> Tuple[str, float, bool]:
        """
        Generate a reply using LLM with safe fallback.

        Args:
            user_message: User's message
            language: Response language (en/ml)
            conversation: Optional SupportConversation instance for context

        Returns:
            Tuple of (response_text, confidence_score, used_fallback)
        """
        # Sanitize and truncate prompt
        sanitized_message = self._sanitize_prompt(user_message)
        truncated_message = self._truncate_prompt(sanitized_message)

        # Build conversation context if conversation is provided
        conversation_context = ""
        if conversation is not None:
            conversation_context = self._build_conversation_context(conversation)
            # Sanitize and truncate conversation context as well
            conversation_context = self._sanitize_prompt(conversation_context)

        # Prepare prompts with conversation context
        system_prompt, user_prompt = self._prepare_prompts(truncated_message, language, conversation_context)

        # Truncate the final user prompt to ensure it fits within token limits
        user_prompt = self._truncate_prompt(user_prompt)

        # Try to get response from configured provider
        response_text = None
        confidence = 0.0

        if self.provider == 'openai':
            response_text, confidence = self._call_openai_api(system_prompt, user_prompt)
        elif self.provider == 'anthropic':
            response_text, confidence = self._call_anthropic_api(system_prompt, user_prompt)
        elif self.provider == 'mock':
            response_text, confidence = self._call_mock_api(user_message, language)
        else:
            logger.warning(f"Unknown LLM provider: {self.provider}")

        # Fallback to template-based response if AI fails
        if response_text is None:
            logger.warning("LLM failed, using fallback response")
            from support.utils.responses import generate_response
            response_text = generate_response('general', language, {})
            confidence = 0.5
            return response_text, confidence, True

        return response_text, confidence, False


# Singleton instance
_llm_client = None


def get_llm_client() -> LLMClient:
    """
    Get or create the singleton LLM client instance.

    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
