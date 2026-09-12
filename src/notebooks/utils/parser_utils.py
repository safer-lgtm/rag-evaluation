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


# Gemeinsames Zerlegen in Chunks inkl. Strategie- und Mindestgrößen-Filter
def split_into_chunks(text, chunk_strategy, chunk_size, chunk_overlap, min_chunk_size):
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    if chunk_strategy == "full":
        return [cleaned_text] if len(cleaned_text) >= min_chunk_size else []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = text_splitter.split_text(cleaned_text)
    return [c for c in chunks if len(c) >= min_chunk_size]


# PDF
def parse_pdf(file_path, chunk_strategy="chunked", chunk_size=800, chunk_overlap=200, min_chunk_size=20):
    doc = fitz.open(file_path)
    full_text = ""

    for page in doc:
        full_text += extract_content_from_page(page)

    return split_into_chunks(full_text, chunk_strategy, chunk_size, chunk_overlap, min_chunk_size)


# DOCX
def parse_docx(file_path, chunk_strategy="chunked", chunk_size=800, chunk_overlap=200, min_chunk_size=20):
    from docx import Document

    document = Document(file_path)
    full_text = "\n".join(p.text for p in document.paragraphs)

    for table in document.tables:
        rows = [[cell.text for cell in row.cells] for row in table.rows]
        full_text += "\n" + convert_to_markdown(rows) + "\n"

    return split_into_chunks(full_text, chunk_strategy, chunk_size, chunk_overlap, min_chunk_size)


# PPTX
def parse_pptx(file_path, chunk_strategy="chunked", chunk_size=800, chunk_overlap=200, min_chunk_size=20):
    from pptx import Presentation

    prs = Presentation(file_path)
    full_text = ""

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                full_text += shape.text + "\n"
            if shape.has_table:
                for row in shape.table.rows:
                    cells = [cell.text for cell in row.cells]
                    full_text += "| " + " | ".join(cells) + " |\n"

    return split_into_chunks(full_text, chunk_strategy, chunk_size, chunk_overlap, min_chunk_size)


# XLSX
def parse_xlsx(file_path, chunk_strategy="chunked", chunk_size=800, chunk_overlap=200, min_chunk_size=20):
    import pandas as pd

    excel = pd.ExcelFile(file_path)
    full_text = ""

    for sheet_name in excel.sheet_names:
        df = excel.parse(sheet_name, header=None)
        full_text += f"## {sheet_name}\n"
        rows = df.astype(str).fillna("").values.tolist()
        full_text += convert_to_markdown(rows) + "\n"

    return split_into_chunks(full_text, chunk_strategy, chunk_size, chunk_overlap, min_chunk_size)