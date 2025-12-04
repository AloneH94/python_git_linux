import yfinance as yf
import pandas as pd
import numpy as np


# ===========================
# 1. Récupération des données
# ===========================

def fetch_multi_asset_data(symbols, start_date, end_date):
    """
    Récupère les prix de clôture ajustés pour plusieurs tickers via Yahoo Finance.

    Parameters
    ----------
    symbols : list[str]
        Liste de tickers, ex: ["AAPL", "MSFT", "GOOGL"]
    start_date : str
        Date de début "YYYY-MM-DD"
    end_date : str
        Date de fin "YYYY-MM-DD"

    Returns
    -------
    prices : pd.DataFrame ou None
        Index = dates, colonnes = tickers, valeurs = prix de clôture.
    """
    if not symbols:
        return None

    try:
        data = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False
        )

        # yfinance renvoie souvent un MultiIndex (Open, High, Low, Close...)
        # On garde la colonne 'Close'
        if isinstance(data.columns, pd.MultiIndex):
            prices = data["Close"]
        else:
            prices = data

        # Cas d'un seul ticker -> Series -> on convertit en DataFrame
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=symbols[0])

        prices = prices.dropna(how="all")
        if prices.empty:
            return None

        return prices

    except Exception as e:
        print(f"Erreur lors de la récupération des données multi-actifs : {e}")
        return None


# ===========================
# 2. Rendements & corrélations
# ===========================

def compute_returns(prices, log_return=False):
    """
    Calcule les rendements journaliers des actifs.

    Parameters
    ----------
    prices : pd.DataFrame
        Prix de clôture.
    log_return : bool
        True -> rendements log, False -> rendements simples.

    Returns
    -------
    returns : pd.DataFrame
    """
    if log_return:
        returns = np.log(prices / prices.shift(1))
    else:
        returns = prices.pct_change()

    return returns.dropna()


def compute_correlation(returns):
    """Renvoie la matrice de corrélation entre actifs."""
    return returns.corr()


# ===========================
# 3. Portefeuille
# ===========================

def compute_portfolio_returns(returns, weights):
    """
    Calcule le rendement journalier du portefeuille.

    Parameters
    ----------
    returns : pd.DataFrame
        Rendements journaliers par actif.
    weights : pd.Series ou np.ndarray
        Poids du portefeuille (somme = 1).

    Returns
    -------
    port_returns : pd.Series
    """
    if not isinstance(weights, pd.Series):
        weights = pd.Series(weights, index=returns.columns)

    # normalisation des poids pour être sûr que la somme = 1
    weights = weights / weights.sum()
    port_returns = (returns * weights).sum(axis=1)
    return port_returns


def compute_portfolio_metrics(port_returns, periods_per_year=252, rf=0.0):
    """
    Calcule les métriques principales du portefeuille.

    Parameters
    ----------
    port_returns : pd.Series
        Rendements journaliers du portefeuille.
    periods_per_year : int
        Nombre de périodes par an (252 pour du daily).
    rf : float
        Taux sans risque annualisé.

    Returns
    -------
    metrics : dict
        - mean_annual
        - vol_annual
        - sharpe
        - max_drawdown
        - cum_value (pd.Series)
    """
    if port_returns is None or port_returns.empty:
        return None

    mean_daily = port_returns.mean()
    vol_daily = port_returns.std()

    mean_annual = mean_daily * periods_per_year
    vol_annual = vol_daily * np.sqrt(periods_per_year)

    sharpe = (mean_annual - rf) / vol_annual if vol_annual > 0 else np.nan

    # Valeur cumulée (capital initial = 1)
    cum_value = (1 + port_returns).cumprod()
    running_max = cum_value.cummax()
    drawdown = (cum_value - running_max) / running_max
    max_dd = drawdown.min()

    return {
        "mean_annual": mean_annual,
        "vol_annual": vol_annual,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "cum_value": cum_value
    }
