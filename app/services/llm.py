# app/services/llm.py
from langchain_openai import AzureChatOpenAI
from app.config.settings import settings

# Single global LLM instance (chat) used for all extraction calls right now.
# If you later need deterministic JSON, you can create a second one with temperature=0.0.
llm_deterministic = AzureChatOpenAI(
    azure_deployment=settings.azure_openai_chat_deployment,
    api_version=settings.azure_openai_api_version,
    temperature=0.0,
    # Optional: pass model kwargs if you want JSON forcing (works if endpoint supports)
    # model_kwargs={"response_format": {"type": "json_object"}}
)

llm_questions = AzureChatOpenAI(
    azure_deployment=settings.azure_openai_chat_deployment,
    api_version=settings.azure_openai_api_version,
    temperature=0.4,
)

llm_eval = AzureChatOpenAI(
    azure_deployment=settings.azure_openai_chat_deployment,
    api_version=settings.azure_openai_api_version,
    temperature=0.0
)


