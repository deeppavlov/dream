# DialogFlow Framework Template
Changes can only be made in the `dialogflows` directory.

Template has dialog flows based on programy (`repeating`) and based on valila python (`greeting`).

```bash
python utils/create_local_yml.py -s dff-template-skill -s convers-evaluation-selector 

docker-compose -f docker-compose.yml -f local.yml up -d --build

docker-compose -f docker-compose.yml -f local.yml exec agent python -m deeppavlov_agent.run
docker-compose -f docker-compose.yml -f local.yml logs -f dff-template-skill
docker-compose -f docker-compose.yml -f local.yml exec dff-template-skill bash test.sh
```


# Important changes in files of the agent
docker-compose.yml
```yml
  dff-template-skill:
    build:
      args:
        SERVICE_PORT: 8095
        SERVICE_NAME: dff_template_skill # has to be the same with skill dir name
      context: .
      dockerfile: ./skills/dff_template_skill/Dockerfile
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
  dff-template-skill:
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
    # import common.test_utils as t_utils; t_utils.save_to_test(request.json,"tests/TEST_NAME_in.json",indent=4)
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


## Links between dff skills
1. Making a link (example of link from dff\_animals\_skill to dff\_wiki_skill)
```python
    import common.dialogflow_framework.utils.state as state_utils
    ... # some code
    def why_do_you_like_response(vars):
        ... # some code
        if found_animal:
            response = f"Cool! Why do you like {found_animal}?"
        else:
            response = f"Cool! Why do you like them?"
            
        if found_entity_id:
            # making cross link
            state_utils.set_cross_link(vars, to_service_name="dff_wiki_skill", from_service_name="dff_animals_skill")
            add_info = {"entity_id": found_entity_id, "entity_substr": found_animal, "entity_types": found_types,
                        "entity_page": found_entity_page} # if we want to pass some info between skills
            # save info in cross state
            state_utils.save_cross_state(vars, service_name="dff_wiki_skill", new_state=add_info)
            state_utils.set_dff_suspension(vars) # stop current dff skill so that after the next dff skill will finish
                                                 # its scenario, the current scenario was resumed from this state
        
        return response
```

2. Using the link in the destination skill (dff\_wiki_skill in our example)
```python
    import common.dialogflow_framework.utils.state as state_utils
    ... # some code
    def tell_fact_request(ngrams, vars):
        cross_link = state_utils.get_cross_link(vars, service_name="dff_wiki_skill")
        # cross link is a dict {"from_service": "dff_animals_skill"}
        cross_state = state_utils.get_cross_state(vars, service_name="dff_wiki_skill")
        # cross_state is a dict add_info which was saved in why_do_you_like_response using save_cross_state function
        from_skill = cross_link.get("from_service", "")
        if from_skill == "dff_animals_skill":
            flag = True

```

3. To switch the destination skill if the link was made, we can add a function in common folder
   (in our example in common/wiki_skill.py)
```python
    def find_wiki_cross_links(dialog):
        flag = False
        human_attributes = dialog.get("human", {}).get("attributes", {})
        dff_shared_state = human_attributes.get("dff_shared_state", {"cross_states": {}, "cross_links": {}})
        cross_links = dff_shared_state["cross_links"].get("dff_wiki_skill", {})
        if cross_links:
            flag = True
        return flag 
```
Then in skill\_selectors/rule\_based_selector/connector.py:
```python
    from common.wiki_skill import find_wiki_cross_links
    ... # some code
        if find_wiki_cross_links(dialog):
            skills_for_uttr.append("dff_wiki_skill")
```

4. Reverse transition (from dff\_wiki\_skill to dff\_animals_skill in our example) is made the way.

## Insert scenario parser to a dff skill

```python
    ... # some imports
    import json
    from common.insert_scenario import start_or_continue_scenario, smalltalk_response, start_or_continue_facts, \
        facts_response # imports for scenario insertion
    
    # place your config in the directory skills/your_dff_skill_name/{inserted_scenario_config_name}.json
    # and load config
    with open(inserted_scenario_config_name, 'r') as fl:
        topic_config = json.load(fl)

    class State(Enum):
        USR_START = auto()
        #
        ... # States of your skill
        
        # States for scenario insertion
        SYS_INSERT_SMALLTALK = auto()
        USR_INSERT_SMALLTALK = auto()
        #
        SYS_INSERT_FACT = auto()
        USR_INSERT_FACT = auto()

        ... # Some other states of your skill

        # Two request and two response functions for scenario insertion

        def insert_scenario_smalltalk_request(ngrams, vars):
            flag = start_or_continue_scenario(vars, topic_config)
            logger.info(f"special_topic_request={flag}")
            return flag
        
        
        def insert_scenario_smalltalk_response(vars):
            response = smalltalk_response(vars, topic_config)
            return response
        
        
        def insert_scenario_facts_request(ngrams, vars):
            flag = start_or_continue_facts(vars, topic_config)
            logger.info(f"special_topic_facts_request={flag}")
            return flag
        
        
        def insert_scenario_facts_response(vars):
            response = facts_response(vars, topic_config)
            return response

        simplified_dialog_flow = dialogflow_extension.DFEasyFilling(State.USR_START)
    
        ... # Your state transitions

        # State transitions for scenario insertion

        simplified_dialog_flow.add_user_serial_transitions(
            State.SOME_STATE,
            {
                ... # transitions to other states
                State.SYS_INSERT_SMALLTALK: insert_scenario_smalltalk_request,
            },
        )

        simplified_dialog_flow.add_user_serial_transitions(
            State.USR_INSERT_SMALLTALK,
            {
                State.SYS_INSERT_FACT: insert_scenario_facts_request,
                State.SYS_INSERT_SMALLTALK: insert_scenario_smalltalk_request,
                State.SOME_OTHER_YOUR_STATE: some_other_state_request,
            },
        )
        
        simplified_dialog_flow.add_user_serial_transitions(
            State.USR_INSERT_FACT,
            {
                State.SYS_INSERT_SMALLTALK: insert_scenario_smalltalk_request,
                State.SYS_INSERT_FACT: insert_scenario_facts_request,
                State.SOME_OTHER_YOUR_STATE: some_other_state_request,
            },
        )
        
        simplified_dialog_flow.add_system_transition(State.SYS_INSERT_SMALLTALK, State.USR_INSERT_SMALLTALK,
                                             insert_scenario_smalltalk_response, )
        simplified_dialog_flow.add_system_transition(State.SYS_INSERT_FACT, State.USR_INSERT_FACT,
                                             insert_scenario_facts_response, )

        simplified_dialog_flow.set_error_successor(State.SYS_INSERT_SMALLTALK, State.SYS_ERR)
        simplified_dialog_flow.set_error_successor(State.USR_INSERT_SMALLTALK, State.SYS_ERR)
        simplified_dialog_flow.set_error_successor(State.SYS_INSERT_FACT, State.SYS_ERR)
        simplified_dialog_flow.set_error_successor(State.USR_INSERT_FACT, State.SYS_ERR)
```