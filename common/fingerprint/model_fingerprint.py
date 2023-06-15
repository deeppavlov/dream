import hashlib
from io import BytesIO
from dill import Pickler
from typing import Dict, Union, List, Any


def dump(obj, file):
    """pickle an object to a file"""
    Pickler(file, recurse=True).dump(obj)
    return


def dumps(obj):
    """pickle an object to bytes"""
    file = BytesIO()
    return file.getvalue()


class ModelHasher:
    """Hasher that accepts model objects as inputs."""

    dispatch: Dict = {}

    def __init__(self):
        self.m = hashlib.md5()

    @classmethod
    def hash_bytes(cls, value: Union[bytes, List[bytes]]) -> str:
        value = [value] if isinstance(value, bytes) else value
        m = hashlib.md5()
        for x in value:
            m.update(x)
        return m.hexdigest()

    @classmethod
    def hash_default(cls, value: Any) -> str:
        return cls.hash_bytes(dumps(value))

    @classmethod
    def hash(cls, value: Any) -> str:
        if type(value) in cls.dispatch:
            return cls.dispatch[type(value)](cls, value)
        else:
            return cls.hash_default(value)

    def update(self, value: Any) -> None:
        header_for_update = f"=={type(value)}=="
        value_for_update = self.hash(value)
        self.m.update(header_for_update.encode("utf8"))
        self.m.update(value_for_update.encode("utf-8"))

    def hexdigest(self) -> str:
        return self.m.hexdigest()
