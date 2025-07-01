#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime, timedelta
import random

def add_test_data():
    """Pievieno testa datus datu bāzei"""
    try:
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        print("🚀 PIEVIENOJAM TESTA DATUS")
        print("=" * 40)
        
        # Pievieno testa lietotāju
        test_user_id = "sitvain12@gmail.com"
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, registration_date, last_activity, total_trades, profit)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_user_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            15,  # kopējais tirdzniecību skaits
            1250.75  # kopējais peļņa EUR
        ))
        print(f"✅ Pievienots lietotājs: {test_user_id}")
        
        # Pievieno testa tirdzniecības
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
        signals = ['BUY', 'SELL']
        
        print("\n📊 Pievienojam testa tirdzniecības...")
        for i in range(10):
            timestamp = (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            symbol = random.choice(symbols)
            signal = random.choice(signals)
            profit = round(random.uniform(-50, 150), 2)  # EUR
            confidence = round(random.uniform(60, 95), 2)  # %
            
            cursor.execute("""
                INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, test_user_id, symbol, signal, profit, confidence))
            
            print(f"   {i+1}. {symbol} {signal} - {profit}€ (Confidence: {confidence}%)")
        
        # Pievieno tirgus datus
        print("\n📈 Pievienojam tirgus datus...")
        for i in range(5):
            timestamp = (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
            symbol = random.choice(symbols)
            
            # Ģenerē features JSON
            features = {
                "price": round(random.uniform(1.0, 1.5), 5),
                "volume": random.randint(1000, 10000),
                "rsi": round(random.uniform(30, 70), 2),
                "macd": round(random.uniform(-0.01, 0.01), 4),
                "bollinger_upper": round(random.uniform(1.1, 1.4), 5),
                "bollinger_lower": round(random.uniform(1.0, 1.3), 5)
            }
            
            signal = random.choice([0, 1, 2])  # 0=HOLD, 1=BUY, 2=SELL
            confidence = round(random.uniform(60, 90), 2)
            
            cursor.execute("""
                INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, test_user_id, symbol, json.dumps(features), signal, confidence))
            
            signal_text = ['HOLD', 'BUY', 'SELL'][signal]
            print(f"   {i+1}. {symbol} - {signal_text} (Confidence: {confidence}%)")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Testa dati veiksmīgi pievienoti - {datetime.now().strftime('%H:%M:%S')}")
        print("\n🔍 Tagad palaidiet: python check_db.py lai apskatītu datus!")
        
    except Exception as e:
        print(f"❌ Kļūda: {e}")

if __name__ == "__main__":
    add_test_data()
