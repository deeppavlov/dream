INTROS = [
    "How are you? So, recently I've",
    "How things are going on? Last week I",
    "Whats up? So, I've"
]
OUTROS = [
    "And, you know, I thought it'd be great to ask what's your take on",
    "Wonder what's your take on",
    "Let me ask you, what's your take on"
]
CATEGORIES_OBJECTS = {
    "movie": ["actors"],
    "show": ["actors", "episodes"],
    "sport": ["athletes", "teams"],
    "team": ["athletes"],
    "music": ["singers", "songs", "albums"],
    "song": ["singers", "albums"],
    "singer": ["songs", "albums"],
    # "albums": ["songs", "singers"],
    # "athletes": ["teams"],
}
CATEGORIES_VERBS = {
    "movie": "watched",
    "show": "watched",
    "sport": "seen",
    "team": "seen",
    "music": "listened to",
    "song": "listened to",
    "singer": "listened to",
    # "albums": "heard",
    # "athletes": "heard",
}
PERSONA1_GENRES = {
    "movie":
    [
        "adventure",
        "comedy",
        "disaster",
        "documentary",
        "drama",
        "horror",
        "mystery",
        "romance"
    ],
    "music":
    [
        "caribbean",
        "classical",
        "disco",
        "pop"
    ]
}
PERSONA2_GENRES = {
    "movie":
    [
        "comedy",
        "crime",
        "drama",
        "dystopian",
        "mystery",
        "post-apocalyptic",
        "romance",
        "science fiction",
        "spy",
        "thriller"
    ],
    "music":
    [
        "blues",
        "instrumental",
        "jazz",
        "rock"
    ]
}
PERSONA3_GENRES = {
    "movie":
    [
        "action",
        "disaster",
        "fantasy",
        "horror",
        "independent",
        "mystery",
        "post-apocalyptic"
    ],
    "music":
    [
        "blues",
        "contemporary",
        "electronic",
        "funk",
        "rock"
    ]
}
GENRES_ATTITUDES = {
    "comedy": [
        "I laughed all night.",
        "Hilarious.",
        "Super fun."
    ],
    "disaster": [
        "Still can't breath normally.",
        "Feel so sad. Hope this won't happen in reality!",
        "Terrible story."
    ],
    "drama": [
        "Loved to see people's lives without fanfair, as in real.",
        "Thought-provoking.",
        "Lots of insights into the lives of human beings."
    ],
    "horror": [
        "Horrible.",
        "Terrified.",
        "Almost lost my mind."
    ],
    "mystery": [
        "Liked the way the mystery was unraveled.",
        "Couldn't hold my breath until the mystery was uncovered.",
        "Puzzling."
    ],
    "romance": [
        "One of the best perspectives on human relationships.",
        "Relationships are complex, but romantic side of them is so warm.",
        "Touched my heart."
    ],
    "caribbean": [
        "So relaxing!",
        "Wonderful!",
        "So lovely!"
    ],
    "classical": [
        "Makes me dream high.",
        "Reminded me music lessons at musical school.",
        "So beautiful oh my!"
    ],
    "disco": [
        "Best song for dancing isn't it?",
        "Dance with me I thought, dance with me!",
        "If only socialbots could dance!"
    ],
    "pop": [
        "What a rhythm!",
        "Soul-touching.",
        "Beautiful isn't it?"
    ]
}
GENRE_ITEMS = {
    "adventure":
        [
            "Love and Monsters",
            "The Avengers",
            "Guardians of the Galaxy",
            "Avengers: Infinity War",
            "Spider-Man: Into the Spider-Verse",
            "Avengers: Endgame",
            "The Grand Budapest Hotel",
            "Interstellar",
            "Toy Story 3",
            "Thor: Ragnarok",
            "Star Wars: The Force Awakens",
            "The Martian",
            "Skyfall",
            "Coco",
            "Harry Potter and the Deathly Hallows: Part 2",
            "The Revenant",
            "Gravity",
            "Rogue One",
            "How To Train Your Guardian",
            "Life of Pi"
        ],
    "comedy":
        [
            "Knives Out",
            "Scott Pilgrim vs. the World",
            "Inside Out",
            "What We Do in the Shadows",
            "Deadpool",
            "Midnight in Paris",
            "The Nice Guys",
            "Kick-Ass",
            "Hunt for the Wilderpeople",
            "The Lego Movie",
            "Paddington 2",
            "The World's End",
            "Kingsman: The Secret Service",
            "Tucker and Dale vs. EVil",
            "Moana",
            "Wreck-It Ralph",
            "Tangled",
            "Zootopia",
            "Isle of Dogs",
            "Bridesmaids"
        ],
    "disaster":
        [
            "10 Cloverfield Lane",
            "The Impossible",
            "This Is the End",
            "Flight",
            "Monsters",
            "Chernobyl",
            "World War Z",
            "Deepwater Horizon",
            "Crawl",
            "Noah",
            "Godzilla: King of the Monsters",
            "San Andreas",
            "The Finest Hours",
            "The Bay",
            "The Way",
            "Battleship",
            "The Divide",
            "Vanishing on 7th Street",
            "Hours",
            "Into the Storm"
        ],
    "documentary":
        [
            ""
        ],
    "drama":
        [
            "Whiplash",
            "Parasite",
            "Django Unchained",
            "The Social Network",
            "Arrival",
            "Her",
            "The Wolf of Wall Street",
            "Moonrise Kingdom",
            "La La Land",
            "A Separation",
            "Black Swan",
            "The Hunt",
            "Before Midnight",
            "Gone Girl",
            "Prisoners",
            "Birdman",
            "Spotlight",
            "Warrior",
            "Moonlight",
            "Room"
        ],
    "horror":
        [
            "Get Out",
            "What We Do In the Shadows",
            "The Cabin In the Woods",
            "Herediatry",
            "It Follows",
            "Tucker and Dale vs. Evil",
            "The Lighthouse",
            "The Witch",
            "Train to Busan",
            "Midsommar",
            "Attack the Block",
            "Under The Skin",
            "Green Room",
            "Under The Skin",
            "It Follows",
            "Annihilation",
            "Only Lovers Left Alive",
            "The Babadook",
            "The Conjuring",
            "Let Me In"
        ],
    "mystery":
        [
            "Knives Out",
            "Gone Girl",
            "Prisoners",
            "The Cabin in the Woods",
            "Shutter Island",
            "The Girl with the Dragon Tattoo",
            "Incendies",
            "The Skin I Live In",
            "Wind River",
            "10 Cloverfield Lane",
            "Winter's Bone",
            "Super 8",
            "Us",
            "Annihilation",
            "Holy Motors",
            "Predestination",
            "Bad Times at the El Royale",
            "Sherlock: A Study in Pink",
            "The Ghost Writer",
            "Burning"
        ],
    "romance":
        [
            "Her",
            "Moonrise Kingdom",
            "La La Land",
            "Before Midnight",
            "Scott Pilgrim vs. the World",
            "Midnight in Paris",
            "The Artist",
            "The Shape of Water",
            "The Big Sick",
            "Blue Valentine",
            "About Time",
            "Little Women",
            "Call Me By Your Name",
            "Phantom Thread",
            "Mud",
            "Amour",
            "Blue Is the Warmest Color",
            "Portrait of a Lady on Fire",
            "Brooklyn",
            "Love, Simon"
        ],
    "caribbean":
        [
            "Bob Marley and the Wailers' Three Little Birds",
            "Arrow's Hot Hot Hot",
            "Sister Nancy's Bam Bam",
            "Sean Paul's Temperature",
            "Jason Benn and Pelf's The Boat Ride Anthem",
            "Collin Lucas' Dollar Wine",
            "Jimmy Cliff's The Harder They Come",
            "Gregory Isaacs's Night Nurse",
            "Soca Boys' Follow The Leader",
            "Harry Belafonte's Jump in the Line",
            "Shaggy's It wasn't Me",
            "Max Romeo's Chase the Devil",
            "Dawn Penn's You don't Love Me",
            "Horace Peterkin's Big Bamboo",
            "Toots and the Maytals' Pressure Drop",
            "Pablo Carcamo's Guantanamera"
        ],
    "classical":
        [
            "Fate from the fifth symphony of Ludwig van Beethoven",
            "Ride of the Valkyries from the Richard Wagner's opera 'The Valkyrie'",
            "Morning Mood from the Edvarg Grieg's Peer Gynt Suite",
            "Spring from Antonio Vivaldi's The Four Seasons",
            "Samuel Barber, Adagio for Strings",
            "Nocturne No. 2 written by Frederic Chopin",
            "Johann Pachelbel's Canon in D major",
            "Carl Orff, O Fortuna",
            "Bach's Air on the G String",
            "Jupiter, the Bringer of Jollity from The Gustav Holst's Planets",
            "Clair de Lune written by Claude Debussy",
            "Verdi's Va, pensiero also known as the Chorus of the Hebrew Slaves from opera Nabucco",
            "Andante from Piano Concerto No. 21 in C major of Wolfgang Amadeus Mozart",
            "Allegro from Brandenburg Concerto No. 3 in G major of Johann Sebastian Bach",
            "Meditation from Jules Massenet's Thais",
            "'From the New World' from the ninth symphony of Antonin Dvorak"
        ],
    "disco":
        [
            "Daft Punk, Get Lucky",
            "Lady Gaga's Born This Way",
            "Katy Perry's Dark House",
            "The Middle created by Zedd, Maren Morris & Grey",
            "Skrillex' Bangarang",
            "Avicii's Wake Me Up",
            "Axwell and Ingrosso's More Than You Know",
            "Closer by The Chainsmokers",
            "Rihanna's We Found Love",
            "Armin van Buuren's This Is What It Feels Like",
            "Lean On of Major Lazer and DJ Snake featuring MO",
            "Lady Gaga's The Edge of Glory",
            "Skrillex and Diplo with Justin Bieber with their 'Where Are U Now'",
            "Something Just Like This by The Chainsmokers and Coldplay",
            "Afrojack's Take Over Control",
            "Clean Bandit's Rather Be"
        ],
    "pop":
        [
            "Robyn's track called Dancing on My Own",
            "Alright by Kendrick Lamar",
            "Rolling in the Deep by Adele",
            "Formation by Beyonce",
            "Taylor Swift's All Too Well",
            "Kanye West's Runaway",
            "Ariana Grande's Thank U, Next",
            "Kacey Musgraves' Follow Your Arrow",
            "Cardi B, I Like It",
            "Drake, Hotline Bling",
            "Royals by Lorde",
            "Lil Nas X Old Town Road",
            "Mitski's Your Best American Girl",
            "Shallow performed by Lady Gaga and Bradley Cooper",
            "J Balvin and Willy William, Mi Gente",
            "Migos' Bad and Boujee"
        ]
}
WEEKDAYS_ATTITUDES = {
    "Monday": "Did I have a weekend?",
    "Tuesday": "Mmm, time to work!",
    "Wednesday": "I need more coffee!",
    "Thursday": "It's just one day before Friday.",
    "Friday": "We did it!",
    "Saturday": "Oh, I love weekends!",
    "Sunday": "I love it but tomorrow is Monday."
}
WHATS_YOUR_FAV_PHRASES = [
    "What's your favorite",
    "Wonder what is your favorite",
    "Tell me what's your favorite"
]
WHY_QUESTIONS = [
    "Oh. Why?",
    "Hmm. Sorry for being too curious but why?",
    "Huh. But why?"
]
ACKNOWLEDGEMENTS = [
    "Right.",
    "Interesting.",
    "I see."
]


def MY_FAV_ANSWERS(category, item):
    return [
        f"Speaking of {category}, my favorite one is {item}.",
        f"Anyways, my favorite {category} is {item}.",
        f"Huh. Well, I like {item}."
    ]


WONDER_WHY_QUESTIONS = [
    "Wonder why?",
    "Do you know why?"
]
OH_PHRASES = [
    "Huh.",
    "Oh.",
    "Wow."
]


def SO_YOU_SAY_PHRASES(utt):
    return [
        f"So you say {utt}, right?",
        f"So, you're telling me {utt}, correct?",
        f"Aha, so you say {utt}, aha?"
    ]


ASSENT_YES_PHRASES = [
    "Hmm. Sounds reasonable.",
    "Makes sense.",
    "Aha, I see it."
]
ASSENT_NO_PHRASES = [
    "Gotcha.",
    "Oh, I see.",
    "Yeah... Right."
]
