import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Importation de notre module local Quant A
import single_asset_module as sam

# Import Quant B (doit contenir render_quantb())
from QuantB_portfolio.dashboard_quantb import render_quantb


# ===========================
# Configuration de la page (UNE SEULE FOIS)
# ===========================
st.set_page_config(
    page_title="Quant Dashboard | Module A & B",
    layout="wide",
    page_icon="📈"
)

st.title("📈 Quantitative Analysis Dashboard")
st.markdown("Real-time financial data analysis, backtesting strategies, and forecasting.")

# ===========================
# Tabs
# ===========================
tabA, tabB = st.tabs(["Module A (Quant A)", "Module B (Quant B)"])


# ==========================================================
# ======================= TAB A : QUANT A ===================
# ==========================================================
with tabA:
    st.header("📈 Module A — Single Asset Analysis")

    # Sidebar : Paramètres (Quant A)
    st.sidebar.header("⚙️ Parameters (Quant A)")

    # Sélection de l'actif
    ticker = st.sidebar.text_input("Asset Symbol (Yahoo Finance)", value="AAPL")

    # Sélection des dates
    today = datetime.now()
    start_date = st.sidebar.date_input("Start Date", value=today - timedelta(days=365 * 2))
    end_date = st.sidebar.date_input("End Date", value=today)

    # Paramètres de capital
    initial_capital = st.sidebar.number_input("Initial Capital ($)", value=10000, step=1000)

    # Paramètres Momentum
    st.sidebar.subheader("Momentum Strategy Settings")
    lookback = st.sidebar.slider("Lookback Period (Days)", 10, 100, 20)
    threshold = st.sidebar.number_input("Signal Threshold", 0.01, 0.10, 0.02, step=0.01)

    # Chargement des données
    if start_date >= end_date:
        st.error("Error: Start date must be before End date.")
    else:
        with st.spinner(f'Fetching data for {ticker}...'):
            df = sam.fetch_financial_data(ticker, start_date, end_date)

        if df is None or df.empty:
            st.error(f"No data found for {ticker}. Please check the symbol.")
        else:
            # Indicateurs en temps réel
            latest_price = float(df["Close"].iloc[-1].values[0] if hasattr(df["Close"].iloc[-1], "values") else df["Close"].iloc[-1])
            prev_price   = float(df["Close"].iloc[-2].values[0] if hasattr(df["Close"].iloc[-2], "values") else df["Close"].iloc[-2])
            daily_return = ((latest_price - prev_price) / prev_price) * 100

            col1, col2, col3 = st.columns(3)
            col1.metric("Asset", ticker)
            col2.metric("Current Price", f"${latest_price:.2f}", f"{daily_return:.2f}%")
            col3.metric("Data Points", len(df))

            # Exécution des stratégies
            df_bh = sam.buy_and_hold_strategy(df, initial_capital)
            metrics_bh = sam.calculate_metrics(df_bh, initial_capital)

            df_mom = sam.momentum_strategy(df, initial_capital, lookback, threshold)
            metrics_mom = sam.calculate_metrics(df_mom, initial_capital)

            # Visualisation principale
            st.subheader("Strategy Performance Comparison")

            fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Prix de l'actif
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='Raw Asset Price',
                    line=dict(color='gray', dash='dot', width=1)
                ),
                secondary_y=True
            )

            # Valeur Portefeuille Buy & Hold
            fig.add_trace(
                go.Scatter(
                    x=df_bh.index,
                    y=df_bh['Holdings'],
                    mode='lines',
                    name='Buy & Hold ($)',
                    line=dict(color='#1f77b4')
                ),
                secondary_y=False
            )

            # Valeur Portefeuille Momentum
            fig.add_trace(
                go.Scatter(
                    x=df_mom.index,
                    y=df_mom['Holdings'],
                    mode='lines',
                    name='Momentum Strategy ($)',
                    line=dict(color='#ff7f0e')
                ),
                secondary_y=False
            )

            fig.update_layout(
                title=f"Portfolio Value vs Asset Price: {ticker}",
                xaxis_title="Date",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="Portfolio Value ($)", secondary_y=False)
            fig.update_yaxes(title_text="Asset Price ($)", secondary_y=True, showgrid=False)

            st.plotly_chart(fig, use_container_width=True)

            # Tableau des métriques
            st.subheader("📊 Performance Metrics")

            metrics_data = {
                "Metric": ["Total Return", "Annual Return", "Volatility", "Sharpe Ratio", "Max Drawdown", "Final Value"],
                "Buy & Hold": [
                    f"{metrics_bh['Total Return']:.2%}",
                    f"{metrics_bh['Annual Return']:.2%}",
                    f"{metrics_bh['Volatility']:.2%}",
                    f"{metrics_bh['Sharpe Ratio']:.2f}",
                    f"{metrics_bh['Max Drawdown']:.2%}",
                    f"${metrics_bh['Final Value']:.2f}"
                ],
                "Momentum": [
                    f"{metrics_mom['Total Return']:.2%}",
                    f"{metrics_mom['Annual Return']:.2%}",
                    f"{metrics_mom['Volatility']:.2%}",
                    f"{metrics_mom['Sharpe Ratio']:.2f}",
                    f"{metrics_mom['Max Drawdown']:.2%}",
                    f"${metrics_mom['Final Value']:.2f}"
                ]
            }
            st.table(pd.DataFrame(metrics_data).set_index("Metric"))

            # Analyse prédictive
            st.subheader("🤖 AI Price Forecast (30 Days with 95% CI)")

            if st.button("Run Predictive Model", key="run_pred_model_quanta"):
                future_dates, future_prices, lower, upper, r2_score_val = sam.run_predictive_model(df)

                fig_pred = go.Figure()

                recent_df = df.iloc[-90:]
                fig_pred.add_trace(go.Scatter(
                    x=recent_df.index,
                    y=recent_df['Close'],
                    mode='lines',
                    name='Historical Data'
                ))

                fig_pred.add_trace(go.Scatter(
                    x=future_dates,
                    y=future_prices,
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='red', dash='dash')
                ))

                fig_pred.add_trace(go.Scatter(
                    x=future_dates,
                    y=upper,
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    name='Upper Bound'
                ))

                fig_pred.add_trace(go.Scatter(
                    x=future_dates,
                    y=lower,
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    name='95% Confidence Interval'
                ))

                fig_pred.update_layout(
                    title=f"Linear Regression Forecast (Model Accuracy R²: {r2_score_val:.2f})",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    hovermode="x unified"
                )
                st.plotly_chart(fig_pred, use_container_width=True)


# ==========================================================
# ======================= TAB B : QUANT B ===================
# ==========================================================
with tabB:
    # IMPORTANT : pas de st.set_page_config() dans QuantB
    render_quantb()

