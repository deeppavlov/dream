from locust import HttpUser, task

batch = [
    {"sentences": ["i love you", "i hate you", "i dont care"]},
    {"sentences": ["you son of the bitch", "yes"]},
    {"sentences": ["why you are so dumb"]},
    {"sentences": ["let's talk about movies"]},
    {"sentences": ["let's talk about games"]},
    {"sentences": ["let's switch topic"]},
]


class QuickstartUser(HttpUser):
    @task
    def hello_world(self):
        ans = self.client.post("", json=batch[self.batch_index % len(batch)])
        self.batch_index += 1
        if ans.status_code != 200:
            print(ans.status_code, ans.text)

    def on_start(self):
        self.batch_index = 0
