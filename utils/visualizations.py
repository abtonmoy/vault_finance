import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def show_file_summary(df):
    """Display enhanced file summary with visual cards"""
    st.markdown("### 📁 File Summary")
    
    summary = df.groupby('source_file').agg({
        'amount': ['count', 'sum'],
        'date': ['min', 'max']
    }).round(2)
    summary.columns = ['Transaction Count', 'Total Amount', 'Start Date', 'End Date']
    
    # Create visual cards for each file using theme colors
    files = summary.index.tolist()
    cols = st.columns(min(len(files), 3))
    
    for i, file in enumerate(files):
        with cols[i % 3]:
            count = summary.loc[file, 'Transaction Count']
            total = summary.loc[file, 'Total Amount']
            start_date = summary.loc[file, 'Start Date'].strftime('%m/%d/%y')
            end_date = summary.loc[file, 'End Date'].strftime('%m/%d/%y')
            
            st.markdown(f"""
            <div style="
                background: hsl(207, 90%, 54%);
                background: linear-gradient(135deg, hsl(207, 90%, 54%) 0%, hsl(262, 83%, 58%) 100%);
                padding: 1rem;
                border-radius: 0.5rem;
                color: hsl(211, 100%, 99%);
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px hsla(20, 14.3%, 4.1%, 0.1);
                animation: fade-in 0.3s ease-out;
            ">
                <h4 style="margin: 0; font-size: 0.9rem;">{file[:20]}...</h4>
                <p style="margin: 0.5rem 0; font-size: 1.2rem; font-weight: bold;">{count} transactions</p>
                <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">{start_date} - {end_date}</p>
                <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">Net: ${total:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

def show_enhanced_metrics(df):
    """Display enhanced key financial metrics with better styling"""
    st.markdown("### 💼 Financial Overview")
    
    # Calculate metrics
    income_mask = (df['category'] == 'Income')
    total_income = df[df['amount'] > 0]['amount'].sum()
    
    expense_mask = (df['category'] != 'Transfer') & (df['category'] != 'Income')
    total_expenses = abs(df[expense_mask & (df['amount'] < 0)]['amount'].sum())
    
    net_income = total_income - total_expenses
    
    expense_txns = df[expense_mask & (df['amount'] < 0)]
    avg_txn = expense_txns['amount'].abs().mean() if not expense_txns.empty else 0
    
    # Calculate additional metrics
    total_transactions = len(df)
    days_span = (df['date'].max() - df['date'].min()).days if 'date' in df.columns else 0
    daily_avg_spending = total_expenses / max(days_span, 1) if days_span > 0 else 0
    
    # Create metric cards with theme colors
    col1, col2, col3, col4 = st.columns(4)
    
    # Theme-based colors
    colors = [
        ("hsl(142, 76%, 36%)", "📈"),  # Green for income
        ("hsl(0, 84.2%, 60.2%)", "📉"),  # Red for expenses  
        ("hsl(142, 76%, 36%)" if net_income > 0 else "hsl(0, 84.2%, 60.2%)", "💰"),  # Conditional
        ("hsl(207, 90%, 54%)", "📊")  # Blue for daily avg
    ]
    
    metrics = [
        ("Total Income", total_income),
        ("Total Expenses", total_expenses),
        ("Net Income", net_income),
        ("Daily Avg Spend", daily_avg_spending)
    ]
    
    columns = [col1, col2, col3, col4]
    
    for i, ((label, value), (color, icon)) in enumerate(zip(metrics, colors)):
        with columns[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, {color}88 100%);
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.2s ease;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">{icon}</div>
                <div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 0.5rem; font-weight: 500;">{label}</div>
                <div style="font-size: 1.8rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">${value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Additional quick stats
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", f"{total_transactions:,}")
    with col2:
        st.metric("Time Period", f"{days_span} days")
    with col3:
        categories = df['category'].nunique()
        st.metric("Categories", f"{categories}")
    with col4:
        avg_monthly = total_expenses * 30 / max(days_span, 1) if days_span > 0 else 0
        st.metric("Monthly Avg Spend", f"${avg_monthly:,.2f}")

def show_enhanced_spending_overview(df):
    """Create a comprehensive spending overview dashboard"""
    st.markdown("### 📊 Spending Dashboard")
    
    # Filter for expenses only
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense transactions found.")
        return
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Category Distribution', 'Daily Spending Trend', 'Top Merchants', 'Amount Distribution'),
        specs=[[{"type": "pie"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "histogram"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Enhanced Pie Chart
    category_spending = spending_df.groupby('category')['amount'].sum().abs()
    category_spending = category_spending.sort_values(ascending=False)
    
    colors = px.colors.qualitative.Set3[:len(category_spending)]
    
    fig.add_trace(
        go.Pie(
            labels=category_spending.index,
            values=category_spending.values,
            hole=0.4,
            marker_colors=colors,
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 2. Daily Spending Trend
    if 'date' in spending_df.columns:
        daily_spending = spending_df.groupby('date')['amount'].sum().abs()
        daily_spending = daily_spending.rolling(window=7, center=True).mean()  # 7-day moving average
        
        fig.add_trace(
            go.Scatter(
                x=daily_spending.index,
                y=daily_spending.values,
                mode='lines+markers',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=4),
                name='7-day Average',
                hovertemplate="Date: %{x}<br>Spending: $%{y:.2f}<extra></extra>"
            ),
            row=1, col=2
        )
    
    # 3. Top Merchants
    top_merchants = spending_df.groupby('description')['amount'].sum().abs().sort_values(ascending=True).tail(10)
    
    fig.add_trace(
        go.Bar(
            x=top_merchants.values,
            y=[desc[:25] + '...' if len(desc) > 25 else desc for desc in top_merchants.index],
            orientation='h',
            marker_color='#3498db',
            hovertemplate="<b>%{y}</b><br>Total Spent: $%{x:,.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # 4. Amount Distribution
    amounts = spending_df['amount'].abs()
    
    fig.add_trace(
        go.Histogram(
            x=amounts,
            nbinsx=30,
            marker_color='#9b59b6',
            opacity=0.7,
            hovertemplate="Amount Range: $%{x}<br>Count: %{y}<extra></extra>"
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Comprehensive Spending Analysis",
        title_x=0.5,
        title_font_size=20
    )
    
    # Update subplot titles
    fig.update_annotations(font_size=14)
    
    st.plotly_chart(fig, use_container_width=True)

def show_advanced_monthly_analysis(df):
    """Advanced monthly analysis with income/expense/net tracking using theme colors"""
    st.markdown("### 📈 Monthly Financial Analysis")
    
    if 'date' not in df.columns or df['date'].isna().all():
        st.info("No date information available for monthly trends.")
        return
    
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M').astype(str)
    
    # Calculate monthly data
    income_mask = (df['amount'] > 0) & (df['category'] == 'Income')
    expense_mask = (df['amount'] < 0) & (df['category'] != 'Transfer')
    
    monthly_income = df_monthly[income_mask].groupby('month')['amount'].sum()
    monthly_expenses = df_monthly[expense_mask].groupby('month')['amount'].sum().abs()
    
    all_months = sorted(set(monthly_income.index.tolist() + monthly_expenses.index.tolist()))
    
    if not all_months:
        st.info("No data available for monthly trends.")
        return
    
    # Prepare data
    income_values = [monthly_income.get(m, 0) for m in all_months]
    expense_values = [monthly_expenses.get(m, 0) for m in all_months]
    net_values = [inc - exp for inc, exp in zip(income_values, expense_values)]
    
    # Create subplot with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Income vs Expenses', 'Net Income Trend'),
        vertical_spacing=0.15,
        specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
    )
    
    # Theme colors
    income_color = '#22c55e'  # Green from theme
    expense_color = '#ef4444'  # Red from theme
    
    # Income/Expense bars
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=income_values,
            name='Income',
            marker_color=income_color,
            opacity=0.8,
            hovertemplate="<b>Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=expense_values,
            name='Expenses',
            marker_color=expense_color,
            opacity=0.8,
            hovertemplate="<b>Expenses</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Net income bars with conditional colors
    colors = [income_color if x >= 0 else expense_color for x in net_values]
    
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=net_values,
            name='Net Income',
            marker_color=colors,
            opacity=0.7,
            hovertemplate="<b>Net Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Add trend line for net income
    if len(net_values) > 1:
        z = np.polyfit(range(len(net_values)), net_values, 1)
        trend_line = np.poly1d(z)(range(len(net_values)))
        
        fig.add_trace(
            go.Scatter(
                x=all_months,
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color='#eab308', width=3, dash='dash'),  # Yellow from theme
                hovertemplate="Trend: $%{y:,.2f}<extra></extra>"
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        height=700,
        title_text="Monthly Financial Trends",
        title_x=0.5,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='hsl(20, 14.3%, 4.1%)')
    )
    
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_yaxes(title_text="Amount ($)", row=1, col=1)
    fig.update_yaxes(title_text="Net Income ($)", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)

def show_category_insights(df):
    """Show detailed category analysis with insights"""
    st.markdown("### 🎯 Category Deep Dive")
    
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense transactions found.")
        return
    
    # Category analysis
    category_stats = spending_df.groupby('category').agg({
        'amount': ['sum', 'count', 'mean'],
        'date': ['min', 'max']
    }).round(2)
    
    category_stats.columns = ['Total_Spent', 'Transaction_Count', 'Avg_Transaction', 'First_Date', 'Last_Date']
    category_stats['Total_Spent'] = category_stats['Total_Spent'].abs()
    category_stats['Avg_Transaction'] = category_stats['Avg_Transaction'].abs()
    category_stats = category_stats.sort_values('Total_Spent', ascending=False)
    
    # Create enhanced category visualization
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Spending by Category', 'Transaction Frequency'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Total spending
    colors = px.colors.qualitative.Plotly
    fig.add_trace(
        go.Bar(
            x=category_stats.index,
            y=category_stats['Total_Spent'],
            marker_color=colors[:len(category_stats)],
            name='Total Spent',
            hovertemplate="<b>%{x}</b><br>Total: $%{y:,.2f}<br>Avg: $%{customdata:.2f}<extra></extra>",
            customdata=category_stats['Avg_Transaction']
        ),
        row=1, col=1
    )
    
    # Transaction count
    fig.add_trace(
        go.Bar(
            x=category_stats.index,
            y=category_stats['Transaction_Count'],
            marker_color=colors[:len(category_stats)],
            name='Transaction Count',
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Avg Amount: $%{customdata:.2f}<extra></extra>",
            customdata=category_stats['Avg_Transaction']
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        title_text="Category Analysis Overview"
    )
    
    fig.update_xaxes(tickangle=45)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Category insights table
    st.markdown("#### 📋 Category Summary")
    
    # Format the dataframe for display
    display_stats = category_stats.copy()
    display_stats['Total_Spent'] = display_stats['Total_Spent'].apply(lambda x: f"${x:,.2f}")
    display_stats['Avg_Transaction'] = display_stats['Avg_Transaction'].apply(lambda x: f"${x:.2f}")
    display_stats['First_Date'] = display_stats['First_Date'].dt.strftime('%Y-%m-%d')
    display_stats['Last_Date'] = display_stats['Last_Date'].dt.strftime('%Y-%m-%d')
    
    display_stats.columns = ['Total Spent', 'Transactions', 'Avg per Transaction', 'First Transaction', 'Last Transaction']
    
    st.dataframe(display_stats, use_container_width=True)

def show_spending_patterns(df):
    """Analyze spending patterns by day of week and time"""
    st.markdown("### 📅 Spending Patterns")
    
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty or 'date' not in spending_df.columns:
        st.info("No spending data with dates available.")
        return
    
    # Add day of week and hour analysis
    spending_df['day_of_week'] = spending_df['date'].dt.day_name()
    spending_df['month_name'] = spending_df['date'].dt.month_name()
    
    # Create pattern analysis
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Spending by Day of Week', 'Spending by Month', 'Weekly Pattern Heatmap', 'Category by Day'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "heatmap"}, {"type": "bar"}]]
    )
    
    # Day of week analysis
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_spending = spending_df.groupby('day_of_week')['amount'].sum().abs()
    daily_spending = daily_spending.reindex(day_order, fill_value=0)
    
    colors = ['#3498db' if day in ['Saturday', 'Sunday'] else '#2ecc71' for day in daily_spending.index]
    
    fig.add_trace(
        go.Bar(
            x=daily_spending.index,
            y=daily_spending.values,
            marker_color=colors,
            hovertemplate="<b>%{x}</b><br>Total Spent: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Monthly spending
    monthly_spending = spending_df.groupby('month_name')['amount'].sum().abs()
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_spending = monthly_spending.reindex([m for m in month_order if m in monthly_spending.index])
    
    fig.add_trace(
        go.Bar(
            x=monthly_spending.index,
            y=monthly_spending.values,
            marker_color='#e74c3c',
            hovertemplate="<b>%{x}</b><br>Total Spent: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=2
    )
    
    # Create heatmap data (category vs day of week)
    if len(spending_df['category'].unique()) > 1:
        heatmap_data = spending_df.groupby(['category', 'day_of_week'])['amount'].sum().abs().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(columns=day_order, fill_value=0)
        
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale='Reds',
                hovertemplate="<b>%{y}</b><br>%{x}<br>Amount: $%{z:,.2f}<extra></extra>"
            ),
            row=2, col=1
        )
    
    # Category distribution by weekend vs weekday
    spending_df['is_weekend'] = spending_df['day_of_week'].isin(['Saturday', 'Sunday'])
    weekend_categories = spending_df[spending_df['is_weekend']].groupby('category')['amount'].sum().abs()
    weekday_categories = spending_df[~spending_df['is_weekend']].groupby('category')['amount'].sum().abs()
    
    all_categories = set(weekend_categories.index) | set(weekday_categories.index)
    weekend_vals = [weekend_categories.get(cat, 0) for cat in all_categories]
    weekday_vals = [weekday_categories.get(cat, 0) for cat in all_categories]
    
    fig.add_trace(
        go.Bar(
            x=list(all_categories),
            y=weekday_vals,
            name='Weekday',
            marker_color='#3498db',
            opacity=0.7
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=list(all_categories),
            y=weekend_vals,
            name='Weekend',
            marker_color='#e74c3c',
            opacity=0.7
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        title_text="Spending Pattern Analysis",
        showlegend=True
    )
    
    fig.update_xaxes(tickangle=45, row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)

def show_enhanced_transaction_table(df, uploaded_files):
    """Enhanced transaction table with better filtering and styling"""
    st.markdown("### 📋 Transaction Explorer")
    
    # Enhanced filters in columns
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
    
    # Apply filters
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
    
    # Show filter results
    st.info(f"📊 Showing {len(filtered_df):,} of {len(df):,} transactions")
    
    # Prepare display dataframe
    display_cols = ['date', 'description', 'amount', 'category']
    if 'source_file' in filtered_df.columns and len(uploaded_files) > 1:
        display_cols.append('source_file')
    
    display_df = filtered_df[display_cols].copy()
    
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    # Add styling based on amount
    def style_amount(val):
        if pd.isna(val):
            return val
        if val > 0:
            return f"<span style='color: #27ae60; font-weight: bold;'>+${val:,.2f}</span>"
        else:
            return f"<span style='color: #e74c3c; font-weight: bold;'>-${abs(val):,.2f}</span>"
    
    # Create a copy for display with styled amounts
    styled_df = display_df.copy()
    styled_df['amount'] = styled_df['amount'].apply(lambda x: f"${x:,.2f}")
    
    # Display with custom styling
    st.dataframe(
        styled_df.sort_values('date' if 'date' in styled_df.columns else styled_df.columns[0], ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Quick stats for filtered data
    if not filtered_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_amount = filtered_df['amount'].sum()
        avg_amount = filtered_df['amount'].mean()
        income_count = len(filtered_df[filtered_df['amount'] > 0])
        expense_count = len(filtered_df[filtered_df['amount'] < 0])
        
        with col1:
            st.metric("Total Amount", f"${total_amount:,.2f}")
        with col2:
            st.metric("Average Amount", f"${avg_amount:,.2f}")
        with col3:
            st.metric("Income Transactions", f"{income_count}")
        with col4:
            st.metric("Expense Transactions", f"{expense_count}")

# Export function for the enhanced visualizations
def show_all_enhanced_visualizations(df, uploaded_files):
    """Main function to show all enhanced visualizations"""
    
    # Enhanced metrics
    show_enhanced_metrics(df)
    
    st.markdown("---")
    
    # File summary for multiple files
    if len(uploaded_files) > 1 and 'source_file' in df.columns:
        show_file_summary(df)
        st.markdown("---")
    
    # Comprehensive spending overview
    show_enhanced_spending_overview(df)
    
    st.markdown("---")
    
    # Advanced monthly analysis
    show_advanced_monthly_analysis(df)
    
    st.markdown("---")
    
    # Category insights
    show_category_insights(df)
    
    st.markdown("---")
    
    # Spending patterns
    show_spending_patterns(df)
    
    st.markdown("---")
    
    # Enhanced transaction table
    show_enhanced_transaction_table(df, uploaded_files)