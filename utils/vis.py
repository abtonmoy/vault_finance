import streamlit as st
import plotly.graph_objects as go
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from utils.theme import THEME_COLORS, THEME_GRADIENTS, get_gradient_color, get_theme_background, get_theme_border, get_theme_text_color

def hex_to_rgba(hex_color, alpha=0.6):
    """Convert hex color to RGBA with specified alpha transparency."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

def show_sankey_flow_diagram(df):
    """Create a modern Sankey diagram with flows starting from source color, transparent in the middle, transitioning to target color."""
    st.markdown("### 💰 Money Flow Analysis")
    
    # Prepare data for Sankey diagram
    income_df = df[(df['amount'] > 0) & (df['category'] == 'Income')].copy()
    expense_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if income_df.empty and expense_df.empty:
        st.info("No income or expense data available for flow analysis.")
        return
    
    # Color palette matching the image
    income_colors = [
        "#0A6397",  # Light blue (Paycheck)
        "#5BA3F5",  # Medium blue
        "#6CB6FF",  # Bright blue
        "#7DC9FF",  # Light cyan
        "#8EDCFF"   # Very light cyan
    ]
    
    expense_colors = [
        "#FF6B6B",  # Red (Shopping)
        "#F1C40F",  # Yellow (Housing)
        "#E91E63",  # Pink (Financial)
        "#4A90E2",  # Light blue (Bills & Utilities)
        "#FF9800",  # Orange (Food & Dining)
        "#9B59B6",  # Purple (Travel & Lifestyle)
        "#2ECC71"   # Green (Savings)
    ]
    
    # Create nodes and links
    nodes = []
    links = []
    node_colors = []
    link_colors = []
    
    # Income sources
    income_sources = {}
    total_income_amount = income_df['amount'].sum() if not income_df.empty else 0
    if not income_df.empty:
        income_by_source = income_df.groupby('description')['amount'].sum().sort_values(ascending=False)
        for i, (source, amount) in enumerate(income_by_source.items()):
            source_name = source[:25] + "..." if len(source) > 25 else source
            percentage = (amount / total_income_amount * 100) if total_income_amount > 0 else 0
            income_sources[source] = len(nodes)
            nodes.append(f"{source_name}\n${amount:,.2f} ({percentage:.2f}%)")
            node_colors.append(income_colors[i % len(income_colors)])
    
    # Add "Available Funds" node
    available_funds_idx = len(nodes)
    nodes.append(f"Available Funds\n${total_income_amount:,.2f} (100%)")
    node_colors.append("#5BA3F5")  # Darker blue like "Income" in the image
    
    # Expense categories
    expense_categories = {}
    if not expense_df.empty:
        expense_by_category = expense_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
        for i, (category, amount) in enumerate(expense_by_category.items()):
            percentage = (amount / total_income_amount * 100) if total_income_amount > 0 else 0
            expense_categories[category] = len(nodes)
            nodes.append(f"{category}\n${amount:,.2f} ({percentage:.2f}%)")
            node_colors.append(expense_colors[i % len(expense_colors)])
    
    # Net Savings
    total_expense_amount = expense_df['amount'].abs().sum() if not expense_df.empty else 0
    net_income = total_income_amount - total_expense_amount
    if net_income > 0:
        savings_idx = len(nodes)
        percentage = (net_income / total_income_amount * 100) if total_income_amount > 0 else 0
        nodes.append(f"Net Savings\n${net_income:,.2f} ({percentage:.2f}%)")
        node_colors.append("#04622B")  # Green for savings
    
    # Links from income sources to Available Funds
    if not income_df.empty:
        for i, (source, amount) in enumerate(income_by_source.items()):
            source_idx = income_sources[source]
            links.append({
                'source': source_idx,
                'target': available_funds_idx,
                'value': amount
            })
            link_colors.append(hex_to_rgba(node_colors[source_idx], 0.6))
    
    # Links from Available Funds to expense categories
    if not expense_df.empty and total_income_amount > 0:
        for i, (category, amount) in enumerate(expense_by_category.items()):
            links.append({
                'source': available_funds_idx,
                'target': expense_categories[category],
                'value': amount
            })
            link_colors.append(hex_to_rgba(node_colors[available_funds_idx], 0.6))
    
    # Link for savings
    if net_income > 0:
        links.append({
            'source': available_funds_idx,
            'target': savings_idx,
            'value': net_income
        })
        link_colors.append(hex_to_rgba(node_colors[available_funds_idx], 0.6))
    
    if not links:
        st.info("Insufficient data to create money flow diagram.")
        return
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=25,
            thickness=30,
            line=dict(color="rgba(255,255,255,0.8)", width=0),
            label=nodes,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>Total Flow: $%{value:,.0f}<extra></extra>",
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links],
            color=link_colors,
            hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>" +
                         "Amount: $%{value:,.0f}<extra></extra>",
            line=dict(width=0.0, color="rgba(255,255,255,0.2)")
        )
    )])
    
    # Update layout to match the image
    fig.update_layout(
        title=dict(
            text="Financial Flow: Income → Available Funds → Expenses",
            x=0.5,
            font=dict(size=20, family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", color="#000000")
        ),
        height=650,
        paper_bgcolor="white",
        plot_bgcolor="aliceblue",
        margin=dict(l=40, r=40, t=80, b=40),
        hoverlabel=dict(
            font=dict(
                color="black",
                size=14,
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
            ),
            bgcolor="rgba(255, 255, 255, 0.95)",
            bordercolor="rgba(0,0,0,0.2)",
            align="left"
        ),
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            color="black",
            size=12
        )
    )
    
    # Display the Sankey diagram
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'displaylogo': False
    })
    
    # Summary cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #4A90E2 0%, #5BA3F5 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 32px rgba(74, 144, 226, 0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💰</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem; font-weight: 500;">Income Sources</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{len(income_sources)}</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">${total_income_amount:,.0f} total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📊</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem; font-weight: 500;">Expense Categories</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{len(expense_categories)}</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">${total_expense_amount:,.0f} total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        flow_efficiency = (total_expense_amount / total_income_amount * 100) if total_income_amount > 0 else 0
        efficiency_color = "#2ECC71" if flow_efficiency < 80 else "#F39C12" if flow_efficiency < 95 else "#E74C3C"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {efficiency_color} 0%, {efficiency_color}CC 100%);
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            text-align: center;
            box-shadow: 0 8px 32px rgba(46, 204, 113, 0.3);
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        ">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚡</div>
            <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.5rem; font-weight: 500;">Flow Efficiency</div>
            <div style="font-size: 1.8rem; font-weight: bold;">{flow_efficiency:.0f}%</div>
            <div style="font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem;">of income allocated</div>
        </div>
        """, unsafe_allow_html=True)

# Rest of the file remains unchanged
def show_enhanced_transaction_table(df, uploaded_files):
    """Enhanced transaction table with better filtering and modern styling"""
    st.markdown("### 📋 Transaction Explorer")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        categories = ['All'] + sorted(df['category'].unique().tolist())
        selected_category = st.selectbox("📂 Category", categories)
    
    with col2:
        if 'source_file' in df.columns:
            files = ['All'] + sorted(df['source_file'].unique().tolist())
            selected_file = st.selectbox("📄 File", files)
        else:
            selected_file = 'All'
    
    with col3:
        amount_filter = st.selectbox("💰 Amount Filter", ['All', 'Income Only', 'Expenses Only', 'Large Transactions (>$100)'])
    
    with col4:
        if 'date' in df.columns and not df['date'].isna().all():
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            date_range = st.date_input("📅 Date Range", value=(min_date, max_date), max_value=max_date, min_value=min_date)
        else:
            date_range = None
    
    filtered_df = df.copy()
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if selected_file != 'All' and 'source_file' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['source_file'] == selected_file]
    
    if amount_filter == 'Income Only':
        filtered_df = filtered_df[filtered_df['amount'] > 0]
    elif amount_filter == 'Expenses Only':
        filtered_df = filtered_df[filtered_df['amount'] < 0]
    elif amount_filter == 'Large Transactions (>$100)':
        filtered_df = filtered_df[filtered_df['amount'].abs() > 100]
    
    if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        if 'date' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #2E8B8B 0%, #4A90E2 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        font-weight: 500;
    ">
        📊 Showing {len(filtered_df):,} of {len(df):,} transactions
    </div>
    """, unsafe_allow_html=True)
    
    display_cols = ['date', 'description', 'amount', 'category']
    if 'source_file' in filtered_df.columns and len(uploaded_files) > 1:
        display_cols.append('source_file')
    
    display_df = filtered_df[display_cols].copy()
    
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df.sort_values('date' if 'date' in display_df.columns else display_df.columns[0], ascending=False),
        use_container_width=True,
        height=400
    )
    
    if not filtered_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_amount = filtered_df['amount'].sum()
        avg_amount = filtered_df['amount'].mean()
        income_count = len(filtered_df[filtered_df['amount'] > 0])
        expense_count = len(filtered_df[filtered_df['amount'] < 0])
        
        metrics = [
            ("Total Amount", total_amount, "💰", "#4A90E2"),
            ("Average Amount", avg_amount, "📊", "#2E8B8B"),
            ("Income Transactions", income_count, "📈", "#2ECC71"),
            ("Expense Transactions", expense_count, "📉", "#FF6B6B")
        ]
        
        for i, (label, value, icon, color) in enumerate(metrics):
            with [col1, col2, col3, col4][i]:
                if "Transactions" in label:
                    value_text = f"{value}"
                else:
                    value_text = f"${value:,.2f}"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {color} 0%, {color}CC 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    color: white;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border: 1px solid rgba(255,255,255,0.1);
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                    <div style="font-size: 0.8rem; opacity: 0.9; margin-bottom: 0.3rem;">{label}</div>
                    <div style="font-size: 1.4rem; font-weight: bold;">{value_text}</div>
                </div>
                """, unsafe_allow_html=True)