from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_username: str
    database_password: str
    database_name: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    invite_secret_key: str
    invite_algorithm: str
    invite_access_token_expire_minutes: int

    UPLOAD_DIR: str = "uploads"
    USE_S3: bool = False
    S3_BUCKET: str | None = None

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "eu-north-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
