#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sqlite3
import json
from datetime import datetime

def check_database():
    """Pārbauda un parāda datu bāzes saturu"""
    try:
        conn = sqlite3.connect('svnbot.db')
        cursor = conn.cursor()
        
        print("🔍 DATU BĀZES ANALĪZE - SVN Trading Bot")
        print("=" * 50)
        
        # Iegūst visas tabulas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 Datu bāzē ir {len(tables)} tabulas:")
        for table in tables:
            print(f"   • {table[0]}")
        
        print("\n" + "=" * 50)
        
        # Apskata katru tabulu
        for table in tables:
            table_name = table[0]
            print(f"\n📋 TABULA: {table_name.upper()}")
            print("-" * 30)
            
            # Iegūst tabulas struktūru
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("Kolumnas:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = "🔑" if col[5] else "  "
                nullable = "NULL" if not col[3] else "NOT NULL"
                print(f"   {is_pk} {col_name} ({col_type}) - {nullable}")
            
            # Iegūst ierakstu skaitu
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"\n📈 Ierakstu skaits: {count}")
            
            # Parāda dažus ierakstus, ja tie eksistē
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print("\n🔍 Piemēra dati (pirmie 3 ieraksti):")
                    for i, row in enumerate(rows, 1):
                        print(f"   {i}. {row}")
        
        conn.close()
        print(f"\n✅ Datu bāzes analīze pabeigta - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Kļūda: {e}")

if __name__ == "__main__":
    check_database()
