#Quant B: Module for Multi-Asset Portfolio Analysis

## Synopsis
The goal of the multi-asset portfolio analysis module Quant B is to examine risk-return decomposition, diversification, rebalancing techniques, and portfolio construction.  
It enhances Quant A by moving the emphasis from single-asset analysis to portfolio-level quantitative finance and is fully integrated into the Streamlit dashboard.

The fundamental ideas of quantitative asset allocation and professional portfolio management are replicated in this module.

## Information Sources

Quant B uses the Yahoo Finance API, which can be accessed via the yfinance Python library, to obtain historical price data.

Among the supported asset classes are:The stocks
ETFs
Indices of the marketCryptocurrency
FX pairs
Commodities

To guarantee uniformity across dividends and corporate actions, adjusted prices are used (auto_adjust=True). ```python yf.download( symbols, start=start_date, end=end_date, auto_adjust=True)
