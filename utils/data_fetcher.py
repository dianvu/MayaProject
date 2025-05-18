from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
from datetime import datetime
import calendar
from utils.database import TransactionDB
import os

class Transaction(BaseModel): # Pydantic model used for validation
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    transaction_type: str
    transaction_method: str
    amount: Optional[float] = None
    segment_tag: str
    
    def is_spend(self) -> bool:
        return self.transaction_type == "SPEND"
    
    def is_cash_in(self) -> bool:
        return self.transaction_type == "CASH-IN"

class DataFetcher:
    def __init__(self, processed_csv_path: str, db_path: str = "data/transactions.db", force_db_reload: bool = False):
        """
        Initialize DataFetcher.
        Args:
            processed_csv_path: Path to the processed CSV file.
            db_name: Directory to the SQLite database file.
            force_db_reload: If True, clears existing transactions and reloads from CSV.
        """
        self.processed_csv_path = processed_csv_path
        self.db_path = db_path
        self.db = TransactionDB(self.db_path)
        
        if force_db_reload:
            print("Forcing database reload: Clearing existing transactions.")
            self.db.clear_transactions() # Clear DB before loading
        
        self.user_ids = self._load_all_user_ids_from_db()
        
        # # Load CSV data into database
        # self._load_csv_to_db()

    def _load_csv_to_db(self):
        """Loads data from the processed CSV file into the database."""
        if not os.path.exists(self.processed_csv_path):
            print(f"Error: Processed CSV file not found at {self.processed_csv_path}")
            raise FileNotFoundError(f"Processed CSV file not found at {self.processed_csv_path}")

        try:
            data_df = pd.read_csv(self.processed_csv_path)
            data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])
            data_df['amount'] = pd.to_numeric(data_df['amount'], errors='coerce').fillna(0.0)
            
            # Convert DataFrame to list of dictionaries for insertion
            transactions_to_insert = []
            for _, row in data_df.iterrows():
                try:
                    # Basic validation or transformation if needed
                    transaction_dict = {
                        'user_id': str(row['user_id']),
                        'timestamp': row['timestamp'], # Datetime object
                        'transaction_type': str(row['transaction_type']),
                        'transaction_method': str(row['transaction_method']),
                        'amount': float(row['amount']),
                        'segment_tag': str(row['segment_tag'])
                    }
                    transactions_to_insert.append(transaction_dict)
                except Exception as e:
                    print(f"Skipping row due to error during transformation: {row} - Error: {e}")
                    continue
            
            if transactions_to_insert:
                self.db.insert_transactions(transactions_to_insert)
                print(f"Successfully loaded {len(transactions_to_insert)} transactions into the database.")
            else:
                print("No transactions found in CSV to load.")

        except Exception as e:
            print(f"Error loading CSV data to database: {e}")
            raise

    def _load_all_user_ids_from_db(self) -> set:
        """Loads all unique user IDs from the transactions table."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT user_id FROM transactions")
            return {row[0] for row in cursor.fetchall()}

    def _month_start_date(self, year: int, month: int) -> datetime:
        return datetime(year, month, 1)

    def _month_end_date(self, year: int, month: int) -> datetime:
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day, 23, 59, 59)
        
    def _format_tag(self, tag: str) -> str:
        """Convert a tag from UPPER_CASE_WITH_UNDERSCORES to 'lowercase with spaces'."""
        return tag.lower().replace('_', ' ') if isinstance(tag, str) else "unknown"

    def monthly_profile(self, year: int, month: int, user_id: str) -> str:
        """
        Generate a concise text-based monthly profile for a user using data from the database.
        """
        if user_id not in self.user_ids:
            return f"Error: User ID {user_id} not found in the database."
        if not (1 <= month <= 12):
             return "Error: Invalid month, must be from 1 to 12."

        profile_data = self.db.get_monthly_profile(user_id, year, month)
        raw_transactions = self.db.get_monthly_transactions(user_id, year, month)

        if profile_data['spend_count'] == 0 and profile_data['cash_in_count'] == 0:
            return f"User {user_id} ({year}-{month:02d})\nNo transaction data found for this period."

        # Format segments
        formatted_segments = [self._format_tag(tag) for tag in profile_data.get('segments', [])]
        
        profile_lines = [
            f"User {user_id} monthly transactions Summary (Timestamp: {year}-{month:02d})",
            f"- Total spend is {profile_data['total_spend']:.2f} with {profile_data['spend_count']} transactions",
        ]
        
        # Spending methods summary
        spend_methods_summary = []
        for item in profile_data.get('methods_summary', []):
            if item['type'] == 'SPEND' and profile_data['total_spend'] > 0:
                percentage = (item['total_amount'] / profile_data['total_spend']) * 100
                spend_methods_summary.append(f"{item['method'].lower()} with {percentage:.2f}%")
        if spend_methods_summary:
             profile_lines.append(f"- Spending methods include {', '.join(spend_methods_summary)}")
        else:
            profile_lines.append("- No spending methods recorded or zero total spend.")

        profile_lines.append(f"- Total cash-in is {profile_data['total_cash_in']:.2f} with {profile_data['cash_in_count']} transactions")

        # Cash-in methods summary
        cash_in_methods_summary = []
        for item in profile_data.get('methods_summary', []):
            if item['type'] == 'CASH-IN' and profile_data['total_cash_in'] > 0:
                percentage = (item['total_amount'] / profile_data['total_cash_in']) * 100
                cash_in_methods_summary.append(f"{item['method'].lower()} with {percentage:.2f}%")
        if cash_in_methods_summary:
            profile_lines.append(f"- Cash-in methods include {', '.join(cash_in_methods_summary)}")
        else:
            profile_lines.append("- No cash-in methods recorded or zero total cash-in.")

        if formatted_segments:
            profile_lines.append(f"- User tags: {', '.join(formatted_segments)}")
        else:
            profile_lines.append("- User tags: Not available")
            
        # Detailed transactions (would be large if the users having lots of transaction)
        # spend_transactions = [t for t in raw_transactions if t['transaction_type'] == "SPEND"]
        # cash_in_transactions = [t for t in raw_transactions if t['transaction_type'] == "CASH-IN"]
        
        # profile_lines.append("Detailed transactions:")
        # if spend_transactions:
        #     spend_amounts = [f"{t['amount']:.2f}" for t in sorted(spend_transactions, key=lambda x: x['timestamp'])]
        #     profile_lines.append(f"Spend: {', '.join(spend_amounts)}")
        
        # if cash_in_transactions:
        #     cash_in_amounts = [f"{t['amount']:.2f}" for t in sorted(cash_in_transactions, key=lambda x: x['timestamp'])]
        #     profile_lines.append(f"Cash-in: {', '.join(cash_in_amounts)}")
        
        # # Add spend/cash-in ratio if applicable
        # if profile_data['total_cash_in'] > 0:
        #     ratio = profile_data['total_spend'] / profile_data['total_cash_in']
        #     profile_lines.append(f"- Spend/Cash-in ratio: {ratio:.2%}")
        
        return "\n".join(profile_lines)

    def active_users(self, year: int, month: int, min_transactions: int = 3,
                    max_users: int = 1000, min_spend: float = 0, min_cash_in: float = 0) -> List[str]:
        """
        Get a list of active users for a specific month based on multiple criteria.
        
        Args:
            year: The year to filter transactions
            month: The month to filter transactions (1-12)
            min_transactions: Minimum number of transactions required to be considered active
            max_users: Maximum number of users to return
            min_spend: Minimum total spend amount required
            min_cash_in: Minimum total cash-in amount required
            
        Returns:
            List of user IDs that meet the criteria
        """
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")
            
        start_date = self._month_start_date(year, month)
        end_date = self._month_end_date(year, month)
        
        # Get active users from database
        results = self.db.get_active_users(start_date, end_date, min_transactions)
        
        # Filter users based on spend and cash-in criteria
        filtered_users = []
        for user_id, count, spend, cash_in in results:
            if spend >= min_spend and cash_in >= min_cash_in:
                filtered_users.append((user_id, count))
        
        # Sort by transaction count (descending) and limit to max_users
        filtered_users.sort(key=lambda x: x[1], reverse=True)
        chosen_users = filtered_users[:max_users]
        
        return [user_id for user_id, _ in chosen_users]
