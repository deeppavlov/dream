FROM python:3.9.1
# ###################### IMMUTABLE SECTION ######################################
# Do not change anything in this section 
WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG FLASK_APP
ENV FLASK_APP ${FLASK_APP}

COPY common/dff/requirements.txt .
RUN pip install -r requirements.txt

COPY skills/${SERVICE_NAME}/requirements.txt .
RUN pip install -r requirements.txt

COPY skills/${SERVICE_NAME}/ ./
COPY ./common/ ./common/

RUN pwd
RUN ls -la
RUN ls -la /src
RUN echo 'port:'
RUN echo $SERVICE_PORT
# RUN flask --app server run -h 0.0.0.0 -p ${SERVICE_PORT}

#CMD tail -f /dev/null
CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}