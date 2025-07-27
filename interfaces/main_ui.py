import streamlit as st
import pandas as pd
from datetime import datetime
from core.categorizer import TransactionCategorizer
from core.parser import parse_pdf_statement, create_transaction_type_summary
from utils.visualizations import show_all_enhanced_visualizations
from utils.vis  import show_sankey_flow_diagram, show_enhanced_transaction_table

def create_enhanced_deduplication_config():
    """Create enhanced UI for configuring deduplication settings"""
    
    st.sidebar.markdown("""
    <div class="settings-gradient">
        <h3 style="margin: 0;">🔧 Settings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("🔍 Duplicate Removal", expanded=True):
        remove_cc_duplicates = st.checkbox(
            "Handle Credit Card Payments",
            value=True,
            help="Remove credit card payment summaries when individual charges are present"
        )
        
        remove_transfer_duplicates = st.checkbox(
            "Remove Duplicate Transfers",
            value=True,
            help="Remove duplicate transfer transactions between accounts"
        )
        
        aggressive_deduplication = st.checkbox(
            "Aggressive Deduplication",
            value=False,
            help="Use fuzzy matching to find similar transactions (may remove legitimate transactions)"
        )
    
    with st.sidebar.expander("⚙️ Advanced Settings", expanded=False):
        st.markdown("**Credit Card Payment Matching:**")
        cc_date_window = st.slider(
            "Payment cycle window (days)",
            min_value=30,
            max_value=60,
            value=45,
            help="How far back to look for charges when matching payments"
        )
        
        cc_amount_tolerance = st.slider(
            "Payment amount tolerance (%)",
            min_value=5,
            max_value=25,
            value=15,
            help="Allowed difference between payment and charges"
        ) / 100
        
        if aggressive_deduplication:
            st.markdown("**Fuzzy Matching Settings:**")
            fuzzy_date_window = st.slider(
                "Date window for similar transactions",
                min_value=1,
                max_value=7,
                value=2,
                help="Days to look for similar transactions"
            )
            
            description_threshold = st.slider(
                "Description similarity threshold",
                min_value=70,
                max_value=95,
                value=85,
                help="How similar descriptions must be to consider duplicates"
            )
        else:
            fuzzy_date_window = 2
            description_threshold = 85
    
    # Quick stats in sidebar
    if 'transactions_df' in st.session_state and st.session_state['transactions_df'] is not None:
        df = st.session_state['transactions_df']
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Quick Stats")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Transactions", f"{len(df):,}")
            income = df[df['amount'] > 0]['amount'].sum()
            st.metric("Income", f"${income:,.0f}")
        
        with col2:
            categories = df['category'].nunique()
            st.metric("Categories", f"{categories}")
            expenses = abs(df[df['amount'] < 0]['amount'].sum())
            st.metric("Expenses", f"${expenses:,.0f}")
    
    return {
        'remove_credit_card_duplicates': remove_cc_duplicates,
        'remove_transfer_duplicates': remove_transfer_duplicates,
        'aggressive_deduplication': aggressive_deduplication,
        'cc_date_window': cc_date_window,
        'cc_amount_tolerance': cc_amount_tolerance,
        'fuzzy_date_window': fuzzy_date_window,
        'description_threshold': description_threshold
    }

def show_welcome_screen():
    """Show enhanced welcome screen with better design"""
    
    # Main header
    st.markdown("""
    <div class="gradient-header">
        <h1 style="margin: 0;"> Personal Vault </h1>
        <p style="margin: 0.5rem 0 0 0;">transaction analysis with auto categorization and duplicate detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>Algorithmic Categorization</h3>
            <p>Advanced machine learning automatically categorizes your transactions with high accuracy</p>
            <ul>
                <li>Fuzzy merchant matching</li>
                <li>Amount-based rules</li>
                <li>Timing pattern analysis</li>
                <li>Multi-pass categorization</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🔍 Smart Deduplication</h3>
            <p>Intelligent duplicate detection handles complex financial scenarios</p>
            <ul>
                <li>Credit card payment cycles</li>
                <li>Transfer deduplication</li>
                <li>Fuzzy transaction matching</li>
                <li>Multi-file support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Advanced Analytics</h3>
            <p>Comprehensive financial insights and beautiful visualizations</p>
            <ul>
                <li>Interactive dashboards</li>
                <li>Spending pattern analysis</li>
                <li>Monthly trend tracking</li>
                <li>Category deep dives</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    <div class="gradient-header">
        <h3 style="margin: 0;">📋 How to Get Started</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Step-by-Step Guide:
        
        **1. 📥 Download Your Statements**
        - Log into your online banking portal
        - Download **text-based PDF** statements (not scanned images)
        - Multiple files from different accounts are supported
        
        **2. ⚙️ Configure Settings**
        - Adjust deduplication settings in the sidebar
        - Choose your preferred categorization options
        - Enable advanced features as needed
        
        **3. 🚀 Upload and Analyze**
        - Upload your PDF files using the uploader
        - Watch as algorithm processes and categorizes transactions
        - Explore interactive dashboards and insights
        
        **4. 📊 Export Results**
        - Download processed data as CSV
        - Share insights with financial advisors
        - Track spending trends over time
        """)
    
    with col2:
        st.markdown("""
        ### 🏦 Supported Banks:
        
        **Fully Tested:**
        - ✅ Chase Bank
        - ✅ Wells Fargo
        - ✅ Bank of America
        - ✅ Citibank
        
        **Generally Compatible:**
        - 🔄 Most major US banks
        - 🔄 Credit unions
        - 🔄 Online banks
        
        ### 🔒 Privacy & Security:
        - 🛡️ 100% local processing
        - 🚫 No data uploaded to servers
        - 🔐 Your data stays private
        - ⚡ Real-time analysis
        """)
    
    # Upload area
    st.markdown("""
    <div class="gradient-card" style="text-align: center; margin-top: 2rem;">
        <h3 style="margin-top: 0;">🎯 Ready to Start?</h3>
        <p>Upload your bank statement PDF files below</p>
    </div>
    """, unsafe_allow_html=True)

def show_processing_progress(uploaded_files):
    """Show enhanced processing progress"""
    
    st.markdown("""
    <div class="gradient-header">
        <h3 style="margin: 0;">🔄 Processing Your Files</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Show files being processed
    for i, file in enumerate(uploaded_files, 1):
        st.markdown(f"""
        <div class="file-info">
            <strong>📄 {file.name}</strong> ({file.size / 1024:.1f} KB)
        </div>
        """, unsafe_allow_html=True)
    
    # Processing steps
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <span class="progress-step"> Reading PDFs</span>
        <span class="progress-step"> Auto Categorization</span>
        <span class="progress-step"> Duplicate Detection</span>
        <span class="progress-step"> Analytics Generation</span>
    </div>
    """, unsafe_allow_html=True)

def show_success_summary(df):
    """Show enhanced success summary"""
    
    total_transactions = len(df)
    date_range = ""
    if 'date' in df.columns and not df['date'].isna().all():
        date_range = f" from {df['date'].min().strftime('%b %d, %Y')} to {df['date'].max().strftime('%b %d, %Y')}"
    
    st.markdown(f"""
    <div class="gradient-card">
        <h3 style="margin: 0;">✅ Processing Complete!</h3>
        <p style="margin: 0.5rem 0 0 0;">Successfully analyzed <strong>{total_transactions:,} transactions</strong>{date_range}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick overview
    col1, col2, col3, col4 = st.columns(4)
    
    income_mask = (df['category'] == 'Income')
    total_income = df[df['amount'] > 0]['amount'].sum()
    expense_mask = (df['category'] != 'Transfer') & (df['category'] != 'Income')
    total_expenses = abs(df[expense_mask & (df['amount'] < 0)]['amount'].sum())
    categories = df['category'].nunique()
    files = df['source_file'].nunique() if 'source_file' in df.columns else 1
    
    metrics = [
        ("💰", "Total Income", f"${total_income:,.2f}"),
        ("💸", "Total Expenses", f"${total_expenses:,.2f}"),
        ("📂", "Categories", f"{categories}"),
        ("📄", "Files Processed", f"{files}")
    ]
    
    for i, (icon, label, value) in enumerate(metrics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div class="gradient-metric">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="font-size: 0.9rem; margin-bottom: 0.25rem;">{label}</div>
                <div style="font-size: 1.3rem; font-weight: bold;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def main_ui():
    """ main UI function"""
    
    # Set page config
    st.set_page_config(
        page_title="Vault Finances",
        page_icon="assets/icon.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'transactions_df' not in st.session_state:
        st.session_state['transactions_df'] = None
    
    # Get deduplication configuration from sidebar
    dedup_config = create_enhanced_deduplication_config()
    
    # Main content
    uploaded_files = st.file_uploader(
        "",
        type="pdf",
        accept_multiple_files=True,
        help="Upload text-based PDF bank statements from major banks"
    )
    
    if uploaded_files:
        # Show processing progress
        show_processing_progress(uploaded_files)
        
        # Warning for multiple files
        if len(uploaded_files) > 1:
            st.markdown("""
            <div class="warning-gradient">
                <strong>⚠️ Multiple Files Detected</strong><br>
                The system will automatically detect and remove duplicates between files. 
                Review deduplication settings in the sidebar if needed.
            </div>
            """, unsafe_allow_html=True)
        
        # Process files
        with st.spinner("🔄 Processing..."):
            df = parse_pdf_statement(uploaded_files, dedup_config)
        
        if df is not None and not df.empty:
            # Store in session state
            st.session_state['transactions_df'] = df
            
            # Show success summary
            show_success_summary(df)

            # sankey diagram
            show_sankey_flow_diagram(df)
            
            # Transaction type analysis
            create_transaction_type_summary(df)

            
            # show_enhanced_transaction_table(df, uploaded_files)
            
            # Show all enhanced visualizations
            show_all_enhanced_visualizations(df, uploaded_files)

            #
            
            # Export section
            st.markdown("""
            <div class="gradient-header">
                <h3 style="margin: 0;">💾 Export & Actions</h3>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"bank_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Create summary report
                summary_data = f"""
Bank Statement Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Summary:
- Total Transactions: {len(df):,}
- Total Income: ${df[df['amount'] > 0]['amount'].sum():,.2f}
- Total Expenses: ${abs(df[df['amount'] < 0]['amount'].sum()):,.2f}
- Categories: {df['category'].nunique()}
- Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}

Top Spending Categories:
"""
                spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')]
                if not spending_df.empty:
                    top_categories = spending_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False).head(5)
                    for cat, amount in top_categories.items():
                        summary_data += f"- {cat}: ${amount:,.2f}\n"
                
                st.download_button(
                    label="📋 Download Summary",
                    data=summary_data,
                    file_name=f"statement_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col3:
                if st.button("🔄 Process New Files", use_container_width=True):
                    st.session_state['transactions_df'] = None
                    st.rerun()
            
            with col4:
                if st.button("📊 Generate Report", use_container_width=True):
                    st.balloons()
                    st.success("Report generated! Check the download buttons above.")
        
        else:
            # Enhanced error message
            st.markdown("""
            <div class="error-gradient">
                <h3 style="margin: 0;">❌ Processing Failed</h3>
                <p style="margin: 0.5rem 0 0 0;">No valid transactions could be extracted from the uploaded files.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("🔧 Troubleshooting Guide", expanded=True):
                st.markdown("""
                ### Common Issues and Solutions:
                
                **📄 PDF Format Issues:**
                - Ensure PDFs contain actual text (not scanned images)
                - Try downloading statements in different formats from your bank
                - Some mobile banking PDFs may not work - use desktop/web versions
                
                **🏦 Bank Compatibility:**
                - Works best with Chase, Wells Fargo, Bank of America
                - Other banks may need format adjustments
                - Contact support if your bank isn't recognized
                
                **📊 Data Quality:**
                - Check if PDFs have transactions in table format
                - Ensure date ranges contain actual transactions
                - Account summary pages won't work - need transaction details
                
                **🔧 Technical Solutions:**
                - Try uploading one file at a time
                - Ensure files are under 200MB each
                - Clear browser cache and retry
                """)
    
    else:
        # Show welcome screen
        show_welcome_screen()

if __name__ == "__main__":
    main_ui()