from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_INITDB_DATABASE: str
    KAFKA_BROKER: str
    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str

    REDIS: str
    KAFKA_LAMODA_TOPIC: str


    class Config:
        env_file = './.env'


settings = Settings()
