from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
import pandas as pd
from datetime import datetime, timedelta
import calendar
from collections import Counter
from utils.database import TransactionDB

class Transaction(BaseModel):
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
    def __init__(self, file_path: str = None, data: pd.DataFrame = None, db_path: str = "transactions.db"):
        """Initialize DataFetcher with either a file path or a pandas DataFrame"""
        if file_path:
            self.data = pd.read_csv(file_path)
        elif data is not None:
            self.data = data
        else:
            raise ValueError("Either file_path or data must be provided")
        
        # Convert timestamp column to datetime
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        
        # Ensure amount column is float and handle null values
        self.data['amount'] = pd.to_numeric(self.data['amount'], errors='coerce')
        
        # Initialize database
        self.db = TransactionDB(db_path)
        
        # Convert data to list of dictionaries and validate
        transactions = []
        for _, row in self.data.iterrows():
            try:
                transaction = {
                    'user_id': str(row['user_id']),
                    'timestamp': row['timestamp'],
                    'transaction_type': str(row['transaction_type']),
                    'transaction_method': str(row['transaction_method']),
                    'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                    'segment_tag': str(row['segment_tag'])
                }
                transactions.append(transaction)
            except Exception as e:
                print(f"Error processing row: {row}")
                print(f"Error details: {str(e)}")
                continue
        
        # Insert validated transactions into database
        try:
            self.db.insert_transactions(transactions)
        except Exception as e:
            print(f"Error inserting transactions into database: {str(e)}")
            raise
        
        # Class attributes
        self.user_ids = set(self.data["user_id"].unique())
    
    def _month_start_date(self, year: int, month: int) -> datetime:
        return datetime(year, month, 1)

    def _month_end_date(self, year: int, month: int) -> datetime:
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day)
        
    def _monthly_transactions(self, year: int, month: int, user_id: Optional[str] = None) -> List[Transaction]:
        # Error handling
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")
        if user_id and user_id not in self.user_ids:
            print(f"User ID {user_id} not found.")
            return []
        
        # Get transactions from database
        if user_id:
            transactions = self.db.get_monthly_transactions(user_id, year, month)
        else:
            # If no user_id specified, fall back to pandas filtering
            start_of_month = self._month_start_date(year, month)
            end_of_month = self._month_end_date(year, month)
            mask = (self.data['timestamp'] >= start_of_month) & (self.data['timestamp'] <= end_of_month)
            filtered_df = self.data[mask]
            transactions = filtered_df.to_dict('records')
        
        # Convert to Transaction objects
        return [
            Transaction(
                user_id=user_id,  # Use the provided user_id
                timestamp=t['timestamp'],
                transaction_type=t['transaction_type'],
                transaction_method=t['transaction_method'],
                amount=t['amount'],
                segment_tag=t['segment_tag']
            ) for t in transactions
        ]
    
    def _monthly_spend(self, year: int, month: int, user_id: Optional[str] = None) -> tuple:
        if user_id:
            # Get from database
            profile = self.db.get_monthly_profile(user_id, year, month)
            return profile['total_spend'], profile['spend_count'], []
        else:
            # Fall back to pandas filtering
            transactions = self._monthly_transactions(year, month, user_id)
            spend_transactions = [t for t in transactions if t.is_spend()]
            return sum(t.amount for t in spend_transactions), len(spend_transactions), spend_transactions
    
    def _monthly_cash_in(self, year: int, month: int, user_id: Optional[str] = None) -> tuple:
        if user_id:
            # Get from database
            profile = self.db.get_monthly_profile(user_id, year, month)
            return profile['total_cash_in'], profile['cash_in_count'], []
        else:
            # Fall back to pandas filtering
            transactions = self._monthly_transactions(year, month, user_id)
            cash_in_transactions = [t for t in transactions if t.is_cash_in()]
            return sum(t.amount for t in cash_in_transactions), len(cash_in_transactions), cash_in_transactions
    
    def _format_tag(self, tag: str) -> str:
        """Convert a tag from UPPER_CASE to lowercase with spaces"""
        return tag.lower().replace('_', ' ')
    
    def monthly_profile(self, year: int, month: int, user_id: str) -> str:
        """Generate a concise monthly profile for a user with essential transaction information"""
        # Error handling
        if user_id not in self.user_ids:
            return f"Error: User ID {user_id} not found."
        if not (1 <= month <= 12):
             return "Error: Invalid month, must be from 1 to 12" 

        # Get profile data from database
        profile = self.db.get_monthly_profile(user_id, year, month)
        
        # Format segments
        formatted_segments = [self._format_tag(tag) for tag in profile['segments']]
        
        # Get transactions
        spend_transactions = [t for t in self._monthly_transactions(year, month, user_id) if t.is_spend()]
        cash_in_transactions = [t for t in self._monthly_transactions(year, month, user_id) if t.is_cash_in()]
        
        # Format the concise profile
        profile_lines = [
            f"User {user_id} ({year}-{month:02d})",
            f"Segments: {', '.join(formatted_segments)}",
            f"Spend: {profile['total_spend']:.2f} ({profile['spend_count']} txns)"
        ]
        
        # Add spend transactions
        if spend_transactions:
            profile_lines.append("Spend transactions:")
            for t in sorted(spend_transactions, key=lambda x: x.timestamp):
                date_str = t.timestamp.strftime("%Y-%m-%d")
                profile_lines.append(f"  {date_str}: {t.amount:.2f} via {t.transaction_method.lower()}")
        
        profile_lines.append(f"Cash-in: {profile['total_cash_in']:.2f} ({profile['cash_in_count']} txns)")
        
        # Add cash-in transactions
        if cash_in_transactions:
            profile_lines.append("Cash-in transactions:")
            for t in sorted(cash_in_transactions, key=lambda x: x.timestamp):
                date_str = t.timestamp.strftime("%Y-%m-%d")
                profile_lines.append(f"  {date_str}: {t.amount:.2f} via {t.transaction_method.lower()}")
        
        # Add spend/cash-in ratio if applicable
        if profile['total_cash_in'] > 0:
            ratio = profile['total_spend'] / profile['total_cash_in']
            profile_lines.append(f"Spend/Cash-in ratio: {ratio:.2%}")
        
        return "\n".join(profile_lines)
    
    def _monthly_transactions_by_user(self, year: int, month: int) -> Dict[str, int]:
        """Get transaction counts by user for a specific month"""
        # Get start and end of month
        start_of_month = self._month_start_date(year, month)
        end_of_month = self._month_end_date(year, month)

        # Filter data for the specified month
        mask = (self.data['timestamp'] >= start_of_month) & (self.data['timestamp'] <= end_of_month)
        monthly_data = self.data[mask]
        
        # Count transactions per user
        user_transaction_counts = Counter(monthly_data['user_id'])
        
        return user_transaction_counts
    
    def active_users(self, year: int, month: int, min_transactions: int=3,
                      max_users: int=1000, min_spend: float=0, min_cash_in: float=0) -> List[str]:
        """Get a list of active users for a specific month based on multiple criteria"""
        if not (1 <= month <=12):
            raise ValueError("Month must be between 1 and 12.")
        
        # Get transaction count
        user_counts = self._monthly_transactions_by_user(year, month)
        # Filter based on transaction count
        active_users = {user: count for user, count in user_counts.items() if count >= min_transactions}
        
        # Filter based on minimum spend/cash-in 
        if min_spend > 0 or min_cash_in > 0:
            filtered_users = []
            for user_id in active_users:
                spend_amount, _, _ = self._monthly_spend(year, month, user_id)
                cash_in_amount, _, _ = self._monthly_cash_in(year, month, user_id)
                
                if spend_amount >= min_spend and cash_in_amount >= min_cash_in:
                    filtered_users.append((user_id, active_users[user_id]))
        else:
            filtered_users = [(user_id, count) for user_id, count in active_users.items()]
            
        chosen_users = filtered_users[:max_users]
        return [user_id for user_id, _ in chosen_users]
    
    # def get_segment_users(self, year: int, month: int, 
    #                      min_transactions: int = 3, max_users: int = 50,
    #                      min_spend: float = 0, min_cash_in: float = 0) -> Dict[str, List[str]]:
    #     """Get active users grouped by their segments for a given month
        
    #     if not (1 <= month <= 12):
    #         raise ValueError("Month must be between 1 and 12.")
        
    #     # Get all active users first
    #     active_users = self.active_users(
    #         year=year,
    #         month=month,
    #         min_transactions=min_transactions,
    #         max_users=None,  # Don't limit here, we'll filter by segment first
    #         min_spend=min_spend,
    #         min_cash_in=min_cash_in
    #     )
        
    #     # Initialize dictionary to store users by segment
    #     segment_users_dict = {}
        
    #     # Get unique segments from the dataset
    #     unique_segments = self.data['segment_tag'].unique()
        
    #     # For each segment, find users who belong to it
    #     for segment in unique_segments:
    #         # Get all users in this segment
    #         segment_users = []
    #         for user_id in active_users:
    #             # Get user's segment
    #             user_segment = self.data[self.data['user_id'] == user_id].iloc[0]['segment_tag']
    #             # Check if user belongs to this segment
    #             if user_segment == segment:
    #                 segment_users.append(user_id)
            
    #         # Only add segment to dictionary if it has at least max_users (50) users
    #         if len(segment_users) >= max_users:
    #             # Take exactly max_users (50) users
    #             segment_users_dict[segment] = segment_users[:max_users]
        
    #     return segment_users_dict

    def get_segment_users(self, year: int, month: int, 
                     min_transactions: int = 3, max_users: int = 50,
                     min_spend: float = 0, min_cash_in: float = 0) -> Dict[str, List[str]]:
        """Get active users grouped by their segments for a given month
        
        Args:
            year (int): Target year
            month (int): Target month (1-12)
            min_transactions (int): Minimum number of transactions required
            max_users (int): Maximum number of users to return per segment (default: 50)
            min_spend (float): Minimum spend amount required
            min_cash_in (float): Minimum cash-in amount required
            
        Returns:
            Dict[str, List[str]]: Dictionary with segment names as keys and lists of user IDs as values
        """
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12.")
        
        # Get all active users first - keeping this part as requested
        active_users = self.active_users(
            year=year,
            month=month,
            min_transactions=min_transactions,
            max_users=None,  # Don't limit here, we'll filter by segment first
            min_spend=min_spend,
            min_cash_in=min_cash_in
        )
        
        # Create a look-up dictionary for user segments (optimize segment lookups)
        user_segments = {}
        
        # Filter the data once to get monthly data (more efficient)
        start_of_month = self._month_start_date(year, month)
        end_of_month = self._month_end_date(year, month)
        monthly_mask = (self.data['timestamp'] >= start_of_month) & (self.data['timestamp'] <= end_of_month)
        monthly_data = self.data[monthly_mask]
        
        # For active users, get their segment (use vectorized operations)
        if active_users:
            # Filter to only include active users
            active_user_data = monthly_data[monthly_data['user_id'].isin(active_users)]
            
            # Group by user_id and find the most recent segment for each user
            for user_id in active_users:
                user_rows = active_user_data[active_user_data['user_id'] == user_id]
                if not user_rows.empty:
                    # Get the latest transaction's segment for this user
                    latest_tx = user_rows.loc[user_rows['timestamp'].idxmax()]
                    user_segments[user_id] = latest_tx['segment_tag']
        
        # Initialize segment dictionary and group users
        segment_users_dict = {}
        
        # Group users by segment
        for user_id, segment in user_segments.items():
            if segment not in segment_users_dict:
                segment_users_dict[segment] = []
            segment_users_dict[segment].append(user_id)
        
        # Filter to only include segments with enough users and apply max_users limit
        return {segment: users[:max_users] 
                for segment, users in segment_users_dict.items() 
                if len(users) >= max_users}