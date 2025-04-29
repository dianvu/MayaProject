from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from prompts.executive_summary_templates import executive_summary_zero_shot, executive_summary_few_shot, executive_summary_cot
from prompts.cash_flow_templates import cash_flow_cot
from prompts.transaction_behaviour_templates import transaction_behavior_cot

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
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=cash_flow_cot
        )
    }
    return cash_flow_prompt

def get_transaction_behaviour():
    transaction_behaviour_prompt = {
        "chain_of_thought": PromptTemplate(
            input_variables=["transaction_summary"],
            template=transaction_behavior_cot
        )
    }
    return transaction_behaviour_prompt

# Chain creation from Anthropic model
def create_chains(llm, prompts):
    chains = {}
    for method, prompt in prompts.items():
        chains[method] = (prompt | llm | (lambda response: {method: response}))
    return chains
