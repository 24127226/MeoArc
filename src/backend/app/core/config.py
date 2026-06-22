from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = BACKEND_DIR / '.env'

class Settings(BaseSettings):
    database_url: str
    model_name: str
    model_provider: str
    ai_api_key: Optional[str] = None
    local_model_base_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    @model_validator(mode='after')
    def check_api_key_or_local_url(self):
        if not self.ai_api_key and not self.local_model_base_url:
            raise ValueError(
                "Lỗi cấu hình: Bạn phải cung cấp 'ai_api_key' khi dùng Cloud Model, "
                "hoặc cung cấp 'local_model_base_url' nếu dùng Local Model!"
            )
        return self


settings = Settings()