from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LANGUAGES = {
    'ENG': '🇺🇸',
    'RUS': '🇷🇺',
    'KZ': '🇰🇿',
    'GER': '🇩🇪',
    'ITA': '🇮🇹',
    'ESP': '🇪🇸',
    'FRA': '🇫🇷',
    'UZB': '🇺🇿',
    'POL': '🇵🇱',
}


class Database(BaseSettings):
    postgres_user: str = Field(..., env='POSTGRES_USER')
    postgres_password: str = Field(..., env='POSTGRES_USER')
    postgres_db: str = Field(..., env='POSTGRES_DB')
    postgres_host: str = Field(..., env='POSTGRES_HOST')
    postgres_port: str = Field(..., env='POSTGRES_PORT')

    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class Settings(BaseSettings):
    bot_token: str = Field(..., env='BOT_TOKEN')
    admins: list = Field(..., env='ADMINS')

    db: Database = Database()

    @property
    def languages(self):
        return LANGUAGES


settings = Settings()