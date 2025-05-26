import json
import os
import pandas as pd
from pathlib import Path
import sys

# Add project root to path (going up one level from features folder)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

def extract_evaluations(reports_dir: str, output_dir: str):
    """
    Extract evaluation components from JSON reports and save to a single CSV file.
    
    Args:
        reports_dir: Directory containing the JSON report files
        output_dir: Directory to save the CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # List to store all evaluation data
    all_eval_data = []
    
    # Process each JSON file in the reports directory
    for json_file in Path(reports_dir).glob('*.json'):
        try:
            # Read JSON file
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract user_id and metadata
            user_id = data['metadata']['user_id']
            year = data['metadata']['year']
            month = data['metadata']['month']
            
            # Process each component (executive_summary and recommendations)
            for component in ['executive_summary', 'recommendations']:
                eval_info = data['evaluations'][component]
                best_approach = data['best_approaches'][component]
                
                all_eval_data.append({
                    'user_id': user_id,
                    'year': year,
                    'month': month,
                    'component': component,
                    'ethical_flag': eval_info['ethical_flag'],
                    'confidence': eval_info['confidence'],
                    'similarity_score': eval_info['similarity_score'],
                    'best_approach': best_approach
                })
            
            print(f"Processed evaluations for user {user_id}")
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
    
    # Create DataFrame and save to CSV
    if all_eval_data:
        df = pd.DataFrame(all_eval_data)
        output_file = os.path.join(output_dir, 'all_evaluations.csv')
        df.to_csv(output_file, index=False)
        print(f"\nCreated combined evaluation CSV with {len(df)} rows")
        print(f"File saved to: {output_file}")
    else:
        print("No evaluation data was processed")

if __name__ == "__main__":
    # Define directories relative to project root
    reports_dir = os.path.join(project_root, "reports/2025/March")
    output_dir = os.path.join(project_root, "evaluations/2025/March")
    
    # Extract evaluations
    extract_evaluations(reports_dir, output_dir)
    print("Evaluation extraction completed!") 