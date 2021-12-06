from typing import Dict, List, Sequence
from pydantic import BaseModel, validator
from src.data.conceptnet import conceptnet_relations

ATOMIC_VALID_EFFECTS = {"all", "oEffect", "oReact", "oWant", "xAttr", "xEffect", "xIntent", "xNeed", "xReact", "xWant"}
CONCEPTNET_VALID_RELATIONS = {"all"}.union(conceptnet_relations)


class AtomicInputEventModel(BaseModel):
    input: str
    category: Sequence[str] = ("xReact", "xNeed", "xAttr", "xWant", "oEffect", "xIntent", "oReact")

    @validator("category")
    def is_valid(cls, category):
        if not ATOMIC_VALID_EFFECTS.issuperset(category):
            raise ValueError(
                "Must consists only of: {}".format(ATOMIC_VALID_EFFECTS)
            )
        return category


class AtomicResponseModelPerCategory(BaseModel):
    beams: List[str]
    effect_type: str
    event: str


class AtomicResponseModel(BaseModel):
    __root__: Dict[str, AtomicResponseModelPerCategory]


class ConceptNetInputBaseModel(BaseModel):
    category: Sequence[str] = ("SymbolOf", "HasProperty", "Causes", "CausesDesire")

    @validator("category")
    def is_valid(cls, category):
        if not CONCEPTNET_VALID_RELATIONS.issuperset(category):
            raise ValueError(
                "Must consists only of: {}".format(CONCEPTNET_VALID_RELATIONS)
            )
        return category


class ConceptNetInputEventModel(ConceptNetInputBaseModel):
    input: str


class ConceptNetAnnotatorEventModel(ConceptNetInputBaseModel):
    nounphrases: Sequence[Sequence[str]] = [["basketball", "unicorn"], ["pancakes"],
                                            ["ieaundy karianne rania tecca dot"]]


class ConceptNetResponseModelPerCategory(BaseModel):
    e1: str
    relation: str
    beams: List[str]


class ConceptNetResponseModel(BaseModel):
    __root__: Dict[str, ConceptNetResponseModelPerCategory]


class ConceptNetAnnotatorResponseModel(BaseModel):
    __root__: List[
        Dict[str, Dict[str, List[str]]]
    ]
