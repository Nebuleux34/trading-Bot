import ccxt
import pandas as pd
import time

# ── Configuration ──────────────────────────────────────────
API_KEY    = "mx0vgllQs1umrvFfYK"
API_SECRET = "207e7bd0f75040bdb8f7c11abc9cf7ab"

SYMBOL     = "BTC/USDT"
TIMEFRAME  = "1h"
MA_COURT   = 9
MA_LONG    = 21
MONTANT    = 10  # euros investis par trade
STOP_LOSS  = 0.03  # 3% de perte maximum

# ── Connexion MEXC ─────────────────────────────────────────
exchange = ccxt.mexc({
    "apiKey": API_KEY,
    "secret": API_SECRET,
})

def get_signal():
    bougies = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=50)
    df = pd.DataFrame(bougies, columns=["timestamp","open","high","low","close","volume"])
    df["ma_court"] = df["close"].rolling(MA_COURT).mean()
    df["ma_long"]  = df["close"].rolling(MA_LONG).mean()

    avant  = df.iloc[-2]
    actuel = df.iloc[-1]

    if avant["ma_court"] < avant["ma_long"] and actuel["ma_court"] > actuel["ma_long"]:
        return "ACHETER"
    elif avant["ma_court"] > avant["ma_long"] and actuel["ma_court"] < actuel["ma_long"]:
        return "VENDRE"
    return "ATTENDRE"

def run():
    print("Bot démarré. En attente de signaux...")
    position = False
    prix_achat = None

    while True:
        try:
            signal = get_signal()
            prix   = exchange.fetch_ticker(SYMBOL)["last"]
            print(f"Signal : {signal} | Prix BTC : {prix} USDT")

            # Stop-loss
            if position and prix_achat:
                perte = (prix - prix_achat) / prix_achat
                if perte <= -STOP_LOSS:
                    solde = exchange.fetch_balance()["BTC"]["free"]
                    exchange.create_market_sell_order(SYMBOL, solde)
                    print(f"🛑 STOP-LOSS déclenché : vente à {prix} USDT (perte: {perte*100:.1f}%)")
                    position = False
                    prix_achat = None

            if signal == "ACHETER" and not position:
                quantite = MONTANT / prix
                exchange.create_market_buy_order(SYMBOL, quantite)
                prix_achat = prix
                print(f"✅ ACHAT exécuté : {quantite:.6f} BTC à {prix} USDT")
                position = True

            elif signal == "VENDRE" and position:
                solde = exchange.fetch_balance()["BTC"]["free"]
                exchange.create_market_sell_order(SYMBOL, solde)
                print(f"✅ VENTE exécutée : {solde:.6f} BTC à {prix} USDT")
                position = False
                prix_achat = None

        except Exception as e:
            print(f"⚠️ Erreur : {e}")

        time.sleep(3600)

run()
