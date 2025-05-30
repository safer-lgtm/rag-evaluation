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
# COMMAND ----------
import importlib
from utils import sharepoint_utils
importlib.reload(sharepoint_utils)
from utils.sharepoint_utils import get_access_token, get_site_info, download_file
import requests

# COMMAND ----------
client_id = dbutils.secrets.get(scope="my_scope", key="client_id")
client_secret = dbutils.secrets.get(scope="my_scope", key="client_secret")
tenant_id = dbutils.secrets.get(scope="my_scope", key="tenant_id")

dbutils.widgets.text("site_name", "teams/WIKI", "Site Name") # nur ab "teams" gebraucht
dbutils.widgets.text("volume", "raw_data", "Volume name")
dbutils.widgets.text("source_data_folder", "sharepoint_doc_data", "Sharepoint Folder")
dbutils.widgets.dropdown("catalog", "development", ["development", "production"], "Catalog")
dbutils.widgets.text("schema", "sms_sales_assistant", "Schema Name")

# COMMAND ----------
site_name = dbutils.widgets.get("site_name")
volume = dbutils.widgets.get("volume")
source_data_folder = dbutils.widgets.get("source_data_folder")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

source_data_path = f"/Volumes/{catalog}/{schema}/{volume}/{source_data_folder}"
# fixed configs
ALLOWED_FILE_TYPES = ["docx", "pptx", "pdf", "xlsx"]
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

# COMMAND ----------
# MAGIC %md
# MAGIC # crawl sharepoint documents (DriveFiles)
# COMMAND ----------
# Gemeinsame Funktion zum Crawlen von Dateien und Ordnern
def crawl_items(client_id, client_secret, token_url, items, source_data_path):
    for item in items:
        if "file" in item:  # Datei gefunden
            file_name = item["name"]
            file_url = item["webUrl"]
            download_url = item.get("@microsoft.graph.downloadUrl", file_url)  # Direkter Download-Link bevorzugt)

            if file_name.lower().endswith(tuple(ALLOWED_FILE_TYPES)):
                download_file(source_data_path, file_name, download_url)

        elif "folder" in item:  # Ordner gefunden
            print(f"📁 [Ordner] {item['name']}")
            child_folder_id = item["id"]
            drive_id = item["parentReference"]["driveId"]
            child_folder_url = f"{GRAPH_API_URL}/drives/{drive_id}/items/{child_folder_id}/children"
            # Kindordner rekursiv crawlen
            crawl_drive(client_id, client_secret, token_url, child_folder_url, source_data_path)

# COMMAND ----------
# Dateien & folder rekursiv durchsuchen
def crawl_drive(client_id, client_secret, token_url, drive_url, source_data_path):
    access_token = get_access_token(client_id, client_secret, token_url)
    headers = {"Authorization": f"Bearer {access_token}"}
    while drive_url:
        response = requests.get(drive_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            items = data.get("value", [])
            crawl_items(client_id, client_secret, token_url, items, source_data_path)  # Aufruf der gemeinsamen Funktion

            # Nächste Seite abrufen, falls vorhanden
            drive_url = data.get("@odata.nextLink")
        else:
            raise RuntimeError(f"❌ Fehler beim Abrufen von {drive_url}: {response.status_code} - {response.text}")

# COMMAND ----------

def main(client_id, client_secret, tenant_id, site_name, source_data_path, control_table_fullname):
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    access_token = get_access_token(client_id, client_secret, token_url)

    print(f"\n🔍 Durchsuche SharePoint-Website: {site_name}")
    site_info = get_site_info(access_token, site_name)

    site_id = site_info.get("id")
    drive_url = f"{GRAPH_API_URL}/sites/{site_id}/drive/root/children"

    crawl_drive(client_id, client_secret, token_url, drive_url, source_data_path)

# COMMAND ----------
main(client_id, client_secret, tenant_id, site_name, source_data_path)