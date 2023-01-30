# Wikidata Parser

Arguments of the annotator: "parser_info": (what we want to extract from Wikidata) and "query".

Examples of queries:

To extract triplets for entities, the "query" argument should be the list of entities ids and "parser_info" - list of "find\_triplets" strings.

```python
requests.post(wiki_parser_url, json = {"parser_info": ["find_triplets"], "query": ["Q159"]}).json()
```

To find relation between two entities:

```python
requests.post("http://0.0.0.0:8077/model", json={"parser_info": ["find_entities_rels"], "query": [["Q649", "Q159"]]}).json()
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

Example of wiki parser annotations:

{'entities_info': {'Forrest Gump': {'genre': [['Q130232', 'drama'], ['Q157443', 'comedy film'], ['Q192881', 'tragicomedy'], ['Q21401869', 'flashback film'], ['Q2975633', 'coming-of-age story']], 'has quality': [['Q45172088', 'fails the Bechdel Test'], ['Q58483045', 'passes the reverse Bechdel Test'], ['Q93639564', 'passes the Mako Mori Test'], ['Q93985027', 'fails the Vito Russo Test']], 'instance of': [['Q11424', 'film']], 'publication date': [['"+1994-06-23^^T"', '23 June 1994'], ['"+1994-07-06^^T"', '06 July 1994'], ['"+1994-10-05^^T"', '05 October 1994'], ['"+1994-10-13^^T"', '13 October 1994'], ['"+1994-10-14^^T"', '14 October 1994']]}, 'entity_substr': 'Forrest Gump'}, 'topic_skill_entities_info': {}}

# Parsing new Wikidata dump:

First, you should download a new Wikidata dump from https://dumps.wikimedia.org/wikidatawiki/entities/ in the format json.bz2.

Parsing json.bz2 dump to extract triplets:

```bash
python3 wiki_process.py -f <dump_fname> -d <directory_to_save_extracted_triplets>
```

Convert to .nt format:

```bash
python3 make_nt_files.py -d <directory_to_save_extracted_triplets> -nt <directory_for_nt_files>
```

Merge several .nt files into one file:

```bash
python3 merge_wikidata_nt.py -nt <directory_for_nt_files>
```

Then you should install the library https://github.com/rdfhdt/hdt-cpp. In the directory libhdt/tools you can find the tool rdf2hdt for converting .nt files to .hdt format (.hdt format is used in Wiki Parser).

Make final Wikidata hdt file:

```bash
./rdf2hdt <directory_for_nt_files>/wikidata.nt <directory_for_nt_files>/wikidata.hdt
```
