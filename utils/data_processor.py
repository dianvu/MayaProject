import os, sys
import pandas as pd
from datetime import datetime

class DataProcessor:
    def __init__(self, file_path: str, input_file: str, output_file: str = None):
        self.file_path = file_path
        self.input_file = input_file
        self.output_file = output_file or "transactions.csv"
    
    def process(self):
        # Read the input data
        data = pd.read_csv(os.path.join(self.file_path, self.input_file))

        # Rename columns
        column_names = [
            "user_id",
            "segment_tag1",
            "segment_tag2",
            "segment_tag3",
            "timestamp",
            "source",
            "transaction_type",
            "transaction_method",
            "platform",
            "amount"]
        data.columns = column_names

        # Drop column without useful info
        data.drop(columns=["source", "platform"], inplace=True)

        # Extract date only
        data['timestamp'] = pd.to_datetime(data['timestamp']).dt.date
        
        # Create segment_tag column combines tag from segment_tag1, segment_tag2, segment_tag3 then drop 
        def combine_tags(row):
            tags = []
            for col in ["segment_tag1", "segment_tag2", "segment_tag3"]:
              if pd.notna(row[col]) and str(row[col]) != "nan":
                tags.append(str(row[col]))
            return ', '.join(tags)
        data['segment_tag'] = data.apply(combine_tags, axis=1)
        data.drop(columns=["segment_tag1", "segment_tag2", "segment_tag3"], inplace=True)

        # Save processed file
        data.to_csv(os.path.join(self.file_path, self.output_file), index=False)