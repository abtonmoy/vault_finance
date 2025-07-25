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