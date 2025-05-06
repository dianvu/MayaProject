savings_position_zero_shot = """
Given the following transaction summary:
{transaction_summary}

Generate an analysis of the user's savings and financial position, including spending as a percentage of income, potential savings amount, and an assessment of their financial health. Output only the savings and financial position analysis text.
"""

savings_position_few_shot = """
Here are a couple of examples of transaction summaries and their savings and financial position analyses:

Example 1:
Transaction Summary: User abc123def monthly transactions Summary (Timestamp: 2025-03) 
- Total spend is 600 with 8 transactions
- Spending methods include send money with 50.00%, qr with 37.50%, maya shop with 12.50%
- Total cash-in is 1000 with 2 transactions
- Cash-in methods include bank transfer with 75.00%, send money with 25.00%
Savings & Financial Position Analysis:
* Spending as % of Income: 60%
* Potential Savings: ₱400
Your spending represents 60% of your income this month, allowing for a 40% savings rate. This is an excellent savings percentage that exceeds the recommended 20% threshold. With consistent saving at this level, you can build a robust emergency fund and achieve long-term financial goals.

Example 2:
Transaction Summary: User ghi456jkl monthly transactions Summary (Timestamp: 2025-02) 
- Total spend is 800 with 10 transactions 
- Total cash-in is 600 with 3 transactions
Savings & Financial Position Analysis:
* Spending as % of Income: 133.33%
* Potential Savings: -₱200
Your spending exceeds your income by 33.33% this month, resulting in a negative savings position. This suggests you may be using savings or credit to cover expenses. If this pattern continues, it could lead to financial strain and depleted reserves. Consider reviewing expenses to bring them in line with income.

Now, analyze the following transaction summary:
{transaction_summary}

Generate a savings and financial position analysis based on the examples. Output only the savings and financial position analysis text.
"""

savings_position_cot = """
Analyze the following transaction summary step-by-step to generate a savings and financial position analysis:
{transaction_summary}

Thought Process:
1. Extract the total cash-in (income) amount.
2. Extract the total spend amount.
3. Calculate spending as a percentage of income: (Total Spend ÷ Total Cash-In) × 100.
4. Calculate potential savings: Total Cash-In - Total Spend.
5. Evaluate the savings rate against general financial guidelines (e.g., 20% is often recommended).
6. Consider the implications of the savings rate for the user's financial health.
7. Take into account any user tags or patterns that might provide context for the financial position.
8. Assess overall financial health based on the spending-to-income ratio and savings potential.

Based on the step-by-step analysis, generate an analysis of the user's savings and financial position, including spending as a percentage of income, potential savings amount, and an assessment of their financial health. Output only the savings and financial position analysis text.
"""