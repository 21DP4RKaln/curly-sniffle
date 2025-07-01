import os
import sqlite3
import psycopg2
from datetime import datetime

def migrate_to_postgres():
    """Migrate SQLite data to PostgreSQL for Vercel"""
    
    # Database URLs
    sqlite_path = os.path.join(os.path.dirname(__file__), 'src', 'SVNbot.db')
    postgres_url = os.environ.get('DATABASE_URL')
    
    if not postgres_url:
        print("❌ DATABASE_URL environment variable not set")
        return
    
    if not os.path.exists(sqlite_path):
        print("❌ SQLite database not found, creating empty PostgreSQL schema")
        create_postgres_schema(postgres_url)
        return
    
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    postgres_conn = psycopg2.connect(postgres_url)
    
    try:
        # Create PostgreSQL schema
        create_postgres_schema_with_connection(postgres_conn)
        
        # Migrate users
        migrate_users(sqlite_conn, postgres_conn)
        
        # Migrate market_data
        migrate_market_data(sqlite_conn, postgres_conn)
        
        # Migrate trades
        migrate_trades(sqlite_conn, postgres_conn)
        
        postgres_conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_conn.rollback()
    finally:
        sqlite_conn.close()
        postgres_conn.close()

def create_postgres_schema(postgres_url):
    """Create PostgreSQL schema"""
    conn = psycopg2.connect(postgres_url)
    create_postgres_schema_with_connection(conn)
    conn.commit()
    conn.close()

def create_postgres_schema_with_connection(conn):
    """Create PostgreSQL schema with existing connection"""
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP,
            total_trades INTEGER DEFAULT 0,
            profit REAL DEFAULT 0.0
        )
    ''')
    
    # Market data table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            symbol TEXT,
            features TEXT,
            signal INTEGER,
            confidence REAL
        )
    ''')
    
    # Trades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            symbol TEXT,
            signal TEXT,
            profit REAL,
            confidence REAL
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_market_data_user_time ON market_data(user_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_time ON trades(user_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
    
    print("✅ PostgreSQL schema created")

def migrate_users(sqlite_conn, postgres_conn):
    """Migrate users table"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute('SELECT * FROM users')
        users = sqlite_cursor.fetchall()
        
        for user in users:
            postgres_cursor.execute('''
                INSERT INTO users (id, registration_date, last_activity, total_trades, profit)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    last_activity = EXCLUDED.last_activity,
                    total_trades = EXCLUDED.total_trades,
                    profit = EXCLUDED.profit
            ''', user)
        
        print(f"✅ Migrated {len(users)} users")
    except Exception as e:
        print(f"⚠️ Users migration skipped: {e}")

def migrate_market_data(sqlite_conn, postgres_conn):
    """Migrate market_data table"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute('SELECT timestamp, user_id, symbol, features, signal, confidence FROM market_data ORDER BY timestamp DESC LIMIT 1000')
        market_data = sqlite_cursor.fetchall()
        
        for data in market_data:
            postgres_cursor.execute('''
                INSERT INTO market_data (timestamp, user_id, symbol, features, signal, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', data)
        
        print(f"✅ Migrated {len(market_data)} market data records")
    except Exception as e:
        print(f"⚠️ Market data migration skipped: {e}")

def migrate_trades(sqlite_conn, postgres_conn):
    """Migrate trades table"""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        sqlite_cursor.execute('SELECT timestamp, user_id, symbol, signal, profit, confidence FROM trades ORDER BY timestamp DESC LIMIT 1000')
        trades = sqlite_cursor.fetchall()
        
        for trade in trades:
            postgres_cursor.execute('''
                INSERT INTO trades (timestamp, user_id, symbol, signal, profit, confidence)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', trade)
        
        print(f"✅ Migrated {len(trades)} trades")
    except Exception as e:
        print(f"⚠️ Trades migration skipped: {e}")

if __name__ == "__main__":
    migrate_to_postgres()
