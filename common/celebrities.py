from common.universal_templates import if_chat_about_particular_topic


def skill_trigger_phrases():
    return ['What is your favourite celebrity?']


def talk_about_celebrity(human_utterance, bot_utterance):
    user_lets_chat_about = if_chat_about_particular_topic(human_utterance, bot_utterance,
                                                          key_words=['celebrit', 'actor'])
    flag = bool(user_lets_chat_about)
    return flag


def enable_celebrity(human_utterance, bot_utterance):
    talk_about = talk_about_celebrity(human_utterance, bot_utterance)
    bot_talk_about = 'celebrit' in bot_utterance.get('text', '')
    bot_talk_about = bot_talk_about or bot_utterance.get('active_skill', '') == 'dff_celebrity_skill'
    return talk_about or bot_talk_about
