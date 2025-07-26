import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.theme import THEME_COLORS, THEME_GRADIENTS

# Modern color palette
MODERN_COLORS = {
    'primary': '#4A90E2',      # Modern blue
    'secondary': '#2E8B8B',    # Teal
    'success': '#2ECC71',      # Green
    'danger': '#FF6B6B',       # Coral red
    'warning': '#F39C12',      # Orange
    'info': '#5BA3F5',         # Light blue
    'dark': '#f8f9fa',         # Light gray background
    'light': '#ffffff',        # White
    'text': '#2c3e50',         # Dark text color
    'grid': '#e9ecef'          # Light grid color
}

def show_file_summary(df):
    """Display enhanced file summary with modern visual cards"""
    st.markdown("### 📁 File Summary")
    
    summary = df.groupby('source_file').agg({
        'amount': ['count', 'sum'],
        'date': ['min', 'max']
    }).round(2)
    summary.columns = ['Transaction Count', 'Total Amount', 'Start Date', 'End Date']
    
    # Create modern visual cards for each file
    files = summary.index.tolist()
    cols = st.columns(min(len(files), 3))
    
    colors = [MODERN_COLORS['primary'], MODERN_COLORS['secondary'], MODERN_COLORS['success'], 
              MODERN_COLORS['info'], MODERN_COLORS['warning'], MODERN_COLORS['danger']]
    
    for i, file in enumerate(files):
        with cols[i % 3]:
            count = summary.loc[file, 'Transaction Count']
            total = summary.loc[file, 'Total Amount']
            start_date = summary.loc[file, 'Start Date'].strftime('%m/%d/%y')
            end_date = summary.loc[file, 'End Date'].strftime('%m/%d/%y')
            
            color = colors[i % len(colors)]
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, {color}CC 100%);
                padding: 1.5rem;
                border-radius: 12px;
                color: white;
                margin-bottom: 1rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.2s ease;
            ">
                <h4 style="margin: 0; font-size: 1rem; font-weight: 600;">{file[:30]}{'...' if len(file) > 30 else ''}</h4>
                <p style="margin: 1rem 0 0.5rem 0; font-size: 1.5rem; font-weight: bold;">{count} transactions</p>
                <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">{start_date} - {end_date}</p>
                <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Net: ${total:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)

def show_enhanced_metrics(df):
    """Display enhanced key financial metrics with modern styling"""
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
    
    # Create modern metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("Total Income", total_income, "💰", MODERN_COLORS['success']),
        ("Total Expenses", total_expenses, "💸", MODERN_COLORS['danger']),
        ("Net Income", net_income, "📊", MODERN_COLORS['success'] if net_income > 0 else MODERN_COLORS['danger']),
        ("Daily Avg Spend", daily_avg_spending, "📅", MODERN_COLORS['info'])
    ]
    
    columns = [col1, col2, col3, col4]
    
    for i, ((label, value), (_, _, icon, color)) in enumerate(zip([(m[0], m[1]) for m in metrics], metrics)):
        with columns[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, {color}BB 100%);
                padding: 1.8rem;
                border-radius: 16px;
                color: white;
                text-align: center;
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            ">
                <div style="font-size: 3rem; margin-bottom: 0.8rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));">{icon}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.8rem; font-weight: 500; letter-spacing: 0.5px;">{label}</div>
                <div style="font-size: 2rem; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">${value:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Additional quick stats with modern cards
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    additional_metrics = [
        ("Total Transactions", f"{total_transactions:,}", "📋"),
        ("Time Period", f"{days_span} days", "⏰"),
        ("Categories", f"{df['category'].nunique()}", "📂"),
        ("Monthly Avg Spend", f"${(total_expenses * 30 / max(days_span, 1)):,.2f}" if days_span > 0 else "$0.00", "📆")
    ]
    
    for i, (label, value, icon) in enumerate(additional_metrics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {MODERN_COLORS['secondary']} 0%, {MODERN_COLORS['primary']} 100%);
                padding: 1.2rem;
                border-radius: 12px;
                color: white;
                text-align: center;
                box-shadow: 0 6px 20px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.1);
            ">
                <div style="font-size: 1.8rem; margin-bottom: 0.5rem;">{icon}</div>
                <div style="font-size: 0.8rem; opacity: 0.9; margin-bottom: 0.3rem;">{label}</div>
                <div style="font-size: 1.3rem; font-weight: bold;">{value}</div>
            </div>
            """, unsafe_allow_html=True)

def show_enhanced_spending_overview(df):
    """Create a comprehensive spending overview dashboard with modern styling"""
    st.markdown("### 📊 Spending Dashboard")
    
    # Filter for expenses only
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense transactions found.")
        return
    
    # Create modern subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Category Distribution', 'Daily Spending Trend', 'Top Merchants', 'Amount Distribution'),
        specs=[[{"type": "pie"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "histogram"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # Modern color palette
    colors = [MODERN_COLORS['primary'], MODERN_COLORS['danger'], MODERN_COLORS['success'], 
              MODERN_COLORS['warning'], MODERN_COLORS['info'], MODERN_COLORS['secondary']]
    
    # 1. Enhanced Pie Chart with modern styling
    category_spending = spending_df.groupby('category')['amount'].sum().abs()
    category_spending = category_spending.sort_values(ascending=False)
    
    fig.add_trace(
        go.Pie(
            labels=category_spending.index,
            values=category_spending.values,
            hole=0.5,
            marker=dict(
                colors=colors[:len(category_spending)],
                line=dict(color='white', width=2)
            ),
            textposition="outside",
            textinfo="percent+label",
            textfont=dict(size=11, color='white'),
            hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 2. Modern Daily Spending Trend
    
    if 'date' in spending_df.columns:
        daily_spending = spending_df.groupby('date')['amount'].sum().abs().sort_index()
        daily_spending_ma = daily_spending.rolling(window=7, center=True).mean()
        
        fig.add_trace(
            go.Scatter(
                x=daily_spending.index,
                y=daily_spending.values,
                mode='lines+markers',  # Changed from 'markers' to connect points with lines
                marker=dict(color=MODERN_COLORS['danger'], size=6, opacity=0.6),
                line=dict(color=MODERN_COLORS['danger'], width=1),  # Thin line to connect points
                name='Daily',
                showlegend=False,
                hovertemplate="Date: %{x}<br>Spending: $%{y:.2f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=daily_spending_ma.index,
                y=daily_spending_ma.values,
                mode='lines',
                line=dict(color=MODERN_COLORS['primary'], width=3),
                name='7-day Average',
                showlegend=False,
                hovertemplate="Date: %{x}<br>7-day Avg: $%{y:.2f}<extra></extra>"
            ),
            row=1, col=2
        )
    
    # 3. Modern Top Merchants Bar Chart
    top_merchants = spending_df.groupby('description')['amount'].sum().abs().sort_values(ascending=True).tail(10)
    
    fig.add_trace(
        go.Bar(
            x=top_merchants.values,
            y=[desc[:30] + '...' if len(desc) > 30 else desc for desc in top_merchants.index],
            orientation='h',
            marker=dict(
                color=MODERN_COLORS['secondary'],
                line=dict(color='white', width=1)
            ),
            hovertemplate="<b>%{y}</b><br>Total Spent: $%{x:,.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # 4. Modern Amount Distribution
    amounts = spending_df['amount'].abs()
    
    fig.add_trace(
        go.Histogram(
            x=amounts,
            nbinsx=25,
            marker=dict(
                color=MODERN_COLORS['info'],
                opacity=0.8,
                line=dict(color='white', width=1)
            ),
            hovertemplate="Amount Range: $%{x}<br>Count: %{y}<extra></extra>"
        ),
        row=2, col=2
    )
    
    # Modern layout
    fig.update_layout(
        height=850,
        showlegend=False,
        title=dict(
            text="Spending Analysis",
            x=0.5,
            font=dict(size=24, family="Inter, sans-serif", color=MODERN_COLORS['text'])
        ),
        paper_bgcolor=MODERN_COLORS['light'],
        plot_bgcolor=MODERN_COLORS['light'],
        font=dict(color=MODERN_COLORS['text'], family="Inter, sans-serif")
    )
    
    # Update subplot styling
    fig.update_annotations(font_size=16, font_color=MODERN_COLORS['text'], font_family="Inter, sans-serif")
    
    # Update axes for modern look
    fig.update_xaxes(gridcolor=MODERN_COLORS['grid'], tickfont=dict(color=MODERN_COLORS['text']))
    fig.update_yaxes(gridcolor=MODERN_COLORS['grid'], tickfont=dict(color=MODERN_COLORS['text']))
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def show_advanced_monthly_analysis(df):
    """Advanced monthly analysis with modern styling"""
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
    
    # Create modern subplot
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Income vs Expenses', 'Net Income Trend'),
        vertical_spacing=0.2,
        specs=[[{}], [{"secondary_y": True}]]
    )
    
    # Income/Expense bars with modern styling
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=income_values,
            name='Income',
            marker=dict(
                color=MODERN_COLORS['success'],
                line=dict(color='white', width=1)
            ),
            opacity=0.9,
            hovertemplate="<b>Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=expense_values,
            name='Expenses',
            marker=dict(
                color=MODERN_COLORS['danger'],
                line=dict(color='white', width=1)
            ),
            opacity=0.9,
            hovertemplate="<b>Expenses</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Net income bars with conditional colors
    colors = [MODERN_COLORS['success'] if x >= 0 else MODERN_COLORS['danger'] for x in net_values]
    
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=net_values,
            name='Net Income',
            marker=dict(
                color=colors,
                line=dict(color='white', width=1)
            ),
            opacity=0.8,
            hovertemplate="<b>Net Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Add modern trend line
    if len(net_values) > 1:
        z = np.polyfit(range(len(net_values)), net_values, 1)
        trend_line = np.poly1d(z)(range(len(net_values)))
        
        fig.add_trace(
            go.Scatter(
                x=all_months,
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color=MODERN_COLORS['warning'], width=4, dash='dash'),
                hovertemplate="Trend: $%{y:,.2f}<extra></extra>"
            ),
            row=2, col=1
        )
    
    # Modern layout
    fig.update_layout(
        height=750,
        title=dict(
            text="Monthly Financial Trends",
            x=0.5,
            font=dict(size=22, family="Inter, sans-serif", color=MODERN_COLORS['text'])
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=MODERN_COLORS['text'])
        ),
        paper_bgcolor=MODERN_COLORS['light'],
        plot_bgcolor=MODERN_COLORS['light'],
        font=dict(color=MODERN_COLORS['text'], family="Inter, sans-serif")
    )
    
    # Update axes - FIXED: using title_font instead of titlefont
    fig.update_xaxes(
        title_text="Month", 
        row=2, col=1, 
        tickangle=45,
        gridcolor=MODERN_COLORS['grid'],
        tickfont=dict(color=MODERN_COLORS['text']),
        title_font=dict(color=MODERN_COLORS['text'])
    )
    fig.update_yaxes(
        title_text="Amount ($)", 
        row=1, col=1,
        gridcolor=MODERN_COLORS['grid'],
        tickfont=dict(color=MODERN_COLORS['text']),
        title_font=dict(color=MODERN_COLORS['text'])
    )
    fig.update_yaxes(
        title_text="Net Income ($)", 
        row=2, col=1,
        gridcolor=MODERN_COLORS['grid'],
        tickfont=dict(color=MODERN_COLORS['text']),
        title_font=dict(color=MODERN_COLORS['text'])
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def show_category_insights(df):
    """Show detailed category analysis with modern insights"""
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
    
    # Create modern category visualization
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total Spending by Category', 'Transaction Frequency'),
        specs=[[{"type": "bar"}, {"type": "bar"}]],
        horizontal_spacing=0.15
    )
    
    # Modern color palette for categories
    colors = [MODERN_COLORS['primary'], MODERN_COLORS['danger'], MODERN_COLORS['success'], 
              MODERN_COLORS['warning'], MODERN_COLORS['info'], MODERN_COLORS['secondary']]
    
    # Total spending with gradient effect
    fig.add_trace(
        go.Bar(
            x=category_stats.index,
            y=category_stats['Total_Spent'],
            marker=dict(
                color=colors[:len(category_stats)],
                line=dict(color='white', width=1)
            ),
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
            marker=dict(
                color=colors[:len(category_stats)],
                line=dict(color='white', width=1)
            ),
            name='Transaction Count',
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Avg Amount: $%{customdata:.2f}<extra></extra>",
            customdata=category_stats['Avg_Transaction']
        ),
        row=1, col=2
    )
    
    # Modern layout
    fig.update_layout(
        height=550,
        showlegend=False,
        title=dict(
            text="Category Analysis Overview",
            x=0.5,
            font=dict(size=20, family="Inter, sans-serif", color=MODERN_COLORS['text'])
        ),
        paper_bgcolor=MODERN_COLORS['light'],
        plot_bgcolor=MODERN_COLORS['light'],
        font=dict(color=MODERN_COLORS['text'], family="Inter, sans-serif")
    )
    
    # Update axes with modern styling - FIXED: using title_font instead of titlefont
    fig.update_xaxes(
        tickangle=45,
        gridcolor=MODERN_COLORS['grid'],
        tickfont=dict(color=MODERN_COLORS['text']),
        title_font=dict(color=MODERN_COLORS['text'])
    )
    fig.update_yaxes(
        gridcolor=MODERN_COLORS['grid'],
        tickfont=dict(color=MODERN_COLORS['text']),
        title_font=dict(color=MODERN_COLORS['text'])
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Modern category insights table
    st.markdown("#### 📋 Category Summary")
    
    # Format the dataframe for display with modern styling
    display_stats = category_stats.copy()
    display_stats['Total_Spent'] = display_stats['Total_Spent'].apply(lambda x: f"${x:,.2f}")
    display_stats['Avg_Transaction'] = display_stats['Avg_Transaction'].apply(lambda x: f"${x:.2f}")
    display_stats['First_Date'] = display_stats['First_Date'].dt.strftime('%Y-%m-%d')
    display_stats['Last_Date'] = display_stats['Last_Date'].dt.strftime('%Y-%m-%d')
    
    display_stats.columns = ['Total Spent', 'Transactions', 'Avg per Transaction', 'First Transaction', 'Last Transaction']
    
    st.dataframe(display_stats, use_container_width=True)

def show_spending_patterns(df):
    """Analyze spending patterns by day of week and time with modern styling"""
    st.markdown("### 📅 Spending Patterns")
    
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty or 'date' not in spending_df.columns:
        st.info("No spending data with dates available.")
        return
    
    # Add day of week and month analysis
    spending_df['day_of_week'] = spending_df['date'].dt.day_name()
    spending_df['month_name'] = spending_df['date'].dt.month_name()
    
    # Create modern pattern analysis
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Spending by Day of Week', 'Spending by Month', 'Category vs Day Heatmap', 'Weekend vs Weekday'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "heatmap"}, {"type": "bar"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # Day of week analysis with modern colors
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_spending = spending_df.groupby('day_of_week')['amount'].sum().abs()
    daily_spending = daily_spending.reindex(day_order, fill_value=0)
    
    # Different colors for weekdays vs weekends
    colors = [MODERN_COLORS['info'] if day in ['Saturday', 'Sunday'] else MODERN_COLORS['primary'] for day in daily_spending.index]
    
    fig.add_trace(
        go.Bar(
            x=daily_spending.index,
            y=daily_spending.values,
            marker=dict(
                color=colors,
                line=dict(color='white', width=1)
            ),
            hovertemplate="<b>%{x}</b><br>Total Spent: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Monthly spending with gradient
    monthly_spending = spending_df.groupby('month_name')['amount'].sum().abs()
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_spending = monthly_spending.reindex([m for m in month_order if m in monthly_spending.index])
    
    fig.add_trace(
        go.Bar(
            x=monthly_spending.index,
            y=monthly_spending.values,
            marker=dict(
                color=MODERN_COLORS['danger'],
                line=dict(color='white', width=1)
            ),
            hovertemplate="<b>%{x}</b><br>Total Spent: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=2
    )
    
    # Create modern heatmap data (category vs day of week)
    if len(spending_df['category'].unique()) > 1:
        heatmap_data = spending_df.groupby(['category', 'day_of_week'])['amount'].sum().abs().unstack(fill_value=0)
        heatmap_data = heatmap_data.reindex(columns=day_order, fill_value=0)
        
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns,
                y=heatmap_data.index,
                colorscale=[[0, MODERN_COLORS['dark']], [0.5, MODERN_COLORS['secondary']], [1, MODERN_COLORS['danger']]],
                hovertemplate="<b>%{y}</b><br>%{x}<br>Amount: $%{z:,.2f}<extra></extra>",
                colorbar=dict(
                    title="Amount ($)",
                    titlefont=dict(color='white'),
                    tickfont=dict(color='white')
                )
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
            marker=dict(
                color=MODERN_COLORS['primary'],
                line=dict(color='white', width=1)
            ),
            opacity=0.8
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Bar(
            x=list(all_categories),
            y=weekend_vals,
            name='Weekend',
            marker=dict(
                color=MODERN_COLORS['info'],
                line=dict(color='white', width=1)
            ),
            opacity=0.8
        ),
        row=2, col=2
    )
    
    # Modern layout
    fig.update_layout(
        height=850,
        title=dict(
            text="Spending Pattern Analysis",
            x=0.5,
            font=dict(size=22, family="Inter, sans-serif", color='white')
        ),
        showlegend=True,
        legend=dict(
            font=dict(color='white'),
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        paper_bgcolor=MODERN_COLORS['dark'],
        plot_bgcolor=MODERN_COLORS['dark'],
        font=dict(color='white', family="Inter, sans-serif")
    )
    
    # Update axes with modern styling - FIXED: using title_font instead of titlefont
    fig.update_xaxes(
        tickangle=45, 
        row=2, col=2,
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color='white'),
        title_font=dict(color='white')
    )
    
    # Update all axes
    for row in [1, 2]:
        for col in [1, 2]:
            fig.update_xaxes(
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(color='white'),
                title_font=dict(color='white'),
                row=row, col=col
            )
            fig.update_yaxes(
                gridcolor="rgba(255,255,255,0.1)",
                tickfont=dict(color='white'),
                title_font=dict(color='white'),
                row=row, col=col
            )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def show_enhanced_transaction_table(df, uploaded_files):
    """Enhanced transaction table with better filtering and modern styling"""
    st.markdown("### 📋 Transaction Explorer")
    
    # Enhanced filters in columns with modern styling
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
    
    # Show filter results with modern styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {MODERN_COLORS['primary']} 0%, {MODERN_COLORS['secondary']} 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
        font-weight: 600;
        box-shadow: 0 8px 32px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    ">
        📊 Showing {len(filtered_df):,} of {len(df):,} transactions
    </div>
    """, unsafe_allow_html=True)
    
    # Prepare display dataframe
    display_cols = ['date', 'description', 'amount', 'category']
    if 'source_file' in filtered_df.columns and len(uploaded_files) > 1:
        display_cols.append('source_file')
    
    display_df = filtered_df[display_cols].copy()
    
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    
    # Display with modern table styling
    st.dataframe(
        display_df.sort_values('date' if 'date' in display_df.columns else display_df.columns[0], ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Modern quick stats cards
    if not filtered_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        total_amount = filtered_df['amount'].sum()
        avg_amount = filtered_df['amount'].mean()
        income_count = len(filtered_df[filtered_df['amount'] > 0])
        expense_count = len(filtered_df[filtered_df['amount'] < 0])
        
        metrics = [
            ("Total Amount", total_amount, "💰", MODERN_COLORS['primary']),
            ("Average Amount", avg_amount, "📊", MODERN_COLORS['secondary']),
            ("Income Transactions", income_count, "📈", MODERN_COLORS['success']),
            ("Expense Transactions", expense_count, "📉", MODERN_COLORS['danger'])
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
                    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
                    border: 1px solid rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                    <div style="font-size: 0.8rem; opacity: 0.9; margin-bottom: 0.3rem; font-weight: 500;">{label}</div>
                    <div style="font-size: 1.4rem; font-weight: bold;">{value_text}</div>
                </div>
                """, unsafe_allow_html=True)

# Export function for the enhanced visualizations
def show_all_enhanced_visualizations(df, uploaded_files):
    """Main function to show all enhanced visualizations with modern styling"""
    
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