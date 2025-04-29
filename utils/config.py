from langchain_anthropic import ChatAnthropic

def anthropic_llm():
    llm = ChatAnthropic(
        api_key = "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",
        model_name = "claude-3-7-sonnet-20250219",
        temperature = 0.0
    )
    return llm