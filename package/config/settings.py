from functools import lru_cache
from package.types import CHSettings, PGSettings
from package.utils.settings import create_ch_settings, create_pg_settings
from pydantic import BaseModel, Field


class Settings(BaseModel):
    test_ch: CHSettings = Field(default_factory=create_ch_settings("test_"))
    test_pg: PGSettings = Field(default_factory=create_pg_settings("test_"))


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings()
