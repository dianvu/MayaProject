from langchain.prompts import PromptTemplate
from prompts.executive_summary_templates import executive_summary_zero_shot, executive_summary_few_shot, executive_summary_cot
# from prompts.cash_flow_templates import cash_flow_zero_shot, cash_flow_few_shot, cash_flow_cot
# from prompts.transaction_behaviour_templates import transaction_behavior_zero_shot, transaction_behavior_few_shot, transaction_behavior_cot
# from prompts.saving_position_templates import savings_position_zero_shot, savings_position_few_shot, savings_position_cot
from prompts.recommendations_templates import recommendations_zero_shot, recommendations_few_shot, recommendations_cot
from model.prompt_ethical import ethical_check, tokenizer, model
from model.prompt_similarity import get_embedding, similarity_score, embedding_model
import os
import json
import calendar


class ReportGenerator:
    """Class for generating financial reports using different prompting techniques."""
    def __init__(self, llm, user_id=None, year=None, month=None):
        self.llm = llm
        self.user_id = user_id
        self.year = year
        self.month = month if isinstance(month, str) else calendar.month_name[month] if month else None
        self.prompt_templates = self._load_prompt_templates()
        
    def _load_prompt_templates(self):
        """Load all prompt templates for different components and approaches."""
        return {
            "executive_summary": {
                "zero_shot": PromptTemplate(input_variables=["transaction_summary"], template=executive_summary_zero_shot),
                "few_shot": PromptTemplate(input_variables=["transaction_summary"], template=executive_summary_few_shot),
                "chain_of_thought": PromptTemplate(input_variables=["transaction_summary"], template=executive_summary_cot)
            },
            # "cash_flow": {
            #     "zero_shot": PromptTemplate(input_variables=["transaction_summary"], template=cash_flow_zero_shot),
            #     "few_shot": PromptTemplate(input_variables=["transaction_summary"], template=cash_flow_few_shot),
            #     "chain_of_thought": PromptTemplate(input_variables=["transaction_summary"], template=cash_flow_cot)
            # },
            # "transaction_behaviour": {
            #     "zero_shot": PromptTemplate(input_variables=["transaction_summary"], template=transaction_behavior_zero_shot),
            #     "few_shot": PromptTemplate(input_variables=["transaction_summary"], template=transaction_behavior_few_shot),
            #     "chain_of_thought": PromptTemplate(input_variables=["transaction_summary"], template=transaction_behavior_cot)
            # },
            # "savings_position": {
            #     "zero_shot": PromptTemplate(input_variables=["transaction_summary"], template=savings_position_zero_shot),
            #     "few_shot": PromptTemplate(input_variables=["transaction_summary"], template=savings_position_few_shot),
            #     "chain_of_thought": PromptTemplate(input_variables=["transaction_summary"], template=savings_position_cot)
            # },
            "recommendations": {
                "zero_shot": PromptTemplate(input_variables=["transaction_summary"], template=recommendations_zero_shot),
                "few_shot": PromptTemplate(input_variables=["transaction_summary"], template=recommendations_few_shot),
                "chain_of_thought": PromptTemplate(input_variables=["transaction_summary"], template=recommendations_cot)
            }
        }
    
    def _best_approach(self, component_name, transaction_summary):
        """Select the best prompting approach for a component based on similarity and ethical evaluation."""
        component_prompts = self.prompt_templates[component_name]
        best_similarity = float('-inf')
        chosen_approach = None
        
        for approach_name, prompt_template in component_prompts.items():
            # Generate and get LLM output
            chain = prompt_template | self.llm
            llm_result = chain.invoke({"transaction_summary": transaction_summary})
            llm_output_text = str(llm_result.content)
            
            # Perform ethical check before similarity evaluation
            ethical_result = ethical_check(llm_output_text)
            if ethical_result["ethical_flag"] != "Safe":
                similarity = -1.0  # Penalize unethical content with worst cosine value
            else:
                # Embed template and output then calculate cosine similarity
                embeddings = get_embedding([prompt_template.template, llm_output_text], embedding_model)
                embedding_template = embeddings[0]
                embedding_output = embeddings[1]
                similarity = similarity_score(embedding_template, embedding_output)
            
            if similarity > best_similarity:
                best_similarity = similarity
                chosen_approach = approach_name
        
        return chosen_approach or "chain_of_thought"  # Fallback to chain_of_thought if no approach selected
    
    def generate_report(self, transaction_summary, approach=None):
        """
        Generate a full financial report using the specified prompting approach or select the best approach.
        
        Args:
            transaction_summary: The transaction data for analysis
            approach: Optional dictionary of approaches to use for each component.
                     If None, will select the best approach for each component.
            
        Returns:
            A structured report with metadata, components, and evaluation metrics
        """
        # If no approach specified, select best approach for each component
        if approach is None:
            approach = {}
            for component_name in self.prompt_templates.keys():
                approach[component_name] = self._best_approach(component_name, transaction_summary)
        
        # Generate each component using the appropriate approach
        report_components = {}
        component_metrics = {}
        
        for component, component_prompts in self.prompt_templates.items():
            component_approach = approach.get(component, "chain_of_thought")
            prompt_template = component_prompts[component_approach]
            
            # Create a chain and invoke it
            chain = prompt_template | self.llm
            result = chain.invoke({"transaction_summary": transaction_summary})
            llm_output = result.content
            
            # Store the component output
            report_components[component] = llm_output
            
            # Calculate metrics for this component
            ethical_result = ethical_check(llm_output)
            
            # Calculate similarity between template and output
            embeddings = get_embedding([prompt_template.template, llm_output], embedding_model)
            template_similarity = similarity_score(embeddings[0], embeddings[1])
            
            component_metrics[component] = {
                "ethical_flag": ethical_result["ethical_flag"],
                "confidence": float(f"{ethical_result['confidence']:.2f}"),
                "similarity_score": float(f"{template_similarity:.2f}")
            }
        
        # Create the structured report with metadata and metrics
        return {
            "metadata": {
                "user_id": self.user_id,
                "year": self.year,
                "month": self.month
            },
            "report_components": report_components,
            "evaluation": component_metrics
        }

    def save_report(self, report, output_folder="reports"):
        """Save the report to text and JSON files."""
        metadata = report["metadata"]
        user_id = metadata["user_id"]
        year = metadata["year"]
        month = metadata["month"]
        
        # Create the directory structure
        year_folder = os.path.join(output_folder, str(year))
        month_folder = os.path.join(year_folder, month)
        
        # Create all necessary directories
        for folder in [year_folder, month_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
            
        # Save report to JSON file
        report_json = f"{user_id}_{year}_{month}.json"
        json_path = os.path.join(month_folder, report_json)
        with open(json_path, "w") as f_json:
            json.dump(report, f_json, indent=4)