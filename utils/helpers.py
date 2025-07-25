import streamlit as st
import re


def debug_print(title, content):
    """Helper for debugging output"""
    if st.checkbox(f"Show {title}", key=f"debug_{title.replace(' ', '_').lower()}"):
        st.markdown(f"### 🔍 {title}")
        if isinstance(content, list):
            for i, item in enumerate(content[:20]):  # Limit to first 20 items
                st.text(f"{i+1}: {item}")
        elif isinstance(content, dict):
            for key, value in list(content.items())[:20]:
                st.text(f"{key}: {value}")
        else:
            st.text(str(content)[:2000])  # Limit text length


def calculate_financial_metrics(df):
    """Centralized function for consistent financial calculations"""
    
    # Income: Only transactions categorized as 'Income' with positive amounts
    income_mask = (df['category'] == 'Income') & (df['amount'] > 0)
    total_income = df[income_mask]['amount'].sum()
    
    # Expenses: Negative amounts excluding transfers and income categories
    expense_mask = (df['amount'] < 0) & (df['category'] != 'Transfer') & (df['category'] != 'Income')
    total_expenses = abs(df[expense_mask]['amount'].sum())
    
    # Net income
    net_income = total_income - total_expenses
    
    # Additional metrics
    total_transactions = len(df)
    categories = df['category'].nunique()
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'total_transactions': total_transactions,
        'categories': categories
    }