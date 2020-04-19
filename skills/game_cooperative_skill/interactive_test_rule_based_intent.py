# %%

from skills.rule_based_intent import skill

history = [
    "are you good",
    "yes"
]
history = []

while True:
    history.append(input("test request: "))
    history.append(skill.respond(history))
    print(f"model response: {history[-1]}")

# %%
