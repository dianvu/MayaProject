executive_summary_zero_shot = """
Given the following transaction summary:
{transaction_summary}

Generate a concise executive summary highlighting key financial insights. Output only the summary text.
"""

executive_summary_few_shot = """
Here are a couple of examples of financial summaries and their executive summaries.

Example 1:
Transaction Summary: User abc123def monthly transactions Summary (Timestamp: 2025-03) 
- Total spend is 600 with 8 transactions
- Spending methods include send money with 50.00%, qr with 37.50%, maya shop with 12.50%
- Total cash-in is 1000 with 2 transactions
- Cash-in methods include bank transfer with 75.00%, send money with 25.00%
- Spending accounts for 50% of total cash-in.
Executive Summary: You spend half of your income in this month- March. Indicating moderate spending habits relative to cash inflow.

Example 2:
Transaction Summary: User ghi456jkl monthly transactions Summary (Timestamp: 2025-02) - Total spend is 800 with 10 transactions - Total cash-in is 600 with 3 transactions - Spending exceeds cash-in.
Executive Summary: Spending amount exceeded cash inflow in this month- February. Suggesting potential financial strain.

Now, analyze the following transaction summary:
{transaction_summary}

Generate a concise executive summary highlighting key financial insights based on the examples. Output only the summary text.
"""

executive_summary_cot = """
Analyze the following transaction summary step-by-step to generate an executive summary:
{transaction_summary}

Thought Process:
1. Identify the user and timestamp: User d962c87b..., Timestamp 2025-04.
2. Note user tags: professional hustlers, loan and gaming, prudent planners. These might be contradictory or indicate diverse activities.
3. Extract Total Spend: 680.4237 across 8 transactions.
4. Extract Total Cash-in: 965.5426 across 4 transactions.
5. Calculate Spend vs Cash-in Ratio: 680.4237 / 965.5426 = ~70.47%.
6. Analyze Spending Methods: Dominated by 'send money' (50%) and 'qr' (37.5%). Maya shop is minor (12.5%).
7. Analyze Cash-in Methods: Dominated by 'bank transfer' (75%). 'send money' is smaller (25%).
8. Synthesize Insights: The user spent significantly less than their cash-in (approx. 70%), suggesting a potential surplus or savings for the month. Spending is diverse (send money, QR, shop). Cash-in is primarily via bank transfers. The user tags present a mixed profile (hustler/gaming vs. prudent planner).

Based on the step-by-step analysis, generate a concise executive summary. Output only the summary text.
"""