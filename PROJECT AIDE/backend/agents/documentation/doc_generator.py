# doc_generator.py
import os
import json
import requests
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# ==============================
# 🔐 OpenRouter Model Config
# ==============================
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

LLM_MODELS = [
    {
        "name": "DeepSeek R1",
        "model": "deepseek/deepseek-r1:free",
        "api_key": "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"
    },
    {
        "name": "Meta LLaMA 3.3",
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "api_key": "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"
    },
    {
        "name": "Google Gemma",
        "model": "google/gemma-3n-e4b-it:free",
        "api_key": "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"
    },
    {
        "name": "DeepSeek Chat v3",
        "model": "deepseek/deepseek-chat-v3.1:free",
        "api_key": "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"
    }
]

# ==============================
# ⚙️ LLM Call Function
# ==============================
def call_openrouter_llm(prompt: str, temperature: float = 0.4, max_tokens: int = 800) -> str:
    """
    Calls one of the available OpenRouter models in fallback order until success.
    """
    for i, llm in enumerate(LLM_MODELS):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm['api_key']}"
        }
        payload = {
            "model": llm["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(OPENROUTER_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                # Handle Unicode characters properly
                return content.encode('utf-8', errors='replace').decode('utf-8')
            elif response.status_code == 429:
                print(f"[{llm['name']}] Rate limited, trying next model...")
                continue
            else:
                print(f"[{llm['name']}] Failed: {response.status_code} -> {response.text}")
        except Exception as e:
            print(f"[{llm['name']}] Error: {str(e)}")
            continue

    # If all LLMs fail, return a simple fallback response
    return "❌ All LLMs are currently unavailable due to rate limiting. Please try again in a few minutes, or consider using your own API keys for better reliability."


# ==============================
# 🧠 Core Doc Generator Class
# ==============================
class DocumentationAgent:
    """
    Documentation Agent that reads code/docs, summarizes, and generates missing documentation.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        if not self.base_path.exists():
            raise ValueError(f"Base path {self.base_path} does not exist.")
        
        # Create output directory for generated docs
        self.output_dir = self.base_path / "docs" / "auto_generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Collect docs
    # -------------------------
    def collect_docs(self) -> List[Path]:
        """
        Collects all text-based files (.py, .md, .txt, .rst, .yml, .yaml, .json) in the project.
        Excludes common directories like __pycache__, .git, node_modules, etc.
        """
        file_extensions = [".py", ".md", ".txt", ".rst", ".yml", ".yaml", ".json", ".toml"]
        excluded_dirs = {"__pycache__", ".git", "node_modules", ".venv", "venv", "env", ".pytest_cache", ".tox", "build", "dist"}
        
        collected_files = []
        for ext in file_extensions:
            for file_path in self.base_path.rglob(f"*{ext}"):
                # Skip files in excluded directories
                if any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                    continue
                # Skip hidden files
                if any(part.startswith('.') for part in file_path.parts if part != file_path.name):
                    continue
                collected_files.append(file_path)
        
        return sorted(collected_files)

    # -------------------------
    # Read file
    # -------------------------
    def read_file(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    def extract_docstrings(self, file_path: Path) -> List[Dict[str, str]]:
        """
        Extract docstrings from Python files.
        Returns list of dicts with 'function', 'class', 'docstring' keys.
        """
        if not file_path.suffix == ".py":
            return []
        
        content = self.read_file(file_path)
        docstrings = []
        
        # Simple regex to find function/class definitions with docstrings
        patterns = [
            (r'def\s+(\w+)\s*\([^)]*\):\s*\n\s*"""(.*?)"""', 'function'),
            (r'class\s+(\w+).*?:\s*\n\s*"""(.*?)"""', 'class'),
        ]
        
        for pattern, doc_type in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            for match in matches:
                name = match.group(1)
                docstring = match.group(2).strip()
                if docstring:
                    docstrings.append({
                        'type': doc_type,
                        'name': name,
                        'docstring': docstring,
                        'file': str(file_path.relative_to(self.base_path))
                    })
        
        return docstrings

    # -------------------------
    # Summarize file
    # -------------------------
    def summarize_file(self, file_path: Path) -> str:
        content = self.read_file(file_path)
        if not content.strip():
            return f"No content in {file_path.name}"
        prompt = f"Summarize this file for documentation:\n\nFile: {file_path.name}\n\n{content[:4000]}"
        summary = call_openrouter_llm(prompt)
        return summary

    # -------------------------
    # Generate README
    # -------------------------
    def generate_readme(self) -> str:
        """
        Generates a professional README for the project using all collected files.
        """
        docs = self.collect_docs()
        
        # Collect project information
        project_info = self._analyze_project_structure()
        
        # Extract docstrings from Python files
        all_docstrings = []
        for doc in docs:
            if doc.suffix == ".py":
                all_docstrings.extend(self.extract_docstrings(doc))
        
        # Build content for LLM
        combined_content = f"Project Structure:\n{project_info}\n\n"
        
        # Add key files content
        key_files = [d for d in docs if d.name in ["README.md", "main.py", "app.py", "requirements.txt", "package.json", "setup.py"]]
        for doc in key_files[:5]:  # limit to 5 key files
            content = self.read_file(doc)[:1500]
            combined_content += f"\n\n# {doc.name}\n{content}"
        
        # Add docstrings
        if all_docstrings:
            combined_content += "\n\n# Code Documentation\n"
            for ds in all_docstrings[:10]:  # limit to 10 docstrings
                combined_content += f"\n## {ds['type'].title()}: {ds['name']} (in {ds['file']})\n{ds['docstring']}\n"

        prompt = f"""Generate a complete and professional README.md for this project.
Here are code and documentation samples:

{combined_content[:10000]}

Include:
- Project overview and description
- Installation steps with requirements
- Usage examples and API documentation
- Project structure and key files
- Contributing guidelines
- License information (if available)
- Credits and acknowledgments

Make it professional, well-structured, and informative.
"""
        readme_text = call_openrouter_llm(prompt, temperature=0.5, max_tokens=2000)
        
        # Save the README
        readme_file = self.output_dir / "README_AUTO.md"
        readme_file.write_text(readme_text, encoding="utf-8")
        return str(readme_file)

    def _analyze_project_structure(self) -> str:
        """Analyze and describe the project structure."""
        structure = []
        
        # Get top-level directories and files
        for item in sorted(self.base_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                structure.append(f"📁 {item.name}/")
            elif item.is_file() and not item.name.startswith('.'):
                structure.append(f"📄 {item.name}")
        
        return "\n".join(structure)

    # -------------------------
    # Query documentation
    # -------------------------
    def generate_api_docs(self) -> str:
        """
        Generates API documentation from FastAPI routes and Python docstrings.
        """
        docs = self.collect_docs()
        api_info = []
        
        # Find FastAPI routes
        for doc in docs:
            if doc.suffix == ".py":
                content = self.read_file(doc)
                if "FastAPI" in content or "@app." in content or "@router." in content:
                    # Extract route information
                    routes = re.findall(r'@(?:app|router)\.(get|post|put|delete|patch)\("([^"]+)"', content)
                    for method, path in routes:
                        api_info.append(f"{method.upper()} {path}")
        
        # Extract docstrings for API functions
        api_docstrings = []
        for doc in docs:
            if doc.suffix == ".py":
                docstrings = self.extract_docstrings(doc)
                for ds in docstrings:
                    if any(keyword in ds['docstring'].lower() for keyword in ['api', 'endpoint', 'route', 'request', 'response']):
                        api_docstrings.append(ds)
        
        # Generate API documentation
        api_content = "API Endpoints:\n" + "\n".join(api_info) + "\n\n"
        if api_docstrings:
            api_content += "API Documentation:\n"
            for ds in api_docstrings:
                api_content += f"\n## {ds['name']} (in {ds['file']})\n{ds['docstring']}\n"
        
        prompt = f"""Generate comprehensive API documentation for this project.
Here is the API information:

{api_content}

Create professional API documentation including:
- Endpoint descriptions
- Request/response formats
- Authentication requirements
- Error handling
- Usage examples
"""
        api_docs = call_openrouter_llm(prompt, temperature=0.3, max_tokens=2000)
        
        # Save API documentation
        api_file = self.output_dir / "API_DOCS.md"
        api_file.write_text(api_docs, encoding="utf-8")
        return str(api_file)

    def query_docs(self, question: str) -> str:
        """
        Answers questions about the documentation.
        """
        # Get project context
        docs = self.collect_docs()
        context = ""
        
        # Add key files content for context
        key_files = [d for d in docs if d.name in ["README.md", "main.py", "app.py"]]
        for doc in key_files[:3]:
            content = self.read_file(doc)[:1000]
            context += f"\n\n# {doc.name}\n{content}"
        
        prompt = f"""You are a Documentation QA Agent.
You are given a question related to the project.
Answer accurately and contextually, based on the provided project context.

Project Context:
{context}

Question: {question}

Provide a helpful, accurate answer based on the project documentation and code.
"""
        return call_openrouter_llm(prompt)


# ==============================
# 🚀 CLI / Interactive Example
# ==============================
if __name__ == "__main__":
    base_path = input("Enter the path to your project folder: ").strip()
    agent = DocumentationAgent(base_path=base_path)

    print("🧾 Generating project README...")
    readme_path = agent.generate_readme()
    print(f"✅ README generated at: {readme_path}")

    print("\n💬 Example question:")
    question = input("Enter a question about your project docs: ").strip()
    answer = agent.query_docs(question)
    print("Answer:", answer)
