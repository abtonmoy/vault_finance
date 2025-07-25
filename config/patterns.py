#Chase-specific patterns
CHASE_PATTERNS = {
    'date_patterns': [
        r'\b(\d{1,2}/\d{1,2})\b',  # MM/DD or M/D
        r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',  # MM/DD/YY or MM/DD/YYYY
        r'\b([A-Za-z]{3}\s+\d{1,2})\b',  # Jan 15
        r'\b(\w{3,9}\s+\d{1,2},?\s*\d{2,4}?)\b'  # January 15, 2024
    ],
    'amount_patterns': [
        r'(?:^|\s)(\$?\-?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)',  # $1,234.56
        r'(?:^|\s)(\(\$?\d{1,3}(?:,\d{3})*\.\d{2}\))(?:\s|$)',  # ($1,234.56)
        r'(?:^|\s)(\-\$?\d{1,3}(?:,\d{3})*\.\d{2})(?:\s|$)'     # -$1,234.56
    ]
}

# Merchant name normalization patterns
MERCHANT_PATTERNS = {
    r'AMAZON\.COM\*\w+': 'Amazon',
    r'AMZN\s+MKTP': 'Amazon',
    r'WAL-MART.*': 'Walmart',
    r'TARGET\s+\d+': 'Target',
    r'STARBUCKS.*': 'Starbucks',
    r'MCDONALD\'S.*': 'McDonald\'s',
    r'TST\*\s*(.+)': r'\1',  # Remove TST* prefix
    r'SQ\*\s*(.+)': r'\1',   # Remove Square prefix
    r'\d{4}\s+(.+)': r'\1',  # Remove leading numbers
}