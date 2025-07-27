import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.theme import THEME_COLORS, THEME_GRADIENTS


CHART_COLORS = [
    THEME_COLORS["lapis_lazuli"],
    THEME_COLORS["midnight_green"], 
    THEME_COLORS["pakistan_green"],
    THEME_COLORS["dark_green"],
    "#2E8B8B",  # Complementary teal
    "#4A90A4",  # Complementary blue-gray
    "#5B9279",  # Complementary green-gray
    "#6B7A8F"   # Complementary gray-blue
]


SCATTER_COLORS = [
    "#FF6B6B",  # Bright coral red
    "#4ECDC4",  # Bright teal
    "#45B7D1",  # Bright blue
    "#96CEB4",  # Mint green
    "#FFEAA7",  # Light yellow
    "#DDA0DD",  # Plum
    "#98D8C8",  # Aquamarine
    "#F7DC6F",  # Light gold
    "#BB8FCE",  # Light purple
    "#85C1E9",  # Light blue
    "#F8C471",  # Light orange
    "#82E0AA"   # Light green
]

def show_individual_file_analysis(df, uploaded_files):
    """Show detailed analysis for each individual file with modern styling"""
    
    if len(uploaded_files) <= 1 or 'source_file' not in df.columns:
        st.info("Individual file analysis requires multiple uploaded files.")
        return
    
    st.markdown("### 📂 Individual File Analysis")
    
    # File selector with modern styling
    files = sorted(df['source_file'].unique().tolist())
    
    # Create tabs for each file
    if len(files) <= 5:
        tabs = st.tabs([f"📄 {file[:15]}{'...' if len(file) > 15 else ''}" for file in files])
        
        for i, file in enumerate(files):
            with tabs[i]:
                show_single_file_analysis(df, file)
    else:
        # Use selectbox for many files
        selected_file = st.selectbox("Select file to analyze:", files, key="individual_file_selector")
        if selected_file:
            show_single_file_analysis(df, selected_file)

def show_single_file_analysis(df, filename):
    """Show comprehensive analysis for a single file"""
    
    # Filter data for this file
    file_df = df[df['source_file'] == filename].copy()
    
    if file_df.empty:
        st.warning(f"No data found for {filename}")
        return
    
    # File header with modern styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {THEME_COLORS['lapis_lazuli']} 0%, {THEME_COLORS['midnight_green']} 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(20px);
    ">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 700;">📄 {filename}</h2>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem;">{len(file_df)} transactions analyzed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # File-specific metrics
    show_file_specific_metrics(file_df)
    
    # File-specific visualizations
    show_file_spending_charts(file_df, filename)
    
    # File category breakdown
    show_file_category_analysis(file_df, filename)
    
    # File transaction timeline
    if 'date' in file_df.columns and not file_df['date'].isna().all():
        show_file_timeline(file_df, filename)

def show_file_specific_metrics(file_df):
    """Show key metrics for a specific file"""
    
    # Calculate file-specific metrics
    total_transactions = len(file_df)
    income_transactions = len(file_df[file_df['amount'] > 0])
    expense_transactions = len(file_df[file_df['amount'] < 0])
    
    total_income = file_df[file_df['amount'] > 0]['amount'].sum()
    total_expenses = abs(file_df[file_df['amount'] < 0]['amount'].sum())
    net_amount = total_income - total_expenses
    
    # Date range
    if 'date' in file_df.columns and not file_df['date'].isna().all():
        date_range_days = (file_df['date'].max() - file_df['date'].min()).days
        start_date = file_df['date'].min().strftime('%m/%d/%Y')
        end_date = file_df['date'].max().strftime('%m/%d/%Y')
    else:
        date_range_days = 0
        start_date = "N/A"
        end_date = "N/A"
    
    # Average transaction amounts
    avg_income = file_df[file_df['amount'] > 0]['amount'].mean() if income_transactions > 0 else 0
    avg_expense = abs(file_df[file_df['amount'] < 0]['amount'].mean()) if expense_transactions > 0 else 0
    
    # Create metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    primary_metrics = [
        ("Total Income", total_income, "💰", THEME_COLORS["lapis_lazuli"]),
        ("Total Expenses", total_expenses, "💸", "#FF6B6B"),
        ("Net Amount", net_amount, "📊", THEME_COLORS["lapis_lazuli"] if net_amount >= 0 else "#FF6B6B"),
        ("Transactions", total_transactions, "📋", THEME_COLORS["midnight_green"])
    ]
    
    for i, (label, value, icon, color) in enumerate(primary_metrics):
        with [col1, col2, col3, col4][i]:
            if label == "Transactions":
                value_text = f"{value:,}"
            else:
                value_text = f"${value:,.2f}"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color} 0%, {color}CC 100%);
                padding: 1.8rem;
                border-radius: 16px;
                color: white;
                text-align: center;
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(20px);
            ">
                <div style="font-size: 3rem; margin-bottom: 0.8rem;">{icon}</div>
                <div style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 0.8rem; font-weight: 500;">{label}</div>
                <div style="font-size: 2rem; font-weight: bold;">{value_text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Secondary metrics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    secondary_metrics = [
        ("Date Range", f"{start_date} - {end_date}", "📅"),
        ("Time Span", f"{date_range_days} days", "⏰"),
        ("Avg Income", f"${avg_income:.2f}" if avg_income > 0 else "$0.00", "📈"),
        ("Avg Expense", f"${avg_expense:.2f}" if avg_expense > 0 else "$0.00", "📉")
    ]
    
    for i, (label, value, icon) in enumerate(secondary_metrics):
        with [col1, col2, col3, col4][i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {THEME_COLORS['pakistan_green']} 0%, {THEME_COLORS['dark_green']} 100%);
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

def show_file_spending_charts(file_df, filename):
    """Show spending charts specific to one file"""
    
    st.markdown("#### 📊 Spending Analysis")
    
    spending_df = file_df[(file_df['amount'] < 0) & (file_df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info(f"No expense transactions found in {filename}")
        return
    
    # Create comprehensive spending visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Category Distribution',
            'Daily Spending Trend',
            'Top Merchants',
            'Transaction Amount Distribution'
        ),
        specs=[[{"type": "pie"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "histogram"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # 1. Category pie chart
    category_spending = spending_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False)
    
    fig.add_trace(
        go.Pie(
            labels=category_spending.index,
            values=category_spending.values,
            hole=0.4,
            marker=dict(
                colors=CHART_COLORS[:len(category_spending)],
                line=dict(color='white', width=2)
            ),
            textposition="outside",
            textinfo="percent+label",
            textfont=dict(size=10, color='white'),
            hovertemplate="<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # 2. Daily spending trend
    if 'date' in spending_df.columns:
        daily_spending = spending_df.groupby('date')['amount'].sum().abs().sort_index()
        
        # Raw daily spending
        fig.add_trace(
            go.Scatter(
                x=daily_spending.index,
                y=daily_spending.values,
                mode='lines+markers',
                marker=dict(color='#FF6B6B', size=5, opacity=0.7),
                line=dict(color='#FF6B6B', width=2),
                name='Daily Spending',
                showlegend=False,
                hovertemplate="Date: %{x}<br>Spending: $%{y:.2f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        # 7-day moving average if enough data
        if len(daily_spending) >= 7:
            ma_7 = daily_spending.rolling(window=7, center=True).mean()
            fig.add_trace(
                go.Scatter(
                    x=ma_7.index,
                    y=ma_7.values,
                    mode='lines',
                    line=dict(color=THEME_COLORS["lapis_lazuli"], width=3),
                    name='7-day Average',
                    showlegend=False,
                    hovertemplate="Date: %{x}<br>7-day Avg: $%{y:.2f}<extra></extra>"
                ),
                row=1, col=2
            )
    
    # 3. Top merchants
    merchant_spending = spending_df.groupby('description')['amount'].sum().abs()
    top_merchants = merchant_spending.sort_values(ascending=True).tail(10)
    
    fig.add_trace(
        go.Bar(
            x=top_merchants.values,
            y=[desc[:25] + '...' if len(desc) > 25 else desc for desc in top_merchants.index],
            orientation='h',
            marker=dict(
                color=THEME_COLORS["midnight_green"],
                line=dict(color='white', width=1)
            ),
            hovertemplate="<b>%{y}</b><br>Total: $%{x:,.2f}<extra></extra>"
        ),
        row=2, col=1
    )
    
    # 4. Amount distribution
    amounts = spending_df['amount'].abs()
    
    fig.add_trace(
        go.Histogram(
            x=amounts,
            nbinsx=20,
            marker=dict(
                color=THEME_COLORS["pakistan_green"],
                opacity=0.8,
                line=dict(color='white', width=1)
            ),
            hovertemplate="Amount Range: $%{x}<br>Count: %{y}<extra></extra>"
        ),
        row=2, col=2
    )
    
    # Update layout with theme
    fig.update_layout(
        height=800,
        showlegend=False,
        title=dict(
            text=f"Spending Analysis - {filename[:30]}{'...' if len(filename) > 30 else ''}",
            x=0.5,
            font=dict(size=20, family="Inter, sans-serif", color='white')
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white', family="Inter, sans-serif")
    )
    
    # Update subplot titles
    fig.update_annotations(font_size=14, font_color='white', font_family="Inter, sans-serif")
    
    # Update axes
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color='white'))
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color='white'))
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def show_file_category_analysis(file_df, filename):
    """Show detailed category analysis for a specific file"""
    
    st.markdown("#### 🎯 Category Breakdown")
    
    spending_df = file_df[(file_df['amount'] < 0) & (file_df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense categories to analyze.")
        return
    
    # Category statistics
    category_stats = spending_df.groupby('category').agg({
        'amount': ['sum', 'count', 'mean', 'std'],
        'date': ['min', 'max'] if 'date' in spending_df.columns else ['count', 'count']  # fallback
    }).round(2)
    
    if 'date' in spending_df.columns:
        category_stats.columns = ['Total_Spent', 'Count', 'Avg_Amount', 'Std_Amount', 'First_Date', 'Last_Date']
    else:
        category_stats.columns = ['Total_Spent', 'Count', 'Avg_Amount', 'Std_Amount', 'Placeholder1', 'Placeholder2']
    
    category_stats['Total_Spent'] = category_stats['Total_Spent'].abs()
    category_stats['Avg_Amount'] = category_stats['Avg_Amount'].abs()
    category_stats = category_stats.sort_values('Total_Spent', ascending=False)
    
    # Create category comparison chart
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Total Spending by Category', 'Average Transaction Size'),
        horizontal_spacing=0.15
    )
    
    # Total spending bar chart
    fig.add_trace(
        go.Bar(
            x=category_stats.index,
            y=category_stats['Total_Spent'],
            marker=dict(
                color=CHART_COLORS[:len(category_stats)],
                line=dict(color='white', width=1)
            ),
            name='Total Spent',
            hovertemplate="<b>%{x}</b><br>Total: $%{y:,.2f}<br>Transactions: %{customdata}<extra></extra>",
            customdata=category_stats['Count']
        ),
        row=1, col=1
    )
    
    # Average transaction size
    fig.add_trace(
        go.Bar(
            x=category_stats.index,
            y=category_stats['Avg_Amount'],
            marker=dict(
                color=SCATTER_COLORS[:len(category_stats)],
                line=dict(color='white', width=1)
            ),
            name='Average Amount',
            hovertemplate="<b>%{x}</b><br>Avg: $%{y:.2f}<br>Count: %{customdata}<extra></extra>",
            customdata=category_stats['Count']
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        showlegend=False,
        title=dict(
            text=f"Category Analysis - {filename[:30]}{'...' if len(filename) > 30 else ''}",
            x=0.5,
            font=dict(size=18, family="Inter, sans-serif", color='white')
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white', family="Inter, sans-serif")
    )
    
    # Update axes
    fig.update_xaxes(
        tickangle=45,
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color='white')
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color='white')
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Category summary table
    st.markdown("##### 📋 Detailed Category Summary")
    
    # Format for display
    display_stats = category_stats[['Total_Spent', 'Count', 'Avg_Amount']].copy()
    display_stats['Total_Spent'] = display_stats['Total_Spent'].apply(lambda x: f"${x:,.2f}")
    display_stats['Avg_Amount'] = display_stats['Avg_Amount'].apply(lambda x: f"${x:.2f}")
    display_stats.columns = ['Total Spent', 'Transactions', 'Avg per Transaction']
    
    st.dataframe(display_stats, use_container_width=True)

def show_file_timeline(file_df, filename):
    """Show transaction timeline for a specific file"""
    
    st.markdown("#### 📈 Transaction Timeline")
    
    if 'date' not in file_df.columns or file_df['date'].isna().all():
        st.info("No date information available for timeline analysis.")
        return
    
    # Prepare timeline data
    file_df_timeline = file_df.copy()
    file_df_timeline['month'] = file_df_timeline['date'].dt.to_period('M').astype(str)
    
    # Monthly aggregations
    monthly_income = file_df_timeline[file_df_timeline['amount'] > 0].groupby('month')['amount'].sum()
    monthly_expenses = file_df_timeline[file_df_timeline['amount'] < 0].groupby('month')['amount'].sum().abs()
    monthly_transactions = file_df_timeline.groupby('month').size()
    
    all_months = sorted(set(monthly_income.index.tolist() + monthly_expenses.index.tolist()))
    
    if not all_months:
        st.info("No monthly data available.")
        return
    
    # Prepare data arrays
    income_values = [monthly_income.get(m, 0) for m in all_months]
    expense_values = [monthly_expenses.get(m, 0) for m in all_months]
    transaction_counts = [monthly_transactions.get(m, 0) for m in all_months]
    net_values = [inc - exp for inc, exp in zip(income_values, expense_values)]
    
    # Create timeline visualization
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Monthly Income vs Expenses', 'Transaction Volume'),
        vertical_spacing=0.2,
        specs=[[{"secondary_y": True}], [{}]]
    )
    
    # Income and expense bars
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=income_values,
            name='Income',
            marker=dict(
                color=THEME_COLORS["lapis_lazuli"],
                line=dict(color='white', width=1)
            ),
            opacity=0.9,
            hovertemplate="<b>Income</b><br>%{x}: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=expense_values,
            name='Expenses',
            marker=dict(
                color='#FF6B6B',
                line=dict(color='white', width=1)
            ),
            opacity=0.9,
            hovertemplate="<b>Expenses</b><br>%{x}: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Net income line
    colors = [THEME_COLORS["lapis_lazuli"] if x >= 0 else '#FF6B6B' for x in net_values]
    fig.add_trace(
        go.Scatter(
            x=all_months,
            y=net_values,
            mode='lines+markers',
            name='Net Income',
            line=dict(color='#FFEAA7', width=3),
            marker=dict(color=colors, size=8, line=dict(color='white', width=2)),
            hovertemplate="<b>Net Income</b><br>%{x}: $%{y:,.2f}<extra></extra>"
        ),
        row=1, col=1
    )
    
    # Transaction volume
    fig.add_trace(
        go.Bar(
            x=all_months,
            y=transaction_counts,
            name='Transaction Count',
            marker=dict(
                color=THEME_COLORS["pakistan_green"],
                line=dict(color='white', width=1)
            ),
            opacity=0.8,
            hovertemplate="<b>Transactions</b><br>%{x}: %{y} transactions<extra></extra>"
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=700,
        title=dict(
            text=f"Financial Timeline - {filename[:30]}{'...' if len(filename) > 30 else ''}",
            x=0.5,
            font=dict(size=18, family="Inter, sans-serif", color='white')
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color='white')
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white', family="Inter, sans-serif")
    )
    
    # Update axes
    fig.update_xaxes(
        tickangle=45,
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color='white')
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.1)",
        tickfont=dict(color='white')
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

