from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_INITDB_DATABASE: str
    KAFKA_BROKER: str
    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str

    class Config:
        env_file = './.env'


settings = Settings()