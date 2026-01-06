import yfinance as yf
import pandas as pd
import numpy as np



# 1. Data


def fetch_multi_asset_data(symbols, start_date, end_date):
    """
    Récupère les prix ajustés (auto_adjust=True => "Close" ajusté)
    pour plusieurs tickers via Yahoo Finance.

    Returns
    -------
    prices : pd.DataFrame or None
        Index = dates, colonnes = tickers, valeurs = prix.
    """
    if not symbols:
        return None

    try:
        data = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
            group_by="column"
        )

        # yfinance renvoie souvent un MultiIndex (Price field, ticker)
        if isinstance(data.columns, pd.MultiIndex):
            # Le champ peut être "Close" en auto_adjust
            if "Close" in data.columns.get_level_values(0):
                prices = data["Close"]
            else:
                # fallback
                prices = data.xs("Close", axis=1, level=0, drop_level=False)
        else:
            prices = data

        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=symbols[0])

        # Drop lignes vides
        prices = prices.dropna(how="all")

        # Drop colonnes entièrement vides (tickers invalides)
        prices = prices.dropna(axis=1, how="all")

        if prices.empty:
            return None

        return prices

    except Exception as e:
        return None



# 2. returns & correlations


def compute_returns(prices: pd.DataFrame, log_return: bool = False) -> pd.DataFrame:
    """
    Calcule les rendements journaliers.

    log_return=True : log(prices/prices.shift(1))
    sinon : pct_change()
    """
    if prices is None or prices.empty:
        return pd.DataFrame()

    if log_return:
        returns = np.log(prices / prices.shift(1))
    else:
        returns = prices.pct_change()

    returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")
    returns = returns.dropna()
    return returns


def compute_correlation(returns: pd.DataFrame) -> pd.DataFrame:
    if returns is None or returns.empty:
        return pd.DataFrame()
    return returns.corr()



# 3. Portfolio : helpers

def normalize_weights(weights, columns):
    """Convertit/norme les poids en pd.Series aligné sur columns."""
    if weights is None:
        return pd.Series(dtype=float)

    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=columns)

    weights = weights.reindex(columns).fillna(0.0)
    s = weights.sum()
    if s == 0:
        return pd.Series(1 / len(columns), index=columns)
    return weights / s


def _rebal_dates(index: pd.DatetimeIndex, freq: str):
    """
    Retourne les dates (dans l'index) où on rebalance.
    freq: "none", "daily", "weekly", "monthly"
    """
    if freq == "none":
        return pd.DatetimeIndex([])

    if freq == "daily":
        return index

    # For weekly/monthly, we take the last available date of each periods
    s = pd.Series(index=index, data=np.ones(len(index)))
    if freq == "weekly":
        grp = s.resample("W").last().dropna().index
    elif freq == "monthly":
        grp = s.resample("M").last().dropna().index
    else:
        grp = pd.DatetimeIndex([])

    # We keep only existing-in-index ones
    return index.intersection(grp)



# 4. Portfolio : calculus


def compute_portfolio_value(
    prices: pd.DataFrame,
    weights,
    rebalancing: str = "monthly"
) -> pd.Series:
    """
    Calcule la valeur du portefeuille (base 1) à partir des PRICES,
    en simulant un rebalancement.

    - rebalancing: "none", "daily", "weekly", "monthly"
      * none  : buy-and-hold (poids initiaux, drift)
      * daily : rebal chaque jour (poids constants)
      * weekly/monthly : rebal aux fins de périodes

    Hypothèses : pas de frais, pas de cash, allocations long-only.
    """
    if prices is None or prices.empty:
        return pd.Series(dtype=float)

    prices = prices.dropna().copy()
    cols = prices.columns
    w = normalize_weights(weights, cols)

    # Normalization
    norm = prices / prices.iloc[0]

    # Initial value
    V = 1.0

    units = (V * w) / norm.iloc[0]

    rebalancing = rebalancing.lower()
    rebal_dates = set(_rebal_dates(norm.index, rebalancing))

    out = []
    for dt, row in norm.iterrows():
        V = float((units * row).sum())
        out.append((dt, V))

        if dt in rebal_dates and dt != norm.index[0] and rebalancing != "none":
            units = (V * w) / row

    port_value = pd.Series(dict(out)).sort_index()
    port_value.name = "PortfolioValue"
    return port_value


def compute_portfolio_returns_from_value(
    port_value: pd.Series,
    log_return: bool = False
) -> pd.Series:
    """Rendements du portefeuille dérivés de la série de valeur."""
    if port_value is None or port_value.empty:
        return pd.Series(dtype=float)

    if log_return:
        r = np.log(port_value / port_value.shift(1))
    else:
        r = port_value.pct_change()

    r = r.replace([np.inf, -np.inf], np.nan).dropna()
    r.name = "PortfolioReturns"
    return r


def compute_portfolio_metrics(
    port_returns: pd.Series,
    periods_per_year: int = 252,
    rf: float = 0.0,
    log_return: bool = False
):
    """
    Calcule les métriques du portefeuille.
    rf : taux sans risque annualisé (ex: 0.02 pour 2%)
    """
    if port_returns is None or port_returns.empty:
        return None

    mean_daily = port_returns.mean()
    vol_daily = port_returns.std()

    mean_annual = mean_daily * periods_per_year
    vol_annual = vol_daily * np.sqrt(periods_per_year)

    sharpe = (mean_annual - rf) / vol_annual if vol_annual > 0 else np.nan

    if log_return:
        cum_value = np.exp(port_returns.cumsum())
    else:
        cum_value = (1 + port_returns).cumprod()

    running_max = cum_value.cummax()
    drawdown = (cum_value - running_max) / running_max
    max_dd = float(drawdown.min()) if not drawdown.empty else np.nan

    return {
        "mean_annual": float(mean_annual),
        "vol_annual": float(vol_annual),
        "sharpe": float(sharpe) if np.isfinite(sharpe) else np.nan,
        "max_drawdown": max_dd,
        "cum_value": cum_value
    }


# 5. Diversification

def compute_risk_contributions(returns: pd.DataFrame, weights, periods_per_year: int = 252):
    """
    Contribution au risque (vol) approximée via covariance:
      RC_i = w_i * (Σ w)_i / (w' Σ w)
    Retourne un DataFrame avec:
      - weight
      - marginal_contrib
      - risk_contrib (part)
    """
    if returns is None or returns.empty:
        return pd.DataFrame()

    cov = returns.cov() * periods_per_year
    cols = cov.columns
    w = normalize_weights(weights, cols).to_numpy(dtype=float).reshape(-1, 1)

    port_var = (w.T @ cov.to_numpy(dtype=float) @ w).item()
    if port_var <= 0:
        return pd.DataFrame()

    mrc = (cov.values @ w)  # marginal contribution to variance
    rc = (w * mrc) / port_var  # fraction of variance

    df = pd.DataFrame({
        "weight": w.flatten(),
        "marginal_contrib": mrc.flatten(),
        "risk_contrib": rc.flatten()
    }, index=cols)

    return df.sort_values("risk_contrib", ascending=False)


def compute_return_contributions(returns: pd.DataFrame, weights, periods_per_year: int = 252):
    """
    Contribution au rendement annualisé (simple):
      contrib_i = w_i * mean_i * periods_per_year
    """
    if returns is None or returns.empty:
        return pd.DataFrame()

    cols = returns.columns
    w = normalize_weights(weights, cols)
    mu_annual = returns.mean() * periods_per_year
    contrib = w * mu_annual

    df = pd.DataFrame({
        "weight": w,
        "mu_annual": mu_annual,
        "return_contrib": contrib
    }).sort_values("return_contrib", ascending=False)

    return df

