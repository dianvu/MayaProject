recommendations_zero_shot = """
Given the following transaction summary:
{transaction_summary}

Generate personalized financial recommendations for the user based on their spending and income patterns. Include 3-5 actionable suggestions that can help improve their financial health. Format numbers with proper spacing and use consistent formatting. Output only the recommendations text.
"""

recommendations_few_shot = """
Here are a couple of examples of transaction summaries and their personalized recommendations:

Example 1:
Transaction Summary: User abc123def monthly transactions Summary (Timestamp: 2025-03) 
- Total spend is 600 with 8 transactions
- Spending methods include send money with 50.00%, qr with 37.50%, maya shop with 12.50%
- Total cash-in is 1000 with 2 transactions
- Cash-in methods include bank transfer with 75.00%, send money with 25.00%
- User tags: budget conscious, digital native, investor
Recommendations:
1. **Maintain Current Savings Rate**: Continue saving 40% of your income to build wealth and reach long-term financial goals faster.
2. **Categorize Send Money Transactions**: With 50% of spending via send money, track these transfers by purpose (bills, investments, personal) to gain better visibility into your spending patterns.
3. **Diversify Income Sources**: While your savings rate is healthy, having 75% of income from a single source (bank transfers) presents concentration risk. Consider developing additional income streams.
4. **Set Up Automatic Investments**: As an investor, consider automating a portion of your savings into investment accounts to maximize returns on your healthy savings rate.

Example 2:
Transaction Summary: User ghi456jkl monthly transactions Summary (Timestamp: 2025-02) 
- Total spend is 800 with 10 transactions 
- Spending methods include qr with 60.00%, send money with 30.00%, maya shop with 10.00%
- Total cash-in is 600 with 3 transactions
- Cash-in methods include bank transfer with 50.00%, send money with 50.00%
- User tags: frequent shopper, entertainment seeker
Recommendations:
1. **Create a Spending Budget**: Your spending exceeds your income by 33%. Establish a monthly budget that aligns with your actual income to avoid financial strain.
2. **Review QR Payment Transactions**: With 60% of spending through QR payments, review these transactions to identify potential discretionary purchases that could be reduced.
3. **Build an Emergency Fund**: Work toward saving at least 3-6 months of essential expenses to avoid relying on credit during income fluctuations.
4. **Increase Income Sources**: Explore opportunities to supplement your current income streams to better support your spending habits and lifestyle.
5. **Track Entertainment Expenses**: As an entertainment seeker, specifically categorize these expenses to ensure they remain a sustainable portion of your budget.

Now, analyze the following transaction summary:
{transaction_summary}

Generate personalized recommendations based on the examples. Format numbers with proper spacing and use consistent formatting. Output only the recommendations text.
"""

recommendations_cot = """
Analyze the following transaction summary step-by-step to generate personalized financial recommendations:
{transaction_summary}

Thought Process:
1. Review the user's spending patterns and payment methods.
2. Analyze the user's income sources and total cash-in amount.
3. Calculate the savings rate and assess overall financial health.
4. Consider the user's tags and what they reveal about financial habits and priorities.
5. Identify areas where the user could improve financial management.
6. Consider specific recommendations for:
   a. Spending patterns and potential optimizations
   b. Income diversification or enhancement
   c. Savings targets and strategies
   d. Financial tracking and categorization
   e. Alignment with user tags and apparent priorities
7. Formulate 3-5 specific, actionable recommendations tailored to the user's financial situation.
8. Ensure recommendations are specific, measurable, achievable, relevant, and time-bound where possible.
9. Format all numbers with proper spacing and use consistent formatting throughout.

Based on the step-by-step analysis, generate personalized financial recommendations for the user based on their spending and income patterns. Include 3-5 actionable suggestions that can help improve their financial health. Format numbers with proper spacing and use consistent formatting. Output only the recommendations text.
"""