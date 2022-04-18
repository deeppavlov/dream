## Dumper

Loads dialogs from the agent database to the csv-file every 12 hours.
You can change schedule by modifying `run-app` file.

### Run

```commandline
AGENT_URL=<agent_url> DUMP_PATH=<dump_path> docker-compose up --build
```
where `AGENT_URL` - location of the agent to dump and `DUMP_PATH` - host machine volume name where dump will be located.

### Load data

```python
import pandas as pd

df = pd.read_csv('/path/to/dump/file')
```
