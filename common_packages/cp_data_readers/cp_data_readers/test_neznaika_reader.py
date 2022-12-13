from pathlib import Path

from cp_data_readers.neznaika_reader import read

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent.parent.parent
    dataset_dir = project_dir / "data" / "datasets" / "neznaika.v2"
    infiles = ["eng/train/eng-write_2833_parsed.json", "his/train/hist-write_7006_parsed.json"]
    subjects = ["английский", "история"]
    for infile, subject in zip(infiles[::-1], subjects[::-1]):
        infile = dataset_dir / infile
        output = read(infile, subject=subject)
        # for key, key_errors in output["annotations"].items():
        #     for error in key_errors:
        #         assert error["text"] == output["clear_essay"][error["start_span"] : error["end_span"]]
