# COMeT

## Description

COMeT is a Commonsense Transformers for Automatic Knowledge Graph Construction service based
on [comet-commonsense](https://github.com/atcbosselut/comet-commonsense) framework written in Python 3.


### Quickstart from docker for COMeT with Atomic graph

```bash
python utils/create_local_yml.py -s comet-atomic
docker-compose -f docker-compose.yml -f local.yml up -d --build comet-atomic
docker-compose -f docker-compose.yml -f local.yml exec comet-atomic bash test.sh
```

### Quickstart from docker for COMeT with ConceptNet graph

```bash
python utils/create_local_yml.py -s comet-conceptnet
docker-compose -f docker-compose.yml -f local.yml up -d --build comet-conceptnet
docker-compose -f docker-compose.yml -f local.yml exec comet-conceptnet bash test.sh
```

### Average RAM for CPU and average starting time for COMeT

| For CPU inference:             | Atomic  | ConceptNet |
|--------------------------------|---------|------------|
| Average RAM usage              | 1800 MB | 1330 MB    |
| Average starting time          | 5s      | 4s         |
| Average request execution time | 4s      | 1s         |

| For GPU inference:             | Atomic  | ConceptNet |
|--------------------------------|---------|------------|
| Average GPU memory usage       | 1580 MB | 1550 MB    |
| Average RAM usage              | 4200 MB | 3800 MB    |
| Average starting time          | 4s      | 3s         |
| Average request execution time | 0.4s    | 0.2s       |

## Input/Output

**Input**
- hypotheses: possible assistant's replies
- currentUtterance: latest reply from a user
- pastResponses: a list of user's utterances

an input example ():
```
{
  "input": "PersonX went to a mall",
  "category": [
    "xReact",
    "xNeed",
    "xAttr",
    "xWant",
    "oEffect",
    "xIntent",
    "oReact"
  ]
}

```
**Output**
a list of probabilities about the utterance based on categories:
- xReact
- xNeed
- xAttr
- xWant
- oEffect
- xIntent
- oReact

an output example ():
```
  "xReact": {
    "beams": [
      "satisfied",
      "happy",
      "excited"
    ],
    "effect_type": "xReact",
    "event": "PersonX went to a mall"
  },
  "xNeed": {
    "beams": [
      "to drive to the mall",
      "to get in the car",
      "to drive to the mall"
    ],
    "effect_type": "xNeed",
    "event": "PersonX went to a mall"
  },
  "xAttr": {
    "beams": [
      "curious",
      "fashionable",
      "interested"
    ],
    "effect_type": "xAttr",
    "event": "PersonX went to a mall"
  },
  "xWant": {
    "beams": [
      "to buy something",
      "to go home",
      "to shop"
    ],
    "effect_type": "xWant",
    "event": "PersonX went to a mall"
  },
  "oEffect": {
    "beams": [
      "they go to the store",
      "they go to the mall"
    ],
    "effect_type": "oEffect",
    "event": "PersonX went to a mall"
  },
  "xIntent": {
    "beams": [
      "to buy something",
      "to shop",
      "to buy things"
    ],
    "effect_type": "xIntent",
    "event": "PersonX went to a mall"
  },
  "oReact": {
    "beams": [
      "happy",
      "interested"
    ],
    "effect_type": "oReact",
    "event": "PersonX went to a mall"
  }
}
```



## Dependencies

none