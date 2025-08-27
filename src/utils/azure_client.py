from llama_index.llms.azure_openai import AzureOpenAI
from .config import settings

def get_azure_llm():
    """Get configured Azure OpenAI LLM instance"""
    return AzureOpenAI(
        model=settings.azure_deployment_name,
        deployment_name=settings.azure_deployment_name,
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )