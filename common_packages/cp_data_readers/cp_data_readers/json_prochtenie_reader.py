from typing import Optional

from cp_data_readers.utils import RUSSIAN_SUBJECTS, _parse_to_sentences
from ru_sent_tokenize import ru_sent_tokenize


def parse_text(data: dict, file_name: str = "", subject: Optional[str] = None):
    extended_markup = {}
    standard_markup = data

    # filling extended_markup
    sentence_tokenizer = ru_sent_tokenize if subject in RUSSIAN_SUBJECTS else None
    (extended_markup["clear_essay_sentences"], extended_markup["clear_essay_word_offsets"],) = _parse_to_sentences(
        standard_markup["text"], sentence_tokenizer=sentence_tokenizer
    )
    return {
        "standard_markup": standard_markup,
        "extended_markup": extended_markup,
    }


def to_std_selections(errors, group="mistakes"):
    selections = []
    for ind, err in enumerate(errors):
        selections.append(
            {
                "comment": err.get("comment", ""),
                "correction": err.get("corrected_text", ""),
                "endSelection": err["end_span"],
                "explanation": err.get("corrected_text", ""),
                "group": "error" if "mistakes" == group else "meaning",
                "id": ind,
                "startSelection": err["start_span"],
                "subtype": err.get("subtype", ""),
                "tag": err.get("links", ""),
                "type": err["type"],
            }
        )
    return selections
