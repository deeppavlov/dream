from locust import HttpUser, task

batch = [
    {"sentences": ["i love you", "i hate you", "i dont care"]},
    {"sentences": ["почему ты так глуп"]},
    {"sentences": ["поговорим о играх"]},
    {"sentences": ["поговорим о фильмах"]},
    {"sentences": ["поменяем тему"]},
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
