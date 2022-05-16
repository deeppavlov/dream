from pydantic import BaseSettings


class BotSettings(BaseSettings):
    server_host: str
    server_port: str
    bot_name: str

    agent_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
