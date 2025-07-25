import sys
import os

sys.path.append(os.path.abspath("../"))
import streamlit as st
import pandas as pd
from core.parser import parse_pdf_statement
# from core.parser import parse_pdf_statement
from utils.visualizations import (
    show_file_summary,
    show_metrics,
    show_category_bar_chart,
    show_spending_pie_chart,
    show_monthly_trend,
    show_top_merchants,
    show_transaction_table,
    show_summary_statistics
)

def main_ui():
    st.title("💰 Enhanced Bank Statement Analyzer")
    st.markdown("Upload your bank statement PDF files to analyze spending with improved AI-powered categorization.")
    
    # Initialize session state
    if 'transactions_df' not in st.session_state:
        st.session_state['transactions_df'] = None
    
    uploaded_files = st.file_uploader(
        "Upload PDF bank statements",
        type="pdf",
        accept_multiple_files=True,
        help="Supports text-based PDFs from Chase, Wells Fargo, Bank of America, etc."
    )
    
    if uploaded_files:
        with st.spinner("Parsing and analyzing transactions with enhanced categorization..."):
            df = parse_pdf_statement(uploaded_files)
        
        if df is not None and not df.empty:
            # Store dataframe in session state
            st.session_state['transactions_df'] = df
            st.success(f"✅ Loaded {len(df)} transactions with enhanced categorization!")
            
            # Show date range
            if 'date' in df.columns and not df['date'].isna().all():
                date_range = f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}"
                st.info(f"📅 Date Range: {date_range}")
            
            # File Summary
            if len(uploaded_files) > 1 and 'source_file' in df.columns:
                show_file_summary(df)
            
            # Metrics
            show_metrics(df)
            
            # Categorization summary
            st.subheader("📊 Enhanced Categorization Summary")
            col1, col2 = st.columns(2)
            with col1:
                show_category_bar_chart(df)
            with col2:
                show_spending_pie_chart(df)
            
            # Financial analysis
            st.header("📊 Financial Analysis")
            col1, col2 = st.columns(2)
            with col1:
                show_monthly_trend(df)
            with col2:
                show_top_merchants(df)
            
            # Transaction table
            show_transaction_table(df, uploaded_files)
            
            # Summary statistics
            show_summary_statistics(df)
        
        else:
            st.error("❌ No valid transactions could be extracted. Please check:")
            st.markdown("""
            - Ensure PDFs contain actual transaction data (not just account summaries)
            - PDFs should be text-based (not scanned images)
            - Try different Chase statement formats or other bank statements
            - Check if the PDF has transactions in a table format
            """)
    
    else:
        st.markdown("""
        ### 📄 How to Use:
        1. Download **text-based PDF** bank statements from your bank
        2. Upload one or more PDF files 
        3. View automatic analysis with **enhanced AI-powered categorization**
        
        **New Features:**
        - 🎯 **Smart Categorization**: Uses fuzzy matching, amount-based rules, and timing patterns
        - 📊 **Confidence Scoring**: Shows how certain the system is about each category
        - ✏️ **Interactive Corrections**: Easy interface to fix miscategorized transactions
        - 🔧 **Custom Rules**: Add your own categorization patterns
        
        **Supported Banks:** Chase, Wells Fargo, Bank of America, and others
        
        **Note:** This tool works best with text-based PDFs that contain transaction tables.
        Scanned PDFs (images) are not supported without OCR.
        """)

if __name__ == "__main__":
    main_ui()