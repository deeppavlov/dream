import base64
import json
from typing import List


def encode_actions(json_data: List[dict]) -> str:
    return base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")


def decode_actions(b64_data: str) -> List[dict]:
    return json.loads(base64.b64decode(b64_data).decode("utf-8"))
