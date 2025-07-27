import streamlit as st
import plotly.graph_objects as go
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from utils.theme import THEME_COLORS, THEME_GRADIENTS, get_gradient_color, get_theme_background, get_theme_border, get_theme_text_color

def hex_to_rgba(hex_color, alpha=0.4):
    """Convert hex color to RGBA with specified alpha transparency."""
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"

def create_gradient_color(color1, color2, position=0.5):
    """Create a gradient between two colors at a given position."""
    # Convert hex to RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Interpolate
    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * position)
    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * position)
    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * position)
    
    return f"#{r:02x}{g:02x}{b:02x}"

def show_sankey_flow_diagram(df):
    """Create a premium Sankey diagram matching the investment plot aesthetic."""
    st.markdown("### 💰 Money Flow Analysis")
    
    # Prepare data for Sankey diagram
    income_df = df[(df['amount'] > 0) & (df['category'] == 'Income')].copy()
    expense_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if income_df.empty and expense_df.empty:
        st.info("No income or expense data available for flow analysis.")
        return
    
    # Premium color palette - darker and more sophisticated
    income_colors = [
        "#1E5F74",  # Darker deep blue
        "#7A1E4B",  # Darker deep magenta
        "#C26D00",  # Darker warm orange
        "#9A2F14",  # Darker deep red
        "#456B58",  # Darker sage green  
        "#4E5A6B",  # Darker blue gray
        "#354A32",  # Darker forest green
        "#5A0890",  # Darker purple
        "#C41E62",  # Darker pink
        "#3399CC"   # Darker light blue
    ]
    
    expense_colors = [
        "#CC4545",  # Darker coral red
        "#3BA89D",  # Darker teal
        "#3690A8",  # Darker sky blue
        "#739E87",  # Darker mint
        "#CC9B3D",  # Darker golden yellow
        "#CC79C4",  # Darker pink
        "#4380CC",  # Darker blue
        "#4A1F9E",  # Darker purple
        "#00A8A9",  # Darker cyan
        "#CC7A34",  # Darker orange
        "#0D8566",  # Darker green
        "#BB4A1C"   # Darker red orange
    ]
    
    # Create nodes and links
    nodes = []
    links = []
    node_colors = []
    link_colors = []
    
    # Income sources with enhanced styling
    income_sources = {}
    total_income_amount = income_df['amount'].sum() if not income_df.empty else 0
    if not income_df.empty:
        income_by_source = income_df.groupby('description')['amount'].sum().sort_values(ascending=False)
        for i, (source, amount) in enumerate(income_by_source.items()):
            source_name = source[:20] + "..." if len(source) > 20 else source
            percentage = (amount / total_income_amount * 100) if total_income_amount > 0 else 0
            income_sources[source] = len(nodes)
            nodes.append(f"{source_name}<br>${amount:,.0f} ({percentage:.1f}%)")
            node_colors.append(income_colors[i % len(income_colors)])
    
    # Central "Available Funds" node with prominent styling
    available_funds_idx = len(nodes)
    nodes.append(f"Available Funds<br>${total_income_amount:,.0f}")
    node_colors.append("#2C3E50")  # Darker blue-gray for central node
    
    # Expense categories with refined colors
    expense_categories = {}
    if not expense_df.empty:
        expense_by_category = expense_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
        for i, (category, amount) in enumerate(expense_by_category.items()):
            percentage = (amount / total_income_amount * 100) if total_income_amount > 0 else 0
            expense_categories[category] = len(nodes)
            nodes.append(f"{category}<br>${amount:,.0f} ({percentage:.1f}%)")
            node_colors.append(expense_colors[i % len(expense_colors)])
    
    # Net Savings with premium green
    total_expense_amount = expense_df['amount'].abs().sum() if not expense_df.empty else 0
    net_income = total_income_amount - total_expense_amount
    if net_income > 0:
        savings_idx = len(nodes)
        percentage = (net_income / total_income_amount * 100) if total_income_amount > 0 else 0
        nodes.append(f"Net Savings<br>${net_income:,.0f} ({percentage:.1f}%)")
        node_colors.append("#1E8449")  # Darker premium green
    
    # Enhanced links with gradient effects
    if not income_df.empty:
        for i, (source, amount) in enumerate(income_by_source.items()):
            source_idx = income_sources[source]
            links.append({
                'source': source_idx,
                'target': available_funds_idx,
                'value': amount
            })
            # Create gradient from source color to central node
            source_color = node_colors[source_idx]
            link_colors.append(hex_to_rgba(source_color, 0.4))
    
    # Links from Available Funds to expenses with enhanced gradients
    if not expense_df.empty and total_income_amount > 0:
        for i, (category, amount) in enumerate(expense_by_category.items()):
            links.append({
                'source': available_funds_idx,
                'target': expense_categories[category],
                'value': amount
            })
            # Gradient from central node to target
            target_color = node_colors[expense_categories[category]]
            link_colors.append(hex_to_rgba(target_color, 0.3))
    
    # Savings link with special treatment
    if net_income > 0:
        links.append({
            'source': available_funds_idx,
            'target': savings_idx,
            'value': net_income
        })
        link_colors.append(hex_to_rgba("#1E8449", 0.5))
    
    if not links:
        st.info("Insufficient data to create money flow diagram.")
        return
    
    # Create enhanced Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=35,  # Increased padding for better spacing
            thickness=25,  # Slightly thinner nodes for elegance
            line=dict(color="rgba(255,255,255,0.4)", width=2),  # Subtle border
            label=nodes,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>Total: $%{value:,.0f}<extra></extra>",
            x=[0.01 if i < len(income_sources) else 0.5 if i == available_funds_idx else 0.99 for i in range(len(nodes))],
            y=[i/(len(income_sources)-1) if i < len(income_sources) else 0.5 if i == available_funds_idx else (i-len(income_sources)-1)/(len(nodes)-len(income_sources)-2) if i > available_funds_idx else 0.5 for i in range(len(nodes))]
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links],
            color=link_colors,
            hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>" +
                         "Amount: $%{value:,.0f}<extra></extra>",
            line=dict(width=1, color="rgba(255,255,255,0.15)")  # Subtle link borders
        )
    )])
    
    # Premium layout styling to match investment plot
    fig.update_layout(
        title=dict(
            text="Financial Flow: Income → Available Funds → Expenses",
            x=0.2,
            font=dict(
                size=24, 
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif", 
                color="white"
            ),
            pad=dict(t=20)
        ),
        height=700,  # Increased height for better proportions
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        margin=dict(l=50, r=50, t=100, b=50),  # Better margins
        hoverlabel=dict(
            font=dict(
                color="white",
                size=13,
                family="Inter, -apple-system, BlinkMacSystemFont, sans-serif"
            ),
            bgcolor="rgba(0, 0, 0, 0.85)",
            bordercolor="rgba(255,255,255,0.3)",
            align="left",
            namelength=-1
        ),
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            color="white",
            size=11
        ),
        # Add subtle animations
        transition=dict(
            duration=800,
            easing="cubic-in-out"
        )
    )
    
    # Display with  config
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'displaylogo': False,
        'doubleClick': 'reset',
        'showTips': False
    })
    
    # Premium summary cards with enhanced gradients
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #2E86AB 0%, #4A9EDF 50%, #6BB6FF 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            text-align: center;
            box-shadow: 0 12px 40px rgba(46, 134, 171, 0.4);
            border: 2px solid rgba(255,255,255,0.15);
            backdrop-filter: blur(15px);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; 
                        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
            <div style="position: relative; z-index: 2;">
                <div style="font-size: 3rem; margin-bottom: 0.8rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">💰</div>
                <div style="font-size: 1rem; opacity: 0.95; margin-bottom: 0.8rem; font-weight: 600; letter-spacing: 0.5px;">Income Sources</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.3rem;">{len(income_sources)}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; font-weight: 500;">${total_income_amount:,.0f} total</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #FF6B6B 0%, #FF8787 50%, #FFA8A8 100%);
            padding: 2rem;
            border-radius: 16px;
            color: white;
            text-align: center;
            box-shadow: 0 12px 40px rgba(255, 107, 107, 0.4);
            border: 2px solid rgba(255,255,255,0.15);
            backdrop-filter: blur(15px);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; 
                        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
            <div style="position: relative; z-index: 2;">
                <div style="font-size: 3rem; margin-bottom: 0.8rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">📊</div>
                <div style="font-size: 1rem; opacity: 0.95; margin-bottom: 0.8rem; font-weight: 600; letter-spacing: 0.5px;">Expense Categories</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.3rem;">{len(expense_categories)}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; font-weight: 500;">${total_expense_amount:,.0f} total</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        flow_efficiency = (total_expense_amount / total_income_amount * 100) if total_income_amount > 0 else 0
        efficiency_color = "#27AE60" if flow_efficiency < 80 else "#F39C12" if flow_efficiency < 95 else "#E74C3C"
        efficiency_gradient = f"linear-gradient(135deg, {efficiency_color} 0%, {efficiency_color}E6 50%, {efficiency_color}CC 100%)"
        
        st.markdown(f"""
        <div style="
            background: {efficiency_gradient};
            padding: 2rem;
            border-radius: 16px;
            color: white;
            text-align: center;
            box-shadow: 0 12px 40px rgba(39, 174, 96, 0.4);
            border: 2px solid rgba(255,255,255,0.15);
            backdrop-filter: blur(15px);
            position: relative;
            overflow: hidden;
        ">
            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; 
                        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);"></div>
            <div style="position: relative; z-index: 2;">
                <div style="font-size: 3rem; margin-bottom: 0.8rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">⚡</div>
                <div style="font-size: 1rem; opacity: 0.95; margin-bottom: 0.8rem; font-weight: 600; letter-spacing: 0.5px;">Flow Efficiency</div>
                <div style="font-size: 2.2rem; font-weight: 800; margin-bottom: 0.3rem;">{flow_efficiency:.0f}%</div>
                <div style="font-size: 0.9rem; opacity: 0.9; font-weight: 500;">of income allocated</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
        background: linear-gradient(135deg, {THEME_COLORS["midnight_green"]} 0%, {THEME_COLORS["lapis_lazuli"]} 100%);
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
            ("Total Amount", total_amount, "💰", THEME_COLORS["lapis_lazuli"]),
            ("Average Amount", avg_amount, "📊", THEME_COLORS["midnight_green"]),
            ("Income Transactions", income_count, "📈", THEME_COLORS["pakistan_green"]),
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