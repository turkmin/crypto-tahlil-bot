import urllib.request
import json
import pandas as pd
import ta
import time
from telegram import Bot
from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "100 Tanga Skaneri Jonli Oqimda!"

# --- SOZLAMALAR ---
TOKEN = '8807605095:AAFvyM9F3wBnroFr6y_is5Yr5ERcJUfQZQw'
CHAT_ID = '5798244980'

SYMBOLS = [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'DOGEUSDT', 'LINKUSDT',
    'MATICUSDT', 'SHIBUSDT', 'LTCUSDT', 'TRXUSDT', 'NEARUSDT', 'FILUSDT', 'UNIUSDT', 'ATOMUSDT', 'OPUSDT', 'APTUSDT',
    'ARBUSDT', 'INJUSDT', 'TIAUSDT', 'SUIUSDT', 'SEIUSDT', 'ORDIUSDT', 'ICPUSDT', 'IMXUSDT', 'STXUSDT', 'RNDRUSDT',
    'EGLDUSDT', 'THETAUSDT', 'FETUSDT', 'AGIXUSDT', 'GRTUSDT', 'FTMUSDT', 'GALAUSDT', 'BEAMUSDT', 'SANDUSDT', 'MANAUSDT',
    'APEUSDT', 'AXSUSDT', 'AAVEUSDT', 'MKRUSDT', 'COMPUSDT', 'CRVUSDT', 'SUSHIUSDT', 'DYDXUSDT', 'RUNEUSDT', 'LDOUSDT',
    'PENDLEUSDT', 'ENSUSDT', 'WOOUSDT', 'JUPUSDT', 'PYTHUSDT', 'WIFUSDT', 'BONKUSDT', 'PEPEUSDT', 'FLOKIUSDT', 'MEMEUSDT',
    'ALTUSDT', 'MANTAUSDT', 'XAIUSDT', 'AIUSDT', 'NFPUSDT', 'JTOUSDT', 'ACEUSDT', 'STRKUSDT', 'PORTALUSDT', 'AXLUSDT',
    'METISUSDT', 'RONINUSDT', 'DYMUSDT', 'OMUSDT', 'CFXUSDT', 'MINAUSDT', 'FLOWUSDT', 'CHZUSDT', 'ONEUSDT', 'ZILUSDT',
    'ENJUSDT', 'HOTUSDT', 'ANKRUSDT', 'IOTAUSDT', 'KAVAUSDT', 'ZRXUSDT', 'BATUSDT', 'OMGUSDT', 'WAVESUSDT', 'ONTUSDT',
    'QTUMUSDT', 'ICXUSDT', 'LSKUSDT', 'IOSTUSDT', 'SCUSDT', 'RVNUSDT', 'DGBUSDT', 'ALGOUSDT', 'XTZUSDT', 'HBARUSDT'
]

def get_binance_data(symbol):
    url = f"https://binance.com{symbol}&interval=15m&limit=300"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode())
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            return df
    except Exception:
        return None

def calculate_indicators(df):
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    macd_object = ta.trend.MACD(df['close'], window_fast=12, window_slow=26, window_sign=9)
    df['macd'] = macd_object.macd()
    df['macd_signal'] = macd_object.macd_signal()
    return df

def send_telegram_message(text):
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            pass
    except Exception as e:
        print(f"Telegram xatosi: {e}")

def monitor_market():
    # Bu yozuv endi aniq chiqadi, chunki bu ketma-ket oqimda
    print("🚀 [START] JONLI MULTI-SKANER SISTEMASI SINKRON REJIMDA ISHGA TUSHDI! 🚀", flush=True)
    send_telegram_message("⚙️ *TOP-100 Skaner ketma-ket (Sinxron) monitoring rejimiga o'tkazildi!* Endi barcha loglar Render oynasida to'g'ridan-to'g'ri ko'rinadi.")
    
    last_signal_times = {symbol: None for symbol in SYMBOLS}
    
    while True:
        for symbol in SYMBOLS:
            df = get_binance_data(symbol)
            if df is not None and len(df) >= 200:
                df = calculate_indicators(df)
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2]
                
                price = last_row['close']
                rsi = last_row['rsi']
                ema = last_row['ema200']
                candle_time = str(last_row['time'])
                
                if pd.isna(rsi) or pd.isna(ema):
                    continue

                # ASOSIY O'ZGARISH: Har bir tekshirilgan parani shart bajarilishidan qat'i nazar Render logiga chiqaramiz
                print(f"📊 [PROCESSED] -> {symbol} | Narx: ${price:.4f} | RSI: {rsi:.2f}", flush=True)

                long_tp, long_sl = price * 1.015, price * 0.994
                short_tp, short_sl = price * 0.985, price * 1.006

                is_long = (price > ema) and (rsi < 43) and (prev_row['macd'] < prev_row['macd_signal']) and (last_row['macd'] > last_row['macd_signal'])
                is_short = (price < ema) and (rsi > 57) and (prev_row['macd'] > prev_row['macd_signal']) and (last_row['macd'] < last_row['macd_signal'])

                if (is_long or is_short) and (last_signal_times.get(symbol) != candle_time):
                    msg = f"🚀 *YANGI 10x FYUCHES SIGNALI!* 🚀\n\n"
                    msg += f"🪙 *Tanga: {symbol}*\n"
                    msg += f"⚙️ *Leverage: 10x*\n"
                    msg += f"💰 Kirish narxi: ${price:,.4f}\n📉 RSI: {rsi:.2f}\n\n"
                    
                    if is_long:
                        msg += "🟢 *YO'NALISH: LONG (SOTIB OLISH)* 🟢\n\n"
                        msg += f"🎯 Target (TP +15%): ${long_tp:,.4f}\n🛑 Stop Loss (SL -6%): ${long_sl:,.4f}\n"
                    elif is_short:
                        msg += "🔴 *YO'NALISH: SHORT (SOTISH)* 🔴\n\n"
                        msg += f"🎯 Target (TP +15%): ${short_tp:,.2f}\n🛑 Stop Loss (SL -6%): ${short_sl:,.2f}\n"
                    
                    msg += f"\n📊 *Risk va Foyda:* Siz yutqazsangiz $12, yutsangiz $30 olasiz ($200 balans bilan)."
                    send_telegram_message(msg)
                    last_signal_times[symbol] = candle_time
            
            # Binance serverlarini yuklamaslik uchun kichik tanaffus
            time.sleep(0.2)
            
        print("--- 🔄 100 TA TANGA TO'LIQ SKANERLANDI. KEYINGI AYLANISH ---", flush=True)
        time.sleep(30)

if __name__ == '__main__':
    # Monitoringni alohida oddiy Thread qilib, Flask'ni parallel qoldiramiz, printlar endi bir-birini to'smaydi
    t = threading.Thread(target=monitor_market)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=10000)
