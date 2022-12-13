import json
from typing import Optional

from cp_data_readers.utils import RUSSIAN_SUBJECTS, _parse_to_sentences
from ru_sent_tokenize import ru_sent_tokenize


def _parse_neznaika_criteria(data: dict):
    # use only lower cased cyrillic "к" as name of criteria
    return {
        elem["criterion_code"].lower().replace("k", "K").replace("к", "K"): str(elem["criterion_points"][0])
        for elem in data["criteria"]
    }


NEZNAIKA_ENGLISH_ERROR_TYPES = {
    "Грамматическая": "А.грамм",
    "Пунктуационная": "А.пункт",
    "Стилистическая": "А.стиль",
    "Орфографическая": "А.орф",
    "Лексическая": "А.лекс",
}


def _process_error(error: dict, offset=0, subject=None):
    """
    Функция, приводящая ошибку из Незнайки в вид, напоминающий ошибки из основного датасета.
    TO_DO: добавить преобразование типа ошибки из Незнайки в тип из основного датасета.
    """
    processed_error = {
        "comment": "",
        "endSelection": 0,
        "startSelection": 0,
        "text": "",
        "type": "",
        "id": 0,
        "subtype": "",
        "tag": "",
        "explanation": "",
        "correction": "",
        "group": "error",
    }
    processed_error["startSelection"] = error["start"] + offset
    processed_error["endSelection"] = error["end"] + offset
    processed_error["text"] = error["err_span"]
    error_type = NEZNAIKA_ENGLISH_ERROR_TYPES.get(error["err_type"])
    if subject == "eng" and error_type:
        processed_error["type"] = error_type
        error_location = "standard"
    else:
        error_location = "extended"
        processed_error["rawType"] = error["err_type"]
    processed_error["comment"] = error["err_text"]
    return error_location, processed_error


def parse_text(data: dict, file_name: str = "", subject: Optional[str] = None):
    extended_markup = {}
    standard_markup = {
        "fileName": file_name,
        "meta": {
            "name": file_name,
            "class": "11",
            "year": 2020,
            "taskText": "",
            "category": None,
            "expert": "neznaika_exp",
            "test": "егэ незнайка",
            "theme": None,
            "subject": None,
        },
    }
    assert subject is not None
    # filling meta
    standard_markup["meta"]["subject"] = subject
    standard_markup["meta"]["theme"] = data["text"]

    # filling text
    standard_markup["text"] = "\n".join(data["essay"])

    # filling criteria
    standard_markup["criteria"] = _parse_neznaika_criteria(data)

    # filling selections
    extended_markup["selections"] = []
    standard_markup["selections"] = []
    offset = 0
    for i, paragraph_errors in enumerate(data["errors"]):
        for error in paragraph_errors:
            error_location, processed_error = _process_error(error, offset=offset, subject=subject)
            if "extended" in error_location:
                extended_markup["selections"] += [processed_error]
            else:
                standard_markup["selections"] += [processed_error]
        offset += len(data["essay"][i]) + 1

    # filling extended_markup
    sentence_tokenizer = ru_sent_tokenize if subject in RUSSIAN_SUBJECTS else None
    (extended_markup["clear_essay_sentences"], extended_markup["clear_essay_word_offsets"],) = _parse_to_sentences(
        standard_markup["text"], sentence_tokenizer=sentence_tokenizer
    )
    return {
        "standard_markup": standard_markup,
        "extended_markup": extended_markup,
    }


def read(infile: str, subject: Optional[str] = None):
    with open(infile, "r", encoding="utf8") as fin:
        text_lines = json.load(fin)
    return parse_text(text_lines["raw_input"], subject=subject, file_name=infile.name)
