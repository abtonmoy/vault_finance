import re
from collections import Counter
from datetime import datetime
from fuzzywuzzy import fuzz
from config import categories
from typing import Dict, List, Optional

class TransactionCategorizer:
    def __init__(self):
        self.category_patterns = self._compile_patterns()
        self.custom_rules = {}
        self.learning_data = {}
    
    def _compile_patterns(self) -> Dict[str, List[str]]:
        """Compile all category keywords into searchable patterns"""
        patterns = {}
        for category, subcategories in categories.SPENDING_CATEGORIES.items():
            all_keywords = []
            if isinstance(subcategories, dict):
                for subcat_keywords in subcategories.values():
                    all_keywords.extend(subcat_keywords)
            else:
                all_keywords = subcategories
            patterns[category] = [kw.lower() for kw in all_keywords]
        return patterns
    
    def normalize_merchant_name(self, description: str) -> str:
        """Normalize merchant names using regex patterns"""
        description = description.strip()
        
        for pattern, replacement in pattern.MERCHANT_PATTERNS.items():
            description = re.sub(pattern, replacement, description, flags=re.IGNORECASE)
        
        # Remove common prefixes/suffixes
        description = re.sub(r'^(DEBIT CARD|CREDIT CARD|ONLINE|WEB)\s+', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\s+(PAYMENT|PURCHASE|TRANSACTION)$', '', description, flags=re.IGNORECASE)
        
        return description.strip()
    
    def fuzzy_match_merchant(self, description: str, threshold: int = 80) -> Optional[str]:
        """Use fuzzy matching to identify known merchants"""
        desc_lower = description.lower()
        
        known_merchants = {
            'amazon': 'Shopping',
            'walmart': 'Groceries',
            'target': 'Shopping',
            'starbucks': 'Food & Dining',
            'mcdonalds': 'Food & Dining',
            'shell': 'Transportation',
            'exxon': 'Transportation',
            'netflix': 'Entertainment',
            'spotify': 'Entertainment'
        }
        
        for merchant, category in known_merchants.items():
            if fuzz.partial_ratio(merchant, desc_lower) >= threshold:
                return category
        
        return None
    
    def categorize_by_amount(self, amount: float, description: str) -> Optional[str]:
        """Suggest categories based on transaction amount"""
        abs_amount = abs(amount)
        
        # Very small amounts are likely coffee, snacks, or fees
        if abs_amount < 5.00:
            if any(word in description.lower() for word in ['fee', 'charge', 'maintenance']):
                return 'Banking & Fees'
            elif any(word in description.lower() for word in ['coffee', 'starbucks', 'dunkin']):
                return 'Food & Dining'
        
        # Large amounts might be rent, major purchases
        elif abs_amount > 1000.00:
            if any(word in description.lower() for word in ['rent', 'mortgage', 'property']):
                return 'Bills & Utilities'
            elif any(word in description.lower() for word in ['hospital', 'medical', 'surgery']):
                return 'Healthcare'
        
        return None
    
    def categorize_by_timing(self, description: str, date: datetime) -> Optional[str]:
        """Categorize based on timing patterns"""
        if date is None:
            return None
            

        '''
        have to fix it; ajaira assumption
        '''
        # Weekend transactions more likely to be entertainment/dining
        if date.weekday() >= 5:  # Saturday or Sunday
            if any(word in description.lower() for word in ['restaurant', 'bar', 'movie', 'game']):
                return 'Entertainment'
        
        # Recurring monthly transactions likely bills
        if any(word in description.lower() for word in ['autopay', 'automatic', 'recurring']):
            return 'Bills & Utilities'
        
        return None
    
    def multi_pass_categorization(self, description: str, amount: float, date: datetime = None) -> str:
        """Enhanced categorization using multiple passes"""
        
        # Step 1: Normalize description
        normalized_desc = self.normalize_merchant_name(description)
        desc_lower = normalized_desc.lower()
        
        # Step 2: Income detection (positive amounts) - Moved up to handle first
        if amount > 0:
            income_keywords = ['deposit', 'payroll', 'salary', 'refund', 'reversal', 
                            'return', 'credit', 'direct deposit', 'dividend', 
                            'interest earned', 'payment received', 'reimbursement']
            if any(kw in desc_lower for kw in income_keywords):
                return 'Income'

        # Step 3: Handle credit card payments (negative amounts)
        credit_card_keywords = [
            'payment thank you', 
            'online payment', 
            'autopay', 
            'credit card payment',
            'cc payment'
        ]
        if amount < 0 and any(kw in desc_lower for kw in credit_card_keywords):
            return 'Bills and Utilities'

        # Step 4: Handle transfers
        transfer_keywords = ['transfer', 'zelle', 'venmo', 'cash app', 'paypal transfer']
        if any(kw in desc_lower for kw in transfer_keywords):
            return 'Transfer'

        # Step 5: Try fuzzy matching for known merchants
        fuzzy_category = self.fuzzy_match_merchant(normalized_desc)
        if fuzzy_category:
            return fuzzy_category
            
        # Step 6: Amount-based categorization
        amount_category = self.categorize_by_amount(amount, normalized_desc)
        if amount_category:
            return amount_category
            
        # Step 7: Timing-based categorization
        if date:
            timing_category = self.categorize_by_timing(normalized_desc, date)
            if timing_category:
                return timing_category
        
        # Step 8: Optimized keyword matching with scoring
        category_scores = {}
        for category, keywords in self.category_patterns.items():
            score = 0
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', desc_lower):
                    # Prioritize exact matches
                    if keyword == desc_lower:
                        score += 20
                    # Full word matches
                    else:
                        score += 10
                # Partial matches (reduced weight)
                elif keyword in desc_lower:
                    score += 2
            
            if score > 0:
                category_scores[category] = score
        
        # Return highest scoring category
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'Other'