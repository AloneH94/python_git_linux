import numpy as np
import pandas as pd
import yfinance as yf

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


# ----------------------------
# Data fetching
# ----------------------------
def fetch_financial_data(ticker, start_date, end_date):
    """
    Fetch OHLCV data from Yahoo Finance.
    Returns a DataFrame indexed by Date with columns including 'Close'.
    """
    df = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if df is None or df.empty:
        return pd.DataFrame()

    df.index = pd.to_datetime(df.index)
    return df


# ----------------------------
# Strategies
# ----------------------------
def buy_and_hold_strategy(df, initial_capital):
    """
    Buy & Hold: invest full capital at first date, hold until end.
    Returns df_strat with columns: 'Holdings', 'Strategy_Return'
    """
    out = df.copy()
    out = out.dropna(subset=["Close"])

    first_price = float(out["Close"].iloc[0])
    if first_price <= 0:
        out["Holdings"] = np.nan
        out["Strategy_Return"] = np.nan
        return out

    shares = initial_capital / first_price
    out["Holdings"] = shares * out["Close"]
    out["Strategy_Return"] = out["Holdings"].pct_change().fillna(0.0)
    return out


def momentum_strategy(df, initial_capital, lookback=20, threshold=0.02):
    """
    Simple momentum strategy:
    - Compute lookback return: Close / Close.shift(lookback) - 1
    - Signal = 1 if lookback_return > threshold else 0
    - When signal=1 we are invested, else we are in cash
    Returns df_strat with: 'Signal', 'Holdings', 'Strategy_Return'
    """
    out = df.copy()
    out = out.dropna(subset=["Close"])

    out["Lookback_Return"] = out["Close"] / out["Close"].shift(lookback) - 1.0
    out["Signal"] = (out["Lookback_Return"] > threshold).astype(int)

    # daily asset returns
    out["Asset_Return"] = out["Close"].pct_change().fillna(0.0)

    # Strategy return: earn asset return only when invested
    out["Strategy_Return"] = out["Signal"].shift(1).fillna(0).astype(int) * out["Asset_Return"]

    # Portfolio value
    out["Holdings"] = initial_capital * (1.0 + out["Strategy_Return"]).cumprod()
    return out


# ----------------------------
# Metrics
# ----------------------------
def _max_drawdown(equity_curve: pd.Series) -> float:
    running_max = equity_curve.cummax()
    dd = equity_curve / running_max - 1.0
    return float(dd.min())


def calculate_metrics(df_strat, initial_capital, trading_days=252):
    """
    Compute basic performance metrics from a strategy DataFrame with:
    - 'Holdings' (portfolio value)
    - 'Strategy_Return' (daily strategy returns)
    Returns dict with keys used in dashboard_quanta.py.
    """
    out = {}
    if df_strat is None or df_strat.empty or "Holdings" not in df_strat.columns:
        # return safe defaults
        return {
            "Total Return": 0.0,
            "Annual Return": 0.0,
            "Volatility": 0.0,
            "Sharpe Ratio": 0.0,
            "Max Drawdown": 0.0,
            "Final Value": float(initial_capital),
        }

    holdings = df_strat["Holdings"].dropna()
    if holdings.empty:
        return {
            "Total Return": 0.0,
            "Annual Return": 0.0,
            "Volatility": 0.0,
            "Sharpe Ratio": 0.0,
            "Max Drawdown": 0.0,
            "Final Value": float(initial_capital),
        }

    final_value = float(holdings.iloc[-1])
    total_return = final_value / float(initial_capital) - 1.0

    # daily returns
    if "Strategy_Return" in df_strat.columns:
        rets = df_strat["Strategy_Return"].dropna()
    else:
        rets = holdings.pct_change().dropna()

    # guard
    if rets.empty:
        ann_return = 0.0
        vol = 0.0
        sharpe = 0.0
    else:
        vol = float(rets.std()) * np.sqrt(trading_days)
        ann_return = float((1.0 + rets.mean()) ** trading_days - 1.0)
        sharpe = float(ann_return / vol) if vol > 0 else 0.0

    mdd = _max_drawdown(holdings)

    out["Total Return"] = float(total_return)
    out["Annual Return"] = float(ann_return)
    out["Volatility"] = float(vol)
    out["Sharpe Ratio"] = float(sharpe)
    out["Max Drawdown"] = float(mdd)
    out["Final Value"] = float(final_value)
    return out


# ----------------------------
# Predictive model (your function)
# ----------------------------
def run_predictive_model(data, forecast_days=30):
    """
    Linear Regression forecast with confidence interval (approx 95% based on test RMSE).
    Returns: future_dates, future_preds, lower_bound, upper_bound, r2
    """
    df = data[["Close"]].copy().dropna()

    for i in range(1, 6):
        df[f"Lag_{i}"] = df["Close"].shift(i)
    df = df.dropna()

    X = df[["Lag_1", "Lag_2", "Lag_3", "Lag_4", "Lag_5"]]
    y = df["Close"]

    split = int(len(df) * 0.8)
    X_train, y_train = X.iloc[:split], y.iloc[:split]
    X_test, y_test = X.iloc[split:], y.iloc[split:]

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred_test = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    confidence_interval = 1.96 * rmse

    last_features = X.iloc[-1].to_numpy().reshape(1, -1)
    future_preds = []

    for _ in range(forecast_days):
        pred = float(model.predict(last_features)[0])
        future_preds.append(pred)
        last_features[:, 1:] = last_features[:, :-1]
        last_features[:, 0] = pred

    future_dates = pd.bdate_range(start=data.index[-1], periods=forecast_days + 1)[1:]
    future_dates = future_dates.to_pydatetime().tolist()

    lower_bound = [p - confidence_interval for p in future_preds]
    upper_bound = [p + confidence_interval for p in future_preds]
    r2 = r2_score(y_test, y_pred_test)

    return future_dates, future_preds, lower_bound, upper_bound, r2
