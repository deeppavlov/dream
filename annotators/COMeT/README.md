# COMeT

COMeT is a Commonsense Transformers for Automatic Knowledge Graph Construction service based
on [comet-commonsense](https://github.com/atcbosselut/comet-commonsense) framework written in Python 3.

# Quickstart from docker for COMeT with Atomic graph

```bash
python utils/create_local_yml.py -s comet-atomic
docker-compose -f docker-compose.yml -f local.yml up -d --build comet-atomic
docker-compose -f docker-compose.yml -f local.yml exec comet-atomic bash test.sh
```

# Quickstart from docker for COMeT with ConceptNet graph

```bash
python utils/create_local_yml.py -s comet-conceptnet
docker-compose -f docker-compose.yml -f local.yml up -d --build comet-conceptnet
docker-compose -f docker-compose.yml -f local.yml exec comet-conceptnet bash test.sh
```

# Average RAM for CPU and average starting time for COMeT

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