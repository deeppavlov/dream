import json
import random
import re

from common.grounding import COMPLIMENT_PROPERTIES
from common.utils import MIDAS_SEMANTIC_LABELS


INTENT_DICT = {
    "Information_DeliveryIntent": "You just told me about ENTITY_NAME, right?",
    "Information_RequestIntent": "You've asked me about ENTITY_NAME haven't you?",
    "User_InstructionIntent": "You just gave me a command. Am I right?",
    "Opinion_ExpressionIntent": "You just shared your opinion about ENTITY_NAME with me, right?",
    "ClarificationIntent": "You clarified me what you've just said about ENTITY_NAME, right?",
    "Topic_SwitchIntent": "You wanted to change topic, right?",
    "Opinion_RequestIntent": "You wanted to hear my thoughts about ENTITY_NAME, am I correct?",
}

MIDAS_INTENT_DICT = {
    "open_question_factual": "You have asked me about ENTITY_NAME, right?",
    "open_question_opinion": "You have requested my opinion about ENTITY_NAME, right?",
    "open_question_personal": "You have asked me a personal question, right?",
    "yes_no_question": "You have asked me a yes-no question about ENTITY_NAME, right?",
    "clarifying_question": "You asked to clarify what I've just said about ENTITY_NAME, right?",
    "command": "You just gave me a command. Am I right?",
    "dev_command": "You have just given me a command. Am I right?",
    "pos_answer": "You have just given me a positive answer. Am I right?",
    "neg_answer": "You have just given me a negative answer. Am I right?",
    "statement": "You have just stated something. Am I right?",
    "complaint": "You have just complained on ENTITY_NAME. Am I right?",
    "comment": "You have just commented on ENTITY_NAME. Am I right?",
}

TOPIC_DICT = {
    "Garden": "We were discussing gardening, am I right?",
    "PersonalTransport": "We were discussing cars, am I right?",
    "Animals&Pets": "We were discussing animals, am I right?",
    "Toys&Games": "We were discussing games, am I right?",
    "Videogames": "We were discussing videogames, am I right?",
    "Beauty": "We were talking about beauty, am I right?",
    "Job": "We were talking about job, am I right?",
    "Art&Hobbies": "We were talking about art and hobbies, am I right?",
    "Sports": "We were discussing sports, am I right?",
    "News": "We were discussing news, am I right?",
    "Travel": "We were discussing traveling, am I right?",
    "Politics": "We were discussing politics, am I right?",
    "Celebrities&Events": "We were discussing celebrities, am I right?",
    "Depression": "We were talking about depression, am I right?",
    "Food": "We were discussing food, am I right?",
    "Books&Literature": "We were discussing books, am I right?",
    "Music": "We were discussing music, am I right?",
    "Gadgets": "We were discussing gadgets, am I right?",
    "Movies_TV": "We were discussing movies, am I right?",
    "Education": "We were discussing education, am I right?",
    "MassTransit": "We were discussing mass transit, am I right?",
    "Psychology": "We were discussing psychology, am I right?",
    "Science_and_Technology": "We were discussing science and technology, am I right?",
    "Disasters": "We were discussing something bad, am I right?",
    "Space": "We were discussing space, am I right?",
    "Finance": "We were discussing finance, am I right?",
    "Artificial_Intelligence": "We were discussing AI, am I right?",
    "Religion": "We were discussing religion, am I right?",
    "Leisure": "We were talking about leisure time, am I right?",
    "Clothes": "We were talking about clothes, am I right?",
    "Health&Medicine": "We were discussing health issues, am I right?",
    "Home&Design": "We were discussing home utilities, am I right?",
    "Family&Relationships": "We were discussing family matters, am I right?",
}

DA_TOPIC_DICT = {
    "Entertainment_Movies": "We were discussing movies, am I right?",
    "Entertainment_Books": "We were discussing books, am I right?",
    "Entertainment_General": "We are just trying to be polite to each other, aren't we?",
    "Science_and_Technology": "I was under impression we were chatting about technology stuff.",
    "Sports": "So I thought we were talking about sports.",
    "Politics": "Correct me if I'm wrong but I thought we were discussing politics.",
}


COBOT_TOPIC_DICT = {
    "Phatic": "We are just trying to be polite to each other, aren't we?",
    "Other": "I can't figure out what we are talking about exactly. Can you spare a hand?",
    "Movies_TV": "We were discussing movies, am I right?",
    "Music": "Thought we were talking about music.",
    "SciTech": "I was under impression we were chatting about technology stuff.",
    "Literature": "We were discussing literature, am I right?",
    "Travel_Geo": "Thought we were talking about some travel stuff.",
    "Celebrities": "We're discussing celebrities, right?",
    "Games": "We're talking about games, correct?",
    "Pets_Animals": "Thought we were talking about animals.",
    "Sports": "So I thought we were talking about sports.",
    "Psychology": "Correct me if I'm wrong but I thought we were talking about psychology.",
    "Religion": "Aren't we talking about religion, my dear?",
    "Weather_Time": "Aren't we discussing the best topic of all times, weather?",
    "Food_Drink": "Thought we were discussing food stuff.",
    "Politics": "Correct me if I'm wrong but I thought we were discussing politics.",
    "Sex_Profanity": "This is a something I'd rather avoid talking about.",
    "Art_Event": "My understanding is we are discussing arts, aren't we?",
    "Math": "My guess is we were talking about math stuff.",
    "News": "Aren't we discussing news my dear friend?",
    "Entertainment": "Thought we were discussing something about entertainment.",
    "Fashion": "We are talking about fashion am I right?",
}


def get_entity_name(annotations):
    entity_list = []
    for tmp in annotations.get("ner", []):
        if len(tmp) > 0 and "text" in tmp[0]:
            entity_list.append(tmp[0]["text"])
    if len(entity_list) == 1:
        entity_name = entity_list[0]
    elif len(entity_list) > 1:
        entity_name = ",".join(entity_list[:-1]) + " and " + entity_list[-1]
    else:
        entity_name = ""
    entity_name = entity_name.replace("?", "")
    return entity_name


with open("./data/midas_acknowledgements.json", "r") as f:
    MIDAS_INTENT_ACKNOWLEDGEMENTS = json.load(f)

MIDAS_INTENT_ANALOGUES = {
    "open_question_opinion": ["open_question_opinion", "Opinion_RequestIntent"],
    "open_question_factual": ["open_question_factual", "Information_RequestIntent"],
    "open_question_personal": ["open_question_personal"],
    "yes_no_question": ["yes_no_question"],
}


def get_midas_analogue_intent_for_any_intent(intent):
    for midas_intent_name in MIDAS_INTENT_ANALOGUES:
        if intent in MIDAS_INTENT_ANALOGUES[midas_intent_name]:
            return midas_intent_name
    if intent in MIDAS_SEMANTIC_LABELS:
        return intent
    return None


def get_midas_intent_acknowledgement(intent, entity_name):
    pos_responses = MIDAS_INTENT_ACKNOWLEDGEMENTS.get(intent, [])
    if pos_responses:
        response = random.choice(pos_responses).replace("SUBJECT", entity_name)
        response = response.replace("PROPERTY", random.choice(COMPLIMENT_PROPERTIES).lower())
    else:
        response = ""
    response = response.replace("?", "")
    return response


def reformulate_question_to_statement(question):
    statement = question.lower()
    # do you have any dogs -> whether I have any dogs
    statement = re.sub(r"^do you", "whether I", statement)
    # why do you have three dogs -> why I have three dogs
    statement = re.sub(r"\bdo you\b", "I", statement)
    # are you kidding -> whether I'm kidding
    statement = re.sub(r"^are you", "whether I'M", statement)
    # why are you laughing -> why I'm laughing
    statement = re.sub(r"\bare you\b", "I'M", statement)

    # what are yours favorite colors -> what are my favorite colors
    statement = re.sub(r"\byours\b", "MY", statement)
    # what is your favorite color -> what is my favorite color
    statement = re.sub(r"\byour\b", "MY", statement)
    # can you tell me jokes -> can I tell me jokes
    statement = re.sub(r"\byou\b", "I", statement)
    # can you tell me jokes -> can I tell you jokes
    statement = re.sub(r"\bme\b", "YOU", statement)
    # can you say my name -> can I say your name
    statement = re.sub(r"\bmy\b", "YOUR", statement)

    return statement.lower()
