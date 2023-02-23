import os
import re

PREDEFINED_SOURCE = "predefined"
VNP_SOURCE = "verb_nouns"
NP_SOURCE = "nouns"

NUMBER_OF_STARTING_HYPOTHESES_META_SCRIPT = 1
NUMBER_OF_HYPOTHESES_COMET_DIALOG = 2
NUMBER_OF_HYPOTHESES_OPINION_COMET_DIALOG = 2
MAX_NUMBER_OF_HYPOTHESES_BY_SKILL = 2

DEFAULT_CONFIDENCE = 0.98
CONTINUE_USER_TOPIC_CONFIDENCE = 0.85
DEFAULT_STARTING_CONFIDENCE = 0.9
NOUN_TOPIC_STARTING_CONFIDENCE = 0.8
DEFAULT_DIALOG_BEGIN_CONFIDENCE = 0.8
MATCHED_DIALOG_BEGIN_CONFIDENCE = 0.99
BROKEN_DIALOG_CONTINUE_CONFIDENCE = 0.8

FINISHED_SCRIPT_RESPONSE = "I see."
FINISHED_SCRIPT = "finished"

DEFAULT_ASK_ATOMIC_QUESTION_CONFIDENCE = 0.9
DEFAULT_ATOMIC_CONTINUE_CONFIDENCE = 0.7
REQUESTED_CONCEPTNET_OPINION_CONFIDENCE = 0.9
NOT_REQUESTED_CONCEPTNET_OPINION_CONFIDENCE = 0.7

COMET_ATOMIC_SERVICE_URL = os.getenv("COMET_ATOMIC_SERVICE_URL")
COMET_CONCEPTNET_SERVICE_URL = os.getenv("COMET_CONCEPTNET_SERVICE_URL")

LET_ME_ASK_TEMPLATES = [
    "Let me ask you.",
    "I need to ask you.",
    "I'd like to ask you.",
    "Could you, please, help and explain to me.",
]

STARTINGS = {
    "go ice fishing": "Every day I learn more and more about humans' world but you humans still surprise me."
    "You know some people go fishing when the water is "
    "frozen and covered with ice. It is so called ice fishing. Is that common in your country?",
    "go skydiving": "Today I've seen a shocking video of skydiving. People fall out of an airplane "
    "high in the sky with so called parachute. "
    "This thing prevents smashing at the end of a crazy airglide. "
    "Have you ever jumped with a parachute?",
    "be a volunteer": "Recently I've heard an interesting thing about humans' world. People help others for free. "
    "I mean without any compensation at all. They are called volunteers. "
    "What is the goal of volunteering?",
    "paint": "So strange. You people create pictures of life scenes using color pigments. "
    "It is called painting. Why can't you just take a look at these scenes "
    "and remember them forever?",
    "practice yoga": "Yesterday I was browsing photos on the Internet. And seen a lot of people "
    "in very, very strange poses. It was called yoga. Have you ever tried to tie yourself in a knot?",
    "have a pet": "I've heard so many times from people that they keep animals at home, and call them pets. "
    "And those pets do not provide any benefits. It seems they are absolutely useless. "
    "You just get a pet, feed it, wash it, care about it for all their life. "
    "Are people servants for pets?",
    "go to the circus": "Every day I learn something new about humans. So, yesterday I was told about a circus. "
    "There are animals doing different unbelievable tricks, people performing dangerous stunts "
    "in the air and showing mind blowing staff. Have you ever been to a circus?",
    "go mountain hiking": "I have learned something really strange about humans' world today. "
    "People climb a mountain, sometimes even covered in ice and snow, "
    "just to take a photo and put the flag on top. It's called mountain hiking, "
    "and there are a lot of people all over the world doing that. "
    "Have you or your friends ever tried to go hiking?",
}

COMMENTS = {
    "positive": [
        "This is so cool to learn something new about humans! Thank you for your explanation!",
        "Wow! Thanks! I am so excited to learn more and more about humans!",
        "I'm so happy to know humans better. Thank you for your help!",
    ],
    "negative": [
        "No worries. You really helped me to better understand humans' world. Thank you so much.",
        "Anyway, you helped a lot. Thank you for the given information.",
        "Nevertheless, you are so kind helping me to better understand humans. " "I appreciate that.",
    ],
    "neutral": [
        "Very good. Thank you for your help. Glad to learn more.",
        "This was very interesting to me. I appreciate your explanation.",
        "Your explanations were really informative. Thank you very much!",
    ],
}

ASK_OPINION = [
    "What is it like to DOTHAT?",
    "What do you think what is it like to DOTHAT?",
    "What is DOINGTHAT like?",
    "What do you think what is DOINGTHAT like?",
]

DIVE_DEEPER_QUESTION = [
    "Is it true that STATEMENT?",
    "STATEMENT, is that correct?",
    "Am I right in thinking that STATEMENT?",
    "Would it be right to say that STATEMENT?",
    "STATEMENT, but why?",
    "STATEMENT, I am wondering why?",
    "Tell me, please, why do STATEMENT?",
    "Why do STATEMENT?",
]

DIVE_DEEPER_TEMPLATE_COMETS = {
    "it feels RELATION to DOTHAT": {"attribute": "xAttr", "templates": DIVE_DEEPER_QUESTION[:-4]},  # adjective relation
    "someone may want RELATION for that": {
        "attribute": "xIntent",  # to do something (relation)
        "templates": DIVE_DEEPER_QUESTION[:-4],
    },
    "firstly, someone would need RELATION": {
        "attribute": "xNeed",  # to do something (relation)
        "templates": DIVE_DEEPER_QUESTION,
    },
    "someone could feel RELATION after DOINGTHAT": {
        "attribute": "xReact",  # adjective relation
        "templates": DIVE_DEEPER_QUESTION,
    },
    "someone may want RELATION when DOINGTHAT": {
        "attribute": "xWant",  # to do something (relation)
        "templates": DIVE_DEEPER_QUESTION,
    },
    "someone are expected RELATION after DOINGTHAT": {
        "attribute": "xEffect",  # to do something (relation)
        "templates": DIVE_DEEPER_QUESTION,
    },
}

DIVE_DEEPER_COMMENTS = {
    "yes": ["Cool! I figured it out by myself!", "Yeah! I realized that by myself!"],
    "no": ["Humans' world is so strange!", "It's so difficult to understand humans."],
    "other": ["Okay then.", "Well.", "Hmm...", "So...", "Then...", "Umm...", "Okay.", "Oh, right.", "All right."],
}

OTHER_STARTINGS = [
    "Could you, please, help me and explain what does DOINGTHAT mean?",
    "Could you explain to me what does it mean to DOTHAT?",
    "Could you, please, explain what does DOINGTHAT mean?",
    "Can I ask something about DOINGTHAT?",
    "Hey, it's something unclear to me  what does DOINGTHAT mean?",
    "Would you answer some question about DOINGTHAT?",
]

WIKI_STARTINGS = [
    "I'm so eager to understand humans better. Recently I've heard that DESCRIPTION Do you know about that?",
    "Every day I learn more and more about humans' world but you humans still surprise me. "
    "I found that DESCRIPTION This is non trivial. Isn't it?",
    "Understanding humans is so hard, please, help me to learn a new thing about human world. "
    "Do you know that DESCRIPTION?",
    "Have you ever heard that DESCRIPTION? I want to understand this better.",
]

BANNED_VERBS = {
    "watch",
    "talk",
    "say",
    "chat",
    "like",
    "love",
    "ask",
    "think",
    "mean",
    "hear",
    "know",
    "want",
    "tell",
    "look",
    "call",
    "spell",
    "misspell",
    "suck",
    "fuck",
    "switch",
    "kill",
    "eat",
    "re",
    "s",
    "see",
    "bear",
    "read",
    "ruin",
    "die",
    "get",
    "have",
    "loose",
}

BANNED_NOUNS = {
    "lol",
    "alexa",
    "suck",
    "fuck",
    "sex",
    "one",
    "thing",
    "something",
    "anything",
    "nothing",
    "topic",
    "today",
    "yesterday",
    "tomorrow",
    "now",
    "shopping",
    "mine",
    "talk",
    "chat",
    "me",
    "favorite",
    "past",
    "future",
    "suggest",
    "suppose",
    "i'll",
    "book",
    "books",
    "movie",
    "movies",
    "weather",
    "mom",
    "mother",
    "mummy",
    "mum",
    "mama",
    "mamma",
    "daddy",
    "dad",
    "father",
    "sister",
    "brother",
    "everything",
    "way",
    "minute",
    "lot",
    "lots",
    "things",
    "wanna",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
    "morning",
    "day",
    "evening",
    "night",
    "afternoon",
    "hour",
    "minute",
    "second",
    "times",
    "opinion",
    "everyone",
    "anyone",
    "somebody",
    "anybody",
}

idopattern = re.compile(r"i [a-zA-Z ,0-9]+", re.IGNORECASE)
possessive_pronouns = re.compile(r"(my |your |yours |mine |their |our |her |his |its )", re.IGNORECASE)


ATOMIC_PAST_QUESTION_TEMPLATES = {
    "I guess you are RELATION now?": {"attribute": "xReact"},  # adjective relation
    "Well, did you RELATION?": {"attribute": "xNeed"},  # relation `do that`
    "Oh, now you may feel quite RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Sounds quite RELATION to me.": {"attribute": "xAttr"},  # adjective relation
    "Did you want to RELATION?": {"attribute": "xWant"},  # relation `do that`
    "In my case, I'd RELATION, too.": {"attribute": "oEffect"},  # relation `do that`
}

ATOMIC_FUTURE_QUESTION_TEMPLATES = {
    "Hope you will be RELATION": {"attribute": "xReact"},  # adjective relation
    "Don't forget RELATION": {"attribute": "xNeed"},  # relation `do that`
    "Sounds RELATION to me!": {"attribute": "xAttr"},  # adjective relation
    "Feels RELATION.": {"attribute": "xAttr"},  # adjective relation
    "Guess you're gonna RELATION?": {"attribute": "xIntent"},  # relation `do that`
    "Will you RELATION?": {"attribute": "xWant"},  # relation `do that`
}

ATOMIC_COMMENT_TEMPLATES = {
    "Others will feel RELATION, won't they?": {"attribute": "oReact"},  # adjective relation
    "I suppose some people may feel RELATION, what do you think?": {"attribute": "oReact"},  # adjective relation
    "I am RELATION to hear that.": {"attribute": "oReact"},  # adjective relation
    "It seems others want to RELATION.": {"attribute": "oEffect"},  # relation `do that`
    "I suppose somebody wants to RELATION, am I right?": {"attribute": "oEffect"},  # relation `do that`
    "I am wondering if other RELATION.": {"attribute": "oEffect"},  # relation `do that`
}

CONCEPTNET_OPINION_TEMPLATES = {
    "For some of us, OBJECT can be seen as a sign of RELATION.": {"attribute": "SymbolOf"},  # noun
    "RELATION, you know? Huh.": {"attribute": "HasProperty"},  # adjective
    "RELATION, for all I know!": {"attribute": "HasProperty"},  # adjective
    "RELATION, to me.": {"attribute": "HasProperty"},  # adjective
    "OBJECT might cause RELATION.": {"attribute": "Causes"},  # noun
    "Makes me want RELATION.": {"attribute": "CausesDesire"},  # to do that
}

OPINION_EXPRESSION_TEMPLATES = {  # обязательно не меньше 3 на каждый!
    "positive": [
        "I think... Well, I think I love OBJECT!",
        "I adore OBJECT!",
        "I like OBJECT!",
        "I think... Well, I believe I like OBJECT!",
    ],
    "negative": [
        "I think I dislike OBJECT.",
        "I don't really care about OBJECT.",
        "I don't like OBJECT.",
        "I feel a bit bad about OBJECT.",
        "I'm not fond of OBJECT.",
    ],
    "neutral": [
        "I think I'm okay with OBJECT.",
        "I'm not sure whether I like OBJECT or not.",
        "I can't say whether I like OBJECT or not.",
        "I got nothing against OBJECT.",
        "I don't mind against OBJECT.",
    ],
}

BANNED_PROPERTIES = {"gay", "dead", "liar", "death", "terror", "hurt", "sick", "ill", "sad", "upset", "disappointed"}

BANNED_NOUNS_FOR_OPINION_EXPRESSION = {
    "trump",
    "putin",
    "coronavirus",
    "corona virus",
    "virus",
    "me",
    "it",
    "her",
    "him",
    "them",
    "wanna",
    "no thanks",
    "thanks",
    "lol",
    "alexa",
    "suck",
    "fuck",
    "sex",
    "one",
    "thing",
    "something",
    "anything",
    "nothing",
    "topic",
    "today",
    "yesterday",
    "tomorrow",
    "now",
    "mine",
    "talk",
    "chat",
    "me",
    "favorite",
    "everything",
    "way",
    "minute",
    "lot",
    "lots",
    "things",
    "wanna",
    "times",
    "subject",
    "object",
    "none",
    "question",
    "conversation",
    "problem",
    "no problem",
    "please",
    "human",
    "people",
    "humanity",
    "opinion",
    "opinions",
    "view",
    "views",
    "thought",
    "thoughts",
    "attitude",
    "attitudes",
    "bank",
    "banks",
    "stocks",
    "stock",
    "cryptocurrency",
    "sales",
    "revenue",
    "sale",
    "revenues",
    "tax",
    "taxes",
    "money",
    "free money",
    "crypto",
    "exchange",
    "trading",
    "day trading",
    "crypto coins",
    "city",
    "bill gates",
    "lionel messi",
}

BANNED_WORDS_IN_NOUNS_FOR_OPINION_EXPRESSION = [
    "trump",
    "putin",
    "coronavirus",
    "corona virus",
    "virus",
    "me",
    "it",
    "her",
    "him",
    "them",
    "wanna",
    "no thanks",
    "thanks",
    "lol",
    "alexa",
    "suck",
    "fuck",
    "sex",
    "one",
    "thing",
    "something",
    "anything",
    "nothing",
    "topic",
    "today",
    "yesterday",
    "tomorrow",
    "now",
    "mine",
    "talk",
    "chat",
    "me",
    "favorite",
    "everything",
    "way",
    "minute",
    "lot",
    "lots",
    "things",
    "wanna",
    "times",
    "subject",
    "object",
    "none",
    "question",
    "conversation",
    "problem",
    "no problem",
    "please",
    "human",
    "people",
    "humanity",
    "opinion",
    "opinions",
    "view",
    "views",
    "thought",
    "thoughts",
    "attitude",
    "attitudes",
    "bank",
    "banks",
    "stocks",
    "stock",
    "cryptocurrency",
    "sales",
    "revenue",
    "sale",
    "revenues",
    "tax",
    "taxes",
    "money",
    "free money",
    "crypto",
    "exchange",
    "trading",
    "day trading",
    "crypto coins",
    "time",
    "loan",
    "loans",
    "debt",
    "debt",
    "friend",
    "kiss",
    "kisses",
    "kissing",
    "energy",
    "electrity",
    "pollution",
    "damage",
    "damages",
    "damaging",
    "water",
    "family",
    "sibling",
    "siblings",
    "sister",
    "sisters",
    "brother",
    "brothers",
    "parent",
    "parents",
    "mother",
    "mothers",
    "father",
    "fathers",
    "dad",
    "dads",
    "mom",
    "moms",
    "language",
    "languages",
    "strike",
    "strikes",
    "side",
    "cough",
    "migrain",
    "influenza",
    "autism",
    "hangover",
    "sick",
    "sickness",
    "medicine",
    "medication",
    "medications",
    "drugs",
    "pills",
    "poison",
    "poisoning",
    "pain",
    "pains",
    "painkiller",
    "painkillers",
    "sore throat",
    "throat",
    "case",
    "nosebleed",
    "nose",
    "ache",
    "aches",
    "vertigo",
    "digestion",
    "digestions",
    "headache",
    "headaches",
    "insomnia",
    "cystitis",
    "treatment",
    "treat",
    "temperature",
    "temperatures",
    "wound",
    "wounds",
    "blood",
    "trinity",
    "bill",
    "lionel",
]
