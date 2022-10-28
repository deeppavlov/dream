import logging
import random
import re
from collections import Counter
from os import getenv
from typing import Any

import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import nltk
import requests
import sentry_sdk
from common.constants import CAN_CONTINUE_SCENARIO
from df_engine.core import Actor, Context
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
#from textblob import TextBlob

nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
INFILLING = getenv("INFILLING")
DIALOGPT_RESPOND = getenv("DIALOGPT_RESPOND_ENG_SERVICE_URL")
assert INFILLING


with open("popular_30k.txt", "r") as f:
    common_words = [x.strip() for x in f.read().split("\t")]

def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def compose_data_for_infilling(ctx, actor): # ПОКА ЧТО ТРИ ПРОШЛЫЕ РЕПЛИКИ, ДОДЕЛАТЬ
    data = []
    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)
    if len(human_uttrs) > 1:
        data += [{"speaker": human_uttrs[-2]["user"]["user_type"], "text": human_uttrs[-2]["text"]}]
    if len(bot_uttrs) > 0:
        data += [{"speaker": bot_uttrs[-1]["user"]["user_type"], "text": bot_uttrs[-1]["text"]}]
    if len(human_uttrs) > 0:
        data += [{"speaker": human_uttrs[-1]["user"]["user_type"], "text": human_uttrs[-1]["text"]}]

    return data

def generate_infilling_response(prompts=['_']):
    reply = random.choice(prompts)

    def infilling_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"dff-recommendation-skill: {reply}")
    
        request_data = compose_data_for_infilling(ctx, actor)
        previous_context = ' '.join([x['text'] for x in request_data])
        request_data = {"texts": [previous_context + ' ' + reply]}
        if len(request_data) > 0:
            response = requests.post(INFILLING, json=request_data).json()
            hypothesis = [response["infilled_text"][0].replace(previous_context, '')]
        else:
            hypothesis = []

        for hyp in hypothesis:
            # if hyp[-1] not in [".", "?", "!"]:
            #     hyp += "."
            gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
        #!!! ВАЖНО
        #ctx = int_prs.save_slots_to_ctx({"recommendation": hypothesis[0]})(ctx, actor) #как сделать чтоб это работало? Диля

        if len(curr_responses) == 0:
            return ""

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)
    return infilling_response



def compose_data_for_dialogpt(recommend, discussed_entity, ctx, actor, hyponym='', question=False):
    data = []
    # for uttr in dialog["utterances"][-3:]:
    #     curr_uttr = {"speaker": uttr["user"]["user_type"], "text": uttr["text"]}
    #     data.append(curr_uttr)

    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)
    if len(human_uttrs) > 1:
        data.append(human_uttrs[-2]["text"])
    if len(bot_uttrs) > 0 and bot_uttrs[-1] != bot_uttrs[0]:
        data.append(bot_uttrs[-1]["text"])
    if len(human_uttrs) > 0:
        text_to_append = human_uttrs[-1]["text"]
        if discussed_entity:
            if question: #возможно надо убрать
                text_to_append +=  ' ' + 'What do you think about'
            if ctx.misc.get("slots", {}).get(discussed_entity):
                text_to_append +=  ' ' + ctx.misc["slots"][discussed_entity] + '.'
            if ctx.misc.get("slots", {}).get("details"):
                text_to_append +=  ' ' + ctx.misc["slots"]["details"]
            if hyponym:
                text_to_append = 'Tell me about ' + hyponym + 's'
                ctx.misc["curr_hyponym"] = hyponym + 's' #ПОСМОТРЕТЬ КАК И ЧТО СОХРАНЯЕТСЯ, ПОДУМАТЬ ПРО НОДУ ГДЕ ИСПОЛЬЗОВАТЬ (далеко не везде). Продумать случаи когда гипонима нет и все может падать.
        if recommend:
            text_to_append += ' recommendation please'
            if ctx.misc.get("slots", {}).get("details") and (ctx.misc.get("slots", {}).get("details") not in text_to_append):
                text_to_append +=  ' ' + ctx.misc["slots"]["details"]
        data.append(text_to_append)
        # if question: 
        #     data.append("Okay, I'll try to help. Ask.")

    return data

GEN_STOPWORDS = re.compile(r"thanks|message|pm|comment|sent you|link|comment|send|I'll see|username|add me|lt|thread|I'll reply|upvote", re.IGNORECASE)

def generative_response(recommend=False, question=False, discussed_entity=""):
    def generative_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> Any:

        ## вероятно надо будет вынести в отдельную функцию
        if question == True:
            common_hyponyms = []
            if ctx.misc.get("slots", {}).get('topic_entity', ''):
                entity =  str(ctx.misc["slots"]['topic_entity'])
                text_tagged = nltk.pos_tag(word_tokenize(entity))
                noun_tokens = [x[0].lower() for x in text_tagged if x[1] == 'NNP' or x[1] == 'NN' or x[1] == 'NNS']
                noun_lemmas = [lemmatizer.lemmatize(x) for x in noun_tokens]
                noun_synset = wordnet.synsets(noun_lemmas[0])[0]
                hypos = lambda s:s.hyponyms()
                all_candidates = list(noun_synset.closure(hypos))     
                candidate_hyponyms = [ss.lemma_names()[0].replace('_', ' ') for ss in all_candidates]
                common_hyponyms = list(set(common_words) & set(candidate_hyponyms))
                #common_hyponyms = candidate_hyponyms
            ### 
            if common_hyponyms:
                hyponym = common_hyponyms[random.randrange(0, len(common_hyponyms))] #заменить на рандомный выбор
            else:
                hyponym = ''
            # #hyp!!!
            if hyponym:
                # blob = TextBlob([hyponym])
                # plural_hyponym = [word.pluralize() for word in blob.words][0]
                return 'What do you think about ' + hyponym + 's?'
                # return 'What do you think about ' + plural_hyponym + 's?'

        if ctx.misc.get("num_gen_responses", 0):
            num_gen_responses = ctx.misc.get("num_gen_responses", 0)
            num_gen_responses = int(num_gen_responses) + 1
        else:
            num_gen_responses = 1
        ctx.misc["num_gen_responses"] = num_gen_responses
        #return str(ctx.misc.get("num_gen_responses", 0))
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"dff-generative-skill: {reply}")

        hyponym = ''
        request_data = compose_data_for_dialogpt(recommend, discussed_entity, ctx, actor, hyponym=hyponym, question=question)
        if len(request_data) > 0:
            result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
            hypotheses = result[0]
        else:
            hypotheses = []
        if hypotheses:
            for hyp in hypotheses[0]:
                if hyp and not re.search(STOP_WORDS, hyp):
                    if hyp[-1] not in [".", "?", "!"]:
                        hyp += "."
                    gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
        if len(curr_responses) == 0:
            return ""

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)
    return generative_response_handler


def name_response(): # мб доделать позже

    def name_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        human_uttrs = int_ctx.get_human_utterances(ctx, actor)
        if len(human_uttrs) > 0:
            person = ''
            for key, value in human_uttrs[-1]["annotations"]['wiki_parser'].items():
                if value:
                    entity = random.choice(list(value.items()))
                    if entity[1].get('instance of', {})[0][0] == 'Q5':
                        return str(value)
                        occupation, place, genre = '', '', ''
                        if entity[1].get('genre', {}):
                            genre = entity[1].get('genre')[0][1] + ' '
                        if entity[1].get('occupation', {}):
                            occupation = ', the ' + genre + entity[1].get('occupation')[0][1]
                        if entity[1].get('country of sitizenship', {}):
                            place = ' from ' + entity[1].get('country of sitizenship')[0][1]
                        return 'Wow, just like ' + str(entity[0]) + occupation + place
        return "That's a beautiful name! Nice to meet you."
    return name_response_handler


def generate_np_response(response_options=[''], recommend=False, discussed_entity=""):
    
    reply = random.choice(response_options)

    def np_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

        def gathering_responses(reply, confidence, human_attr, bot_attr, attr):
            nonlocal curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs
            if reply and confidence:
                curr_responses += [reply]
                curr_confidences += [confidence]
                curr_human_attrs += [human_attr]
                curr_bot_attrs += [bot_attr]
                curr_attrs += [attr]
                logger.info(f"dff-recommendation-skill: {reply}")

        noun_phrases = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
        if noun_phrases:
            noun_phrases = noun_phrases[0]
            request_data = compose_data_for_dialogpt(recommend, discussed_entity, ctx, actor)
            if len(request_data) > 0:
                result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
                hypotheses = result[0]
            else:
                hypotheses = []
            
            if hypotheses:
                for hyp in hypotheses[0]:
                    if hyp[-1] not in [".", "?", "!"]:
                        hyp += "."
                    gathering_responses(hyp, 0.99, {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
            if len(curr_responses) == 0:
                return ""

            return int_rsp.multi_response(
                replies=curr_responses,
                confidences=curr_confidences,
                human_attr=curr_human_attrs,
                bot_attr=curr_bot_attrs,
                hype_attr=curr_attrs,
            )(ctx, actor, *args, **kwargs)
        else:
            return reply
    return np_response


ASK_ABOUT_PRESEQ_DICT = { #сделать еще одну штуку для поспрашивать насчет топика который идет сейчас!!!
    "cinema": {
        "left_context": ["I love movies and TV series. What about you?"],
        "prequestion": "Do you like watching movies?", 
        "prequestion_1": "So, do you like movies in general?", 
        "question": "Which movie is your favourite?"
        },
    "food": {
        "left_context": ["I love eating. What about you? "],
        "prequestion": "I don't know if I can call myself a foodie... And are you?", 
        "prequestion_1": "Well, do you enjoy cooking or going to restaurants?", 
        "question": "What is your favourite dish then?"
        },
    "videogames": {
        "left_context": ["Playing your favourite computer game is the end to a long tiring day. I love games. ", "Oh"],
        "prequestion": "Do you like playing computer games?", 
        "prequestion_1": "And what do you think about computer games?", 
        "question": "Which one are you playing now?"
        },
    } 
# а в каком случае его включать? посмотреть на другие сценарии! нужна ли штука которая поспрашивает вопросы для текущего топика: возможно впишется в чат эбаут
# есть возможность взять вопросы которые и так есть в дримботе link-to (ПОСМОТРЕТЬ!!!). вопросы лежат каждый в отдельном файлике, Диля кинет ссылку (вопросы на разные темы)
# оч поход на чатэбаут но с нашей инициативой (initiate topic!!!), то есть по сути это штука поговорить про топик который я преддложила

def ask_about_presequence(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if ctx.validation:
        return ""
    used_questions = ctx.misc.get("used_questions", [])
    ctx.misc["next_question"] = []
    ASK_ABOUT_PRESEQ = dict(ASK_ABOUT_PRESEQ_DICT)
    for topic, questions in ASK_ABOUT_PRESEQ.items():
        if topic not in used_questions:
            question_topic = topic
            question_seq = questions
            break
    used_questions.append(topic)
    ctx.misc["used_questions"] = used_questions
    ctx.misc["next_question"] = question_seq["question"]
    ctx.misc["next_prequestion"] = question_seq["prequestion_1"]
    request_data = question_seq["left_context"]
    if len(request_data) > 0:
        result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
        hypotheses = result[0]
    else:
        hypotheses = []
    
    if hypotheses:
        for hyp in hypotheses[0]:
            if re.search(STOP_WORDS, hyp):
                continue
            if hyp[-1] not in [".", "?", "!"]:
                hyp += "."
            return hyp + ' ' + str(question_seq["prequestion"]) 
    else:
        return ''


def ask_about_presequence_2(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if ctx.validation:
        return ""
    request_data = compose_data_for_dialogpt(False, "", ctx, actor)
    if len(request_data) > 0:
        result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
        hypotheses = result[0]
    else:
        hypotheses = []
    presequence = ctx.misc.get("next_prequestion", [])
    if hypotheses:
        for hyp in hypotheses[0]:
            if re.search(STOP_WORDS, hyp):
                continue
            if hyp[-1] not in [".", "?", "!"]: #переделать в отдельную функцию фильтрации реддита
                hyp += "."
            return hyp + ' ' + str(presequence)
    else:
        return ''

STOP_WORDS = re.compile(r"reddit|\bop\b|upvote|thanks|\?|this movie|guy|username|add me|\blt\b|thread|I'll reply|downvote|comment", re.IGNORECASE)

#сделать границы слова
#комет -- генеративная моделька генерирующая по атрибутам. Модель генерирует для новых сущностей, которых нет в графе
#https://github.com/deeppavlov/dream/blob/main/annotators/COMeT/tests/atomic_out.json
#посмотреть метаскрипт!!!
#подключить даммискилл


HYPONYM_QUESTIONS = ["What do you think about _?", "Why don't we discuss _?", "Let's talk about _.", 
'By the way, I really like _. What about you?',
"I've been thinking about _ recently..."]

def get_hyponyms(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    common_hyponyms = []
    available_hyponyms = ctx.misc.get("slots", {}).get('available_hyponyms', {})
    if ctx.misc.get("slots", {}).get('topic_entity', ''):
        entity =  str(ctx.misc["slots"]['topic_entity'])
        if entity in available_hyponyms.keys():
            common_hyponyms = available_hyponyms[entity]
        else:
            text_tagged = nltk.pos_tag(word_tokenize(entity))
            noun_tokens = [x[0].lower() for x in text_tagged if x[1] == 'NNP' or x[1] == 'NN' or x[1] == 'NNS']
            noun_lemmas = [lemmatizer.lemmatize(x) for x in noun_tokens]
            if noun_lemmas:
                synsets =  wordnet.synsets(noun_lemmas[0], pos='n')
                if synsets:
                    noun_synset = synsets[0]
                    if noun_lemmas[0]=='food' or noun_lemmas[0]=='dish':
                        noun_synset = wordnet.synsets(noun_lemmas[0], pos='n')[1]
                    hypos = lambda s:s.hyponyms()
                    all_candidates = list(noun_synset.closure(hypos))     
                    candidate_hyponyms = [ss.lemma_names()[0].replace('_', ' ') for ss in all_candidates]
                    common_hyponyms = list(set(common_words) & set(candidate_hyponyms))
        #common_hyponyms = candidate_hyponyms
    ### 
    if common_hyponyms:
        hyponym = common_hyponyms[random.randrange(0, len(common_hyponyms))] #заменить на рандомный выбор
        available_hyponyms[entity] = common_hyponyms.remove(hyponym)
        ctx.misc['available_hyponyms'] = available_hyponyms
    else:
        hyponym = ''
    # #hyp!!!
    if hyponym:
        # blob = TextBlob([hyponym])
        # plural_hyponym = [word.pluralize() for word in blob.words][0]
        hyponym = hyponym + 's'
        return HYPONYM_QUESTIONS[random.randrange(0, len(HYPONYM_QUESTIONS))].replace('_', hyponym)


def generate_with_string(to_append='get_questions', position_string='before'):
    def generate_with_string_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        if ctx.validation:
            return ""
        request_data = compose_data_for_dialogpt(False, "", ctx, actor)
        if len(request_data) > 0:
            result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
            hypotheses = result[0]
        else:
            hypotheses = []
        if to_append == 'get_questions':
            string_to_attach = ctx.misc.get("next_question", [])
        elif to_append == 'get_hyponyms':
            string_to_attach = get_hyponyms(ctx, actor)
        else:
            string_to_attach = to_append
        if hypotheses:
            for hyp in hypotheses[0]:
                if re.search(STOP_WORDS, hyp):
                    continue
                if hyp[-1] not in [".", "?", "!"]: #переделать в отдельную функцию фильтрации реддита
                        hyp += "."
                if string_to_attach:
                    if position_string == 'before':
                        return hyp + ' ' + str(string_to_attach)
                    elif position_string == 'after':
                        return str(string_to_attach) + ' ' + hyp
                else:
                    return hyp 
        else:
            return ''
    return generate_with_string_handler
