import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "bot.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            target_profit REAL DEFAULT 60.0,
            timezone TEXT DEFAULT 'UTC',
            theme TEXT DEFAULT 'dark'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            action TEXT,
            entry_price REAL,
            tp_price REAL,
            sl_price REAL,
            quantity REAL,
            status TEXT,
            pnl REAL DEFAULT 0.0,
            target_profit REAL,
            bybit_order_id TEXT,
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO settings (target_profit, timezone, theme) VALUES (?, ?, ?)', (60.0, 'UTC', 'dark'))
    conn.commit()
    conn.close()

def get_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM settings WHERE id = 1')
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_settings(target_profit, timezone, theme):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE settings 
        SET target_profit = ?, timezone = ?, theme = ? 
        WHERE id = 1
    ''', (target_profit, timezone, theme))
    conn.commit()
    conn.close()

def insert_trade(ticker, action, entry_price, tp_price, sl_price, quantity, status, target_profit, bybit_order_id=None, error_msg=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (ticker, action, entry_price, tp_price, sl_price, quantity, status, target_profit, bybit_order_id, error_msg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ticker, action, entry_price, tp_price, sl_price, quantity, status, target_profit, bybit_order_id, error_msg))
    trade_id = c.lastrowid
    conn.commit()
    conn.close()
    return trade_id

def get_trades():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM trades ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_open_trades():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM trades WHERE status = "open"')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_trade(trade_id, status=None, pnl=None, target_profit=None):
    conn = get_db_connection()
    c = conn.cursor()
    updates = []
    params = []
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if pnl is not None:
        updates.append("pnl = ?")
        params.append(pnl)
    if target_profit is not None:
        updates.append("target_profit = ?")
        params.append(target_profit)
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE trades SET {', '.join(updates)} WHERE id = ?"
        params.append(trade_id)
        c.execute(query, tuple(params))
        conn.commit()
    conn.close()
