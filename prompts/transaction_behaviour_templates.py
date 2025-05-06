transaction_behavior_zero_shot = """
Given the following transaction summary:
{transaction_summary}

Generate a detailed analysis of the user's transaction behavior, including total number of transactions, breakdown between cash-in and spending transactions, top spending categories, and observations about transaction patterns. Output only the transaction behavior analysis text.
"""

transaction_behavior_few_shot = """
Here are a couple of examples of transaction summaries and their transaction behavior analyses:

Example 1:
Transaction Summary: User abc123def monthly transactions Summary (Timestamp: 2025-03) 
- Total spend is 600 with 8 transactions
- Spending methods include send money with 50.00%, qr with 37.50%, maya shop with 12.50%
- Total cash-in is 1000 with 2 transactions
- Cash-in methods include bank transfer with 75.00%, send money with 25.00%
Transaction Behavior Analysis:
* Total Transactions: 10
   * Cash-in: 2 transactions
   * Spending: 8 transactions
* Top Spending Categories:
   1. Send Money – ₱300
   2. QR Payments – ₱225
   3. Maya Shop – ₱75
The user conducted few cash-in transactions but more frequent spending transactions. Their preference for send money suggests regular peer-to-peer transfers, possibly for bills or shared expenses. QR payments indicate consistent in-person purchasing.

Example 2:
Transaction Summary: User ghi456jkl monthly transactions Summary (Timestamp: 2025-02) 
- Total spend is 800 with 10 transactions 
- Spending methods include qr with 60.00%, send money with 30.00%, maya shop with 10.00%
- Total cash-in is 600 with 3 transactions
- Cash-in methods include bank transfer with 50.00%, send money with 50.00%
Transaction Behavior Analysis:
* Total Transactions: 13
   * Cash-in: 3 transactions
   * Spending: 10 transactions
* Top Spending Categories:
   1. QR Payments – ₱480
   2. Send Money – ₱240
   3. Maya Shop – ₱80
The user shows a preference for QR payments, suggesting frequent retail or merchant transactions. With spending transactions occurring more than three times as often as cash-in transactions, the user appears to make regular smaller purchases rather than bulk spending.

Now, analyze the following transaction summary:
{transaction_summary}

Generate a detailed transaction behavior analysis based on the examples. Output only the transaction behavior analysis text.
"""

transaction_behavior_cot = """
Analyze the following transaction summary step-by-step to generate a transaction behavior analysis:
{transaction_summary}

Thought Process:
1. Count the total number of transactions from both cash-in and spending.
2. Separate transactions into cash-in and spending categories.
3. Identify the top spending categories by amount.
4. Calculate actual spending amounts for each category using percentages and total spend.
5. Examine the frequency and value patterns of transactions.
6. Consider what the transaction patterns reveal about the user's financial habits.
7. Look for any unusual or notable transaction patterns.
8. Consider how the user's tags might relate to their transaction behavior.

Based on the step-by-step analysis, generate a detailed analysis of the user's transaction behavior, including total number of transactions, breakdown between cash-in and spending transactions, top spending categories, and observations about transaction patterns. Output only the transaction behavior analysis text.
"""