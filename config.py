from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_INITDB_DATABASE: str
    KAFKA_BROKER: str
    REDIS: str

    class Config:
        env_file = './.env'


settings = Settings()