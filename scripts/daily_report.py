import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# ============================================================
# PATH CONFIG (robuste pour exécution manuelle + cron)
# ============================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))      # .../scripts
PROJECT_DIR = os.path.dirname(CURRENT_DIR)                   # .../python_git_linux
MODULE_DIR = os.path.join(PROJECT_DIR, "QuantA_single_asset") # .../QuantA_single_asset

if MODULE_DIR not in sys.path:
    sys.path.append(MODULE_DIR)

try:
    import single_asset_module as sam
    print("Module 'single_asset_module' imported successfully.")
except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
    print(f"Checked path: {MODULE_DIR}")
    sys.exit(1)

# ============================================================
# PARAMETERS
# ============================================================
ASSETS = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "EURUSD=X", "GC=F"]  # Gold futures = GC=F
REPORT_DIR = os.path.join(PROJECT_DIR, "daily_reports")


# ============================================================
# METRICS
# ============================================================
def _annualized_vol(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized volatility from periodic returns."""
    if returns is None or returns.dropna().empty:
        return float("nan")
    return float(returns.dropna().std() * (periods_per_year ** 0.5))


def _max_drawdown(returns: pd.Series) -> float:
    """Max drawdown computed from periodic returns."""
    if returns is None or returns.dropna().empty:
        return float("nan")
    cum = (1.0 + returns.dropna()).cumprod()
    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    return float(dd.min())


def _safe_float(x) -> float:
    """Convert to float safely, returns nan if it fails."""
    try:
        return float(x)
    except Exception:
        return float("nan")


# ============================================================
# REPORT GENERATION
# ============================================================
def generate_daily_report() -> str:
    """
    Génère un rapport TXT avec des stats de base sur une liste d'actifs.
    Retourne le chemin du fichier généré.
    """
    os.makedirs(REPORT_DIR, exist_ok=True)

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    report_file = os.path.join(REPORT_DIR, f"report_{today_str}.txt")

    # 1 an glissant
    end_date = now
    start_date = end_date - timedelta(days=365)

    print(f"Generating report for {today_str}...")
    print(f"Report directory: {REPORT_DIR}")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("==========================================\n")
        f.write("   DAILY QUANTITATIVE FINANCE REPORT\n")
        f.write(f"   Date: {today_str}\n")
        f.write("==========================================\n\n")

        for symbol in ASSETS:
            try:
                data = sam.fetch_financial_data(symbol, start_date, end_date)

                # --- safety checks ---
                if data is None or getattr(data, "empty", True) or len(data) < 2:
                    f.write(f"[!] Asset: {symbol} - Not enough data\n\n")
                    print(f"[WARN] Not enough data for {symbol}")
                    continue

                if "Close" not in data.columns:
                    f.write(f"[!] Asset: {symbol} - Missing 'Close' column\n\n")
                    print(f"[WARN] Missing 'Close' for {symbol}. Columns: {list(data.columns)}")
                    continue

                # --- last values ---
                last_close = _safe_float(data["Close"].iloc[-1])
                prev_close = _safe_float(data["Close"].iloc[-2])

                daily_var = float("nan")
                if pd.notna(last_close) and pd.notna(prev_close) and prev_close != 0:
                    daily_var = ((last_close - prev_close) / prev_close) * 100.0

                last_open = float("nan")
                if "Open" in data.columns:
                    last_open = _safe_float(data["Open"].iloc[-1])

                # --- returns over 1 year ---
                returns = data["Close"].pct_change().dropna()
                vol = _annualized_vol(returns, periods_per_year=252)
                max_dd = _max_drawdown(returns)

                # --- write report block ---
                f.write(f"Asset: {symbol}\n")
                f.write("----------------------------\n")
                f.write(f"Open (last):       {last_open:.2f}\n" if pd.notna(last_open) else "Open (last):       N/A\n")
                f.write(f"Close (last):      {last_close:.2f}\n" if pd.notna(last_close) else "Close (last):      N/A\n")
                f.write(f"24h Variation:     {daily_var:+.2f}%\n" if pd.notna(daily_var) else "24h Variation:     N/A\n")
                f.write(f"Annual Volatility: {vol:.2%}\n" if pd.notna(vol) else "Annual Volatility: N/A\n")
                f.write(f"1Y Max Drawdown:   {max_dd:.2%}\n" if pd.notna(max_dd) else "1Y Max Drawdown:   N/A\n")
                f.write("\n")

                print(f"[OK] Processed {symbol}")

            except Exception as e:
                f.write(f"[!] Asset: {symbol} - Error: {str(e)}\n\n")
                print(f"[ERROR] {symbol}: {e}")

    print(f"Report saved to: {report_file}")
    return report_file


if __name__ == "__main__":
    generate_daily_report()
