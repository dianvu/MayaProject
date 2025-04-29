from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Set, Union
import pandas as pd
from datetime import datetime, timedelta
import calendar
from collections import Counter

class Transaction(BaseModel):
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    transaction_type: str
    transaction_method: str
    amount: float
    segment_tag: str
    
    def is_spend(self) -> bool:
        return self.transaction_type == "SPEND"
    
    def is_cash_in(self) -> bool:
        return self.transaction_type == "CASH-IN"

class DataFetcher:
    def __init__(self, file_path: str = None, data: pd.DataFrame = None):
        """Initialize DataFetcher with either a file path or a pandas DataFrame"""
        if file_path:
            self.data = pd.read_csv(file_path)
        elif data is not None:
            self.data = data
        else:
            raise ValueError("Either file_path or data must be provided")
        
        # Convert timestamp column to datetime
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        
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
        
        # Get start and end of month then filtered transactions within this timestamp
        start_of_month = self._month_start_date(year, month)
        end_of_month = self._month_end_date(year, month)
        
        mask = (self.data['timestamp'] >= start_of_month) & (self.data['timestamp'] <= end_of_month)
        if user_id:
            mask = mask & (self.data['user_id'] == user_id)
        
        filtered_df = self.data[mask]
        
        # Convert only the filtered rows to Transaction objects
        return [
            Transaction(
                user_id=row.user_id,
                timestamp=row.timestamp,
                transaction_type=row.transaction_type,
                transaction_method=row.transaction_method,
                amount=row.amount,
                segment_tag=row.segment_tag
            ) for _, row in filtered_df.iterrows()
        ]
        
    def _monthly_spend(self, year: int, month: int, user_id: Optional[str] = None) -> tuple:
        transactions = self._monthly_transactions(year, month, user_id)
        spend_transactions = [t for t in transactions if t.is_spend()]
        return sum(t.amount for t in spend_transactions), len(spend_transactions), spend_transactions
    
    def _monthly_cash_in(self, year: int, month: int, user_id: Optional[str] = None) -> tuple:
        transactions = self._monthly_transactions(year, month, user_id)
        cash_in_transactions = [t for t in transactions if t.is_cash_in()]
        return sum(t.amount for t in cash_in_transactions), len(cash_in_transactions), cash_in_transactions
    
    def _format_tag(self, tag: str) -> str:
        """Convert a tag from UPPER_CASE to lowercase with spaces"""
        return tag.lower().replace('_', ' ')
    
    def monthly_profile(self, year: int, month: int, user_id: str) -> str:
        # Error handling
        if user_id not in self.user_ids:
            return f"Error: User ID {user_id} not found."
        if not (1 <= month <= 12):
             return "Error: Invalid month, must be from 1 to 12" 

        """Useful stats section for user profile"""
        spend_amount, spend_count, spend_transactions = self._monthly_spend(year, month, user_id)
        cash_in_amount, cash_in_count, cash_in_transactions = self._monthly_cash_in(year, month, user_id)

        # Transactions by transaction_method
        spend_by_method = Counter([t.transaction_method for t in spend_transactions])
        spend_by_method_total = spend_by_method.total()
        cash_in_by_method = Counter([t.transaction_method for t in cash_in_transactions])
        cash_in_by_method_total = cash_in_by_method.total()
		
		# Fetch data for the specified month ONLY
        transactions = self._monthly_transactions(year, month, user_id)
        
        # Get user-specific segments only
        user_segments = set()
        for transaction in transactions:
            user_segments.add(transaction.segment_tag)
        
        # Format the segments in lowercase with spaces
        formatted_segments = [self._format_tag(tag) for tag in user_segments]

        """Formulate user profile section """        
		    # Prepare the header for the insights text
        insights = [f"User {user_id} monthly transactions Summary (Timestamp: {year}-{month:02d})"]
		
		    # Handle case where there's no data for the month
        if not transactions:
             insights.append("- No transaction data found for this month.")
             return "\n".join(insights)
		
        # User segments - only show those belonging to this user
        insights.append(f"- This user is tagged with {', '.join(formatted_segments)}")
        
        # User total spend with amounts listed
        insights.append(f"- Total spend is {spend_amount} with {spend_count} transactions")
        insights.append("- Spend transactions:")
        for i, transaction in enumerate(spend_transactions, 1):
            insights.append(f"  {i}. {transaction.amount} via {transaction.transaction_method.lower()}")
        
        # User spending method
        spend_by_method_display = []
        for method, count in spend_by_method.most_common(5):
            percentage = (count / spend_by_method_total)
            spend_by_method_display.append(f"{method.lower()} with {percentage:.2%}")
        spend_by_method_summary = ", ".join(spend_by_method_display)
        insights.append(f"- Spending methods include {spend_by_method_summary}")
        
        # User total cash-in with amounts listed
        insights.append(f"- Total cash-in is {cash_in_amount} with {cash_in_count} transactions")
        insights.append("- Cash-in transactions:")
        for i, transaction in enumerate(cash_in_transactions, 1):
            insights.append(f"  {i}. {transaction.amount} via {transaction.transaction_method.lower()}")
        
        # User cash-in method
        cash_in_by_method_display = []
        for method, count in cash_in_by_method.most_common(5):
            percentage = (count / cash_in_by_method_total)
            cash_in_by_method_display.append(f"{method.lower()} with {percentage:.2%}")
        cash_in_by_method_summary = ", ".join(cash_in_by_method_display)
        insights.append(f"- Cash-in methods include {cash_in_by_method_summary}")
        
        # User spend/cash-in ratio, check for cash-in
        if cash_in_amount > 0:
            insights.append(f"- Spending accounts for {(spend_amount / cash_in_amount):.2%} of total cash-in")
        else:
            insights.append("- The ratio of spending to cash-in is not applicable, as the user did not deposit any funds")
        
        return "\n".join(insights)
    
    def _monthly_transactions_by_user(self, year: int, month: int) -> Dict[str, int]:
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
        """Get a list of active users for a specific month based on multiple criteria

        Args:
            year (int): Target year
            month (int): Target month (1-12)
            min_transactions (int, optional): Minimum of transactions required. Defaults to 3.
            max_users (int, optional): Maximum number of users to return. Defaults to 1000.
            min_spend (float, optional): Minimum spend amount required. Defaults to 0.
            min_cash_in (float, optional): Minimum cash-in amount required. Defaults to 0.

        Returns:
            List[str]: List of user_ids meet all criteria
        """
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