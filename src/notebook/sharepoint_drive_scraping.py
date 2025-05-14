# Databricks notebook source
# COMMAND ----------
# MAGIC %pip install -q beautifulsoup4
# MAGIC dbutils.library.restartPython()
# COMMAND ----------
# MAGIC %md
# MAGIC # Config

# COMMAND ----------
import os
import sys
# Add the current working directory to the Python path, as Databricks only processes folder types, not packages
sys.path.append(os.path.dirname(os.getcwd()))