## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import read_data_tool

## Task 1: Verify the document is a valid financial document
verification = Task(
    description=(
        "Read the uploaded financial document at path '{file_path}' using the Financial Document Reader tool.\n"
        "Verify that it is a legitimate financial document (e.g., 10-K, 10-Q, earnings report, annual report).\n"
        "Identify the document type, the company name, the reporting period, and key sections present.\n"
        "If the document is not a financial report, clearly state that and explain why."
    ),
    expected_output=(
        "A structured verification report containing:\n"
        "- Document type (e.g., Quarterly Earnings Update, Annual Report, 10-K)\n"
        "- Company name and ticker symbol\n"
        "- Reporting period covered\n"
        "- Key sections identified (income statement, balance sheet, cash flow, etc.)\n"
        "- Verification status: VALID or INVALID with reasoning"
    ),
    agent=verifier,
    tools=[read_data_tool],
    async_execution=False,
)

## Task 2: Analyze the financial document based on user query
analyze_financial_document = Task(
    description=(
        "Thoroughly analyze the financial document at path '{file_path}' to answer the user's query: {query}\n"
        "Use the Financial Document Reader tool with the path '{file_path}' to read the document.\n"
        "Extract and interpret key financial metrics including:\n"
        "- Revenue, net income, and profit margins\n"
        "- Cash flow from operations, investing, and financing\n"
        "- Key balance sheet items (total assets, liabilities, equity)\n"
        "- Year-over-year or quarter-over-quarter comparisons if available\n"
        "- Any notable trends, risks, or opportunities mentioned in the report\n"
        "Cite specific numbers and page references from the document."
    ),
    expected_output=(
        "A comprehensive financial analysis report with:\n"
        "- Executive summary addressing the user's query\n"
        "- Key financial metrics with actual numbers from the document\n"
        "- Trend analysis and comparisons (YoY/QoQ where available)\n"
        "- Notable strengths and concerns identified\n"
        "- Data-backed conclusions"
    ),
    agent=financial_analyst,
    tools=[read_data_tool],
    async_execution=False,
)

## Task 3: Provide investment recommendations
investment_analysis = Task(
    description=(
        "Based on the financial analysis of the document at '{file_path}', provide well-reasoned investment recommendations.\n"
        "Consider the user's query context: {query}\n"
        "Evaluate:\n"
        "- The company's financial health and growth trajectory\n"
        "- Valuation metrics (P/E, P/B, EV/EBITDA if calculable)\n"
        "- Competitive positioning and market conditions\n"
        "- Short-term and long-term investment outlook\n"
        "Always include appropriate disclaimers that this is not personalized financial advice."
    ),
    expected_output=(
        "A structured investment recommendation including:\n"
        "- Investment thesis (bull case and bear case)\n"
        "- Key financial ratios and what they indicate\n"
        "- Potential catalysts and risks\n"
        "- Recommendation with supporting rationale\n"
        "- Disclaimer: This analysis is for informational purposes only and does not constitute financial advice"
    ),
    agent=investment_advisor,
    tools=[read_data_tool],
    async_execution=False,
)

## Task 4: Assess risks
risk_assessment = Task(
    description=(
        "Perform a thorough risk assessment based on the financial document at '{file_path}'.\n"
        "Consider the user's query context: {query}\n"
        "Evaluate:\n"
        "- Credit risk (debt levels, interest coverage, credit ratings)\n"
        "- Market risk (revenue concentration, competitive threats)\n"
        "- Operational risk (supply chain, regulatory, management)\n"
        "- Liquidity risk (current ratio, quick ratio, cash reserves)\n"
        "Categorize each risk by severity (High/Medium/Low) and likelihood."
    ),
    expected_output=(
        "A structured risk assessment report containing:\n"
        "- Risk matrix with severity and likelihood ratings\n"
        "- Detailed analysis of each risk category\n"
        "- Key risk indicators with actual numbers from the document\n"
        "- Mitigation factors already in place\n"
        "- Overall risk rating with justification"
    ),
    agent=risk_assessor,
    tools=[read_data_tool],
    async_execution=False,
)
