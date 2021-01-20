gunicorn  --workers=1 --timeout 500 --graceful-timeout 500 server:app -b 0.0.0.0:8080 &
MODEL_PID=$!
gunicorn  --workers=1 --timeout 500 --graceful-timeout 500 server_proxy:app -b 0.0.0.0:8078 &
PROXY_PID=$!
while kill -0 $MODEL_PID && kill -0 $PROXY_PID ; do sleep 0.5; done
echo $MODEL_PID is model
echo $PROXY_PID is proxy
exit 1
