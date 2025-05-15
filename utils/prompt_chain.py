from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from prompts.executive_summary_templates import executive_summary_zero_shot, executive_summary_few_shot, executive_summary_cot
from prompts.cash_flow_templates import cash_flow_zero_shot, cash_flow_few_shot, cash_flow_cot
from prompts.transaction_behaviour_templates import transaction_behavior_zero_shot, transaction_behavior_few_shot, transaction_behavior_cot
from prompts.saving_position_templates import savings_position_zero_shot, savings_position_few_shot, savings_position_cot
from prompts.recommendations_templates import recommendations_zero_shot, recommendations_few_shot, recommendations_cot
import os
import csv
import json
import calendar

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

def get_report_components(llm, transaction_summary, best_approaches=None, user_id=None, year=None, month=None):
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
    report_components = {}
    
    # Extract content from AIMessage objects
    exec_summary_result = exec_summary_chain.invoke({"transaction_summary": transaction_summary})
    report_components["executive_summary"] = str(exec_summary_result) if hasattr(exec_summary_result, "content") else str(exec_summary_result)
    
    cash_flow_result = cash_flow_chain.invoke({"transaction_summary": transaction_summary})
    report_components["cash_flow"] = str(cash_flow_result) if hasattr(cash_flow_result, "content") else str(cash_flow_result)
    
    transaction_behaviour_result = transaction_behaviour_chain.invoke({"transaction_summary": transaction_summary})
    report_components["transaction_behaviour"] = str(transaction_behaviour_result) if hasattr(transaction_behaviour_result, "content") else str(transaction_behaviour_result)
    
    savings_position_result = savings_position_chain.invoke({"transaction_summary": transaction_summary})
    report_components["savings_position"] = str(savings_position_result) if hasattr(savings_position_result, "content") else str(savings_position_result)
    
    recommendations_result = recommendations_chain.invoke({"transaction_summary": transaction_summary})
    report_components["recommendations"] = str(recommendations_result) if hasattr(recommendations_result, "content") else str(recommendations_result)
    
    # Create the structured report with metadata and report components
    report = {
        "metadata": {
            "user_id": user_id if user_id else None,
            "year": year if year else None,
            "month": month if isinstance(month, str) else calendar.month_name[month] if month else None
        },
        "report_components": report_components
    }
    
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
    """Generate financial reports for multiple users using different prompting techniques.

    This function generates financial reports for each user in the provided list using three different
    prompting approaches: zero-shot, few-shot, and chain-of-thought. For each user and approach,
    it generates a complete financial report including executive summary, cash flow analysis,
    transaction behavior, savings position, and recommendations.

    Args:
        llm: The language model instance to use for generating reports
        data_fetcher: An object that provides access to user transaction data
        year (int): The year for which to generate reports
        month (int): The month for which to generate reports
        user_ids (list): List of user IDs to generate reports for
        output_folder (str, optional): Directory where reports will be saved. Defaults to "reports".

    The function generates the following folder structure:
        reports/
            {year}/
                {month_name}/
                    text/
                        {user_id}_{method}_{year}_{month_name}.txt
                    json/
                        {user_id}_{method}_{year}_{month_name}.json

    Note:
        The function creates the necessary directory structure if it doesn't exist.
        Each report is generated using the specified prompting technique for all components
        (executive summary, cash flow, transaction behavior, savings position, and recommendations).
    """
    
    # Convert month number to month name
    month_name = calendar.month_name[month]
    
    # Create the directory structure
    year_folder = os.path.join(output_folder, str(year))
    month_folder = os.path.join(year_folder, month_name)
    text_folder = os.path.join(month_folder, "text")
    json_folder = os.path.join(month_folder, "json")
    
    # Create all necessary directories
    for folder in [year_folder, month_folder, text_folder, json_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

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
            }
            # "few-shot": {
            #     "executive_summary": "few_shot",
            #     "cash_flow": "few_shot",
            #     "transaction_behaviour": "few_shot",
            #     "savings_position": "few_shot",
            #     "recommendations": "few_shot"
            # },
            # "chain_of_thought": {
            #     "executive_summary": "chain_of_thought",
            #     "cash_flow": "chain_of_thought",
            #     "transaction_behaviour": "chain_of_thought",
            #     "savings_position": "chain_of_thought",
            #     "recommendations": "chain_of_thought"
            # }
        }
        for method, approach in prompting_methods.items():
            print(f"Generating {method} report...")
            try:
                report_components = get_report_components(
                    llm, 
                    transaction_summary, 
                    approach,
                    user_id=user_id,
                    year=year,
                    month=month_name)
                
                # Excluded metadata from the text report templates
                report_formatted = get_report_template(report_components["report_components"], year, month_name, user_id)
                
                # Save report to text file
                report_filename = f"{user_id}_{method}_{year}_{month_name}.txt"
                report_path = os.path.join(text_folder, report_filename)
                with open(report_path, "w") as f:
                    f.write(report_formatted)
                    
                # Save report components to JSON
                report_json = f"{user_id}_{method}_{year}_{month_name}.json"
                json_path = os.path.join(json_folder, report_json)
                with open(json_path, "w") as f_json:
                    json.dump(report_components, f_json, indent=4)
                
            except Exception as e:
                print(f"Error generating {method} report for user {user_id}: {str(e)}")