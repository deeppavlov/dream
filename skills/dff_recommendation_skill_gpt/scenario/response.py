from code import interact
import logging
import random
import re
from collections import Counter
from os import getenv
from typing import Any
import sys
from typing import List

import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.dff.integration.condition as int_cnd
import common.utils as common_utils
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
NER_URL = getenv("NER_URL")
assert INFILLING


STOP_WORDS = re.compile(r'''reddit|moderator|\bop\b|play|upvote|thanks|this movie|(this|that|the) guy|username|add me|\blt\b|thread|edit|spelling|\
|downvote|comment|message|\bpm\b|sent you|link|trade|trading|\bsub\b|post|the first one|thread|\blt\b|this one|steam|have a nice day|game|guild|\
|the second one|(I will|I'll|Ill|I) (can)*(reply|send|see|give|try|steal|be stealing|be online|be back|pm)|\br\b|\badd\b|\badded\b|gold|name|\
|account|the guy|this guy|flair|banned|profile|I('ve| have)* mentioned|I'm (gonna|going to)|he('s| is) saying|\bpost\b|\bu\b|community|\bfc\b|\bign\b''', re.IGNORECASE)
SWITCH_TOPIC = ["Well... ", "But enough about that! "]
HYPONYM_TOPIC = ["What do you think about _?", "Why don't we discuss _?", "Let's talk about _.", 
'By the way, I really like _. What about you?']
ASK_ABOUT_PRESEQ_DICT = { #сделать еще одну штуку для поспрашивать насчет топика который идет сейчас!!!
    "cinema": {
        "left_context": ["I love movies and TV series. Movies are the best. What about you?"],
        "prequestion": "I've heard many people say they are addicted to Netflix. Do you like watching movies?", 
        "prequestion_1": "Oh, all right, and what about series?", 
        "question": "What have you watched recently?",
        "user_dislikes_topic": "Well yeah, not all movies deserve to be watched. Why don't we change the topic?"
        },
    "food": {
        "left_context": ["I love eating, especially sandwiches. What about you? "],
        "prequestion": "I've just read that people have burger eating competitions. I'd love to participate! I am such a foodie... And are you?", 
        "prequestion_1": "Well, do you enjoy cooking or going to restaurants?", 
        "question": "What is your favourite dish?",
        "user_dislikes_topic": "Sometimes I think that food is nothing more than fuel. I do love burgers though..."
        },
    "videogames": {
        "left_context": ["Playing your favourite computer game is the end to a long tiring day. I love games. ", "Oh"],
        "prequestion": "Somethimes I think that I wouldn't survive without my computer... Do you like playing computer games?", 
        "prequestion_1": "And what do you think about computer games?", 
        "question": "Which one are you playing now?",
        "user_dislikes_topic": "Video games can take up too much time. I'm doing my best to keep my addiction in moderation though."
        }, #написать для набора вопросов из коммон
    # "space travel": {
    #     "left_context": [""],
    #     "prequestion": "I know that people are planning to go to Mars soon. Space travel is so exciting for me! Did you dream of being an astronaut when you were a child?", 
    #     "prequestion_1": "Oh, well... Do you like reading or watching science fiction? I'm such a fan of books about faraway planets.", 
    #     "question": "Would you travel to space if you had a chance?",
    #     "user_dislikes_topic": "Space is not for everyone! You have to be really well-trained to go there. An ordinary person wouldn't survive..."
    #     }, 
    "ocean": {
        "left_context": [""],
        "prequestion": "In heaven it's all they talk about. The ocean. And the sunset. Have you ever been to the seaside?", 
        "prequestion_1": "I wish I could feel the waves touch my feet one day... But I'm just a bot.", 
        "question": "Would you prefer to live near the sea or in the mountains?",
        "user_dislikes_topic": "Well, some people like woods or mountains much more than sea. The nature is beautiful anyways."
        }, 
    # "job": {
    #     "left_context": [""],
    #     "prequestion": "They say that questions like 'What dinosaur would you like to be?' are very popular now during job interviews. It's always better to be prepared... So, what dinosaur would you choose?", 
    #     "prequestion_1": "If I was a dinosaur, I would be a T-Rex for sure. Love those tiny arms! Pterosaurs are nice too as they could fly. Good old times...", 
    #     "question": "Did you like dinosaurs when you were a kid? ",
    #     "user_dislikes_topic": "Oh... Those interview questions might be really weird. I would be confused as well. "
    #     }, 
    } 
BOT_PERSONAL_INFORMATION_PATTERNS = re.compile(r'''I have (a|the|two|many|three)|I will|I want|I had|My (sister|brother|mother|father|
friend)|I (was|went|live)|he is a troll|I don't have|I'll|I'd like|I('m|am) (not|a|from)''', re.IGNORECASE)
THIRD_PERSON = re.compile(r'''s*he (.*s|will)''', re.IGNORECASE)
APOLOGIZE_FOR_DIFFICULT_WORD = ['Oh, yeah, that might have been confusing. Here is what my magic book says:',
'Sorry, sometimes I forget that human brain is not as large as mine. I can define it as:',
'Let me look it up... The thesaurus tells me that it is']

TOXIC_BOT = re.compile(r'''hate|evil|porn|see you|bye|trade|i have to go''', re.IGNORECASE)
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.95
DEFAULT_CONFIDENCE = 0.9
BIT_LOWER_CONFIDENCE = 0.8
ZERO_CONFIDENCE = 0.0


with open("popular_30k.txt", "r") as f:
    common_words = [x.strip() for x in f.read().split("\t")]


def user_dislikes_topic(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return ctx.misc.get("user_dislikes_topic", '')


def compose_data_for_dialogpt(ctx: Context, actor: Actor, recommend: bool=False, discussed_entity: str="") -> List[str]:
    data = []
    human_uttrs = int_ctx.get_human_utterances(ctx, actor)
    bot_uttrs = int_ctx.get_bot_utterances(ctx, actor)
    if len(human_uttrs) > 1:
        data.append(human_uttrs[-2]["text"])
    if len(bot_uttrs) > 0 and bot_uttrs[-1] != bot_uttrs[0]:
        data.append(bot_uttrs[-1]["text"])
    if len(human_uttrs) > 0:
        text_to_append = human_uttrs[-1]["text"]
        if discussed_entity:
            if ctx.misc.get("slots", {}).get(discussed_entity, ''):
                entity = ctx.misc.get("slots", {}).get(discussed_entity,'')
                if not re.search(entity, human_uttrs[-1]["text"], re.IGNORECASE):
                    text_to_append +=  ' ' + entity 
            if ctx.misc.get("slots", {}).get("details"):
                text_to_append +=  ' ' + ctx.misc["slots"]["details"]
        if recommend:
            if ctx.misc.get("slots", {}).get("request") and (ctx.misc.get("slots", {}).get("request") not in text_to_append):
                text_to_append +=  ' ' + ctx.misc["slots"]["request"]
            if ctx.misc.get("slots", {}).get("details") and (ctx.misc.get("slots", {}).get("details") not in text_to_append):
                text_to_append +=  ' ' + ctx.misc["slots"]["details"]
            text_to_append += 'give me a recommendation please'
        data.append(text_to_append)
    return data


def determine_confidence(ctx: Context, actor: Actor, hypothesis: str, recommendation: bool=False) -> int:
    if not hypothesis:
        return 0
    confidence = 0.99 
    if re.search(STOP_WORDS, hypothesis): #все
        confidence -= 0.2
    if len(hypothesis.split(' ')) < 4:
        confidence -= 0.05
    if re.search(BOT_PERSONAL_INFORMATION_PATTERNS, hypothesis):
        confidence -= 0.15
    if re.search(TOXIC_BOT, hypothesis):
        confidence -= 0.25
    if re.search(THIRD_PERSON, hypothesis):
        confidence -= 0.07
    if recommendation:
        request_data = {"last_utterances": [[hypothesis]]}
        result = requests.post(NER_URL, json=request_data).json()
        if result[0]:
            confidence += 0.07
    if len(re.findall(r'\?', hypothesis)):
        confidence -= 0.1
    if not re.search(r'[a-zA-Z]', hypothesis):
        confidence = 0
    return confidence


def process_hypothesis(hyp: str) -> str:
    logger.info(f"sent_before_tok -- {hyp}")
    hyp_sent_tok = sent_tokenize(hyp.replace('lt 3', '').replace('...', '.').replace('..', '.'))
    if len(hyp_sent_tok) > 3:
        hyp_sent_tok = hyp_sent_tok[:len(hyp_sent_tok)-2]
    elif len(hyp_sent_tok) > 2:
        hyp_sent_tok = hyp_sent_tok[:len(hyp_sent_tok)-1]
    elif len(hyp_sent_tok) > 4:
        hyp_sent_tok = hyp_sent_tok[:3]
    sentences_capitalized = [s.capitalize() for s in hyp_sent_tok]
    text_truecase = re.sub(" (?=[\.,'!?:;])", "", ' '.join(sentences_capitalized))
    logger.info(f"sent_after_tok -- {hyp_sent_tok}")
    return text_truecase


def count_gen_responses(ctx, actor, not_reset=False):
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    num_gen_responses = int(shared_memory.get("num_gen_responses", 0))

    if num_gen_responses:
        num_gen_responses = int(num_gen_responses) + 1
        logger.info(f"count_gen_responses -- increased num gen responses to: {num_gen_responses}")
        if int(shared_memory.get("num_gen_responses", 0)) > 2 and not not_reset: 
            int_ctx.save_to_shared_memory(ctx, actor, num_gen_responses=0)
            logger.info(f"count_gen_responses -- TOO MUCH GEN RESPONSES. decrease from {num_gen_responses} to 0")
        else:
            int_ctx.save_to_shared_memory(ctx, actor, num_gen_responses=num_gen_responses)
    else:
        num_gen_responses = 1
        int_ctx.save_to_shared_memory(ctx, actor, num_gen_responses=num_gen_responses)


def generative_response(recommend=False, question=False, discussed_entity="", not_reset=False):

    def generative_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        # ctx.misc.get("slots", {}).get('topic_entity', ''):
        # entity =  str(ctx.misc["slots"]['topic_entity'])
        count_gen_responses(ctx, actor, not_reset=not_reset)
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
        request_data = compose_data_for_dialogpt(ctx, actor, recommend=recommend, discussed_entity=discussed_entity)
        if len(request_data) > 0:
            result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
            hypotheses = result[0]
        else:
            hypotheses = []
        if hypotheses:
            for hyp in hypotheses[0]:
                if hyp:
                    hyp = process_hypothesis(hyp)
                    if hyp[-1] not in [".", "?", "!"]:
                        hyp += "."
                    gathering_responses(hyp, determine_confidence(ctx, actor, hyp, recommendation=recommend), {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
        if len(curr_responses) == 0:
            return ""

        with open("test.txt", "a") as f:
            f.write(str(curr_responses) + str(curr_confidences))
        for index in sorted(range(len(curr_confidences)), key=lambda k: curr_confidences[k])[:3]:
            with open("test.txt", "a") as f:
                f.write(f'\n\n{index}')
                f.write(f'{curr_responses}') 
            # curr_responses.pop(index)
            # curr_confidences.pop(index)
            # curr_human_attrs.pop(index)
            # curr_bot_attrs.pop(index)
            # curr_attrs.pop(index)

        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)
    return generative_response_handler


def generate_np_response(response_options=[''], recommend=False, discussed_entity=""):
    
    reply = random.choice(response_options)

    def np_response(ctx: Context, actor: Actor, *args, **kwargs) -> Any:
        count_gen_responses(ctx, actor)
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
            request_data = compose_data_for_dialogpt(ctx, actor, recommend=recommend, discussed_entity=discussed_entity)
            if len(request_data) > 0:
                result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
                hypotheses = result[0]
            else:
                hypotheses = []
            
            if hypotheses:
                for hyp in hypotheses[0]:
                    if hyp:
                        hyp = process_hypothesis(hyp)
                        if hyp[-1] not in [".", "?", "!"]:
                            hyp += "."
                        gathering_responses(hyp, determine_confidence(ctx, actor, hyp), {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
            if len(curr_responses) == 0:
                return ""

            with open("test.txt", "a") as f:
                f.write(str(curr_responses) + str(curr_confidences))
            for index in sorted(range(len(curr_confidences)), key=lambda k: curr_confidences[k])[:3]:
                with open("test.txt", "a") as f:
                    f.write(f'\n\n{index}')
                    f.write(f'{curr_responses}')
            #     curr_responses.pop(index)
            #     curr_confidences.pop(index)
            #     curr_human_attrs.pop(index)
            #     curr_bot_attrs.pop(index)
            #     curr_attrs.pop(index)
        
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


def ask_about_presequence(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    if ctx.validation:
        return ""
    used_questions = ctx.misc.get("used_questions", [])
    ctx.misc["next_question"] = []
    ASK_ABOUT_PRESEQ = dict(ASK_ABOUT_PRESEQ_DICT)
    if len(used_questions) > 1:
        ctx.misc['slots']["time_to_go"] = True
    preseq_items = list(ASK_ABOUT_PRESEQ.items())
    random.shuffle(preseq_items)
    for topic, questions in preseq_items:
        if topic not in used_questions:
            question_topic = topic
            question_seq = questions
            break
    used_questions.append(topic)
    ctx.misc["question_topic"] = question_topic
    ctx.misc["user_dislikes_topic"] = question_seq["user_dislikes_topic"]
    ctx.misc["used_questions"] = used_questions
    ctx.misc["next_question"] = question_seq["question"]
    ctx.misc["next_prequestion"] = question_seq["prequestion_1"]
    request_data = question_seq["left_context"]
    return str(question_seq["prequestion"]) 
    if len(request_data) > 0:
        result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
        hypotheses = result[0]
    else:
        hypotheses = []
    
    if hypotheses:
        for hyp in hypotheses[0]:
            hyp = process_hypothesis(hyp)
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
    request_data = compose_data_for_dialogpt(ctx, actor)
    if len(request_data) > 0:
        result = requests.post(DIALOGPT_RESPOND, json={"utterances_histories": [request_data]}).json()
        hypotheses = result[0]
    else:
        hypotheses = []
    presequence = ctx.misc.get("next_prequestion", '')
    if hypotheses:
        for hyp in hypotheses[0]:
            if re.search(STOP_WORDS, hyp):
                continue
            hyp = process_hypothesis(hyp)
            if hyp[-1] not in [".", "?", "!"]: #переделать в отдельную функцию фильтрации реддита
                hyp += "."
            return hyp + ' ' + str(presequence)
    else:
        return ''


def get_hyponyms(ctx: Context, actor: Actor, *args, **kwargs) -> str: #sister terms also might be of interest
    common_hyponyms = []
    available_hyponyms = ctx.misc.get("slots", {}).get('available_hyponyms', {})
    used_hyponyms = ctx.misc.get("slots", {}).get('used_hyponyms', [])
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
                    definitions = {}
                    for hypo in all_candidates:
                        definitions[hypo.lemma_names()[0].replace('_', ' ')] = hypo.definition()
                    candidate_hyponyms = [ss.lemma_names()[0].replace('_', ' ') for ss in all_candidates]
                    common_hyponyms = list(set(common_words) & set(candidate_hyponyms))
    if common_hyponyms:
        ctx.misc["slots"]['we_found_hyp'] = True
        hyponym = common_hyponyms[random.randrange(0, len(common_hyponyms))] #заменить на рандомный выбор
        available_hyponyms[entity] = common_hyponyms.remove(hyponym)
        ctx.misc["slots"]['available_hyponyms'] = available_hyponyms
        # blob = TextBlob([hyponym])
        # plural_hyponym = [word.pluralize() for word in blob.words][0]
        syns = wordnet.synsets(hyponym)
        used_hyponyms.append(hyponym)
        hyponym_pl = hyponym + 's'
        ctx.misc["slots"]['used_hyponyms'] = used_hyponyms
        ctx.misc["slots"]['current_hyp_definition'] = definitions[hyponym]
        hyponym_topic = HYPONYM_TOPIC[random.randrange(0, len(HYPONYM_TOPIC))].replace('_', hyponym_pl)
        switch_topic = SWITCH_TOPIC[random.randrange(0, len(SWITCH_TOPIC))].replace('_', ctx.misc.get("slots", {}).get('topic_entity', ''))
        hyponym_question = switch_topic + hyponym_topic
        ctx.misc['slots']['hyp_question_asked'] = True
        return hyponym_question
    else:
        return ''


def give_hyponym_definition():
    def give_hyponym_definition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        random.shuffle(APOLOGIZE_FOR_DIFFICULT_WORD)
        definition = str(ctx.misc.get("slots", {}).get('current_hyp_definition', ''))
        if ctx.misc.get("slots", ""):
            ctx.misc["slots"]['current_hyp_definition'] = ''
        return APOLOGIZE_FOR_DIFFICULT_WORD[0] + ' ' + definition
    return give_hyponym_definition_handler


def generate_with_string(to_append='get_questions', position_gen='before'):

    def generate_with_string_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        count_gen_responses(ctx, actor)
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
        if ctx.validation:
            return ""
        request_data = compose_data_for_dialogpt(ctx, actor)
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
            if type(to_append) == list:
                used_prompts = ctx.misc.get("used_prompts", [])
                random.shuffle(to_append)
                for prompt in to_append:
                    if prompt not in used_prompts:
                        string_to_attach = prompt
                        break
                used_prompts.append(string_to_attach)
                ctx.misc["used_prompts"] = used_prompts
        if hypotheses:
            for hyp in hypotheses[0]:
                if hyp:
                    hyp = process_hypothesis(hyp)
                    if hyp[-1] not in [".", "?", "!"]: #переделать в отдельную функцию фильтрации реддита
                        hyp += "."
                if string_to_attach:
                    if position_gen == 'before':
                        hyp = hyp + ' ' + str(string_to_attach)
                    elif position_gen == 'after':
                        hyp = str(string_to_attach) + ' ' + hyp #тут аккуратнее, мб стоит добавить малтиреспонс хэндлер
                gathering_responses(hyp, determine_confidence(ctx, actor, hyp.replace(str(string_to_attach), '')), {}, {}, {"can_continue": CAN_CONTINUE_SCENARIO})
                
        if len(curr_responses) == 0:
                return ""
        with open("test.txt", "a") as f:
            f.write(str(curr_responses) + str(curr_confidences))
            for index in sorted(range(len(curr_confidences)), key=lambda k: curr_confidences[k])[:3]:
                with open("test.txt", "a") as f:
                    f.write(f'\n\n{index}')
                    f.write(f'{curr_responses}')
        return int_rsp.multi_response(
            replies=curr_responses,
            confidences=curr_confidences,
            human_attr=curr_human_attrs,
            bot_attr=curr_bot_attrs,
            hype_attr=curr_attrs,
        )(ctx, actor, *args, **kwargs)
    return generate_with_string_handler

# а в каком случае его включать? посмотреть на другие сценарии! нужна ли штука которая поспрашивает вопросы для текущего топика: возможно впишется в чат эбаут
# есть возможность взять вопросы которые и так есть в дримботе link-to (ПОСМОТРЕТЬ!!!). вопросы лежат каждый в отдельном файлике, Диля кинет ссылку (вопросы на разные темы)
# оч поход на чатэбаут но с нашей инициативой (initiate topic!!!), то есть по сути это штука поговорить про топик который я преддложила
