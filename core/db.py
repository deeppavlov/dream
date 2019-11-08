import motor.motor_asyncio
from core.transform_config import DB_HOST, DB_PORT, DB_NAME


class DataBase:
    _inst = None

    def __new__(cls, *args, **kwargs):
        if not cls._inst:
            cls._inst = super(DataBase, cls).__new__(cls)
        return cls._inst

    def __init__(self, host, port, name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        self.db = self.client[name]

    def get_db(self):
        return self.db


db = DataBase(DB_HOST, DB_PORT, DB_NAME).get_db()
