import streamlit as st
from interfaces import main_ui
from interfaces import review_ui
from interfaces import rules_ui
from interfaces import investment_tracker

def main():
    # Initialize session state
    if 'transactions_df' not in st.session_state:
        st.session_state['transactions_df'] = None
        
    tab1, tab2, tab3,tab4 = st.tabs(["📄 Upload & Analyze", "🎯 Review Categories", "🔧 Custom Rules", "Investment Tracker"])
    
    with tab1:
        main_ui.main_ui()

   
    with tab2:
        if st.session_state['transactions_df'] is not None:
            df = st.session_state['transactions_df']
            updated_df = review_ui.create_categorization_interface(df)
            st.session_state['transactions_df'] = updated_df
    
    with tab3:
        rules_ui.create_custom_rules_interface()
        # kf

    with tab4:
        investment_tracker.show_investment_dashboard()

if __name__ == "__main__":
    main()