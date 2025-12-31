import re
from typing import Dict, List


# Intent keywords mapping for English and Malayalam
INTENT_KEYWORDS = {
    'order_status': {
        'en': ['order', 'track', 'delivery', 'shipped', 'status', 'where'],
        'ml': ['ഓർഡർ', 'ട്രാക്ക്', 'ഡെലിവറി', 'എത്തിയോ', 'സ്ഥിതി', 'എവിടെയാണ്']
    },
    'return_refund': {
        'en': ['return', 'refund', 'replace', 'damaged', 'cancel'],
        'ml': ['റിട്ടേൺ', 'റീഫണ്ട്', 'തിരികെ', 'നശിച്ചു', 'ക്യാൻസൽ']
    },
    'policy': {
        'en': ['policy', 'rules', 'terms', 'conditions'],
        'ml': ['നയം', 'നയങ്ങൾ', 'നിയമങ്ങൾ', 'വ്യവസ്ഥകൾ']
    },
    'escalation': {
        'en': ['complaint', 'talk to agent', 'human', 'support executive', 'escalate'],
        'ml': ['പരാതി', 'മനുഷ്യൻ', 'മനുഷ്യനോട്', 'കസ്റ്റമർ കെയർ', 'കസ്റ്റമർ കെയറിനെ', 'എസ്കലേറ്റ്']
    }
}


def detect_intent(text: str, language: str = 'en') -> str:
    """
    Detect the intent of the given text using rule-based keyword matching.
    
    Args:
        text: Input text to analyze
        language: Language of the text ('en' for English, 'ml' for Malayalam)
        
    Returns:
        str: Intent type - one of 'order_status', 'return_refund', 'policy', 
             'escalation', or 'general' (fallback)
        
    Intent Detection Rules:
        - Order Status: Contains order/delivery tracking keywords
        - Return/Refund: Contains return/refund/cancellation keywords  
        - Policy: Contains policy/terms/conditions keywords
        - Escalation: Contains complaint/human agent keywords
        - General: Fallback if no specific intent detected
    """
    if not text or not text.strip():
        return 'general'
    
    # Normalize language input
    language = language.lower()
    if language not in ['en', 'ml']:
        language = 'en'  # Default to English if unknown
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check intents in priority order (more specific intents first)
    # Priority: escalation > policy > return_refund > order_status > general
    
    # 1. Check for escalation intent first (most specific)
    escalation_keywords = INTENT_KEYWORDS['escalation'].get(language, [])
    for keyword in escalation_keywords:
        if keyword.lower() in text_lower:
            return 'escalation'
    
    # 2. Check for policy intent
    policy_keywords = INTENT_KEYWORDS['policy'].get(language, [])
    for keyword in policy_keywords:
        if keyword.lower() in text_lower:
            return 'policy'
    
    # 3. Check for return/refund intent
    return_keywords = INTENT_KEYWORDS['return_refund'].get(language, [])
    for keyword in return_keywords:
        if keyword.lower() in text_lower:
            return 'return_refund'
    
    # 4. Check for order status intent
    order_keywords = INTENT_KEYWORDS['order_status'].get(language, [])
    for keyword in order_keywords:
        if keyword.lower() in text_lower:
            return 'order_status'
    
    # 5. If no specific intent detected, return general
    return 'general'