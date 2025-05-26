import os
import json
from pathlib import Path
import sys

# Add project root to path
project_root = os.path.abspath(os.getcwd())
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.data_fetcher import DataFetcher

def read_json_file(file_path):
    """Read a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {str(e)}")
        return None

def extract_user_id(content):
    """Extract user_id from content."""
    if not content:
        return None
        
    if isinstance(content, dict):
        # Look for user_id in metadata or directly in content
        if 'metadata' in content and isinstance(content['metadata'], dict):
            return content['metadata'].get('user_id')
        return content.get('user_id')
    return None

def process_json_files():
    # Initialize DataFetcher
    data_path = os.path.join(project_root, "data")
    output_file = os.path.join(data_path, "transactions.csv")
    db = os.path.join(data_path, "transactions.db")
    data_fetcher = DataFetcher(output_file, db)
    
    # Target year and month (you can modify these as needed)
    target_year = 2025
    target_month = 3
    
    # Get Desktop path
    desktop_path = os.path.expanduser("~/Desktop")
    
    # Walk through Desktop and its subdirectories
    for root, dirs, files in os.walk(desktop_path):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                
                # Read JSON and extract user_id
                content = read_json_file(json_path)
                user_id = extract_user_id(content)
                
                if user_id:
                    try:
                        # Get monthly profile
                        transaction_summary = data_fetcher.monthly_profile(target_year, target_month, user_id)
                        
                        # Save profile to text file in the same directory
                        output_path = os.path.join(root, f"{user_id}_profile.txt")
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(transaction_summary)
                        print(f"Saved profile for {user_id} to {output_path}")
                    except Exception as e:
                        print(f"Error processing user {user_id}: {str(e)}")
                else:
                    print(f"No user_id found in {json_path}")

if __name__ == "__main__":
    process_json_files()