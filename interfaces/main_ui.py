import streamlit as st
import pandas as pd
from datetime import datetime
from core.categorizer import TransactionCategorizer
from core.parser import parse_pdf_statement, create_transaction_type_summary
from utils.visualizations import show_all_enhanced_visualizations
from utils.vis  import show_sankey_flow_diagram, show_enhanced_transaction_table

# Modern theme system using CSS variables
def load_custom_css():
    st.markdown("""
    <style>
    /* Import the theme variables */
    :root {
      --background: hsl(0, 0%, 100%);
      --foreground: hsl(20, 14.3%, 4.1%);
      --muted: hsl(60, 4.8%, 95.9%);
      --muted-foreground: hsl(25, 5.3%, 44.7%);
      --popover: hsl(0, 0%, 100%);
      --popover-foreground: hsl(20, 14.3%, 4.1%);
      --card: hsl(0, 0%, 100%);
      --card-foreground: hsl(20, 14.3%, 4.1%);
      --border: hsl(20, 5.9%, 90%);
      --input: hsl(20, 5.9%, 90%);
      --primary: hsl(207, 90%, 54%);
      --primary-foreground: hsl(211, 100%, 99%);
      --secondary: hsl(60, 4.8%, 95.9%);
      --secondary-foreground: hsl(24, 9.8%, 10%);
      --accent: hsl(60, 4.8%, 95.9%);
      --accent-foreground: hsl(24, 9.8%, 10%);
      --destructive: hsl(0, 84.2%, 60.2%);
      --destructive-foreground: hsl(60, 9.1%, 97.8%);
      --ring: hsl(20, 14.3%, 4.1%);
      --radius: 0.5rem;
      --chart-1: hsl(207, 90%, 54%);
      --chart-2: hsl(142, 76%, 36%);
      --chart-3: hsl(45, 93%, 47%);
      --chart-4: hsl(262, 83%, 58%);
      --chart-5: hsl(12, 76%, 61%);
      --sidebar-background: hsl(0, 0%, 98%);
      --sidebar-foreground: hsl(20, 14.3%, 4.1%);
      --sidebar-primary: hsl(207, 90%, 54%);
      --sidebar-primary-foreground: hsl(211, 100%, 99%);
      --sidebar-accent: hsl(60, 4.8%, 95.9%);
      --sidebar-accent-foreground: hsl(24, 9.8%, 10%);
      --sidebar-border: hsl(20, 5.9%, 90%);
      --sidebar-ring: hsl(20, 14.3%, 4.1%);
    }

    .dark {
      --background: hsl(240, 10%, 3.9%);
      --foreground: hsl(0, 0%, 98%);
      --muted: hsl(240, 3.7%, 15.9%);
      --muted-foreground: hsl(240, 5%, 64.9%);
      --popover: hsl(240, 10%, 3.9%);
      --popover-foreground: hsl(0, 0%, 98%);
      --card: hsl(240, 10%, 3.9%);
      --card-foreground: hsl(0, 0%, 98%);
      --border: hsl(240, 3.7%, 15.9%);
      --input: hsl(240, 3.7%, 15.9%);
      --primary: hsl(207, 90%, 54%);
      --primary-foreground: hsl(211, 100%, 99%);
      --secondary: hsl(240, 3.7%, 15.9%);
      --secondary-foreground: hsl(0, 0%, 98%);
      --accent: hsl(240, 3.7%, 15.9%);
      --accent-foreground: hsl(0, 0%, 98%);
      --destructive: hsl(0, 62.8%, 30.6%);
      --destructive-foreground: hsl(0, 0%, 98%);
      --ring: hsl(240, 4.9%, 83.9%);
      --chart-1: hsl(207, 90%, 54%);
      --chart-2: hsl(142, 76%, 36%);
      --chart-3: hsl(45, 93%, 47%);
      --chart-4: hsl(262, 83%, 58%);
      --chart-5: hsl(12, 76%, 61%);
      --sidebar-background: hsl(240, 5.9%, 10%);
      --sidebar-foreground: hsl(0, 0%, 98%);
      --sidebar-primary: hsl(207, 90%, 54%);
      --sidebar-primary-foreground: hsl(211, 100%, 99%);
      --sidebar-accent: hsl(240, 3.7%, 15.9%);
      --sidebar-accent-foreground: hsl(0, 0%, 98%);
      --sidebar-border: hsl(240, 3.7%, 15.9%);
      --sidebar-ring: hsl(240, 4.9%, 83.9%);
    }

    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background: hsl(var(--background));
        color: hsl(var(--foreground));
        transition: background-color 0.3s ease, color 0.3s ease;
    }
    
    /* Header styling */
    .main-header {
        background: hsl(var(--primary));
        background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--chart-4)) 100%);
        padding: 2rem;
        border-radius: var(--radius);
        color: hsl(var(--primary-foreground));
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px hsl(var(--foreground) / 0.2);
    }
    
    .main-header p {
        margin: 1rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Feature cards */
    .feature-card {
        background: hsl(var(--card));
        color: hsl(var(--card-foreground));
        padding: 1.5rem;
        border-radius: var(--radius);
        border: 1px solid hsl(var(--border));
        border-left: 4px solid hsl(var(--primary));
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: fade-in 0.3s ease-out;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px hsl(var(--foreground) / 0.15);
    }
    
    .feature-card h3 {
        color: hsl(var(--primary));
        margin-bottom: 0.5rem;
    }
    
    .feature-card ul {
        color: hsl(var(--muted-foreground));
        font-size: 0.9rem;
    }
    
    /* Success/error styling */
    .success-box {
        background: hsl(var(--chart-2));
        background: linear-gradient(135deg, hsl(var(--chart-2)) 0%, hsl(var(--chart-2) / 0.8) 100%);
        color: hsl(var(--primary-foreground));
        padding: 1rem;
        border-radius: var(--radius);
        margin: 1rem 0;
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    .error-box {
        background: hsl(var(--destructive));
        background: linear-gradient(135deg, hsl(var(--destructive)) 0%, hsl(var(--destructive) / 0.8) 100%);
        color: hsl(var(--destructive-foreground));
        padding: 1rem;
        border-radius: var(--radius);
        margin: 1rem 0;
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    /* Upload area styling */
    .upload-area {
        border: 2px dashed hsl(var(--primary));
        border-radius: var(--radius);
        padding: 2rem;
        text-align: center;
        background: hsl(var(--muted));
        margin: 1rem 0;
        transition: all 0.2s ease;
    }
    
    .upload-area:hover {
        background: hsl(var(--accent));
        border-color: hsl(var(--primary) / 0.8);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: hsl(var(--sidebar-background)) !important;
        border-right: 1px solid hsl(var(--sidebar-border));
    }
    
    /* Button styling */
    .stButton > button {
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        border: 1px solid hsl(var(--primary));
        border-radius: var(--radius);
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: hsl(var(--primary) / 0.9);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px hsl(var(--foreground) / 0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: hsl(var(--card));
        color: hsl(var(--card-foreground));
        padding: 1.5rem;
        border-radius: var(--radius);
        text-align: center;
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.1);
        margin-bottom: 1rem;
        border: 1px solid hsl(var(--border));
        border-top: 4px solid hsl(var(--primary));
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        animation: fade-in 0.3s ease-out;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px hsl(var(--foreground) / 0.15);
    }
    
    /* Section headers */
    .section-header {
        background: hsl(var(--primary));
        background: linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--chart-4)) 100%);
        color: hsl(var(--primary-foreground));
        padding: 1rem 1.5rem;
        border-radius: var(--radius);
        margin: 2rem 0 1rem 0;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    /* File info styling */
    .file-info {
        background: hsl(var(--chart-1));
        background: linear-gradient(135deg, hsl(var(--chart-1)) 0%, hsl(var(--chart-1) / 0.8) 100%);
        color: hsl(var(--primary-foreground));
        padding: 1rem;
        border-radius: var(--radius);
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    /* Progress indicators */
    .progress-step {
        display: inline-block;
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        padding: 0.5rem 1rem;
        border-radius: 1rem;
        margin: 0.25rem;
        font-size: 0.9rem;
        font-weight: 500;
        animation: fade-in 0.3s ease-out;
    }
    
    /* Warning box */
    .warning-box {
        background: hsl(var(--chart-3));
        background: linear-gradient(135deg, hsl(var(--chart-3)) 0%, hsl(var(--chart-3) / 0.8) 100%);
        color: hsl(var(--foreground));
        padding: 1rem;
        border-radius: var(--radius);
        margin: 1rem 0;
        box-shadow: 0 2px 4px hsl(var(--foreground) / 0.1);
        animation: fade-in 0.3s ease-out;
    }
    
    /* Chart containers */
    .chart-container {
        background: hsl(var(--card));
        color: hsl(var(--card-foreground));
        padding: 1rem;
        border-radius: var(--radius);
        border: 1px solid hsl(var(--border));
        box-shadow: 0 4px 6px hsl(var(--foreground) / 0.05);
        margin: 1rem 0;
        animation: fade-in 0.3s ease-out;
    }
    
    /* Financial styling */
    .financial-positive {
        color: hsl(var(--chart-2));
        font-weight: 600;
    }
    
    .financial-negative {
        color: hsl(var(--destructive));
        font-weight: 600;
    }
    
    /* Custom animations */
    @keyframes fade-in {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Smooth transitions */
    * {
        transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: hsl(var(--muted-foreground) / 0.3);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: hsl(var(--muted-foreground) / 0.5);
    }
    
    /* Streamlit overrides */
    .stSelectbox > div > div {
        background: hsl(var(--input));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
    }
    
    .stDateInput > div > div {
        background: hsl(var(--input));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
    }
    
    .stCheckbox > label {
        color: hsl(var(--foreground));
    }
    
    .stSlider > div > div > div {
        background: hsl(var(--primary));
    }
    </style>
    """, unsafe_allow_html=True)

def create_enhanced_deduplication_config():
    """Create enhanced UI for configuring deduplication settings"""
    
    st.sidebar.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    ">
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
    <div class="main-header">
        <h1>💰 Smart Bank Statement Analyzer</h1>
        <p>AI-powered transaction analysis with intelligent categorization and duplicate detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🧠 AI Categorization</h3>
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
    <div class="section-header">
        📋 How to Get Started
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
        - Watch as AI processes and categorizes transactions
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
    <div class="upload-area">
        <h3>🎯 Ready to Start?</h3>
        <p>Upload your bank statement PDF files below</p>
    </div>
    """, unsafe_allow_html=True)

def show_processing_progress(uploaded_files):
    """Show enhanced processing progress"""
    
    st.markdown("""
    <div class="section-header">
        🔄 Processing Your Files
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
        <span class="progress-step">📖 Reading PDFs</span>
        <span class="progress-step">🧠 AI Categorization</span>
        <span class="progress-step">🔍 Duplicate Detection</span>
        <span class="progress-step">📊 Analytics Generation</span>
    </div>
    """, unsafe_allow_html=True)

def show_success_summary(df):
    """Show enhanced success summary"""
    
    total_transactions = len(df)
    date_range = ""
    if 'date' in df.columns and not df['date'].isna().all():
        date_range = f" from {df['date'].min().strftime('%b %d, %Y')} to {df['date'].max().strftime('%b %d, %Y')}"
    
    st.markdown(f"""
    <div class="success-box">
        <h3 style="margin: 0;">✅ Processing Complete!</h3>
        <p style="margin: 0.5rem 0 0 0;">Successfully analyzed <strong>{total_transactions:,} transactions</strong>{date_range}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick overview
    col1, col2, col3, col4 = st.columns(4)
    
    income_mask = (df['category'] == 'Income')
    # total_income = df[income_mask & (df['amount'] > 0)]['amount'].sum()
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
            <div class="metric-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.25rem;">{label}</div>
                <div style="font-size: 1.3rem; font-weight: bold; color: #333;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def main_ui():
    """Enhanced main UI function"""
    
    # Set page config
    st.set_page_config(
        page_title="Smart Bank Statement Analyzer",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_custom_css()
    
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
            <div class="warning-box">
                <strong>⚠️ Multiple Files Detected</strong><br>
                The system will automatically detect and remove duplicates between files. 
                Review deduplication settings in the sidebar if needed.
            </div>
            """, unsafe_allow_html=True)
        
        # Process files
        with st.spinner("🔄 Processing with AI-powered analysis..."):
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
            <div class="section-header">
                💾 Export & Actions
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
            <div class="error-box">
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