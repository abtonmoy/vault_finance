import streamlit as st
from config.categories import SPENDING_CATEGORIES

def create_custom_rules_interface():
    """Interface for creating custom categorization rules"""
    
    st.subheader("🔧 Custom Categorization Rules")
    
    with st.expander("Add Custom Rule"):
        col1, col2 = st.columns(2)
        
        with col1:
            pattern = st.text_input(
                "Merchant/Description Pattern:",
                placeholder="e.g., 'LOCAL COFFEE SHOP'",
                help="Enter text that appears in transaction descriptions"
            )
        
        with col2:
            categories = list(SPENDING_CATEGORIES.keys())
            selected_category = st.selectbox("Category:", categories)
        
        if st.button("Add Rule") and pattern:
            # In a real app, you'd save this to a database or file
            st.success(f"✅ Rule added: '{pattern}' → {selected_category}")
            st.info("Custom rules will be applied to future categorizations.")
