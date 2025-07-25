# config/duplicate_patterns.py
"""
Configuration patterns for duplicate detection and transaction classification
"""

# Credit card payment patterns - these indicate a payment TO a credit card
CREDIT_CARD_PAYMENT_PATTERNS = [
    r'payment\s+thank\s+you',
    r'online\s+payment',
    r'autopay',
    r'automatic\s+payment',
    r'credit\s+card\s+payment',
    r'cc\s+payment',
    r'electronic\s+payment',
    r'web\s+payment',
    r'mobile\s+payment',
    r'bill\s+pay',
    r'billpay',
    r'payment\s+to\s+.*credit',
    r'payment\s+to\s+.*card',
    r'chase\s+credit\s+crd',
    r'discover\s+payment',
    r'capital\s+one\s+payment',
    r'citi\s+payment',
    r'amex\s+payment',
    r'american\s+express\s+payment'
]

# Transfer patterns - these indicate money movement between accounts
TRANSFER_PATTERNS = [
    r'transfer\s+to',
    r'transfer\s+from',
    r'internal\s+transfer',
    r'account\s+transfer',
    r'online\s+transfer',
    r'mobile\s+transfer',
    r'wire\s+transfer',
    r'ach\s+transfer',
    r'zelle\s+transfer',
    r'quickpay\s+transfer',
    r'person\s+to\s+person',
    r'p2p\s+transfer',
    r'venmo\s+transfer',
    r'paypal\s+transfer',
    r'cash\s+app\s+transfer'
]

# Patterns that indicate potential duplicates across different account types
CROSS_ACCOUNT_DUPLICATE_INDICATORS = {
    'credit_card_purchases': [
        r'amazon',
        r'walmart',
        r'target',
        r'starbucks',
        r'mcdonalds',
        r'gas\s+station',
        r'grocery',
        r'restaurant',
        r'retail',
        r'online\s+purchase'
    ],
    
    'recurring_payments': [
        r'netflix',
        r'spotify',
        r'hulu',
        r'disney',
        r'subscription',
        r'monthly\s+fee',
        r'annual\s+fee',
        r'membership',
        r'insurance',
        r'utility',
        r'rent',
        r'mortgage'
    ],
    
    'fee_transactions': [
        r'overdraft\s+fee',
        r'maintenance\s+fee',
        r'atm\s+fee',
        r'foreign\s+transaction\s+fee',
        r'late\s+fee',
        r'service\s+charge',
        r'processing\s+fee'
    ]
}

# Bank-specific patterns for better identification
BANK_SPECIFIC_PATTERNS = {
    'chase': {
        'credit_card_payment': r'chase\s+credit\s+crd.*payment',
        'transfer': r'chase\s+quickpay',
        'fee': r'chase\s+.*fee'
    },
    'wells_fargo': {
        'credit_card_payment': r'wells\s+fargo.*payment',
        'transfer': r'surepay',
        'fee': r'wells\s+fargo.*fee'
    },
    'bank_of_america': {
        'credit_card_payment': r'boa.*payment|bank\s+of\s+america.*payment',
        'transfer': r'boa\s+transfer',
        'fee': r'boa.*fee'
    }
}

# Merchant normalization patterns
MERCHANT_NORMALIZATION = {
    # Remove location codes and store numbers
    r'#\d+': '',
    r'\d{3,4}\s*$': '',  # Remove trailing store numbers
    r'^(\d{2,4})\s+': '',  # Remove leading store numbers
    
    # Standardize common merchants
    r'amazon\.com.*': 'amazon',
    r'amzn\s+mktp.*': 'amazon',
    r'walmart\s+#\d+': 'walmart',
    r'target\s+#\d+': 'target',
    r'starbucks\s+#\d+': 'starbucks',
    r'mcdonalds\s+#\d+': 'mcdonalds',
    
    # Remove common prefixes/suffixes
    r'^(pos|debit|credit)\s+': '',
    r'\s+(purchase|payment|transaction)$': '',
    r'^www\.': '',
    r'\.com.*$': ''
}

# Thresholds for duplicate detection
DUPLICATE_DETECTION_THRESHOLDS = {
    'exact_match': {
        'date_window_days': 0,  # Must be same day
        'amount_tolerance_percent': 0,  # Must be exact amount
        'description_similarity_min': 100  # Must be identical
    },
    
    'fuzzy_match': {
        'date_window_days': 3,  # Within 3 days
        'amount_tolerance_percent': 1,  # Within 1%
        'description_similarity_min': 70  # 70% similar description
    },
    
    'credit_card_payment_match': {
        'date_window_days': 45,  # Credit card billing cycle
        'amount_tolerance_percent': 10,  # Within 10% (for multiple purchases)
        'description_similarity_min': 0  # Amount-based matching
    },
    
    'transfer_match': {
        'date_window_days': 1,  # Same or next day
        'amount_tolerance_percent': 0,  # Must be exact
        'description_similarity_min': 50  # Looser description matching
    }
}

# Categories to exclude from certain duplicate checks
EXCLUDE_FROM_DUPLICATE_CHECKS = {
    'income_categories': ['Income', 'Salary', 'Deposit', 'Refund'],
    'fee_categories': ['Banking & Fees', 'ATM Fee', 'Service Charge'],
    'investment_categories': ['Investment', 'Dividend', 'Interest']
}

# Rules for handling duplicate resolution
DUPLICATE_RESOLUTION_RULES = {
    'credit_card_vs_bank': 'keep_payment',  # Keep the payment, remove individual charges
    'transfer_duplicates': 'keep_first',    # Keep first occurrence
    'exact_duplicates': 'keep_first',       # Keep first occurrence
    'fuzzy_duplicates': 'manual_review'     # Flag for manual review
}