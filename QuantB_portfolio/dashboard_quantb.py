import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
# Cache data fetch
# ===========================
@st.cache_data(ttl=300, show_spinner=False)  # cache 5 min
def cached_fetch(tickers, start_str, end_str):
    return pm.fetch_multi_asset_data(tickers, start_str, end_str)


# ===========================
# Sidebar : paramètres
# ===========================

st.sidebar.header("Portfolio Settings")

default_tickers = "AAPL, MSFT, GOOGL"
tickers_input = st.sidebar.text_input(
    "Tickers (séparés par des virgules)",
    value=default_tickers
)

today = datetime.today().date()
one_year_ago = today - timedelta(days=365)

start_date = st.sidebar.date_input("Start Date", one_year_ago)
end_date = st.sidebar.date_input("End Date", today)

weight_mode = st.sidebar.radio(
    "Weights mode",
    ["Equal Weight", "Custom Weights"]
)

rebalancing = st.sidebar.selectbox(
    "Rebalancing frequency",
    ["None (Buy & Hold)", "Daily", "Weekly", "Monthly"],
    index=3
)

log_return = st.sidebar.checkbox("Use log returns", value=False)

rf = st.sidebar.number_input(
    "Risk-free rate (annual, ex: 0.02 = 2%)",
    min_value=-0.50,
    max_value=1.00,
    value=0.00,
    step=0.01
)

run_button = st.sidebar.button("Run Portfolio Analysis")


# ===========================
# Main
# ===========================

if not run_button:
    st.info("Configure le portefeuille dans la sidebar puis clique sur **Run Portfolio Analysis**.")
else:
    # Validation dates
    if start_date >= end_date:
        st.error("Start Date must be before End Date.")
        st.stop()

    # Nettoyage tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    tickers = list(dict.fromkeys(tickers))  # unique, conserve l'ordre

    if len(tickers) == 0:
        st.error("Veuillez entrer au moins un ticker.")
        st.stop()

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    with st.spinner("Fetching data from Yahoo Finance..."):
        prices = cached_fetch(tickers, start_str, end_str)

    if prices is None or prices.empty:
        st.error("Aucune donnée trouvée pour ces tickers / cette période.")
        st.stop()

    # Tickers réellement récupérés
    fetched = list(prices.columns)
    missing = [t for t in tickers if t not in fetched]
    if missing:
        st.warning(f"Tickers ignorés (pas de données): {', '.join(missing)}")

    if len(fetched) < 1:
        st.error("Aucun ticker valide après récupération des données.")
        st.stop()

    # Petites infos dataset
    st.subheader("0️⃣ Dataset Summary")
    colA, colB, colC = st.columns(3)
    colA.metric("Tickers used", str(len(fetched)))
    colB.metric("Start (effective)", str(prices.index.min().date()))
    colC.metric("End (effective)", str(prices.index.max().date()))

    st.subheader("1️⃣ Raw Prices (tail)")
    st.dataframe(prices.tail())

    # Rendements actifs
    returns = pm.compute_returns(prices, log_return=log_return)
    if returns.empty:
        st.error("Impossible de calculer les rendements (données insuffisantes).")
        st.stop()

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
                value=float(1.0 / len(returns.columns)),
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
    st.dataframe(weights.to_frame("weight").style.format("{:.2%}"))

    # -------------------------
    # Rebalancing mapping
    # -------------------------
    reb_map = {
        "None (Buy & Hold)": "none",
        "Daily": "daily",
        "Weekly": "weekly",
        "Monthly": "monthly"
    }
    reb = reb_map.get(rebalancing, "monthly")

    # -------------------------
    # Valeur portefeuille + returns portefeuille
    # -------------------------
    port_value = pm.compute_portfolio_value(prices, weights, rebalancing=reb)
    if port_value.empty:
        st.error("Erreur dans le calcul de la valeur portefeuille.")
        st.stop()

    port_returns = pm.compute_portfolio_returns_from_value(port_value, log_return=log_return)
    metrics = pm.compute_portfolio_metrics(
        port_returns,
        periods_per_year=252,
        rf=float(rf),
        log_return=log_return
    )

    if metrics is None:
        st.error("Erreur dans le calcul des métriques de portefeuille.")
        st.stop()

    mean_annual = metrics["mean_annual"]
    vol_annual = metrics["vol_annual"]
    sharpe = metrics["sharpe"]
    max_dd = metrics["max_drawdown"]
    cum_value = metrics["cum_value"]

    # ---- Metrics ----
    st.subheader("3️⃣ Portfolio Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Annual Return", f"{mean_annual:.2%}")
    col2.metric("Annual Volatility", f"{vol_annual:.2%}")
    col3.metric("Sharpe Ratio", f"{sharpe:.2f}" if pd.notna(sharpe) else "NaN")
    col4.metric("Max Drawdown", f"{max_dd:.2%}" if pd.notna(max_dd) else "NaN")
    col5.metric("Rebalancing", rebalancing)

    # ---- Courbes actifs + portefeuille ----
    st.subheader("4️⃣ Normalized Prices & Portfolio Value")

    norm_prices = prices / prices.iloc[0]
    port_norm = port_value / port_value.iloc[0]

    fig = go.Figure()

    for col in norm_prices.columns:
        fig.add_trace(go.Scatter(
            x=norm_prices.index,
            y=norm_prices[col],
            mode="lines",
            name=col
        ))

    fig.add_trace(go.Scatter(
        x=port_norm.index,
        y=port_norm.values,
        mode="lines",
        name="Portfolio",
        line=dict(width=4)
    ))

    fig.update_layout(
        title="Normalized Prices (base 1) & Portfolio Value",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---- Corrélation ----
    st.subheader("5️⃣ Correlation Matrix")

    corr = pm.compute_correlation(returns)
    if corr.empty:
        st.warning("Matrice de corrélation indisponible.")
    else:
        fig_corr = go.Figure(data=go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            zmin=-1, zmax=1,
            colorbar=dict(title="Corr")
        ))
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

    # ---- Diversification effects ----
    st.subheader("7️⃣ Diversification (Contributions)")

    rc = pm.compute_risk_contributions(returns, weights, periods_per_year=252)
    if not rc.empty:
        st.markdown("**Risk contribution** (part de variance) :")
        st.dataframe(
            rc[["weight", "risk_contrib"]].style.format({"weight": "{:.2%}", "risk_contrib": "{:.2%}"})
        )

        fig_rc = go.Figure()
        fig_rc.add_trace(go.Bar(
            x=rc.index,
            y=rc["risk_contrib"],
            name="Risk Contribution"
        ))
        fig_rc.update_layout(
            title="Risk Contribution by Asset (share of variance)",
            xaxis_title="Asset",
            yaxis_title="Risk Contribution"
        )
        st.plotly_chart(fig_rc, use_container_width=True)
    else:
        st.warning("Risk contribution indisponible (covariance/vol nulle ou données insuffisantes).")

    rcontrib = pm.compute_return_contributions(returns, weights, periods_per_year=252)
    if not rcontrib.empty:
        st.markdown("**Return contribution** (annualisé) :")
        st.dataframe(
            rcontrib[["weight", "mu_annual", "return_contrib"]].style.format({
                "weight": "{:.2%}",
                "mu_annual": "{:.2%}",
                "return_contrib": "{:.2%}"
            })
        )

        fig_rcontrib = go.Figure()
        fig_rcontrib.add_trace(go.Bar(
            x=rcontrib.index,
            y=rcontrib["return_contrib"],
            name="Return Contribution"
        ))
        fig_rcontrib.update_layout(
            title="Return Contribution by Asset (annualized)",
            xaxis_title="Asset",
            yaxis_title="Return Contribution"
        )
        st.plotly_chart(fig_rcontrib, use_container_width=True)
    else:
        st.warning("Return contribution indisponible.")
