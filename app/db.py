import json

from sqlmodel import create_engine

from .config import config

engine = create_engine(
    config.db_uri, echo=config.debug, json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
)
