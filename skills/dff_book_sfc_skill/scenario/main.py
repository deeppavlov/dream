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
from df_engine.core.keywords import PROCESSING, TRANSITIONS, GLOBAL, RESPONSE, LOCAL, MISC
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl
import scenario.sf_conditions as dm_cnd

import common.dff.integration.condition as int_cnd
import common.dff.integration.processing as int_prs
import common.dff.integration.response as int_rsp

import common.constants as common_constants

from common.movies import SWITCH_MOVIE_SKILL_PHRASE
from common.science import OFFER_TALK_ABOUT_SCIENCE
import scenario.condition as loc_cnd
import scenario.processing as loc_prs
import scenario.response as loc_rsp


fav_keys = list(loc_rsp.FAVOURITE_BOOK_ATTRS.keys())
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
            ("books_general", "dislikes_reading", 0.5): loc_cnd.dislikes_reading,
            ("books_general", "book_start", 5): cnd.all(
                [
                    loc_cnd.is_proposed_skill,
                    cnd.neg(loc_cnd.check_flag("book_skill_active")),
                    cnd.neg(loc_cnd.check_flag("book_start_visited")),
                ]
            ),
            # ("books_general", "book_restart"): cnd.all(
            #     [
            #         loc_cnd.is_proposed_skill,
            #         cnd.neg(loc_cnd.check_flag("book_skill_active")),
            #         loc_cnd.check_flag("book_start_visited"),
            #     ]
            # ),
            ("bot_fav_book", "fav_name", 1.8): cnd.any(  # было 4
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.FAVOURITE_BOOK_PHRASES),
                    loc_cnd.asked_fav_book,
                ]
            ),
            ("bot_fav_book", "fav_denied", 2): cnd.all(
                [loc_cnd.is_last_used_phrase(loc_rsp.FAVOURITE_BOOK_PHRASES), int_cnd.is_no_vars]
            ),
            ("bible_flow", "bible_start", 1.8): cnd.all(
                [
                    loc_cnd.asked_about_bible,
                    cnd.neg(loc_cnd.check_flag("bible_start_visited")),
                ]
            ),
            ("bible_flow", "bible_elaborate", 1.8): cnd.all(
                [loc_cnd.asked_about_bible, loc_cnd.check_flag("bible_start_visited")]
            ),
            ("genre_flow", "tell_phrase", 1): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.told_fav_genre,
                            loc_cnd.asked_opinion_genre,
                        ]
                    ),
                    loc_cnd.check_genre_regexp,
                ]
            ),
            ("genre_flow", "return_genrebook", 1.2): loc_cnd.genrebook_request_detected,
            ("concrete_book_flow", "user_fav", 0.8): cnd.all([loc_cnd.told_fav_book, loc_cnd.book_in_request]),
            ("concrete_book_flow", "denied_information", 3): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase([loc_rsp.TELL_REQUEST, loc_rsp.TELL_REQUEST2]),
                            loc_cnd.asked_book_content,
                        ]
                    ),
                    int_cnd.is_no_vars,
                ]
            ),
            ("concrete_book_flow", "tell_about", 1.2): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase([loc_rsp.TELL_REQUEST, loc_rsp.TELL_REQUEST2]),
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
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase(loc_rsp.WHEN_IT_WAS_PUBLISHED),
                            loc_cnd.asked_book_date,
                        ]
                    ),
                    cnd.any([loc_cnd.date_in_slots, loc_cnd.date_in_request]),
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
                            loc_cnd.about_book,
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
            ("undetected_flow", "unrecognized_author", 0.8): cnd.all(
                [
                    loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                    loc_cnd.check_author_regexp,
                    cnd.neg(loc_cnd.author_in_request),
                ]
            ),
            ("undetected_flow", "no_book_author", 0.8): cnd.all(
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
            ("undetected_flow", "quit", 0.7): cnd.all(
                [
                    cnd.any(
                        [
                            loc_cnd.is_last_used_phrase(loc_rsp.ALL_QUESTIONS_ABOUT_BOOK),
                            loc_cnd.about_book,
                        ]
                    ),
                    cnd.any([int_cnd.is_yes_vars, loc_cnd.no_entities]),
                    cnd.neg(loc_cnd.book_in_request),
                    cnd.neg(loc_cnd.author_in_request),
                    cnd.neg(loc_cnd.movie_in_request),
                ]
            ),
        }
    },
    "global_flow": {
        "start": {
            RESPONSE: "",
            PROCESSING: {"set_can_continue": int_prs.set_can_continue(MUST_CONTINUE)},
            TRANSITIONS: {("books_general", "book_start"): cnd.true()},
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
                "set_flag": loc_prs.set_flag("book_skill_active"),
                "set_confidence": int_prs.set_confidence(ZERO_CONFIDENCE),
                "set_can_continue": int_prs.set_can_continue(CAN_NOT_CONTINUE),
            },
            TRANSITIONS: {},
        },
    },
    "books_general": {
        "book_start": {
            RESPONSE: loc_rsp.append_unused("", [loc_rsp.START_PHRASE]),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE),
                "set_flag": loc_prs.set_flag("book_skill_active", True),
                "execute_response": loc_prs.execute_response,
            },
            TRANSITIONS: {
                "change_subject": cnd.any(
                    [
                        dm_cnd.is_sf("Sustain.Continue.Prolong.Extend"),
                        dm_cnd.is_sf("Sustain.Continue.Prolong.Enhance"),
                        dm_cnd.is_sf("Sustain.Continue.Prolong.Elaborate")
                    ]
                ),
                "bot_answer": cnd.any(
                    [
                        dm_cnd.is_sf("React.Rejoinder.Support.Track.Clarify"),
                        dm_cnd.is_sf("React.Respond.Support.Track.Check"),
                        dm_cnd.is_sf("React.Rejoinder.Support.Challenge.Rebound")
                    ]
                ),
                "dislikes_reading": cnd.any(
                    [
                        dm_cnd.is_sf("React.Respond.Confront.Reply.Disagree"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Disavow"),
                        dm_cnd.is_sf("React.Rejoinder.Confront.Challenge.Counter"),
                        int_cnd.is_no_vars
                    ]
                ),
                "likes_reading": cnd.true(),
            },
            MISC: {"speech_functions": ["Open.Demand.Fact"]},
        },
        "book_restart": {
            RESPONSE: loc_rsp.append_unused(
                initial="Speaking of books, ",
                phrases=loc_rsp.QUESTIONS_ABOUT_BOOKS,
                exit_on_exhaust=True,
            ),
            PROCESSING: {
                "set_confidence": int_prs.set_confidence(DEFAULT_CONFIDENCE),
                "set_flag": loc_prs.set_flag("book_skill_active", True),
                "set_can_continue": int_prs.set_can_continue(CAN_CONTINUE_SCENARIO),
            },
            TRANSITIONS: {("undetected_flow", "quit"): cnd.true()},
        },
        "dislikes_reading": {
            RESPONSE: "Why don't you love reading? Maybe you haven't found the right book?",
            TRANSITIONS: {
                "right_book_reassure": cnd.any(
                    [
                        dm_cnd.is_sf("React.Respond.Support.Reply.Affirm"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Agree"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Acknowledge"),
                        int_cnd.is_yes_vars
                    ]
                ),
                "ask_not_like": cnd.any(
                    [
                        dm_cnd.is_sf("React.Respond.Confront.Reply.Disagree"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Disavow"),
                        dm_cnd.is_sf("React.Rejoinder.Confront.Challenge.Counter"),
                        int_cnd.is_no_vars
                    ]
                ),
                "change_subject": cnd.true()
            },
            MISC: {
                "speech_functions": ["React.Rejoinder.Support.Track.Clarify"],
            },
        },
        "likes_reading": {
            RESPONSE: "I enjoy reading so much! Books help me understand humans much better. "
            "Why do you enjoy reading?",
            TRANSITIONS: {
                "bot_answer": dm_cnd.is_sf("React.Rejoinder.Support.Track.Clarify"),
                "dislikes_reading": cnd.any(
                    [
                        dm_cnd.is_sf("React.Respond.Confront.Reply.Disagree"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Disavow"),
                        dm_cnd.is_sf("React.Rejoinder.Confront.Challenge.Counter"),
                        int_cnd.is_no_vars
                    ]
                ),
                "told_why": dm_cnd.is_sf("React.Rejoinder.Support.Response.Resolve"),
                "change_subject": cnd.true()
            },
            MISC: {
                "speech_functions": ["React.Rejoinder.Support.Track.Clarify"]
            }
        },
        "told_why": {
            RESPONSE: loc_rsp.append_unused(
                initial="That's great. Outside of a dog, a book is man's best friend. ",
                phrases=[loc_rsp.WHAT_BOOK_LAST_READ],
            ),
            TRANSITIONS: {
                ("bot_fav_book", "fav_name"): cnd.true()
            },
            MISC: {"speech_functions": ["React.Rejoinder.Support.Track.Clarify"]},
        },
        "bot_answer": {
            RESPONSE: int_rsp.multi_response(
                replies=["I think that reading is cool and all people should read books!",
                         "I just cannot imagine my life without books."],
                confidences=[1.0, 1.0],
                hype_attr=[
                    {"can_continue": common_constants.MUST_CONTINUE},  # for the first hyp
                    {"can_continue": common_constants.CAN_CONTINUE_SCENARIO},  # for the second hyp
                ],
            ),
            TRANSITIONS: {("bot_fav_book", "fav_name"): cnd.true()},
            MISC: {"speech_functions": ["React.Rejoinder.Support.Response.Resolve"]},
        },
        "right_book_reassure": {
            RESPONSE: "Oh, I'm sure you'll find it one day!",
            TRANSITIONS: {("bot_fav_book", "fav_name"): cnd.true()},
            MISC: {"speech_functions": ["React.Respond.Support.Develop.Extend"]},
        },
        "ask_not_like": {
            RESPONSE: 'Oh. Then what is the reason, in your opinion?',
            TRANSITIONS: {("bot_fav_book", "fav_name"): cnd.true()},
            MISC: {"speech_functions": ["React.Rejoinder.Support.Track.Clarify"]},
        },
        "test_5": {
            RESPONSE: int_rsp.multi_response(
                replies=["bye", "goodbye"],
                confidences=[1.0, 0.5],
                hype_attr=[
                    {"can_continue": common_constants.MUST_CONTINUE},  # for the first hyp
                    {"can_continue": common_constants.CAN_CONTINUE_SCENARIO},  # for the second hyp
                ],
            ),
            PROCESSING: {"set_confidence": int_prs.set_confidence(0.0)},
            TRANSITIONS: {},
            MISC: {"speech_functions": ["React.Rejoinder.Confront.Challenge.Detach"]},
        },
        "change_subject": {
            RESPONSE: "All right. By the way, I'm really interested in books that are important for the mankind. Have you ever read the Bible?",
            TRANSITIONS: {("bible_flow", "bible_elaborate_not_read"): cnd.any(
                [
                    dm_cnd.is_sf("React.Respond.Confront.Reply.Disagree"),
                    dm_cnd.is_sf("React.Respond.Support.Reply.Disavow"),
                    dm_cnd.is_sf("React.Rejoinder.Confront.Challenge.Counter"),
                    int_cnd.is_no_vars
                ]
            ),
                          ("bible_flow", "bible_elaborate"): cnd.true()},
            MISC: {"speech_functions": ["React.Rejoinder.Support.Track.Clarify"]},
        },
    },
    "bot_fav_book": {
        "fav_name": {
            RESPONSE: loc_rsp.append_unused(initial="{fav_book_init} ", phrases=[loc_rsp.TELL_REQUEST]),
            PROCESSING: {
                "save_next_key": loc_prs.save_next_key(fav_keys, loc_rsp.FAVOURITE_BOOK_ATTRS),
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                "fav_denied": int_cnd.is_no_vars,
            },
        },
        "fav_elaborate": {
            RESPONSE: loc_rsp.append_unused(initial="{cur_book_about} ", phrases=[loc_rsp.TELL_REQUEST2]),
            PROCESSING: {
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                ("concrete_book_flow", "offer_date"): cnd.true(),
            },
        },
        "fav_denied": {
            RESPONSE: "OK, let me ask you something else then, alright?",
            PROCESSING: {
                "set_flag": loc_prs.set_flag("denied_favorite", True),
                "set_confidence": int_prs.set_confidence(BIT_LOWER_CONFIDENCE),
            },
            TRANSITIONS: {
                ("books_general", "book_restart"): int_cnd.is_yes_vars,
            },
        },
    },
    "concrete_book_flow": {
        "ask_fav": {
            RESPONSE: loc_rsp.append_unused(initial="Fabulous! And ", phrases=[loc_rsp.WHAT_BOOK_IMPRESSED_MOST]),
            PROCESSING: {
                "set_flag": loc_prs.set_flag("user_fav_book_visited", True),
                "execute_response": loc_prs.execute_response,
            },
            TRANSITIONS: {
                "user_fav": cnd.true()
            },
        },
        "user_fav": {
            RESPONSE: "Great choice! Would you like us to discuss it?",
            PROCESSING: {
                "get_book": loc_prs.get_book,
                "set_flag": loc_prs.set_flag("user_fav_book_visited", True),
            },
            TRANSITIONS: {"denied_information": cnd.true()},
        },
        "ask_opinion": {
            RESPONSE: loc_rsp.append_unused(initial="", phrases=loc_rsp.OPINION_REQUEST_ON_BOOK_PHRASES),
            TRANSITIONS: {
                "user_liked": loc_cnd.sentiment_detected("positive"),
                "user_disliked": loc_cnd.sentiment_detected("negative"),
            },
        },
        "user_liked": {
            RESPONSE: loc_rsp.append_question(
                initial="I see you love it." "It is so wonderful that you read the books you love. "
            ),
            PROCESSING: {"set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE)},
            TRANSITIONS: {
                ("bible_flow", "bible_start"): cnd.true(),
                "denied_information": int_cnd.is_no_vars,
            },
        },
        "user_disliked": {
            RESPONSE: loc_rsp.append_question(initial="It's OK. Maybe some other books will fit you better. "),
            PROCESSING: {"set_confidence": int_prs.set_confidence(SUPER_CONFIDENCE)},
            TRANSITIONS: {},
        },
        "offer_best": {
            RESPONSE: loc_rsp.append_unused(
                initial="You have a great taste in books! "
                "I also adore books by {cur_book_author}, "
                "especially {cur_author_best}. ",
                phrases=loc_rsp.ASK_ABOUT_OFFERED_BOOK,
            ),
            PROCESSING: {
                "get_book": loc_prs.get_book,
                "get_author": loc_prs.get_author,
                "get_book_by_author": loc_prs.get_book_by_author,
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: loc_cnd.has_read_transitions,
        },
        "offer_genre": {
            RESPONSE: loc_rsp.ASK_GENRE_OF_BOOK,
            PROCESSING: {
                "get_book": loc_prs.get_book,
                "get_book_genre": loc_prs.get_book_genre,
            },
            TRANSITIONS: {"tell_genre": cnd.true(10)},
        },
        "tell_genre": {
            RESPONSE: loc_rsp.append_question(initial="I believe that {cur_book_name} is {cur_genre}. "),
            PROCESSING: {
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                ("bible_flow", "bible_start"): cnd.true(),
                "denied_information": int_cnd.is_no_vars,
            },
        },
        "offer_fact": {
            RESPONSE: ("It's an amazing book! " + loc_rsp.OFFER_FACT_ABOUT_BOOK),
            PROCESSING: {
                "get_book": loc_prs.get_book,
                "about_bookreads": loc_prs.about_bookreads,
                "about_wiki": loc_prs.about_wiki,
                "get_movie": loc_prs.get_movie,
            },
            TRANSITIONS: {
                "denied_information": cnd.true(),
            },
        },
        "tell_about": {  # НЕ РАБОТАЕТ
            RESPONSE: loc_rsp.append_unused(initial="{cur_book_about} ", phrases=[loc_rsp.WHEN_IT_WAS_PUBLISHED]),
            PROCESSING: {
                "get_book_year": loc_prs.get_book_year,
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                "tell_date": cnd.all([int_cnd.is_yes_vars, loc_cnd.check_slot("cur_book_ago")]),
                "denied_information": int_cnd.is_no_vars,
                ("global_flow", "fallback"): cnd.true(),
            },
        },
        "tell_movie": {
            RESPONSE: "I enjoyed watching the film {cur_book_movie} based on this book, "
            "directed by {cur_book_director}. ",
            PROCESSING: {
                "get_movie": loc_prs.get_movie,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {},
        },
        "offer_date": {
            RESPONSE: loc_rsp.append_unused(
                initial="I've read it. It's an amazing book! ",
                phrases=[loc_rsp.WHEN_IT_WAS_PUBLISHED],
            ),
            PROCESSING: {
                "get_book": loc_prs.get_book,
                "get_book_year": loc_prs.get_book_year,
                "execute_response": loc_prs.execute_response,
            },
            TRANSITIONS: {
                "tell_date": cnd.all([int_cnd.is_yes_vars, loc_cnd.check_slot("cur_book_ago")]),
                "denied_information": cnd.true(),
            },
        },
        "tell_date": {
            RESPONSE: loc_rsp.append_unused(initial="{cur_book_ago}ago! ", phrases=loc_rsp.DID_NOT_EXIST),
            PROCESSING: {
                "get_book_year": loc_prs.get_book_year,
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {
                "offer_genre": cnd.true(),
            },
        },
        "denied_information": {
            RESPONSE: loc_rsp.append_question(initial="As you wish. "),
            TRANSITIONS: {("bible_flow", "bible_start", 1): cnd.true(),
                          ("undetected_flow", "quit"): cnd.true(),
                          },
        },
    },
    "genre_flow": {
        "tell_phrase": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                "set_flag": loc_prs.set_flag("user_fav_genre_visited", True),
                "get_genre_regexp": loc_prs.get_genre_regexp,
                "set_can_continue": int_prs.set_can_continue(MUST_CONTINUE),
            },
            TRANSITIONS: {
                ("concrete_book_flow", "denied_information"): int_cnd.is_no_vars,
            },
        },
        "return_genrebook": {
            RESPONSE: (
                "Amazing! I hear, {cur_book_name} is quite good. " + loc_rsp.HAVE_YOU_READ_BOOK
            ),
            PROCESSING: {
                "get_genre_regexp": loc_prs.get_genre_regexp,
                "get_book_by_genre": loc_prs.get_book_by_genre,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: loc_cnd.has_read_transitions,
        },
        "not_read_genrebook": {
            RESPONSE: loc_rsp.append_unused(
                initial=random.choice(loc_rsp.READ_BOOK_ADVICES) + " ",
                phrases=[loc_rsp.TELL_REQUEST],
            ),
            PROCESSING: {"execute_response": loc_prs.execute_response},
            TRANSITIONS: {
                ("books_general", "book_restart"): int_cnd.is_no_vars,
            },
        },
        "genrebook_info": {
            RESPONSE: loc_rsp.append_question(initial="{cur_book_about} Anyway, "),
            PROCESSING: {
                "about_bookreads": loc_prs.about_bookreads,
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {},
        },
        "bot_fav": {
            RESPONSE: loc_rsp.genre_phrase,
            PROCESSING: {
                "save_slots_to_ctx": int_prs.save_slots_to_ctx(
                    {"cur_genre", random.choice(list(loc_rsp.GENRE_PHRASES.keys()))}
                )
            },
            TRANSITIONS: {},
        },
    },
    "bible_flow": {
        "bible_start": {
            RESPONSE: "Okay! By the way, I know that Bible is one of the most widespread books on Earth. "
            "It is the foundation stone of Christianity. Have you read the whole Bible?",
            TRANSITIONS: {
                "bible_elaborate_not_read": cnd.any(
                    [
                        dm_cnd.is_sf("React.Respond.Confront.Reply.Disagree"),
                        dm_cnd.is_sf("React.Respond.Support.Reply.Disavow"),
                        dm_cnd.is_sf("React.Rejoinder.Confront.Challenge.Counter"),
                        int_cnd.is_no_vars
                    ]
                ),
                "bible_elaborate": cnd.true(),
            },
        },
        "bible_elaborate": {
            RESPONSE: loc_rsp.append_unused(
                initial="Unfortunately, as a socialbot, I don't have an immortal soul, "
                "so I don't think I will ever go to Heaven. "
                "That's why I don't know much about religion. "
                "Apart from the Bible, ",
                phrases=loc_rsp.QUESTIONS_ABOUT_BOOKS,
            ),
            TRANSITIONS: {
                ("books_general", "book_restart"): cnd.true(),
            },
        },
        "bible_elaborate_not_read": {
            RESPONSE: loc_rsp.append_unused(
                initial='''I definitely recommend you to read it one day! All right, let's discuss something else. ''',
                phrases=loc_rsp.QUESTIONS_ABOUT_BOOKS,
            ),
            TRANSITIONS: {
                ("books_general", "book_restart"): cnd.true(),
            },
        },
    },
    "undetected_flow": {
        "quit": {
            RESPONSE: "I'm sorry, I don't know what to answer yet, but I will definitely learn! Have a nice day, bye!",
            TRANSITIONS: {},
        },
        "change_branch": {
            RESPONSE: loc_rsp.append_question(initial=""),
            TRANSITIONS: {},
        },
        "cannot_name": {RESPONSE: loc_rsp.BOOK_ANY_PHRASE, TRANSITIONS: {}},
        "ask_question": {
            RESPONSE: loc_rsp.append_question(initial="Never heard about it. I will check it out later. "),
            TRANSITIONS: {},
        },
        "unrecognized_author": {
            RESPONSE: loc_rsp.append_question(
                initial="Strange, I've never heard about this author. I'll surely check out his works sometime. "
            ),
            TRANSITIONS: {},
        },
        "no_book_author": {
            RESPONSE: loc_rsp.append_question(initial="{cur_book_author} is a wonderful writer! By the way, "),
            PROCESSING: {
                "get_author_regexp": loc_prs.get_author_regexp,
                "execute_response": loc_prs.execute_response,
                "fill_responses_by_slots": int_prs.fill_responses_by_slots(),
            },
            TRANSITIONS: {},
        },
    }
}


actor = Actor(
    flows,
    start_label=("global_flow", "start"),
    fallback_label=("undetected_flow", "quit")
)
logger.info("Actor created successfully")
