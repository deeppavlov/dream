# Fact Retrieval

## Description

The service extracts facts (sentences) from Wikidata and WikiHow and topical chat based on the user's utterance. The facts are ranked using the dialog history (three last utterances). Works for the texts in Russian.


## I/O

**Inpunt**
(an example of query)

```python
requests.post("http://0.0.0.0:8100/model", json = {
            "dialog_history": [["Какая столица России?"]],
            "entity_substr": [["россии"]],
            "entity_tags": [["loc"]],
            "entity_pages": [[["Россия"]]],
        }).json()
```

**Output:** [[
        "Росси́я или Росси́йская Федера́ция (РФ), — государство в Восточной Европе и Северной Азии. Столица — Москва. Государственный язык — русский. Денежная единица — "российский рубль."]]

## Dependencies

