import requests


def main():
    url = "http://0.0.0.0:8137/batch_model"
    input_data = {"sentences": ["Do you like ice cream?", "It's going to be sunny today",
                                 "I love dogs", "Do you want to know some interesting fact?", 
                                 "Wolves have small teeth"], 
                  "last_bot_utterances": ["I hate dogs", "Wolves have big teeth", "The moon is a satellite of the earth"]}
    result = requests.post(url, json=input_data)
    desired_output = [{'decision': 'neutral',
                       'entailment': 0.001990885240957141,
                       'neutral': 0.7070657014846802,
                       'contradiction': 0.2909433841705322},
                      {'decision': 'neutral',
                       'entailment': 0.18027520179748535,
                       'neutral': 0.4318046271800995,
                       'contradiction': 0.38792020082473755},
                      {'decision': 'contradiction',
                       'entailment': 2.6359959974797675e-06,
                       'neutral': 0.0002536950050853193,
                       'contradiction': 0.999743640422821},
                      {'decision': 'neutral',
                       'entailment': 0.014720427803695202,
                       'neutral': 0.9783505797386169,
                       'contradiction': 0.0069289617240428925},
                      {'decision': 'contradiction',
                       'entailment': 0.0019739861600100994,
                       'neutral': 0.029022568836808205,
                       'contradiction': 0.9690034985542297}]

    assert result.json() == [{"batch": desired_output}]
    print("Successfully predicted contradiction!")


if __name__ == "__main__":
    main()
