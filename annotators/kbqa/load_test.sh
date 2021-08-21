pip install -r requirements_load_test.txt
locust -f load_test.py --headless -u 1 -r 1 --host http://0.0.0.0:8080/model