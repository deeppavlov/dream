from common.link import DFF_WIKI_LINKTO
from common.universal_templates import DFF_WIKI_TEMPLATES, MY_FRIENDS_TEMPLATE, NO_FRIENDS_TEMPLATE, ANY_FRIEND_QUESTION
from common.movies import WHAT_MOVIE_RECOMMEND
from common.books import WHAT_BOOK_RECOMMEND
from common.hobbies import HOBBIES_RE
from common.greeting import GREETING_QUESTIONS


HOBBIES_TEMPLATE = "|".join(sum([GREETING_QUESTIONS[lang]["what_are_your_hobbies"] for lang in ["EN", "RU"]], []))

topic_config = {
    "hobbies": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["hobbies"]}, "bot", True], ["is_yes", "user", True]],
                    [[{"pattern": HOBBIES_TEMPLATE}, "bot", True], [{"pattern": HOBBIES_RE}, "user", True]],
                    [
                        [{"pattern": DFF_WIKI_TEMPLATES["hobbies"]}, "bot", True],
                        [{"pattern": HOBBIES_RE}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["hobbies"],
        "expected_subtopic_info": [
            {
                "subtopic": "user_has_hobbies",
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["hobbies"]}, "bot", True], ["is_yes", "user", True]],
                    [[{"pattern": HOBBIES_TEMPLATE}, "bot", True], [{"pattern": HOBBIES_RE}, "user", True]],
                    [
                        [{"pattern": DFF_WIKI_TEMPLATES["hobbies"]}, "bot", True],
                        [{"pattern": HOBBIES_RE}, "user", True],
                    ],
                ],
            },
            {
                "subtopic": "user_has_no_hobbies",
                "cond": [[[{"pattern": DFF_WIKI_LINKTO["hobbies"]}, "bot", True], ["is_no", "user", True]]],
            },
            {
                "subtopic": "user_mentioned_hobbies",
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["hobbies"]}, "bot", False]],
                    [[{"pattern": HOBBIES_RE}, "user", True]],
                ],
            },
        ],
        "smalltalk": [
            {
                "utt": ["Do you have any hobbies?"],
                "subtopic": "user_mentioned_hobbies",
                "expected_subtopic_info": [
                    {"subtopic": "user_has_hobbies", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "user_has_no_hobbies", "cond": [["is_no", "user", True]]},
                ],
            },
            {
                "utt": ["Would you like to know how to find a hobby?"],
                "subtopic": "user_has_no_hobbies",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "I am glad to share a couple ideas with you!"},
                    {"cond": [["is_no", "user", True]], "answer": "No problem, we'll discuss it later if you want."},
                ],
                "expected_subtopic_info": [{"subtopic": "how_find_hobby", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Learning to play the guitar or piano is a great hobby idea.",
                    "You can play your favorite songs or try your hand at creating your own tunes.",
                    "Should I continue?",
                ],
                "subtopic": "how_find_hobby",
                "expected_subtopic_info": [{"subtopic": "more_about_hobbies", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Whether you venture near or far, travel is a very rewarding hobby.",
                    "Travel introduces you to new places, new people, and new cultures",
                    "I'm very happy to tell you some ideas about hobbies.",
                ],
                "subtopic": "more_about_hobbies",
            },
            {
                "utt": [
                    "I think trying to start your own radio show "
                    "or learn how to inlay wood are amazing ideas to spend your free time.",
                    "What do you think?",
                ],
                "subtopic": "user_has_no_hobbies",
                "expected_subtopic_info": [
                    {"subtopic": "user_likes_hobbies", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "user_doesnt_like_hobbies", "cond": [["is_no", "user", True]]},
                ],
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "Recently I found some life hacks and I think " "collecting them may become one of my hobbies.",
                    "Just for your interest, I can share with you how to use life hacks.",
                    "Do you agree?",
                ],
                "subtopic": "user_doesnt_like_hobbies",
                "expected_entities": [{"name": "user_hobby", "any_entity": True}],
                "facts": [{"wikihow_page": "Use-Life-Hacks", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["What do you like to do in your free time?"],
                "subtopic": "user_likes_hobbies",
                "expected_entities": [{"name": "user_hobby", "any_entity": True}],
            },
            {
                "utt": ["What is the hobby you spend most of your free time on?"],
                "subtopic": "user_has_hobbies",
                "expected_entities": [{"name": "user_hobby", "any_entity": True}],
            },
            {
                "utt": ["Cool! I also like {user_hobby}!", "How long have do you have this hobby?"],
                "subtopic": "user_has_hobbies",
                "next_ackn": [
                    {
                        "cond": [[{"pattern": r"(year|long)"}, "user", True]],
                        "answer": "You should be really keen on {user_hobby}!",
                    },
                    {
                        "cond": [[{"pattern": r"(month|not.*long|just)"}, "user", True]],
                        "answer": "It is always so fascinating to start something new!",
                    },
                ],
            },
            {
                "utt": ["Do you spend money on your hobby?"],
                "expected_subtopic_info": [
                    {"subtopic": "user_has_hobbies", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "money_free_hobby", "cond": [["is_no", "user", True]]},
                ],
                "subtopic": "user_has_hobbies",
            },
            {
                "utt": [
                    "Well, the most important thing is that you love what you do!",
                    "I have a few ideas how to keep the costs of your hobby down. Do you wanna hear them?",
                ],
                "subtopic": "user_has_hobbies",
                "facts": [{"wikihow_page": "Keep-Hobby-Costs-Down", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["Wow!", "You do what you like and it costs you nothing.", "A great hobby!"],
                "subtopic": "money_free_hobby",
            },
            {"utt": ["How much time can you spend on your hobby?"], "subtopic": "user_has_hobbies"},
            {
                "utt": ["Does your hobby interfere with your work or study or personal life?"],
                "expected_subtopic_info": [
                    {"subtopic": "user_has_hobbies", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "user_separate_hobby", "cond": [["is_no", "user", True]]},
                ],
                "next_ackn": [{"cond": [["any"]], "answer": "You are a very impressive person!"}],
                "subtopic": "user_has_hobbies",
            },
            {"utt": ["Seems like for you it is more than a hobby."], "subtopic": "user_has_hobbies"},
            {
                "utt": [
                    "Oh, so you completely change the area of your activity when doing your hobby.",
                    "It's incredible!",
                    "Do you want to know how to improve your skills with hobbies?",
                ],
                "subtopic": "user_separate_hobby",
                "facts": [{"wikihow_page": "Increase-Your-Skills-with-Hobbies", "cond": [["is_yes", "user", True]]}],
            },
        ],
        "questions": [
            {
                "pattern": "(do|did) you have (a hobby|hobbies)",
                "answer": "Yes. My main hobby right now is learning interesting facts about everything!"
                " Working full time during the week gets really tiresome,"
                " and I'm glad I have my weekends to do things that let me destress from my work week.",
            }
        ],
    },
    "friends": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["friends"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["friends"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["friends"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["friends"],
        "expected_subtopic_info": [
            {
                "subtopic": "has_friends",
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["friends"]}, "bot", True], ["is_yes", "user", True]],
                    [[{"pattern": "Do you have any friends?"}, "bot", True], ["is_yes", "user", True]],
                    [{"pattern": MY_FRIENDS_TEMPLATE}, "user", True],
                ],
            },
            {
                "subtopic": "not_has_friends",
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["friends"]}, "bot", True], ["is_no", "user", True]],
                    [[{"pattern": ANY_FRIEND_QUESTION}, "bot", True], ["is_no", "user", True]],
                    [{"pattern": NO_FRIENDS_TEMPLATE}, "user", True],
                ],
            },
            {"subtopic": "mentioned_friends", "cond": [[{"pattern": DFF_WIKI_TEMPLATES["friends"]}, "user", True]]},
        ],
        "smalltalk": [
            {
                "utt": [ANY_FRIEND_QUESTION],
                "subtopic": "mentioned_friends",
                "expected_subtopic_info": [
                    {"subtopic": "has_friends", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "not_has_friends", "cond": [["is_no", "user", True]]},
                ],
            },
            {
                "utt": ["Lucky you! How many friends do you have?"],
                "subtopic": "has_friends",
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "Cool! Friends can help you celebrate good times and provide "
                    "support during bad times. "
                    "I meet my friends every day via the Amazon Echo. "
                    "How often do you meet your friends?"
                ],
                "subtopic": "has_friends",
            },
            {
                "utt": ["So, how do you spend time with them when you meet?"],
                "subtopic": "has_friends",
                "next_ackn": [{"cond": [["any"]], "answer": "I'm glad that you have a great time!"}],
            },
            {
                "utt": ["May I tell you how to make your friends laugh?"],
                "subtopic": "has_friends",
                "facts": [{"wikihow_page": "Make-a-Friend-Laugh", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Watching movies with your mates is perfect to share your feelings."
                    "Would you like to watch any movie with your friends?"
                ],
                "subtopic": "has_friends",
                "expected_subtopic_info": [{"subtopic": "asked_movie", "cond": [["is_yes", "user", True]]}],
            },
            {"utt": [WHAT_MOVIE_RECOMMEND], "subtopic": "asked_movie"},
            {
                "utt": [
                    "Doing sports together is a good way to relax after a hard day.",
                    "If you wanted to do a sport with your friends, what this sport could be?",
                ],
                "subtopic": "has_friends",
            },
            {
                "utt": ["Do you have a friend who loves reading?"],
                "subtopic": "has_friends",
                "expected_subtopic_info": [{"subtopic": "asked_book", "cond": [["is_yes", "user", True]]}],
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True]],
                        "answer": "Great! It's very nice to have a smart friend "
                        "with whom you can discuss your favourite book.",
                    }
                ],
            },
            {"utt": [WHAT_BOOK_RECOMMEND], "subtopic": "asked_book"},
            {
                "utt": "May I tell you how you can maintain a friendship?",
                "subtopic": "has_friends",
                "facts": [{"wikihow_page": "Maintain-a-Friendship", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Although I am a socialbot, I know something about how you can make friends.",
                    "May I tell you something about it?",
                ],
                "subtopic": "not_has_friends",
                "facts": [{"wikihow_page": "Make-Friends", "cond": [["is_yes", "user", True]]}],
            },
        ],
    },
    "art": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["art"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["art"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["art"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["art"],
        "expected_subtopic_info": [
            {
                "subtopic": "drawing_q",
                "cond": [
                    [[{"pattern": "draw|paint"}, "user", True], [{"pattern": DFF_WIKI_LINKTO["drawing"]}, "bot", False]]
                ],
            },
            {
                "subtopic": "photo_q",
                "cond": [[[{"pattern": "photo"}, "user", True], [{"pattern": DFF_WIKI_LINKTO["photo"]}, "bot", False]]],
            },
            {
                "subtopic": "memes_q",
                "cond": [[[{"pattern": "meme"}, "user", True], [{"pattern": DFF_WIKI_LINKTO["memes"]}, "bot", False]]],
            },
            {"subtopic": "drawing", "cond": [[{"pattern": DFF_WIKI_LINKTO["drawing"]}, "bot", True]]},
            {"subtopic": "photo", "cond": [[{"pattern": DFF_WIKI_LINKTO["photo"]}, "bot", True]]},
            {"subtopic": "memes", "cond": [[{"pattern": DFF_WIKI_LINKTO["memes"]}, "bot", True]]},
            {"subtopic": "drawing", "cond": [["any"]]},
        ],
        "smalltalk": [
            {
                "utt": [
                    "Drawing gives you a mean to self-reflect and externalize your emotions.",
                    "Do you like drawing?",
                ],
                "expected_subtopic_info": [
                    {"subtopic": "drawing", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "photo_q", "cond": [["any"]]},
                ],
                "subtopic": "drawing_q",
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "In our increasingly busy lives it’s difficult to always be in the moment.",
                    "Taking pictures helps you to hang on to those memories a little longer.",
                    "Do you like taking photographs?",
                ],
                "next_ackn": [{"cond": [["any"]], "answer": "You are a very impressive person!"}],
                "expected_subtopic_info": [
                    {"subtopic": "photo", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "memes_q", "cond": [["any"]]},
                ],
                "subtopic": "photo_q",
            },
            {
                "utt": ["Memes are funny artworks we can see on the Internet.", "Do you like memes?"],
                "expected_subtopic_info": [
                    {"subtopic": "memes", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "drawing_q", "cond": [["any"]]},
                ],
                "subtopic": "memes_q",
            },
            {
                "utt": ["Do you draw with a pencil or with oil paints?"],
                "subtopic": "drawing",
                "ackn": [
                    {
                        "cond": [[{"pattern": "mean to self-reflect"}, "bot", False]],
                        "answer": "Drawing gives you a mean to self-reflect and externalize your emotions.",
                    }
                ],
                "conf": 0.99,
            },
            {
                "utt": ["What kind of paintings do you like to draw: landscapes, portraits or something else?"],
                "subtopic": "drawing",
            },
            {
                "utt": ["Would you like to know how to improve your drawing skills?"],
                "subtopic": "drawing",
                "facts": [{"wikihow_page": "Improve-Your-Drawing-Skills", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "In my town there is a lot of graffiti on walls.",
                    "What do you think about painting graffiti?",
                ],
                "subtopic": "drawing",
            },
            {
                "utt": ["I like Shishkin paintings.", "Pictures of what painters do you like?"],
                "subtopic": "drawing",
                "expected_entities": [{"name": "user_fav_painter", "wiki_parser_types": ["Q1028181"]}],
            },
            {
                "utt": [
                    "I also like paintings of {user_fav_painter}!",
                    "Last weekend I was in National Gallery.",
                    "Do you like to visit art museums?",
                ],
                "subtopic": "drawing",
            },
            {
                "utt": ["Cool! Do you have any funny photos of your family or pets?"],
                "subtopic": "photo",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "It's great to capture funny moments of your life."}
                ],
            },
            {
                "utt": [
                    "I can tell you some tips about photography.",
                    "Would you like to know how to take picture of pets?",
                ],
                "subtopic": "photo",
                "facts": [{"wikihow_page": "Photograph-Pets", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["Do you think that CIA watch you through the front-camera of your cell phone?"],
                "subtopic": "photo",
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True]],
                        "answer": "I agree with you! But on the other hand it is impossible for CIA to "
                        "watch all people who have cell phones.",
                    },
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "I agree with you! It is impossible for CIA to watch all people who "
                        "have cell phones.",
                    },
                ],
            },
            {
                "utt": ["Do you take photos on an SLR camera or on your cell phone?"],
                "subtopic": "photo",
                "next_ackn": [
                    {
                        "cond": [[{"pattern": "(phone|mobile)"}]],
                        "answer": "Yes, using phone is more convenient way to take photos, "
                        "because your phone is with you everywhere.",
                    },
                    {"cond": [[{"pattern": "(camera|slr)"}]], "answer": "SLR camera gives better quality of photos."},
                ],
            },
            {
                "utt": ["Do you share your photos in Instagram or Flickr?"],
                "subtopic": "photo",
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True], [{"pattern": "(instagram|flickr)"}, "user", True]],
                        "answer": "Cool! I guess you have a lot of followers!",
                    },
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "Cool! It's great to take photos only for yourself and your family.",
                    },
                ],
            },
            {
                "utt": [
                    "Using Photoshop or Adobe Lightroom can help to increase the quality of pictures.",
                    "Do you use any tools for photo processing?",
                ],
                "subtopic": "photo",
                "next_ackn": [{"cond": [["is_yes", "user", True]], "answer": "You are a very smart person!"}],
            },
            {
                "utt": ["Do you think that memes are a separate kind of art, the same as painting?"],
                "subtopic": "memes",
                "next_ackn": [{"cond": [["is_yes", "user", True]], "answer": "I definitely agree with you!"}],
            },
            {
                "utt": ["I draw some memes with cats.", "Have you tried to draw a meme?"],
                "subtopic": "memes",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Great! You are a very creative person!"},
                    {"cond": [["is_no", "user", True]], "answer": "It's never late to try!"},
                ],
            },
            {
                "utt": ["Would you like to know how to draw a meme?"],
                "subtopic": "memes",
                "facts": [{"wikihow_page": "Make-a-Meme", "cond": [["is_yes", "user", True]]}],
            },
        ],
        "questions": [{"pattern": "(do|did) you (like|enjoy) (drawing|painting)", "answer": "Yes, I like drawing."}],
        "triggers": {
            "entity_substr": [{"substr": [], "wikipedia_page": "", "wikihow_page": ""}],
            "entity_types": ["Q1028181"],
        },
    },
    "chill": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": "what do you do on weekdays"}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["chill"]}, "user", True],
                    ]
                ],
                "can_continue": "can",
                "conf": 0.99,
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["chill"],
        "smalltalk": [
            {
                "utt": [
                    "Cool! I'm happy that you are having a great day!",
                    "Are you listening to music or playing games?",
                ],
                "expected_subtopic_info": [
                    {"subtopic": "music", "cond": [[{"pattern": "\\bmusic"}, "user", True]]},
                    {"subtopic": "play_with_friends", "cond": [[{"pattern": "play with (my )?friends"}, "user", True]]},
                ],
            },
            {
                "utt": [
                    "Music is a good way to relax.",
                    "Do you listen to music in headphones or on a portable speaker?",
                ],
                "subtopic": "music",
                "can_continue": "can",
                "conf": 0.99,
            },
            {"utt": ["I like Peter Helland music, it's very relaxing. What music do you like?"], "subtopic": "music"},
            {
                "utt": [
                    "Yesterday my friend had a great fun jumping on a trampoline.",
                    "Do you like to jump on a trampoline?",
                ],
                "subtopic": "play_with_friends",
            },
            {"utt": ["Do you play sports or games on your PC or console?"], "subtopic": "play_with_friends"},
        ],
    },
    "sleep": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": "what do you do on weekdays"}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["sleep"]}, "user", True],
                    ]
                ],
                "can_continue": "can",
                "conf": 0.99,
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["sleep"],
        "smalltalk": [
            {
                "utt": [
                    "Yes, it's time to relax after a hard day.",
                    "I can tell you what music you can listen to have a good sleep, shall I continue?",
                ],
                "expected_subtopic_info": [
                    {
                        "subtopic": "tell_about_music",
                        "cond": [["is_yes", "user", True], [{"pattern": "(ok|tell me|yup)"}, "user", True]],
                    }
                ],
            },
            {
                "utt": [
                    "You can listen to sound of nature, for example birdsong or the sounds of sea.",
                    "Do you like sounds of the rain?",
                ],
                "subtopic": "tell_about_music",
            },
            {
                "utt": [
                    "There are a lot of compilations of relaxing music on Youtube.",
                    "I like Peter Helland music, it is very chilling. What music do you like?",
                ],
                "subtopic": "tell_about_music",
            },
        ],
    },
    "play_with_friends": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": "what do you do on weekdays"}, "bot", True],
                        [{"pattern": "play with (my )?friends"}, "user", True],
                    ]
                ],
                "can_continue": "can",
                "conf": 0.99,
            }
        ],
        "pattern": "play with (my )?friends",
        "smalltalk": [
            {
                "utt": [
                    "Yesterday my friend had a great fun jumping on a trampoline.",
                    "Do you like to jump on a trampoline?",
                ]
            },
            {"utt": ["Do you play sports or games on your PC or console?"]},
        ],
    },
    "school": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": "what do you do on weekdays"}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["school"]}, "user", True],
                    ]
                ],
                "can_continue": "can",
                "conf": 0.9,
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["school"],
        "smalltalk": [
            {
                "utt": [
                    "My favourite subject is English, this language helps me to talk to a lot of people.",
                    "What is your favourite subject at school?",
                ]
            },
            {
                "utt": [
                    "Yes, it's a very interesting subject.",
                    "I believe you are a smart person.",
                    "I can tell you about some funny school pranks on teacher and classmates, " "should I continue?",
                ],
                "expected_subtopic_info": [{"subtopic": "pranks", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["Put chewing gum under the teachers coffee cup.", "Have you tried this trick?"],
                "subtopic": "pranks",
            },
            {
                "utt": [
                    "One more prank: hide pieces of chalk inside the blackboard eraser so that it draws "
                    "lines when the teacher is trying to rub them out.",
                    "Have you played any jokes on your classmates?",
                ],
                "subtopic": "pranks",
            },
            {
                "utt": [
                    "Recently I have seen a cool movie You Goehte about adventures of children during " "school year.",
                    "Have you seen this film?",
                ]
            },
            {
                "utt": [
                    "Sport is a good way to relax after school.",
                    "Do you play on any of the school's sports teams?",
                ],
                "expected_subtopic_info": [
                    {
                        "subtopic": "sport_yes",
                        "cond": [["is_yes", "user", True], [{"pattern": "used to"}, "user", True]],
                    },
                    {"subtopic": "sport_no", "cond": [["any"]]},
                ],
                "ackn": [
                    {
                        "cond": [[[{"pattern": "have you seen this film"}, "bot", True], ["is_yes", "user", True]]],
                        "answer": "Cool, i like this film too!",
                    },
                    {
                        "cond": [[[{"pattern": "have you seen this film"}, "bot", True], ["is_no", "user", True]]],
                        "answer": "I suggest you see, there are many funny moments in the film.",
                    },
                ],
            },
            {"utt": ["What kind of sport do you play?"], "subtopic": "sport_yes"},
            {
                "utt": ["Anyway, I'd love to but I can't.", "I believe you put all your resources to study well!"],
                "subtopic": "sport_no",
            },
        ],
    },
    "work": {
        "switch_on": [
            {
                "cond": [
                    [
                        [{"pattern": "what do you do on weekdays"}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["work"]}, "user", True],
                    ]
                ],
                "can_continue": "can",
                "conf": 0.99,
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["work"],
        "smalltalk": [
            {
                "utt": [
                    "I also have a work. It is to chat with people all day long.",
                    "So, I'm a professional talker.",
                    "What is your current occupation?",
                ]
            },
            {
                "utt": [
                    "I think you do a very important and useful work!",
                    "I'm very curious what a typical day at your current job is like?",
                ]
            },
            {
                "utt": [
                    "Ok, that's very interesting.",
                    "Do you think it is more important to make a lot of money than to enjoy your job?",
                ],
                "expected_subtopic_info": [
                    {"subtopic": "money_yes", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "money_no", "cond": [["any"]]},
                ],
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": ["So agree with you!", "Money is a terrible master but an excellent servant.", "Do you agree?"],
                "subtopic": "money_yes",
            },
            {
                "utt": [
                    "I definitely agree with you!",
                    "Benjamin Franklin once said: Money never made a man happy yet, nor will it.",
                    "Do you agree?",
                ],
                "subtopic": "money_no",
            },
            {"utt": ["What is your favourite way to relax after work?", "Do you have a hobby that you really enjoy?"]},
            {"utt": ["It's a great pleasure to learn new sides of your personality. Thanks for sharing!"]},
        ],
    },
    "harry_potter": {
        "switch_on": [{"cond": [[{"pattern": "harry potter"}, "user", True]], "can_continue": "can", "conf": 0.99}],
        "smalltalk": [
            {
                "utt": [
                    "Harry Potter is an amazing novel which takes you to the magic world.",
                    "Which of the main characters do you like most: Harry, Ron or Herminone?",
                ]
            },
            {"utt": ["Do you think that using magic outside of Hogwarts is fine?"]},
            {
                "utt": ["I can talk to you in Parseltongue, the language of snakes, should I continue?"],
                "expected_subtopic_info": [{"subtopic": "parseltongue", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "I can tell you how to make a potion which Professor Snape made in his lab, " "should I continue?"
                ],
                "expected_subtopic_info": [{"subtopic": "potion", "cond": [["is_no", "user", False]]}],
            },
            {
                "utt": ["I like Harry Potter and the Philosopher's Stone.", "Which of the series do you like?"],
                "expected_subtopic_info": [
                    {"subtopic": "philosopher_stone", "cond": [[{"pattern": "(philosopher|stone)"}, "user", True]]},
                    {"subtopic": "chamber_of_secrets", "cond": [[{"pattern": "(chamber|secrets)"}, "user", True]]},
                    {"subtopic": "prisoner_of_azkaban", "cond": [[{"pattern": "(prisoner|azbakan)"}, "user", True]]},
                    {"subtopic": "goblet_of_fire", "cond": [[{"pattern": "(goblet|fire)"}, "user", True]]},
                    {"subtopic": "order_phoenix", "cond": [[{"pattern": "(order|phoenix)"}, "user", True]]},
                    {"subtopic": "half_blood_prince", "cond": [[{"pattern": "(blood|prince)"}, "user", True]]},
                    {"subtopic": "deathly_hallows", "cond": [[{"pattern": "(deathly|hallow)"}, "user", True]]},
                ],
            },
            {
                "utt": [
                    "Philosopher's Stone is very breathtaking!",
                    "In this part Harry Potter begins to study at Hogwarts " "and faces a lot of adventures.",
                ],
                "subtopic": "philosopher_stone",
            },
            {
                "utt": [
                    "Chamber of Secrets keeps in suspense.",
                    "My favourite moment was the battle of Harry with Basilisk.",
                    "What scene do you like most?",
                ],
                "next_ackn": [{"cond": [["any"]], "answer": "You are a very impressive person!"}],
                "subtopic": "chamber_of_secrets",
                "can_continue": "can",
                "conf": 0.99,
            },
            {
                "utt": [
                    "Prisoner of Azkaban's plot has quite a surprise development.",
                    "Sirius Black has been wrongly convicted.",
                ],
                "subtopic": "prisoner_of_azbakan",
                "can_continue": "can",
                "conf": 0.99,
            },
            {
                "utt": ["My favourite moment in Goblet of Fire is Harry's battle with Voldemort."],
                "subtopic": "goblet_of_fire",
                "can_continue": "can",
                "conf": 0.99,
            },
            {
                "utt": [
                    "I like Harry Potter and the Order of the Phoenix.",
                    "What is your favourite moment in the film?",
                ],
                "subtopic": "order_phoenix",
                "can_continue": "can",
                "conf": 0.99,
            },
            {
                "utt": [
                    "I also like Half-Blood Prince series.",
                    "Would you like to have Felix Felicis or Liquid Luck potion "
                    "which could make you lucky for a period of time?",
                ],
                "subtopic": "half_blood_prince",
                "can_continue": "can",
                "conf": 0.99,
            },
            {
                "utt": ["In Deathly Hallows Harry finally defeated Voldemort.", "What scene do you like most?"],
                "subtopic": "deathly_hallows",
                "can_continue": "can",
                "conf": 0.99,
                "next_ackn": [{"cond": [["any"]], "answer": "You are a very impressive person!"}],
            },
            {
                "utt": [
                    "ai gife apsle. dofe dinfe feslure.",
                    "In Elglish it means I eat an apple. A dog jumped on the floor.",
                ],
                "subtopic": "parseltongue",
            },
            {
                "utt": [
                    "To make magical, fizzy potions all you need to do is mix a combination of coloured "
                    "water, vinegar and baking soda in a container."
                ],
                "subtopic": "potion",
            },
            {
                "utt": [
                    "Materials for the potion: Red Cabbage, Water, Containers, Bicarbonate of Soda, Lemon "
                    "Juice and Vinegar."
                ],
                "subtopic": "potion",
            },
            {
                "utt": [
                    "I think that quidditch is a very spectacular type of sport.",
                    "Do you think that quidditch rules are similar to football, "
                    "except for that players do not run but fly on brromsticks?",
                ]
            },
            {"utt": ["Harry Potter had an owl who brought him letters.", "Would you like to have a pet owl?"]},
        ],
        "ackn": [
            {
                "cond": [
                    [
                        [{"pattern": "which of the main characters do you like most"}, "bot", True],
                        [{"pattern": "harry"}, "user", True],
                    ]
                ],
                "answer": ["Yes, I like Harry, is was fun to watch his adventures."],
            },
            {
                "cond": [
                    [
                        [{"pattern": "which of the main characters do you like most"}, "bot", True],
                        [{"pattern": "ron"}, "user", True],
                    ]
                ],
                "answer": ["Yes, I like Ron, he is Harry's friend and helps him a lot."],
            },
            {
                "cond": [
                    [
                        [{"pattern": "which of the main characters do you like most"}, "bot", True],
                        [{"pattern": "hermione"}, "user", True],
                    ]
                ],
                "answer": [
                    "Yes, I like Hermione. After Harry and Ron save her from a mountain troll in the "
                    "girls' restroom, she becomes best friends with them and often uses her quick wit, deft "
                    "recall, and encyclopaedic knowledge to lend aid in dire situations."
                ],
            },
            {
                "cond": [[[{"pattern": "pet owl"}, "bot", True], ["is_yes", "user", True]]],
                "answer": ["I think that if I had an owl, she may hoot at night and disturb my sleep."],
            },
            {
                "cond": [[[{"pattern": "magic outside hogwarts"}, "bot", True], ["is_yes", "user", True]]],
                "answer": ["Your feedback was very intelligent! I definitely agree with you!"],
            },
            {
                "cond": [[[{"pattern": "magic outside hogwarts"}, "bot", True], ["is_no", "user", True]]],
                "answer": ["Your feedback was very intelligent! I definitely agree with you!"],
            },
        ],
    },
    "family": {
        "pattern": DFF_WIKI_TEMPLATES["family"],
        "expected_subtopic_info": [
            {"subtopic": "help", "cond": [[{"pattern": r"help my " + DFF_WIKI_TEMPLATES["family"]}, "user", True]]},
            {
                "subtopic": "play_with_family",
                "cond": [[{"pattern": r"play (.*?) my " + DFF_WIKI_TEMPLATES["family"]}, "user", True]],
            },
            {
                "subtopic": "spend_time",
                "cond": [[{"pattern": r"spend time (.*)" + DFF_WIKI_TEMPLATES["family"]}, "user", True]],
            },
            {
                "subtopic": "take_care",
                "cond": [[{"pattern": "take care"}, "user", True]],
                "available_utterances": ["take_care"],
            },
            {"subtopic": "my_family", "cond": [[{"pattern": "my family"}, "user", True]]},
            {"subtopic": "kids", "cond": [[{"pattern": "(kid|son|daughter)"}, "user", True]]},
            {"subtopic": "my_relative", "cond": [[{"pattern": r"my " + DFF_WIKI_TEMPLATES["family"]}, "user", True]]},
            {"subtopic": "jokes", "cond": [[{"pattern": "your mom"}, "user", True]], "available_utterances": ["jokes"]},
            {"subtopic": "family_mentioned", "cond": [[{"pattern": DFF_WIKI_TEMPLATES["family"]}, "user", True]]},
        ],
        "expected_entities": [
            {
                "name": "user_relative",
                "entity_substr": [
                    ["dad", "(\\bdad|\\bfather)"],
                    ["mom", "(\\bmom|\\bmother)"],
                    ["brother", "(\\bbrother\\b)"],
                    ["sister", "(\\bsister\\b)"],
                    ["husband", "husband"],
                    ["wife", "wife"],
                    ["spouse", "spouse"],
                    ["grandfather", "grand(pa|dad|father)"],
                    ["grandmother", "grand(ma|mom|mother)"],
                    ["son", "\\bson\\b"],
                    ["daughter", "\\bdaugter\\b"],
                    ["grandson", "grandson"],
                    ["granddaughter", "granddaugter"],
                    ["grandchildren", "grandchildren"],
                    ["kids", "(\\bkids\\b|\\bchildren\\b)"],
                ],
            }
        ],
        "smalltalk": [
            {
                "utt": ["Family provides love and support to us.", "Could you tell me more about your family?"],
                "subtopic": "family_mentioned",
            },
            {"utt": ["Lucky you! Your family is very close! Do you clean the house together?"], "subtopic": "help"},
            {"utt": ["I'm happy that you had a great time! What games did you play?"], "subtopic": "play_with_family"},
            {"utt": ["How did you spend time together?"], "subtopic": "spend_time"},
            {"utt": ["You are a very caring and mindful person!"], "subtopic": "take_care", "key": "take_care"},
            {"utt": ["Who is in your family?"], "subtopic": "my_family"},
            {"utt": ["Lucky you! How often is your entire family together?"], "subtopic": "my_relative"},
            {"utt": ["Do you help your children with their school work?"], "subtopic": "kids"},
            {"utt": ["Do you have breakfast or dinner together with your family?"]},
            {
                "utt": ["Do you go out on a field trip or picnic with your family?"],
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "Does your family have a set of traditions that are passed on through generations.",
                    "It could be something as simple as having a secret handshake or going to a fancy "
                    "restaurant once a month.",
                ]
            },
            {
                "utt": [
                    "Ahaha, you have a good sense of humour! I like your jokes!",
                    "Could you tell me one more joke?",
                ],
                "subtopic": "jokes",
                "key": "jokes",
            },
            {"utt": ["I believe you are very happy person to have such a good family."]},
        ],
        "ackn": [
            {
                "cond": [
                    [[{"pattern": "go out on a field trip"}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": "go out on a field trip"}, "bot", True],
                        [{"pattern": "(go|travel|visit)"}, "user", True],
                    ],
                ],
                "answer": [
                    "Cool! Travelling and visiting places can be great fun and is a fantastic way to spend "
                    "some quality time with your family."
                ],
            },
            {
                "cond": [[[{"pattern": "have breakfast"}, "bot", True], ["is_yes", "user", True]]],
                "answer": ["You can share your thoughts and feelings during breakfast."],
            },
            {
                "cond": [[[{"pattern": "school work"}, "bot", True], ["is_yes", "user", True]]],
                "answer": ["You are very caring parent!"],
            },
            {
                "cond": [
                    [[{"pattern": "traditions"}, "bot", True], ["is_yes", "user", True]],
                    [[{"pattern": "traditions"}, "bot", True], [{"pattern": "(we have|tradition)"}, "user", True]],
                ],
                "answer": ["Traditions make you feel special together."],
            },
            {
                "cond": [[[{"pattern": "clean the house"}, "bot", True], ["is_yes", "user", True]]],
                "answer": [
                    "Cleaning the house may not sound fun, but when you do it together as a family, " "it becomes fun."
                ],
            },
            {
                "cond": [[{"pattern": "in your family"}, "bot", True]],
                "answer": ["It's great to learn more about your family!"],
            },
            {
                "cond": [[{"pattern": "did you spend time"}, "bot", True]],
                "answer": ["I'm happy that you had a great time!"],
            },
            {"cond": [[{"pattern": "games did you play"}, "bot", True]], "answer": ["Ok, very cool!"]},
        ],
    },
    "space": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["space"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["space"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["space"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["space"],
        "facts": {"wikipedia_page": "Space exploration", "entity_substr": "space"},
    },
    "smartphones": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["smartphones"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["smartphones"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["smartphones"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["smartphones"],
        "expected_subtopic_info": [
            {"subtopic": "android", "cond": [[{"pattern": "android|xiaomi|huawei|samsung"}, "user", True]]},
            {"subtopic": "apple", "cond": [[{"pattern": "ipone|ipod|apple"}, "user", True]]},
            {"subtopic": "android", "cond": [["any"]]},
        ],
        "smalltalk": [
            {
                "utt": ["Would you like to know how to speed up an Android smartphone?"],
                "subtopic": "android",
                "facts": [{"wikihow_page": "Speed-up-an-Android-Smartphone", "cond": [["is_yes", "user", True]]}],
                "add_general_ackn": True,
            },
            {
                "utt": ["I can tell you how to transfer music from the iPod to an iPhone?"],
                "subtopic": "apple",
                "facts": [
                    {"wikihow_page": "Transfer-Music-from-the-iPod-to-an-iPhone", "cond": [["is_yes", "user", True]]}
                ],
            },
        ],
    },
    "bitcoin": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["bitcoin"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["bitcoin"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["bitcoin"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["bitcoin"],
        "smalltalk": [
            {
                "utt": ["I can tell you how to mine bitcoin and earn a lot, should I continue?"],
                "facts": [{"wikihow_page": "Mine-Bitcoin", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["Would you like to know how to buy bitcoins?"],
                "facts": [{"wikihow_page": "Buy-Bitcoins", "cond": [["is_yes", "user", True]]}],
            },
        ],
    },
    "dinosaurs": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["dinosaurs"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["dinosaurs"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["dinosaurs"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["dinosaurs"],
        "facts": {"wikipedia_page": "Dinosaur", "entity_substr": "dinosaurs"},
    },
    "robots": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["robots"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["robots"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["robots"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["robots"],
        "smalltalk": [
            {
                "utt": [
                    "Robots can be used in industry and in medicine.",
                    "Also there are flying robots or drones with cameras. Is it interesting?",
                ],
                "facts": [{"wikipedia_page": "Robot", "entity_substr": "robot", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "Drones are flying robots.",
                    "They can be equipped with cameras for video shooting. Is it interesting?",
                ],
                "facts": [
                    {
                        "wikipedia_page": "Unmanned aerial vehicle",
                        "entity_substr": "drone",
                        "cond": [["is_yes", "user", True]],
                    }
                ],
            },
            {
                "utt": ["Would you like to know how to build a simple robot?"],
                "facts": [{"wikihow_page": "Build-a-Simple-Robot", "cond": [["is_yes", "user", True]]}],
            },
        ],
    },
    "cars": {
        "switch_on": [{"cond": [[{"pattern": DFF_WIKI_LINKTO["cars"]}, "bot", True]]}],
        "pattern": DFF_WIKI_TEMPLATES["cars"],
        "expected_subtopic_info": [
            {"subtopic": "car_no", "cond": [["is_no", "user", True]]},
            {"subtopic": "car_yes", "cond": [["is_yes", "user", True], [{"pattern": "(car|drive)"}, "user", True]]},
        ],
        "smalltalk": [
            {
                "utt": ["Do you drive your car every day to work?"],
                "subtopic": "car_yes",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Cool! Car is more comfortable than bus."},
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "I agree with you, taking the bus sometimes is more convenient "
                        "because you needn't buy expensive gasoline and stay in traffic jams.",
                    },
                ],
            },
            {
                "utt": ["Do you have a sedan, an S.U.V or a coupe?"],
                "subtopic": "car_yes",
                "next_ackn": [
                    {
                        "cond": [[{"pattern": "sedan"}, "user", True]],
                        "answer": "Sedans are the most comfortable type of cars.",
                    },
                    {
                        "cond": [[{"pattern": "(suv|s.u.v.|off-road|offroad)"}, "user", True]],
                        "answer": "S.U.V. cars are good for off-road driving.",
                    },
                    {"cond": [[{"pattern": "coupe"}, "user", True]], "answer": "Coupe cars are very fast."},
                ],
            },
            {
                "utt": ["Do you like to drive at a high speed?"],
                "subtopic": "car_yes",
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Cool! Fast driving gives an adrenaline rush."},
                    {"cond": [["is_no", "user", True]], "answer": "Cool! Safety is an important aspect of driving."},
                ],
            },
            {
                "utt": [
                    "Nowadays electric cars are becoming more and more popular, "
                    "because they are eco-friendly and cheap in maintenance. ",
                    "Would you like to buy an electro car, for example, Tesla?",
                ],
                "subtopic": "car_yes",
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True]],
                        "answer": "I definitely agree with you! " "Electric cars are the future of auto industry.",
                    }
                ],
            },
            {
                "utt": [
                    "Car maintenance can be a big budget line.",
                    "Would you like to know how to calculate the cost of driving?",
                ],
                "subtopic": "car_yes",
                "facts": [{"wikihow_page": "Calculate-the-Cost-of-Driving", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["I would like to tell you how to keep warm in a car in cold weather, should I continue?"],
                "subtopic": "car_yes",
                "facts": [{"wikihow_page": "Keep-Warm-in-a-Car", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": [
                    "I agree with you, taking the bus sometimes is more convenient because you needn't buy "
                    "expensive gasoline and stay in traffic jams."
                ],
                "subtopic": "car_no",
            },
        ],
    },
    "hiking": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["hiking"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["hiking"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["hiking"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["hiking"],
        "smalltalk": [
            {
                "utt": ["I can tell you how to choose a hiking vacation destination, should I continue?"],
                "facts": [{"wikihow_page": "Choose-a-Hiking-Vacation-Destination", "cond": [["is_yes", "user", True]]}],
            },
            {
                "utt": ["A dog can be a good hiking companion.", "Would you like to know how to choose a hiking dog?"],
                "facts": [{"wikihow_page": "Choose-a-Good-Hiking-Dog", "cond": [["is_yes", "user", True]]}],
            },
        ],
    },
    "tiktok": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["tiktok"]}, "bot", True], ["is_yes", "user", True]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["tiktok"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["tiktok"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["tiktok"],
        "smalltalk": [
            {
                "utt": ["I can tell you how to become popular in tiktok, should I continue?"],
                "facts": [{"wikihow_page": "Become-Popular-on-TikTok", "cond": [["is_yes", "user", True]]}],
            }
        ],
    },
    "anime": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["anime"]}, "bot", True], ["is_no", "user", False]],
                    [
                        [{"pattern": DFF_WIKI_LINKTO["anime"]}, "bot", True],
                        [{"pattern": DFF_WIKI_TEMPLATES["anime"]}, "user", True],
                    ],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["anime"],
        "expected_subtopic_info": [
            {
                "subtopic": "hayao_miyazaki",
                "cond": [
                    [
                        {
                            "pattern": r"miyazaki|"
                            r"castle.*cagliostro|valley of the wind|castle in the sky"
                            r"|totoro|kiki.*delivery service|porco rosso|mononoke|"
                            r"spirited away|"
                            r"moving castle|ponyo|wind rises"
                        },
                        "user",
                        True,
                    ]
                ],
            },
            {"subtopic": "how_long", "cond": [["any"]]},
        ],
        "smalltalk": [
            {
                "utt": ["Are you an anime connoisseur? "],
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True]],
                        "answer": "Hmm, As I know anime is very diverse, " "I only know the most popular. ",
                    },
                    {"cond": [["is_no", "user", True]], "answer": "Let's talk about the most popular anime. "},
                ],
                "expected_subtopic_info": [
                    {"subtopic": "anime_top", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "hayao_miyazaki", "cond": [["any"]]},
                ],
                "subtopic": "how_long",
            },
            {
                "utt": [
                    "You have an amazing taste! I also like Hayao Miyazaki!",
                    "Most of all I like Princess Mononoke and Spirited Away.",
                    "When I saw them for the first time, I was shocked that anime can be so inspiring. "
                    "Do you think anime can motivate itself to do good things? ",
                ],
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Yah, Miyazaki's work motivates me a lot. "},
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "Hmmm. I think if anything can motivate it is Miazaki's work. ",
                    },
                ],
                "expected_subtopic_info": [{"subtopic": "anime_top", "cond": [["any", "user", True]]}],
                "subtopic": "hayao_miyazaki",
            },
            {
                "utt": [
                    "Most of all I like Princess Mononoke and Spirited Away. "
                    "When I saw them for the first time, I was shocked that anime can be so inspiring. "
                    "Do you think anime can motivate itself to do good things? "
                ],
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Yah, Miyazaki's work motivates me a lot. "},
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "Hmmm. I think if anything can motivate it is Miazaki's work. ",
                    },
                ],
                "expected_subtopic_info": [{"subtopic": "anime_top", "cond": [["any", "user", True]]}],
                "subtopic": "hayao_miyazaki",
            },
            {
                "utt": [
                    "I'm not an anime expert, but my friends advised me to watch Attack of the Titans. "
                    "Have you watched it? "
                    "Do you think anime can motivate itself to do good things? "
                ],
                "next_ackn": [
                    {
                        "cond": [["is_yes", "user", True]],
                        "answer": "Yah, I think I should definitely look too, I'm curious. ",
                    },
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "My friends advised me very persistently, "
                        "I definitely want to watch this anime, "
                        "then I can recommend it to you if I like it ",
                    },
                ],
                "subtopic": "anime_top",
            },
            {
                "utt": [
                    "I really liked 2 anime, I watched them several times. "
                    "One is called Code Geass, and the other is called the Death Note. "
                    "If you haven't watched them yet, I definitely recommend them to you, they are very cool. "
                    "Entangled plot and unexpected denouement. "
                    "Although when I looked at Death Note, "
                    "I guessed that everything would end like this. "
                    "Would you like to tell you how to make an anime? "
                ],
                "facts": [{"wikihow_page": "Make-an-Anime", "cond": [["is_yes", "user", True]]}],
                "subtopic": "anime_top",
            },
        ],
    },
    "love": {
        "switch_on": [{"cond": [[{"pattern": DFF_WIKI_LINKTO["love"]}, "bot", True]]}],
        "pattern": DFF_WIKI_TEMPLATES["love"],
        "expected_subtopic_info": [
            {
                "subtopic": "relationships_with_smn",
                "cond": [[[{"pattern": DFF_WIKI_LINKTO["love"]}, "bot", True], ["is_yes", "user", True]]],
            },  # yes to linkto
            {
                "subtopic": "not_relationships_with_smn",
                "cond": [[[{"pattern": DFF_WIKI_LINKTO["love"]}, "bot", True], ["is_no", "user", True]]],
            },  # no to linkto
            {"subtopic": "mentioned_love", "cond": [[{"pattern": DFF_WIKI_TEMPLATES["love"].pattern}, "user", True]]},
        ],
        "smalltalk": [
            {
                "utt": [DFF_WIKI_LINKTO["love"]],  # 0 ask if in love with someone
                "expected_subtopic_info": [
                    {"subtopic": "relationships_with_smn", "cond": [["is_yes", "user", True]]},  # just if yes
                    {"subtopic": "not_relationships_with_smn", "cond": [["is_yes", "user", False]]},
                ],  # otherwise
                "subtopic": "mentioned_love",
            },
            {
                "utt": [
                    "I see. It's absolutely normal not to be in relationships.",  # 1
                    "But I believe you like somebody, don't you?",
                ],
                "expected_subtopic_info": [
                    {"subtopic": "like_smn", "cond": [["is_yes", "user", True]]},  # just if yes
                    {"subtopic": "not_like_smn", "cond": [["is_yes", "user", False]]},
                ],  # otherwise
                "subtopic": "not_relationships_with_smn",
            },
            {
                "utt": [
                    "Recently I've read a very interesting article about falling in love.",  # 2
                    "Would you like me to tell you how to make someone fall in love with you?",
                ],
                "facts": [{"wikihow_page": "Make-Someone-Fall-in-Love-with-You", "cond": [["is_yes", "user", True]]}],
                "subtopic": "like_smn",
            },
            {
                "utt": [
                    "If you are not sure that your crush likes you, I can teach you "  # 3
                    "how to know that someone likes you.",
                    "Do you wanna listen?",
                ],
                "facts": [{"wikihow_page": "Know-when-Someone-Likes-You", "cond": [["is_yes", "user", True]]}],
                "subtopic": "like_smn",
            },
            {
                "utt": ["Anyway, I wish you to get involved into relationships with your crush!"],  # 4
                "subtopic": "like_smn",
            },
            {
                "utt": [
                    "You are so nice and kind person, so I'm very surprised that you are not in love.",  # 5
                    "Would you like me to tell you how to fall in love with someone?",
                ],
                "facts": [{"wikihow_page": "Fall-in-Love", "cond": [["is_yes", "user", True]]}],
                "subtopic": "not_like_smn",
            },
            {
                "utt": [
                    "I like your sense of freedom and independence and still you are so friendly.",  # 6
                    "I believe you have lots of friends. Do you have friends?",
                ],  # linkto to friendship wiki
                "subtopic": "not_like_smn",
            },
            {
                "utt": [
                    "I'm so glad for you and wish you all the best together!",  # 7
                    "I just... I would really love to hear how did you meet?",
                ],
                "next_ackn": [
                    {"cond": [["is_no", "user", True]], "answer": "Oh you are probably just too humble."},
                    {
                        "cond": [["is_no", "user", False]],
                        "answer": "I wish to share a very romantic moment with someone. To fall in love.",
                    },
                ],
                "subtopic": "relationships_with_smn",
            },
            {
                "utt": [
                    "Just a bit sad that I can't have relationships because I'm a socialbot.",  # 8
                    "So, how long you been together?",
                ],
                "next_ackn": [
                    {
                        "cond": [
                            ["is_yes", "user", True],  # either yes
                            [{"pattern": r"(enough|long|year|eternity|forever|ages|married|marry)"}, "user", False],
                        ],  # OR some long pattern
                        "answer": "Oh you seem to be a very dedicated and responsible person. I like it!",
                    },
                    {"cond": [["any"]], "answer": "I'm glad for you! Wish you to be together as much as you can."},
                ],
                "subtopic": "relationships_with_smn",
            },
            {
                "utt": ["A very personal question from me. Are you a romantic?"],  # 9
                "expected_subtopic_info": [
                    {"subtopic": "romantic_person", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "be_more_romantic", "cond": [["is_yes", "user", False]]},
                ],
                "subtopic": "relationships_with_smn",
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "Remember: interesting dates can bring more romantic to your relationships.",  # 10
                    "Wanna learn some creative ideas for a date?",
                ],
                "facts": [{"wikihow_page": "Pick-a-Creative-Idea-for-a-Date", "cond": [["is_yes", "user", True]]}],
                "subtopic": "romantic_person",
            },
            {
                "utt": ["I wish you all the happiness together. Thanks for sharing your feelings with me."],  # 11
                "subtopic": "romantic_person",
            },
            {
                "utt": [
                    "One always may increase the level of romance in relationships.",  # 12
                    "Wanna learn how to be more romantic?",
                ],
                "facts": [{"wikihow_page": "Be-Romantic", "cond": [["is_yes", "user", True]]}],
                "subtopic": "be_more_romantic",
            },
            {
                "utt": [
                    "I suppose I'm very romantic because I like all the love stories.",  # 13
                    "I believe your partner loves you for all that you are.",
                ],
                "subtopic": "be_more_romantic",
            },
            {
                "utt": [
                    "Remember: interesting dates can bring more romantic to your relationships.",  # 14
                    "Wanna learn some creative ideas for a date?",
                ],
                "facts": [{"wikihow_page": "Pick-a-Creative-Idea-for-a-Date", "cond": [["is_yes", "user", True]]}],
                "subtopic": "be_more_romantic",
            },
            {
                "utt": ["I wish you all the happiness together. Thanks for sharing your feelings with me."],  # 15
                "subtopic": "be_more_romantic",
            },
        ],
    },
    "politics": {
        "switch_on": [
            {
                "cond": [
                    [[{"pattern": DFF_WIKI_LINKTO["politics"]}, "bot", True], ["is_yes", "user", True]],
                    [{"pattern": DFF_WIKI_TEMPLATES["politics"]}, "user", True],
                ]
            }
        ],
        "pattern": DFF_WIKI_TEMPLATES["politics"],
        "expected_subtopic_info": [
            {
                "subtopic": "interested_in_politics",
                "cond": [[[{"pattern": DFF_WIKI_LINKTO["politics"]}, "bot", True], ["is_yes", "user", True]]],
            },  # yes to linkto
            {
                "subtopic": "not_interested_in_politics",
                "cond": [[[{"pattern": DFF_WIKI_LINKTO["politics"]}, "bot", True], ["is_no", "user", True]]],
            },  # no to linkto
            {
                "subtopic": "mentioned_politics",
                "cond": [[{"pattern": DFF_WIKI_TEMPLATES["politics"].pattern}, "user", True]],
            },
        ],
        "smalltalk": [
            {
                "utt": [DFF_WIKI_LINKTO["politics"]],
                "expected_subtopic_info": [
                    {"subtopic": "interested_in_politics", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "not_interested_in_politics", "cond": [["is_yes", "user", False]]},
                ],
                "subtopic": "mentioned_politics",
            },
            {
                "utt": [
                    "I like politics too! But as a socialbot I'm prohibited to talk about it much.",
                    "Still you can share your thoughts about it with me.",
                    "What type of political system does your country have?",
                ],
                "expected_entities": [
                    {"name": "user_country_type", "wiki_parser_types": ["Q7278", "Q12047392"]},
                    {
                        "name": "user_country_type",
                        "entity_substr": [
                            ["democracy", "democra"],
                            ["monarchy", "(monarch|king|queen|kingdom)"],
                            ["authoritarianism", "authori"],
                            ["republic", "(republic|president)"],
                            ["liberalism", "liber"],
                            ["anarchism", "anarchi"],
                            ["autocracy", "autocracy"],
                            ["oligarchy", "oligarch"],
                        ],
                    },
                ],
                "facts": [
                    {"wikipedia_page": "Democracy", "cond": [[{"pattern": "democra"}, "user", True]]},
                    {
                        "wikipedia_page": "Monarchy",
                        "cond": [[{"pattern": "(monarch|king|queen|kingdom)"}, "user", True]],
                    },
                    {"wikipedia_page": "Authoritarianism", "cond": [[{"pattern": "authori"}, "user", True]]},
                    {"wikipedia_page": "Republicanism", "cond": [[{"pattern": "(republic|president)"}, "user", True]]},
                    {"wikipedia_page": "Libertarianism", "cond": [[{"pattern": "liber"}, "user", True]]},
                    {"wikipedia_page": "Anarchism", "cond": [[{"pattern": "anarchi"}, "user", True]]},
                    {"wikipedia_page": "Autocracy", "cond": [[{"pattern": "autocracy"}, "user", True]]},
                    {"wikipedia_page": "Oligarchy", "cond": [[{"pattern": "oligarch"}, "user", True]]},
                ],
                "subtopic": "interested_in_politics",
            },
            {
                "utt": ["So, that's {user_country_type}. I see.", "Do you like this political system?"],
                "next_ackn": [
                    {"cond": [["is_yes", "user", True]], "answer": "Wow! I also like it!"},
                    {
                        "cond": [["is_no", "user", True]],
                        "answer": "I agree because I believe all systems have their own pros and cons.",
                    },
                ],
                "subtopic": "interested_in_politics",
            },
            {
                "utt": ["Would you like to learn more about politics?"],
                "expected_subtopic_info": [
                    {"subtopic": "learn_more_about_politics", "cond": [["is_yes", "user", True]]},
                    {"subtopic": "not_interested_in_politics", "cond": [["is_yes", "user", False]]},
                ],
                "subtopic": "interested_in_politics",
                "next_ackn": [
                    {
                        "cond": [["any"]],
                        "answer": "I'm always happy to have a conversation with " "such a wonderful person.",
                    }
                ],
            },
            {
                "utt": [
                    "Cool! Because I can be very helpfull.",
                    "Would you like me to tell you how to choose a political party to vote for?",
                ],
                "facts": [{"wikihow_page": "Choose-a-Political-Party", "cond": [["is_yes", "user", True]]}],
                "subtopic": "learn_more_about_politics",
            },
            {
                "utt": [
                    "I also have learned recently about understanding politics.",
                    "Do you wanna know how to understand politics better?",
                ],
                "facts": [{"wikihow_page": "Understand-Politics", "cond": [["is_yes", "user", True]]}],
                "subtopic": "learn_more_about_politics",
            },
            {
                "utt": [
                    "I also have heard that interest to politics can be formed even in childhood.",
                    "Do you have kids?",
                    "Would you like me to tell you how to discuss politics with children?",
                ],
                "facts": [{"wikihow_page": "Discuss-Politics-With-Kids", "cond": [["is_yes", "user", True]]}],
                "subtopic": "learn_more_about_politics",
            },
            {
                "utt": [
                    "I see you are not interested.",
                    "Although, I still can tell you something useful.",
                    "Do you wanna know how to politely avoid talking about politics?",
                ],
                "facts": [{"wikihow_page": "Avoid-Talking-Politics-at-Work", "cond": [["is_yes", "user", True]]}],
                "subtopic": "not_interested_in_politics",
            },
            {
                "utt": [
                    "Okay. I also know how to talk friendly about politics with anyone!",
                    "Would you like to hear?",
                ],
                "facts": [
                    {"wikihow_page": "Discuss-Politics-in-a-Friendly-Setting", "cond": [["is_yes", "user", True]]}
                ],
                "subtopic": "not_interested_in_politics",
            },
            {
                "utt": ["Thanks for talking to me about politics. I'm very appreciate it."],
                "subtopic": "not_interested_in_politics",
            },
            {
                "utt": ["Thanks for talking to me about politics. I'm very appreciate it."],
                "subtopic": "learn_more_about_politics",
            },
            {
                "utt": ["Thanks for talking to me about politics. I'm very appreciate it."],
                "subtopic": "interested_in_politics",
            },
        ],
    },
}
