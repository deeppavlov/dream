import json
import pathlib

from cp_data_readers.utils import clear_text, open_json

SUBJECT_LIST = ["русский язык", "литература", "история", "обществознание", "английский"]


def update_full_map(broken_types_dict={}, previous_full_map={}):

    full_map = previous_full_map.copy()

    preprocessed_broken_types_dict = {}

    for key in broken_types_dict.keys():
        if key == "common_mistakes":
            preprocessed_broken_types_dict[key] = {
                clear_text(raw_type): clear_type for raw_type, clear_type in broken_types_dict[key].items()
            }
        else:
            preprocessed_broken_types_dict[key] = {}
            for subject in SUBJECT_LIST:
                preprocessed_broken_types_dict[key][subject] = {
                    clear_text(raw_type): clear_type for raw_type, clear_type in broken_types_dict[key][subject].items()
                }

    for subject in SUBJECT_LIST:
        full_map[subject]["sections"].update(preprocessed_broken_types_dict["sections"].get(subject, {}))
        full_map[subject]["mistakes"].update(preprocessed_broken_types_dict["mistakes"].get(subject, {}))
        if subject != "английский":
            full_map[subject]["mistakes"].update(preprocessed_broken_types_dict.get("common_mistakes", {}))

    return full_map


if __name__ == "__main__":

    current_dir = pathlib.Path(__file__).parent / "annotations_data"

    previous_full_map_path = current_dir / "full_map.json"
    output_path = current_dir / "full_map.json"
    broken_types_path = current_dir / "broken_types.json"

    previous_full_map = open_json(previous_full_map_path)
    broken_types = open_json(broken_types_path)

    new_full_map = update_full_map(broken_types, previous_full_map)

    with open(output_path, "w") as f:
        json.dump(new_full_map, f, ensure_ascii=False, indent=4)
