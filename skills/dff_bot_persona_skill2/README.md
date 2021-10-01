# DialogFlow Framework Template
Changes can only be made in the `dialogflows` directory.

Template has dialog flows based on programy (`repeating`) and based on valila python (`greeting`).



# Importan changes in files of the agent
docker-compose.yml
```yml
  dff-template:
    build:
      args:
        SERVICE_PORT: 8095
        SERVICE_NAME: dff_template # has to be the same with skill dir name
      context: .
      dockerfile: ./skills/dff_template/Dockerfile
    command:  gunicorn --workers=1 server:app -b 0.0.0.0:8095 --reload
    deploy:
      mode: replicated
      replicas: 4
      resources:
        limits:
          memory: 768M
        reservations:
          memory: 768M
```


dev.yml
```yml
  dff-template:
    env_file: [.env.dev]
    volumes:
      - "./skills/dff_template:/src"
      - "./common:/src/common"
    ports:
      - 8095:8095
```

pipeline.json
```json
            "dff_template": {
                "connector": {
                    "protocol": "http",
                    "url": "http://dff-template:8095/respond"
                },
                "dialog_formatter": "state_formatters.dp_formatters:dff_template_formatter",
                "response_formatter": "state_formatters.dp_formatters:skill_with_attributes_formatter_service",
                "previous_services": ["skill_selectors"],
                "state_manager_method": "add_hypothesis"
            },
```

state_formatters/formatter.py
```python
def DFF_TEMPLATE_formatter(dialog: Dict) -> List[Dict]:
    service_name = f"DFF_TEMPLATE"
    return utils.dff_formatter(dialog, service_name)
```
[skill_selectors/rule_based_selector/connector.py](https://github.com/dilyararimovna/dp-dream-alexa/blob/a4fdea01a1f16c2a877f9d9447350463adc96a2f/skill_selectors/rule_based_selector/connector.py#L381)

```python
        response=["dff_template"],
```


# Tests
## Test creating

The file `server.py` contains this code

```python
@app.route("/respond", methods=["POST"])
def respond():
    # next commented line for test creating
    # import common.test_utils as t_utils; t_utils.save_to_test(responses,"tests/TEST_NAME_in.json",indent=4)
    responses = handler(request.json)
    # next commented line for test creating
    # import common.test_utils as t_utils; t_utils.save_to_test(responses,"tests/TEST_NAME_out.json",indent=4)
    return jsonify(responses)

```
Steps:
1. Uncomment lines with json dump 
1. Name your test by replacing `YOUR_TEST_NAME` in both line. They have to be same.
1. Start a test dialog with agent.Every turn will be written in `tests/TEST_NAME*`. `*_in.json` - for input data, `*_in.json` - for response data.

If your want to write down all turns of test dialog you can use this code

```python
index = 0
@app.route("/respond", methods=["POST"])
def respond():
    # next commented line for test creating
    import common.test_utils as t_utils;t_utils.save_to_test(responses,f"tests/TEST_NAME_{index}_in.json",indent=4)
    responses = handler(request.json)
    # next commented line for test creating
    import common.test_utils as t_utils;t_utils.save_to_test(responses,f"tests/TEST_NAME_{index}_out.json",indent=4)
    index +=1
    return jsonify(responses)

```
## Test using
Tests are used for two way:

- service initialization in `server.py`

```python
try:
    test_server.run_test(handler)
    logger.info("test query processed")
except Exception as exc:
    sentry_sdk.capture_exception(exc)
    logger.exception(exc)
    raise exc
```

- service testing by `test.sh` execution


## Test extending
If you use service based on random behavior you can send `random_seed` in your service. You can find corespond lines in `server.py`
```python
    ... # some code
    rand_seed = requested_data.get("rand_seed")  # for tests
    ... # some code
    if rand_seed:
        random.seed(int(rand_seed)
    ... # some code
```

For answer comparison we use `common.test_utils`:
- `compare_structs` - for json structure comparison
- `compare_text` - for text comparison

You can use them for you custom comparison.