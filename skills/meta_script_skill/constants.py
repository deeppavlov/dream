import re

PREDEFINED_SOURCE = "predefined"
VNP_SOURCE = "verb_nouns"
NP_SOURCE = "nouns"

DEFAULT_CONFIDENCE = 0.98
CONTINUE_USER_TOPIC_CONFIDENCE = 0.85
DEFAULT_STARTING_CONFIDENCE = 0.9
NOUN_TOPIC_STARTING_CONFIDENCE = 0.8
DEFAULT_DIALOG_BEGIN_CONFIDENCE = 0.8
MATCHED_DIALOG_BEGIN_CONFIDENCE = 0.99
BROKEN_DIALOG_CONTINUE_CONFIDENCE = 0.8
FINISHED_SCRIPT_RESPONSE = "I see. Let's talk about something you want. Pick up the topic."
FINISHED_SCRIPT = "finished"

COMET_SERVICE_URL = "http://comet_atomic:8053/comet"
CONCEPTNET_SERVICE_URL = "http://comet_conceptnet:8065/comet"

LET_ME_ASK_TEMPLATES = [
    "Let me ask you.",
    "I need to ask you.",
    "I'd like to ask you.",
    "Could you, please, help and explain to me."
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
                          "Have you or your friends ever tried to go hiking?"
}

COMMENTS = {"positive": ["This is so cool to learn something new about humans! Thank you for your explanation!",
                         "Wow! Thanks! I am so excited to learn more and more about humans!",
                         "I'm so happy to know humans better. Thank you for your help!"],
            "negative": ["No worries. You really helped me to better understand humans' world. Thank you so much.",
                         "Anyway, you helped a lot. Thank you for the given information.",
                         "Nevertheless, you are so kind helping me to better understand humans. "
                         "I appreciate that."],
            "neutral": ["Very good. Thank you for your help. Glad to learn more.",
                        "This was very interesting to me. I appreciate your explanation.",
                        "Your explanations were really informative. Thank you very much!"]}

ASK_OPINION = ["What is it like to DOTHAT?",
               "What do you think what is it like to DOTHAT?",
               "What is DOINGTHAT like?",
               "What do you think what is DOINGTHAT like?"]

DIVE_DEEPER_QUESTION = ["Is it true that STATEMENT?",
                        "STATEMENT, is that correct?",
                        "Am I right in thinking that STATEMENT?",
                        "Would it be right to say that STATEMENT?",
                        "STATEMENT, but why?",
                        "STATEMENT, I am wondering why?",
                        "Tell me, please, why do STATEMENT?",
                        "Why do STATEMENT?"
                        ]

DIVE_DEEPER_TEMPLATE_COMETS = {
    "it feels RELATION to DOTHAT": {"attribute": "xAttr",  # adjective relation
                                    "templates": DIVE_DEEPER_QUESTION[:-4]},
    "someone may want RELATION for that": {"attribute": "xIntent",  # to do something (relation)
                                           "templates": DIVE_DEEPER_QUESTION[:-4]},
    "firstly, someone would need RELATION": {"attribute": "xNeed",  # to do something (relation)
                                             "templates": DIVE_DEEPER_QUESTION},
    "someone could feel RELATION after DOINGTHAT": {"attribute": "xReact",  # adjective relation
                                                    "templates": DIVE_DEEPER_QUESTION},
    "someone may want RELATION when DOINGTHAT": {"attribute": "xWant",  # to do something (relation)
                                                 "templates": DIVE_DEEPER_QUESTION},
    "someone are expected RELATION after DOINGTHAT": {"attribute": "xEffect",  # to do something (relation)
                                                      "templates": DIVE_DEEPER_QUESTION}
}

DIVE_DEEPER_COMMENTS = {"yes": ["Cool! I figured it out by myself!",
                                "Yeah! I realized that by myself!"],
                        "no": ["Humans' world is so strange!",
                               "It's so difficult to understand humans."],
                        "other": ["Okay then.",
                                  "Well.",
                                  "Hmm...",
                                  "So...",
                                  "Then...",
                                  "Umm...",
                                  "Okay.",
                                  "Oh, right.",
                                  "All right."]}

OTHER_STARTINGS = [
    "I didn't get what does DOINGTHAT mean?",
    "What does it mean to DOTHAT?",
    "What does DOINGTHAT mean?",
    "Can I ask something about DOINGTHAT?",
    "Hey, I have a question about DOINGTHAT?",
    "Would you answer some question about DOINGTHAT?"
]

WIKI_STARTINGS = [
    "I'm so eager to understand humans better. Recently I've heard that DESCRIPTION Do you know about that?",
    "Every day I learn more and more about humans' world but you humans still surprise me. "
    "I found that DESCRIPTION This is non trivial. Isn't it?",
    "Understanding humans is so hard, please, help me to learn a new thing about human world. "
    "Do you know that DESCRIPTION?",
    "Have you ever heard that DESCRIPTION? I want to understand this better."
]

BANNED_VERBS = ["watch", "talk", "say", "chat", "like", "love", "ask",
                "think", "mean", "hear", "know", "want", "tell", "look",
                "call", "spell", "misspell", "suck", "fuck", "switch", "kill",
                "eat", "re", "s", "see", "bear", "read", "ruin"]

BANNED_NOUNS = ["lol", "alexa", "suck", "fuck", "sex", "one", "thing", "something", "anything", "nothing", "topic",
                "today", "yesterday", "tomorrow", "now", "shopping", "mine", "talk", "chat", "me", "favorite",
                "past", "future", "suggest", "suppose", "i'll", "book", "books", "movie", "movies", "weather",
                "mom", "mother", "mummy", "mum", "mama", "mamma", "daddy", "dad", "father", "sister", "brother",
                "everything"]

idopattern = re.compile(r"i [a-zA-Z ,0-9]", re.IGNORECASE)
