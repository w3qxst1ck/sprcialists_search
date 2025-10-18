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

CALENDAR_MONTHS = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь"
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
    admin_tg_username: str = "kill_rilll"
    admin_group_id: str = Field(..., env='ADMIN_GROUP_ID')
    local_media_path: str = "media/"

    s3_secret_key: str = Field(..., env='S3_SECRET_KEY')
    s3_access_key: str = Field(..., env='S3_ACCESS_KEY')
    s3_url: str = "https://s3.ru-7.storage.selcloud.ru"
    s3_bucket_name: str = "profile-media"

    executors_profile_path: str = "profiles/executors/"
    clients_profile_path: str = "profiles/clients/"
    executors_cv_path: str = "cv/executors/"

    db: Database = Database()

    @property
    def languages(self):
        return LANGUAGES

    @property
    def calendar_months(self):
        return CALENDAR_MONTHS


settings = Settings()