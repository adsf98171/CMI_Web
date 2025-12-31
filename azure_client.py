# common/azure_client.py
from openai import AzureOpenAI
from config import Config

client = AzureOpenAI(
    api_key=Config.AZURE_API_KEY,
    azure_endpoint=Config.AZURE_ENDPOINT,
    api_version=Config.API_VERSION
)

def get_client_and_deployment():
    return client, Config.DEPLOYMENT