#!/bin/bash

roscore &

gunicorn --workers=1 server:app &

wait -n

exit $?