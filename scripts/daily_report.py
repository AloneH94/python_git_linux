import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# --- CONFIGURATION DES CHEMINS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
module_path = os.path.join(parent_dir, "QuantA_single_asset")
sys.path.append(module_path)

try:
    import single_asset_module as sam
    print("Module 'single_asset_module' imported successfully.")
except ImportError as e:
    print(f"Error importing module: {e}")
    print(f"Checked path: {module_path}")
    sys.exit(1)

# --- PARAMÈTRES ---
ASSETS = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "EURUSD=X", "GC=F"]  # <- Or (futures)
REPORT_DIR = os.path.join(parent_dir, "daily_reports")


def _annualized_vol(returns: pd.Series, periods_per_year: int = 252) -> float:
    if returns is None or returns.dropna().empty:
        return float("nan")
    return float(returns.dropna().std() * (periods_per_year ** 0.5))


def _max_drawdown(returns: pd.Series) -> float:
    if returns is None or returns.dropna().empty:
        return float("nan")
    cum = (1 + returns.dropna()).cumprod()
    running_max = cum.cummax()
    dd = (cum - running_max) / running_max
    return float(dd.min())


def generate_daily_report():
    """Génère un rapport txt avec les stats des actifs surveillés."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    report_file = os.path.join(REPORT_DIR, f"report_{today_str}.txt")

    # Période d'analyse (1 an glissant pour volatilité/drawdown)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    print(f"Generating report for {today_str}...")

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("==========================================\n")
        f.write("   DAILY QUANTITATIVE FINANCE REPORT\n")
        f.write(f"   Date: {today_str}\n")
        f.write("==========================================\n\n")

        for symbol in ASSETS:
            try:
                data = sam.fetch_financial_data(symbol, start_date, end_date)

                # Sécurité : données suffisantes
                if data is None or data.empty or len(data) < 2:
                    f.write(f"[!] Asset: {symbol} - Not enough data\n\n")
                    print(f"Not enough data for {symbol}")
                    continue

                # Colonnes attendues
                if "Close" not in data.columns:
                    f.write(f"[!] Asset: {symbol} - Missing 'Close' column\n\n")
                    print(f"Missing Close for {symbol}. Columns: {list(data.columns)}")
                    continue

                # Open/Close du dernier jour disponible
                last_close = float(data["Close"].iloc[-1])
                prev_close = float(data["Close"].iloc[-2])
                daily_var = ((last_close - prev_close) / prev_close) * 100.0

                last_open = float(data["Open"].iloc[-1]) if "Open" in data.columns else float("nan")

                # Returns daily sur 1 an
                returns = data["Close"].pct_change().dropna()

                vol = _annualized_vol(returns, periods_per_year=252)
                max_dd = _max_drawdown(returns)

                # Écriture du rapport
                f.write(f"Asset: {symbol}\n")
                f.write("----------------------------\n")
                f.write(f"Open (last):       {last_open:.2f}\n" if pd.notna(last_open) else "Open (last):       N/A\n")
                f.write(f"Close (last):      {last_close:.2f}\n")
                f.write(f"24h Variation:     {daily_var:+.2f}%\n")
                f.write(f"Annual Volatility: {vol:.2%}\n" if pd.notna(vol) else "Annual Volatility: N/A\n")
                f.write(f"1Y Max Drawdown:   {max_dd:.2%}\n" if pd.notna(max_dd) else "1Y Max Drawdown:   N/A\n")
                f.write("\n")

                print(f"Processed {symbol}")

            except Exception as e:
                f.write(f"[!] Asset: {symbol} - Error: {str(e)}\n\n")
                print(f"Error processing {symbol}: {e}")

    print(f"Report saved to: {report_file}")


if __name__ == "__main__":
    generate_daily_report()
