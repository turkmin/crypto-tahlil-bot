import urllib.request
import json
import pandas as pd
import ta
import asyncio
from telegram import Bot

# --- SOZLAMALAR ---
TOKEN = '8807605095:AAFvyM9F3wBnroFr6y_is5Yr5ERcJUfQZQw'  # Maxfiy tokeningiz
CHAT_ID = '6261546654'  # Shaxsiy Telegram ID raqamingiz
SYMBOL = 'BTCUSDT'

def get_binance_data(symbol):
    """Binance API'dan grafik ma'lumotlarini to'g'ri URL orqali yuklash"""
    url = f"https://binance.com{symbol}&interval=15m&limit=300"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            return df
    except Exception as e:
        print(f"Binance ulanish xatosi: {e}")
        return None

def calculate_indicators(df):
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    macd_object = ta.trend.MACD(df['close'], window_fast=12, window_slow=26, window_sign=9)
    df['macd'] = macd_object.macd()
    df['macd_signal'] = macd_object.macd_signal()
    return df

async def send_auto_message(text):
    try:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='Markdown')
    except Exception as e:
        print(f"Telegram xatosi: {e}")

async def monitor_market():
    print("🤖 SERVERDA KRIPTO AVTOMATIK MONITORING ISHGA TUSHDI!")
    # Bot serverda yonganda sizga darhol xabar boradi:
    await send_auto_message("🤖 *Salom! Bot Render serverida muvaffaqiyatli ishga tushdi va 15 minutlik grafikda avtomatik signallarni kuzatishni boshladi!*")
    
    last_signal_time = None
    
    while True:
        df = get_binance_data(SYMBOL)
        if df is not None:
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            price = last_row['close']
            rsi = last_row['rsi']
            ema = last_row['ema200']
            candle_time = str(last_row['time'])
            
            long_tp, long_sl = price * 1.015, price * 0.994
            short_tp, short_sl = price * 0.985, price * 1.006

            is_long = (price > ema) and (rsi < 38) and (prev_row['macd'] < prev_row['macd_signal']) and (last_row['macd'] > last_row['macd_signal'])
            is_short = (price < ema) and (rsi > 62) and (prev_row['macd'] > prev_row['macd_signal']) and (last_row['macd'] < last_row['macd_signal'])

            print(f"🕒 Narx: ${price:.2f} | RSI: {rsi:.2f}")

            if (is_long or is_short) and (last_signal_time != candle_time):
                msg = f"🚀 *YANGI AVTOMATIK KRIPTO SIGNAL (Binance)!* 🚀\n\n"
                msg += f"💰 Narx: ${price:,.2f}\n📉 RSI: {rsi:.2f}\n\n"
                
                if is_long:
                    msg += "🟢 *YO'NALISH: LONG (SOTIB OLISH)* 🟢\n\n"
                    msg += f"🎯 Target (TP): ${long_tp:,.2f}\n🛑 Stop Loss (SL): ${long_sl:,.2f}\n"
                elif is_short:
                    msg += "🔴 *YO'NALISH: SHORT (SOTISH)* 🔴\n\n"
                    msg += f"🎯 Target (TP): ${short_tp:,.2f}\n🛑 Stop Loss (SL): ${short_sl:,.2f}\n"
                
                await send_auto_message(msg)
                last_signal_time = candle_time

        await asyncio.sleep(60) # Server har daqiqada tekshirib turadi

if __name__ == '__main__':
    asyncio.run(monitor_market())
