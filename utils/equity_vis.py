import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils import helpers

def portfolio_allocation_chart(portfolio_df):
    """Create a pie chart of portfolio allocation"""
    if portfolio_df.empty or 'market_value' not in portfolio_df.columns:
        return None
    
    # Group by symbol for allocation
    allocation = portfolio_df.groupby('symbol')['market_value'].sum().reset_index()
    
    fig = px.pie(
        allocation,
        names='symbol',
        values='market_value',
        title='Portfolio Allocation by Holding',
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>"
    )
    
    return fig

def gain_loss_waterfall(portfolio_df):
    """Create waterfall chart of gains and losses"""
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
        text=[f"${x:,.2f}" for x in sorted_df['gain_loss']],
        y=sorted_df['gain_loss'],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    
    fig.update_layout(
        title="Gain/Loss by Holding",
        showlegend=False,
        yaxis_title="Amount ($)",
        xaxis_title="Holding"
    )
    
    # Add overall performance line
    total_gain = portfolio_df['gain_loss'].sum()
    fig.add_hline(
        y=total_gain,
        line_dash="dash",
        line_color="green" if total_gain >= 0 else "red",
        annotation_text=f"Total: ${total_gain:,.2f}",
        annotation_position="bottom right"
    )
    
    return fig

def historical_performance_chart(historical_values):
    """Chart historical portfolio value over time"""
    if historical_values.empty or 'total_value' not in historical_values.columns:
        return None
    
    # Ensure sorted by date
    historical = historical_values.sort_values('date')
    
    fig = px.line(
        historical,
        x='date',
        y='total_value',
        title='Historical Portfolio Value',
        labels={'total_value': 'Portfolio Value ($)'}
    )
    
    # Add 30-day moving average if enough data
    if len(historical) > 30:
        historical['30_day_ma'] = historical['total_value'].rolling(window=30).mean()
        fig.add_trace(go.Scatter(
            x=historical['date'],
            y=historical['30_day_ma'],
            mode='lines',
            name='30-Day MA',
            line=dict(dash='dash')
        ))
    
    fig.update_layout(
        hovermode='x unified',
        xaxis_title='Date',
        yaxis_title='Portfolio Value ($)',
        showlegend=False
    )
    
    return fig

def sector_allocation_chart(portfolio_df):
    """Create sunburst chart of sector allocation"""
    if portfolio_df.empty or 'sector' not in portfolio_df.columns:
        return None
    
    # Group by sector and holding
    sector_data = portfolio_df.groupby(['sector', 'symbol'])['market_value'].sum().reset_index()
    
    fig = px.sunburst(
        sector_data,
        path=['sector', 'symbol'],
        values='market_value',
        title='Sector Allocation'
    )
    
    fig.update_traces(
        textinfo='label+percent parent',
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percentParent}<extra></extra>"
    )
    
    return fig

def risk_analysis_chart(portfolio_df):
    """Visualize risk analysis through volatility"""
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
        }
    )
    
    # Add quadrants
    max_value = portfolio_df['market_value'].max() * 1.1
    max_pct = portfolio_df['gain_loss_pct'].abs().max() * 1.1
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.add_vline(x=portfolio_df['market_value'].median(), line_dash="dash", line_color="gray")
    
    fig.update_layout(
        shapes=[
            # High value, high gain
            dict(type="rect", x0=portfolio_df['market_value'].median(), y0=0, 
                x1=max_value, y1=max_pct, fillcolor="green", opacity=0.1, layer="below"),
            # High value, low gain
            dict(type="rect", x0=portfolio_df['market_value'].median(), y0=-max_pct, 
                x1=max_value, y1=0, fillcolor="red", opacity=0.1, layer="below"),
            # Low value, high gain
            dict(type="rect", x0=0, y0=0, 
                x1=portfolio_df['market_value'].median(), y1=max_pct, fillcolor="lightgreen", opacity=0.1, layer="below"),
            # Low value, low gain
            dict(type="rect", x0=0, y0=-max_pct, 
                x1=portfolio_df['market_value'].median(), y1=0, fillcolor="lightcoral", opacity=0.1, layer="below")
        ],
        annotations=[
            dict(x=max_value*0.75, y=max_pct*0.75, text="High Value<br>High Gain", showarrow=False),
            dict(x=max_value*0.75, y=-max_pct*0.75, text="High Value<br>Low Gain", showarrow=False),
            dict(x=max_value*0.25, y=max_pct*0.75, text="Low Value<br>High Gain", showarrow=False),
            dict(x=max_value*0.25, y=-max_pct*0.75, text="Low Value<br>Low Gain", showarrow=False)
        ]
    )
    
    return fig

def capital_allocation_line(portfolio_df, risk_free_rate):
    """Create Capital Allocation Line visualization"""
    if portfolio_df.empty or 'annualized_return' not in portfolio_df.columns or 'annualized_volatility' not in portfolio_df.columns:
        return None
    
    # Create efficient frontier
    portfolios = []
    for i in range(100):
        w = np.random.random(len(portfolio_df))
        w /= np.sum(w)
        
        port_return = np.sum(w * portfolio_df['annualized_return'])
        port_volatility = np.sqrt(np.dot(w.T, np.dot(portfolio_df.cov(), w)))
        
        portfolios.append({
            'return': port_return,
            'volatility': port_volatility,
            'sharpe': (port_return - risk_free_rate) / port_volatility
        })
    
    portfolios_df = pd.DataFrame(portfolios)
    
    # Create CAL
    max_sharpe = portfolios_df.loc[portfolios_df['sharpe'].idxmax()]
    cal_slope = (max_sharpe['return'] - risk_free_rate) / max_sharpe['volatility']
    
    fig = px.scatter(
        portfolios_df,
        x='volatility',
        y='return',
        color='sharpe',
        title='Capital Allocation Line (CAL)',
        labels={
            'volatility': 'Volatility (Risk)',
            'return': 'Expected Return'
        }
    )
    
    # Add CAL line
    cal_x = np.linspace(0, portfolios_df['volatility'].max() * 1.2, 50)
    cal_y = risk_free_rate + cal_slope * cal_x
    
    fig.add_trace(go.Scatter(
        x=cal_x,
        y=cal_y,
        mode='lines',
        name='Capital Allocation Line',
        line=dict(color='red', dash='dash')
    ))
    
    # Add risk-free rate point
    fig.add_trace(go.Scatter(
        x=[0],
        y=[risk_free_rate],
        mode='markers',
        name='Risk-Free Rate',
        marker=dict(color='green', size=10)
    ))
    
    # Add tangent portfolio
    fig.add_trace(go.Scatter(
        x=[max_sharpe['volatility']],
        y=[max_sharpe['return']],
        mode='markers',
        name='Optimal Portfolio',
        marker=dict(color='blue', size=10)
    ))
    
    fig.update_layout(
        xaxis_title='Volatility (Standard Deviation)',
        yaxis_title='Expected Return',
        coloraxis_colorbar=dict(title='Sharpe Ratio')
    )
    
    return fig

def render_equity_visualizations(tracker):
    """Render all equity visualizations in a dashboard"""
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