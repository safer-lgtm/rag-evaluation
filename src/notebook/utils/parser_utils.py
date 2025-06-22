import fitz  # PyMuPDF
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

import os
import sys
# Add the current working directory to the Python path, as Databricks only processes folder types, not packages
sys.path.append(os.path.dirname(os.getcwd()))

# PDF Files
def format_text_pdf(text):
    text = text.strip()
    text = re.sub(r'[\u000b|\u000c]', r' ', text)
    text = re.sub(r'\n\n+', r'', text)
    text = re.sub(r'\s\s+', r' ', text)
    text = re.sub(r'[\xE2|\x96|\xAA|▪]', r' ', text)
    return text

def extract_content_from_page(page):
    content = ""

    text = page.get_text("text")
    text = format_text_pdf(text)
    if text:
        content += text + "\n"

    tables = page.get_text("dict")["blocks"]
    for table in tables:
        if table["type"] == 5:  # Table type
            table_data = []
            for line in table["lines"]:
                row = [span["text"] for span in line["spans"]]
                table_data.append(row)
            markdown_table = convert_to_markdown(table_data)
            content += markdown_table + "\n"
    return content


def convert_to_markdown(table_data):
    markdown = ""
    for row in table_data:
        markdown += "| " + " | ".join(row) + " |\n"
    return markdown


# Hauptfunktion: PDF einlesen und in Chunks zerlegen
def parse_pdf(file_path, chunk_size=800, chunk_overlap=120):
    doc = fitz.open(file_path)
    full_text = ""

    for page in doc:
        page_content = extract_content_from_page(page)
        full_text += page_content

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = text_splitter.split_text(full_text.strip())
    return chunks