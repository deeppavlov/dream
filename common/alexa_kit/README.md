### Create environment variables
```
ALEXA_SKILL_ID="amzn1.ask.skill.v3ry-l0ng-uuid-str1ng"
AGENT_URL="http://agent:4242/"
```

### Create self-signed certificate
```
cd $DREAM_ROOT/common/alexa_kit
openssl genrsa -out private-key.pem 2048
openssl req -new -x509 -days 365 \
            -key private-key.pem \
            -config configuration.cnf \
            -out certificate.pem
```

### Configure and build model
In Alexa Developer Console navigate to the Build tab, in the left menu select Interaction Model -> JSON Editor.
Copy and paste `./skills.json` contents, save and build your model.

This should complete steps 1-3 in your *skill builder checklist*.

### Configure Endpoint
Open endpoint configuration (step 4 in your *skill builder checklist*), choose HTTPS as Service Endpoint Type.

Configure your default region, providing the URL which you set in your `configuration.cnf` DNS.1 field.

Choose "I will upload as self-signed certificate in X 509 format" and upload your `certificate.pem`.
