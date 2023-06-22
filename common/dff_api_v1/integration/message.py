from typing import Optional
from dff.script import Message


class DreamMessage(Message):
    confidence: Optional[float] = None
    human_attr: Optional[dict] = None
    bot_attr: Optional[dict] = None
    hype_attr: Optional[dict] = None
