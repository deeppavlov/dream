import uuid

from locust import HttpUser, task

phrases = [
    "hi there",
    "what can you do?",
    "help me to write an email",
    "i am writing an article about penguins",
    "do you love dogs?",
    "what is your favorite task?",
]


class QuickstartUser(HttpUser):
    @task
    def hello_world(self):
        phrase = next(self.data, None)
        if phrase is None:
            self.on_start()
            phrase = next(self.data)
        # print(f"you: {phrase}")
        ans = self.client.post("", json={"user_id": self.id, "payload": phrase})
        if ans.status_code != 200:
            print(ans.status_code, ans.text)
        elif ans.json()["active_skill"] in ["dummy_skill", "last_chance_service"]:
            print("Fallback responses")

    #        else:
    #            print(f"bot: {ans.json()['response']}")

    def on_start(self):
        print("start")
        self.id = f"test_{uuid.uuid4().hex[5:]}"
        self.data = (p for p in phrases)
