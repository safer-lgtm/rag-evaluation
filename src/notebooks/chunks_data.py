# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC ## Install dependencies
from mlflow import spark
from mlflow.utils.databricks_utils import dbutils

# COMMAND ----------
# MAGIC %pip install markdown
# MAGIC %pip install PyMuPDF
# MAGIC %pip install PyPDF2
# MAGIC %pip install Pillow pytesseract pdf2image
# MAGIC %pip install python-docx
# MAGIC %pip install python-pptx
# MAGIC %pip install pandas openpyxl
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set variables

# COMMAND ----------

dbutils.widgets.text('volume', 'raw_data', 'Volume')
dbutils.widgets.text('catalog', 'workspace', 'Catalog')
dbutils.widgets.text("schema", "default", "Schema Name")
dbutils.widgets.text('control_table', 'sharepoint_doc_control', 'Control table name')
dbutils.widgets.text('chunk_table', 'chunks', 'Chunk table name')
dbutils.widgets.text('source_data_folder', '', 'Volume subfolder (leave empty for root)')
dbutils.widgets.text('chunk_size', '800', 'Chunk size')
dbutils.widgets.text('chunk_overlap', '200', 'Chunk overlap')
dbutils.widgets.text('min_chunk_size', '20', 'Min chunk size')
dbutils.widgets.dropdown('chunk_strategy', 'chunked', ['full', 'chunked', 'semantic', 'summary'], 'Chunk strategy')


# COMMAND ----------

volume = dbutils.widgets.get("volume")
schema = dbutils.widgets.get("schema")
catalog = dbutils.widgets.get("catalog")
control_table = dbutils.widgets.get("control_table")
chunk_table = dbutils.widgets.get("chunk_table")
source_data_folder = dbutils.widgets.get("source_data_folder")
chunk_strategy = dbutils.widgets.get("chunk_strategy")
chunk_size = int(dbutils.widgets.get("chunk_size"))
chunk_overlap = int(dbutils.widgets.get("chunk_overlap"))
min_chunk_size = int(dbutils.widgets.get("min_chunk_size"))

if source_data_folder:
    source_data_path = f"/Volumes/{catalog}/{schema}/{volume}/{source_data_folder}"
else:
    source_data_path = f"/Volumes/{catalog}/{schema}/{volume}"

control_table_fullname = f"{catalog}.{schema}.{control_table}"
chunk_table_fullname = f"{catalog}.{schema}.{chunk_table}"

ALLOWED_FILE_TYPES = ["docx", "pptx", "pdf", "xlsx"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create tables

# COMMAND ----------
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {control_table_fullname} (
        document_path STRING NOT NULL,
        document_name STRING NOT NULL,
        source_url STRING,
        timestamp TIMESTAMP,
        last_modified STRING,
        relevant BOOLEAN,
        category STRING,
        document_id STRING NOT NULL
    )
""")

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {chunk_table_fullname} (
        chunk_id STRING NOT NULL,
        chunk STRING NOT NULL,
        url STRING,
        timestamp TIMESTAMP,
        document_id STRING
    )
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scan volume and register files

# COMMAND ----------
import os
import hashlib
import datetime

file_entries = dbutils.fs.ls(source_data_path)

new_files = []
for entry in file_entries:
    file_path = entry.path
    file_name = entry.name
    if not file_name.lower().endswith(tuple(ALLOWED_FILE_TYPES)):
        continue
    file_id = hashlib.md5(file_path.encode()).hexdigest()
    existing = spark.sql(f"SELECT 1 FROM {control_table_fullname} WHERE document_id = '{file_id}'").collect()
    if not existing:
        new_files.append((file_path, file_name, "", datetime.datetime.now(), None, True, "", file_id))

if new_files:
    df = spark.createDataFrame(new_files, ['document_path', 'document_name', 'source_url', 'timestamp', 'last_modified', 'relevant', 'category', 'document_id'])
    df.write.mode("append").format("delta").saveAsTable(control_table_fullname)
    print(f"Registered {len(new_files)} new files in control table.")
else:
    print("No new files to register.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Chunk files

# COMMAND ----------
import sys
sys.path.append(os.path.dirname(os.getcwd()))

from utils.chunk_utils import write_chunks_if_not_exists
from utils.parser_utils import parse_pdf, parse_docx, parse_pptx, parse_xlsx

files = spark.sql(
    f"SELECT * FROM {control_table_fullname} WHERE document_id NOT IN (SELECT document_id FROM {chunk_table_fullname})").collect()

for file in files:
    print(f'processing: {file["document_path"]}')
    if os.path.getsize(file['document_path']) == 0:
        print(f"Skipping empty file: {file['document_path']}")
        continue

    file_path = file['document_path']
    kwargs = dict(chunk_strategy=chunk_strategy, chunk_size=chunk_size, chunk_overlap=chunk_overlap,
                  min_chunk_size=min_chunk_size)

    if file_path.endswith('.pdf'):
        chunks = parse_pdf(file_path=file_path, **kwargs)
    elif file_path.endswith('.docx'):
        chunks = parse_docx(file_path=file_path, **kwargs)
    elif file_path.endswith('.pptx'):
        chunks = parse_pptx(file_path=file_path, **kwargs)
    elif file_path.endswith('.xlsx'):
        chunks = parse_xlsx(file_path=file_path, **kwargs)
    else:
        print(f"Skipping unsupported file type: {file_path}")
        continue

    for chunk in chunks:
        write_chunks_if_not_exists(spark, chunk, file['source_url'], file['document_id'], chunk_table_fullname, min_chunk_size)

print(f"Done. Processed {len(files)} files.")
