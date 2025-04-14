import configparser
from dataclasses import dataclass

from .db import DBConfig


@dataclass
class Config:
    db: DBConfig


def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    db_ = config["db"]

    return Config(
        db=DBConfig(
            db_type=db_.get("db_type"),
            login=db_.get("login"),
            password=db_.get("password"),
            db_name=db_.get("db_name"),
            db_host=db_.get("db_host"),
            db_port=db_.getint("db_port")
        ),
    )
