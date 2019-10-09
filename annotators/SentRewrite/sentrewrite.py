import spacy
import neuralcoref

nlp = spacy.load('en_core_web_sm')
neuralcoref.add_to_pipe(nlp)


def recover_mentions(dialog):
    # dialog: list of utterances, each utterance could have several sentences

    discourse = " ".join(dialog)
    doc = nlp(discourse)
    if not doc._.has_coref:
        return {"clusters": [], "modified_sents": dialog}
    else:
        clusters = [[{'start': mention.start_char,
                      'end': mention.end_char,
                      'text': mention.text,
                      'resolved': cluster.main.text
                      }
                     for mention in cluster.mentions]
                    for cluster in doc._.coref_clusters
                    ]

        mentions = [mention for cluster in clusters for mention in cluster]

        sorted_mentions = sorted(mentions, key=lambda i: i['start'], reverse=True)

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

        return {"clusters": clusters, "modified_sents": new_dialog}
