from common.universal_templates import if_chat_about_particular_topic


def skill_trigger_phrases():
    return ['What is your favourite celebrity?']


def talk_about_celebrity(human_utterance, bot_utterance):
    user_lets_chat_about = if_chat_about_particular_topic(human_utterance, bot_utterance,
                                                          key_words=['celebrit', 'actor'])
    flag = bool(user_lets_chat_about)
    return flag
