# Quantitative Finance Dashboard — Python, Git & Linux

## Project Overview

The Python, Git, Linux for Finance course includes this project.  
It mimics an asset management company's professional quantitative research workflow.

The objective is to create a 24/7 financial dashboard that:obtains data about the dynamic market,
employs portfolio simulations and quantitative strategies, shows outcomes in a polished and interactive interface, operates on a virtual machine running Linux and is created cooperatively with Git/GitHub.

The application is written in Python and uses Streamlit for the front-end.


## Global Architecture

The platform consists of two modules that make up a single Streamlit application:
Quant A: Univariate Single Asset Analysis
Quant B: Multivariate Multi-Asset Portfolio Analysis

Both modules are integrated into a single dashboard using tabs.

Every module consists of:A back-end layer that includes computations, models, and data retrieval
The front-end layer includes user interaction and visualization.

---

## Repository Structure

```text
python_git_linux/
│
├── QuantA_single_asset/
│   ├── dashboard_quanta.py        # Main Streamlit app (Quant A + Quant B tabs)
│   ├── single_asset_module.py     # Data fetching, strategies, metrics, forecasting
│   └── requirement_quanta.txt     # Dependencies specific to Quant A
│
├── QuantB_portfolio/
│   ├── __init__.py
│   ├── dashboard_quantb.py        # Quant B Streamlit rendering logic
│   └── portfolio_module.py        # Portfolio computations & metrics
│
├── scripts/
│   ├── daily_report.py            # Automated daily report generator
│   └── cron_setup.md              # Cron job configuration documentation
│
├── daily_reports/                 # Generated reports (created at runtime)
├── requirements.txt               # Global dependencies
├── README.md
└── .gitignore
