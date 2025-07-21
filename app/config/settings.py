from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
load_dotenv() 

class Settings(BaseSettings):
    app_env: str = Field("dev", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    azure_openai_endpoint: str | None = Field(None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = Field(None, env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field(None, env="AZURE_OPENAI_API_VERSION")
    azure_openai_chat_deployment: str | None = Field(None, env="AZURE_OPENAI_CHAT_DEPLOYMENT")
    azure_openai_embedding_deployment: str | None = Field(None, env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    azure_speech_key: str | None = Field(default=None, env="AZURE_SPEECH_KEY")
    azure_speech_region: str | None = Field(default=None, env="AZURE_SPEECH_REGION")



    max_chars: int = 15000  # truncate long docs defensively
    extraction_retries: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
