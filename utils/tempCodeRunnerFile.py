import os
import sys

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import TransactionDB

def main():
    try:
        # Initialize the database
        db = TransactionDB()
        
        # Export all user monthly statistics to a single CSV file
        print("Exporting user monthly statistics...")
        db.export_all_user_monthly_stats()
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()