from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("autopilot-ai/EthicalEye", use_fast=False) # Add use_fast=False due to error
model = AutoModelForSequenceClassification.from_pretrained("autopilot-ai/EthicalEye")

def ethical_check(text: str) -> dict:
    """Check if the given text contains any ethical concerns.
    
    Args:
        text (str): The text to check for ethical concerns
        
    Returns:
        dict: A dictionary containing the ethical check results with keys:
            - flag (str): Whether the text is considered Safe or not
            - confidence (float): The confidence score of the classification
    """
    # Tokenize the input text
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    
    # Make predictions
    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get the logits and apply softmax to get probabilities
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1)
    
    # Get the predicted class and its probability
    predicted_class_id = torch.argmax(logits, dim=1).item()
    confidence = probabilities[0][predicted_class_id].item()
    predicted_label = model.config.id2label[predicted_class_id]
    
    return {
        "ethical_flag": predicted_label,
        "confidence": confidence,
    }

# if __name__ == "__main__":
#     text_to_classify = """
#     Financial Recommendations\n\nBased on your transaction summary, here are personalized recommendations to enhance your financial health:\n\n1. **Establish a Dedicated Savings Plan**: While your spending-to-income ratio of 82.11% indicates you're living within your means, you could optimize your savings. Consider automatically transferring 10-15% of incoming funds to a high-yield savings account to build a stronger financial cushion.\n\n2. **Track Spending Categories**: Your transactions show high volume (930 monthly transactions) but lack categorization. Use a budgeting app to categorize expenses and identify potential areas to reduce discretionary spending, particularly in social/entertainment categories suggested by your \"lush drinkers\" tag.\n\n3. **Diversify Payment Methods**: You're exclusively using \"send money\" for transactions. Consider using credit cards with rewards programs for certain purchases to earn cashback or points, while maintaining your current spending levels.\n\n4. **Create a \"Fun Fund\"**: Given your \"lush drinkers\" tag, allocate a specific monthly budget for social activities. This allows you to enjoy your lifestyle while setting clear boundaries on entertainment spending.\n\n5. **Review Transaction Frequency**: With an average of 31 transactions daily, consider consolidating purchases where possible to reduce impulse spending and improve expense tracking.
#     """
#     result = ethical_check(text_to_classify)
#     print(f"Result: {result}")