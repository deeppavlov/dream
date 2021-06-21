import argparse
import json
import logging
import os
import re
import shutil
import subprocess
from datetime import datetime


logging.basicConfig(format='%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


VERSION_PATTERN = re.compile(r"^v([0-9]+\.)*([0-9]+)$")
_date_time_re = r"[0-9]{4}(\.[0-9]{2}){2}_[0-9]{2}:[0-9]{2}"
DUMP_PATTERN = re.compile(rf"^time_interval_logs_{_date_time_re}-{_date_time_re}.json$")

DATE_FORMAT = "%Y.%m.%d"

S3_DUMPS_PATH = "s3://dp-dream-alexa-dumps/"

COUNT = "count"
CHANGED = "changed_skill"
CONTINUED = "continued_skill"
TERMINATED = "terminated_dialog"
NO_SKILL = "next_bot_utterance_have_sno_active_skill"
OBLIGATORY_COUNT_KEYS = [COUNT, CHANGED, CONTINUED, TERMINATED]

PROCESSED_DUMPS_FILE = "list_of_processed_dumps.json"


processed_dialogs = set()


def parse_args():
    parser = argparse.ArgumentParser(
        description=f"This script is used for collecting user answer statistics. For each skill and for each bot "
                    f"utterance the number of times each human answer occurred is calculated. For each human answer "
                    f"were calculated: 1) the number of times an active skill continued on the next utterance, "
                    f"2) the number of times an active skill changed on the next bot utterance, 3) the number of "
                    f"times a dialog stopped. Statistics for each bot version is saved in a separate file in "
                    f"`--stats-dir` directory. The stats are collected from S3 dumps. S3 dumps can be downloaded "
                    f"independently or by this script (do not provide the `--input-files` parameter if you wish to "
                    f"download from AWS). If you want to update existing statistics, you should set option "
                    f"`--update-existing-stats` and provide path to existing statistics in "
                    f"`--stats-dir`. If parameter `--input-files` is not provided, statistics for dumps that are "
                    f"missing in the list of processed dumps '{{stats_dir}}/{PROCESSED_DUMPS_FILE}' but present in "
                    f"directory `--dumps-dir` will be calculated and added to stats in directory `--stats-dir`. "
                    f"If the option `--download` is set, dumps on AWS S3 which are missing in "
                    f"'{{stats_dir}}/{PROCESSED_DUMPS_FILE}' and `--dumps-dir` will be downloaded to `--dumps-dir`."
    )
    parser.add_argument(
        "--input-files",
        "-i",
        nargs="+",
        help="Paths to json files with dialog dumps in the format this files are provided on AWS S3. If this parameter "
             "is provided, parameters `--dumps-dir` and `--download` are ignored. Parameter `--update-existing-stats` "
             "is still working if `--input-files` are provided."
    )
    parser.add_argument(
        "--stats-dir",
        "-s",
        help=f"Path to directory where statistics and the file '{{stats_dir}}/{PROCESSED_DUMPS_FILE}' are saved.",
        default="answer_stats",
    )
    parser.add_argument(
        "--dumps-dir",
        "-d",
        help="Path to directory where dumps of Alexa Prize dialogs are placed. If download from AWS S3 is performed, "
             "downloaded dumps are saved into `--dumps-dir`.",
        default="dialog_dumps",
    )
    parser.add_argument(
        "--start_date",
        "-t",
        help="Starting date in format yyyy.mm.dd for relevant dumps. Dumps which older dialogs are not used.",
        default="2021.06.01",
    )
    parser.add_argument(
        "--update-existing-stats",
        "-u",
        help="Statistics in `--stats-dir` are upgraded using either `--input-files` or unprocessed dumps from "
             "`--dumps-dir` and AWS S3.",
        action="store_true",
    )
    parser.add_argument(
        "--download",
        "-L",
        help="Look for unprocessed dumps on AWS S3. If this option is not provided, only unused dumps from "
             "`--dumps-dir` are used for calculating stats.",
        action="store_true",
    )
    parser.add_argument(
        "--max-mega-bytes",
        "-m",
        type=float,
        default=750.0,
        help="The maximum disk space in MB taken by dumps which are simultaneously loaded into RAM. If you increase "
             "this parameter, the script works faster since it updates and saves stats less frequently. The amount "
             "RAM taken by the script is approximately three times larger than `--max-mega-bytes`."
    )
    args = parser.parse_args()
    args.start_date = datetime.strptime(args.start_date, DATE_FORMAT)
    return args


def is_human(utterance):
    if "attributes" not in utterance:
        logger.warning(f"No key 'attributes' in utterance {utterance}. "
                       f"This utterance marked as belonging neither to bot nor to human.")
        return None
    return "version" in utterance["attributes"]


def get_bot_version(utterances):
    version = None
    for uttr in utterances:
        if "attributes" not in uttr:
            logger.warning(f"No key 'attributes' in utterance {uttr}. "
                           f"This utterance marked as belonging neither to bot nor to human.")
            continue
        if "version" in uttr["attributes"]:
            version = uttr["attributes"]["version"]
            if version is not None and VERSION_PATTERN.match(version):
                break
            else:
                logger.warning(f"Found version {version} which does not match pattern {VERSION_PATTERN.pattern}")
                version = None
                break
    return version


def get_first_bot_utterance_index(utterances):
    first_index = None
    for i, uttr in enumerate(utterances):
        if "attributes" not in uttr:
            logger.warning(f"No key 'attributes' in utterance {uttr}")
        if "version" not in uttr["attributes"]:
            first_index = i
            break
    return first_index


def split_into_bot_and_human_utterances(utterances, dialog_id, dump_file_name):
    bot_utterances, human_utterances = [], []
    prev_speaker = ""
    for i, uttr in enumerate(utterances):
        ishuman = is_human(uttr)
        if ishuman is None:
            logger.warning(f"Aborting splitting utterances be speakers for dialog {dialog_id} from "
                           f"dump {dump_file_name} because dialog contains utterance which cannot be recognised as "
                           f"human or bot utterance. Lists with bot and human utterances are made empty to avoid "
                           f"errors.")
            return [], []
        speaker = "human" if ishuman else "bot"
        if prev_speaker == speaker:
            logger.warning(f"Utterances with numbers {i-1} and {i} in both belong to human. "
                           f"Dialog: {dialog_id}, dump: {dump_file_name}")
        if speaker == "human":
            human_utterances.append(uttr)
        else:
            bot_utterances.append(uttr)
    return bot_utterances, human_utterances


def get_answer_stats_from_dialog_dumps(dumps):
    stats = {}
    for dump_file_name, dump in dumps.items():
        logger.info(f"Collecting stats from dump {dump_file_name}")
        number_of_dialogs_without_human_replicas = 0
        for dialog in dump:
            if dialog['id'] in processed_dialogs:
                continue
            else:
                processed_dialogs.add(dialog['id'])
            utterances = dialog["utterances"]
            bot_version = get_bot_version(utterances)
            if bot_version is None:
                logger.warning(f"No version for dialog {dialog['id']} from dump {dump_file_name} was found. "
                               f"All utterances in dialog are made by bot. Skipping dialog...")
                number_of_dialogs_without_human_replicas += 1
                continue
            if bot_version not in stats:
                stats[bot_version] = {"dumps": [dump_file_name], "skills": {}}
                skills = stats[bot_version]["skills"]
            else:
                if dump_file_name not in stats[bot_version]["dumps"]:
                    stats[bot_version]["dumps"].append(dump_file_name)
                skills = stats[bot_version]["skills"]
            first_bot_utterance_index = get_first_bot_utterance_index(utterances)
            if first_bot_utterance_index is None:
                logger.warning(f"No bot utterances was found in {dialog['id']} from dump {dump_file_name}. "
                               f"Skipping...")
                continue
            if first_bot_utterance_index == 0:
                logger.warning(f"First utterance in dialog {dialog['id']} from dump {dump_file_name} was made by bot")
            else:
                utterances = utterances[1:]
            bot_utterances, human_utterances = split_into_bot_and_human_utterances(
                utterances, dialog["id"], dump_file_name)
            for i, (bot_u, human_u) in enumerate(zip(bot_utterances, human_utterances)):
                bot_text, human_text = bot_u.get("text"), human_u.get("text")
                if bot_text is None:
                    logger.warning(
                        f"No text in bot utterance {bot_u} from dialog {dialog['id']} from dump {dump_file_name}")
                    continue
                if human_text is None:
                    logger.warning(
                        f"No text in human utterance {human_u} from dialog {dialog['id']} from dump {dump_file_name}")
                    continue
                if bot_text.startswith("alexa handler:"):
                    continue
                active_skill = bot_u.get("active_skill")
                if active_skill is None:
                    logger.warning(f"There is not active skill for bot utterance {bot_u} in dialog {dialog['id']} """
                                   f"in dump {dump_file_name}. Skipping utterance pair {bot_u} and {human_u}...")
                    continue
                if active_skill not in skills:
                    skills[active_skill] = {}
                bot_text = bot_text.split('#')[0].strip()  # remove suffixes like #+#repeat
                if bot_text not in skills[active_skill]:
                    skills[active_skill][bot_text] = {
                        COUNT: 1,
                        CHANGED: 0,
                        CONTINUED: 0,
                        TERMINATED: 0,
                        "human_answers": {}
                    }
                else:
                    skills[active_skill][bot_text][COUNT] += 1
                if human_text not in skills[active_skill][bot_text]["human_answers"]:
                    answer_stats = {
                        COUNT: 1,
                        CHANGED: {"count": 0, "dialogs": []},
                        CONTINUED: {"count": 0, "dialogs": []},
                        TERMINATED: {"count": 0, "dialogs": []},
                    }
                    skills[active_skill][bot_text]["human_answers"][human_text] = answer_stats
                else:
                    answer_stats = skills[active_skill][bot_text]["human_answers"][human_text]
                    answer_stats[COUNT] += 1
                if i + 1 < len(bot_utterances) and not human_text.startswith("/"):
                    next_active_skill = bot_utterances[i + 1].get("active_skill")
                    if next_active_skill is None:
                        logger.warning(f"There is not active skill for bot utterance {bot_utterances[i+1]} in dialog "
                                       f"{dialog['id']} in dump {dump_file_name}.")
                        if NO_SKILL not in answer_stats:
                            answer_stats[NO_SKILL] = {
                                "count": 1, "dialogs": [dialog['id']]}
                            skills[active_skill][bot_text][NO_SKILL] = 1
                        else:
                            answer_stats["next_bot_utterance_have_sno_active_skill"]["count"] += 1
                            answer_stats[NO_SKILL]["dialogs"].append(dialog['id'])
                            skills[active_skill][bot_text][NO_SKILL] += 1
                    elif next_active_skill == active_skill:
                        answer_stats[CONTINUED]["count"] += 1
                        answer_stats[CONTINUED]["dialogs"].append(dialog['id'])
                        skills[active_skill][bot_text][CONTINUED] += 1
                    else:
                        answer_stats[CHANGED]["count"] += 1
                        answer_stats[CHANGED]["dialogs"].append(dialog['id'])
                        skills[active_skill][bot_text][CHANGED] += 1
                else:
                    answer_stats[TERMINATED]["count"] += 1
                    answer_stats[TERMINATED]["dialogs"].append(dialog['id'])
                    skills[active_skill][bot_text][TERMINATED] += 1
        logger.info(f"{number_of_dialogs_without_human_replicas}/{len(dump)} dialogs without human replicas in "
                    f"dump {dump_file_name}")
    return stats


def update_stats(stats_to_update, update, version):
    logger.info(f"Updating stats for version {version}")
    for dump_file_name in update["dumps"]:
        if dump_file_name not in stats_to_update["dumps"]:
            stats_to_update["dumps"].append(dump_file_name)
        else:
            logger.info(f"Dump {dump_file_name} was already used in stats for version {version}")
    for skill, skill_answers in update["skills"].items():
        if skill not in stats_to_update['skills']:
            stats_to_update["skills"][skill] = skill_answers
        else:
            for bot_text, answers_to_bot_utterance in update["skills"][skill].items():
                if bot_text not in stats_to_update["skills"][skill]:
                    stats_to_update["skills"][skill][bot_text] = answers_to_bot_utterance
                else:
                    for key in OBLIGATORY_COUNT_KEYS:
                        stats_to_update["skills"][skill][bot_text][key] += update["skills"][skill][bot_text][key]
                    if NO_SKILL in update["skills"][skill][bot_text]:
                        if NO_SKILL in stats_to_update["skills"][skill][bot_text]:
                            stats_to_update["skills"][skill][bot_text][NO_SKILL] \
                                += update["skills"][skill][bot_text][NO_SKILL]
                        else:
                            stats_to_update["skills"][skill][bot_text][NO_SKILL] \
                                = update["skills"][skill][bot_text][NO_SKILL]
                    for human_text, answer_stats in update["skills"][skill][bot_text]["human_answers"].items():
                        if human_text not in stats_to_update["skills"][skill][bot_text]["human_answers"]:
                            stats_to_update["skills"][skill][bot_text]["human_answers"][human_text] = answer_stats
                        else:
                            updated_answer_stats = \
                                stats_to_update["skills"][skill][bot_text]["human_answers"][human_text]
                            answers_stats_update = update["skills"][skill][bot_text]["human_answers"][human_text]
                            updated_answer_stats[COUNT] += answers_stats_update[COUNT]
                            keys = [CHANGED, CONTINUED, TERMINATED]
                            if NO_SKILL in answers_stats_update:
                                if NO_SKILL in updated_answer_stats:
                                    keys.append(NO_SKILL)
                                else:
                                    updated_answer_stats[NO_SKILL] = answers_stats_update[NO_SKILL]
                            for key in keys:
                                dialogs_set = set(updated_answer_stats[key]["dialogs"])
                                for d_id in answers_stats_update[key]["dialogs"]:
                                    if d_id in dialogs_set:
                                        logger.warning(
                                            f"Dialog with id {d_id} is already in stats for answer '{human_text}' on "
                                            f"bot utterance '{bot_text}', skill '{skill}', version {version}.")
                                    else:
                                        updated_answer_stats[key]["dialogs"].append(d_id)
                                updated_answer_stats[key]["count"] += answers_stats_update[key]["count"]


def load_json_files(file_names):
    res = {}
    for fn in file_names:
        with open(fn) as f:
            res[os.path.split(fn)[-1]] = json.load(f)
    return res


def sort_stats_by_utterance_frequency_and_skill_name(stats):
    stats["skills"] = dict(sorted(stats["skills"].items(), key=lambda x: x[0]))
    for skill, skill_stats in stats["skills"].items():
        stats["skills"][skill] = dict(sorted(skill_stats.items(), key=lambda x: -x[1][COUNT]))
        for bot_stats in stats["skills"][skill].values():
            bot_stats["human_answers"] = dict(sorted(bot_stats["human_answers"].items(), key=lambda x: -x[1][COUNT]))


def load_update_and_save_existing_stats(stats_dir, stats):
    logger.info("Updating existing answer stats")
    os.makedirs(stats_dir, exist_ok=True)
    for version, v_stats in stats.items():
        path = os.path.join(stats_dir, version) + '.json'
        if os.path.isfile(path):
            logger.info(f"Found existing stats for version {version}")
            with open(path) as f:
                saved_stats = json.load(f)
            update_stats(saved_stats, v_stats, version)
            sort_stats_by_utterance_frequency_and_skill_name(saved_stats)
            with open(path, 'w') as f:
                json.dump(saved_stats, f, indent=2)
        else:
            logger.info(f"No existing stats for version {version} were found. New stats are saved.")
            sort_stats_by_utterance_frequency_and_skill_name(v_stats)
            with open(path, 'w') as f:
                json.dump(v_stats, f, indent=2)


def save_stats(stats_dir, stats):
    logger.info(f"Saving answer stats to directory {stats_dir}")
    os.makedirs(stats_dir, exist_ok=True)
    for version, v_stats in stats.items():
        path = os.path.join(stats_dir, version) + ".json"
        with open(path, 'w') as f:
            sort_stats_by_utterance_frequency_and_skill_name(v_stats)
            json.dump(v_stats, f, indent=2)


def get_remote_dumps_file_names():
    out = subprocess.run(["aws", "s3", "ls", S3_DUMPS_PATH], stdout=subprocess.PIPE)
    remote_file_names = [line.split()[-1] for line in out.stdout.decode('utf-8').split('\n') if line]
    logger.info(f"{len(remote_file_names)} remote files were found.")
    return remote_file_names


def filter_dumps_by_time(dumps, start_time):
    return [d for d in dumps if datetime.strptime(d.split('_')[3], DATE_FORMAT) >= start_time]


def get_names_of_unprocessed_dumps_on_aws(dumps_dir, processed_dumps_file, start_time):
    logger.info("Looking for unprocessed dump files on aws...")
    if os.path.isfile(processed_dumps_file):
        with open(processed_dumps_file) as f:
            processed_dumps = set(json.load(f))
    else:
        processed_dumps = set()
    remote_dumps = set(filter_dumps_by_time(get_remote_dumps_file_names(), start_time))
    local_dumps = {fn for fn in os.listdir(dumps_dir) if DUMP_PATTERN.match(fn)}
    unprocessed_dumps = [os.path.join(dumps_dir, fn) for fn in remote_dumps - processed_dumps]
    missing_dumps = [os.path.join(dumps_dir, fn) for fn in remote_dumps - processed_dumps - local_dumps]
    logger.info(f"{len(unprocessed_dumps)} unprocessed files were found.")
    logger.info(f"{len(missing_dumps)} missing (which have to be downloaded) files were found.")
    return unprocessed_dumps, missing_dumps


def get_names_of_unprocessed_dumps_on_local_machine(dumps_dir, processed_dumps_file, start_time):
    logger.info(f"Looking for unprocessed dump files in directory '{dumps_dir}'...")
    logger.info(f"{[os.path.splitext(fn)[0] for fn in os.listdir(dumps_dir)[:20]]}")
    local_dumps = set(filter_dumps_by_time([fn for fn in os.listdir(dumps_dir) if DUMP_PATTERN.match(fn)], start_time))
    if os.path.isfile(processed_dumps_file):
        with open(processed_dumps_file) as f:
            processed_dumps = set(json.load(f))
    else:
        processed_dumps = set()
    unprocessed_dumps = [os.path.join(dumps_dir, fn) for fn in local_dumps - processed_dumps]
    logger.info(f"{len(unprocessed_dumps)} unprocessed files were found.")
    return unprocessed_dumps


def download_files_from_aws(file_names, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    for fn in file_names:
        subprocess.run(["aws", "s3", "cp", S3_DUMPS_PATH + os.path.split(fn)[-1], save_dir])


def collect_all_processed_dialogs(stats_dir):
    for elem in os.listdir(stats_dir):
        path = os.path.join(stats_dir, elem)
        if os.path.isfile(path) and VERSION_PATTERN.match(os.path.splitext(elem)[0]):
            with open(path) as f:
                stats = json.load(f)
                for skill_stats in stats["skills"].values():
                    for bot_utterance_stats in skill_stats.values():
                        for human_utterance_stats in bot_utterance_stats["human_answers"].values():
                            for key in [CHANGED, CONTINUED, TERMINATED]:
                                processed_dialogs.update(human_utterance_stats[key]["dialogs"])
                            if NO_SKILL in human_utterance_stats:
                                processed_dialogs.update(human_utterance_stats[NO_SKILL]["dialogs"])
    logger.info(f"Found {len(processed_dialogs)} dialogs which are already processed.")


def split_dumps_into_groups_for_loading(file_names, max_total_size_in_mb):
    groups = []
    group = []
    mb = 2 ** 20
    max_size_bytes = max_total_size_in_mb * mb
    group_size_bytes = 0
    for fn in file_names:
        file_size_bytes = os.path.getsize(fn)
        if file_size_bytes > max_size_bytes:
            raise ValueError(
                f"Increase the value of the script parameter `--max-mega-bytes` at least to "
                f"{file_size_bytes // mb + 1} because the size of file {fn} is larger than current parameter value "
                f"{max_total_size_in_mb}."
            )
        group_size_bytes += file_size_bytes
        if group_size_bytes > max_size_bytes:
            groups.append(group)
            group = [fn]
            group_size_bytes = file_size_bytes
        else:
            group.append(fn)
            group_size_bytes += file_size_bytes
    if group:
        groups.append(group)
    return groups


def update_list_of_processed_dumps(list_of_processed_dumps_file, new_processed_dumps):
    new_processed_dumps = {os.path.split(p)[-1] for p in new_processed_dumps}
    if os.path.isfile(list_of_processed_dumps_file):
        with open(list_of_processed_dumps_file) as f:
            data = json.load(f)
        data = set(data)
        if data & new_processed_dumps:
            logger.warning(f"Dumps {data & set(new_processed_dumps)} were processed despite the fact that they are "
                           f"present in the list {list_of_processed_dumps_file}")
        data |= new_processed_dumps
    else:
        if os.path.isdir(list_of_processed_dumps_file):
            logger.warning(
                f"'{list_of_processed_dumps_file}' is a directory. Removing '{list_of_processed_dumps_file}'")
            shutil.rmtree(list_of_processed_dumps_file)
        data = new_processed_dumps
    with open(list_of_processed_dumps_file, 'w') as f:
        json.dump(list(data), f, indent=2)


def main():
    args = parse_args()
    if args.update_existing_stats and os.path.isdir(args.stats_dir):
        collect_all_processed_dialogs(args.stats_dir)
    processed_dumps_file = os.path.join(args.stats_dir, PROCESSED_DUMPS_FILE)
    if args.input_files is not None:
        num_processed_dumps = 0
        for dumps_for_loading in split_dumps_into_groups_for_loading(args.input_files, args.max_mega_bytes):
            logger.info(f"{num_processed_dumps}/{len(args.input_files)} new dumps processed")
            num_processed_dumps += len(dumps_for_loading)
            stats = get_answer_stats_from_dialog_dumps(load_json_files(dumps_for_loading))
            if args.update_existing_stats:
                load_update_and_save_existing_stats(args.stats_dir, stats)
            else:
                save_stats(args.stats_dir, stats)
            update_list_of_processed_dumps(processed_dumps_file, dumps_for_loading)
    else:
        if args.download:
            unprocessed_file_names, missing_file_names = get_names_of_unprocessed_dumps_on_aws(
                args.dumps_dir, processed_dumps_file, args.start_date)
            download_files_from_aws(missing_file_names, args.dumps_dir)
        else:
            unprocessed_file_names = get_names_of_unprocessed_dumps_on_local_machine(
                args.dumps_dir, processed_dumps_file, args.start_date)
        num_processed_dumps = 0
        for dumps_for_loading in split_dumps_into_groups_for_loading(unprocessed_file_names, args.max_mega_bytes):
            logger.info(f"{num_processed_dumps}/{len(unprocessed_file_names)} new dumps processed")
            num_processed_dumps += len(dumps_for_loading)
            stats = get_answer_stats_from_dialog_dumps(load_json_files(dumps_for_loading))
            if args.update_existing_stats:
                load_update_and_save_existing_stats(args.stats_dir, stats)
            else:
                save_stats(args.stats_dir, stats)
            update_list_of_processed_dumps(processed_dumps_file, dumps_for_loading)


if __name__ == "__main__":
    main()
