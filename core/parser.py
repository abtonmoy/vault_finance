import re
from datetime import datetime, timedelta
import pdfplumber
import PyPDF2
import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from config import patterns
from utils import helpers
from core import categorizer


# Import the deduplication system
import re
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple, Optional
from fuzzywuzzy import fuzz

class TransactionDeduplicator:
    def __init__(self):
        self.credit_card_patterns = [
            r'payment\s+thank\s+you',
            r'online\s+payment',
            r'autopay',
            r'credit\s+card\s+payment',
            r'cc\s+payment',
            r'automatic\s+payment',
            r'electronic\s+payment',
            r'chase\s+credit\s+crd',
            r'discover\s+payment',
            r'capital\s+one\s+payment',
            r'citi\s+payment',
            r'amex\s+payment',
            r'american\s+express\s+payment'
        ]
        
        self.transfer_patterns = [
            r'transfer\s+to',
            r'transfer\s+from',
            r'internal\s+transfer',
            r'account\s+transfer',
            r'online\s+transfer',
            r'zelle',
            r'venmo',
            r'cash\s+app',
            r'paypal\s+transfer'
        ]
    
    def normalize_description(self, description: str) -> str:
        """Normalize transaction descriptions for comparison"""
        if pd.isna(description):
            return ""
        
        desc = str(description).lower().strip()
        
        # Remove common prefixes and suffixes
        desc = re.sub(r'^(debit|credit|online|web|pos|purchase|payment|transaction)\s+', '', desc)
        desc = re.sub(r'\s+(payment|purchase|transaction|charge)$', '', desc)
        
        # Remove numbers, dates, and special characters for fuzzy matching
        desc_clean = re.sub(r'[\d\-/\*#]+', '', desc)
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
        
        return desc_clean
    
    def is_credit_card_payment(self, description: str, amount: float) -> bool:
        """Check if transaction is a credit card payment"""
        if pd.isna(description) or amount >= 0:  # Payments are typically negative
            return False
        
        desc_lower = str(description).lower()
        return any(re.search(pattern, desc_lower, re.IGNORECASE) for pattern in self.credit_card_patterns)
    
    def is_transfer_transaction(self, description: str) -> bool:
        """Check if transaction is a transfer between accounts"""
        if pd.isna(description):
            return False
        
        desc_lower = str(description).lower()
        return any(re.search(pattern, desc_lower, re.IGNORECASE) for pattern in self.transfer_patterns)
    
    def find_exact_duplicates(self, df: pd.DataFrame) -> List[int]:
        """Find exact duplicate transactions (same date, description, amount)"""
        # Create a comparison key
        df['_temp_key'] = df.apply(lambda x: f"{x['date']}_{x['description']}_{x['amount']}", axis=1)
        
        # Find duplicates
        duplicate_mask = df.duplicated(subset=['_temp_key'], keep='first')
        duplicate_indices = df[duplicate_mask].index.tolist()
        
        # Clean up
        df.drop('_temp_key', axis=1, inplace=True)
        
        return duplicate_indices
    
    def find_similar_transactions(self, df: pd.DataFrame, 
                                date_window: int = 2,
                                amount_tolerance: float = 0.01,
                                description_threshold: int = 85) -> List[int]:
        """Find similar transactions that might be duplicates"""
        duplicates_to_remove = []
        processed_indices = set()
        
        for idx, row in df.iterrows():
            if idx in processed_indices:
                continue
                
            # Look for similar transactions
            date_mask = (df['date'] >= row['date'] - timedelta(days=date_window)) & \
                       (df['date'] <= row['date'] + timedelta(days=date_window))
            
            candidates = df[date_mask & (df.index != idx)]
            
            row_amount = abs(row['amount'])
            row_desc = self.normalize_description(row['description'])
            
            for cand_idx, candidate in candidates.iterrows():
                if cand_idx in processed_indices:
                    continue
                
                cand_amount = abs(candidate['amount'])
                cand_desc = self.normalize_description(candidate['description'])
                
                # Check amount similarity
                amount_diff = abs(row_amount - cand_amount)
                amount_similar = amount_diff <= max(row_amount * amount_tolerance, 1.0)
                
                # Check description similarity
                desc_similarity = 0
                if row_desc and cand_desc:
                    desc_similarity = fuzz.ratio(row_desc, cand_desc)
                
                # If very similar, mark as duplicate
                if amount_similar and desc_similarity >= description_threshold:
                    # Keep the earlier transaction, remove the later one
                    if cand_idx > idx:
                        duplicates_to_remove.append(cand_idx)
                        processed_indices.add(cand_idx)
        
        return duplicates_to_remove
    
    def handle_credit_card_duplicates(self, df: pd.DataFrame) -> Tuple[List[int], Dict]:
        """
        Handle credit card payment duplicates more intelligently.
        Instead of removing all charges, we identify payment cycles.
        """
        duplicates_to_remove = []
        credit_card_info = {
            'payments_found': 0,
            'charges_covered': 0,
            'unmatched_payments': []
        }
        
        # Find all credit card payments
        cc_payments = []
        for idx, row in df.iterrows():
            if self.is_credit_card_payment(row['description'], row['amount']):
                cc_payments.append({
                    'index': idx,
                    'amount': abs(row['amount']),
                    'date': row['date'],
                    'description': row['description']
                })
        
        credit_card_info['payments_found'] = len(cc_payments)
        
        # For each payment, try to find corresponding charges
        for payment in cc_payments:
            payment_amount = payment['amount']
            payment_date = payment['date']
            
            # Look for charges in the 45 days before the payment
            start_date = payment_date - timedelta(days=45)
            end_date = payment_date + timedelta(days=2)  # Small buffer for processing delays
            
            # Find potential charges (negative amounts, not transfers or other payments)
            charge_mask = (
                (df['date'] >= start_date) & 
                (df['date'] <= end_date) &
                (df['amount'] < 0) &  # Only expenses
                (df.index != payment['index']) &  # Not the payment itself
                (~df['description'].str.contains('|'.join(self.credit_card_patterns + self.transfer_patterns), 
                                                case=False, na=False, regex=True))
            )
            
            potential_charges = df[charge_mask].copy()
            
            if potential_charges.empty:
                credit_card_info['unmatched_payments'].append(payment)
                continue
            
            # Sum up the charges
            total_charges = abs(potential_charges['amount'].sum())
            
            # Check if charges roughly match the payment (within 15% tolerance)
            # This accounts for timing differences, interest, fees, etc.
            tolerance = 0.15
            if abs(total_charges - payment_amount) <= payment_amount * tolerance:
                # This looks like a valid payment cycle
                # We'll keep the individual charges and remove the payment summary
                # This gives users better visibility into what they actually spent money on
                
                duplicates_to_remove.append(payment['index'])
                credit_card_info['charges_covered'] += len(potential_charges)
                
                st.info(f"💳 Found payment cycle: ${payment_amount:.2f} payment covers "
                       f"{len(potential_charges)} charges totaling ${total_charges:.2f}")
            else:
                credit_card_info['unmatched_payments'].append(payment)
        
        return duplicates_to_remove, credit_card_info
    
    def handle_transfer_duplicates(self, df: pd.DataFrame) -> List[int]:
        """Handle transfer duplicates between accounts"""
        duplicates_to_remove = []
        
        # Find all transfer transactions
        transfer_mask = df['description'].str.contains(
            '|'.join(self.transfer_patterns), case=False, na=False, regex=True
        )
        transfer_transactions = df[transfer_mask]
        
        if transfer_transactions.empty:
            return duplicates_to_remove
        
        # Group transfers by date and amount
        processed_transfers = set()
        
        for idx, transfer in transfer_transactions.iterrows():
            if idx in processed_transfers:
                continue
                
            transfer_amount = abs(transfer['amount'])
            transfer_date = transfer['date']
            
            # Look for matching transfers on the same day
            same_day_mask = (
                (transfer_transactions['date'] == transfer_date) &
                (transfer_transactions['amount'].abs() == transfer_amount) &
                (transfer_transactions.index != idx)
            )
            
            matching_transfers = transfer_transactions[same_day_mask]
            
            if not matching_transfers.empty:
                # Keep the first transfer, remove duplicates
                for match_idx in matching_transfers.index:
                    if match_idx not in processed_transfers:
                        duplicates_to_remove.append(match_idx)
                        processed_transfers.add(match_idx)
                
                processed_transfers.add(idx)
        
        return duplicates_to_remove
    
    def remove_duplicates(self, df: pd.DataFrame, 
                         remove_credit_card_duplicates: bool = True,
                         remove_transfer_duplicates: bool = True,
                         aggressive_deduplication: bool = False) -> pd.DataFrame:
        """
        Remove duplicate transactions with improved logic
        
        Args:
            df: DataFrame with transactions
            remove_credit_card_duplicates: Whether to handle CC payment cycles
            remove_transfer_duplicates: Whether to remove transfer duplicates
            aggressive_deduplication: Whether to use fuzzy matching for similar transactions
        """
        
        if df.empty:
            return df
        
        st.header("🔍 Duplicate Detection & Removal")
        
        df_clean = df.copy()
        all_duplicates = set()
        
        # Step 1: Remove exact duplicates
        st.subheader("1️⃣ Exact Duplicate Detection")
        exact_duplicates = self.find_exact_duplicates(df_clean)
        all_duplicates.update(exact_duplicates)
        
        if exact_duplicates:
            st.info(f"Found {len(exact_duplicates)} exact duplicates")
        else:
            st.success("No exact duplicates found")
        
        # Step 2: Handle credit card payment cycles
        if remove_credit_card_duplicates:
            st.subheader("2️⃣ Credit Card Payment Cycle Analysis")
            cc_duplicates, cc_info = self.handle_credit_card_duplicates(df_clean)
            all_duplicates.update(cc_duplicates)
            
            if cc_info['payments_found'] > 0:
                st.info(f"Found {cc_info['payments_found']} credit card payments")
                st.info(f"Identified {cc_info['charges_covered']} individual charges covered by payments")
                
                if cc_info['unmatched_payments']:
                    st.warning(f"⚠️ {len(cc_info['unmatched_payments'])} payments couldn't be matched to charges")
            else:
                st.success("No credit card payments detected")
        
        # Step 3: Handle transfer duplicates
        if remove_transfer_duplicates:
            st.subheader("3️⃣ Transfer Duplicate Detection")
            transfer_duplicates = self.handle_transfer_duplicates(df_clean)
            all_duplicates.update(transfer_duplicates)
            
            if transfer_duplicates:
                st.info(f"Found {len(transfer_duplicates)} duplicate transfers")
            else:
                st.success("No duplicate transfers found")
        
        # Step 4: Fuzzy matching (optional, more aggressive)
        if aggressive_deduplication:
            st.subheader("4️⃣ Similar Transaction Detection")
            similar_duplicates = self.find_similar_transactions(df_clean)
            all_duplicates.update(similar_duplicates)
            
            if similar_duplicates:
                st.info(f"Found {len(similar_duplicates)} similar transactions")
            else:
                st.success("No similar transactions found")
        
        # Remove all identified duplicates
        df_final = df_clean.drop(index=list(all_duplicates))
        
        # Summary
        st.subheader("📊 Deduplication Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Original Transactions", len(df))
        with col2:
            st.metric("Duplicates Removed", len(all_duplicates))
        with col3:
            st.metric("Final Transactions", len(df_final))
        
        if len(all_duplicates) > 0:
            st.success(f"✅ Successfully removed {len(all_duplicates)} duplicate transactions")
        else:
            st.info("✨ No duplicates found - your data is already clean!")
        
        return df_final.reset_index(drop=True)


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


def parse_pdf_statement(uploaded_files, dedup_config=None) -> pd.DataFrame:
    """
    Main parsing function with improved duplicate handling
    
    Args:
        uploaded_files: List of uploaded PDF files
        dedup_config: Dictionary with deduplication configuration options
    """
    
    # Default configuration if none provided
    if dedup_config is None:
        dedup_config = {
            'remove_credit_card_duplicates': True,
            'remove_transfer_duplicates': True,
            'aggressive_deduplication': False,
            'cc_date_window': 45,
            'cc_amount_tolerance': 0.15,
            'fuzzy_date_window': 2,
            'description_threshold': 85
        }
    
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
        st.success(f"✅ Extracted {len(df)} transactions from {uploaded_file.name}")
    
    if not all_transactions:
        return pd.DataFrame()
    
    # Combine all transactions
    combined_df = pd.concat(all_transactions, ignore_index=True)
    
    # Show initial file summary
    if len(uploaded_files) > 1:
        st.subheader("📊 Initial File Summary")
        file_summary = combined_df.groupby('source_file').agg({
            'amount': 'count',
            'date': ['min', 'max']
        }).round(2)
        file_summary.columns = ['Transaction Count', 'Start Date', 'End Date']
        st.dataframe(file_summary)
    
    # Apply deduplication based on configuration
    if len(uploaded_files) > 1 or dedup_config.get('aggressive_deduplication', False):
        # Use the improved deduplicator
        deduplicator = TransactionDeduplicator()
        
        # Apply deduplication with configuration
        combined_df = deduplicator.remove_duplicates(
            combined_df,
            remove_credit_card_duplicates=dedup_config.get('remove_credit_card_duplicates', True),
            remove_transfer_duplicates=dedup_config.get('remove_transfer_duplicates', True),
            aggressive_deduplication=dedup_config.get('aggressive_deduplication', False)
        )
        
        # Show final file summary
        if len(uploaded_files) > 1:
            st.subheader("📊 Final File Summary")
            file_summary_clean = combined_df.groupby('source_file').agg({
                'amount': 'count',
                'date': ['min', 'max']
            }).round(2)
            file_summary_clean.columns = ['Transaction Count', 'Start Date', 'End Date']
            st.dataframe(file_summary_clean)
        
    else:
        # Single file - just remove basic exact duplicates
        initial_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['date', 'description', 'amount'], keep='first')
        removed_count = initial_count - len(combined_df)
        
        if removed_count > 0:
            st.info(f"🔍 Removed {removed_count} exact duplicates from single file")
    
    # Sort by date
    combined_df = combined_df.sort_values('date').reset_index(drop=True)
    
    total_files = len(uploaded_files)
    st.success(f"🎉 Final Result: {len(combined_df)} unique transactions from {total_files} file(s)")
    
    return combined_df


def create_transaction_type_summary(df):
    """Create a summary showing different types of transactions found"""
    
    st.subheader("🔍 Transaction Type Analysis")
    
    deduplicator = TransactionDeduplicator()
    
    # Analyze transaction types
    credit_card_payments = 0
    transfers = 0
    regular_transactions = 0
    
    for idx, row in df.iterrows():
        if deduplicator.is_credit_card_payment(row['description'], row['amount']):
            credit_card_payments += 1
        elif deduplicator.is_transfer_transaction(row['description']):
            transfers += 1
        else:
            regular_transactions += 1
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💳 Credit Card Payments", credit_card_payments)
    
    with col2:
        st.metric("🔄 Transfers", transfers)
    
    with col3:
        st.metric("💰 Regular Transactions", regular_transactions)
    
    # Show examples of each type
    if credit_card_payments > 0:
        with st.expander("View Credit Card Payments"):
            cc_mask = df.apply(lambda x: deduplicator.is_credit_card_payment(x['description'], x['amount']), axis=1)
            st.dataframe(df[cc_mask][['date', 'description', 'amount']].head(10))
    
    if transfers > 0:
        with st.expander("View Transfers"):
            transfer_mask = df.apply(lambda x: deduplicator.is_transfer_transaction(x['description']), axis=1)
            st.dataframe(df[transfer_mask][['date', 'description', 'amount']].head(10))


class InvestmentTracker:
    def __init__(self):
        self.portfolio = pd.DataFrame()
        self.transactions = pd.DataFrame()
        self.historical_values = pd.DataFrame()
        self.risk_free_rate = 0.02  # Default risk-free rate (2%)
    
    def parse_robinhood_csv(self, uploaded_file):
        """Parse Robinhood CSV reports"""
        try:
            df = pd.read_csv(uploaded_file)
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Filter relevant columns
            required_cols = ['symbol', 'description', 'quantity', 'average_price', 
                             'current_price', 'current_value', 'last_updated']
            df = df[[col for col in required_cols if col in df.columns]]
            
            # Calculate additional metrics
            if 'average_price' in df.columns and 'quantity' in df.columns:
                df['cost_basis'] = df['average_price'] * df['quantity']
            if 'current_price' in df.columns and 'quantity' in df.columns:
                df['market_value'] = df['current_price'] * df['quantity']
            if 'market_value' in df.columns and 'cost_basis' in df.columns:
                df['gain_loss'] = df['market_value'] - df['cost_basis']
                df['gain_loss_pct'] = (df['gain_loss'] / df['cost_basis']) * 100
            
            # Add source information
            df['source'] = uploaded_file.name
            df['brokerage'] = 'Robinhood'
            df['report_date'] = datetime.now().date()
            
            # Add to portfolio
            self._add_to_portfolio(df)
            return True
        except Exception as e:
            st.error(f"Error parsing Robinhood CSV: {str(e)}")
            helpers.debug_print("Robinhood CSV Error", str(e))
            return False
    
    def parse_robinhood_pdf(self, uploaded_file):
        """Enhanced Robinhood PDF parser with better error handling"""
        try:
            holdings = []
            in_portfolio_section = False
            table_started = False
            current_description = None
            debug_log = []
            
            debug_log.append(f"Starting parse of {uploaded_file.name}")
            
            with pdfplumber.open(uploaded_file) as pdf:
                debug_log.append(f"PDF has {len(pdf.pages)} pages")
                
                for page_idx, page in enumerate(pdf.pages):
                    debug_log.append(f"\n===== Page {page_idx+1} =====")
                    
                    page_text = page.extract_text()
                    if not page_text:
                        debug_log.append("Page has no text")
                        continue
                        
                    lines = page_text.split('\n')
                    debug_log.append(f"Extracted {len(lines)} lines")
                    
                    for line_idx, line in enumerate(lines):
                        line = line.strip()
                        
                        # Skip page headers/footers and empty lines
                        if "Robinhood" in line or "Page" in line or not line:
                            continue
                        
                        # Detect start of portfolio section
                        if "Portfolio Summary" in line:
                            in_portfolio_section = True
                            debug_log.append(f"ENTERED PORTFOLIO SECTION")
                            continue
                            
                        # Detect end of portfolio section
                        if "Account Activity" in line or "Deposit Sweep Program Banks" in line:
                            in_portfolio_section = False
                            table_started = False
                            current_description = None
                            debug_log.append(f"EXITED PORTFOLIO SECTION")
                            continue
                            
                        if not in_portfolio_section:
                            continue
                        
                        # Detect table header
                        if "Securities Held in Account" in line and "Sym/Cusip" in line:
                            table_started = True
                            current_description = None
                            debug_log.append(f"TABLE HEADER DETECTED")
                            continue
                            
                        if not table_started:
                            continue
                        
                        # Skip section breaks and totals
                        if "Total Securities" in line or "Brokerage Cash Balance" in line:
                            table_started = False
                            current_description = None
                            debug_log.append(f"TABLE ENDED")
                            continue
                            
                        # Handle yield rows
                        if "Estimated Yield:" in line:
                            current_description = None  # Reset after yield line
                            continue
                            
                        # Check if this is a security name line (no numbers, no symbols, no "Cash")
                        if (not re.search(r'\d', line) and 
                            not re.search(r'\$', line) and 
                            'Cash' not in line and
                            len(line.strip()) > 2):
                            current_description = line.strip()
                            debug_log.append(f"SECURITY NAME: {current_description}")
                            continue
                        
                        # Process security data line
                        if current_description:
                            # Enhanced pattern to match Robinhood data format
                            pattern = r'([A-Z]{1,5})\s+Cash\s+([\d\.]+)\s+\$([,\d\.]+)\s+\$([,\d\.]+)\s+\$([,\d\.]+)\s+([\d\.]+)%'
                            match = re.search(pattern, line)
                            
                            if match:
                                try:
                                    symbol = match.group(1).strip()
                                    quantity = float(match.group(2))
                                    current_price = float(match.group(3).replace(',', ''))
                                    market_value = float(match.group(4).replace(',', ''))
                                    est_dividend = float(match.group(5).replace(',', ''))
                                    portfolio_percent = float(match.group(6)) / 100
                                    
                                    security = {
                                        'description': current_description,
                                        'symbol': symbol,
                                        'account_type': 'Cash',
                                        'quantity': quantity,
                                        'current_price': current_price,
                                        'market_value': market_value,
                                        'est_dividend': est_dividend,
                                        'portfolio_percent': portfolio_percent,
                                        'cost_basis': market_value,  # Use market value as cost basis placeholder
                                        'average_price': current_price,
                                        'gain_loss': 0.0,  # No gain/loss info in statement
                                        'gain_loss_pct': 0.0,
                                        'yield': 0.0
                                    }
                                    
                                    holdings.append(security)
                                    debug_log.append(f"ADDED SECURITY: {symbol} - {current_description} - ${market_value:.2f}")
                                    
                                except Exception as e:
                                    debug_log.append(f"PARSE ERROR: {str(e)} in line: {line}")
                            
                            current_description = None  # Reset for next security
            
            if holdings:
                debug_log.append(f"Successfully parsed {len(holdings)} holdings")
                df = pd.DataFrame(holdings)
                
                # Add metadata
                df['source'] = uploaded_file.name
                df['brokerage'] = 'Robinhood'
                df['report_date'] = datetime.now().date()
                
                # Verify required columns are present
                required_cols = ['symbol', 'description', 'quantity', 'market_value', 'cost_basis']
                for col in required_cols:
                    if col not in df.columns:
                        debug_log.append(f"ERROR: Missing required column {col}")
                        return False, debug_log
                
                debug_log.append(f"DataFrame columns: {list(df.columns)}")
                debug_log.append(f"DataFrame shape: {df.shape}")
                
                # Add to portfolio
                self._add_to_portfolio(df)
                return True, debug_log
                
            debug_log.append("No holdings found after processing all pages")
            return False, debug_log
            
        except Exception as e:
            debug_log.append(f"Critical error: {str(e)}")
            import traceback
            debug_log.append(traceback.format_exc())
            return False, debug_log

    def parse_generic_csv(self, uploaded_file, brokerage):
        """Parse generic brokerage CSV reports"""
        try:
            df = pd.read_csv(uploaded_file)
            
            # Standardize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Map columns to standard format
            column_mapping = {
                'ticker': 'symbol',
                'ticker_symbol': 'symbol',
                'security': 'description',
                'shares': 'quantity',
                'avg_cost': 'average_price',
                'current_value': 'market_value',
                'price': 'current_price',
                'value': 'market_value',
                'current_price': 'current_price'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            
            # Calculate metrics if columns exist
            if 'average_price' in df.columns and 'quantity' in df.columns:
                df['cost_basis'] = df['average_price'] * df['quantity']
            if 'current_price' in df.columns and 'quantity' in df.columns:
                df['market_value'] = df['current_price'] * df['quantity']
            if 'market_value' in df.columns and 'cost_basis' in df.columns:
                df['gain_loss'] = df['market_value'] - df['cost_basis']
                df['gain_loss_pct'] = (df['gain_loss'] / df['cost_basis']) * 100
            
            # Add source information
            df['source'] = uploaded_file.name
            df['brokerage'] = brokerage
            df['report_date'] = datetime.now().date()
            
            # Add to portfolio
            self._add_to_portfolio(df)
            return True
        except Exception as e:
            st.error(f"Error parsing {brokerage} CSV: {str(e)}")
            helpers.debug_print(f"{brokerage} CSV Error", str(e))
            return False
    
    def _add_to_portfolio(self, new_df):
        """Add new holdings to portfolio, updating existing positions with better error handling"""
        if new_df.empty:
            st.warning("No data to add to portfolio")
            return
        
        # Ensure required columns exist
        required_columns = ['symbol', 'description', 'quantity', 'market_value']
        missing_columns = [col for col in required_columns if col not in new_df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            st.error(f"Available columns: {list(new_df.columns)}")
            return
        
        # Fill missing optional columns with defaults
        if 'cost_basis' not in new_df.columns:
            new_df['cost_basis'] = new_df['market_value']  # Use market value as fallback
        if 'current_price' not in new_df.columns:
            new_df['current_price'] = new_df['market_value'] / new_df['quantity']
        if 'average_price' not in new_df.columns:
            new_df['average_price'] = new_df['cost_basis'] / new_df['quantity']
        if 'gain_loss' not in new_df.columns:
            new_df['gain_loss'] = new_df['market_value'] - new_df['cost_basis']
        if 'gain_loss_pct' not in new_df.columns:
            new_df['gain_loss_pct'] = (new_df['gain_loss'] / new_df['cost_basis']) * 100
        
        if self.portfolio.empty:
            self.portfolio = new_df.copy()
            st.success(f"Added {len(new_df)} new positions to portfolio")
        else:
            # Update existing positions
            updated_positions = 0
            new_positions = 0
            
            for idx, row in new_df.iterrows():
                symbol = row['symbol']
                existing_idx = self.portfolio[self.portfolio['symbol'] == symbol].index
                
                if not existing_idx.empty:
                    # Update existing position
                    idx = existing_idx[0]
                    # Update quantity and cost basis using weighted average
                    old_quantity = self.portfolio.at[idx, 'quantity']
                    old_cost_basis = self.portfolio.at[idx, 'cost_basis']
                    
                    new_quantity = old_quantity + row['quantity']
                    new_cost_basis = old_cost_basis + row['cost_basis']
                    
                    self.portfolio.at[idx, 'quantity'] = new_quantity
                    self.portfolio.at[idx, 'cost_basis'] = new_cost_basis
                    self.portfolio.at[idx, 'average_price'] = new_cost_basis / new_quantity if new_quantity > 0 else 0
                    
                    # Update market value if current price is available
                    if 'current_price' in row and pd.notnull(row['current_price']):
                        self.portfolio.at[idx, 'current_price'] = row['current_price']
                        self.portfolio.at[idx, 'market_value'] = new_quantity * row['current_price']
                        self.portfolio.at[idx, 'gain_loss'] = self.portfolio.at[idx, 'market_value'] - new_cost_basis
                        self.portfolio.at[idx, 'gain_loss_pct'] = (self.portfolio.at[idx, 'gain_loss'] / new_cost_basis) * 100 if new_cost_basis > 0 else 0
                    
                    updated_positions += 1
                else:
                    # Add new position
                    self.portfolio = pd.concat([self.portfolio, row.to_frame().T], ignore_index=True)
                    new_positions += 1
            
            st.success(f"Updated {updated_positions} existing positions, added {new_positions} new positions")
        
        # Update historical values
        self._update_historical_values()
    
    def _update_historical_values(self):
        """Update historical portfolio values"""
        total_value = self.portfolio['market_value'].sum()
        new_entry = pd.DataFrame({
            'date': [datetime.now().date()],
            'total_value': [total_value],
            'num_holdings': [len(self.portfolio)]
        })
        
        if self.historical_values.empty:
            self.historical_values = new_entry
        else:
            self.historical_values = pd.concat([self.historical_values, new_entry], ignore_index=True)
    
    def calculate_portfolio_summary(self):
        """Calculate portfolio summary statistics with error handling"""
        if self.portfolio.empty:
            st.warning("Portfolio is empty")
            return None
        
        # Check for required columns
        required_columns = ['market_value', 'cost_basis', 'gain_loss']
        missing_columns = [col for col in required_columns if col not in self.portfolio.columns]
        
        if missing_columns:
            st.error(f"Portfolio missing required columns: {missing_columns}")
            st.error(f"Available columns: {list(self.portfolio.columns)}")
            return None
        
        try:
            summary = {
                'total_value': self.portfolio['market_value'].sum(),
                'total_cost_basis': self.portfolio['cost_basis'].sum(),
                'total_gain_loss': self.portfolio['gain_loss'].sum(), 
                'num_positions': len(self.portfolio),
                'num_brokerages': self.portfolio['brokerage'].nunique() if 'brokerage' in self.portfolio.columns else 1
            }
            
            summary['gain_loss_pct'] = (
                (summary['total_gain_loss'] / summary['total_cost_basis']) * 100 
                if summary['total_cost_basis'] > 0 else 0
            )
            
            return summary
            
        except Exception as e:
            st.error(f"Error calculating portfolio summary: {str(e)}")
            st.error(f"Portfolio columns: {list(self.portfolio.columns)}")
            st.error(f"Portfolio shape: {self.portfolio.shape}")
            return None
    
    def calculate_advanced_metrics(self):
        """Calculate advanced portfolio metrics"""
        if self.historical_values.empty or len(self.historical_values) < 2:
            return None
        
        # Calculate returns
        returns = self.historical_values.sort_values('date')
        returns['daily_return'] = returns['total_value'].pct_change()
        
        # Remove first row (no return)
        returns = returns.iloc[1:]
        
        if returns.empty:
            return None
        
        # Calculate metrics
        avg_daily_return = returns['daily_return'].mean()
        std_daily_return = returns['daily_return'].std()
        total_return = (returns['total_value'].iloc[-1] / returns['total_value'].iloc[0]) - 1
        
        # Annualize metrics
        trading_days = 252
        annualized_return = (1 + avg_daily_return) ** trading_days - 1
        annualized_volatility = std_daily_return * np.sqrt(trading_days)
        
        # Calculate Sharpe ratio
        sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility
        
        # Calculate Sortino ratio (only downside volatility)
        downside_returns = returns[returns['daily_return'] < 0]['daily_return']
        downside_volatility = downside_returns.std() * np.sqrt(trading_days)
        sortino_ratio = (annualized_return - self.risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + returns['daily_return']).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()
        
        # Calculate Calmar ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown < 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'max_drawdown': max_drawdown,
            'total_return': total_return,
            'risk_free_rate': self.risk_free_rate
        }
    
    def get_sector_breakdown(self):
        """Group holdings by sector (requires sector data)"""
        if 'sector' in self.portfolio.columns:
            return self.portfolio.groupby('sector').agg({
                'market_value': 'sum',
                'gain_loss': 'sum'
            }).reset_index()
        return None
    
    def get_asset_class_breakdown(self):
        """Group holdings by asset class (stock, ETF, crypto)"""
        if self.portfolio.empty:
            return None
            
        # Simple classifier based on description
        def classify_asset(description):
            if pd.isna(description):
                return 'Unknown'
            desc = description.lower()
            if 'etf' in desc:
                return 'ETF'
            if 'fund' in desc:
                return 'Mutual Fund'
            if 'bitcoin' in desc or 'crypto' in desc or 'coin' in desc:
                return 'Crypto'
            return 'Stock'
        
        self.portfolio['asset_class'] = self.portfolio['description'].apply(classify_asset)
        return self.portfolio.groupby('asset_class').agg({
            'market_value': 'sum',
            'quantity': 'sum',
            'symbol': 'count'
        }).reset_index().rename(columns={'symbol': 'holdings'})
    
    def get_top_performers(self, n=5):
        """Get top performing positions"""
        if self.portfolio.empty:
            return pd.DataFrame()
        return self.portfolio.nlargest(n, 'gain_loss_pct')
    
    def get_bottom_performers(self, n=5):
        """Get bottom performing positions"""
        if self.portfolio.empty:
            return pd.DataFrame()
        return self.portfolio.nsmallest(n, 'gain_loss_pct')