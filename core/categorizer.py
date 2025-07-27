# core/categorizer.py

import re
import logging
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from fuzzywuzzy import fuzz
from config import categories
from config.patterns import MERCHANT_PATTERNS

# Set up logging
logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Transaction categorizer with improved accuracy and performance.
    """
    
    def __init__(self):
        self.category_patterns = self._compile_patterns()
        self.custom_rules = {}
        self.learning_data = {}
        self.regex_cache = {}
        self._compile_regex_cache()
        
        # Precompiled high-priority patterns for better performance
        self._compile_priority_patterns()

    def _compile_patterns(self) -> Dict[str, List[str]]:
        """Compile all category keywords into searchable patterns with validation."""
        patterns = {}
        
        if not hasattr(categories, 'SPENDING_CATEGORIES'):
            logger.warning("SPENDING_CATEGORIES not found in config.categories")
            return {}
            
        for category, subcategories in categories.SPENDING_CATEGORIES.items():
            all_keywords = []
            
            if isinstance(subcategories, dict):
                for subcat_keywords in subcategories.values():
                    if isinstance(subcat_keywords, list):
                        all_keywords.extend(subcat_keywords)
                    else:
                        logger.warning(f"Invalid subcategory format in {category}")
            elif isinstance(subcategories, list):
                all_keywords = subcategories
            else:
                logger.warning(f"Invalid category format: {category}")
                continue
                
            # Clean and validate keywords
            clean_keywords = []
            for kw in all_keywords:
                if isinstance(kw, str) and kw.strip():
                    clean_keywords.append(kw.lower().strip())
                    
            patterns[category] = clean_keywords
            
        return patterns

    def _compile_regex_cache(self):
        """Precompile regex patterns for faster matching with error handling."""
        self.regex_cache = {}
        
        for category, keywords in self.category_patterns.items():
            compiled_patterns = []
            for kw in keywords:
                try:
                    # Use word boundaries for more precise matching
                    pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
                    compiled_patterns.append(pattern)
                except re.error as e:
                    logger.warning(f"Failed to compile regex for keyword '{kw}': {e}")
                    
            self.regex_cache[category] = compiled_patterns

    def _compile_priority_patterns(self):
        """Compile high-priority patterns for special transaction types."""
        try:
            # Income patterns (positive amounts)
            self.income_patterns = re.compile(
                r'\b(deposit|payroll|salary|refund|reversal|return|credit|direct\s+deposit|'
                r'dividend|interest\s+earned|payment\s+received|reimbursement)\b',
                re.IGNORECASE
            )
            
            # Transfer patterns
            self.transfer_patterns = re.compile(
                r'\b(transfer|zelle|venmo|cash\s+app|paypal\s+transfer|wire\s+transfer|'
                r'p2p|person\s+to\s+person)\b',
                re.IGNORECASE
            )
            
            # Credit card payment patterns
            self.cc_payment_patterns = re.compile(
                r'\b(payment\s+thank\s+you|online\s+payment|autopay|automatic\s+payment|'
                r'credit\s+card\s+payment|cc\s+payment|electronic\s+payment)\b',
                re.IGNORECASE
            )
            
            # Fee patterns
            self.fee_patterns = re.compile(
                r'\b(fee|charge|overdraft|maintenance|service\s+charge|wire\s+fee|'
                r'atm\s+fee|late\s+fee)\b',
                re.IGNORECASE
            )
            
        except re.error as e:
            logger.error(f"Failed to compile priority patterns: {e}")
            # Create dummy patterns that won't match anything
            self.income_patterns = re.compile(r'(?!.*)', re.IGNORECASE)
            self.transfer_patterns = re.compile(r'(?!.*)', re.IGNORECASE)
            self.cc_payment_patterns = re.compile(r'(?!.*)', re.IGNORECASE)
            self.fee_patterns = re.compile(r'(?!.*)', re.IGNORECASE)

    def normalize_merchant_name(self, description: str) -> str:
        """
        Normalize merchant names using regex patterns with error handling.
        """
        if not isinstance(description, str):
            return str(description) if description is not None else ""
            
        description = description.strip()
        
        # Apply merchant-specific patterns
        if hasattr(MERCHANT_PATTERNS, '__iter__'):
            for pattern, replacement in MERCHANT_PATTERNS.items():
                try:
                    description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
                except re.error as e:
                    logger.warning(f"Regex error with pattern '{pattern}': {e}")
                    continue

        # Remove common prefixes/suffixes
        cleanup_patterns = [
            (r'^(DEBIT\s+CARD|CREDIT\s+CARD|ONLINE|WEB)\s+', ''),
            (r'\s+(PAYMENT|PURCHASE|TRANSACTION)$', ''),
            (r'#\d+', ''),  # Remove store numbers
            (r'\d{3,4}\s*$', ''),  # Remove trailing numbers
            (r'^\d{2,4}\s+', ''),  # Remove leading numbers
        ]
        
        for pattern, replacement in cleanup_patterns:
            try:
                description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Cleanup regex error: {e}")
                continue

        return description.strip()

    def fuzzy_match_merchant(self, description: str, threshold: int = 85) -> Optional[str]:
        """
        Use fuzzy matching to identify known merchants with improved accuracy.
        """
        if not isinstance(description, str) or not description.strip():
            return None
            
        if not (0 <= threshold <= 100):
            threshold = 85
            
        desc_lower = description.lower()

        # known merchants database
        known_merchants = {
            # Online/Tech
            'amazon': 'Shopping',
            'amzn': 'Shopping',
            'apple': 'Electronics',
            'microsoft': 'Electronics', 
            'google': 'Electronics',
            'paypal': 'Transfer',
            
            # Retail
            'walmart': 'Groceries',
            'target': 'Shopping',
            'costco': 'Groceries',
            'best buy': 'Electronics',
            'home depot': 'Shopping',
            'lowes': 'Shopping',
            
            # Food
            'starbucks': 'Food & Dining',
            'mcdonalds': 'Food & Dining',
            'subway': 'Food & Dining',
            'chipotle': 'Food & Dining',
            'pizza': 'Food & Dining',
            
            # Gas/Transportation
            'shell': 'Transportation',
            'exxon': 'Transportation',
            'chevron': 'Transportation',
            'bp': 'Transportation',
            'uber': 'Transportation',
            'lyft': 'Transportation',
            
            # Entertainment
            'netflix': 'Entertainment',
            'spotify': 'Entertainment',
            'hulu': 'Entertainment',
            'disney': 'Entertainment',
            
            # Healthcare/Pharmacy
            'walgreens': 'Healthcare',
            'cvs': 'Healthcare',
            'rite aid': 'Healthcare',
            'pharmacy': 'Healthcare',
        }

        best_match = None
        best_score = 0
        
        for merchant, category in known_merchants.items():
            # Try both partial and token sort ratios for better matching
            partial_score = fuzz.partial_ratio(merchant, desc_lower)
            token_score = fuzz.token_sort_ratio(merchant, desc_lower)
            
            # Take the higher of the two scores
            score = max(partial_score, token_score)
            
            if score >= threshold and score > best_score:
                best_score = score
                best_match = category

        return best_match

    def categorize_by_amount(self, amount: float, description: str) -> Optional[str]:
        """
        Suggest categories based on transaction amount with improved logic.
        """
        try:
            abs_amount = abs(float(amount))
        except (ValueError, TypeError):
            return None
            
        if not isinstance(description, str):
            description = str(description) if description is not None else ""
            
        desc_lower = description.lower()

        # Very small amounts (under $5)
        if abs_amount < 5.00:
            if self.fee_patterns.search(desc_lower):
                return 'Banking & Fees'
            elif any(word in desc_lower for word in ['coffee', 'drink', 'snack']):
                return 'Food & Dining'
            elif 'tip' in desc_lower:
                return 'Food & Dining'

        # Medium amounts ($5-50) - common purchases
        elif 5.00 <= abs_amount <= 50.00:
            if any(word in desc_lower for word in ['gas', 'fuel', 'station']):
                return 'Transportation'
            elif any(word in desc_lower for word in ['grocery', 'food', 'market']):
                return 'Groceries'

        # Large amounts (over $1000)
        elif abs_amount > 1000.00:
            if any(word in desc_lower for word in ['rent', 'mortgage', 'property']):
                return 'Bills & Utilities'
            elif any(word in desc_lower for word in ['hospital', 'medical', 'surgery', 'emergency']):
                return 'Healthcare'
            elif any(word in desc_lower for word in ['tuition', 'university', 'college']):
                return 'Education'

        return None

    def categorize_by_timing(self, description: str, date: datetime) -> Optional[str]:
        """
        Categorize based on timing patterns with validation.
        """
        if not isinstance(date, datetime) or not isinstance(description, str):
            return None

        desc_lower = description.lower()

        # Weekend transactions (Friday evening through Sunday)
        if date.weekday() >= 4:  # Friday=4, Saturday=5, Sunday=6
            weekend_indicators = ['restaurant', 'bar', 'movie', 'entertainment', 'game', 'theater']
            if any(word in desc_lower for word in weekend_indicators):
                return 'Entertainment'

        # Early morning transactions (likely automated)
        if date.hour < 6:
            if any(word in desc_lower for word in ['autopay', 'automatic', 'recurring', 'bill']):
                return 'Bills & Utilities'

        return None

    def multi_pass_categorization(self, description: str, amount: float, date: datetime = None) -> str:
        """
            categorization using multiple passes with improved error handling.
        """
        try:
            amount = float(amount) if amount is not None else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount value: {amount}")
            amount = 0.0

        if not isinstance(description, str):
            description = str(description) if description is not None else ""

        # Step 1: Normalize description
        normalized_desc = self.normalize_merchant_name(description)
        desc_lower = normalized_desc.lower()

        # Step 2: Income detection (positive amounts)
        if amount > 0:
            if self.income_patterns.search(desc_lower):
                return 'Income'

        # Step 3: Handle credit card payments (negative amounts)
        if amount < 0 and self.cc_payment_patterns.search(desc_lower):
            return 'Bills & Utilities'

        # Step 4: Handle transfers
        if self.transfer_patterns.search(desc_lower):
            return 'Transfer'

        # Step 5: Handle fees
        if self.fee_patterns.search(desc_lower):
            return 'Banking & Fees'

        # Step 6: Try fuzzy matching for known merchants
        fuzzy_category = self.fuzzy_match_merchant(normalized_desc)
        if fuzzy_category:
            return fuzzy_category

        # Step 7: Amount-based categorization
        amount_category = self.categorize_by_amount(amount, normalized_desc)
        if amount_category:
            return amount_category

        # Step 8: Timing-based categorization
        if date:
            timing_category = self.categorize_by_timing(normalized_desc, date)
            if timing_category:
                return timing_category

        # Step 9: Optimized keyword matching with scoring
        category_scores = {}
        for category, regex_list in self.regex_cache.items():
            score = 0
            for regex in regex_list:
                try:
                    matches = regex.findall(desc_lower)
                    # Score based on number of matches and keyword importance
                    score += len(matches) * 10
                except Exception as e:
                    logger.warning(f"Regex search error: {e}")
                    continue
                    
            if score > 0:
                category_scores[category] = score

        # Return highest scoring category
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]

        return 'Other'

    def add_custom_rule(self, keyword: str, category: str):
        """Add a custom rule for categorization with validation."""
        if not isinstance(keyword, str) or not isinstance(category, str):
            logger.warning("Invalid custom rule: keyword and category must be strings")
            return
            
        if not keyword.strip() or not category.strip():
            logger.warning("Invalid custom rule: keyword and category cannot be empty")
            return
            
        self.custom_rules[keyword.lower().strip()] = category.strip()

    def learn_from_feedback(self, description: str, category: str):
        """Store learning data from user feedback with validation."""
        if not isinstance(description, str) or not isinstance(category, str):
            logger.warning("Invalid feedback: description and category must be strings")
            return
            
        if not description.strip() or not category.strip():
            logger.warning("Invalid feedback: description and category cannot be empty")
            return
            
        self.learning_data[description.lower().strip()] = category.strip()

    def get_category_confidence(self, description: str, amount: float, date: datetime = None) -> Tuple[str, float]:
        """
        Get category with confidence score.
        Returns tuple of (category, confidence_score) where confidence is 0.0-1.0
        """
        # This is a simplified confidence calculation
        # In a real implementation, you might train a model to predict confidence
        
        category = self.multi_pass_categorization(description, amount, date)
        
        # Simple confidence heuristic
        confidence = 0.5  # Default confidence
        
        # Higher confidence for exact merchant matches
        if self.fuzzy_match_merchant(description, threshold=95):
            confidence = 0.9
        # Medium confidence for fuzzy matches
        elif self.fuzzy_match_merchant(description, threshold=75):
            confidence = 0.7
        # Lower confidence for keyword-only matches
        elif category != 'Other':
            confidence = 0.6
        else:
            confidence = 0.3
            
        return category, confidence


def categorize_transaction(description: str, amount: float, date: datetime = None) -> str:
    """
    Public function to categorize a transaction.
    
    Args:
        description: Transaction description
        amount: Transaction amount (negative for expenses, positive for income)
        date: Transaction date (optional)
        
    Returns:
        Category name as string
    """
    try:
        categorizer = TransactionCategorizer()
        return categorizer.multi_pass_categorization(description, amount, date)
    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        return 'Other'


def categorize_transaction_with_confidence(description: str, amount: float, date: datetime = None) -> Tuple[str, float]:
    """
    Public function to categorize a transaction with confidence score.
    
    Args:
        description: Transaction description
        amount: Transaction amount (negative for expenses, positive for income) 
        date: Transaction date (optional)
        
    Returns:
        Tuple of (category, confidence_score)
    """
    try:
        categorizer = TransactionCategorizer()
        return categorizer.get_category_confidence(description, amount, date)
    except Exception as e:
        logger.error(f"Error categorizing transaction: {e}")
        return 'Other', 0.0