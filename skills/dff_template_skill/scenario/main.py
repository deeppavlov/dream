"""
append_question is used to change the current flow, like booklink2reply
append_unused is used to add questions that lead to the concrete_book_flow
"""
import logging
import re
import sentry_sdk
from os import getenv
import random

from dff.core.keywords import PROCESSING, TRANSITIONS, GLOBAL, RESPONSE, LOCAL
from dff.core import Actor
import dff.conditions as cnd
import dff.labels as lbl
import dff.responses as rsp

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp
import common.constants as common_constants
import common.movies as common_movies

from common.movies import SWITCH_MOVIE_SKILL_PHRASE
from common.science import OFFER_TALK_ABOUT_SCIENCE
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
from scenario.processing import CACHE
import scenario.response as loc_rsp
from tools.wiki import (
    get_name,
    what_is_book_about,
    get_published_year,
    best_plain_book_by_author,
    genre_of_book
)

fav_keys = loc_rsp.FAVOURITE_BOOK_ATTRS.keys()
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
            ("global_flow", "fallback"): loc_cnd.exit_skill,
            ("books_general", "dislikes_reading"): loc_cnd.dislikes_reading,
            ("undetected_flow", "cannot_name", 1.6): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    cnd.any(
                        [
                            loc_cnd.doesnt_know,
                            loc_cnd.is_no
                        ]
                    )
                ]
            ),
            ("books_general", "book_start"): cnd.all(
                [
                    loc_cnd.skill_proposed, 
                    cnd.neg(loc_cnd.check_flag("book_skill_active")),
                    cnd.neg(loc_cnd.check_flag("book_start_visited", False))
                ]
            ),
            ("books_general", "book_restart"): cnd.all(
                [
                    loc_cnd.skill_proposed, 
                    cnd.neg(loc_cnd.check_flag("book_skill_active")),
                    loc_cnd.check_flag("book_start_visited", False)
                ]
            ),
            ("bot_fav_book", "fav_start", 0.9): cnd.all(
                [
                    loc_cnd.check_unused(loc_rsp.FAVOURITE_BOOK_PHRASES[0]),
                    cnd.neg(loc_cnd.check_flag("fav_book_start_visited", False)),
                    cnd.neg(loc_cnd.check_flag("denied_favorite"))
                ]
            ),
            ("bot_fav_book", "fav_restart", 0.8): cnd.all(
                [
                    loc_cnd.check_unused(loc_rsp.FAVOURITE_BOOK_PHRASES[1:]),
                    cnd.neg(loc_cnd.check_flag("fav_book_restart_visited", False)),
                    loc_cnd.check_flag("fav_book_start_visited", False),
                    cnd.neg(loc_cnd.check_flag("denied_favorite"))
                ]
            ),
            ("bot_fav_book", "fav_name"): loc_cnd.asked_fav_book,
            ("bible_flow", "bible_start", 0.6): cnd.all(
                [
                    loc_cnd.asked_about_bible,
                    cnd.neg(loc_cnd.check_flag("bible_start_visited", False)),
                ]
            ),
            ("bible_flow", "bible_elaborate", 0.6): cnd.all(
                [
                    loc_cnd.asked_about_bible,
                ]
            ),
            ("concrete_book_flow", "ask_fav", 1.4): cnd.all(
                [
                    cnd.neg(loc_cnd.check_flag("user_fav_book_visited", False)),
                ]
            ),
            ("concrete_book_flow", "user_fav", 1.2): cnd.all(
                [
                    loc_cnd.told_fav_book,
                    cnd.neg(loc_cnd.check_flag("user_fav_book_visited", False)),
                ]
            ),
            ("genre_flow", "tell_phrase", 0.8): cnd.any(
                [
                    loc_cnd.adapter(loc_prs.get_genre_regexp)
                ]
            ),
            ("genre_flow", "ask_fav", 1.4): cnd.all(
                [
                    loc_cnd.check_unused(loc_rsp.WHAT_GENRE_FAV),
                    cnd.neg(loc_cnd.check_flag("user_fav_genre_visited", False)),
                ]
            ),       
            ("genre_flow", "offer_book", 0.8): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.told_fav_genre,
                            loc_cnd.asked_opinion_genre,
                            loc_cnd.is_last_used_phrase(loc_rsp.WHAT_GENRE_FAV)
                        ]
                    ),
                    loc_cnd.adapter(loc_prs.get_genre_regexp),
                    cnd.neg(loc_cnd.check_flag("user_fav_genre_visited", False)),
                ]
            ),
            ("genre_flow", "return_genrebook", 1.2): cnd.all(
                [
                    loc_cnd.asked_to_offer_book,
                    loc_cnd.adapter(loc_prs.get_genre_regexp)
                ]
            ),
            ("concrete_book_flow", "user_fav", 0.8): loc_cnd.told_fav_book,
            ("concrete_book_flow", "tell_about", 0.8): cnd.any([
                # if pertains to current book
                cnd.all(
                    [
                        loc_cnd.asked_book_content,
                        loc_cnd.adapter(loc_prs.get_slot("cur_book_name")),
                        loc_cnd.adapter(loc_prs.about_bookreads)
                    ]
                ),
                cnd.all(
                    [
                        loc_cnd.asked_book_content,
                        loc_cnd.adapter(loc_prs.get_slot("cur_book_plain")),
                        loc_cnd.adapter(loc_prs.about_wiki),

                    ]
                ),
                # if new book was mentioned
                cnd.all(
                    [
                        loc_cnd.asked_book_content,
                        loc_cnd.adapter(loc_prs.get_book),
                        loc_cnd.adapter(lambda ctx, actor: what_is_book_about(
                            loc_prs.get_book(ctx, actor)[1]
                        ))
                    ]
                )
            ]),
            ("concrete_book_flow", "offer_best", 0.8):  cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    cnd.all([
                        loc_cnd.adapter(loc_prs.get_author),
                        loc_cnd.adapter(lambda ctx, actor: best_plain_book_by_author(
                            loc_prs.get_author(ctx, actor)[1]
                        ))
                    ])
                ]
            ),
            ("concrete_book_flow", "offer_date", 1.2): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.adapter(loc_prs.get_book),
                    loc_cnd.adapter(lambda ctx, actor: get_published_year(
                        loc_prs.get_book(ctx, actor)[1]
                    ))
                ]
            ),
            ("concrete_book_flow", "tell_date"): cnd.all(
                [
                    loc_cnd.asked_book_date,
                    cnd.any([
                        # if pertains to current book
                        loc_cnd.adapter(loc_prs.get_slot("cur_book_ago")),
                        # if new book was mentioned
                        cnd.all([
                            loc_cnd.adapter(loc_prs.get_book),
                            loc_cnd.adapter(lambda ctx, actor: get_published_year(
                                loc_prs.get_book(ctx, actor)[1]
                            ))                            
                        ])
                    ])
                    
                ]
            ),
            ("concrete_book_flow", "offer_genre", 2): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.adapter(loc_prs.get_book),
                    loc_cnd.adapter(lambda ctx, actor: genre_of_book(
                        loc_prs.get_book(ctx, actor)[1]
                    ))
                ]
            ),
            ("concrete_book_flow", "offer_fact", 1.2): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.adapter(loc_prs.get_book),
                    cnd.any([
                        loc_cnd.adapter(lambda ctx, actor: what_is_book_about(
                            loc_prs.get_book(ctx, actor)[1]
                        )),
                        loc_cnd.adapter(lambda ctx, actor: get_name(ctx, "movie"))
                    ])
                ]                
            )
        }
    },
    "global_flow": {
        "start": {
            RESPONSE: ""
        },
        "fallback": {
            RESPONSE: "Anyway, let's talk about something else!",
            PROCESSING: {
                "unset_active": loc_prs.set_flag("book_skill_active", False),
                "unset_confidence": int_prs.set_confidence(ZERO_CONFIDENCE),
                "append_switch": loc_prs.append_unused(
                    [
                        SWITCH_MOVIE_SKILL_PHRASE,
                        OFFER_TALK_ABOUT_SCIENCE,
                        "What's on your mind?"
                    ]
                )                
            }
        }
    },
    "books_general": {
        "book_start": {
            RESPONSE: loc_rsp.START_PHRASE,
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_active": loc_prs.set_flag("book_skill_active", True),
                "use_phrase": loc_prs.add_to_used(loc_rsp.START_PHRASE)                
            },
            TRANSITIONS: {
                ("books_general","dislikes_reading"): int_cnd.is_no_vars,
                ("books_general", "likes_reading"): int_cnd.is_yes_vars,
                lbl.to_fallback(): cnd.true()
            }
        },
        "book_restart": {
            RESPONSE: [
                loc_rsp.get_unused(loc_rsp.QUESTIONS_ABOUT_BOOKS)
            ],
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_active": loc_prs.set_flag("book_skill_active", True),                    
            },
            TRANSITIONS: {
                ("undetected_flow", "ask_to_repeat"): cnd.true()
            }
        },
        "dislikes_reading": {
            RESPONSE: "Why don't you love reading? Maybe you haven't found the right book?",
            TRANSITIONS: {
                lbl.to_fallback(0.5): cnd.true()
            }
        },
        "likes_reading": {
            RESPONSE: "Why do you like reading?",
            TRANSITIONS: {
                lbl.forward(2): cnd.true()
            }
        },
        "told_why": {
            RESPONSE: "That's great. Outside of a dog, a book is man's best friend.",
            PROCESSING: {
                "append_question": loc_prs.append_unused([loc_rsp.WHAT_BOOK_LAST_READ])
            },
            TRANSITIONS: {
                ("undetected_flow", "ask_to_repeat", 0.5): cnd.true() 
            }
        }
    },
    "bot_fav_book": {
        "fav_start": {
            RESPONSE: loc_rsp.FAVOURITE_BOOK_PHRASES[0],
            TRANSITIONS: {
                ("bot_fav_book", "name_fav"): int_cnd.is_yes_vars,
                ("bot_fav_book", "fav_denied"): cnd.true()
            }
        },
        "fav_restart": {
            RESPONSE: "",
            PROCESSING: {
                1: loc_prs.append_unused(loc_rsp.FAVOURITE_BOOK_PHRASES[1:], exit_on_exhaust=True)
            },
            TRANSITIONS: {
                ("bot_fav_book", "fav_name"): int_cnd.is_yes_vars,
                ("bot_fav_book", "fav_denied"): cnd.true()
            }
        },
        "fav_name": {
            RESPONSE: "{fav_book_init}",
            PROCESSING: {
                "set_slots": loc_prs.save_random_subdict(fav_keys, loc_rsp.FAVOURITE_BOOK_ATTRS),
                "fill_slots": int_prs.fill_responses_by_slots()                
            },
            TRANSITIONS: {
                lbl.forward(2): int_cnd.is_yes_vars,
                ("bot_fav_book", "fav_denied"): cnd.true()
            }
        },
        "fav_elaborate": {
            RESPONSE: "{cur_book_about}",
            PROCESSING: {
                1: loc_prs.append_unused([loc_rsp.TELL_REQUEST2]),
                2: int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {
                lbl.forward(1.2): int_cnd.is_no_vars,
                ("concrete_book_flow", "offer_date"): cnd.true()  #!!!
            }
        },
        "fav_denied": {
            RESPONSE: "OK, let me ask you something else then, alright?",
            PROCESSING: {
                "set_denied": loc_prs.set_flag("denied_favorite", True),
            },
            TRANSITIONS: {
                lbl.to_fallback(2): int_cnd.is_no_vars,
                ("concrete_book_flow", "denied_information"): int_cnd.is_yes_vars,
                ("concrete_book_flow", "ask_fav"): cnd.neg(loc_cnd.check_flag("user_fav_book_visited", False)),
                ("genre_flow", "ask_fav"): cnd.neg(loc_cnd.check_flag("user_fav_genre_visited", False)),
                ("books_general", "book_restart", 1.2): cnd.true(),
            }
        },
    },
    "concrete_book_flow": {
        "ask_fav": {
            RESPONSE: "Fabulous! And ",
            PROCESSING: {
                1: loc_prs.append_unused([loc_rsp.WHAT_BOOK_IMPRESSED_MOST])
            },
            TRANSITIONS: {
                lbl.forward(2): loc_cnd.told_fav_book,
                ("undetected_flow", "ask_to_repeat", 0.5): cnd.neg(loc_cnd.told_fav_book),
                lbl.to_fallback(0.4): cnd.true()
            }
        },
        "user_fav": {
            RESPONSE: "So, ",
            PROCESSING: {
                1: loc_prs.set_flag("user_fav_visited", True),
                2: loc_prs.append_unused(loc_rsp.WHAT_BOOK_IMPRESSED_MOST)
            }
        },
        "ask_opinion": {
            RESPONSE: loc_rsp.get_unused([loc_rsp.OPINION_REQUEST_ON_BOOK_PHRASES]),
            TRANSITIONS: {
                ("concrete_book_flow", "user_liked"): loc_cnd.sentiment_detected("positive"),
                ("concrete_book_flow", "user_disliked"): loc_cnd.sentiment_detected("negative"),
            }
        },
        "user_liked": {
            RESPONSE: f"I see you love it."
            f"It is so wonderful that you read the books you love.",
            PROCESSING: {
                1: loc_prs.append_question
            },
        },
        "user_disliked": {
            RESPONSE: "It's OK. Maybe some other books will fit you better. ",
            PROCESSING: {
                1: loc_prs.append_question
            }
        },
        "offer_best": {
            RESPONSE: "You have a great taste in books! I also adore books by {cur_book_author}, especially {cur_author_best}. ",
            PROCESSING: {
                1: loc_prs.adapter(loc_prs.get_book),
                2: loc_prs.adapter(loc_prs.get_author),
                3: loc_prs.adapter(loc_prs.get_book_by_author),
                4: int_prs.fill_responses_by_slots()
            },
        },        
        "offer_genre": {
            RESPONSE: loc_rsp.ASK_GENRE_OF_BOOK,
            PROCESSING: {
                1: loc_prs.adapter(loc_prs.get_book),
                2: loc_prs.adapter(loc_prs.get_book_genre)
            },
            TRANSITIONS: {
                lbl.forward(2): cnd.true()
            }
        },
        "tell_genre": {
            RESPONSE: "I believe that {cur_book_name} is {cur_genre}.",
            PROCESSING: {
                1: loc_prs.append_unused(loc_rsp.UNCERTAINTY),
                2: int_prs.fill_responses_by_slots()
            }
        },        
        "offer_fact": {
            RESPONSE: "It's an amazing book! ",
            PROCESSING: {
                1: loc_prs.adapter(loc_prs.get_book),
                2: loc_prs.append_unused(loc_rsp.OFFER_FACT_ABOUT_BOOK)
            },
            TRANSITIONS: {
                "tell_about": cnd.any(
                    [
                        loc_cnd.adapter(loc_prs.about_bookreads),
                        loc_cnd.adapter(loc_prs.about_wiki)
                    ]
                ),
                "tell_movie": loc_cnd.adapter(loc_prs.get_movie),
            }
        },
        "tell_about": {
            RESPONSE: "{cur_book_about}",
            PROCESSING: {
                1: int_prs.fill_responses_by_slots()
            }
        },
        "tell_movie": {
            RESPONSE: "I enjoyed watching the film {cur_book_movie} based on this book, directed by {cur_book_director}. ",
            PROCESSING: {
                1: loc_prs.get_movie,
                2: int_prs.fill_responses_by_slots()
            }
        },
        "offer_date": {
            RESPONSE: "I've read it. It's an amazing book! Would you like to know when it was first published?",
            PROCESSING: {
                1: loc_prs.adapter(loc_prs.get_book),
                2: loc_prs.adapter(loc_prs.get_book_year)
            },
            TRANSITIONS: {
                ("concrete_book_flow", "tell_date", 2): cnd.all(
                    [
                        loc_cnd.is_yes,
                        loc_cnd.adapter(loc_prs.get_slot("cur_book_ago"))
                    ]
                ),
                ("concrete_book_flow", "denied_information"): int_cnd.is_no_vars,
                lbl.to_fallback(0.4): cnd.true(),
            }
        },
        "tell_date": {
            RESPONSE: "{cur_book_ago} ago!",
            PROCESSING: {
                1: loc_prs.adapter(loc_prs.get_book_year),
                2: loc_prs.append_unused(loc_rsp.DID_NOT_EXIST),
                3: int_prs.fill_responses_by_slots()
            }
        },
        "denied_information": {
            RESPONSE: "As you wish. ", 
            PROCESSING: {
                1: loc_prs.append_question
            }
        },
    },
    "genre_flow": {
        "ask_fav": {
            RESPONSE: loc_rsp.WHAT_GENRE_FAV,
            PROCESSING: {
                1: loc_prs.set_flag("user_fav_genre_visited", True)
            },
            TRANSITIONS: {
                ("genre_flow", "return_genrebook", 2): cnd.all([
                    loc_cnd.adapter(loc_prs.get_genre_regexp),
                    cnd.any(
                        [
                            loc_cnd.told_fav_genre,
                            int_cnd.is_opinion_expression
                        ]
                    )
                ]),
                ("undetected_flow", "ask_to_repeat", 0.5): cnd.neg(loc_cnd.told_fav_genre),
                lbl.to_fallback(0.4): cnd.true()
            }
        },
        "tell_phrase": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                1: loc_prs.get_genre_regexp
            },
            TRANSITIONS: {
                lbl.forward(2): cnd.any([
                    loc_cnd.adapter(loc_prs.get_slot("cur_genre")),
                    loc_cnd.adapter(loc_prs.get_genre_regexp),
                ])
            }
        },
        "offer_book": {
            RESPONSE: "Personally, I like all kinds of literature. By the way, may I recommend you a book from this genre?",
            PROCESSING: {
                1: loc_prs.set_flag("user_fav_genre_visited", True),
                2: loc_prs.get_genre_regexp,
            },
            TRANSITIONS: {
                ("genre_flow", "return_genrebook", 2): cnd.all(
                    [
                        int_cnd.is_yes_vars, # if user agreed
                        loc_cnd.adapter(loc_prs.get_book_by_genre) # and we can extract the book from the current slots
                    ]
                )
            }
        },
        "return_genrebook": {
            RESPONSE: "Amazing! I hear, {cur_book_name} by {cur_book_author} is quite good.",
            PROCESSING: {
                # the user only enters the node if the genre can be or has been extracted
                1: loc_prs.append_unused([loc_rsp.HAVE_YOU_READ_BOOK]),
                2: loc_prs.adapter(loc_prs.get_genre_regexp), # extracts new genre or leaves previous
                3: loc_prs.adapter(loc_prs.get_book_by_genre), # extracts the book
                4: int_prs.fill_responses_by_slots()
            },
            TRANSITIONS: {
                ("concrete_book_flow", "ask_opinion"): int_cnd.is_yes_vars,
                lbl.forward(): int_cnd.is_no_vars
            }
        },
        "not_read_genrebook": {
            RESPONSE: "",
            PROCESSING: {
                1: loc_prs.append_unused(loc_rsp.READ_BOOK_ADVICES),
                2: loc_prs.append_unused([loc_rsp.TELL_REQUEST])
            },
            TRANSITIONS: {
                lbl.forward(): cnd.all(
                    [
                        int_cnd.is_yes_vars,
                        loc_cnd.adapter(loc_prs.get_slot("cur_book_about"))
                    ]
                ),
                ("books_general", "books_restart"): int_cnd.is_no_vars,
                lbl.to_fallback(0.4): cnd.true()
            }
        },
        "genrebook_info": {
            RESPONSE: "{cur_book_about} Anyway, ",
            PROCESSING: {
                1: int_prs.fill_responses_by_slots(),
                # 2: loc_prs.append_question
            }
        },
        "bot_fav": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                1: loc_prs.adapter(
                    loc_prs.save_to_slots("cur_genre")(
                        lambda ctx, actor: random.choice(list(loc_rsp.GENRE_PHRASES.keys()))
                    )
                )
            }
        }
    },
    "bible_flow": {
        "bible_start": {
            RESPONSE: "I know that Bible is one of the most widespread books on Earth. "
            "It is the foundation stone of Christianity. Have you read the whole Bible?",
            TRANSITIONS: {
                lbl.forward(2): int_cnd.is_yes_vars,
                "bible_end": cnd.true()
            }
        },
        "bible_elaborate": {
            RESPONSE: "Unfortunately, as a socialbot, I don't have an immortal soul,"
            "so I don't think I will ever go to Heaven. That's why I don't know much about religion.",
            TRANSITIONS: {
                lbl.forward(2): cnd.true()
            }
        },
        "bible_end": {
            RESPONSE: "OK, apart from the Bible,",
            PROCESSING: {
                "append_question ": loc_prs.append_unused(loc_rsp.QUESTIONS_ABOUT_BOOKS)
            }
        }
    },
    "undetected_flow": {
        LOCAL: {
            TRANSITIONS: {
                "cannot_name": cnd.any([
                    loc_cnd.doesnt_know,
                    loc_cnd.is_no
                ]),
                "unrecognized_author": cnd.all(
                    [
                        loc_cnd.adapter(loc_prs.get_author_regexp),
                        cnd.neg(loc_cnd.adapter(loc_prs.get_author))
                    ]
                ),
                "no_book_author": cnd.all(
                    [
                        loc_cnd.adapter(loc_prs.get_author),
                        cnd.neg(loc_cnd.adapter(loc_prs.get_book_by_author))
                    ]
                ),
                "ask_question": cnd.true(),
            }
        },
        "ask_to_repeat": {
            RESPONSE: "Oops, I'm afraid I couldn't make out what you've just said. Can you, please, repeat?",
        },
        "cannot_name": {
            RESPONSE: loc_rsp.BOOK_ANY_PHRASE,
            PROCESSING: {
                1: loc_prs.append_question
            }
        },
        "ask_question": {
            RESPONSE: "Never heard about it. I will check it out later. ",
            PROCESSING: {
                1: loc_prs.append_question
            },
        },
        "unrecognized_author": {
            RESPONSE: "Strange, I've never heard about this author. I'll surely check out his works sometime. ",
            PROCESSING: {
                1: loc_prs.append_question
            }
        },
        "no_book_author": {
            RESPONSE: "{cur_book_author} is a wonderful writer! By the way, ",
            PROCESSING: {
                1: loc_prs.append_question
            }
        }
    }
}


actor = Actor(flows, start_node_label=("global_flow", "start"), fallback_node_label=("global_flow", "fallback"))
CACHE.update_actor_handlers(actor)
