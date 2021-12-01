"""
```append_question``` is used to change the current flow, like booklink2reply
```append_unused``` is used to add questions that lead to the concrete_book_flow, 
e.g. should be responded by a bookname.
"""
import logging
import sentry_sdk
from os import getenv
import random

from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from dff.core.keywords import PROCESSING, TRANSITIONS, GLOBAL, RESPONSE, LOCAL
from dff.core import Actor
import dff.conditions as cnd
import dff.labels as lbl

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs

from common.movies import SWITCH_MOVIE_SKILL_PHRASE
from common.science import OFFER_TALK_ABOUT_SCIENCE
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
import scenario.response as loc_rsp


fav_keys = list(loc_rsp.FAVOURITE_BOOK_ATTRS.keys())
random.shuffle(fav_keys)
fav_keys = iter(fav_keys)

sentry_sdk.init(getenv("SENTRY_DSN"))

logger = logging.getLogger(__name__)

SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98
DEFAULT_CONFIDENCE = 0.95
BIT_LOWER_CONFIDENCE = 0.90
ZERO_CONFIDENCE = 0.0

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("global_flow", "fallback", 1.5): loc_cnd.exit_skill,
            ("books_general", "dislikes_reading", 1.5): loc_cnd.dislikes_reading,
            ("books_general", "book_start"): cnd.all(
                [
                    loc_cnd.is_proposed_skill,
                    cnd.neg(loc_cnd.check_flag("book_skill_active")),
                    cnd.neg(loc_cnd.check_flag("book_start_visited")),
                ]
            ),
            ("books_general", "book_restart"): cnd.all(
                [
                    loc_cnd.is_proposed_skill,
                    cnd.neg(loc_cnd.check_flag("book_skill_active")),
                    loc_cnd.check_flag("book_start_visited"),
                ]
            ),
            ("bot_fav_book", "fav_name", 1.8): cnd.any([
                loc_cnd.is_last_used_phrase(
                    loc_rsp.FAVOURITE_BOOK_PHRASES
                ),
                loc_cnd.asked_fav_book,
            ]),
            ("bot_fav_book", "fav_denied", 1.8): cnd.all([
                loc_cnd.is_last_used_phrase(
                    loc_rsp.FAVOURITE_BOOK_PHRASES
                ),
                int_cnd.is_no_vars
            ]),
            ("bible_flow", "bible_start", 1.8): cnd.all(
                [
                    loc_cnd.asked_about_bible,
                    cnd.neg(loc_cnd.check_flag("bible_start_visited")),
                ]
            ),
            ("bible_flow", "bible_elaborate", 1.8): cnd.all(
                [
                    loc_cnd.asked_about_bible,
                    loc_cnd.check_flag("bible_start_visited")
                ]
            ),
            ("genre_flow", "tell_phrase", 1): cnd.all(
                [
                    cnd.any([
                        loc_cnd.told_fav_genre,
                        loc_cnd.asked_opinion_genre,
                    ]),
                    loc_cnd.check_genre_regexp,
                ]
            ),
            ("genre_flow", "return_genrebook", 1.2): loc_cnd.genrebook_request_detected,
            ("concrete_book_flow", "user_fav", 0.8): cnd.all(
                [
                    loc_cnd.told_fav_book,
                    loc_cnd.book_in_request
                ]
            ),
            ("concrete_book_flow", "denied_information", 0.8): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase([
                                loc_rsp.TELL_REQUEST,
                                loc_rsp.TELL_REQUEST2
                            ]),
                            loc_cnd.asked_book_content,
                        ]
                    ),
                    int_cnd.is_no_vars
                ]
            ) ,
            ("concrete_book_flow", "tell_about", 1.2): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase([
                                loc_rsp.TELL_REQUEST,
                                loc_rsp.TELL_REQUEST2
                            ]),
                            loc_cnd.asked_book_content,
                        ]
                    ),
                    cnd.any([loc_cnd.about_in_slots, loc_cnd.about_in_request]),
                ]
            ),
            ("concrete_book_flow", "offer_best", 1.6): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.bestbook_in_request,
                ]
            ),
            ("concrete_book_flow", "offer_date", 1.2): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.date_in_request,
                ]
            ),
            ("concrete_book_flow", "tell_date", 0.8): cnd.all(
                [
                    cnd.any([
                        loc_cnd.is_last_used_phrase(loc_rsp.WHEN_IT_WAS_PUBLISHED),
                        loc_cnd.asked_book_date,
                    ]),
                    cnd.any([
                        loc_cnd.date_in_slots,
                        loc_cnd.date_in_request                      
                    ])
                ]
            ),
            ("concrete_book_flow", "offer_genre", 1.2): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.genre_in_request,
                ]
            ),
            ("concrete_book_flow", "offer_fact", 1.2): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                            loc_cnd.about_book
                        ]
                    ),
                    cnd.any([loc_cnd.about_in_request, loc_cnd.movie_in_request]),
                ]
            ),
            ("concrete_book_flow", "ask_fav", 0.8): cnd.all(
                [
                    loc_cnd.check_unused(loc_rsp.WHAT_BOOK_IMPRESSED_MOST),
                    loc_cnd.check_flag("user_fav_book_visited"),
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                ]
            ),
            ("undetected_flow", "unrecognized_author", 0.7): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.check_author_regexp,
                    cnd.neg(loc_cnd.author_in_request)
                ]
            ),
            ("undetected_flow", "no_book_author", 0.7): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    cnd.neg(loc_cnd.bestbook_in_request),
                    loc_cnd.check_author_regexp,
                ]
            ),
            ("undetected_flow", "cannot_name", 0.7): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    cnd.any([int_cnd.is_no_vars, loc_cnd.doesnt_know]),
                    cnd.neg(loc_cnd.book_in_request),
                    cnd.neg(loc_cnd.author_in_request),
                    cnd.neg(loc_cnd.movie_in_request),
                ]
            ),            
            ("undetected_flow", "ask_to_repeat", 0.7): cnd.all([
                cnd.any(
                    [
                        loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                        loc_cnd.about_book
                    ]
                ),
                cnd.any([int_cnd.is_yes_vars, loc_cnd.no_entities]),
                cnd.neg(loc_cnd.book_in_request),
                cnd.neg(loc_cnd.author_in_request),
                cnd.neg(loc_cnd.movie_in_request),
            ])
        }
    },
    "global_flow": {
        "start": {
            RESPONSE: "",
            PROCESSING: {1: int_prs.set_can_continue(MUST_CONTINUE)},
            TRANSITIONS: {("books_general", "book_start", 2): cnd.true()},
        },
        "fallback": {
            RESPONSE: loc_rsp.append_unused(
                initial="Anyway, let's talk about something else! ",
                phrases=[
                    SWITCH_MOVIE_SKILL_PHRASE,
                    OFFER_TALK_ABOUT_SCIENCE,
                    "What's on your mind?",
                ],
            ),
            PROCESSING: {
                1: loc_prs.set_flag("book_skill_active"),
                2: int_prs.set_confidence(ZERO_CONFIDENCE),
                3: int_prs.set_can_continue(CAN_NOT_CONTINUE)
            },
        },
    },
    "books_general": {
        "book_start": {
            RESPONSE: loc_rsp.append_unused("", [loc_rsp.START_PHRASE]),
            PROCESSING: {
                1: int_prs.set_confidence(SUPER_CONFIDENCE),
                2: loc_prs.set_flag("book_skill_active", True),
                3: loc_prs.execute_response,
            },
            TRANSITIONS: {
                ("books_general", "dislikes_reading", 2): int_cnd.is_no_vars,
                ("books_general", "likes_reading", 2): cnd.true(),
            },
        },
        "book_restart": {
            RESPONSE: loc_rsp.append_unused(
                initial="Speaking of books, ", 
                phrases=loc_rsp.QUESTIONS_ABOUT_BOOKS,
                exit_on_exhaust=True
            ),
            PROCESSING: {
                1: int_prs.set_confidence(DEFAULT_CONFIDENCE),
                2: loc_prs.set_flag("book_skill_active", True),
                3: int_prs.set_can_continue(CAN_CONTINUE_SCENARIO)
            },
            TRANSITIONS: {("undetected_flow", "ask_to_repeat", 0.6): cnd.true()},
        },
        "dislikes_reading": {
            RESPONSE: "Why don't you love reading? Maybe you haven't found the right book?",
            TRANSITIONS: {lbl.to_fallback(2): cnd.true()},
        },
        "likes_reading": {
            RESPONSE: "I enjoy reading so much! Books help me understand humans much better. Why do you enjoy reading?",
            TRANSITIONS: {lbl.forward(2): cnd.true()},
        },
        "told_why": {
            RESPONSE: loc_rsp.append_unused(
                initial="That's great. Outside of a dog, a book is man's best friend. ",
                phrases=[loc_rsp.WHAT_BOOK_LAST_READ]
            ),
            TRANSITIONS: {("undetected_flow", "ask_to_repeat", 0.5): cnd.true()},
        },
    },
    "bot_fav_book": {
        "fav_name": {
            RESPONSE: loc_rsp.append_unused(
                initial="{fav_book_init} ",
                phrases=[loc_rsp.TELL_REQUEST]
            ),
            PROCESSING: {
                1: loc_prs.save_next_key(
                    fav_keys, loc_rsp.FAVOURITE_BOOK_ATTRS
                ),
                2: loc_prs.execute_response,
                3: int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                lbl.forward(2): int_cnd.is_yes_vars,
                ("bot_fav_book", "fav_denied"): cnd.true(),
            },
        },
        "fav_elaborate": {
            RESPONSE: loc_rsp.append_unused(
                initial="{cur_book_about} ",
                phrases=[loc_rsp.TELL_REQUEST2]
            ),
            PROCESSING: {
                1: loc_prs.execute_response,
                2: int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                lbl.forward(2): int_cnd.is_no_vars,
                ("concrete_book_flow", "offer_date", 1.8): cnd.true(),  #!!!
            },
        },
        "fav_denied": {
            RESPONSE: "OK, let me ask you something else then, alright?",
            PROCESSING: {
                1: loc_prs.set_flag("denied_favorite", True),
                2: int_prs.set_confidence(BIT_LOWER_CONFIDENCE)
            },
            TRANSITIONS: {
                lbl.to_fallback(2): int_cnd.is_no_vars,
                ("books_general", "book_restart", 1.8): int_cnd.is_yes_vars,
            },
        },
    },
    "concrete_book_flow": {
        LOCAL: {
            PROCESSING: {
                1: int_prs.set_confidence(DEFAULT_CONFIDENCE),
                2: int_prs.set_can_continue(CAN_CONTINUE_SCENARIO)
            }
        },
        "ask_fav": {
            RESPONSE: loc_rsp.append_unused(
                initial="Fabulous! And ",
                phrases=[loc_rsp.WHAT_BOOK_IMPRESSED_MOST]
            ),
            PROCESSING: {
                1: loc_prs.set_flag("user_fav_book_visited", True),
                2: loc_prs.execute_response
            },
            TRANSITIONS: {
                lbl.forward(2): cnd.all([loc_cnd.told_fav_book, loc_cnd.book_in_request]),
                ("undetected_flow", "ask_to_repeat", 0.5): cnd.any(
                    [
                        cnd.neg(loc_cnd.told_fav_book),
                        cnd.neg(loc_cnd.book_in_request)                        
                    ]
                ),
                lbl.to_fallback(0.4): cnd.true(),
            },
        },
        "user_fav": {
            RESPONSE: "Great choice! Would you like us to discuss it?",
            PROCESSING: {
                1: loc_prs.get_book,
                2: loc_prs.set_flag("user_fav_book_visited", True)
            },
            TRANSITIONS: {
                ("concrete_book_flow", "denied_information", 1.6): cnd.true()
            }
        },
        "ask_opinion": {
            RESPONSE: loc_rsp.append_unused(
                initial="",
                phrases=loc_rsp.OPINION_REQUEST_ON_BOOK_PHRASES
            ),
            TRANSITIONS: {
                ("concrete_book_flow", "user_liked"): loc_cnd.sentiment_detected(
                    "positive"
                ),
                ("concrete_book_flow", "user_disliked"): loc_cnd.sentiment_detected(
                    "negative"
                ),
            },
        },
        "user_liked": {
            RESPONSE: loc_rsp.append_question(
                initial="I see you love it."
                "It is so wonderful that you read the books you love. "
            ),
            PROCESSING: {
                1: int_prs.set_confidence(SUPER_CONFIDENCE)
            }
        },
        "user_disliked": {
            RESPONSE: loc_rsp.append_question(
                initial="It's OK. Maybe some other books will fit you better. "
            ),
            PROCESSING: {
                1: int_prs.set_confidence(SUPER_CONFIDENCE)
            }
        },
        "offer_best": {
            RESPONSE: loc_rsp.append_unused(
                initial="You have a great taste in books! I also adore books by {cur_book_author}, "
                "especially {cur_author_best}. ",
                phrases=loc_rsp.ASK_ABOUT_OFFERED_BOOK
            ),
            PROCESSING: {
                1: loc_prs.get_book,
                2: loc_prs.get_author,
                3: loc_prs.get_book_by_author,
                4: loc_prs.execute_response,
                5: int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: loc_cnd.has_read_transitions
        },
        "offer_genre": {
            RESPONSE: loc_rsp.ASK_GENRE_OF_BOOK,
            PROCESSING: {
                1: loc_prs.get_book,
                2: loc_prs.get_book_genre,
            },
            TRANSITIONS: {lbl.forward(2): cnd.true()},
        },
        "tell_genre": {
            RESPONSE: loc_rsp.append_question(
                initial="I believe that {cur_book_name} is {cur_genre}. "
            ),
            PROCESSING: {
                1: loc_prs.execute_response,
                2: int_prs.fill_responses_by_slots(),
            },
        },
        "offer_fact": {
            RESPONSE: "It's an amazing book! " + loc_rsp.OFFER_FACT_ABOUT_BOOK,
            PROCESSING: {
                1: loc_prs.get_book,
                2: loc_prs.about_bookreads,
                3: loc_prs.about_wiki,
                4: loc_prs.get_movie
            },
            TRANSITIONS: {
                ("tell_about", 2): loc_cnd.check_slot("cur_book_about"),
                ("tell_movie", 1.9): cnd.all(
                    [
                        loc_cnd.check_slot("cur_book_movie"),
                        loc_cnd.check_slot("cur_book_director")
                    ]
                ),
                ("undetected_flow", "change_branch", 1.8): cnd.true()
            },
        },
        "tell_about": {
            RESPONSE: loc_rsp.append_unused(
                initial="{cur_book_about} ",
                phrases=[loc_rsp.WHEN_IT_WAS_PUBLISHED]
            ),
            PROCESSING: {
                1: loc_prs.get_book_year,
                2: loc_prs.execute_response,
                3: int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {
                ("concrete_book_flow", "tell_date", 2): cnd.all(
                    [int_cnd.is_yes_vars, loc_cnd.check_slot("cur_book_ago")]
                ),
                ("concrete_book_flow", "denied_information", 1.9): int_cnd.is_no_vars,
                ("global_flow", "fallback", 0.5): cnd.true()
            }
        },
        "tell_movie": {
            RESPONSE: "I enjoyed watching the film {cur_book_movie} based on this book, directed by {cur_book_director}. ",
            PROCESSING: {1: loc_prs.get_movie, 2: int_prs.fill_responses_by_slots()},
        },
        "offer_date": {
            RESPONSE: loc_rsp.append_unused(
                initial="I've read it. It's an amazing book! ",
                phrases=[loc_rsp.WHEN_IT_WAS_PUBLISHED]
            ),
            PROCESSING: {
                1: loc_prs.get_book, 
                2: loc_prs.get_book_year,
                3: loc_prs.execute_response
            },
            TRANSITIONS: {
                ("concrete_book_flow", "tell_date", 2): cnd.all(
                    [int_cnd.is_yes_vars, loc_cnd.check_slot("cur_book_ago")]
                ),
                ("concrete_book_flow", "denied_information", 1.9): int_cnd.is_no_vars,
                ("global_flow", "fallback", 0.5): cnd.true()
            }
        },
        "tell_date": {
            RESPONSE: "{cur_book_ago} ago! " + random.choice(loc_rsp.DID_NOT_EXIST),
            PROCESSING: {
                1: loc_prs.get_book_year,
                2: loc_prs.execute_response,
                3: int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                ("concrete_book_flow", "offer_genre", 2): loc_cnd.check_slot("cur_book_plain"),
                ("undetected_flow", "change_branch", 1.9): cnd.true()
            }
        },
        "denied_information": {
            RESPONSE: loc_rsp.append_question(
                initial="As you wish. "
            ),
        },
    },
    "genre_flow": {
        LOCAL: {
            PROCESSING: {
                1: int_prs.set_confidence(DEFAULT_CONFIDENCE)
            }
        },
        "tell_phrase": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                    1: loc_prs.set_flag("user_fav_genre_visited", True),
                    2: loc_prs.get_genre_regexp,
                    3: int_prs.set_can_continue(MUST_CONTINUE)
                },
            TRANSITIONS: {
                ("return_genrebook", 2): loc_cnd.genrebook_in_slots,
                ("concrete_book_flow", "denied_information", 1): int_cnd.is_no_vars
            },
        },
        "return_genrebook": {
            RESPONSE: "Amazing! I hear, {cur_book_name} by {cur_book_author} is quite good." + loc_rsp.HAVE_YOU_READ_BOOK,
            PROCESSING: {
                1: loc_prs.get_genre_regexp,  # extracts new genre or leaves previous
                2: loc_prs.get_book_by_genre,  # extracts the book
                3: int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: loc_cnd.has_read_transitions,
        },
        "not_read_genrebook": {
            RESPONSE: loc_rsp.append_unused(
                initial=random.choice(loc_rsp.READ_BOOK_ADVICES) + " ",
                phrases=[loc_rsp.TELL_REQUEST]   
            ),
            PROCESSING: {
                1: loc_prs.execute_response
            },
            TRANSITIONS: {
                lbl.forward(): cnd.all(
                    [int_cnd.is_yes_vars, loc_cnd.about_in_slots]
                ),
                ("books_general", "book_restart"): int_cnd.is_no_vars,
                lbl.to_fallback(0.4): cnd.true(),
            },
        },
        "genrebook_info": {
            RESPONSE: loc_rsp.append_question(
                initial="{cur_book_about} Anyway, "
            ),
            PROCESSING: {
                1: loc_prs.about_bookreads,
                2: loc_prs.execute_response,
                3: int_prs.fill_responses_by_slots(),
            },
        },
        "bot_fav": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                1: int_prs.save_slots_to_ctx(
                    {
                        "cur_genre",
                        random.choice(list(loc_rsp.GENRE_PHRASES.keys()))
                    }
                )
            },
        },
    },
    "bible_flow": {
        "bible_start": {
            RESPONSE: "I know that Bible is one of the most widespread books on Earth. "
            "It is the foundation stone of Christianity. Have you read the whole Bible?",
            TRANSITIONS: {lbl.forward(2): cnd.true()},
        },
        "bible_elaborate": {
            RESPONSE: loc_rsp.append_unused(
                initial="Unfortunately, as a socialbot, I don't have an immortal soul, "
                "so I don't think I will ever go to Heaven. That's why I don't know much about religion. " 
                "Apart from the Bible, ",
                phrases=loc_rsp.QUESTIONS_ABOUT_BOOKS
            ),
        },
    },
    "undetected_flow": {
        LOCAL: {
            PROCESSING: {
                1: int_prs.set_confidence(BIT_LOWER_CONFIDENCE)
            },
        },
        "ask_to_repeat": {
            RESPONSE: "Oops, I'm afraid I couldn't make out what you've just said. Can you, please, repeat?",
            TRANSITIONS: {
                lbl.forward(1): cnd.true()
            }
        },
        "change_branch": {
            RESPONSE: loc_rsp.append_question(
                initial=""
            ),
        },        
        "cannot_name": {
            RESPONSE: loc_rsp.BOOK_ANY_PHRASE
        },
        "ask_question": {
            RESPONSE: loc_rsp.append_question(
                initial="Never heard about it. I will check it out later. "
            ),
        },
        "unrecognized_author": {
            RESPONSE: loc_rsp.append_question(
                initial="Strange, I've never heard about this author. I'll surely check out his works sometime. "
            ),
        },
        "no_book_author": {
            RESPONSE: loc_rsp.append_question(
                initial="{cur_book_author} is a wonderful writer! By the way, "
            ),
            PROCESSING: {
                1: loc_prs.get_author_regexp,
                2: loc_prs.execute_response,
                3: int_prs.fill_responses_by_slots()
            }
        },
    },
}


actor = Actor(
    flows,
    start_label=("global_flow", "start"),
    fallback_label=("global_flow", "fallback"),
)
logger.info(f"Actor created successfully")
