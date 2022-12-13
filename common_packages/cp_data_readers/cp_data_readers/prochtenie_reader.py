# -*- coding: utf-8 -*-

import json
import pathlib
import re

from cp_data_readers.utils import RUSSIAN_SUBJECTS, _parse_to_sentences, clear_text, find_standard_type
from ru_sent_tokenize import ru_sent_tokenize


def _parse_correction(parsed_annotation):
    text = parsed_annotation["text"]
    link_symbol = text.find("#")
    if link_symbol > 0:
        link_parts = text[link_symbol + 1 :].split("#")
        text = text[:link_symbol].strip()
        parsed_annotation["text"] = text
        for raw_link in link_parts:
            link = raw_link.strip()
            if link.isdigit():
                if not parsed_annotation.get("link", ""):
                    parsed_annotation["link"] = ["#" + link]
                else:
                    parsed_annotation["link"] = parsed_annotation["link"] + ["#" + link]
            else:
                if not parsed_annotation.get("link_text", ""):
                    parsed_annotation["link_text"] = ["#" + link]
                else:
                    parsed_annotation["link_text"] = parsed_annotation["link_text"] + ["#" + link]
    text_and_comment = text.split("::")
    if len(text_and_comment) == 2:
        if ">>" in text_and_comment[0]:
            text_and_correction = text_and_comment[0].split(">>")
            parsed_annotation["text"] = text_and_correction[0]
            parsed_annotation["corrected_text"] = text_and_correction[1]
            parsed_annotation["comment"] = text_and_comment[1].strip()
        elif ">>" in text_and_comment[1]:
            comment_and_correction = text_and_comment[1].split(">>")
            parsed_annotation["text"] = text_and_comment[0].strip()
            parsed_annotation["corrected_text"] = comment_and_correction[1]
            parsed_annotation["comment"] = comment_and_correction[0]
        else:
            parsed_annotation["text"] = text_and_comment[0].strip()
            parsed_annotation["comment"] = text_and_comment[1].strip()
    elif len(text_and_comment) == 1 and ">>" in text_and_comment[0]:
        text_and_correction = text_and_comment[0].split(">>")
        parsed_annotation["text"] = text_and_correction[0]
        parsed_annotation["corrected_text"] = text_and_correction[1]
    return parsed_annotation


def separate_annotations(annotations):
    separated_annotations = {"sections": [], "mistakes": []}
    for annotation in annotations:
        if annotation["raw_type"] == "NOT AN ANNOTATION":
            continue
        splitted_annotation_type = annotation["raw_type"].split()
        separator = 0
        for name in splitted_annotation_type:
            if name.isupper() and len(name) > 1 and name[1] != ".":
                separator += 1
            else:
                break
        section_name = " ".join(splitted_annotation_type[:separator])
        mistake_name = " ".join(splitted_annotation_type[separator:])
        if section_name:
            annotation_copy = annotation.copy()
            annotation_copy["raw_type"] = section_name
            separated_annotations["sections"].append(annotation_copy)
        if mistake_name:
            annotation_copy = annotation.copy()
            annotation_copy["raw_type"] = mistake_name
            separated_annotations["mistakes"].append(annotation_copy)
    return separated_annotations


def separate_type_and_text(text, subject_map):

    splitted_text = text.split()
    start_section_idx = 0
    start_mistake_idx = 0

    for i, _ in enumerate(splitted_text):
        if clear_text("".join(splitted_text[:i])) in subject_map["sections"].keys():
            start_section_idx = i
    for i, _ in enumerate(splitted_text[start_section_idx:]):
        if clear_text("".join(splitted_text[:i])) in subject_map["mistakes"].keys():
            start_mistake_idx = i
    start_idx = start_section_idx + start_mistake_idx

    if not start_idx:
        capital_letters = re.findall(r"[А-ЯN]", text)
        if len(capital_letters) != 0:
            sentence_start = capital_letters[-1]
        else:
            sentence_start = text[0]

        if splitted_text[0].isupper() and splitted_text[0] != "." and "NUM" not in splitted_text[0]:
            start_idx = len(splitted_text[0])
        elif len(splitted_text) == 1 and "NUM" in splitted_text[0]:
            start_idx = 0
        else:
            start_idx = text.find(sentence_start)

    return " ".join(splitted_text[:start_idx]), " ".join(splitted_text[start_idx:])


def _parse_annotation(text, subject_map):
    if not re.findall(r"[\\*]", text):
        text = "NOT AN ANNOTATION \\ " + "(" + text + ")"
    parsed_annotation = {}
    text = re.sub(r"\*", "", text).strip()
    text = re.sub(r"\/", "\\\\", text)
    sections = text.split("\\")
    sections = [el.strip() for el in sections if len(el) != 0]
    if len(sections) == 2:
        parsed_annotation["raw_type"] = sections[0]
        parsed_annotation["text"] = sections[1]
    elif len(sections) == 1:
        section_name, section_text = separate_type_and_text(sections[0], subject_map)
        parsed_annotation["raw_type"] = section_name
        parsed_annotation["text"] = section_text
    else:
        parsed_annotation["raw_type"] = sections[0]
        parsed_annotation["text"] = " ".join(sections[1:])
    parsed_annotation = _parse_correction(parsed_annotation)
    return parsed_annotation


def _clear_num(text="", annotations={}, saved_num=None):
    while re.findall(r"NUM\d\d", text):
        current_annotations = re.findall(r"NUM\d\d", text)
        if len(list(set(current_annotations))) == 1 and current_annotations[0] == saved_num:
            break
        for num in current_annotations:
            if num != saved_num:
                text = text.replace(num, " " + annotations[num]["text"] + " ")
    text = re.sub(" +", " ", text)
    text = re.sub(r'\s+([,?.!"])', r"\1", text)
    return text


def _parse_essay(raw_essay, subject_map):
    annotations = {}
    num_annotation = 0

    while re.findall(r"\([^()]+\)", raw_essay):
        new_brackets = re.findall(r"\([^()]+\)", raw_essay)
        for el in new_brackets:
            num_annotation += 1
            parsed_dict = _parse_annotation(el[1:-1], subject_map)
            parsed_dict["raw_text"] = el
            num_token = "NUM" + str(num_annotation).zfill(2)
            annotations[num_token] = parsed_dict
            raw_essay = raw_essay.replace(el, num_token, 1)

    for current_num in annotations.keys():
        current_text = _clear_num(raw_essay, annotations, current_num)
        annotations[current_num]["start_span"] = current_text.find(current_num)
        annotations[current_num]["raw_text"] = _clear_num(annotations[current_num]["raw_text"], annotations)
        annotations[current_num]["text"] = _clear_num(annotations[current_num]["text"], annotations)
        annotations[current_num]["end_span"] = annotations[current_num]["start_span"] + len(
            annotations[current_num]["text"]
        )

    clear_essay = _clear_num(raw_essay, annotations)

    annotations = separate_annotations(list(annotations.values()))

    for section in annotations["sections"]:
        section["type"] = find_standard_type(section["raw_type"], subject_map["sections"])
    for mistake in annotations["mistakes"]:
        mistake["type"] = find_standard_type(mistake["raw_type"], subject_map["mistakes"])
        try:
            mistake["subtype"] = mistake["raw_type"].split()[1]
        except IndexError:
            mistake["subtype"] = ""

    return clear_essay, annotations


_full_map = json.load((pathlib.Path(__file__).parent / "annotations_data" / "full_map.json").open(encoding="utf8"))


def parse_essay(raw_essay, subject_name):
    clear_essay, annotations = _parse_essay(raw_essay, _full_map[subject_name])
    return clear_essay, annotations


def parse_text(text_lines, full_map=None):
    full_map = _full_map if full_map is None else full_map
    attr_dict = {}

    previous_section = ""
    current_essay_text = ""
    current_text_for_essay = ""

    attr_names = ["линия", "год", "предмет", "тест", "эксперт", "класс"]
    topic_names = ["\ufeffема", "\ufeffтема", "тема"]
    meta_names = ["тема", "год", "тест", "эксперт", "класс"]

    for i, line in enumerate(text_lines):

        clean_line = line.lower().strip()
        candidate_section = clean_line.split(":")[0]

        if previous_section == "тема":
            if candidate_section == "тема":
                continue
            if candidate_section not in attr_names:
                current_text_for_essay += "\n" + line
            else:
                content = re.findall(r"\(([^}]+)\)", current_text_for_essay.replace("*", ""))[0]
                open_brackets_idx = [bracket.start() for bracket in re.finditer(r"\(", content)]
                if len(open_brackets_idx) <= 1:
                    # content includes only name
                    name = content.strip()
                    text = ""
                else:
                    # content includes name and text for the essay
                    separator = open_brackets_idx[1]
                    name = content[:separator].strip()
                    text = content[separator:].strip()[1:-1]
                attr_dict["тема"] = name
                attr_dict["отрывок"] = text

        if candidate_section in topic_names:
            current_text_for_essay = line
            previous_section = "тема"

        elif candidate_section in attr_names:
            attr_dict[candidate_section] = clean_line.split(":")[1].strip()
            previous_section = candidate_section

        # criteria section
        elif re.findall(r"[кk]\d\d?", clean_line):
            if not attr_dict.get("критерии", ""):
                attr_dict["критерии"] = {}
                previous_section = "критерии"
            candidate_criteria_name = re.findall(r"[кk]\d\d?", clean_line)[0]
            # now we use 'к' in criteria names
            candidate_criteria_name = candidate_criteria_name.lower()
            candidate_criteria_name = re.sub(r"k", "к", candidate_criteria_name)
            candidate_criteria_value = clean_line[-1]
            if re.findall(r"\d", candidate_criteria_value):
                candidate_criteria_value = int(candidate_criteria_value)
                if candidate_criteria_name in attr_dict["критерии"]:
                    # fix repetitive criteria names
                    last_index = max([int(c[1:]) for c in attr_dict["критерии"]])
                    attr_dict["критерии"]["к" + str(last_index + 1)] = candidate_criteria_value
                else:
                    attr_dict["критерии"][candidate_criteria_name] = candidate_criteria_value

        elif previous_section == "эссе":
            current_essay_text += "\n" + line

        elif previous_section == "критерии" or previous_section == "эксперт":
            current_essay_text = line
            previous_section = "эссе"

        if current_essay_text:
            attr_dict["эссе"] = current_essay_text

    if attr_dict["эссе"].startswith("\n"):
        attr_dict["эссе"] = attr_dict["эссе"][1:]

    subject_map = _full_map[attr_dict["предмет"]]
    clear_essay, annotations = _parse_essay(attr_dict["эссе"], subject_map)

    clear_essay = re.sub(" +", " ", clear_essay)

    tokenizer = ru_sent_tokenize if attr_dict["предмет"] in RUSSIAN_SUBJECTS else None
    clear_essay_sentences, clear_essay_offsets = _parse_to_sentences(clear_essay, sentence_tokenizer=tokenizer)

    output = {
        "clear_essay": clear_essay,
        "clear_essay_sentences": clear_essay_sentences,
        "clear_essay_word_offsets": clear_essay_offsets,
        "raw_essay": attr_dict["эссе"],
        "subject": attr_dict["предмет"],
        "annotations": annotations,
        "criteria": attr_dict.get("критерии", ""),
        "source": "ПроЧтение",
        "meta": {name: attr_dict[name] for name in meta_names},
    }

    if output["subject"] == "обществознание":
        output["meta"]["линия"] = attr_dict["линия"]

    if attr_dict.get("отрывок", ""):
        output["meta"]["отрывок"] = attr_dict["отрывок"]

    return output


def read(infile):
    with open(infile, "r", encoding="utf8") as fin:
        text_lines = fin.read().splitlines()
    return parse_text(text_lines)
