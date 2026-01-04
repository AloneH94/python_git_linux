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

    # Intervalle de confiance basé sur RMSE test (approx 95%)
    y_pred_test = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    confidence_interval = 1.96 * rmse

    # Prédictions futures (récursives) en mettant à jour les lags
    last_features = X.iloc[-1].to_numpy().reshape(1, -1)  # shape (1,5)
    future_preds = []

    for _ in range(forecast_days):
        pred = model.predict(last_features)[0]
        future_preds.append(pred)

        # shift right: Lag5 <- Lag4 <- ... <- Lag1, et Lag1 <- pred
        last_features[:, 1:] = last_features[:, :-1]
        last_features[:, 0] = pred

    # Dates futures (jours ouvrés)
    future_dates = pd.bdate_range(start=data.index[-1], periods=forecast_days + 1)[1:]
    future_dates = future_dates.to_pydatetime().tolist()

    lower_bound = [p - confidence_interval for p in future_preds]
    upper_bound = [p + confidence_interval for p in future_preds]

    r2 = r2_score(y_test, y_pred_test)

    return future_dates, future_preds, lower_bound, upper_bound, r2
