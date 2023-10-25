# Load Test

We are proposing to utilize Locust for loading tests.

To run tests:

1. Build and raise your assistant. Make sure `agent` container is ready. 
2. On the same machine, run:
```bash
cd tests
./load_test.sh
```
Now on port `9000` interface of Locust is raised. Make sure, the port `9000` is open for outside access.
4. If your assistant is raised on a port `4242`, in separate tab in browser go to `http://0.0.0.0:4242/debug/current_load`.
5. In your browser got to `http://0.0.0.0:9000` (or replace `0.0.0.0` with the IP where locust is raised).
6. Now in Locust tab in browser, provide `Number of users` and `Spawn rate`. 
The `Host` is the address of your agent (e.g., `http://0.0.0.0:4242`). Press `Start Swarming`.
7. Now in Current Load tab in browser, you may find the loading of your containers.
8. Monitor also the Locust tab in the terminal. 
If there are prints `Fallback responses`, there are problems in the assistant 
(as assistant is error-tolerant, so something went wrong inside; in most cases, the assistant will return fallbacks). 
For Locust, fallbacks are not errors. But for us, they are.