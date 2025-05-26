import os
import json
import re
from pathlib import Path

def read_json_file(file_path):
    """Read a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading JSON file {file_path}: {str(e)}")
        return None

def extract_sections(content):
    """Extract metadata, executive summary, and recommendations from content."""
    if not content:
        return None
        
    # Initialize sections
    sections = {
        'metadata': '',
        'executive_summary': '',
        'recommendations': ''
    }
    
    # If content is a dictionary, look for specific keys
    if isinstance(content, dict):
        # Look for metadata (could be in various keys)
        metadata_keys = ['metadata', 'info', 'header', 'title', 'author', 'date', 'user_id', 'year', 'month']
        for key in metadata_keys:
            if key in content:
                if isinstance(content[key], dict):
                    sections['metadata'] += f"{key}: {json.dumps(content[key], indent=2)}\n"
                else:
                    sections['metadata'] += f"{key}: {content[key]}\n"
        
        # Look for executive summary
        summary_keys = ['executive_summary', 'summary', 'abstract', 'overview', 'analysis', 'findings']
        for key in summary_keys:
            if key in content:
                if isinstance(content[key], dict):
                    sections['executive_summary'] += f"{key}:\n{json.dumps(content[key], indent=2)}\n"
                else:
                    sections['executive_summary'] += f"{key}: {content[key]}\n"
        
        # Look for recommendations
        rec_keys = ['recommendations', 'conclusion', 'findings', 'suggestions', 'next_steps', 'action_items']
        for key in rec_keys:
            if key in content:
                if isinstance(content[key], dict):
                    sections['recommendations'] += f"{key}:\n{json.dumps(content[key], indent=2)}\n"
                else:
                    sections['recommendations'] += f"{key}: {content[key]}\n"
        
        # If we haven't found any sections, try to extract from the entire content
        if not any(sections.values()):
            sections['metadata'] = json.dumps(content, indent=2)
    
    return sections

def extract_and_save_summary(json_path):
    content = read_json_file(json_path)
    if not content:
        return
    metadata = content.get('metadata', {})
    user_id = metadata.get('user_id', None)
    report_components = content.get('report_components', {})
    executive_summary = report_components.get('executive_summary', '')
    recommendations = report_components.get('recommendations', '')

    if not user_id:
        print(f"No user_id found in {json_path}")
        return
    if not executive_summary and not recommendations:
        print(f"No executive_summary or recommendations in {json_path}")
        return

    # Prepare output text
    output = f"EXECUTIVE SUMMARY:\n{executive_summary}\n\nRECOMMENDATIONS:\n{recommendations}\n"
    # Save in the same folder as the JSON file
    output_path = os.path.join(os.path.dirname(json_path), f"{user_id}_summary.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"Saved summary for {user_id} to {output_path}")

def process_desktop_jsons():
    desktop_path = os.path.expanduser("~/Desktop")
    for root, dirs, files in os.walk(desktop_path):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                extract_and_save_summary(json_path)

if __name__ == "__main__":
    process_desktop_jsons() 