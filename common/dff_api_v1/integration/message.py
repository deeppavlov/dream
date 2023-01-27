from typing import List, Optional
from pydantic import Field
from dff.script import Message


class DreamMessage(Message):
    confidence: Optional[float] = None
    human_attr: Optional[dict] = None
    bot_attr: Optional[dict] = None
    hype_attr: Optional[dict] = None


class DreamMultiMessage(DreamMessage):
    messages: Optional[List[DreamMessage]] = Field(default_factory=list, min_items=1)
