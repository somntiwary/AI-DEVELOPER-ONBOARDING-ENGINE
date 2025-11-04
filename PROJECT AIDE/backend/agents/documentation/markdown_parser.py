# markdown_parser.py
import re
from pathlib import Path
from typing import List, Dict, Union

class MarkdownParser:
    """
    A professional Markdown parser for extracting structured data:
    - Headings (H1-H6)
    - Code blocks
    - Paragraphs
    """

    def __init__(self, markdown_file: Union[str, Path]):
        self.markdown_file = Path(markdown_file)
        if not self.markdown_file.exists() or self.markdown_file.suffix != ".md":
            raise ValueError(f"File {self.markdown_file} is not a valid Markdown (.md) file.")
        self.content = self.markdown_file.read_text(encoding="utf-8", errors="ignore")
        self.parsed_data = []

    def parse_headings(self) -> List[Dict[str, str]]:
        """
        Extract all headings (H1-H6) from the markdown file.
        Returns a list of dicts: {level: 'H1', heading: 'Title'}
        """
        headings = []
        for line in self.content.splitlines():
            match = re.match(r"^(#{1,6})\s+(.*)", line)
            if match:
                level = f"H{len(match.group(1))}"
                heading = match.group(2).strip()
                headings.append({"level": level, "heading": heading})
        return headings

    def parse_code_blocks(self) -> List[Dict[str, str]]:
        """
        Extract all fenced code blocks.
        Returns a list of dicts: {language: 'python', code: '...'}
        """
        code_blocks = []
        # Regex for ```lang\ncode\n```
        pattern = re.compile(r"```(\w+)?\n(.*?)```", re.DOTALL)
        matches = pattern.findall(self.content)
        for lang, code in matches:
            code_blocks.append({
                "language": lang if lang else "text",
                "code": code.strip()
            })
        return code_blocks

    def parse_paragraphs(self) -> List[str]:
        """
        Extract paragraphs (text between headings or code blocks)
        """
        # Remove code blocks first
        text_no_code = re.sub(r"```.*?```", "", self.content, flags=re.DOTALL)
        # Split by empty lines
        paragraphs = [p.strip() for p in text_no_code.split("\n\n") if p.strip()]
        return paragraphs

    def parse_all(self) -> Dict[str, List]:
        """
        Returns a complete structured representation of the markdown:
        - headings
        - code_blocks
        - paragraphs
        """
        self.parsed_data = {
            "headings": self.parse_headings(),
            "code_blocks": self.parse_code_blocks(),
            "paragraphs": self.parse_paragraphs()
        }
        return self.parsed_data


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    md_path = input("Enter the path to the markdown (.md) file: ").strip()
    parser = MarkdownParser(md_path)

    structured_data = parser.parse_all()
    
    print("\n📌 Headings:")
    for h in structured_data["headings"]:
        print(f"{h['level']}: {h['heading']}")

    print("\n📌 Code Blocks:")
    for i, cb in enumerate(structured_data["code_blocks"], 1):
        print(f"\nCode Block {i} ({cb['language']}):\n{cb['code'][:300]}...")  # preview first 300 chars

    print("\n📌 Paragraphs:")
    for p in structured_data["paragraphs"][:5]:  # show first 5 paragraphs as example
        print(f"- {p[:200]}...")  # preview first 200 chars
