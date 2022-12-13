import json
import pathlib

from cp_data_readers.neznaika_reader import _parse_text

if __name__ == "__main__":
    file_name = "hist-write_7006_parsed_input.json"
    dataset_dir = pathlib.Path("/cephfs/home/sorokin/ProChtenie/Agent/services/annotators/basic_reader/test_data/")

    output_dir = pathlib.Path("dump")
    output_dir.mkdir(exist_ok=True)

    input_file = dataset_dir / file_name
    output_file = output_dir / file_name

    with input_file.open() as f:
        text = json.load(f)
    output = _parse_text(text, input_file.name)
    with input_file.open("wt") as f:
        json.dump(output, f, ensure_ascii=False)
