cash_flow_zero_shot = """
Given the following transaction summary:
{transaction_summary}

Generate a comprehensive cash flow analysis that includes total cash-in, total spend, breakdown by payment methods, and net cash position. Output only the cash flow analysis text.
"""

cash_flow_few_shot = """
Here are a couple of examples of transaction summaries and their cash flow analyses:

Example 1:
Transaction Summary: User abc123def monthly transactions Summary (Timestamp: 2025-03) 
- Total spend is 600 with 8 transactions
- Spending methods include send money with 50.00%, qr with 37.50%, maya shop with 12.50%
- Total cash-in is 1000 with 2 transactions
- Cash-in methods include bank transfer with 75.00%, send money with 25.00%
Cash Flow Analysis: 
* Total Cash-In: ₱1000
   * Bank Transfers: ₱750 (75%)
   * Send Money: ₱250 (25%)
* Total Spend: ₱600
   * Send Money: ₱300 (50%)
   * QR Payments: ₱225 (37.5%)
   * Maya Shop: ₱75 (12.5%)
* Net Cash Position (Cash-In - Spend): ₱400
Primary cash inflow is through bank transfers, with send money as a secondary source. Spending is distributed across multiple payment methods, with send money being the dominant method.

Example 2:
Transaction Summary: User ghi456jkl monthly transactions Summary (Timestamp: 2025-02) 
- Total spend is 800 with 10 transactions 
- Spending methods include qr with 60.00%, send money with 30.00%, maya shop with 10.00%
- Total cash-in is 600 with 3 transactions
- Cash-in methods include bank transfer with 50.00%, send money with 50.00%
Cash Flow Analysis:
* Total Cash-In: ₱600
   * Bank Transfers: ₱300 (50%)
   * Send Money: ₱300 (50%)
* Total Spend: ₱800
   * QR Payments: ₱480 (60%)
   * Send Money: ₱240 (30%)
   * Maya Shop: ₱80 (10%)
* Net Cash Position (Cash-In - Spend): -₱200
Cash inflows are evenly split between bank transfers and send money. Spending primarily occurs through QR payments, followed by send money. There is a negative cash flow position, indicating more spending than income this month.

Now, analyze the following transaction summary:
{transaction_summary}

Generate a comprehensive cash flow analysis based on the examples. Output only the cash flow analysis text.
"""

cash_flow_cot = """
Analyze the following transaction summary step-by-step to generate a cash flow analysis:
{transaction_summary}

Thought Process:
1. Extract the total cash-in amount and number of transactions.
2. Identify the cash-in methods and their percentage distributions.
3. Calculate the actual amount for each cash-in method by multiplying the total cash-in by the percentage.
4. Extract the total spend amount and number of transactions.
5. Identify the spending methods and their percentage distributions.
6. Calculate the actual amount for each spending method by multiplying the total spend by the percentage.
7. Calculate the net cash position by subtracting total spend from total cash-in.
8. Note any significant patterns or observations about cash flow sources and usage.

Based on the step-by-step analysis, generate a comprehensive cash flow analysis that includes total cash-in, total spend, breakdown by payment methods, and net cash position. Output only the cash flow analysis text.
"""