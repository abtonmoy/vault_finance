import streamlit as st
import pandas as pd
from datetime import datetime
from core.robinhood_parser import parse_investment_documents
# from core.parser import parse_pdf_statement
from utils.equity_vis import render_equity_visualizations
from utils import helpers

def show_investment_dashboard():
    """Main UI for investment tracking and analysis"""
    st.header("📈 Investment Portfolio Analysis")
    
    # Document type selection
    doc_type = st.selectbox("Select Document Type", ["CSV", "PDF"])
    
    # Brokerage selection
    brokerage = st.selectbox(
        "Select Brokerage",
        ["Robinhood", "Fidelity", "Charles Schwab", "Vanguard", "Generic"]
    )
    
    # File uploader
    uploaded_files = st.file_uploader(
        f"Upload {brokerage} {doc_type} Reports",
        type=[doc_type.lower()],
        accept_multiple_files=True,
        key="investment_uploader"
    )
    
    if uploaded_files:
        # Parse investment documents
        tracker = parse_investment_documents(uploaded_files, doc_type, brokerage)
        # tracker = parse_pdf_statement(uploaded_files,doc_type)
        if tracker and not tracker.portfolio.empty:
            # Portfolio summary metrics
            st.subheader("📊 Portfolio Summary")
            summary = tracker.calculate_portfolio_summary()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Value", f"${summary['total_value']:,.2f}")
            col2.metric("Total Gain/Loss", 
                       f"${summary['total_gain_loss']:,.2f}", 
                       f"{summary['gain_loss_pct']:.2f}%")
            col3.metric("Positions", summary['num_positions'])
            col4.metric("Brokerages", summary['num_brokerages'])
            
            # Advanced metrics section
            st.subheader("📈 Advanced Portfolio Metrics")
            st.markdown("""
            <style>
            .metric-box {
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background-color: #f9f9f9;
            }
            .metric-title {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 5px;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
            }
            .metric-sub {
                font-size: 14px;
                color: #666;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Risk-free rate input
            tracker.risk_free_rate = st.slider(
                "Risk-Free Rate (%)", 
                min_value=0.0, 
                max_value=10.0, 
                value=2.0, 
                step=0.1,
                format="%.1f%%"
            ) / 100
            
            advanced_metrics = tracker.calculate_advanced_metrics()
            
            if advanced_metrics:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Sharpe Ratio</div>
                        <div class="metric-value">{advanced_metrics['sharpe_ratio']:.2f}</div>
                        <div class="metric-sub">Risk-adjusted return</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Annualized Return</div>
                        <div class="metric-value">{advanced_metrics['annualized_return']*100:.2f}%</div>
                        <div class="metric-sub">CAGR</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col3:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Annualized Volatility</div>
                        <div class="metric-value">{advanced_metrics['annualized_volatility']*100:.2f}%</div>
                        <div class="metric-sub">Portfolio risk</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col4:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Max Drawdown</div>
                        <div class="metric-value">{advanced_metrics['max_drawdown']*100:.2f}%</div>
                        <div class="metric-sub">Worst decline</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Sortino Ratio</div>
                        <div class="metric-value">{advanced_metrics['sortino_ratio']:.2f}</div>
                        <div class="metric-sub">Downside risk-adjusted</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown(f"""
                    <div class="metric-box">
                        <div class="metric-title">Calmar Ratio</div>
                        <div class="metric-value">{advanced_metrics['calmar_ratio']:.2f}</div>
                        <div class="metric-sub">Return vs drawdown</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Asset class breakdown
            st.subheader("📦 Asset Class Breakdown")
            asset_class_df = tracker.get_asset_class_breakdown()
            if asset_class_df is not None:
                st.dataframe(asset_class_df, use_container_width=True)
            
            # Top and bottom performers
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🚀 Top Performers")
                st.dataframe(tracker.get_top_performers(), use_container_width=True)
            
            with col2:
                st.subheader("📉 Bottom Performers")
                st.dataframe(tracker.get_bottom_performers(), use_container_width=True)
            
            # Portfolio details
            st.subheader("🔍 Full Portfolio Details")
            st.dataframe(tracker.portfolio, use_container_width=True)
            
            # Export button
            st.download_button(
                label="💾 Export Portfolio Data",
                data=tracker.portfolio.to_csv(index=False),
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Show visualizations
            render_equity_visualizations(tracker)
        else:
            st.warning("No valid investment data found in the uploaded files.")