# Quantitative Finance Dashboard — Python, Git & Linux

## Project Overview

This project is developed as part of the **Python, Git, Linux for Finance** module. It simulates a professional quantitative research workflow within an asset management context.

The objective is to design, deploy, and maintain a **24/7 online financial dashboard** that retrieves real-time market data, performs quantitative analysis and backtesting, and presents results in a clear, interactive, and professional interface.

The platform is built in **Python**, deployed on a **Linux virtual machine**, and collaboratively developed using **Git/GitHub**.

---

## Global Architecture

The final application is a **single integrated dashboard** composed of two independent but compatible modules:

* **Quant A — Single Asset Analysis (Univariate)**
* **Quant B — Multi-Asset Portfolio Analysis (Multivariate)**

Each module includes both:

* a **back-end** layer (data retrieval, calculations, models), and
* a **front-end** layer (interactive Streamlit dashboard).

---

## Repository Structure

```text
python_git_linux/
│
├── QuantA_single_asset/          # Quant A module (Single Asset)
│   ├── dashboard_quanta.py       # Streamlit dashboard (front-end)
│   ├── single_asset_module.py    # Data, strategies, metrics, forecasting
│   └── requirement_quanta.txt    # Python dependencies (Quant A)
│
├── scripts/
│   ├── daily_report.py           # Automated daily report generator
│   └── cron_setup.md             # Cron job configuration documentation
│
├── daily_reports/                # Generated daily reports (created at runtime)
├── README.md
└── .gitignore
```

---

## Git Workflow & Collaboration

* **main**: stable integration branch
* **quant-a-single-asset**: Quant A development branch
* **quant-b-portfolio**: Quant B development branch

Each contributor works exclusively on their dedicated branch.
Integration is done via **pull requests**, ensuring:

* clean commit history,
* conflict resolution traceability,
* clear separation of responsibilities.

---

## Quant A — Single Asset Analysis Module

### Features

* Real-time data retrieval via **Yahoo Finance (yfinance)**
* Analysis of one asset at a time (stocks, FX, crypto)
* Implemented strategies:

  * Buy & Hold
  * Momentum strategy (parameterized lookback & threshold)
* Performance metrics:

  * Total & annual return
  * Volatility
  * Sharpe ratio
  * Maximum drawdown
* Interactive parameter controls (dates, capital, strategy parameters)
* Main chart displaying:

  * raw asset price
  * cumulative portfolio value of strategies

### Bonus — Predictive Model

* Linear regression with lagged features
* 30-day price forecast
* Approximate 95% confidence interval
* Model accuracy displayed via R² score

---

## Automated Daily Reporting (Cron)

A daily quantitative report is automatically generated **every day at 8:00 PM** using a Linux cron job.

### Metrics included

* Last closing price
* Daily variation
* Annualized volatility
* 1-year maximum drawdown

### Cron configuration

The cron job configuration is documented in:

```
scripts/cron_setup.md
```

Example cron entry:

```bash
0 20 * * * cd /ABSOLUTE/PATH/python_git_linux && /usr/bin/python3 scripts/daily_report.py >> scripts/daily_report.log 2>&1
```

Generated reports are stored locally in:

```
daily_reports/
```

---

## Installation & Execution

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies (Quant A)

```bash
pip install -r QuantA_single_asset/requirement_quanta.txt
```

### 3. Run the Streamlit dashboard

```bash
streamlit run QuantA_single_asset/dashboard_quanta.py
```

The application automatically refreshes data and handles API errors gracefully.

---

## Robustness & Production Considerations

* Safe handling of missing or insufficient data
* No look-ahead bias in backtesting
* Error logging for cron executions
* Modular and readable code structure
* Minimal dependencies to reduce deployment cost

---

## Evaluation Criteria — Compliance Checklist

* Real-time dynamic data source ✅
* Interactive dashboard (Streamlit) ✅
* Backtesting strategies implemented ✅
* Clear visualization of results ✅
* Daily automated report via cron ✅
* Proper GitHub workflow & structure ✅
* Bonus: predictive model with confidence interval ✅

---

## Authors

* **Quant A — Single Asset Analysis**: Alone HAYAT
* **Quant B — Portfolio Analysis**: Benjamin KORN-BRZOZA

---

## Disclaimer

This project is developed for academic purposes and does not constitute financial advice.
