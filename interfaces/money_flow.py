import streamlit as st
import pandas as pd
from datetime import datetime
from core.categorizer import TransactionCategorizer
from core.parser import parse_pdf_statement, create_transaction_type_summary
from utils.visualizations import show_all_enhanced_visualizations
from utils.vis import show_sankey_flow_diagram, show_enhanced_transaction_table

# interfaces/money_flow.py


def money_flow_interface():
    """Main interface for Money Flow Analysis"""
    st.title("💸 Money Flow Dashboard")

    st.markdown(
        """
        Upload your bank statement PDFs, and see how your money flows 
        from **income sources** to **expense categories**.
        """
    )

    uploaded_files = st.file_uploader(
        "Upload PDF bank statements",
        type=["pdf"],
        accept_multiple_files=True
    )

    if not uploaded_files:
        st.info("Please upload at least one PDF to proceed.")
        return

    # Parse uploaded PDFs
    dfs = []
    for uploaded_file in uploaded_files:
        df = parse_pdf_statement(uploaded_file)
        dfs.append(df)

    if not dfs:
        st.error("No transactions found in the uploaded files.")
        return

    # Combine all parsed data
    transactions_df = pd.concat(dfs, ignore_index=True)

    # Categorize transactions
    categorizer = TransactionCategorizer()
    transactions_df = categorizer.categorize(transactions_df)

    st.success(f"Parsed {len(transactions_df)} transactions from {len(uploaded_files)} file(s).")

    # Show Sankey Flow Diagram
    show_sankey_flow_diagram(transactions_df)

    # Show Enhanced Transaction Table
    show_enhanced_transaction_table(transactions_df, uploaded_files)
