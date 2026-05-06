import ccxt
import pandas as pd
import time
import requests
import os

# ── Configuration ──────────────────────────────────────────
API_KEY         = os.environ.get("mx0vglogZAGbVjItgH")
API_SECRET      = os.environ.get("4867bb0fef1b43dd899c263ea2b7d3fc")
TELEGRAM_TOKEN  = os.environ.get("8337123676:AAFYZgPDg4GydXLjMX4mD0kuhiHVDn_Z68U")
TELEGRAM_CHAT_ID = "1099582491"

SYMBOL     = "BTC/USDT"
TIMEFRAME  = "1h"
MA_COURT   = 9
MA_LONG    = 21
MONTANT    = 10
STOP_LOSS  = 0.03

# ── Connexion MEXC ─────────────────────────────────────────
exchange = ccxt.mexc({
    "apiKey": API_KEY,
    "secret": API_SECRET,
})

def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

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
    envoyer_telegram("🤖 Bot de trading démarré ! En attente de signaux...")
    position = False
    prix_achat = None

    while True:
        try:
            signal = get_signal()
            prix   = exchange.fetch_ticker(SYMBOL)["last"]
            print(f"Signal : {signal} | Prix BTC : {prix} USDT")

            if position and prix_achat:
                perte = (prix - prix_achat) / prix_achat
                if perte <= -STOP_LOSS:
                    solde = exchange.fetch_balance()["BTC"]["free"]
                    exchange.create_market_sell_order(SYMBOL, solde)
                    msg = f"🛑 STOP-LOSS déclenché !\nVente à {prix} USDT\nPerte : {perte*100:.1f}%"
                    print(msg)
                    envoyer_telegram(msg)
                    position = False
                    prix_achat = None

            if signal == "ACHETER" and not position:
                quantite = MONTANT / prix
                exchange.create_market_buy_order(SYMBOL, quantite)
                msg = f"✅ ACHAT exécuté !\n{quantite:.6f} BTC à {prix} USDT"
                print(msg)
                envoyer_telegram(msg)
                prix_achat = prix
                position = True

            elif signal == "VENDRE" and position:
                solde = exchange.fetch_balance()["BTC"]["free"]
                exchange.create_market_sell_order(SYMBOL, solde)
                pnl = (prix - prix_achat) / prix_achat * 100
                msg = f"💰 VENTE exécutée !\n{solde:.6f} BTC à {prix} USDT\nPerformance : {pnl:.1f}%"
                print(msg)
                envoyer_telegram(msg)
                position = False
                prix_achat = None

        except Exception as e:
            print(f"⚠️ Erreur : {e}")

        time.sleep(3600)

run()
