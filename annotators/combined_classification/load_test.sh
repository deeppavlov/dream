pip install -r requirements_load_test.txt
locust -f load_test.py --headless -u 10 -r 2 --host http://0.0.0.0:$SERVICE_PORT/model