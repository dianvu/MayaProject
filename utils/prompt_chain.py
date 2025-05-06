from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from prompts.executive_summary_templates import executive_summary_zero_shot, executive_summary_few_shot, executive_summary_cot
from prompts.cash_flow_templates import cash_flow_zero_shot, cash_flow_few_shot, cash_flow_cot
from prompts.transaction_behaviour_templates import transaction_behavior_zero_shot, transaction_behavior_few_shot, transaction_behavior_cot
from prompts.saving_position_templates import savings_position_zero_shot, savings_position_few_shot, savings_position_cot
from prompts.recommendations_templates import recommendations_zero_shot, recommendations_few_shot, recommendations_cot

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

def financial_report(llm, transaction_summary, best_approaches=None):
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
            "executive_summary": "chain_of_thought",
            "cash_flow": "chain_of_thought",
            "transaction_behaviour": "chain_of_thought",
            "savings_position": "chain_of_thought",
            "recommendations": "chain_of_thought"
        }
    
    # Create chains for each component using the best approach
    exec_summary_chain = LLMChain(llm=llm, prompt=executive_summary_prompts[best_approaches.get("executive_summary", "chain_of_thought")])
    cash_flow_chain = LLMChain(llm=llm, prompt=cash_flow_prompts[best_approaches.get("cash_flow", "chain_of_thought")])
    transaction_behaviour_chain = LLMChain(llm=llm, prompt=transaction_behaviour_prompts[best_approaches.get("transaction_behaviour", "chain_of_thought")])
    savings_position_chain = LLMChain(llm=llm, prompt=savings_position_prompts[best_approaches.get("savings_position", "chain_of_thought")])
    recommendations_chain = LLMChain(llm=llm, prompt=recommendations_prompts[best_approaches.get("recommendations", "chain_of_thought")])
    
    # Generate each component of the report
    report = {}
    report["executive_summary"] = exec_summary_chain.run(transaction_summary=transaction_summary)
    report["cash_flow"] = cash_flow_chain.run(transaction_summary=transaction_summary)
    report["transaction_behaviour"] = transaction_behaviour_chain.run(transaction_summary=transaction_summary)
    report["savings_position"] = savings_position_chain.run(transaction_summary=transaction_summary)
    report["recommendations"] = recommendations_chain.run(transaction_summary=transaction_summary)
    
    return report

def get_report_template(year, month, user_id):
    return f"""
**Your Monthly Financial Summary: {month} {year}**
**Prepare for:** User {user_id}

**Executive Summary**
{financial_report["executive_summary"]}

**1. Cash Flow Analysis**
{financial_report["cash_flow"]}

**2. Transaction Behavior**
{financial_report["transaction_behaviour"]}

**3. Savings & Financial Position**
{financial_report["savings_position"]}

**4. Recommendations**
{financial_report["recommendations"]}
"""
