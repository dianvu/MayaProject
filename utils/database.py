import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
import threading
from contextlib import contextmanager
from itertools import combinations
import gc  # For garbage collection

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
    
    # Uncomment to get all transactions for a user in a specific month
    # def get_monthly_transactions(self, user_id: str, year: int, month: int) -> List[Dict]:
    #     """Get all transactions for a user in a specific month."""
    #     with self._get_connection() as conn:
    #         cursor = conn.cursor()
    #         cursor.execute('''
    #             SELECT timestamp, transaction_type, transaction_method, amount, segment_tag
    #             FROM transactions
    #             WHERE user_id = ? AND year = ? AND month = ?
    #             ORDER BY timestamp
    #         ''', (user_id, year, month))
            
    #         return [{
    #             'timestamp': pd.to_datetime(row[0]), # Convert back to datetime
    #             'transaction_type': row[1],
    #             'transaction_method': row[2],
    #             'amount': row[3] if row[3] is not None else 0.0,
    #             'segment_tag': row[4]
    #         } for row in cursor.fetchall()]
            
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

    def get_user_segment_stats(self) -> List[Dict]:
        """Get user statistics grouped by segment tags.
        
        Returns:
            List[Dict]: List of dictionaries containing segment statistics with the following keys:
                - segment_tag: The segment identifier
                - total_spend: Total amount spent by users in this segment
                - total_cash_in: Total cash-in amount for users in this segment
                - spend_count: Number of spend transactions in this segment
                - cash_in_count: Number of cash-in transactions in this segment
                - user_count: Number of unique users in this segment
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT 
                segment_tag,
                COUNT(DISTINCT user_id) as user_count,
                SUM(CASE WHEN transaction_type = 'SPEND' THEN amount ELSE 0 END) as total_spend,
                COUNT(CASE WHEN transaction_type = 'SPEND' THEN 1 END) as spend_count,
                SUM(CASE WHEN transaction_type = 'CASH-IN' THEN amount ELSE 0 END) as total_cash_in,
                COUNT(CASE WHEN transaction_type = 'CASH-IN' THEN 1 END) as cash_in_count
            FROM transactions
            GROUP BY segment_tag
            ORDER BY total_spend DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [{
                'segment_tag': row[0],
                'user_count': row[1],
                'total_spend': row[2],
                'spend_count': row[3],
                'total_cash_in': row[4],
                'cash_in_count': row[5]
            } for row in results]

    def export_user_segment_stats_to_csv(self, output_dir: str = "data/segment_stats", max_combinations: int = 100):
        """Export user statistics grouped by combined segments and time periods to CSV files.
        
        Args:
            output_dir (str): Directory where CSV files will be saved. Defaults to "data/segment_stats".
            max_combinations (int): Maximum number of segment combinations to process. Defaults to 100.
        
        This method will:
        1. Get all unique segment combinations
        2. For each combination, get user statistics grouped by month and year
        3. Export each combination's data to a separate CSV file
        """
        import os
        import pandas as pd
        from itertools import combinations
        import gc  # For garbage collection

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get all unique segments
                print("Fetching unique segments...")
                cursor.execute("SELECT DISTINCT segment_tag FROM transactions")
                all_segments = [row[0] for row in cursor.fetchall()]
                print(f"Found {len(all_segments)} unique segments")
                
                # Generate combinations one at a time to save memory
                combination_count = 0
                for r in range(1, 4):  # Combinations of 1, 2, or 3 segments
                    if combination_count >= max_combinations:
                        break
                        
                    for segments in combinations(all_segments, r):
                        if combination_count >= max_combinations:
                            break
                            
                        try:
                            # Create a safe filename from segments
                            filename = "_".join(segments).replace(" ", "_").lower()
                            
                            # Query to get user statistics for this combination of segments, grouped by month and year
                            placeholders = ", ".join(["?"] * len(segments))
                            query = f"""
                            WITH user_segments AS (
                                SELECT user_id, COUNT(DISTINCT segment_tag) as segment_count
                                FROM transactions
                                WHERE segment_tag IN ({placeholders})
                                GROUP BY user_id
                                HAVING segment_count = {len(segments)}
                            )
                            SELECT 
                                t.user_id,
                                t.year,
                                t.month,
                                COUNT(DISTINCT CASE WHEN t.transaction_type = 'SPEND' THEN t.id END) as spend_count,
                                COUNT(DISTINCT CASE WHEN t.transaction_type = 'CASH-IN' THEN t.id END) as cash_in_count,
                                SUM(CASE WHEN t.transaction_type = 'SPEND' THEN t.amount ELSE 0 END) as total_spend,
                                SUM(CASE WHEN t.transaction_type = 'CASH-IN' THEN t.amount ELSE 0 END) as total_cash_in,
                                GROUP_CONCAT(DISTINCT t.segment_tag) as segments
                            FROM transactions t
                            INNER JOIN user_segments us ON t.user_id = us.user_id
                            GROUP BY t.user_id, t.year, t.month
                            ORDER BY t.year DESC, t.month DESC, total_spend DESC
                            """
                            
                            print(f"Processing combination {combination_count + 1}: {segments}")
                            cursor.execute(query, segments)
                            results = cursor.fetchall()
                            
                            if results:  # Only create file if there are results
                                # Convert to DataFrame
                                df = pd.DataFrame(results, columns=[
                                    'user_id', 'year', 'month',
                                    'spend_count', 'cash_in_count',
                                    'total_spend', 'total_cash_in', 'segments'
                                ])
                                
                                # Add a month_year column for easier filtering
                                df['month_year'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
                                
                                # Export to CSV
                                output_path = os.path.join(output_dir, f"{filename}.csv")
                                df.to_csv(output_path, index=False)
                                print(f"Exported {len(df)} user-month records with segments {segments} to {output_path}")
                                
                                # Print summary statistics
                                print(f"Time period: {df['month_year'].min().strftime('%Y-%m')} to {df['month_year'].max().strftime('%Y-%m')}")
                                print(f"Total unique users: {df['user_id'].nunique()}")
                                print(f"Total months: {df['month_year'].nunique()}")
                            
                            # Clean up memory
                            del df
                            gc.collect()
                            
                        except Exception as e:
                            print(f"Error processing combination {segments}: {str(e)}")
                            continue
                            
                        combination_count += 1
                        
                print(f"Completed processing {combination_count} combinations")
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

    def export_all_user_monthly_stats(self, output_file: str = "data/user_monthly_stats.csv"):
        """Export all user monthly statistics to a single CSV file.
        
        Args:
            output_file (str): Path to the output CSV file. Defaults to "data/user_monthly_stats.csv".
            
        The CSV will contain:
        - user_id: The user identifier
        - year: The year of the transactions
        - month: The month of the transactions
        - spend_count: Number of spend transactions for that user in that month
        - cash_in_count: Number of cash-in transactions for that user in that month
        - total_spend: Total amount spent by that user in that month
        - total_cash_in: Total cash-in amount for that user in that month
        - segments: List of segments the user belongs to
        - month_year: A datetime column for easier time-based filtering
        """
        import os
        import pandas as pd

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                print("Fetching user monthly statistics...")
                query = """
                SELECT 
                    t.user_id,
                    t.year,
                    t.month,
                    COUNT(DISTINCT CASE WHEN t.transaction_type = 'SPEND' THEN t.id END) as spend_count,
                    COUNT(DISTINCT CASE WHEN t.transaction_type = 'CASH-IN' THEN t.id END) as cash_in_count,
                    SUM(CASE WHEN t.transaction_type = 'SPEND' THEN t.amount ELSE 0 END) as total_spend,
                    SUM(CASE WHEN t.transaction_type = 'CASH-IN' THEN t.amount ELSE 0 END) as total_cash_in,
                    GROUP_CONCAT(DISTINCT t.segment_tag) as segments
                FROM transactions t
                GROUP BY t.user_id, t.year, t.month
                ORDER BY t.year DESC, t.month DESC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                if results:
                    # Convert to DataFrame
                    df = pd.DataFrame(results, columns=[
                        'user_id', 'year', 'month',
                        'spend_count', 'cash_in_count',
                        'total_spend', 'total_cash_in', 'segments'
                    ])
                    
                    # Export to CSV
                    df.to_csv(output_file, index=False)
                    
                    # Print summary statistics
                    print(f"\nExported {len(df)} user-month records to {output_file}")
                    print(f"Time period: {df['month_year'].min().strftime('%Y-%m')} to {df['month_year'].max().strftime('%Y-%m')}")
                    print(f"Total unique users: {df['user_id'].nunique()}")
                    print(f"Total months: {df['month_year'].nunique()}")
                    print(f"Total segments: {df['segments'].str.split(',').explode().nunique()}")
                else:
                    print("No data found to export")
                    
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        db = TransactionDB()
        db.export_all_user_monthly_stats()
    except Exception as e:
        print(f"Error in main: {str(e)}")