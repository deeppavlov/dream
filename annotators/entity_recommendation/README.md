# Entity Recommendation

Arguments: "entities" - batch of lists of results of entity linking contaning "entity_ids" and "confidences". Sample of request and response could be found in test_request.json and test_response.json files.

```python
requests.post(
    "http://0.0.0.0:8095/model",
    json = {
        "entities": [ # array info about multiple dialogs
            [ # array info about many messages for 1 dialog
                [ # info about entities in single message
                    { # single entiy
                        "entity_ids": [
                            "Q985254",
                            "Q7979323",
                            "Q7948813",
                            "Q7979325",
                            "Q1247051"
                        ],
                        "confidences": [
                            18.0,
                            13.0,
                            8.0,
                            9.0,
                            22.0
                        ]
                    }
                ]
            ]
        ]
    }
)
```

Output: 
```json
{
    "entity_recommendation": [
        {
            "entities": [
                "Q1247051",
                "Q219315",
                "Q29250",
                "Q485610",
                "Q717951"
            ],
            "confs": [
                1.4059810638427734,
                1.3141860961914062,
                1.2555015087127686,
                1.2477972507476807,
                1.2446001768112183
            ]
        }
    ]
}
```

Original repo: https://github.com/Panesher/dream-entity-recommendation
