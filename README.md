# Quant A — Module for Single Asset Analysis ## Synopsis
The single-asset quantitative analysis module Quant A is intended to carry out short-term price forecasting, strategy backtesting, performance evaluation, and financial data retrieval.  
It uses market data from external APIs to function in real time and is integrated into a Streamlit dashboard.

A professional quantitative research workflow that is frequently utilized in trading desks and asset management is replicated in this module.

## Data Sources

The module employs a two-layer API strategy to retrieve financial time series:

###1. Yahoo Finance API is the primary source.The `yfinance` Python library provides access.  
Supports commodities, stocks, indices, ETFs, foreign exchange, and cryptocurrency.  OHLC and adjusted close prices are provided.Python yf.download (ticker, start=start, end=end)
