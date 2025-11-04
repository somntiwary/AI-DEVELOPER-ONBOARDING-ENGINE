# pdf_parser.py
from pathlib import Path
from typing import Dict, Union, List
import PyPDF2  # pip install PyPDF2

class PDFParser:
    """
    PDF Parser to extract text and metadata from PDF files.
    """

    def __init__(self, pdf_file: Union[str, Path]):
        self.pdf_file = Path(pdf_file)
        if not self.pdf_file.exists() or self.pdf_file.suffix.lower() != ".pdf":
            raise ValueError(f"File {self.pdf_file} is not a valid PDF.")
        self.text = ""
        self.metadata = {}

    def extract_text(self) -> str:
        """
        Extracts text from all pages of the PDF.
        """
        try:
            with open(self.pdf_file, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                all_text = []
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        all_text.append(page_text.strip())
                self.text = "\n\n".join(all_text)
            return self.text
        except Exception as e:
            print(f"❌ Error reading PDF {self.pdf_file}: {e}")
            return ""

    def extract_metadata(self) -> Dict[str, str]:
        """
        Extracts PDF metadata (author, title, subject, producer, etc.)
        """
        try:
            with open(self.pdf_file, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                meta = reader.metadata
                self.metadata = {k[1:]: v for k, v in meta.items() if v}  # remove leading '/' in keys
            return self.metadata
        except Exception as e:
            print(f"❌ Error extracting metadata from {self.pdf_file}: {e}")
            return {}

    def parse(self) -> Dict[str, Union[str, Dict]]:
        """
        Returns full structured data: text + metadata
        """
        return {
            "text": self.extract_text(),
            "metadata": self.extract_metadata()
        }


# ==============================
# 🚀 CLI / Example usage
# ==============================
if __name__ == "__main__":
    pdf_path = input("Enter the path to the PDF file: ").strip()
    parser = PDFParser(pdf_path)

    parsed_data = parser.parse()

    print("\n📌 PDF Metadata:")
    for k, v in parsed_data["metadata"].items():
        print(f"- {k}: {v}")

    print("\n📌 PDF Text Preview (first 1000 chars):")
    print(parsed_data["text"][:1000] + ("..." if len(parsed_data["text"]) > 1000 else ""))
