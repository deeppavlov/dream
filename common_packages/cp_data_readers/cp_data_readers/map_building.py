import json
import pathlib

from cp_data_readers.map_update import SUBJECT_LIST, update_full_map
from cp_data_readers.utils import clear_text, open_json


def generate_common_annotations(criteria):
    current_map = {}
    for annotation, subannotations in criteria.items():
        if annotation[1] == ".":
            capital_type = annotation[:2]
        else:
            capital_type = ""
        current_map[clear_text(annotation)] = annotation
        for subannotation in subannotations:
            current_map[capital_type.lower() + clear_text(subannotation)] = annotation
            current_map[clear_text(annotation + subannotation)] = annotation
    return current_map


def build_standard_full_map(sections_and_criteria):

    full_map = {}

    for subject in SUBJECT_LIST:

        sections_dict = {section: [] for section in sections_and_criteria["sections"][subject]}

        if subject != "английский":
            criteria_dict_copy = sections_and_criteria["criteria"][subject]
            criteria_dict_copy.update(sections_and_criteria["common_mistakes"])
        else:
            criteria_dict_copy = sections_and_criteria["criteria"][subject]

        mistake_map = generate_common_annotations(criteria_dict_copy)
        sections_map = generate_common_annotations(sections_dict)
        full_map[subject] = {"mistakes": mistake_map, "sections": sections_map}

    return full_map


if __name__ == "__main__":

    current_dir = pathlib.Path(__file__).parent / "annotations_data"

    sections_and_criteria_path = current_dir / "sections_and_criteria.json"
    previous_full_map_path = current_dir / ""
    broken_types_path = current_dir / "broken_types.json"
    output_path = current_dir / "full_map.json"

    sections_and_criteria = open_json(sections_and_criteria_path)
    previous_full_map = open_json(previous_full_map_path)
    broken_types = open_json(broken_types_path)

    standard_full_map = build_standard_full_map(sections_and_criteria)
    full_map = update_full_map(broken_types, standard_full_map)

    if previous_full_map:
        for subject in SUBJECT_LIST:
            for section in previous_full_map[subject]["sections"].keys():
                if section not in full_map[subject]["sections"].keys():
                    full_map[subject]["sections"][section] = previous_full_map[subject]["sections"][section].copy()
            for section in previous_full_map[subject]["mistakes"].keys():
                if section not in full_map[subject]["mistakes"].keys():
                    full_map[subject]["mistakes"][section] = previous_full_map[subject]["mistakes"][section].copy()

    with open(output_path, "w") as fout:
        json.dump(full_map, fout, ensure_ascii=False, indent=4)
