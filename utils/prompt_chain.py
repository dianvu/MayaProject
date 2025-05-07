from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from prompts.executive_summary_templates import executive_summary_zero_shot, executive_summary_few_shot, executive_summary_cot
from prompts.cash_flow_templates import cash_flow_zero_shot, cash_flow_few_shot, cash_flow_cot
from prompts.transaction_behaviour_templates import transaction_behavior_zero_shot, transaction_behavior_few_shot, transaction_behavior_cot
from prompts.saving_position_templates import savings_position_zero_shot, savings_position_few_shot, savings_position_cot
from prompts.recommendations_templates import recommendations_zero_shot, recommendations_few_shot, recommendations_cot
import os
import csv

# Prompt Template for each Financial report components
def get_executive_summary():
    executive_summary_prompt = {
        "zero_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=executive_summary_zero_shot
        ),
        "few_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=executive_summary_few_shot
        ),
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=executive_summary_cot
        )
    }
    return executive_summary_prompt

def get_cash_flow():
    cash_flow_prompt = {
        "zero_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=cash_flow_zero_shot
        ),
        "few_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=cash_flow_few_shot
        ),
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=cash_flow_cot
        )
    }
    return cash_flow_prompt

def get_transaction_behaviour():
    transaction_behaviour_prompt = {
        "zero_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=transaction_behavior_zero_shot
        ),
        "few_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=transaction_behavior_few_shot
        ),
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=transaction_behavior_cot
        )
    }
    return transaction_behaviour_prompt

def get_savings_position():
    savings_position_prompt = {
        "zero_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=savings_position_zero_shot
        ),
        "few_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=savings_position_few_shot
        ),
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=savings_position_cot
        )
    }
    return savings_position_prompt

def get_recommendations():
    recommendations_prompt = {
        "zero_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=recommendations_zero_shot
        ),
        "few_shot": PromptTemplate(
            input_variables=["transaction_summary"],
            template=recommendations_few_shot
        ),
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=recommendations_cot
        )
    }
    return recommendations_prompt

# Chain creation from Anthropic model
def create_chains(llm, prompts):
    chains = {}
    for method, prompt in prompts.items():
        chains[method] = (prompt | llm | (lambda response: {method: response}))
    return chains

def get_report_components(llm, transaction_summary, best_approaches=None):
    """
    Generate a financial report using the best prompting approaches for each component.
    
    Args:
        llm: The language model to use
        transaction_summary: The transaction data for the user
        best_approaches: Dictionary mapping component names to best prompting approach.
                        If None, defaults to chain_of_thought for all components.
    
    Returns:
        Dictionary containing generated content for each report component
    """
    # Get all prompt templates
    executive_summary_prompts = get_executive_summary()
    cash_flow_prompts = get_cash_flow()
    transaction_behaviour_prompts = get_transaction_behaviour()
    savings_position_prompts = get_savings_position()
    recommendations_prompts = get_recommendations()
    
    # Default to chain_of_thought if best_approaches not provided
    if best_approaches is None:
        best_approaches = {
            "executive_summary": "few_shot",
            "cash_flow": "chain_of_thought",
            "transaction_behaviour": "chain_of_thought",
            "savings_position": "chain_of_thought",
            "recommendations": "chain_of_thought"
        }
    
    # Create chains using LCEL (prompt | llm)
    exec_summary_chain = executive_summary_prompts[best_approaches.get("executive_summary", "chain_of_thought")] | llm
    cash_flow_chain = cash_flow_prompts[best_approaches.get("cash_flow", "chain_of_thought")] | llm
    transaction_behaviour_chain = transaction_behaviour_prompts[best_approaches.get("transaction_behaviour", "chain_of_thought")] | llm
    savings_position_chain = savings_position_prompts[best_approaches.get("savings_position", "chain_of_thought")] | llm
    recommendations_chain = recommendations_prompts[best_approaches.get("recommendations", "chain_of_thought")] | llm
    
    # Generate each component of the report
    report = {}
    report["executive_summary"] = exec_summary_chain.invoke({"transaction_summary": transaction_summary})
    report["cash_flow"] = cash_flow_chain.invoke({"transaction_summary": transaction_summary})
    report["transaction_behaviour"] = transaction_behaviour_chain.invoke({"transaction_summary": transaction_summary})
    report["savings_position"] = savings_position_chain.invoke({"transaction_summary": transaction_summary})
    report["recommendations"] = recommendations_chain.invoke({"transaction_summary": transaction_summary})
    
    # Extract content from the response objects if needed
    for key, value in report.items():
        if hasattr(value, 'content'):
            report[key] = value.content
    
    return report

def get_report_template(report_components, year, month, user_id):
    return f"""
**Your Monthly Financial Summary: {month} {year}**
**Prepare for:** User {user_id}

**Executive Summary**
{report_components["executive_summary"]}

**1. Cash Flow Analysis**
{report_components["cash_flow"]}

**2. Transaction Behavior**
{report_components["transaction_behaviour"]}

**3. Savings & Financial Position**
{report_components["savings_position"]}

**4. Recommendations**
{report_components["recommendations"]}
"""

def generate_reports(llm, data_fetcher, year, month, user_ids, output_folder="reports"):
    # Ensure output directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Initialize csv for export
    csv_path = os.path.join(output_folder, f"report_{year}_{month}.csv")
    csv_data = []
    csv_headers = ["user_id", "user_profile", "report_type", "report_content"]

    for user_id in user_ids:
        print(f"Generating reports for user {user_id}...")
            
        # Get transaction summary for this user
        transaction_summary = data_fetcher.monthly_profile(year, month, user_id)
            
        # Generate reports using difference prompting techniques
        prompting_methods = {
            "zero-shot": {
                "executive_summary": "zero_shot",
                "cash_flow": "zero_shot",
                "transaction_behaviour": "zero_shot",
                "savings_position": "zero_shot",
                "recommendations": "zero_shot"
            },
            "few-shot": {
                "executive_summary": "few_shot",
                "cash_flow": "few_shot",
                "transaction_behaviour": "few_shot",
                "savings_position": "few_shot",
                "recommendations": "few_shot"
            },
            "chain_of_thought": {
                "executive_summary": "chain_of_thought",
                "cash_flow": "chain_of_thought",
                "transaction_behaviour": "chain_of_thought",
                "savings_position": "chain_of_thought",
                "recommendations": "chain_of_thought"
            }
        }
        for method, approach in prompting_methods.items():
            print(f"Generating {method} report...")
            try:
                report_components = get_report_components(llm, transaction_summary, approach)
                report_formatted = get_report_template(report_components, year, month, user_id)
                
                # Save report to file
                report_filename = f"{user_id}_{method}_{year}_{month}.txt"
                report_path = os.path.join(output_folder, report_filename)
                with open(report_path, "w") as f:
                    f.write(report_formatted)
                
                csv_data.append({
                    "user_id": user_id,
                    "user_profile": transaction_summary,
                    "report_type": method,
                    "report_content": report_formatted
                })
            except Exception as e:
                print(f"Error generating {method} report for user {user_id}: {str(e)}")
        
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)  # Fixed variable name from csv_header to csv_headers
        writer.writeheader()
        writer.writerows(csv_data)
        
    print(f"All reports exported to CSV: {csv_path}")
    return csv_path
