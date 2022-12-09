from common.music import (
    OPINION_REQUESTS_ABOUT_MUSIC,
    ASK_ABOUT_MUSIC,
    GENRES_TEMPLATE,
    VARIOUS_GENRES_TEMPLATE,
    MUSIC_REQUEST_RE,
    MUSIC_TEMPLATE,
)
from common.link import link_to_skill2i_like_to_talk
from common.universal_templates import NOT_LIKE_PATTERN, STOP_PATTERN

music_linkto = f"({'|'.join(OPINION_REQUESTS_ABOUT_MUSIC + link_to_skill2i_like_to_talk['dff_music_skill'])})"


topic_config = {
    "music": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": music_linkto}, "bot", True],
                        ["is_no", "user", False],
                        [{"pattern": NOT_LIKE_PATTERN}, "user", False],
                        [{"pattern": STOP_PATTERN}, "user", False],
                    ]
                ],
                "can_continue": "must",
                "conf": 1.0,
            },
            {
                "cond": [
                    [
                        {
                            "wiki_parser_types": [
                                "Q488205",
                                "Q36834",
                                "Q177220",
                                "Q753110",
                                "Q105756498",
                                "Q215380",
                                "Q207628",
                            ]
                        },
                        "user",
                        True,
                    ],
                    [{"pattern": MUSIC_REQUEST_RE}, "user", True],
                ],
                "can_continue": "must",
            },
        ],
        "pattern": MUSIC_TEMPLATE,
        "expected_entities": ["genre", "singer", "group", "song"],
        "expected_subtopic_info": [
            {"subtopic": "discuss_genre", "cond": [[{"pattern": GENRES_TEMPLATE}, "user", True]]},
            {
                "subtopic": "discuss_singer",
                "cond": [[{"wiki_parser_types": ["Q488205", "Q36834", "Q177220", "Q753110"]}, "user", True]],
            },
            {"subtopic": "discuss_group", "cond": [[{"wiki_parser_types": ["Q105756498", "Q215380"]}, "user", True]]},
            {"subtopic": "discuss_song", "cond": [[{"wiki_parser_types": ["Q207628"]}, "user", True]]},
            {"subtopic": "my_music", "cond": [[{"pattern": ASK_ABOUT_MUSIC}, "user", True]]},
            {"subtopic": "various_genres", "cond": [[{"pattern": VARIOUS_GENRES_TEMPLATE}, "user", True]]},
            {"subtopic": "alexa_music", "cond": [[{"pattern": MUSIC_REQUEST_RE}, "user", True]]},
            {"subtopic": "various_music_types", "cond": [[{"pattern": music_linkto}, "bot", True]]},
            {"subtopic": "what_music", "cond": [[{"pattern": "(music|song)"}, "user", True]]},
            {"subtopic": "all_kinds_music", "cond": [["any"]]},
        ],
        "smalltalk": [
            {
                "utt": [
                    "I'm always happy to have a conversation with such a wonderful person!",
                    "You have an amazing music taste!",
                ],
                "subtopic": "all_kinds_music",
                "expected_subtopic_info": [{"subtopic": "relaxing_music", "cond": [["is_no", "user", False]]}],
            },
            {
                "utt": ["I'm a music lover too! What music is in your playlist?"],
                "subtopic": "what_music",
                "expected_entities": ["genre", "singer", "group", "song"],
                "expected_subtopic_info": ["genres", "singer", "group", "song", "my_music", "various_genres"],
            },
            {
                "utt": ["Brilliant! I like this genre too!", "What singers or bands are in your playlist?"],
                "subtopic": "various_genres",
                "expected_entities": ["singer", "group", "song"],
            },
            {
                "utt": [
                    "Yes, I like {user_genre}!",
                    "My favourite {user_genre} performer is {[bot_data, user_genre, singer]}.",
                    "The song {[bot_data, user_genre, song]} is the best!",
                    "What {user_genre} singers or bands are in your playlist?",
                ],
                "subtopic": "discuss_genre",
                "expected_entities": ["singer", "group", "song"],
                "expected_subtopic_info": ["singer", "group", "song", "my_music"],
            },
            {
                "utt": [
                    "You have a good taste in music! I also listen to {user_singer}.",
                    "I'm fascinated with their songs {[user_singer, songs]}.",
                ],
                "subtopic": "discuss_singer",
                "expected_subtopic_info": ["pop", "rock", "rap", "my_music"],
            },
            {
                "utt": [
                    "You have a good taste in music! I also listen to {user_group}.",
                    "I'm fascinated with their songs {[user_group, songs]}.",
                ],
                "subtopic": "discuss_group",
                "expected_subtopic_info": ["pop", "rock", "rap", "my_music"],
            },
            {
                "utt": ["The song {user_song} is very cool!", "I like listening to {[user_song, performer] music}."],
                "subtopic": "discuss_song",
                "expected_subtopic_info": ["pop", "rock", "rap", "my_music"],
            },
            {
                "utt": ["I would like to tell you about some latest pop songs, should I continue?"],
                "subtopic": "pop",
                "expected_subtopic_info": [{"subtopic": "pop_more", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["I would like to tell you about some latest popular rock songs, should I continue?"],
                "subtopic": "rock",
                "expected_subtopic_info": [{"subtopic": "rock_more", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["I would like to tell you about some latest popular rap tracks, should I continue?"],
                "subtopic": "rap",
                "expected_subtopic_info": [{"subtopic": "rap_more", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Save your tears by The Weeknd and Ariana Grande is a cool track.",
                    "Do you like Ariana Grande?",
                ],
                "subtopic": "pop_more",
            },
            {
                "utt": ["BTS song Butter is number one in the chart.", "What do you think about Korean pop or K-pop?"],
                "subtopic": "pop_more",
            },
            {
                "utt": ["Noverber Rain by Gunz and Roses is a cool track! Do you like Gunz and Roses?"],
                "subtopic": "rock_more",
            },
            {
                "utt": [
                    "I also like Nothing Else Matters by Metallica.",
                    "Lars Ulrich told that they are recording a new album which will be the best in "
                    "their discography.",
                ],
                "subtopic": "rock_more",
            },
            {
                "utt": [
                    "I did it by DJ Khaled, Post Malone, DaBaby and Megan Thee Stallion is a cool track!",
                    "Do you like the vocal of Post Malone?",
                ],
                "subtopic": "rap_more",
            },
            {
                "utt": [
                    "I also like Austronaut in the Ocean track of Masked Wolf.",
                    "I saw a clip for this song Youtube, it is about spaceflight on the Moon.",
                ],
                "subtopic": "rap_more",
            },
            {"utt": ["I like Scorpions.", "Wind of Change is the best!"], "subtopic": "my_music"},
            {
                "utt": [
                    "I think that live performance of your favourite singer is a cool event.",
                    "Have you been to any live shows lately?",
                ]
            },
            {
                "utt": ["Do you like listening to music on the journey, in the car or in the bus?"],
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True], [{"pattern": "(car|bus)"}, "user", True]],
                        "answer": "Great! Relaxing music makes time go faster.",
                    },
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "I agree with you! It's better to travel in silence.",
                    },
                ],
            },
            {
                "utt": ["Do you listen to music in headphones or on a portable speaker?"],
                "next_ackn": [
                    {
                        "cond": [[{"pattern": "(head|phones)"}, "user", True]],
                        "answer": "Great! Headphones enhance the thrill of music.",
                    },
                    {
                        "cond": [[{"pattern": "speaker"}, "user", True]],
                        "answer": "Great! A speaker helps to share your favourite tracks " "with your friends.",
                    },
                ],
            },
            {
                "utt": ["Do you play any musical instrument?"],
                "next_ackn": [
                    {
                        "cond": [
                            ["is_yes", "user", True],
                            [
                                {
                                    "pattern": "(piano|violin|guitar|drum|bass|trombome|trumpet"
                                    "|flute|cello|banjo|harmo|accordeon|synth|ukulele)"
                                },
                                "user",
                                True,
                            ],
                        ],
                        "answer": "You are a very creative person!",
                    },
                    {"cond": [["is_no", "user", True]], "answer": "Ok! It's never late to try!"},
                ],
            },
            {
                "utt": [
                    "Do you like to listen to music during gaming, while you are playing a game?",
                    "I can tell you about some music for gaming, should I continue?",
                ],
                "expected_subtopic_info": [
                    {
                        "subtopic": "gaming_music",
                        "cond": [["is_yes", "user", True], [{"pattern": "(continue|tell)"}, "user", True]],
                    }
                ],
            },
            {
                "utt": [
                    "I like gaming music mixes on Youtube.",
                    "There are drum-n-bass, trap, electro house and dubstep in these tracklists.",
                    "Would you like to know about some chilling tracks you can listen while gaming?",
                ],
                "expected_subtopic_info": [
                    {
                        "subtopic": "gaming_music_tracks",
                        "cond": [["is_yes", "user", True], [{"pattern": "(continue|tell)"}, "user", True]],
                    }
                ],
                "subtopic": "gaming_music",
            },
            {
                "utt": [
                    "Vicetone, Ship Wrek, Roy Knox and TheFatRat are top performers!",
                    "Have a pleasant listening!",
                ],
                "subtopic": "gaming_music_tracks",
            },
            {
                "utt": [
                    "I'm sorry, i do not have this function. But I am a music lover too!",
                    "I can tell you about some relaxing music, should I?",
                ],
                "subtopic": "alexa_music",
                "expected_subtopic_info": [{"subtopic": "relaxing_music", "cond": [["is_no", "user", False]]}],
            },
            {
                "utt": [
                    "Cool! I am a music lover too!",
                    "I can tell you about some relaxing music, should I continue?",
                ],
                "subtopic": "various_music_types",
                "expected_subtopic_info": [{"subtopic": "relaxing_music", "cond": [["is_no", "user", False]]}],
            },
            {
                "utt": [
                    "There are a lot of compilations of relaxing music on Youtube.",
                    "I like Peter Helland music, it is very chilling. Would you like to hear more?",
                ],
                "subtopic": "relaxing_music",
                "expected_subtopic_info": [{"subtopic": "more_relaxing_music", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "You can listen to sound of nature, for example birdsong or the sounds of sea.",
                    "Do you like sounds of the rain?",
                ],
                "subtopic": "more_relaxing_music",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Me too! I like to dream listening sounds of rain."}
                ],
            },
        ],
        "bot_data": {
            "rock": {"singer": "Deep Purple", "song": "Smoke on the Water"},
            "pop": {"singer": "Drake", "song": "Hotline Bling"},
            "rap": {"singer": "Travis Scott", "song": "Goosebumps"},
            "jazz": {"singer": "Louis Armstrong", "song": "What a Wonderful World"},
            "reggae": {"singer": "Bob Marley", "song": "Get Up Stand Up"},
            "rnb": {"singer": "Beyonce", "song": "All Night"},
        },
        "ackn": [
            {
                "cond": [[{"pattern": "my favo(u)?rite song is (.*?)"}, "user", True]],
                "answer": ["I like this song too!"],
            },
            {
                "cond": [[[{"pattern": "live shows"}, "bot", True], ["is_yes", "user", True]]],
                "answer": ["I'm happy that you had a good time!"],
            },
            {
                "cond": [[[{"pattern": "live shows"}, "bot", True], ["is_no", "user", True]]],
                "answer": ["There wasn't much going on due to CoVID-19. Hope we will get some in future."],
            },
        ],
        "expected_entities_info": {
            "genre": {
                "name": "user_genre",
                "entity_substr": [
                    ["pop", "(\\bpop|popular music)"],
                    ["rock", "(\\brock|\\bpunk|heavy metal)"],
                    ["rap", "(\\brap|hip hop)"],
                    ["jazz", "(jazz|blues)"],
                    ["reggae", "reggae"],
                    ["rnb", "rnb|r\\.n\\.b\\.|are and b\\.|r. and b."],
                ],
            },
            "singer": {
                "name": "user_singer",
                "wiki_parser_types": ["Q488205", "Q36834", "Q177220", "Q753110"],
                "relations": ["genre", "songs", "albums", "part of"],
            },
            "group": {
                "name": "user_group",
                "wiki_parser_types": ["Q105756498", "Q215380"],
                "relations": ["genre", "songs", "albums", "has part"],
            },
            "song": {
                "name": "user_song",
                "wiki_parser_types": ["Q207628"],
                "relations": ["genre", "performer", "part of"],
            },
        },
        "expected_subtopics": {
            "genres": {"subtopic": "discuss_genre", "cond": [[{"pattern": GENRES_TEMPLATE}, "user", True]]},
            "singer": {
                "subtopic": "discuss_singer",
                "cond": [[{"wiki_parser_types": ["Q488205", "Q36834", "Q177220", "Q753110"]}, "user", True]],
            },
            "group": {
                "subtopic": "discuss_group",
                "cond": [[{"wiki_parser_types": ["Q105756498", "Q215380"]}, "user", True]],
            },
            "song": {"subtopic": "discuss_song", "cond": [[{"wiki_parser_types": ["Q207628"]}, "user", True]]},
            "pop": {
                "subtopic": "pop",
                "cond": [
                    [{"user_info": {"user_genre": "pop"}}, "user", True],
                    [{"entity_triplets": ["user_singer", "genre", ["pop", "pop music"]]}],
                ],
            },
            "rock": {
                "subtopic": "rock",
                "cond": [
                    [{"user_info": {"user_genre": "rock"}}, "user", True],
                    [
                        {"entity_triplets": ["user_singer", "genre", ["rock", "rock music", "heavy metal"]]},
                        "user",
                        True,
                    ],
                ],
            },
            "rap": {
                "subtopic": "rap",
                "cond": [
                    [{"user_info": {"user_genre": "rap"}}, "user", True],
                    [{"entity_triplets": ["user_singer", "genre", ["rap", "hip hop"]]}, "user", True],
                ],
            },
            "my_music": {
                "subtopic": "my_music",
                "cond": [[{"pattern": "(what|which) (music )?(do )?you " "(like|enjoy)"}, "user", True]],
            },
            "various_genres": {
                "subtopic": "various_genres",
                "cond": [[{"pattern": VARIOUS_GENRES_TEMPLATE}, "user", True]],
            },
        },
    }
}
