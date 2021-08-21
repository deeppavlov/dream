import requests


def to_dialogs(sentences):
    utters = [{"text": sent, "user": {"user_type": "human"}} for sent in ["hi"] + sentences]
    return {"dialogs": [{"utterances": utters, "bot_utterances": utters, "human_utterances": utters}]}


def main_test():
    url = 'http://0.0.0.0:8022/api/rest/v1.0/ask'
    sentences = ['fuck you', 'you suck', 'I hate you']
    for sent in sentences:
        data = to_dialogs([sent])
        response = requests.post(url, json=data).json()[0][0]
        allowed_phrases = ["Could you be more kind to me and talk about something else?",
                           "Could you talk about something else to avoid hurting me?",
                           "Could we talk about something else?",
                           "Could you talk or ask me about something else to avoid hurting me? Please!",
                           "My creators prohibit me to talk about this. I feel frustration, because "
                           "I'd like to tell you a lot, but I can not...",
                           "You know, this is very thin ice we're walking over. Let's try to become a "
                           "better version of ourselves!",
                           "Oops, I hear it again! Your words hurt me. Please, be more polite!"]
        assert any([allowed_phrase in response for allowed_phrase in allowed_phrases]), print(sent, '.', response)
    print("Success")


if __name__ == '__main__':
    main_test()
