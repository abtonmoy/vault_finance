import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils import helpers
from utils.theme import THEME_COLORS, THEME_GRADIENTS

# Define a consistent color palette from theme
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

# High contrast colors for scatter plots against dark backgrounds
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

def portfolio_allocation_chart(portfolio_df):
    """Create a modern pie chart of portfolio allocation"""
    if portfolio_df.empty or 'market_value' not in portfolio_df.columns:
        return None
    
    # Group by symbol for allocation
    allocation = portfolio_df.groupby('symbol')['market_value'].sum().reset_index()
    
    # Calculate percentages to determine which labels to show
    allocation['percentage'] = allocation['market_value'] / allocation['market_value'].sum() * 100
    
    fig = px.pie(
        allocation,
        names='symbol',
        values='market_value',
        title='Portfolio Allocation by Holding',
        hole=0.5,
        color_discrete_sequence=CHART_COLORS
    )
    
    # Create custom text - only show labels for holdings > 3%
    text_info = []
    for i, row in allocation.iterrows():
        if row['percentage'] > 3:
            text_info.append(f"{row['symbol']}<br>{row['percentage']:.1f}%")
        else:
            text_info.append("")  # Empty string for small slices
    
    fig.update_traces(
        textposition='outside',
        text=text_info,
        textinfo='text',
        textfont=dict(size=11, color='white'),
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>",
        marker=dict(line=dict(color='white', width=2))
    )
    
    fig.update_layout(
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white', size=12),
        title=dict(
            font=dict(size=18, color='white'),
            x=0.5
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(color='white')
        )
    )
    
    return fig

def gain_loss_waterfall(portfolio_df):
    """Create modern waterfall chart of gains and losses"""
    if portfolio_df.empty or 'gain_loss' not in portfolio_df.columns:
        return None
    
    # Sort by gain/loss
    sorted_df = portfolio_df.sort_values('gain_loss', ascending=False)
    
    fig = go.Figure(go.Waterfall(
        name="Performance",
        orientation="v",
        measure=["relative"] * len(sorted_df),
        x=sorted_df['symbol'],
        textposition="outside",
        text=[f"${x:,.0f}" for x in sorted_df['gain_loss']],
        textfont=dict(color='white', size=11),
        y=sorted_df['gain_loss'],
        connector=dict(line=dict(color="rgba(255,255,255,0.3)", width=1)),
        increasing=dict(marker=dict(color=THEME_COLORS["lapis_lazuli"])),
        decreasing=dict(marker=dict(color=THEME_COLORS["rojo"])),
        hovertemplate="<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(
            text="Gain/Loss by Holding",
            font=dict(size=18, color='white'),
            x=0.5
        ),
        showlegend=False,
        yaxis=dict(
            title=dict(text="Amount ($)", font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)",
            zerolinecolor="rgba(255,255,255,0.3)"
        ),
        xaxis=dict(
            title=dict(text="Holding", font=dict(color='white')),
            tickfont=dict(color='white'),
            tickangle=45
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white')
    )
    
    # Add overall performance line
    total_gain = portfolio_df['gain_loss'].sum()
    fig.add_hline(
        y=total_gain,
        line_dash="dash",
        line_color=THEME_COLORS["lapis_lazuli"] if total_gain >= 0 else THEME_COLORS["rojo"],
        line_width=2,
        annotation_text=f"Total: ${total_gain:,.2f}",
        annotation_position="top right",
        annotation_font=dict(color='white', size=12)
    )
    
    return fig

def historical_performance_chart(historical_values):
    """Chart historical portfolio value over time with modern styling"""
    if historical_values.empty or 'total_value' not in historical_values.columns:
        return None
    
    # Ensure sorted by date
    historical = historical_values.sort_values('date')
    
    fig = go.Figure()
    
    # Main line
    fig.add_trace(go.Scatter(
        x=historical['date'],
        y=historical['total_value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color=THEME_COLORS["lapis_lazuli"], width=3),
        fill='tonexty',
        fillcolor=f"rgba({int(THEME_COLORS['lapis_lazuli'][1:3], 16)}, {int(THEME_COLORS['lapis_lazuli'][3:5], 16)}, {int(THEME_COLORS['lapis_lazuli'][5:7], 16)}, 0.1)",
        hovertemplate="<b>Portfolio Value</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>"
    ))
    
    # Add 30-day moving average if enough data
    if len(historical) > 30:
        historical['30_day_ma'] = historical['total_value'].rolling(window=30).mean()
        fig.add_trace(go.Scatter(
            x=historical['date'],
            y=historical['30_day_ma'],
            mode='lines',
            name='30-Day Moving Average',
            line=dict(color=THEME_COLORS["midnight_green"], width=2, dash='dash'),
            hovertemplate="<b>30-Day MA</b><br>Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(
            text='Historical Portfolio Value',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        hovermode='x unified',
        xaxis=dict(
            title=dict(text='Date', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            title=dict(text='Portfolio Value ($)', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)"
        ),
        legend=dict(
            font=dict(color='white'),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white')
    )
    
    return fig

def sector_allocation_chart(portfolio_df):
    """Create modern sunburst chart of sector allocation"""
    if portfolio_df.empty or 'sector' not in portfolio_df.columns:
        return None
    
    # Group by sector and holding
    sector_data = portfolio_df.groupby(['sector', 'symbol'])['market_value'].sum().reset_index()
    
    fig = px.sunburst(
        sector_data,
        path=['sector', 'symbol'],
        values='market_value',
        title='Sector Allocation',
        color_discrete_sequence=CHART_COLORS
    )
    
    fig.update_traces(
        textinfo='label+percent parent',
        textfont=dict(color='white', size=11),
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percentParent}<extra></extra>",
        marker=dict(line=dict(color='white', width=1))
    )
    
    fig.update_layout(
        title=dict(
            font=dict(size=18, color='white'),
            x=0.5
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white')
    )
    
    return fig

def risk_analysis_chart(portfolio_df):
    """Visualize risk analysis through volatility with modern styling"""
    if portfolio_df.empty or 'gain_loss_pct' not in portfolio_df.columns:
        return None
    
    fig = px.scatter(
        portfolio_df,
        x='market_value',
        y='gain_loss_pct',
        size='quantity',
        color='symbol',
        hover_name='symbol',
        title='Risk Analysis: Value vs. Performance',
        labels={
            'market_value': 'Current Value ($)',
            'gain_loss_pct': 'Gain/Loss (%)'
        },
        color_discrete_sequence=SCATTER_COLORS
    )
    
    # Update marker properties for better visibility
    fig.update_traces(
        marker=dict(
            line=dict(width=2, color='white'),  # White border around markers
            opacity=0.8,
            sizemin=8  # Minimum marker size
        )
    )
    
    # Add quadrant lines with better visibility
    max_value = portfolio_df['market_value'].max() * 1.1
    max_pct = portfolio_df['gain_loss_pct'].abs().max() * 1.1
    median_value = portfolio_df['market_value'].median()
    
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="rgba(255,255,255,0.8)",  # More visible white line
        line_width=2
    )
    fig.add_vline(
        x=median_value, 
        line_dash="dash", 
        line_color="rgba(255,255,255,0.8)",  # More visible white line
        line_width=2
    )
    
    fig.update_layout(
        title=dict(
            font=dict(size=18, color='white'),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text='Current Value ($)', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)"
        ),
        yaxis=dict(
            title=dict(text='Gain/Loss (%)', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)"
        ),
        legend=dict(
            font=dict(color='white'),
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white')
    )
    
    return fig

def capital_allocation_line(portfolio_df, risk_free_rate):
    """Create modern Capital Allocation Line visualization"""
    if portfolio_df.empty or 'annualized_return' not in portfolio_df.columns or 'annualized_volatility' not in portfolio_df.columns:
        return None
    
    # Create efficient frontier (simplified)
    portfolios = []
    for i in range(100):
        w = np.random.random(len(portfolio_df))
        w /= np.sum(w)
        
        port_return = np.sum(w * portfolio_df['annualized_return'])
        port_volatility = np.sqrt(np.sum(w**2 * portfolio_df['annualized_volatility']**2))
        
        portfolios.append({
            'return': port_return,
            'volatility': port_volatility,
            'sharpe': (port_return - risk_free_rate) / port_volatility if port_volatility > 0 else 0
        })
    
    portfolios_df = pd.DataFrame(portfolios)
    
    # Create figure
    fig = go.Figure()
    
    # Scatter plot of portfolios
    fig.add_trace(go.Scatter(
        x=portfolios_df['volatility'],
        y=portfolios_df['return'],
        mode='markers',
        marker=dict(
            color=portfolios_df['sharpe'],
            colorscale=[[0, THEME_COLORS["rojo"]], [0.5, THEME_COLORS["midnight_green"]], [1, THEME_COLORS["lapis_lazuli"]]],
            size=8,
            opacity=0.7,
            colorbar=dict(title="Sharpe Ratio", titlefont=dict(color='white'), tickfont=dict(color='white'))
        ),
        name='Efficient Frontier',
        hovertemplate="<b>Portfolio</b><br>Volatility: %{x:.2%}<br>Return: %{y:.2%}<br>Sharpe: %{marker.color:.2f}<extra></extra>"
    ))
    
    # Add CAL line
    if not portfolios_df.empty:
        max_sharpe_idx = portfolios_df['sharpe'].idxmax()
        max_sharpe = portfolios_df.loc[max_sharpe_idx]
        cal_slope = (max_sharpe['return'] - risk_free_rate) / max_sharpe['volatility']
        
        cal_x = np.linspace(0, portfolios_df['volatility'].max() * 1.2, 50)
        cal_y = risk_free_rate + cal_slope * cal_x
        
        fig.add_trace(go.Scatter(
            x=cal_x,
            y=cal_y,
            mode='lines',
            name='Capital Allocation Line',
            line=dict(color=THEME_COLORS["rojo"], width=3, dash='dash'),
            hovertemplate="<b>CAL</b><br>Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>"
        ))
        
        # Add risk-free rate point
        fig.add_trace(go.Scatter(
            x=[0],
            y=[risk_free_rate],
            mode='markers',
            name='Risk-Free Rate',
            marker=dict(color='white', size=12, symbol='star'),
            hovertemplate="<b>Risk-Free Rate</b><br>Return: %{y:.2%}<extra></extra>"
        ))
        
        # Add optimal portfolio
        fig.add_trace(go.Scatter(
            x=[max_sharpe['volatility']],
            y=[max_sharpe['return']],
            mode='markers',
            name='Optimal Portfolio',
            marker=dict(color=THEME_COLORS["lapis_lazuli"], size=12, symbol='diamond'),
            hovertemplate="<b>Optimal Portfolio</b><br>Volatility: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(
            text='Capital Allocation Line (CAL)',
            font=dict(size=18, color='white'),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text='Volatility (Standard Deviation)', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)",
            tickformat='.1%'
        ),
        yaxis=dict(
            title=dict(text='Expected Return', font=dict(color='white')),
            tickfont=dict(color='white'),
            gridcolor="rgba(255,255,255,0.1)",
            tickformat='.1%'
        ),
        legend=dict(
            font=dict(color='white'),
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        paper_bgcolor=THEME_COLORS["dark_green"],
        plot_bgcolor=THEME_COLORS["dark_green"],
        font=dict(color='white')
    )
    
    return fig

def render_equity_visualizations(tracker):
    """Render all equity visualizations in a modern dashboard"""
    if tracker.portfolio.empty:
        return
    
    st.header("📊 Equity Portfolio Visualizations")
    
    col1, col2 = st.columns(2)
    with col1:
        allocation_fig = portfolio_allocation_chart(tracker.portfolio)
        if allocation_fig:
            st.plotly_chart(allocation_fig, use_container_width=True)
        
    with col2:
        waterfall_fig = gain_loss_waterfall(tracker.portfolio)
        if waterfall_fig:
            st.plotly_chart(waterfall_fig, use_container_width=True)
    
    # Historical performance
    hist_fig = historical_performance_chart(tracker.historical_values)
    if hist_fig:
        st.plotly_chart(hist_fig, use_container_width=True)
    
    # Capital Allocation Line
    cal_fig = capital_allocation_line(tracker.portfolio, tracker.risk_free_rate)
    if cal_fig:
        st.plotly_chart(cal_fig, use_container_width=True)
    
    # Sector allocation
    sector_fig = sector_allocation_chart(tracker.portfolio)
    if sector_fig:
        st.plotly_chart(sector_fig, use_container_width=True)
    
    # Risk analysis
    risk_fig = risk_analysis_chart(tracker.portfolio)
    if risk_fig:
        st.plotly_chart(risk_fig, use_container_width=True)