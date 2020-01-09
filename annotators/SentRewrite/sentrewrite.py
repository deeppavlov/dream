import neuralcoref
import spacy
from nltk import sent_tokenize
from yesno_question import yesno_question

nlp = spacy.load("en_core_web_sm")
neuralcoref.add_to_pipe(nlp)
ynq = yesno_question()


def distance(ner, mention):
    inside = (ner["start_pos"] >= mention["start"] - 1) and (ner["end_pos"] <= mention["end"] + 1)
    offset = abs(ner["start_pos"] - mention["start"]) + abs(ner["end_pos"] - mention["end"])
    return inside, offset


def recover_mentions(dialog, ner_dialog):
    # replace mentions of each cluster with the main one.
    # dialog: [utterance -> sentence]
    # ner_dialog: [utterance -> sentence -> ner (dict: confidence, start_pos, end_pos, text, type)]

    # change start_pos, end_pos to dialog level in order to be suitable to clusters below
    ners = []
    pos_sent = 0
    for i, utterance in enumerate(ner_dialog):
        for j, sent in enumerate(utterance):
            for ner in sent:
                if ner["confidence"] < 0.6:
                    continue
                ners.append({"confidence": ner["confidence"],
                             "start_pos": ner["start_pos"] + pos_sent,
                             "end_pos": ner["end_pos"] + pos_sent,
                             "text": ner["text"],
                             "type": ner["type"]})
            if i == j == 0:
                pos_sent = len(dialog[0][0]) + 1
            else:
                pos_sent += (len(dialog[i][j]) + 1)

    discourse = " ".join([" ".join(utterance) for utterance in dialog])
    doc = nlp(discourse)
    if doc._.has_coref:
        # list of clusters: [cluster -> mention (dict: start, end, text, resolved)]
        clusters = [[{"start": mention.start_char,
                      "end": mention.end_char,
                      "text": mention.text,
                      "resolved": cluster.main.text,
                      "ner": {"type": "O", "offset": 10000}
                      }
                     for mention in cluster.mentions]
                    for cluster in doc._.coref_clusters
                    ]

        new_clusters = []
        # find the main mention for each cluster
        for cluster in clusters:
            if len(cluster) == 0:
                continue
            main_mention = cluster[0]
            for mention in cluster:
                # find the main ner for each mention, which will be used to decide which mention is the main
                for ner in ners:
                    inside, offset = distance(ner, mention)
                    if inside:
                        if mention["ner"]["offset"] > offset:
                            mention["ner"] = {"type": ner["type"], "offset": offset}
                if main_mention["ner"]["type"] == "O":
                    main_mention = mention
                elif mention["ner"]["offset"] < main_mention["ner"]["offset"]:
                    main_mention = mention

            # change main mention if necessary
            if main_mention["ner"]["type"] != "O":
                new_clusters.append(cluster)
                for m in new_clusters[-1]:
                    m["resolved"] = main_mention["resolved"]
            # keep cluster refer to pronouns
            else:
                pronouns = ["i", "we", "you", "he", "she", "it", "they",
                            "me", "us", "him", "her", "them"]

                # check if cluster refer to pronouns
                is_pronoun_cluster = False
                for m in cluster:
                    if m["text"] in pronouns:
                        is_pronoun_cluster = True
                        break
                if is_pronoun_cluster:
                    new_resolved = cluster[0]["resolved"]
                    if new_resolved in pronouns:
                        for m in cluster:
                            if m["text"] not in pronouns:
                                new_resolved = m["text"]
                                break
                    if new_resolved not in pronouns:
                        new_clusters.append(cluster)
                        for m in new_clusters[-1]:
                            m["resolved"] = new_resolved

        mentions = [mention for cluster in new_clusters for mention in cluster]
        sorted_mentions = sorted(mentions, key=lambda i: i["start"], reverse=True)

        dialog = [" ".join(utterance) for utterance in dialog]
        new_utter_pos = [{"start": 0, "end": len(dialog[0])}]
        for i in range(1, len(dialog)):
            new_utter_pos.append(
                {"start": new_utter_pos[-1]["end"] + 1, "end": new_utter_pos[-1]["end"] + 1 + len(dialog[i])})

        current_utterance_idx = len(dialog) - 1
        for mention in sorted_mentions:
            while mention["start"] < new_utter_pos[current_utterance_idx]["start"]:
                current_utterance_idx -= 1

            discourse = discourse[: mention["start"]] + mention["resolved"] + discourse[mention["end"]:]

            offset = len(mention["resolved"]) - len(mention["text"])
            new_utter_pos[current_utterance_idx]["end"] += offset
            for i in range(current_utterance_idx + 1, len(dialog)):
                new_utter_pos[i]["start"] += offset
                new_utter_pos[i]["end"] += offset

        new_dialog = []
        for i in range(len(dialog)):
            new_dialog.append(discourse[new_utter_pos[i]["start"]: new_utter_pos[i]["end"]])
    else:
        new_clusters = []
        new_dialog = [" ".join(utterance) for utterance in dialog]

    # rewrite short answers for yes/no questions
    final_dialog = []
    if len(new_dialog) < 2:
        final_dialog = new_dialog
    else:
        final_dialog.append(new_dialog[0])
        for i in range(len(new_dialog) - 1):
            final_dialog.append(new_dialog[i + 1])
            sents = sent_tokenize(new_dialog[i])
            if len(sents) > 0:
                question = sents[-1]
                sents = sent_tokenize(new_dialog[i + 1])
                if len(sents) > 0:
                    answer = sents[0]
                    if question != "" and answer != "":
                        full_answer = ynq.rewrite_yesno_answer(question, answer)
                        if full_answer != "":
                            final_dialog[-1] = full_answer + " " + " ".join(sents[1:])

    return {"clusters": new_clusters, "modified_sents": final_dialog}
