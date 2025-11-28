import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION DES CHEMINS ---
# On récupère le chemin absolu du dossier courant (scripts)
current_dir = os.path.dirname(os.path.abspath(__file__))
# On remonte d'un cran pour avoir la racine du projet
parent_dir = os.path.dirname(current_dir)
# On construit le chemin vers le module 'QuantA_single_asset'
module_path = os.path.join(parent_dir, 'QuantA_single_asset')

# On ajoute ce chemin au système pour que Python puisse trouver notre module
sys.path.append(module_path)

try:
    import single_asset_module as sam
    print("Module 'single_asset_module' imported successfully.")
except ImportError as e:
    print(f"Error importing module: {e}")
    print(f"Checked path: {module_path}")
    sys.exit(1)

# --- PARAMÈTRES ---
ASSETS = ["AAPL", "MSFT", "GOOGL", "BTC-USD", "EURUSD=X"]
REPORT_DIR = os.path.join(parent_dir, 'daily_reports')

def generate_daily_report():
    """Génère un rapport txt avec les stats des actifs surveillés."""
    
    # Création du dossier de rapports s'il n'existe pas
    if not os.path.exists(REPORT_DIR):
        try:
            os.makedirs(REPORT_DIR)
        except OSError as e:
            print(f"Error creating directory {REPORT_DIR}: {e}")
            return

    today_str = datetime.now().strftime("%Y-%m-%d")
    report_file = os.path.join(REPORT_DIR, f"report_{today_str}.txt")
    
    # Période d'analyse (1 an glissant pour la volatilité/drawdown)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    print(f"Generating report for {today_str}...")

    with open(report_file, "w") as f:
        f.write(f"==========================================\n")
        f.write(f"   DAILY QUANTITATIVE FINANCE REPORT\n")
        f.write(f"   Date: {today_str}\n")
        f.write(f"==========================================\n\n")
        
        for symbol in ASSETS:
            try:
                # Récupération des données via le module Quant A
                data = sam.fetch_financial_data(symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    # Calcul des métriques basiques
                    last_price = data['Close'].iloc[-1]
                    prev_price = data['Close'].iloc[-2]
                    daily_var = ((last_price - prev_price) / prev_price) * 100
                    
                    # Volatilité (écart-type des rendements * racine(252))
                    volatility = data['Daily Return'].std() * (252**0.5)
                    
                    # Max Drawdown rapide
                    cum_ret = (1 + data['Daily Return']).cumprod()
                    running_max = cum_ret.expanding().max()
                    drawdown = (cum_ret - running_max) / running_max
                    max_dd = drawdown.min()

                    # Écriture dans le fichier
                    f.write(f"Asset: {symbol}\n")
                    f.write(f"----------------------------\n")
                    f.write(f"Close Price:      ${last_price:.2f}\n")
                    f.write(f"24h Variation:    {daily_var:+.2f}%\n")
                    f.write(f"Annual Volatility:{volatility:.2%}\n")
                    f.write(f"1Y Max Drawdown:  {max_dd:.2%}\n")
                    f.write(f"\n")
                    print(f"Processed {symbol}")
                else:
                    f.write(f"[!] Asset: {symbol} - No Data Available\n\n")
                    print(f"No data for {symbol}")
            except Exception as e:
                f.write(f"[!] Asset: {symbol} - Error: {str(e)}\n\n")
                print(f"Error processing {symbol}: {e}")

    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    generate_daily_report()
