# Entity Linking

Arguments: "entity_substr" - batch of lists of entity substrings for which we want to find ids in Wikidata, "template" - template of the sentence (if the sentence with the entity matches of one of templates), "context" - text with the entity.

```python
requests.post("http://0.0.0.0:8079/model", json = {"entity_substr": [["Forrest Gump"]], "entity_tags": [[[("film", 0.9)]]],, "context": ["Who directed Forrest Gump?"]}).json()
```

Output: [[[['Q134773', 'Q3077690', 'Q552213', 'Q5365088', 'Q17006552']], [[0.02, 0.02, 0.02, 0.02, 0.02]]]]
