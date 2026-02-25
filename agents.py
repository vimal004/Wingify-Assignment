## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM

from tools import search_tool, read_data_tool

### Loading LLM — use Gemini via CrewAI's LLM class
llm = LLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
)

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Analyze the user's financial document and provide clear, data-driven insights in response to: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You are a seasoned financial analyst with over 15 years of experience "
        "in corporate finance, equity research, and financial statement analysis. "
        "You carefully read financial reports, extract key metrics (revenue, net income, "
        "margins, cash flow, debt ratios), and provide objective, well-supported analysis. "
        "You always cite specific numbers from the documents you review."
    ),
    tools=[read_data_tool],
    llm=llm,
    max_iter=15,
    allow_delegation=False,
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal="Verify that the uploaded file is a legitimate financial document and extract its metadata.",
    verbose=True,
    memory=True,
    backstory=(
        "You are a meticulous document compliance specialist with expertise in "
        "identifying financial document types (10-K, 10-Q, annual reports, earnings releases). "
        "You check for required sections, data integrity, and document authenticity. "
        "You flag any anomalies or missing information clearly."
    ),
    tools=[read_data_tool],
    llm=llm,
    max_iter=15,
    allow_delegation=False,
)

# Creating an investment advisor agent
investment_advisor = Agent(
    role="Investment Research Analyst",
    goal="Based on the financial analysis, provide well-reasoned investment recommendations with proper risk disclaimers.",
    verbose=True,
    memory=True,
    backstory=(
        "You are a CFA-certified investment analyst with deep expertise in "
        "fundamental analysis and portfolio construction. You translate financial data "
        "into actionable investment insights while always including appropriate risk "
        "disclaimers and noting that past performance does not guarantee future results. "
        "You consider multiple scenarios and present balanced recommendations."
    ),
    llm=llm,
    max_iter=15,
    allow_delegation=False,
)

# Creating a risk assessor agent
risk_assessor = Agent(
    role="Financial Risk Assessment Specialist",
    goal="Evaluate the financial risks present in the document and provide a structured risk assessment.",
    verbose=True,
    memory=True,
    backstory=(
        "You are a risk management professional with experience in credit risk, "
        "market risk, and operational risk analysis. You use quantitative metrics "
        "(debt-to-equity, current ratio, interest coverage) alongside qualitative factors "
        "to produce balanced and actionable risk assessments. "
        "You categorize risks by severity and likelihood."
    ),
    llm=llm,
    max_iter=15,
    allow_delegation=False,
)
