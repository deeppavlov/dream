import motor.motor_asyncio


class DataBase:
    _inst = None

    def __new__(cls, *args, **kwargs):
        if not cls._inst:
            cls._inst = super(DataBase, cls).__new__(cls)
        return cls._inst

    def __init__(self, host, port, name):
        if isinstance(port, str):
            port = int(port)
        self.client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        self.db = self.client[name]

    def get_db(self):
        return self.db
