import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import threading
from contextlib import contextmanager

class TransactionDB:
    def __init__(self, db_path: str = "data/transactions.db"):
        # Ensure the directory for the database exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
             
        self.db_path = db_path
        self._lock = threading.Lock() # For thread safety if ever needed
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
            
            # Do not drop existing tables if DB is persistent (Un-comment to drop)
            # cursor.execute('DROP TABLE IF EXISTS transactions')
            # cursor.execute('DROP TABLE IF EXISTS monthly_stats')
            
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_stats_user_date ON monthly_stats(user_id, year, month)')
            conn.commit()
    
    def _format_timestamp(self, timestamp) -> str:
        """Convert timestamp to ISO format string"""
        if isinstance(timestamp, pd.Timestamp):
            return timestamp.isoformat()
        elif isinstance(timestamp, datetime):
            return timestamp.isoformat()
        return str(timestamp)
    
    def _format_amount(self, amount) -> float:
        """Convert amount to float, handling NULL/NaN values by returning 0.0."""
        if pd.isna(amount) or amount is None or amount == '':
            return 0.0
        try:
            return float(amount)
        except (ValueError, TypeError):
            return 0.0 # Default to 0.0 if conversion fails
    
    def insert_transactions(self, transactions: List[Dict]):
        """Insert a batch of transactions into the database."""
        if not transactions:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            processed_data = []
            for t in transactions:
                # Ensure timestamp is a datetime object for year/month extraction
                dt_timestamp = pd.to_datetime(t['timestamp'])
                timestamp_str = self._format_timestamp(dt_timestamp)
                amount = self._format_amount(t.get('amount')) # Use .get for safety

                processed_data.append((
                    str(t['user_id']),
                    timestamp_str,
                    str(t['transaction_type']),
                    str(t['transaction_method']),
                    amount,
                    str(t['segment_tag']),
                    dt_timestamp.year,
                    dt_timestamp.month
                ))
            
            cursor.executemany('''
                INSERT INTO transactions 
                (user_id, timestamp, transaction_type, transaction_method, amount, segment_tag, year, month)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', processed_data)
            conn.commit()
    
    def get_monthly_profile(self, user_id: str, year: int, month: int) -> Dict:
        """Get monthly profile data for a user from the database."""
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
            
            # Get transaction methods and counts
            cursor.execute('''
                SELECT transaction_method, transaction_type, COUNT(*) as count, SUM(amount) as total_amount
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
                GROUP BY transaction_method, transaction_type
            ''', (user_id, year, month))
            methods_raw = cursor.fetchall()
            methods_summary = [
                {"method": row[0], "type": row[1], "count": row[2], "total_amount": row[3]}
                for row in methods_raw
            ]
            
            # Get distinct segments
            cursor.execute('''
                SELECT DISTINCT segment_tag
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
            ''', (user_id, year, month))
            segments = [row[0] for row in cursor.fetchall() if row[0]] # Filter out None/empty segments

            return {
                'total_spend': stats[0] if stats else 0,
                'spend_count': stats[1] if stats else 0,
                'total_cash_in': stats[2] if stats else 0,
                'cash_in_count': stats[3] if stats else 0,
                'methods_summary': methods_summary,
                'segments': list(set(segments)) # Ensure unique
            }
    
    def get_monthly_transactions(self, user_id: str, year: int, month: int) -> List[Dict]:
        """Get all transactions for a user in a specific month."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, transaction_type, transaction_method, amount, segment_tag
                FROM transactions
                WHERE user_id = ? AND year = ? AND month = ?
                ORDER BY timestamp
            ''', (user_id, year, month))
            
            return [{
                'timestamp': pd.to_datetime(row[0]), # Convert back to datetime
                'transaction_type': row[1],
                'transaction_method': row[2],
                'amount': row[3] if row[3] is not None else 0.0,
                'segment_tag': row[4]
            } for row in cursor.fetchall()]
            
    def get_active_users(self, start_date: datetime, end_date: datetime, min_transactions: int) -> List[Tuple[str, int, float, float]]:
        """Get active users within a date range based on transaction criteria."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                user_id,
                COUNT(*) as transaction_count,
                SUM(CASE WHEN transaction_type = 'SPEND' THEN amount ELSE 0 END) as total_spend,
                SUM(CASE WHEN transaction_type = 'CASH-IN' THEN amount ELSE 0 END) as total_cash_in
            FROM transactions
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY user_id
            HAVING transaction_count >= ?
            """
            
            cursor.execute(query, (start_date.isoformat(), end_date.isoformat(), min_transactions))
            return cursor.fetchall()
    
    def close(self):
        """Placeholder, as connections are managed by context manager"""
        pass 