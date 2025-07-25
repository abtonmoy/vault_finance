import re
from datetime import datetime, timedelta
import pdfplumber
import PyPDF2
import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple, Optional
from config import patterns
from utils import helpers
from core import categorizer


def parse_date(date_str: str, statement_year: int = None) -> Optional[datetime]:
    """Enhanced date parsing for Chase statements"""
    if not date_str or pd.isna(date_str):
        return None
    
    date_str = str(date_str).strip()
    if not date_str:
        return None
    
    # Remove common prefixes/suffixes
    date_str = re.sub(r'^(date|trans|transaction)\s*:?\s*', '', date_str, flags=re.IGNORECASE)
    date_str = re.sub(r'[(),]', '', date_str).strip()
    
    # Use current year if no statement year provided
    if statement_year is None:
        statement_year = datetime.now().year
    
    # Date format patterns
    formats_with_year = ['%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d', '%Y-%m-%d', 
                        '%m-%d-%Y', '%m-%d-%y', '%b %d, %Y', '%B %d, %Y']
    formats_without_year = ['%m/%d', '%m-%d', '%b %d', '%B %d']
    
    # Try formats with year first
    for fmt in formats_with_year:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Handle 2-digit years
            if dt.year < 100:
                if dt.year < 50:
                    dt = dt.replace(year=dt.year + 2000)
                else:
                    dt = dt.replace(year=dt.year + 1900)
            return dt
        except ValueError:
            continue
    
    # Try formats without year
    for fmt in formats_without_year:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Assign appropriate year
            current_date = datetime.now()
            dt = dt.replace(year=statement_year)
            
            # If date is in future, use previous year
            if dt > current_date + timedelta(days=30):
                dt = dt.replace(year=statement_year - 1)
                
            return dt
        except ValueError:
            continue
    
    return None

def clean_amount(amount_str: str) -> float:
    """Enhanced amount cleaning for various formats"""
    if not amount_str or pd.isna(amount_str):
        return 0.0
    
    amount_str = str(amount_str).strip()
    if not amount_str:
        return 0.0
    
    # Handle parentheses (negative amounts)
    is_negative = amount_str.startswith('(') and amount_str.endswith(')')
    
    # Remove all non-numeric characters except decimal points and minus signs
    cleaned = re.sub(r'[^\d.\-]', '', amount_str)
    
    try:
        value = float(cleaned) if cleaned else 0.0
        # Apply negative if in parentheses
        if is_negative:
            value = -abs(value)
        return value
    except ValueError:
        return 0.0

def extract_text(pdf_file) -> Tuple[str, List[str]]:
    """Extract text using multiple methods for better results"""
    pdf_file.seek(0)
    full_text = ""
    lines = []
    
    try:
        # Method 1: pdfplumber (better for tables)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    lines.extend(page_text.split('\n'))
    except Exception as e:
        st.warning(f"pdfplumber extraction failed: {e}")
    
    # Method 2: PyPDF2 fallback
    if not full_text.strip():
        try:
            pdf_file.seek(0)
            reader = PyPDF2.PdfReader(pdf_file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
                    lines.extend(page_text.split('\n'))
        except Exception as e:
            st.warning(f"PyPDF2 extraction failed: {e}")
    
    return full_text, lines

def find_statement_period(text: str) -> Tuple[Optional[datetime], Optional[datetime], int]:
    """Extract statement period and year from PDF text"""
    # Common statement period patterns
    period_patterns = [
        r'(\w+\s+\d{1,2},?\s+\d{4})\s*(?:through|to|-)\s*(\w+\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:through|to|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        r'Statement Period:?\s*(\d{1,2}/\d{1,2}/\d{2,4})\s*(?:through|to|-)\s*(\d{1,2}/\d{1,2}/\d{2,4})',
        r'(\w+\s+\d{1,2})\s*(?:through|to|-)\s*(\w+\s+\d{1,2},?\s+\d{4})'
    ]
    
    current_year = datetime.now().year
    start_date = None
    end_date = None
    
    for pattern in period_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_str, end_str = match.groups()
            start_date = parse_date(start_str, current_year)
            end_date = parse_date(end_str, current_year)
            if start_date and end_date:
                break
    
    # Extract year from statement
    year_match = re.search(r'\b(20\d{2})\b', text)
    statement_year = int(year_match.group(1)) if year_match else current_year
    
    return start_date, end_date, statement_year

def extract_transactions_from_text(text: str, lines: List[str], statement_year: int) -> List[Dict]:
    """Extract transactions using pattern matching on text"""
    transactions = []
    
    # Look for transaction-like patterns in each line
    for line_num, line in enumerate(lines):
        line = line.strip()
        if len(line) < 10:  # Skip very short lines
            continue
        
        # Skip header/footer lines
        if any(skip_word in line.lower() for skip_word in 
               ['statement', 'account', 'balance', 'customer service', 'page', 'continued']):
            continue
        
        # Look for date patterns
        date_found = None
        for pattern in patterns.CHASE_PATTERNS['date_patterns']:
            date_match = re.search(pattern, line)
            if date_match:
                date_str = date_match.group(1)
                date_found = parse_date(date_str, statement_year)
                if date_found:
                    break
        
        if not date_found:
            continue
        
        # Look for amount patterns
        amount_found = None
        for pattern in patterns.CHASE_PATTERNS['amount_patterns']:
            amount_match = re.search(pattern, line)
            if amount_match:
                amount_str = amount_match.group(1)
                amount_found = clean_amount(amount_str)
                if abs(amount_found) > 0.01:  # Must be at least 1 cent
                    break
        
        if amount_found is None or abs(amount_found) < 0.01:
            continue
        
        # Extract description (everything that's not date or amount)
        description_parts = []
        line_words = line.split()
        
        for word in line_words:
            # Skip if it's part of date or amount
            if any(re.search(pattern, word) for pattern in patterns.CHASE_PATTERNS['date_patterns']):
                continue
            if any(re.search(pattern, word) for pattern in patterns.CHASE_PATTERNS['amount_patterns']):
                continue
            if re.match(r'^[\d\.\-\$\(\),]*$', word):  # Skip pure numbers/currency
                continue
            description_parts.append(word)
        
        description = ' '.join(description_parts).strip()
        
        # Clean up description
        description = re.sub(r'\s+', ' ', description)  # Multiple spaces to single
        description = description[:100]  # Limit length
        
        if description and len(description) > 2:
            transactions.append({
                'date': date_found,
                'description': description,
                'amount': amount_found,
                'raw_line': line
            })
    
    # Remove duplicates and sort
    seen = set()
    unique_transactions = []
    for txn in transactions:
        key = (txn['date'], txn['description'], txn['amount'])
        if key not in seen:
            seen.add(key)
            unique_transactions.append(txn)
    
    return sorted(unique_transactions, key=lambda x: x['date'])



def parse_pdf_statement(uploaded_files) -> pd.DataFrame:
    """Main parsing function with enhanced error handling"""
    all_transactions = []
    
    for uploaded_file in uploaded_files:
        st.info(f"📄 Processing {uploaded_file.name}...")
        
        # Extract text
        full_text, lines = extract_text(uploaded_file)
        
        if not full_text.strip():
            st.error(f"❌ Could not extract text from {uploaded_file.name}")
            continue
        
        # Debug: Show extracted text
        helpers.debug_print(f"Extracted Text from {uploaded_file.name}", 
                   f"Full text length: {len(full_text)} characters\nFirst 500 chars:\n{full_text[:500]}")
        
        # Find statement period
        start_date, end_date, statement_year = find_statement_period(full_text)
        st.info(f"📅 Detected statement period: {start_date} to {end_date} (Year: {statement_year})")
        
        # Extract transactions
        raw_transactions = extract_transactions_from_text(full_text, lines, statement_year)
        
        helpers.debug_print(f"Raw Transactions from {uploaded_file.name}", 
                   [f"{t['date']} - {t['description']} - ${t['amount']:.2f}" for t in raw_transactions])
        
        if not raw_transactions:
            st.warning(f"⚠️ No transactions found in {uploaded_file.name}")
            continue
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_transactions)
        df['source_file'] = uploaded_file.name
        
        # Enhanced categorization with date info
        df['category'] = df.apply(lambda x: categorizer.categorize_transaction(x['description'], x['amount'], x['date']), axis=1)
        
        # Filter out likely non-transactions
        df = df[df['amount'] != 0]  # Remove zero amounts
        df = df[df['description'].str.len() > 2]  # Remove very short descriptions
        
        helpers.debug_print(f"Final Transactions from {uploaded_file.name}", df.head(10).to_dict('records'))
        
        all_transactions.append(df)
        st.success(f" Extracted {len(df)} transactions from {uploaded_file.name}")
    
    if not all_transactions:
        return pd.DataFrame()
    
    # Combine all transactions
    combined_df = pd.concat(all_transactions, ignore_index=True)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
    
    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    st.success(f" Total: {len(combined_df)} unique transactions from {len(uploaded_files)} file(s)")
    
    return combined_df
