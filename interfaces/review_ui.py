import streamlit as st
import pandas as pd
from core import analyzer

def create_categorization_interface(df: pd.DataFrame) -> pd.DataFrame:
    """Create interactive interface for reviewing and correcting categorizations"""
    
    st.subheader("🎯 Categorization Review & Correction")
    
    # Add confidence scores
    df_with_confidence = analyzer.add_categorization_confidence(df)
    
    # Show categorization statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        high_conf = len(df_with_confidence[df_with_confidence['confidence'] == 'High'])
        st.metric("High Confidence", f"{high_conf}/{len(df)}")
    
    with col2:
        medium_conf = len(df_with_confidence[df_with_confidence['confidence'] == 'Medium'])
        st.metric("Medium Confidence", f"{medium_conf}/{len(df)}")
    
    with col3:
        low_conf = len(df_with_confidence[df_with_confidence['confidence'] == 'Low'])
        st.metric("Low Confidence", f"{low_conf}/{len(df)}")
    
    # Show suggestions for review
    suggestions = analyzer.suggest_category_corrections(df_with_confidence)
    
    if suggestions:
        st.warning(f"⚠️ Found {len(suggestions)} transactions that might need review:")
        
        for suggestion in suggestions[:5]:  # Show top 5 suggestions
            with st.expander(f"Review: {suggestion['description'][:50]}..."):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Current:** {suggestion['current_category']}")
                    st.write(f"**Suggested:** {suggestion['suggested_category']}")
                    st.write(f"**Reason:** {suggestion['reason']}")
                
                with col2:
                    # Allow user to select correct category
                    all_categories = sorted(df['category'].unique().tolist())
                    correct_category = st.selectbox(
                        "Correct category:",
                        all_categories,
                        index=all_categories.index(suggestion['current_category']),
                        key=f"correct_{suggestion['index']}"
                    )
                    
                    if st.button(f"Update", key=f"update_{suggestion['index']}"):
                        df.loc[suggestion['index'], 'category'] = correct_category
                        st.success("✅ Updated!")
                        st.rerun()
    
    # Manual categorization interface
    st.subheader("✏️ Manual Category Corrections")
    
    # Filter for low confidence transactions
    low_confidence_df = df_with_confidence[df_with_confidence['confidence'] == 'Low'].copy()
    
    if not low_confidence_df.empty:
        st.write("**Low Confidence Transactions (might need manual review):**")
        
        # Reset index to ensure continuity and add a unique identifier
        low_confidence_df = low_confidence_df.reset_index(drop=False)
        low_confidence_df.rename(columns={'index': 'original_index'}, inplace=True)
        
        # Create editable dataframe with the reset index
        display_columns = ['date', 'description', 'amount', 'category', 'confidence']
        
        edited_df = st.data_editor(
            low_confidence_df[display_columns],
            column_config={
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Select the correct category",
                    width="medium",
                    options=sorted(df['category'].unique().tolist()),
                ),
                "date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD",
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount",
                    format="$%.2f",
                ),
            },
            disabled=["date", "description", "amount", "confidence"],
            hide_index=True,
            use_container_width=True,
        )
        
        # Update the main dataframe with changes
        # Use the original_index to map back correctly
        if len(edited_df) == len(low_confidence_df):
            for idx in range(len(edited_df)):
                if idx < len(low_confidence_df):  # Safety check
                    original_idx = low_confidence_df.iloc[idx]['original_index']
                    new_category = edited_df.iloc[idx]['category']
                    
                    # Only update if category changed
                    if df.loc[original_idx, 'category'] != new_category:
                        df.loc[original_idx, 'category'] = new_category
        else:
            st.warning("⚠️ Row count mismatch detected. Please refresh to continue editing.")
    
    else:
        st.info("✅ All transactions have high or medium confidence scores!")
    
    return df
