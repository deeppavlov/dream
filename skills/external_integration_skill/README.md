# Light-weighted skill for external service integration

This skill can be used to integrate external services and skills into DeepPavlov Dream pipeline. 

## Testing the skill

You may test the skill using external_fake_server component that imitates the work of an external service.
To do so, add the following files to the distribution you want to use for testing:

__docker-compose.override.yml (add to WAIT_HOSTS)__
```
external-integration-skill:8168, external-fake-server:8169
```

__docker-compose.override.yml__
```
  external-integration-skill:
    env_file: [ .env ]
    build:
      args:
        SERVICE_PORT: 8168
        SERVICE_NAME: external_integration_skill
        EXTERNAL_SKILL_URL: http://external-fake-server:8169/return_response
        ARGUMENT_TO_SEND: payload
        RESPONSE_KEY: response
      context: .
      dockerfile: ./skills/external_integration_skill/Dockerfile
    command: gunicorn --workers=1 server:app -b 0.0.0.0:8168 --reload
    deploy:
      resources:
        limits:
          memory: 128M
        reservations:
          memory: 128M

  external-fake-server:
    env_file: [ .env ]
    build:
      args:
        SERVICE_PORT: 8169
        SERVICE_NAME: external_fake_server
      context: .
      dockerfile: ./services/external_fake_server/Dockerfile
    command: flask run -h 0.0.0.0 -p 8169
    environment:
      - FLASK_APP=server
    deploy:
      resources:
        limits:
          memory: 100M
        reservations:
          memory: 100M
```

__dev.yml__
```
  external-integration-skill:
    volumes:
      - "./skills/external_integration_skill:/src"
      - "./common:/src/common"
    ports:
      - 8168:8168

  external-fake-server:
    volumes:
      - "./services/external_fake_server:/src"
      - "./common:/src/common"
    ports:
      - 8169:8169
```

__pipeline_conf.json (add to skills)__ 
```
"external_integration_skill": {
    "connector": {
        "protocol": "http",
        "timeout": 2,
        "url": "http://external-integration-skill:8168/respond"
    },
    "dialog_formatter": "state_formatters.dp_formatters:full_dialog",
    "response_formatter": "state_formatters.dp_formatters:skill_with_attributes_formatter_service",
    "previous_services": [
        "skill_selectors"
    ],
    "state_manager_method": "add_hypothesis",
    "is_enabled": true,
    "source": {
        "component": "components/knoIA98f3bijjao9d9pqkne.yml",
        "service": "skills/external_integration_skill/service_configs/external-integration-skill"
    }
}
```

## Integrating real external services

Do the same, but leave out external-fake-server component. Also, pay attention to ```EXTERNAL_SKILL_URL```, ```ARGUMENT_TO_SEND```, ```RESPONSE_KEY```. ```EXTERNAL_SKILL_URL``` is the link to the external service. ```ARGUMENT_TO_SEND``` and ```RESPONSE_KEY``` both depend on the input and output format of the external service. ```ARGUMENT_TO_SEND``` is the key of the input json in which the external skill is expecting to receive the text of the message to reply to ("payload" by default); ```RESPONSE_KEY``` is the key in which the output json of the external skills contains the text of the reply we want to get ("response" by default).