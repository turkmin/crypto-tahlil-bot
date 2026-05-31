{TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            pass
    except Exception as e:
        print(f"Telegram xatosi: {e}")

def main():
    print("🚀 [START] TOP-100 MULTI-SKANER ISHGA TUSHDI!", flush=True)
    send_telegram_message("⚙️ *Skaner toza va original rejimda ishga tushdi!* Har 15 minutda faqat bitta to'liq aylanish bajariladi.")
    
    last_signal_times = {symbol: None for symbol in SYMBOLS}
    
    # 100 ta tangani bir marta to'liq tekshirish
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

            print(f"📊 [OK] -> {symbol} | Narx: ${price:.2f} | RSI: {rsi:.2f}", flush=True)

            long_tp, long_sl = price * 1.015, price * 0.994
            short_tp, short_sl = price * 0.985, price * 1.006

            is_long = (price > ema) and (rsi < 43) and (prev_row['macd'] < prev_row['macd_signal']) and (last_row['macd'] > last_row['macd_signal'])
            is_short = (price < ema) and (rsi > 57) and (prev_row['macd'] > prev_row['macd_signal']) and (last_row['macd'] < last_row['macd_signal'])

            if is_long:
                msg = f"🚀 *YANGI 10x SIGNALI!* 🚀\n\n🪙 *Tanga: {symbol}*\n🟢 *LONG (SOTIB OLISH)*\n💰 Narx: ${price:,.4f}\n🎯 TP: ${long_tp:,.4f} | 🛑 SL: ${long_sl:,.4f}"
                send_telegram_message(msg)
            elif is_short:
                msg = f"🚀 *YANGI 10x SIGNALI!* 🚀\n\n🪙 *Tanga: {symbol}*\n🔴 *SHORT (SOTISH)*\n💰 Narx: ${price:,.4f}\n🎯 TP: ${short_tp:,.4f} | 🛑 SL: ${short_sl:,.4f}"
                send_telegram_message(msg)
        
        time.sleep(0.1)
        
    print("✅ [FINISH] Skanerlash yakunlandi.", flush=True)

if __name__ == '__main__':
    main()
