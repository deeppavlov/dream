# Fact Retrieval

The service extracts facts (sentences) from Wikidata and topical chat based on the user's utterance. The facts are
ranked using the dialog history (three last utterances).

Example of query.

```python
requests.post("http://0.0.0.0:8100/model", json = {"human_sentences": ["Let's talk about Joe Biden."],
                                                   "dialog_history": ["What do you want to talk about? Let's talk about Joe Biden"],
                                                   "nounphr_list": ["Joe Biden"]}).json()
```

Output: [["Joseph Robinette Biden Jr. is an American politician who is serving as the 46th and current president of the United States.",
          "A member of the Democratic Party, he served as the 47th vice president from 2009 to 2017 under Barack Obama and represented Delaware in the United States Senate from 1973 to 2009."]]
