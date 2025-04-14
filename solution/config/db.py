from dataclasses import dataclass


@dataclass
class DBConfig:
    db_type: str
    login: str
    password: str
    db_name: str
    db_host: str
    db_port: int

    def create_db_url(self):
        db_url = f'{self.db_type}://{self.login}:{self.password}' \
                 f'@{self.db_host}:{self.db_port}/{self.db_name}'

        return db_url
