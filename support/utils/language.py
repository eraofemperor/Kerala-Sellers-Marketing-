import re
from typing import Tuple


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        str: Language code - 'en' (English), 'ml' (Malayalam), or 'mixed' (mixed)
        
    Language Detection Rules:
        - English only: Contains only ASCII characters (basic English)
        - Malayalam only: Contains Malayalam Unicode characters but no ASCII letters
        - Mixed: Contains both Malayalam Unicode and ASCII letters
        - Unknown/unsupported: Default to 'en'
    """
    if not text or not text.strip():
        return 'en'
    
    # Malayalam Unicode ranges
    # Malayalam script ranges in Unicode
    malayalam_ranges = [
        (0x0D00, 0x0D7F),  # Malayalam block
        (0x200C, 0x200D),  # Zero width non-joiner and joiner (used in Indic scripts)
    ]
    
    has_malayalam = False
    has_ascii_letters = False
    
    for char in text:
        char_code = ord(char)
        
        # Check if character is in Malayalam Unicode ranges
        for start, end in malayalam_ranges:
            if start <= char_code <= end:
                has_malayalam = True
                break
        
        # Check if character is ASCII letter (a-z, A-Z)
        if (0x41 <= char_code <= 0x5A) or (0x61 <= char_code <= 0x7A):
            has_ascii_letters = True
    
    # Determine language based on detection
    if has_malayalam and has_ascii_letters:
        return 'mixed'
    elif has_malayalam:
        return 'ml'
    elif has_ascii_letters:
        return 'en'
    else:
        # No letters detected, default to English
        return 'en'


def determine_response_language(conversation, detected_language: str) -> str:
    """
    Determine the appropriate response language based on conversation context and detected language.
    
    Args:
        conversation: SupportConversation instance
        detected_language: Language detected from current message
        
    Returns:
        str: Language code to use for response
        
    Priority order:
        1. Explicit user preference (if set later - not implemented yet, so skip)
        2. Current message language
        3. Conversation default language
    """
    # For now, we don't have explicit user preference, so we use:
    # 1. Current message language (if it's not mixed)
    # 2. Conversation default language
    
    if detected_language in ['en', 'ml']:
        return detected_language
    else:
        # For mixed or unknown, use conversation default
        return conversation.language if conversation.language else 'en'