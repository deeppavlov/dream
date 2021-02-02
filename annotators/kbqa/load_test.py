from locust import HttpUser, task


class QuickstartUser(HttpUser):
    @task
    def hello_world(self):
        ans = self.client.post("", json={"x_init": ["Who is Donald Trump?"], "entities": [["Donald Trump"]]})
        if ans.status_code != 200:
            print(ans.status_code, ans.text)

    def on_start(self):
        pass
