import os
import calendar
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import traceback

# Project modules
from utils.data_processor import DataProcessor
from utils.data_fetcher import DataFetcher
from utils.report_generator import ReportGenerator
from utils.config import anthropic_llm

# --- Configuration ---
# Paths (adjust as per your project structure)
# Assuming 'raw_data' contains the initial CSV, 
# 'data' will store processed CSV and DB, 
# 'reports' for output JSONs.
# Ensure these directories exist or are created by the script.
RAW_DATA_DIR = "raw_data"
INITIAL_CSV_FILENAME = "ai-insights_full.csv"
PROCESSED_DATA_DIR = "data"
PROCESSED_CSV_FILENAME = "transactions.csv"
DB_NAME = "transactions.db"
OUTPUT_DIR = "reports"

# Processing parameters
TARGET_YEAR = 2024
TARGET_MONTH = 4

# Embedding model
# Replace with 'FinLang/finance-embeddings-investopedia' if you have it set up
# For this example, using a common default model.
EMBEDDING_MODEL_NAME = 'FinLang/finance-embeddings-investopedia'
# Ensure you have `pip install sentence-transformers sklearn numpy`

# --- Helper Functions for Embeddings and Similarity ---
def get_embedding(text_list: List[str], model: SentenceTransformer) -> np.ndarray:
    """Generates embeddings for a list of texts."""
    embeddings = model.encode(text_list, convert_to_numpy=True)
    return embeddings

def calculate_cosine_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """Calculates cosine similarity between two single embeddings."""
    # Ensure embeddings are 2D for cosine_similarity function
    return cosine_similarity(embedding1.reshape(1, -1), embedding2.reshape(1, -1))[0][0]

# --- Main Workflow ---
def main():
    # Initialize LLM Model
    llm = anthropic_llm()

    # Initialize Embedding Model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Process Initial Data (Raw CSV -> Processed CSV)
    # data_processor = DataProcessor(os.path.join(RAW_DATA_DIR, INITIAL_CSV_FILENAME), os.path.join(PROCESSED_DATA_DIR, PROCESSED_CSV_FILENAME))
    # data_processor.process()

    # Initialize Data Fetcher, get one user for demonstration
    data_fetcher = DataFetcher(processed_csv_path=os.path.join(PROCESSED_DATA_DIR, PROCESSED_CSV_FILENAME))
    USER_IDS_TO_PROCESS = data_fetcher.active_users(year=TARGET_YEAR, month=TARGET_MONTH, min_transactions=5, max_users=1, min_spend=0, min_cash_in=0)

    # 5. Generate reports
    for user_id in USER_IDS_TO_PROCESS:
        # Fetch Monthly Profile (Transaction Summary)
        transaction_summary = data_fetcher.monthly_profile(TARGET_YEAR, TARGET_MONTH, user_id)

        # Initialize Report Generator for this user and period
        report_generator = ReportGenerator(llm, user_id, TARGET_YEAR, TARGET_MONTH)

        # c. Evaluate Prompting Techniques
        best_approaches_for_user = {}

        for component_name, component_prompts in report_generator.prompt_templates.items():
            print(f"  Component: {component_name}")
            best_similarity_for_component = -2.0 # Initialize with a value lower than any possible cosine similarity
            chosen_approach_for_component = None

            for approach_name, prompt_template_obj in component_prompts.items():
                try:
                    raw_template_string = prompt_template_obj.template
                    
                    # Generate LLM Output
                    chain = prompt_template_obj | llm # LangChain's LCEL syntax
                    llm_result = chain.invoke({"transaction_summary": transaction_summary})
                    
                    llm_output_text = ""
                    if hasattr(llm_result, 'content'): # For AIMessage objects
                        llm_output_text = str(llm_result.content)
                    elif isinstance(llm_result, str):
                        llm_output_text = llm_result
                    else: # Fallback for other types
                        llm_output_text = str(llm_result)

                    if not llm_output_text.strip():
                        print(f"    Approach {approach_name}: LLM output is empty. Similarity: N/A")
                        similarity = -1.0 # Penalize empty outputs
                    else:
                        # Embed template and output
                        # Note: get_embedding expects a list of texts
                        embeddings = get_embedding([raw_template_string, llm_output_text], embedding_model)
                        embedding_template = embeddings[0]
                        embedding_output = embeddings[1]
                        
                        similarity = calculate_cosine_similarity(embedding_template, embedding_output)
                        print(f"    Approach {approach_name}: Similarity = {similarity:.4f}")

                    if similarity > best_similarity_for_component:
                        best_similarity_for_component = similarity
                        chosen_approach_for_component = approach_name
                
                except Exception as e:
                    print(f"    Error evaluating {approach_name} for {component_name}: {e}")
                    traceback.print_exc()
                    # Optionally, assign a very low score or handle as failed

            if chosen_approach_for_component:
                best_approaches_for_user[component_name] = chosen_approach_for_component
                print(f"  Best approach for {component_name}: {chosen_approach_for_component} (Similarity: {best_similarity_for_component:.4f})")
            else:
                print(f"  Could not determine best approach for {component_name}. Using default (chain_of_thought).")
                best_approaches_for_user[component_name] = "chain_of_thought" # Fallback

        print(f"\nSelected best approaches for User {user_id}: {best_approaches_for_user}")

        # d. Generate Final Report using the best approaches
        print("Generating final report with selected best approaches...")
        final_report_data = report_generator.generate_report(
            transaction_summary,
            approach=best_approaches_for_user # Pass the dictionary of best approaches
        )

        # e. Save Final Report to JSON
        # The save_report method in new2.py creates subfolders for year/month/type.
        # The 'method' argument can be used to distinguish this optimized report.
        try:
            report_generator.save_report(
                report=final_report_data,
                output_folder=OUTPUT_DIR,
                method="optimized_by_similarity" 
            )
            month_name_str = calendar.month_name[TARGET_MONTH]
            print(f"Final optimized report for {user_id} saved in '{OUTPUT_DIR}/{TARGET_YEAR}/{month_name_str}/json/'")
        except Exception as e:
            print(f"Error saving final report for {user_id}: {e}")
            traceback.print_exc()
            
    print("\nWorkflow finished.")

if __name__ == "__main__":
    main()
