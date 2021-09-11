from pydantic import BaseModel, conlist


class HypothesesSchema(BaseModel):
    is_best: bool
    text: str
    confidence: float


class RequestSchema(BaseModel):
    contexts: conlist(item_type=conlist(item_type=str, min_items=0), min_items=0)
    hypotheses: conlist(item_type=HypothesesSchema, min_items=0)
