import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import du backend Quant B
import portfolio_module as pm


# ===========================
# Configuration Streamlit
# ===========================

st.set_page_config(
    page_title="Quant B | Multi-Asset Portfolio",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Quant B – Multi-Asset Portfolio Analysis")


# ===========================
# Sidebar : paramètres
# ===========================

st.sidebar.header("Portfolio Settings")

default_tickers = "AAPL, MSFT, GOOGL"
tickers_input = st.sidebar.text_input(
    "Tickers (séparés par des virgules)",
    value=default_tickers
)

# Dates par défaut : 1 an en arrière
today = datetime.today().date()
one_year_ago = today - timedelta(days=365)

start_date = st.sidebar.date_input("Start Date", one_year_ago)
end_date = st.sidebar.date_input("End Date", today)

if start_date >= end_date:
    st.sidebar.error("Start Date must be before End Date.")

weight_mode = st.sidebar.radio(
    "Weights mode",
    ["Equal Weight", "Custom Weights"]
)

log_return = st.sidebar.checkbox("Use log returns", value=False)

run_button = st.sidebar.button("Run Portfolio Analysis")


# ===========================
# Main
# ===========================

if not run_button:
    st.info("Configure le portefeuille dans la sidebar puis clique sur **Run Portfolio Analysis**.")
else:
    # Nettoyage de la liste de tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if len(tickers) == 0:
        st.error("Veuillez entrer au moins un ticker.")
    elif start_date >= end_date:
        st.error("Start Date must be before End Date.")
    else:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        with st.spinner("Fetching data from Yahoo Finance..."):
            prices = pm.fetch_multi_asset_data(tickers, start_str, end_str)

        if prices is None or prices.empty:
            st.error("Aucune donnée trouvée pour ces tickers / cette période.")
        else:
            st.subheader("1️⃣ Raw Prices")
            st.dataframe(prices.tail())

            # Rendements
            returns = pm.compute_returns(prices, log_return=log_return)

            # -------------------------
            # Gestion des poids
            # -------------------------
            if weight_mode == "Equal Weight":
                weights = pd.Series(1 / len(returns.columns), index=returns.columns)
            else:
                st.sidebar.subheader("Custom Weights")
                raw_weights = []
                for col in returns.columns:
                    w = st.sidebar.slider(
                        f"Weight {col}",
                        min_value=0.0,
                        max_value=1.0,
                        value=1.0 / len(returns.columns),
                        step=0.01
                    )
                    raw_weights.append(w)
                raw_weights = pd.Series(raw_weights, index=returns.columns)

                if raw_weights.sum() == 0:
                    st.sidebar.error("La somme des poids ne peut pas être 0. Repassage en Equal Weight.")
                    weights = pd.Series(1 / len(returns.columns), index=returns.columns)
                else:
                    weights = raw_weights / raw_weights.sum()

            st.subheader("2️⃣ Portfolio Weights")
            st.write(weights.to_frame("weight"))

            # Rendement du portefeuille
            port_returns = pm.compute_portfolio_returns(returns, weights)
            metrics = pm.compute_portfolio_metrics(port_returns)

            if metrics is None:
                st.error("Erreur dans le calcul des métriques de portefeuille.")
            else:
                mean_annual = metrics["mean_annual"]
                vol_annual = metrics["vol_annual"]
                sharpe = metrics["sharpe"]
                max_dd = metrics["max_drawdown"]
                cum_value = metrics["cum_value"]

                # ---- Metrics ----
                st.subheader("3️⃣ Portfolio Metrics")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Annual Return", f"{mean_annual:.2%}")
                col2.metric("Annual Volatility", f"{vol_annual:.2%}")
                col3.metric("Sharpe Ratio", f"{sharpe:.2f}")
                col4.metric("Max Drawdown", f"{max_dd:.2%}")

                # ---- Courbes actifs + portefeuille ----
                st.subheader("4️⃣ Normalized Prices & Portfolio Value")

                norm_prices = prices / prices.iloc[0]
                port_norm = cum_value / cum_value.iloc[0]

                fig = go.Figure()

                # Actifs
                for col in norm_prices.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=norm_prices.index,
                            y=norm_prices[col],
                            mode="lines",
                            name=col
                        )
                    )

                # Portefeuille
                fig.add_trace(
                    go.Scatter(
                        x=port_norm.index,
                        y=port_norm.values,
                        mode="lines",
                        name="Portfolio",
                        line=dict(width=4)
                    )
                )

                fig.update_layout(
                    title="Normalized Prices (base 1) & Portfolio Value",
                    xaxis_title="Date",
                    yaxis_title="Normalized Value",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # ---- Corrélation ----
                st.subheader("5️⃣ Correlation Matrix")

                corr = pm.compute_correlation(returns)

                fig_corr = go.Figure(
                    data=go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.index,
                        zmin=-1,
                        zmax=1,
                        colorbar=dict(title="Corr")
                    )
                )
                fig_corr.update_layout(title="Assets Correlation Matrix")

                st.plotly_chart(fig_corr, use_container_width=True)

                # ---- Stats par actif ----
                st.subheader("6️⃣ Per-Asset Stats (Annualized)")

                mean_daily_assets = returns.mean()
                vol_daily_assets = returns.std()

                mean_annual_assets = mean_daily_assets * 252
                vol_annual_assets = vol_daily_assets * (252 ** 0.5)

                stats_df = pd.DataFrame({
                    "Annual Return": mean_annual_assets,
                    "Annual Vol": vol_annual_assets,
                })

                st.dataframe(stats_df.style.format("{:.2%}"))
