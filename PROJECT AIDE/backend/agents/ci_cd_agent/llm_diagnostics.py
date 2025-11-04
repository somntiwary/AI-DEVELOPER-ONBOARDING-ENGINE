"""
llm_diagnostics.py
-------------------
Part of the CI/CD Agent module.

Purpose:
- Analyze CI/CD pipeline logs and errors.
- Diagnose likely root causes of build/test failures.
- Suggest fixes and optimizations using LLM or RAG-based reasoning.
- Integrate seamlessly with GitHub Actions, Jenkins, or GitLab CI logs.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Weaviate
from langchain_openai import OpenAIEmbeddings

# Optional: integrate with Weaviate for context-based retrieval
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------
# Helper: Load LLM / RAG Setup
# ---------------------------
def load_llm() -> ChatOpenAI:
    """Initializes the LLM (e.g., OpenAI GPT or similar)."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing OPENAI_API_KEY in environment variables.")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=api_key)


def load_weaviate_client():
    """Connect to Weaviate for retrieving relevant CI/CD docs or examples."""
    weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    try:
        embeddings = OpenAIEmbeddings()
        vectorstore = Weaviate.from_existing_index(weaviate_url, embeddings)
        return vectorstore
    except Exception as e:
        logger.warning(f"Weaviate connection failed: {e}")
        return None


# ---------------------------
# Diagnostics Class
# ---------------------------
class LLMDiagnostics:
    """
    Core diagnostics engine that:
    - Analyzes CI/CD logs and error traces.
    - Provides probable causes.
    - Suggests fixes based on project context.
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.llm = load_llm()
        self.weaviate_client = load_weaviate_client()

    # -------------------------------------
    # Step 1: Extract Context from Logs
    # -------------------------------------
    def extract_relevant_log_snippet(self, log_content: str, max_lines: int = 50) -> str:
        """
        Extracts the most relevant portion of CI/CD logs for analysis.
        Keeps last few lines around the error message.
        """
        logger.info(f"Extracting log snippet from {len(log_content)} characters of log content")
        lines = log_content.splitlines()
        logger.debug(f"Log content split into {len(lines)} lines")
        
        for i, line in enumerate(lines):
            if "error" in line.lower() or "failed" in line.lower():
                start = max(0, i - 20)
                end = min(len(lines), i + 30)
                snippet = "\n".join(lines[start:end])
                logger.info(f"Found error context at line {i}, extracted {end-start} lines around it")
                return snippet
        
        logger.info(f"No error keywords found, returning last {max_lines} lines")
        return "\n".join(lines[-max_lines:])  # fallback: last N lines

    # -------------------------------------
    # Step 2: Diagnose Failure using LLM
    # -------------------------------------
    def diagnose(self, log_content: str, ci_type: str = "GitHub Actions") -> Dict[str, Any]:
        """
        Analyze CI/CD failure logs and return diagnostic insights.
        """
        logger.info(f"Starting diagnosis for {ci_type} with {len(log_content)} characters of log content")
        
        try:
            snippet = self.extract_relevant_log_snippet(log_content)
            logger.debug(f"Extracted snippet length: {len(snippet)} characters")

            prompt = PromptTemplate(
                input_variables=["ci_type", "log_snippet"],
                template=(
                    "You are an expert DevOps AI assisting with diagnosing CI/CD issues.\n\n"
                    "CI/CD Type: {ci_type}\n"
                    "Below is the error log snippet:\n\n"
                    "----- LOG START -----\n"
                    "{log_snippet}\n"
                    "----- LOG END -----\n\n"
                    "Analyze this log and provide:\n"
                    "1. Root Cause Summary\n"
                    "2. Probable Failure Step (build/test/deploy)\n"
                    "3. Suggested Fixes (concise actionable commands)\n"
                    "4. Severity (Low, Medium, High)\n"
                    "5. One-line Explanation for Developer\n\n"
                    "Respond in JSON format."
                )
            )

            logger.info("Invoking LLM for diagnosis")
            chain = prompt | self.llm | StrOutputParser()
            response = chain.invoke({"ci_type": ci_type, "log_snippet": snippet})
            logger.debug(f"LLM response length: {len(response)} characters")

            try:
                diagnosis = json.loads(response)
                logger.info("Successfully parsed LLM response as JSON")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                diagnosis = {"raw_response": response, "parse_error": str(e)}

            logger.info("LLM diagnosis completed successfully")
            return diagnosis
            
        except Exception as e:
            logger.error(f"Error during diagnosis: {e}")
            return {
                "error": str(e),
                "status": "failed",
                "message": "Diagnosis failed due to an unexpected error"
            }

    # -------------------------------------
    # Step 3: Enrich with RAG Context
    # -------------------------------------
    def provide_context_help(self, query: str) -> Optional[str]:
        """
        Uses RAG (Weaviate + LLM) to fetch contextual guidance or fixes
        from prior CI/CD knowledge or documentation.
        """
        if not self.weaviate_client:
            return "No vector DB available for contextual lookup."

        try:
            docs = self.weaviate_client.similarity_search(query, top_k=3)
            context = "\n\n".join([d.page_content for d in docs])
            prompt = PromptTemplate(
                input_variables=["query", "context"],
                template=(
                    "You are a CI/CD assistant AI.\n"
                    "Based on the developer’s query and retrieved context, "
                    "explain the possible causes and solutions.\n\n"
                    "Query: {query}\n\n"
                    "Context:\n{context}\n\n"
                    "Provide a concise yet clear explanation."
                ),
            )
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({"query": query, "context": context})
        except Exception as e:
            logger.error(f"RAG context lookup failed: {e}")
            return None


# ---------------------------
# Example Usage
# ---------------------------
if __name__ == "__main__":
    example_logs = """
    Step 3/5 : RUN npm install
    npm ERR! code ERESOLVE
    npm ERR! Could not resolve dependency: peer react@"^18.0.0" from react-dom@17.0.2
    Error: Process completed with exit code 1
    """

    diag = LLMDiagnostics(project_path="C:/path/to/project")
    result = diag.diagnose(example_logs, ci_type="GitHub Actions")
    print(json.dumps(result, indent=2))

    # Optional RAG help
    print("\nContextual Help:\n", diag.provide_context_help("npm dependency conflict"))
