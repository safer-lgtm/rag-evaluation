# Databricks notebook source
# COMMAND ----------
# MAGIC %md
# MAGIC # crawl sharepoint documents (DriveFiles)
# COMMAND ----------
# Databricks notebook source
# MAGIC %md
# MAGIC ## Install dependencies
from mlflow import spark
from mlflow.utils.databricks_utils import dbutils

# COMMAND ----------
# MAGIC %pip install markdown
# MAGIC %pip install PyMuPDF
# MAGIC %pip install PyPDF2
# MAGIC %pip install Pillow pytesseract pdf2image
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Set variables

# COMMAND ----------

# variable | default value | show name
dbutils.widgets.text('volume', 'raw_data', 'Volume')
dbutils.widgets.dropdown('catalog', 'development', ['development', 'production'], 'Catalog')
dbutils.widgets.text("schema", "default", "Schema Name")
dbutils.widgets.text('control_table', 'sharepoint_doc_control', 'Control table name')
dbutils.widgets.text('chunk_table', 'chunks', 'Chunk table name')
dbutils.widgets.text('source_data_folder', 'sharepoint_doc_data', 'Volume data name')
dbutils.widgets.text('chunk_size', '800', 'Chunk size')
dbutils.widgets.text('chunk_overlap', '200', 'Chunk overlap')
dbutils.widgets.text('min_chunk_size', '20', 'Min chunk size')
dbutils.widgets.dropdown('chunk_strategy', 'chunked', ['full', 'chunked', 'semantic', 'summary'], 'Chunk strategy')


# COMMAND ----------

# config

# set to true if you want to get new files from workspace to be included in the database
volume = dbutils.widgets.get("volume")
schema = dbutils.widgets.get("schema")
catalog = dbutils.widgets.get("catalog")
control_table = dbutils.widgets.get("control_table")
chunk_table = dbutils.widgets.get("chunk_table")
source_data_folder = dbutils.widgets.get("source_data_folder")
chunk_strategy = dbutils.widgets.get("chunk_strategy")  # 'full', 'chunked', 'semantic', 'summary'
chunk_size = int(dbutils.widgets.get("chunk_size"))
chunk_overlap = int(dbutils.widgets.get("chunk_overlap"))
min_chunk_size = int(dbutils.widgets.get("min_chunk_size"))

control_table_fullname = f"{catalog}.{schema}.{control_table}"
chunk_table_fullname = f"{catalog}.{schema}.{chunk_table}"

# COMMAND ----------
spark.sql(
    f"CREATE TABLE IF NOT EXISTS {chunk_table_fullname} (chunk_id STRING NOT NULL, chunk STRING NOT NULL, url STRING, timestamp TIMESTAMP, document_id STRING)")
# COMMAND ----------

# MAGIC %md
# MAGIC # Find all relevant files and their URLs (create source table)
# COMMAND ----------
import os
import sys
# Add the current working directory to the Python path, as Databricks only processes folder types, not packages
sys.path.append(os.path.dirname(os.getcwd()))
# COMMAND ----------

# MAGIC %md
# MAGIC # identify file type and run sub sequence for file processing
# MAGIC # (chunk process)

# COMMAND ----------
from utils.chunk_utils import write_chunks_if_not_exists
from utils.parser_utils import parse_pdf

files = spark.sql(
    f"SELECT * FROM {control_table_fullname} WHERE document_id NOT IN (SELECT document_id FROM {chunk_table_fullname})").collect()

for file in files:
    print(f'processing: {file["document_path"]}')
    if os.path.getsize(file['document_path']) == 0 or file['document_path'].endswith(
            'Übersicht freigegebene Werbeformen je Domain.xlsx'):  # empty file
        print(f"Skipping empty file: {file['document_path']}")
        continue
    if file['document_path'].endswith('.pdf'):
        chunks = parse_pdf(file_path=file['document_path'], chunk_strategy=chunk_strategy, chunk_size=chunk_size,
                           chunk_overlap=chunk_overlap, min_chunk_size=min_chunk_size)
        for chunk in chunks:
            # print(chunk)
            write_chunks_if_not_exists(spark, chunk, file['source_url'], file['document_id'], chunk_table_fullname, min_chunk_size)


