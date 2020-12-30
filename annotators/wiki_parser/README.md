# Wikidata Parser

Arguments of the annotator: "parser_info": (what we want to extract from Wikidata) and "query".

Examples of queries:

To extract triplets for entities, the "query" argument should be the list of entities ids and "parser_info" - list of "find\_triplets" strings.

```python
requests.post(wiki_parser_url, json = {"parser_info": ["find_triplets"], "query": ["Q159"]}).json()
```

To extract all relations of the entities, the "query" argument should be the list of entities ids and "parser_info" - list of "find\_rels" strings.

```python
requests.post(wiki_parser_url, json = {"parser_info": ["find_rels"], "query": [("Q159", "forw", "")]}).json()
```

(triplets of type (subject, relation, object))
or

```python
requests.post(wiki_parser_url, json = {"parser_info": ["find_rels"], "query": [("Q159", "backw", "")]}).json()
```

(triplets of type (object, relation, subject)).

To execute SPARQL queries, the "query" argument should be the list of tuples with the info about SPARQL queries and "parser_info" - list of "query\_execute" strings.

Let us consider an example of the question "What is the deepest lake in Russia?" with the corresponding SPARQL query
"SELECT ?ent WHERE { ?ent wdt:P31 wd:T1 . ?ent wdt:R1 ?obj . ?ent wdt:R2 wd:E1 } ORDER BY ASC(?obj) LIMIT 5"

arguments:
* what_return: ["?obj"]
* query_seq: [["?ent", "http://www.wikidata.org/prop/direct/P17", "http://www.wikidata.org/entity/Q159"]
                ["?ent", "http://www.wikidata.org/prop/direct/P31", "http://www.wikidata.org/entity/Q23397"],
                ["?ent", "http://www.wikidata.org/prop/direct/P4511", "?obj"]]
* filter_info: []
* order\_info: order\_info(variable='?obj', sorting_order='asc')

```python
requests.post("wiki_parser_url", json = {"parser_info": ["query_execute"], "query": [[["?obj"], [["http://www.wikidata.org/entity/Q159", "http://www.wikidata.org/prop/direct/P36", "?obj"]], [], [], True]]}).json()
```

To find labels for entities ids, the "query" argument should be the list of entities ids and "parser_info" - list of "find\_label" strings.

```python
requests.post(wiki_parser_url, json = {"parser_info": ["find_label"], "query": [["Q159", ""]]}).json()
```

In the example in the list ["Q159", ""] the second element which is an empty string can be the string with the sentence.
