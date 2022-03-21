import os
import requests


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    input_data = {"sentences": ["джейсон стетхэм хочет есть."]}
    gold = [
        [
            {
                "dep_": "nsubj",
                "ent_iob_": "B",
                "ent_type_": "PER",
                "lemma_": "джейсон",
                "morph": "Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing",
                "pos_": "PROPN",
                "text": "джейсон",
            },
            {
                "dep_": "appos",
                "ent_iob_": "I",
                "ent_type_": "PER",
                "lemma_": "стетхэм",
                "morph": "Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing",
                "pos_": "PROPN",
                "text": "стетхэм",
            },
            {
                "dep_": "ROOT",
                "ent_iob_": "O",
                "ent_type_": "",
                "lemma_": "хотеть",
                "morph": "Aspect=Imp|Mood=Ind|Number=Sing|Person=Third|Tense=Pres|VerbForm=Fin|Voice=Act",
                "pos_": "VERB",
                "text": "хочет",
            },
            {
                "dep_": "xcomp",
                "ent_iob_": "O",
                "ent_type_": "",
                "lemma_": "есть",
                "morph": "Aspect=Imp|VerbForm=Inf|Voice=Act",
                "pos_": "VERB",
                "text": "есть",
            },
            {
                "dep_": "punct",
                "ent_iob_": "O",
                "ent_type_": "",
                "lemma_": ".",
                "morph": "",
                "pos_": "PUNCT",
                "text": ".",
            },
        ]
    ]

    result = requests.post(url, json=input_data).json()
    assert result == gold, print(result)
    print("Success!")


if __name__ == "__main__":
    main()
