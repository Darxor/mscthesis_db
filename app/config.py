from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_string_url import AnyUrl


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="mscthesis_", env_file=".env", extra="ignore")

    db_uri: Annotated[AnyUrl, Field(title="Database URI")] = AnyUrl("sqlite:///db.sqlite")
    debug: Annotated[bool, Field(title="Debug mode")] = False


config = Config()
