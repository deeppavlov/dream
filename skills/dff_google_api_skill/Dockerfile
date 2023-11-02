FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

# ###################### CUSTOM SECTION ######################################
# Here you can make changes 

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}
ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

COPY skills/dff_google_api_skill/requirements.txt .
RUN pip install -r requirements.txt

COPY skills/dff_google_api_skill/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout 240
