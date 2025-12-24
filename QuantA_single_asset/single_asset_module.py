import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

def fetch_financial_data(symbol, start_date, end_date):
    """Récupère les données historiques via Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        # On ajoute un jour à la fin pour inclure la date de fin dans yfinance
        data = ticker.history(start=start_date, end=end_date)
        
        if data.empty:
            return None
            
        # Calcul des rendements
        data['Daily Return'] = data['Close'].pct_change()
        data['Cumulative Return'] = (1 + data['Daily Return']).cumprod()
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def buy_and_hold_strategy(data, initial_capital):
    """Stratégie Buy and Hold."""
    df = data.copy()
    df['Position'] = 1
    df['Holdings'] = initial_capital * df['Cumulative Return']
    df['Strategy Returns'] = df['Daily Return']
    return df

def momentum_strategy(data, initial_capital, lookback_period=20, threshold=0.02):
    """Stratégie Momentum."""
    df = data.copy()
    df['Momentum'] = df['Close'].pct_change(lookback_period)
    
    df['Signal'] = 0
    df.loc[df['Momentum'] > threshold, 'Signal'] = 1
    df.loc[df['Momentum'] < -threshold, 'Signal'] = -1
    
    # Correction Warning Pandas : Utilisation de ffill() explicite
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    
    # Rendements : décalage d'un jour pour éviter le 'look-ahead bias'
    df['Strategy Returns'] = df['Position'].shift(1) * df['Daily Return']
    df['Strategy Cumulative Returns'] = (1 + df['Strategy Returns'].fillna(0)).cumprod()
    df['Holdings'] = initial_capital * df['Strategy Cumulative Returns']
    
    return df

def calculate_metrics(data, initial_capital):
    """Calcule les KPIs financiers."""
    if 'Strategy Returns' not in data.columns:
        returns = data['Daily Return']
        final_val = data['Close'].iloc[-1] * (initial_capital / data['Close'].iloc[0])
    else:
        returns = data['Strategy Returns']
        final_val = data['Holdings'].iloc[-1]

    # Rendement total
    total_return = (final_val / initial_capital) - 1
    
    # Rendement annuel (252 jours de trading)
    if len(data) > 0:
        annual_return = (1 + total_return) ** (252 / len(data)) - 1
    else:
        annual_return = 0
    
    # Volatilité
    volatility = returns.std() * np.sqrt(252)
    
    # Sharpe Ratio (taux sans risque supposé à 0 pour simplifier)
    sharpe = annual_return / volatility if volatility != 0 else 0
    
    # Max Drawdown
    cum_returns = (1 + returns).cumprod()
    running_max = cum_returns.expanding().max()
    drawdown = (cum_returns - running_max) / running_max
    max_drawdown = drawdown.min()

    return {
        "Total Return": total_return,
        "Annual Return": annual_return,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown,
        "Final Value": final_val
    }

def run_predictive_model(data, forecast_days=30):
    """
    Modèle de Régression Linéaire pour prédiction avec Intervalles de Confiance.
    Returns: future_dates, future_preds, lower_bound, upper_bound, r2
    """
    df = data[['Close']].copy().dropna()
    
    # Feature Engineering: Lag features (J-1 à J-5)
    for i in range(1, 6):
        df[f'Lag_{i}'] = df['Close'].shift(i)
    df = df.dropna()
    
    X = df[['Lag_1', 'Lag_2', 'Lag_3', 'Lag_4', 'Lag_5']]
    y = df['Close']
    
    # Train/Test split (80/20)
    split = int(len(df) * 0.8)
    X_train, y_train = X.iloc[:split], y.iloc[:split]
    X_test, y_test = X.iloc[split:], y.iloc[split:]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Calcul de l'intervalle de confiance
    # On utilise l'erreur quadratique moyenne (RMSE) sur le set de test
    # pour estimer l'incertitude future (Intervalle à 95% = +/- 1.96 * RMSE)
    y_pred_test = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    confidence_interval = 1.96 * rmse
    
    # Prédictions futures
    last_features = X.iloc[-1:].values
    future_preds = []
    
    for _ in range(forecast_days):
        pred = model.predict(last_features)[0]
        future_preds.append(pred)
        # Shift pour mettre à jour les lags avec la nouvelle prédiction
        last_features = np.roll(last_features, -1)
        last_features[0, -1] = pred
        
    future_dates = [data.index[-1] + timedelta(days=i) for i in range(1, forecast_days + 1)]
    
    # Création des bornes (Low / High)
    lower_bound = [p - confidence_interval for p in future_preds]
    upper_bound = [p + confidence_interval for p in future_preds]
    
    # Metrics du modèle
    r2 = r2_score(y_test, y_pred_test)
    
    return future_dates, future_preds, lower_bound, upper_bound, r2
