### DialogFlow Framework Template
Changes can only be made in the `dialogflows` directory.

Template has dialog flows based on programy (`repeating`) and based on valila python (`greeting`).




### Importan changes in files of the bot
docker-compose.yml
```yml
  dff-template:
    build:
      args:
        SERVICE_PORT: 8095
        SERVICE_NAME: dff_template
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
    environment:
      SERVICE_PORT: 8095
      SERVICE_NAME: dff_template
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
skill_selectors/rule_based_selector/connector.py
https://github.com/dilyararimovna/dp-dream-alexa/blob/a4fdea01a1f16c2a877f9d9447350463adc96a2f/skill_selectors/rule_based_selector/connector.py#L381

```python
        response=["dff_template"],
```