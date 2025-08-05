from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
# Initialize the AzureOpenAI client
client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# The model deployment name (not model name like gpt-4), as created in Azure portal
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")