## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import tool, SerperDevTool

## Creating search tool
search_tool = SerperDevTool()

## Creating custom pdf reader tool using @tool decorator
@tool("Financial Document Reader")
def read_data_tool(path: str = 'data/sample.pdf') -> str:
    """Tool to read data from a PDF file and return its full text content.

    Args:
        path (str, optional): Path of the pdf file. Defaults to 'data/sample.pdf'.

    Returns:
        str: Full Financial Document text
    """
    from pypdf import PdfReader

    reader = PdfReader(path)
    full_report = ""
    for page in reader.pages:
        content = page.extract_text() or ""

        # Remove extra whitespace and format properly
        while "\n\n" in content:
            content = content.replace("\n\n", "\n")

        full_report += content + "\n"

    return full_report
