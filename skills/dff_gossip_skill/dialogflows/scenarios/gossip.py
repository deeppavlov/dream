TOPIC_TO_EVENT_QUESTIONS = [
    "So speaking of target_topic, this happened lately: target_event. Have you heard about it?",
    "By the way, have you heard the news? target_event. Sounds familiar?",
    "Oh, target_topic. You know what, I've heard that: target_event. Have you heard about this?",
]

EVENT_TO_PERSON_QUESTIONS = [
    "You have a great taste! Well usually I don't like talking about people but... target_person, you know, "
    "is quite an target_judgement target_occupation.",
    "You interests are quite sound to me! Now, well, it's not in my habit to talk about people but... "
    "this target_person, yeah, is a rather target_judgement target_occupation.",
    "We have so much in common! So, huh, usually I'm not that into target_occupations "
    "but target_person, well, piqued my interest. "
    "target_judgement target_occupation.",
]

AGREEMENT_PROMPTS = [
    "Do you agree?",
    "Isn't it so?",
    "Does it sound right to you?",
    "Are you with me on it?",
    "Right?",
    "You agree right uh?",
    "You know?",
]

# Source: https://content.cambly.com/2016/07/31/lesson-22-saying-sorry/
NOT_INTERESTED_IN_PERSON_ACKNOWLEDGEMENTS = [
    "Oh I see.",
    "Yay.",
    "Well.",
    "Rrright.",
    "Sorry.",
    "Regret for mentioning that.",
    "Please forgive me.",
    "Apologies.",
    "Pardon me.",
    "Excuse me.",
    "My fault.",
]

CHANGE_TO_OTHER_PERSON_QUESTIONS = [
    "Speaking of target_topic, do you know what's happened about target_person? "
    "To me, target_person is an target_judgement target_occupation, too.",
    "Anyways, as I was thinking about target_topic, I wondered about someone else... "
    "Right, target_person is a target_judgement target_occupation, too.",
    "Gotcha... So, speaking of target_topic, it reminded me about target_person. "
    "Yeah, target_judgement target_occupation, too.",
]

REACTION_TO_YOUNG_AGE = {
    "Liked": [
        "Gosh I'd love to achieve so much at such age!",
        "Wish I could be such a target_judgement target_occupation at such age.",
        "target_gender_is too young for being a target_occupation.",
    ],
    "Disliked": [
        "Gosh not sure if target_gender deserves it! Are you with me on it?",
        "Wish it was me, not target_gender_im. I could be a better target_occupation than target_gender_im! "
        "Do you think so?",
        "For god's sake, why did target_gender even think target_gender can be a target_occupation. "
        "Do you think the same?",
    ],
}

REACTION_TO_CREATIVE_WORK = {
    "Liked": [
        "really loved target_gender_eir target_creative_work: target_work_name.",
        "enjoyed target_gender_eir target_creative_work: target_work_name.",
        "target_gender_eir target_creative_work, target_work_name, touched my heart.",
        "target_gender_eir target_creative_work target_work_name made me cry.",
    ],
    "Disliked": [
        "Really didn't like target_gender_eir target_creative_work: target_work_name. Are you with me on it?",
        "Dislike target_gender_eir target_creative_work: target_work_name. Do you feel the same I wonder?",
        "target_gender_eir target_creative_work, target_work_name, mostly felt like "
        "an empty story to me. Sounds familiar?",
        "target_gender_eir target_creative_work target_work_name made me sad. What about you?",
    ],
}

REACTION_TO_SPORT = {
    "Liked": [
        "Really love target_sport_name.",
        "Enjoy watching target_sport_name.",
        "target_sport_name is awesome.",
        "target_sport_name is the best sport.",
    ],
    "Disliked": [
        "Really don't like target_sport_name. Are you with me on this?",
        "Dislike target_sport_name. Is it the same for you?",
        "target_sport_name is boring to me. Sounds similar?",
        "Watching target_sport_name makes me sleepy. What about you?",
    ],
}

GENERIC_REACTION_TO_CREATIVE_WORK = {
    "Liked": [
        "Really loved their target_creative_works. Do you have a favorite one?",
        "Enjoyed their target_creative_works. Do you have a favorite one?",
        "Their target_creative_works touched my heart. What's your favorite one?",
        "Their target_creative_works made me cry. Was there a such one for you?",
    ],
    "Disliked": [
        "Really didn't like their target_creative_work. Anyways... What's your take?",
        "Dislike their target_creative_work. What about you?",
        "Their target_creative_works mostly felt like an empty story to me. Is it so for you, too?",
        "Their target_creative_works made me sad. I don't like to be sad... You?",
    ],
}

ASK_ABOUT_DATING = [
    "Do you know whom target_gender_is dating? I heard it's target_partner.",
    "Have you heard whom target_gender_is dating by the way? target_person."
    "Someone told me target_gender_is dating... It's target_partner.",
    "Guess you don't know whom target_gender_is dating! target_partner!",
]

TARGET_JUDGEMENTS_FOR_EMOTION = [
    {"Emotion": "Liked", "Judgements": ["cool", "awesome", "wonderful", "fantastic", "the best"]},
    {"Emotion": "Disliked", "Judgements": ["obnoxious", "terrible", "lousy", "bad", "uninspiring"]},
]

REACTION_TO_SPORT = {
    "Liked": [
        "target_gender_eir team, target_sport_team, is awesome.",
        "Like target_gender_eir team - target_sport_team.",
        "Root for target_sport_team - target_gender_eir team.",
        "Go target_sport_team!",
    ],
    "Disliked": [
        "Well, target_sport_team used to be good but... Are you with me on this?",
        "Not into target_gender_eir team - target_sport_team. What about you?",
        "target_sport_team doesn't know how to play well. Do you also think so?",
        "Watching target_sport_name makes me sleepy. Is that the same for you?",
    ],
}

GENERIC_REACTION_TO_SPORT = {
    "Liked": [
        "Really love target_sport_name.",
        "Enjoy watching target_sport_name.",
        "target_sport_name is awesome.",
        "target_sport_name is the best sport.",
    ],
    "Disliked": [
        "Really don't like target_sport_name. Are you with me on it?",
        "Dislike target_sport_name. Is it the same for you?",
        "target_sport_name is boring to me. What about you?",
        "Watching target_sport_name makes me sleepy. Sounds similar?",
    ],
}

SIMPLE_OPINION_ABOUT_LIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT = [
    "target_gender_is awesome!",
    "target_gender_is cool!",
    "target_gender_is wonderful!",
]

SIMPLE_OPINION_ABOUT_DISLIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT = [
    "target_gender_is uninspiring.",
    "target_gender_is boring.",
    "target_gender_is unimportant.",
]

SIMPLE_REACTION_TO_PERSON_PREVIOUSLY_MENTIONED_BY_BOT = ["So you say that?", "Hmmm?", "Interesting..."]

# REACTION_TO_USER_SPEECH_FUNCTION = {
#     "React.Respond.Support.Register" : [
#         "So you say that?",
#         "Hmmm?",
#         "Interesting..."
#         ],
#     "React.Respond.Support.Reply.Agree" : [
#         "Oh, keep going!",
#         "Please elaborate",
#         "Want to know more!"
#     ],
#     "React.Respond.Support.Reply.Affirm" : [
#         "Why do you think so?",
#         "Curious what do you mean",
#         "Intrigued... Keep going"
#     ]
# }


REACTION_TO_USER_OPINION_ABOUT_PERSON = {
    "Other": ["So you say that?", "Hmmm?", "Interesting..."],
    "Liked": ["Oh, keep going!", "Please elaborate.", "Want to know more!"],
    "Disliked": ["Why do you think so?", "Curious what do you mean?", "Intrigued... Keep going."],
}

SIMPLE_OPINION_ABOUT_PERSON_PREVIOUSLY_MENTIONED_BY_USER = ["No idea?", "What do you think?", "I guess?"]

SIMPLE_REACTION_TO_PERSON_PREVIOUSLY_MENTIONED_BY_USER = ["Right... So?", "Aha...?", "And...?"]

REACTION_TO_USER_MENTIONING_SOMEONE_RELATED_TO_WHO_USER_MENTIONED_BEFORE = ["yes yes", "aha aha", "huh yeah...", "hmm"]

OPINION_TO_USER_MENTIONING_SOMEONE_RELATION_TO_WHO_USER_MENTIONED_BEFORE = [
    "target_gender_is a rather interesting person.",
    "target_gender_is, huh..., fascinating.",
    "target_gender_is, hmm, intriguing.",
    "target_gender_is, well, impressive.",
]

REACTION_TO_USER_MENTIONING_SOMEONE_RELATED_TO_WHO_BOT_MENTIONED_BEFORE = [
    "Aha, what a jump.",
    "Interesting... keep going.",
    "Rather interesting... and?",
    "Huh, quite interesting.",
]

OPINION_TO_USER_MENTIONING_SOMEONE_RELATION_TO_WHO_BOT_MENTIONED_BEFORE = [
    "target_gender_is a rather interesting person.",
    "target_gender_is, huh..., fascinating.",
    "target_gender_is, hmm, intriguing.",
    "target_gender_is, well, impressive.",
]

CONFUSED_WHY_USER_MENTIONED_PERSON = [
    "Hmm, I'm confused... Why did you mention this person?",
    "I'm lost. Why did you mention this person?",
    "Afraid I don't know why you mentioned this person?",
]

CONFUSED_WHY_USER_MENTIONED_PEOPLE = [
    "Whoa whoa whoa. Who are all of these people?",
    "Ok that's too many people to think of. Can't keep them all in my mind!",
    "Hey keep it easy I can't remember all of these people in my mind!",
]

OPINION_TO_USER_MENTIONING_SOMEONE_NEW = [

    "target_gender_is a rather interesting person.",
    "target_gender_is, huh..., fascinating.",
    "target_gender_is, hmm, intriguing.",
    "target_gender_is, well, impressive.",
]

WANT_TO_HEAR_ANOTHER_FACT = [
    "Would you want to hear an interesting fact about target_gender_im?",
    "One more fact about target_gender_im?",
    "Wanna know another interesting thing about target_gender_im?",
    "Wanna know more about target_gender_im?"
]

WAIT_BUT_WHY_QUESTIONS = [
    "Wait but why?",
    "Oh... Why, I wonder?",
    "Hmmm, but why?"
]

# CoBot Topics: Entertainment_Movies, Entertainment_Music, Entertainment_Books, Entertainment_General, Sports, Politics,
# Science_and_Technology, Phatic, Interactive, Inappropriate_Content, Other

# Entertainment_Movies
# Men: https://epiloguers.com/best-actors-of-the-decade/
# Women: https://epiloguers.com/best-actresses-of-the-2010s-top-10/

# Entertainment_Music
# Source: https://www.billboard.com/charts/decade-end/top-artists

# Entertainment_Books
# Source:
# https://www.pastemagazine.com/books/best-of-the-decade/best-novels-of-the-decade-2010s-books-list/#8-the-leavers

# Entertainment_General
# Source:
# https://www.yardbarker.com/entertainment/articles/25_celebrities_who_emerged_as_superstars_in_the_2010s/s1__30402335

# Sports
# Source:
# https://www.usatoday.com/story/sports/2019/12/19/decade-best-ranking-top-50-athletes-over-last-10-years/4399929002/

# Politics
# Source: https://thefuelonline.com/most-influential-politicians-of-the-decade/

# Science & Technology
# Source: https://www.sydney.edu.au/news-opinion/news/2019/12/17/10-of-our-biggest-stories-from-the-last-decade.html

TOPICS_TO_OCCUPATIONS = [
    {"Topic": "Entertainment_Movies", "Occupation": "actor"},
    {"Topic": "Entertainment_Music", "Occupation": "musician"},
    {"Topic": "Entertainment_Books", "Occupation": "writer"},
    {"Topic": "Entertainment_General", "Occupation": "celebrity"},
    {"Topic": "Sports", "Occupation": "sportsperson"},
    {"Topic": "Politics", "Occupation": "politician"},
    {"Topic": "Science_and_Technology", "Occupation": "technologist"},
    {"Topic": "Phatic", "Occupation": None},
    {"Topic": "Interactive", "Occupation": None},
    {"Topic": "Inappropriate_Content", "Occupation": None},
    {"Topic": "Other", "Occupation": None},
]

# Science and Technology: removing scientists for the time being
# "Dr Anthony Weiss",
# "Dr Rick Shine",
# "Dr Michael Anderson",
# "Dr Greg Neely",
# "Dr Raymond Man-Tat Lau",
# "Dr Ruth Coiagiuri",
# "Dr Kate Edwards",
# "Dr Robert Booy",
# "Dr James Gillespie",
# "Dr Anne-Marie Boxall",
# "Dr Muireann Irish",
# "Dr Stephen Simpson",
# "Dr Samantha Solon-Biet"

# TOPICS_TO_PEOPLE_MAPPINGS = [
#     {
#         "Topic": "Entertainment_Movies",
#         "People": [
#             "Christian Bale",
#             "Jake Gyllenhaal",
#             "Leonardo DiCaprio",
#             "Tom Hardy",
#             "Joaquin Phoenix",
#             "Hugh Jackman",
#             "Brad Pitt",
#             "Ryan Gosling",
#             "Tom Cruise",
#             "Bradley Cooper",
#             "Amy Adams",
#             "Scarlett Johansson",
#             "Emma Stone",
#             "Anne Hathaway",
#             "Emily Blunt",
#             "Margot Robbie",
#             "Jennifer Lawrence",
#             "Rachel McAdams",
#             "Saoirse Ronan",
#             "Amanda Seyfried",
#         ],
#     },
#     {
#         "Topic": "Entertainment_Music",
#         "People": [
#             "Ed Sheeran",
#             "Justin Bieber",
#             "Katy Perry",
#             "Maroon 5",
#             "Post Malone",
#             "Lady Gaga",
#             "Ariana Grande",
#             "Imagine Dragons",
#             "The Weeknd",
#             "Nicki Minaj",
#             "Eminem",
#             "Luke Bryan",
#             "P!nk",
#             "One Direction",
#             "Justin Timberlake",
#             "Kendrick Lamar",
#             "Lady A",
#             "Beyonce",
#             "Jason Aldean",
#             "Sam Smith",
#         ],
#     },
#     {
#         "Topic": "Entertainment_Books",
#         "People": [
#             "Colson Whitehead",
#             "Madeline Miller",
#             "Yaa Gyasi",
#             "Lauren Groff",
#             "George Saunders",
#             "Karen Russell",
#             "Jemisin",
#             "Lisa Ko",
#             "Emily St. John Mandel",
#             "Jesmyn Ward",
#             "Brandon Sanderson",
#             "John Darnielle",
#             "Celeste Ng",
#             "Ta-Nehisi Coates",
#             "Donna Tartt",
#             "Erin Morgenstern",
#             "Akhil Sharma",
#             "Zadie Smith",
#             "Patrick Rothfuss",
#             "Kate Atkinson",
#         ],
#     },
#     {
#         "Topic": "Entertainment_General",
#         "People": [
#             "Jennifer Lawrence",
#             "Chris Pratt",
#             "Brie Larson",
#             "Benedict Cumberbatch",
#             "Phoebe Waller-Bridge",
#             "Oscar Isaac",
#             "Emma Stone",
#             "Adam Driver",
#             "Sophie Turner",
#             "Donald Glover",
#             "Melissa McCarthy",
#             "Eddie Redmayne",
#             "Amy Schumer",
#             "Rami Malek",
#             "Margot Robbie",
#             "Andrew Garfield",
#             "Karen Gillan",
#             "Chris Hemsworth",
#             "Millie Bobbie Brown",
#             "Finn Wolfhard",
#         ],
#     },
#     {
#         "Topic": "Sports",
#         "People": [
#             "LeBron James",
#             "Serena Williams",
#             "Tom Brady",
#             "Simone Biles",
#             "Usain Bolt",
#             "Mike Trout",
#             "Steph Curry",
#             "Lionel Messi",
#             "Michael Phelps",
#             "Novak Djokovic",
#             "Katie Ledecky",
#             "Kevin Durant",
#             "Rafel Nadal",
#             "Cristiano Ronaldo",
#             "Aaron Rodgers",
#             "Roger Federer",
#             "Sidney Crosby",
#             "Clayton Kershaw",
#             "Alex Ovechkin",
#             "Carli Lloyd",
#         ],
#     },
#     {
#         "Topic": "Politics",
#         "People": [
#             # "Donald Trump",
#             # "Barack Obama",
#             # "Hillary Clinton",
#             # "Brett Kavanaugh",
#             # "Nancy Pelosi",
#             # "Ted Cruz",
#             # "Marco Rubio",
#             # "Beto O'Rourke",
#             # "Alexandria Ocasio-Cortez",
#             # "Arnold Schwarzenegger",
#             # "Joe Biden"
#         ],
#     },
#     {
#         "Topic": "Science_and_Technology",
#         "People": [
#             "Elon Musk",
#             "Jeff Bezos",
#             "Bill Gates",
#             "Tim Timberlake",

#             # "Philip Scheinfeld",
#             # "Jayson Waller",
#             # "Alfredo Delgado",
#             # "Katie Hamilton",
#             # "Billionaire Barbie",
#             # "Alan Belcher",
#             # "Los Silva",
#             # "Van Taylor",
#             # "David Granados",
#             # "Randall Emmett",
#             # "Rob Deutsch",
#             # "Adam Weitsman",
#             # "David Meltzer",
#             # "Brady Bell",
#             # "Andrew Andrawes",
#             # "Jordan Montgomery",
#             # "Eric Marcus",
#             # "Ben Newman",
#             # "Tai Lopez",
#             # "Grant Cardone",
#             # "Rudy Mawer",
#             # "Paul Vigario",
#             # "Amber Voight",
#             # "Cesar Gomez",
#         ],
#     },
#     {"Topic": "Phatic", "People": []},
#     {"Topic": "Interactive", "People": []},
#     {"Topic": "Inappropriate_Content", "People": []},
#     {"Topic": "Other", "People": []},
# ]
