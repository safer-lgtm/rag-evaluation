import requests
import os
from bs4 import BeautifulSoup

# Token holen
def get_access_token(client_id, client_secret, token_url):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(token_url, headers=headers, data=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise RuntimeError(f"❌ Fehler beim Abrufen des Tokens: {response.text}")

# Informationen über eine SharePoint-Website abrufen
def get_site_info(access_token, site_name):
    headers = {"Authorization": f"Bearer {access_token}"}
    graph_api_url = "https://graph.microsoft.com/v1.0"
    site_url = f"{graph_api_url}/sites/name.sharepoint.com:/{site_name}"
    response = requests.get(site_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(f"❌ Fehler beim Abrufen der Site-Info ({site_name}): {response.text}")

# Page Content
def extract_text_from_html(html_content):
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    return

def download_file(source_data_path, file_name, download_url):
    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        if not os.path.exists(source_data_path):
            os.makedirs(source_data_path)
        file_path = os.path.join(source_data_path, file_name)
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except OSError as e:
        if e.errno == 27:
            print(f"Skipping file: {file_name}. File too large to write in one go")
        else:
            print(f"Skipping file due to error: {e}")

def write_source_entry(file_path, file_name, file_url, source_table, timestamp, last_modified, relevant, category, file_id):
    r = spark.sql(f"SELECT * FROM {source_table} WHERE document_id = '{file_id}'")

    new_data = [(str(file_path), str(file_name), str(file_url), timestamp, last_modified, bool(relevant), str(category), str(file_id))]
    df_new = spark.createDataFrame(new_data, ['document_path', 'document_name', 'source_url', 'timestamp', 'last_modified', 'relevant', 'category', 'document_id'])

    if r.isEmpty():
        df_new.write.mode("append").format("delta").saveAsTable(source_table)
