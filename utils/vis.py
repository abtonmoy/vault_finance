import streamlit as st
import plotly.graph_objects as go
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def show_sankey_flow_diagram(df):
    """Create a visually-rich Sankey diagram with proper label visibility"""
    st.markdown("### Money Flow Analysis")
    
    # Prepare data for Sankey diagram
    income_df = df[(df['amount'] > 0) & (df['category'] == 'Income')].copy()
    expense_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if income_df.empty and expense_df.empty:
        st.info("No income or expense data available for flow analysis.")
        return
    
    # Create nodes and links
    nodes = []
    links = []
    node_colors = []
    
    # Income sources (from description for income transactions)
    income_sources = {}
    if not income_df.empty:
        income_by_source = income_df.groupby('description')['amount'].sum().sort_values(ascending=False)
        for i, (source, amount) in enumerate(income_by_source.items()):
            source_name = source[:30] + "..." if len(source) > 30 else source
            income_sources[source] = len(nodes)
            
            # Generate unique color for each income source
            color = get_gradient_color(i, len(income_by_source), 'income')
            nodes.append(source_name)
            node_colors.append(color)
    
    # Add "Total Income" node
    total_income_idx = len(nodes)
    nodes.append("Total Income")
    node_colors.append(get_gradient_color(0, 1, 'total'))
    
    # Expense categories
    expense_categories = {}
    if not expense_df.empty:
        expense_by_category = expense_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
        for i, (category, amount) in enumerate(expense_by_category.items()):
            expense_categories[category] = len(nodes)
            
            # Generate unique color for each expense category
            color = get_gradient_color(i, len(expense_by_category), 'expense')
            nodes.append(category)
            node_colors.append(color)
    
    # Create links from income sources to total income
    if not income_df.empty:
        for source, amount in income_by_source.items():
            links.append({
                'source': income_sources[source],
                'target': total_income_idx,
                'value': amount,
                'color': calculate_midpoint_color(
                    node_colors[income_sources[source]], 
                    node_colors[total_income_idx]
                )
            })
    
    # Create links from total income to expense categories
    total_income_amount = income_df['amount'].sum() if not income_df.empty else 0
    total_expense_amount = expense_df['amount'].abs().sum() if not expense_df.empty else 0
    
    if not expense_df.empty and total_income_amount > 0:
        for category, amount in expense_by_category.items():
            proportion = amount / total_expense_amount if total_expense_amount > 0 else 0
            flow_amount = min(amount, total_income_amount * proportion)
            
            links.append({
                'source': total_income_idx,
                'target': expense_categories[category],
                'value': flow_amount,
                'color': calculate_midpoint_color(
                    node_colors[total_income_idx],
                    node_colors[expense_categories[category]]
                )
            })
    
    # Add savings/net income if positive
    net_income = total_income_amount - total_expense_amount
    if net_income > 0:
        savings_idx = len(nodes)
        color = get_gradient_color(0, 1, 'savings')
        nodes.append("Net Savings")
        node_colors.append(color)
        
        links.append({
            'source': total_income_idx,
            'target': savings_idx,
            'value': net_income,
            'color': calculate_midpoint_color(
                node_colors[total_income_idx],
                color
            )
        })
    
    if not links:
        st.info("Insufficient data to create money flow diagram.")
        return
    
    # Create Sankey diagram - CRITICAL: No textfont property for nodes
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="rgba(0,0,0,0.05)", width=0.5),
            label=nodes,
            color=node_colors,
            hovertemplate="<b>%{label}</b><br>Value: $%{value:,.0f}<extra></extra>",
            # IMPORTANT: Sankey nodes don't support textfont property!
            # This was causing the error in previous implementations
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links],
            color=[link['color'] for link in links],
            hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>" +
                         "Amount: $%{value:,.0f}<extra></extra>",
            line=dict(width=0)
        )
    )])
    
    # Update layout with optimized styling
    fig.update_layout(
        title=dict(
            text="Money Flow: From Income Sources to Expense Categories",
            x=0.0,
            font=dict(size=18, family="Arial, sans-serif")
        ),
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=60, b=30),
        hoverlabel=dict(
            font=dict(
                color=get_theme_text_color(),
                size=16,
                family="Arial, sans-serif"
            ),
            bgcolor=get_theme_background(opacity=1.0),
            bordercolor=get_theme_border(),
            align="left"
        ),
        font=dict(
            family="Arial, sans-serif",
            color=get_theme_text_color(),
            size=13
        ),
        transition_duration=300
    )
    
    # Display the Sankey diagram
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Add summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Income Sources", 
            len(income_sources),
            delta=f"${total_income_amount:,.0f}",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Expense Categories", 
            len(expense_categories),
            delta=f"-${total_expense_amount:,.0f}",
            delta_color="inverse"
        )
    
    with col3:
        flow_efficiency = (total_expense_amount / total_income_amount * 100) if total_income_amount > 0 else 0
        st.metric(
            "Flow Efficiency", 
            f"{flow_efficiency:.0f}%",
            help="Percentage of income allocated to expenses"
        )

# Helper functions
def get_gradient_color(index, total, category, opacity=1.0):
    """Generate professional gradient colors based on category and index"""
    if category == 'income':
        # Darker green palette for better contrast in dark mode
        cmap = LinearSegmentedColormap.from_list('income', ['#22c55e', '#78e5d5'])
    elif category == 'expense':
        # Dark red/pink palette
        cmap = LinearSegmentedColormap.from_list('expense', ['#ef4444', '#fecdd6'])
    elif category == 'total':
        # Primary income color
        return "rgba(34, 197, 94, 1.0)"
    elif category == 'savings':
        # Calm savings color
        return "rgba(34, 211, 238, 1.0)"
    
    if category in ['income', 'expense']:
        # Reverse index for descending importance (largest = darkest)
        color_val = (total - 1 - index) / max(total - 1, 1)
        rgb = cmap(color_val)[:3]
        return f"rgba({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)}, {opacity})"
    
    return "#ffffff"

def calculate_midpoint_color(color1, color2):
    """Calculate a single color that visually represents a midpoint between two colors"""
    # Extract RGB values from rgba string
    def parse_rgba(rgba_str):
        rgba_str = rgba_str.replace('rgba(', '').replace(')', '')
        parts = [p.strip() for p in rgba_str.split(',')]
        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
        return (r, g, b)
    
    # Parse colors
    rgb1 = parse_rgba(color1)
    rgb2 = parse_rgba(color2)
    
    # Calculate midpoint
    mid_rgb = (
        (rgb1[0] + rgb2[0]) // 2,
        (rgb1[1] + rgb2[1]) // 2,
        (rgb1[2] + rgb2[2]) // 2
    )
    
    # Return as rgba string with adjusted opacity for better visibility
    return f"rgba({mid_rgb[0]}, {mid_rgb[1]}, {mid_rgb[2]}, 0.7)"

def get_theme_background(opacity=0.95):
    """Return appropriate hover background color with configurable opacity"""
    try:
        bg_color = st.get_option("theme.backgroundColor")
        # Handle None case
        if bg_color is None:
            return f"rgba(255, 255, 255, {opacity})"
        
        # Check for dark theme indicators
        if "dark" in bg_color.lower() or "000" in bg_color or "111" in bg_color or "222" in bg_color:
            return f"rgba(30, 30, 30, {opacity})"
        return f"rgba(255, 255, 255, {opacity})"
    except Exception as e:
        # Fallback to light mode if any error occurs
        return f"rgba(255, 255, 255, {opacity})"

def get_theme_border():
    """Return appropriate hover border color based on theme"""
    try:
        bg_color = st.get_option("theme.backgroundColor")
        # Handle None case
        if bg_color is None:
            return "rgba(0,0,0,0.2)"  # Default to light mode
        
        # Check for dark theme indicators
        if "dark" in bg_color.lower() or "000" in bg_color or "111" in bg_color or "222" in bg_color:
            return "rgba(255, 255, 255, 0.2)"  # Light border for dark theme
        return "rgba(0,0,0,0.2)"  # Dark border for light theme
    except Exception as e:
        # Fallback to light mode if any error occurs
        return "rgba(0,0,0,0.2)"

def get_theme_text_color():
    """Detect Streamlit theme and return appropriate text color"""
    try:
        bg_color = st.get_option("theme.backgroundColor")
        # Handle None case
        if bg_color is None or "dark" in bg_color.lower() or "000" in bg_color or "111" in bg_color or "222" in bg_color:
            return "#FFFFFF"  # Pure white for dark theme (better contrast)
        return "#000000"  # Pure black for light theme
    except Exception as e:
        # Fallback to white if any error occurs
        return "#FFFFFF"
    

def show_enhanced_transaction_table(df, uploaded_files):
    """Enhanced transaction table with better filtering and styling"""
    st.markdown("### 📋 Transaction Explorer")