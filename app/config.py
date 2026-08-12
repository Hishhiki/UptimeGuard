from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    telegram_bot_token: str
    telegram_chat_id: str

    model_config = {"env_file": ".env"}

settings = Settings()
