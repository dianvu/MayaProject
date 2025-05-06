import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import threading
from contextlib import contextmanager

class TransactionDB:
    def __init__(self, db_path: str = "transactions.db"):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._create_tables()
        self._create_indexes()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, timeout=30)  # 30 second timeout
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing tables if they exist
            cursor.execute('DROP TABLE IF EXISTS transactions')
            cursor.execute('DROP TABLE IF EXISTS monthly_stats')
            
            # Create transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    transaction_method TEXT NOT NULL,
                    amount REAL DEFAULT 0,
                    segment_tag TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL
                )
            ''')
            
            # Create monthly_stats table for caching aggregated data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_stats (
                    user_id TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    total_spend REAL NOT NULL DEFAULT 0,
                    spend_count INTEGER NOT NULL DEFAULT 0,
                    total_cash_in REAL NOT NULL DEFAULT 0,
                    cash_in_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, year, month)
                )
            ''')
            
            conn.commit()
    
    def _create_indexes(self):
        """Create indexes for faster queries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Indexes for transactions table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(year, month)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, year, month)')
            
            conn.commit()
    
    def _format_timestamp(self, timestamp) -> str:
        """Convert timestamp to ISO format string"""
        if isinstance(timestamp, pd.Timestamp):
            return timestamp.isoformat()
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        return str(timestamp)
    
    def _format_amount(self, amount) -> float:
        """Convert amount to float, handling NULL values"""
        if pd.isna(amount) or amount is None or amount == '':
            return 0.0
        try:
            return float(amount)
        except (ValueError, TypeError):
            return 0.0
    
    def insert_transactions(self, transactions: List[Dict]):
        """Insert transactions into the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for t in transactions:
                # Convert timestamp to ISO format string
                timestamp_str = self._format_timestamp(t['timestamp'])
                # Handle amount conversion
                amount = self._format_amount(t['amount'])
                
                cursor.execute('''
                    INSERT INTO transactions 
                    (user_id, timestamp, transaction_type, transaction_method, amount, segment_tag, year, month)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(t['user_id']),
                    timestamp_str,
                    str(t['transaction_type']),
                    str(t['transaction_method']),
                    amount,
                    str(t['segment_tag']),
                    t['timestamp'].year,
                    t['timestamp'].month
                ))
            
            conn.commit()
    
    def get_monthly_profile(self, user_id: str, year: int, month: int) -> Dict:
        """Get monthly profile data for a user"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(CASE WHEN transaction_type = 'SPEND' THEN amount ELSE 0 END), 0) as total_spend,
                    COUNT(CASE WHEN transaction_type = 'SPEND' THEN 1 END) as spend_count,
                    COALESCE(SUM(CASE WHEN transaction_type = 'CASH-IN' THEN amount ELSE 0 END), 0) as total_cash_in,
                    COUNT(CASE WHEN transaction_type = 'CASH-IN' THEN 1 END) as cash_in_count
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
            ''', (user_id, year, month))
            
            stats = cursor.fetchone()
            
            # Get transaction methods
            cursor.execute('''
                SELECT transaction_method, transaction_type, COUNT(*) as count
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
                GROUP BY transaction_method, transaction_type
            ''', (user_id, year, month))
            
            methods = cursor.fetchall()
            
            # Get segments
            cursor.execute('''
                SELECT DISTINCT segment_tag
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
            ''', (user_id, year, month))
            
            segments = [row[0] for row in cursor.fetchall()]
            
            return {
                'total_spend': stats[0] or 0,
                'spend_count': stats[1] or 0,
                'total_cash_in': stats[2] or 0,
                'cash_in_count': stats[3] or 0,
                'methods': methods,
                'segments': segments
            }
    
    def get_monthly_transactions(self, user_id: str, year: int, month: int) -> List[Dict]:
        """Get all transactions for a user in a specific month"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, transaction_type, transaction_method, amount, segment_tag
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
                ORDER BY timestamp
            ''', (user_id, year, month))
            
            return [{
                'timestamp': pd.to_datetime(row[0]),
                'transaction_type': row[1],
                'transaction_method': row[2],
                'amount': row[3] if row[3] is not None else 0.0,
                'segment_tag': row[4]
            } for row in cursor.fetchall()]
    
    def close(self):
        """Close the database connection"""
        # No need to close anything since we're using context managers
        pass 