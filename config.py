import json
from datetime import datetime
from google.cloud import secretmanager
from google.oauth2 import service_account

def access_secret_version(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    secret_string = response.payload.data.decode("UTF-8")
    return secret_string

# 你 GCP 專案 ID
PROJECT_ID = "gen-lang-client-0700041250"

access_token = access_secret_version(PROJECT_ID, "LINE_CHANNEL_ACCESS_TOKEN")
secret = access_secret_version(PROJECT_ID, "LINE_CHANNEL_SECRET")

API_KEY = access_secret_version(PROJECT_ID, "API_KEY")
PAGE_Orders = access_secret_version(PROJECT_ID, "PAGE_Orders")#36
PAGE_Customers = access_secret_version(PROJECT_ID, "PAGE_Customers")#41
PAGE_Inventory = access_secret_version(PROJECT_ID, "PAGE_Inventory")#32