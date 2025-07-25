import pandas as pd
from typing import Dict, List
from categorizer import TransactionCategorizer

def add_categorization_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Add confidence scores to categorization"""
    categorizer = TransactionCategorizer()
    
    def get_confidence(row):
        desc = row['description'].lower()
        category = row['category']
        
        # High confidence for exact merchant matches
        if categorizer.fuzzy_match_merchant(desc, threshold=90):
            return 'High'
        
        # Medium confidence for keyword matches
        keywords = categorizer.category_patterns.get(category, [])
        if any(kw in desc for kw in keywords):
            return 'Medium'
        
        return 'Low'
    
    df['confidence'] = df.apply(get_confidence, axis=1)
    return df

def suggest_category_corrections(df: pd.DataFrame) -> List[Dict]:
    """Suggest potential miscategorizations for user review"""
    suggestions = []
    
    # Look for unusual patterns
    for idx, row in df.iterrows():
        desc = row['description'].lower()
        category = row['category']
        amount = row['amount']
        
        # Check for potential mismatches
        if category == 'Other' and abs(amount) > 100:
            suggestions.append({
                'index': idx,
                'description': row['description'],
                'current_category': category,
                'suggested_category': 'Review - Large Amount',
                'reason': 'Large uncategorized transaction'
            })
        
        # Check for groceries miscategorized as shopping
        if category == 'Shopping' and any(word in desc for word in ['market', 'grocery', 'food']):
            suggestions.append({
                'index': idx,
                'description': row['description'],
                'current_category': category,
                'suggested_category': 'Groceries',
                'reason': 'Likely grocery store'
            })
    
    return suggestions
