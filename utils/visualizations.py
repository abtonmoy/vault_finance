import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def show_file_summary(df):
    """Display file summary table"""
    st.subheader("📁 File Summary")
    summary = df.groupby('source_file').agg({
        'amount': ['count', 'sum'],
        'date': ['min', 'max']
    }).round(2)
    summary.columns = ['Transaction Count', 'Total Amount', 'Start Date', 'End Date']
    st.dataframe(summary)

def show_metrics(df):
    """Display key financial metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    income_mask = (df['amount'] > 0) & (df['category'] == 'Income')
    total_income = df[income_mask]['amount'].sum() if income_mask.any() else 0
    
    expense_mask = (df['amount'] < 0) & (df['category'] != 'Transfer')
    total_expenses = abs(df[expense_mask]['amount'].sum()) if expense_mask.any() else 0
    
    net_income = total_income - total_expenses
    
    non_transfer_mask = df['category'] != 'Transfer'
    avg_txn = df[non_transfer_mask]['amount'].abs().mean() if non_transfer_mask.any() else 0
    
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Net Income", f"${net_income:,.2f}", 
                  delta="✅ Profit" if net_income > 0 else "❌ Loss")
    with col4:
        st.metric("Avg Transaction", f"${avg_txn:,.2f}")

def show_category_bar_chart(df):
    """Display horizontal bar chart of transaction counts by category"""
    category_counts = df['category'].value_counts()
    fig = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        title='Transactions by Category',
        labels={'x': 'Number of Transactions', 'y': 'Category'}
    )
    st.plotly_chart(fig, use_container_width=True)

def show_spending_pie_chart(df):
    """Display spending distribution pie chart"""
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense transactions found for spending distribution.")
        return
    
    category_spending = spending_df.groupby('category')['amount'].sum().abs()
    category_spending = category_spending[category_spending > 0]
    
    if category_spending.empty:
        st.info("No spending data available for distribution chart.")
        return
    
    category_spending = category_spending.sort_values(ascending=False)
    fig_pie = px.pie(
        values=category_spending.values,
        names=category_spending.index,
        title='Spending Distribution',
        hover_data=[category_spending.values],
        labels={'values': 'Amount ($)'}
    )
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
    )
    fig_pie.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.01)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

def show_monthly_trend(df):
    """Display monthly income vs expenses bar chart"""
    if 'date' not in df.columns or df['date'].isna().all():
        st.info("No date information available for monthly trends.")
        return
    
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M').astype(str)
    
    income_mask = (df['amount'] > 0) & (df['category'] == 'Income')
    expense_mask = (df['amount'] < 0) & (df['category'] != 'Transfer')
    
    monthly_income = df_monthly[income_mask].groupby('month')['amount'].sum()
    monthly_expenses = df_monthly[expense_mask].groupby('month')['amount'].sum().abs()
    
    all_months = sorted(set(monthly_income.index.tolist() + monthly_expenses.index.tolist()))
    
    if not all_months:
        st.info("No data available for monthly trends.")
        return
    
    fig_bar = go.Figure()
    income_values = [monthly_income.get(m, 0) for m in all_months]
    expense_values = [monthly_expenses.get(m, 0) for m in all_months]
    
    if any(v > 0 for v in income_values):
        fig_bar.add_trace(go.Bar(
            x=all_months, 
            y=income_values, 
            name='Income', 
            marker_color='green',
            hovertemplate='<b>Income</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
        ))
    
    if any(v > 0 for v in expense_values):
        fig_bar.add_trace(go.Bar(
            x=all_months, 
            y=expense_values, 
            name='Expenses', 
            marker_color='red',
            hovertemplate='<b>Expenses</b><br>Month: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
        ))
    
    fig_bar.update_layout(
        title='Monthly Income vs Expenses', 
        barmode='group',
        xaxis_title='Month',
        yaxis_title='Amount ($)',
        hovermode='x unified'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def show_top_merchants(df):
    """Display top 10 largest expenses by merchant"""
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    if spending_df.empty:
        st.info("No expense transactions found.")
        return
    
    top_merchants = spending_df.nlargest(10, 'amount', keep='all')[['description', 'amount', 'category']].copy()
    top_merchants['amount'] = top_merchants['amount'].abs()
    
    if top_merchants.empty:
        st.info("No expense data available for merchant analysis.")
        return
    
    top_merchants['short_description'] = top_merchants['description'].apply(
        lambda x: x[:30] + '...' if len(x) > 30 else x
    )
    
    fig_merchants = px.bar(
        top_merchants,
        x='amount',
        y='short_description',
        color='category',
        orientation='h',
        title='Top 10 Largest Expenses',
        labels={'amount': 'Amount ($)', 'short_description': 'Merchant'},
        hover_data={'description': True, 'amount': ':$,.2f'}
    )
    fig_merchants.update_layout(yaxis={'categoryorder': 'total ascending'}, height=400)
    st.plotly_chart(fig_merchants, use_container_width=True)

def show_transaction_table(df, uploaded_files):
    """Display transaction table with filters"""
    st.header("📋 Transaction Details")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ['All'] + sorted(df['category'].unique().tolist())
        selected_category = st.selectbox("Category Filter:", categories)
    
    with col2:
        if 'source_file' in df.columns:
            files = ['All'] + sorted(df['source_file'].unique().tolist())
            selected_file = st.selectbox("File Filter:", files)
        else:
            selected_file = 'All'
    
    with col3:
        if 'date' in df.columns and not df['date'].isna().all():
            min_date = df['date'].min().date()
            max_date = df['date'].max().date()
            date_range = st.date_input("Date Range", value=(min_date, max_date))
        else:
            date_range = None
    
    # Apply filters
    filtered_df = df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_file != 'All' and 'source_file' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['source_file'] == selected_file]
    if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        if 'date' in filtered_df.columns:
            filtered_df = filtered_df[
                (filtered_df['date'].dt.date >= start_date) & 
                (filtered_df['date'].dt.date <= end_date)
            ]
    
    # Display columns
    display_cols = ['date', 'description', 'amount', 'category']
    if 'source_file' in filtered_df.columns and len(uploaded_files) > 1:
        display_cols.append('source_file')
    
    # Format dataframe
    display_df = filtered_df[display_cols].copy()
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(
        display_df.sort_values('date' if 'date' in display_df.columns else display_df.columns[0], 
                              ascending=False), 
        use_container_width=True
    )

def show_summary_statistics(df):
    """Display top spending categories and transaction counts"""
    st.subheader("📈 Enhanced Summary Statistics")
    col1, col2 = st.columns(2)
    
    spending_df = df[(df['amount'] < 0) & (df['category'] != 'Transfer')].copy()
    
    with col1:
        st.write("**Top Spending Categories:**")
        if not spending_df.empty:
            top_categories = spending_df.groupby('category')['amount'].sum().abs().sort_values(ascending=False).head()
            for cat, amount in top_categories.items():
                st.write(f"• {cat}: ${amount:,.2f}")
    
    with col2:
        st.write("**Transaction Count by Category:**")
        category_counts = df['category'].value_counts()
        for cat, count in category_counts.head().items():
            st.write(f"• {cat}: {count} transactions")