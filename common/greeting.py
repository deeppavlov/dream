import re

GREETING_QUESTIONS = {
    "what_to_talk_about": ["What do you want to talk about?",
                           "What would you want to talk about?",
                           "What would you like to chat about?",
                           "What do you wanna talk about?",
                           "What are we gonna talk about?",
                           "What's on your mind?"
                           ],
    "what_are_your_interests": ["What are your interests?",
                                "What do you like?",
                                "What things excite you?",
                                # "What's cool?"
                                ],
    "what_are_your_hobbies": ["What are your hobbies?",
                              "What do you like to do in your free time?",
                              "Which things capture your imagination?",
                              "What are the things you love to spend your spare time with?",
                              "How do you like to spend your spare time?"
                              ],
    "recent_personal_events": ["What happened in your life recently?",
                               "What's happening?",
                               "What's going on?",
                               "What's up?"
                               ]
}

dont_tell_you_templates = re.compile(
    r"(\bno\b|\bnot\b|\bnone\b|nothing|anything|something|"
    r"(n't|not) (know|remember|tell|share|give|talk|want|wanna)|"
    r"(\bi|\bi'm) ?(do|did|will|am|can)?(n't| not))", re.IGNORECASE)


def dont_tell_you_answer(annotated_phrase):
    if re.search(dont_tell_you_templates, annotated_phrase["text"]):
        return True
    return False
