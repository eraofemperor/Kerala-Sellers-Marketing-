
def generate_response(intent, language, context=None):
    """
    Generate a response based on intent and language using predefined templates.
    
    Args:
        intent (str): Detected intent (order_status, return_refund, policy, escalation, general)
        language (str): Response language (en, ml)
        context (dict, optional): Context data for template formatting
        
    Returns:
        str: Formatted response message
    """
    if context is None:
        context = {}

    templates = {
        'en': {
            'order_status': "Your order is currently {status}. Expected delivery: {date}.",
            'return_refund': "You can request a return within 7 days of delivery.",
            'policy': "Here is our {policy_type} policy.",
            'escalation': "I am connecting you to a support executive.",
            'general': "How can I help you today?"
        },
        'ml': {
            'order_status': "നിങ്ങളുടെ ഓർഡർ നിലവിൽ {status} ആണ്.",
            'return_refund': "ഡെലിവറി കഴിഞ്ഞ് 7 ദിവസത്തിനുള്ളിൽ റിട്ടേൺ അഭ്യർത്ഥിക്കാം.",
            'policy': "{policy_type} നയം ഇതാണ്.",
            'escalation': "നിങ്ങളെ കസ്റ്റമർ കെയറുമായി ബന്ധിപ്പിക്കുന്നു.",
            'general': "എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാം?"
        }
    }

    # Default to English if language not supported
    lang_templates = templates.get(language, templates['en'])
    
    # Get template for intent, fallback to general
    template = lang_templates.get(intent, lang_templates['general'])

    # Default context values for placeholders
    default_context = {
        'status': 'being processed' if language == 'en' else 'പ്രോസസ്സ് ചെയ്യുന്നു',
        'date': 'soon' if language == 'en' else 'ഉടൻ',
        'policy_type': 'general' if language == 'en' else 'പൊതുവായ'
    }

    # Merge default context with provided context
    full_context = {**default_context, **context}

    try:
        return template.format(**full_context)
    except KeyError:
        # If formatting fails, return the template itself or a very basic fallback
        return template
