from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    telegram_bot_token: str
    telegram_chat_id: str | None = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
