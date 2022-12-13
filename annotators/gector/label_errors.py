import difflib
import os
import re
from string import punctuation

import spacy
from cp_data_readers.utils import _word_tokenize
from gector.gec_model import GecBERTModel
from sacremoses import MosesDetokenizer

# для этого есть функция is_punctuation в utils ридера, замените
punct = punctuation + "«»—…“”*№–"

spacy_model = spacy.load("en", disable=["ner"])

md = MosesDetokenizer(lang="en")

model = GecBERTModel(
    vocab_path="vocab/output_vocabulary",
    model_paths=["/model_data/xlnet_0_gector.th", "/model_data/roberta_1_gector.th"],
    min_probability=0.0,
    model_name="roberta",
    special_tokens_fix=0,
    is_ensemble=True,
)

ENG_PRONOUNS = {
    "i",
    "me",
    "my",
    "mine",
    "myself",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "that",
    "they",
    "them",
    "their",
    "theirs",
    "themself",
    "themselves",
    "these",
    "this",
    "those",
    "we",
    "what",
    "whatever",
    "which",
    "who",
    "whom",
    "whose",
    "why",
    "us",
    "our",
    "ours",
    "ourselves",
    "everyone",
    "someone",
    "anyone",
    "everything",
    "anything",
    "something",
    "nothing",
    "every",
    "some",
    "any",
}

ENG_ARTICLES = {"a", "an", "the"}

ENG_LINKERS = {
    "besides",
    "however",
    "nevertheless",
    "firstly",
    "secondly",
    "thirdly",
    "thus",
    "therefore",
    "though",
    "although",
    "finally",
    "next",
    "despite",
    "additionally",
    "indeed",
    "especially",
}

ENG_MODAL_VERBS = {
    "be able to",
    "can",
    "could",
    "have to",
    "has to",
    "had to",
    "will have to",
    "would have to",
    "may",
    "might",
    "must",
    "need",
    "needed",
    "ought to",
    "shall",
    "should",
    "used to",
    "will",
    "would",
}

ENG_ADJ_COMP = {
    "more",
    "most",
    "worst",
}

FP_PLURAL_NOUNS = {
    "businesses",
    "humans",
    "lives",
    "research",
    "viruses",
}

FP_PUNCT_WORDS = {
    "believe",
    "hence",
    "i",
    "nowadays",
    "now",
    "often",
    "present",
    "think",
    "time",
    "times",
    "why",
}


FP_LEX_WORDS = {
    "affected",
    "ca",
    "method",
    "path",
    "will",
    "would",
}

FP_LEX_VERBS_TO_GRAM = {
    "can",
    "could",
}


def read_data(folderpath, bad_suffixes=None):
    if bad_suffixes is None:
        bad_suffixes = ["map"]
    filepaths = [
        os.path.join(folderpath, f) for f in os.listdir(folderpath) if not any(f.endswith(x) for x in bad_suffixes)
    ]
    words = []
    for filepath in filepaths:
        with open(filepath, "r", encoding="utf8") as f:
            data = f.readlines()
        words.extend([x.strip() for x in data])
    return set(words)


words = read_data("/data/dictionaries/scowl_70")


def predict_corrections(input_data, model=model, batch_size=64):
    predictions = []
    batch = []
    for sent in input_data:
        batch.append(sent["words"])
        if len(batch) == batch_size:
            preds, cnt = model.handle_batch(batch)
            predictions.extend(preds)
            batch = []
    if batch:
        preds, cnt = model.handle_batch(batch)
        predictions.extend(preds)
    return [md.detokenize(x) for x in predictions]


def _get_opcodes(before, after):
    if isinstance(before, str):
        before = _word_tokenize(before)[0]
    if isinstance(after, str):
        after = _word_tokenize(after)[0]
    s = difflib.SequenceMatcher(None, before, after)
    opcodes = []
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag != "equal":
            opcodes.append([tag, (i1, i2), (j1, j2), before[i1:i2], after[j1:j2]])
    return opcodes, before, after


def classify_changes(opcodes, before, after, word_offsets, before_text):
    before_parsed, after_parsed = spacy_model(before), spacy_model(after)
    before, after = _word_tokenize(before)[0], _word_tokenize(after)[0]
    corrections = []
    skip = False
    for i, item in enumerate(opcodes):
        if skip:
            skip = False
            continue
        if "(" in item[3] or any(e in x.lower() for e in ENG_LINKERS for x in item[3]):
            continue
        correction = {"comment": "", "subtype": "", "group": "error", "tag": ""}
        start, end = item[1]
        if "replace" == item[0]:
            correction["startSelection"] = word_offsets[start][0]
            correction["endSelection"] = word_offsets[end - 1][1]
            correction["correction"] = md.detokenize(item[4])
            normalized_error = item[3][0].lower().translate(str.maketrans("", "", punct))
            normalized_correction = item[4][0].lower().translate(str.maketrans("", "", punct))
            if normalized_error in ENG_PRONOUNS and normalized_correction in ENG_PRONOUNS:
                if normalized_error == normalized_correction:
                    correction["type"] = "А.орф"
                    correction["explanation"] = "Орфографическая ошибка."
                else:
                    correction["type"] = "А.грамм"
                    correction["subtype"] = "мест"
                    correction["explanation"] = "Местоимение"
            elif all(not re.search("\w*[.,?!]\s*\w+", x) for x in item[3]) and all(
                not re.search("\w+[.,?!]", x) for x in item[3]
            ):
                if len(item[3]) == len(item[4]):
                    if "'s" in item[3][0] or "'s" in item[4][0]:
                        correction["type"] = "А.грамм"
                        correction["subtype"] = "прит"
                        correction["explanation"] = "Форма притяжательного падежа существительного"
                    elif normalized_error == normalized_correction or normalized_error not in words:
                        correction["type"] = "А.орф"
                        correction["explanation"] = "Орфографическая ошибка."
                    else:
                        before_pos = before_parsed[item[1][0]].pos_
                        after_pos = after_parsed[item[2][0]].pos_
                        if before_parsed[item[1][0]].lemma_ != after_parsed[item[2][0]].lemma_ and (
                            before_pos == after_pos == "NOUN"
                            or before_pos == after_pos == "ADJ"
                            or before_pos == after_pos == "VERB"
                        ):
                            if after_parsed[item[2][0]].lemma_ in FP_LEX_WORDS:
                                continue
                            elif after_parsed[item[2][0]].lemma_ in FP_LEX_VERBS_TO_GRAM:
                                correction["type"] = "А.грамм"
                                correction["subtype"] = "видовр"
                                correction["explanation"] = "Видовременная форма глагола"
                            else:
                                correction["type"] = "А.лекс"
                                correction["subtype"] = "конт"
                                correction[
                                    "explanation"
                                ] = "Лексическая ошибка. Неправильное употребление слова в контексте"
                        elif before_pos == after_pos == "ADP":
                            correction["type"] = "А.грамм"
                            correction["subtype"] = "пред"
                            correction["explanation"] = "Предлог"
                        elif after[item[2][0]] in ENG_MODAL_VERBS:
                            correction["type"] = "А.грамм"
                            correction["subtype"] = "мод"
                            correction["explanation"] = "Модальный глагол"
                        elif any(x in punct for x in item[4][0]):
                            continue
                        elif (before_parsed[item[1][0]].tag_ == "NN" and after_parsed[item[2][0]].tag_ == "NNS") or (
                            before_parsed[item[1][0]].tag_ == "NNS" and after_parsed[item[2][0]].tag_ == "NN"
                        ):
                            if item[4][0] in FP_PLURAL_NOUNS:
                                continue
                            correction["type"] = "А.грамм"
                            correction["subtype"] = "множ"
                            correction["explanation"] = "Форма множественного числа"
                        else:
                            correction["type"] = "А.грамм"
                            correction["subtype"] = "видовр"
                            correction["explanation"] = "Видовременная форма глагола"
                elif len(item[3]) < len(item[4]):
                    if normalized_correction in ENG_ARTICLES:
                        correction["type"] = "А.грамм"
                        correction["subtype"] = "арт"
                        correction["explanation"] = "Артикль"
                    else:
                        correction["type"] = "А.грамм"
                        correction["subtype"] = "видовр"
                        correction["explanation"] = "Видовременная форма глагола"
                else:
                    if normalized_error in ENG_ARTICLES:
                        correction["type"] = "А.грамм"
                        correction["subtype"] = "арт"
                        correction["explanation"] = "Артикль"
                    else:
                        correction["type"] = "А.грамм"
                        correction["subtype"] = "видовр"
                        correction["explanation"] = "Видовременная форма глагола"
        elif "delete" == item[0]:
            if not item[3] and not item[4]:
                continue
            correction["type"] = "А.грамм"
            normalized_error = item[3][0].lower().translate(str.maketrans("", "", punct))
            if len(item[3]) == 1:
                if normalized_error in ENG_ARTICLES:
                    item[4].append(before[end])
                    end += 1
                    if item[4][-1] in ENG_ADJ_COMP or item[4][-1].endswith("est"):
                        correction["subtype"] = "сравн"
                    else:
                        correction["subtype"] = "арт"
                        correction["explanation"] = "Артикль"
                elif item[3][0] in punct:
                    start -= 1
                    item[4].insert(0, before[start])
                    correction["type"] = "А.пункт"
                    continue  # выключили пунктуацию
                elif spacy_model(item[3][0])[0].pos_ == "ADP":
                    correction["subtype"] = "пред"
                    correction["explanation"] = "Предлог"
                else:
                    correction["subtype"] = "видовр"
                    correction["explanation"] = "Видовременная форма глагола"
            else:
                if spacy_model(item[3][0])[0].pos_ == "ADP":
                    correction["subtype"] = "пред"
                    correction["explanation"] = "Предлог"
                else:
                    correction["subtype"] = "видовр"
                    correction["explanation"] = "Видовременная форма глагола"
            correction["startSelection"] = word_offsets[start][0]
            correction["endSelection"] = word_offsets[end - 1][1]
            correction["correction"] = md.detokenize(item[4])
        elif "insert" == item[0]:
            normalized_correction = item[4][0].lower().translate(str.maketrans("", "", punct))
            correction["type"] = "А.грамм"
            after_pos = "".join([token.pos_ for token in spacy_model(normalized_correction)])
            if item[4][0] in punct and item[2][0] != len(before):
                start -= 1
                if before[start].lower() in FP_PUNCT_WORDS:
                    continue
                item[4].insert(0, before[start])
                correction["type"] = "А.пункт"
                continue  # выключили пунктуацию
            elif normalized_correction in ENG_ARTICLES:
                item[4].append(before[end])
                end += 1
                if item[4][-1] in ENG_ADJ_COMP or item[4][-1].endswith("est"):
                    correction["subtype"] = "сравн"
                    correction["explanation"] = "Форма степени сравнения прилагательного или наречия"
                else:
                    correction["subtype"] = "арт"
                    correction["explanation"] = f"Пропущен артикль {normalized_correction}"
            elif after_pos == "ADP":
                start -= 1
                item[4].insert(0, before[start])
                correction["subtype"] = "пред"
                correction["explanation"] = f"Пропущен предлог {normalized_correction}"
            else:
                correction["type"] = "А.грамм"
                if i + 1 < len(opcodes) and item[3:][::-1] == opcodes[i + 1][3:]:
                    skip = True
                    _start, _end = opcodes[i + 1][1]
                    item[4].extend(before[end:_start])
                    end = _end
                    correction["subtype"] = "поряд"
                    correction["explanation"] = "Порядок слов в предложении"
                elif ("ROOT" in [x.dep_ for x in after_parsed[item[2][0] : item[2][1] + 1]]) or (
                    "nsubj" in [x.dep_ for x in after_parsed[item[2][0] : item[2][1] + 1]]
                ):
                    if end >= len(before):
                        continue
                    item[4].append(before[end])
                    end += 1
                    correction["subtype"] = "проп"
                    correction[
                        "explanation"
                    ] = "Пропуск слова (подлежащего или сказуемого), влияющий на грамматическую структуру предложения"
                else:
                    start -= 1
                    item[4].insert(0, before[start])
                    correction["subtype"] = "видовр"
                    correction["explanation"] = "Видовременная форма глагола"
            correction["startSelection"] = word_offsets[start][0]
            if end > start:
                correction["endSelection"] = word_offsets[end - 1][1]
            else:
                correction["endSelection"] = correction["startSelection"]
            correction["correction"] = md.detokenize(item[4])
        ## ONLY FOR DEBUG ##
        # correction["source"] = before_text[correction["startSelection"]:correction["endSelection"]]
        if "explanation" not in correction:
            correction["explanation"] = correction["correction"]
        corrections.append(correction)
    return corrections
