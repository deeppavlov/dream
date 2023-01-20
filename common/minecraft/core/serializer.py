import base64
import json
from typing import List, NamedTuple, Any, Optional
from pathlib import Path


def encode_actions(json_data: List[dict]) -> str:
    return base64.b64encode(json.dumps(json_data).encode("utf-8")).decode("utf-8")


def decode_actions(b64_data: str) -> List[dict]:
    return json.loads(base64.b64decode(b64_data).decode("utf-8"))


class CommandBuffer(NamedTuple):
    success_flag: List[bool] = []
    crash_reason: List[str] = []
    command_name: List[str] = []
    command_args: List[Any] = []
    command_kwargs: List[Any] = []
    response: List[str] = []
    coords: List[List[int]] = []

    def append(self, **kwargs) -> None:
        self.success_flag.append(kwargs.get("success_flag"))
        self.crash_reason.append(kwargs.get("crash_reason"))
        self.command_name.append(kwargs.get("command_name"))
        self.command_args.append(kwargs.get("command_args"))
        self.command_kwargs.append(kwargs.get("command_kwargs"))

        self.response.append(kwargs.get("response"))
        self.coords.append(kwargs.get("coords"))

    def to_json(self, logfile: Optional[Path] = None) -> str:
        json_str = json.dumps(self._asdict(), indent = 4)
        print(json_str)
        if logfile is not None:
            with open(logfile, "w", encoding="utf-8") as f:
                f.write(json_str)

        return json_str

