from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Banking REST Service"
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    cors_origins: list[str] = ["*"]

    @property
    def database_url(self) -> str:
        """Generate database URL with data_db folder."""
        db_dir = Path(__file__).parent.parent / "data_db"
        db_dir.mkdir(exist_ok=True)
        db_path = db_dir / "banking.db"
        return f"sqlite:///{db_path}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )


settings = Settings()
