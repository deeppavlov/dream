import argparse
import difflib
import re

import csv
import statistics

parser = argparse.ArgumentParser()
parser.add_argument("-pred_f", "--pred_file", type=str)
parser.add_argument("-true_f", "--true_file", type=str)
parser.add_argument("-time_limit", "--time_limit", type=float, default=3)

spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^a-z0-9 ]")

SPECIAL_SKILLS = {
    "RANDOM_SKILLS": [
        "dff_program_y_skill",
        "dummy_skill",
        "movie_tfidf_retrieval",
        "entertainment_tfidf_retrieval",
        "music_tfidf_retrieval",
        "personal_info_skill",
        "knowledge_grounding_skill",
        "dff_friendship_skill",
        "meta_script_skill",
        "comet_dialog_skill",
        "dummy_skill",
        "news_api_skill",
        "convert_reddit",
        "dff_grounding_skill",
        "dff_book_skill",
        "dff_movie_skill",
        "dff_music_skill",
        "dff_animals_skill",
        "dff_sport_skill",
        "dff_food_skill",
        "dff_weather_skill",
        "dff_bot_persona_skill",
        "dff_gaming_skill",
        "dff_gossip_skill",
        "dff_science_skill",
        "dff_travel_skill",
        "dff_wiki_skill",
        "dff_short_story_skill",
        "game_cooperative_skill",
        "dialogpt",
        "dialogpt_persona_based",
    ],
}


def clean_text(text):
    return special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()


def main():
    args = parser.parse_args()

    with open(args.pred_file, "r", newline="") as f:
        reader = csv.reader(f, delimiter=" ")
        pred_data = [row for row in reader][1:]
        active_skills = [row[1] for row in pred_data]
        pred_data = [row[-4:] for row in pred_data]

    with open(args.true_file, "r", newline="") as f:
        reader = csv.reader(f, delimiter=" ")
        true_data = [row for row in reader][1:]
    proc_times = [float(r[0]) for r in pred_data]
    mean_proc_time = statistics.mean(proc_times)

    print(f"Mean proc time: {mean_proc_time}")
    assert statistics.mean(proc_times) <= args.time_limit, print(
        f"Mean proc time: {mean_proc_time} > {args.time_limit}"
    )

    error_reports = []

    for pred_r, true_r, skill in zip(pred_data, true_data, active_skills):
        true_sents = set([sent.lower().replace("\n", " ").replace("  ", " ") for sent in true_r[2:]])
        acceptable_skill_names = true_r[0]
        assert skill != "exception", print("ERROR: {} not in {}".format(pred_r[-1], true_sents))

        passed_acceptable_skills = True
        passed_gold_phrases = True

        if acceptable_skill_names.strip():
            if acceptable_skill_names[0] == "!":
                # отрицание возможно только для одного скилла!!!
                skill_name = acceptable_skill_names[1:]
                if skill != skill_name:
                    passed_acceptable_skills = False
                    print(f"FOUND POSSIBLE ERROR: pred skill: {skill} is PROHIBITED: {skill_name}")
            else:
                acceptable_skill_names = acceptable_skill_names.split(";")
                acceptable_skill_names = sum(
                    [SPECIAL_SKILLS.get(skill_name, [skill_name]) for skill_name in acceptable_skill_names], []
                )
                if skill in acceptable_skill_names:
                    pass
                else:
                    passed_acceptable_skills = False
                    print(
                        f"FOUND POSSIBLE ERROR: pred skill: {skill} "
                        f"NOT IN Acceptable skill names: {acceptable_skill_names}"
                    )

        if true_sents:
            checked = False
            for true_sent in true_sents:
                true_cl_text = clean_text(true_sent)
                pred_cl_text = clean_text(pred_r[-1])
                if true_cl_text in pred_cl_text:
                    checked = True
                elif difflib.SequenceMatcher(None, true_cl_text.split(), pred_cl_text.split()).ratio() > 0.9:
                    checked = True
            if not checked:
                passed_gold_phrases = False
                print(f"FOUND POSSIBLE ERROR: {pred_r[-1]} by skill {skill} not in {true_sents}")

        if len(acceptable_skill_names) > 0 or len(true_sents) > 0:
            if (len(acceptable_skill_names) > 0 and passed_acceptable_skills) or (
                len(true_sents) > 0 and passed_gold_phrases
            ):
                continue
            else:
                error_reports += [
                    f"\nERROR!!!\nAcceptable skill names: `{acceptable_skill_names}`.\n"
                    f"Passed acceptable skill names: `{passed_acceptable_skills}`.\n"
                    f"True sentences: `{true_sents}`.\n"
                    f"Passed true sentences: `{passed_gold_phrases}`.\n"
                    f"Skill: {skill}\nSkill output: {pred_r[-1]}"
                ]
    print("\n\nASSERTION RESULTS:\n")
    assert len(error_reports) == 0, print("\n\n".join(error_reports))


if __name__ == "__main__":
    main()
