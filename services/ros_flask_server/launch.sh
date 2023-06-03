#!/bin/bash

roscore &

# rosrun ros_dream listener.py &

gunicorn --workers=1 server:app &

wait -n

exit $?