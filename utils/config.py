import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

def anthropic_llm():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model_name = os.getenv("ANTHROPIC_MODEL_NAME")
    
    llm = ChatAnthropic(
        api_key=api_key,
        model_name=model_name,
        temperature=0.0
    )
    return llm