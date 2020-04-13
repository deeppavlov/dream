GENRES = {"Genre": ["genre"],
          "Action": ["action"],
          "Adult": ["adult", "grown up"],
          "Adventure": ["adventure", "cloak and dagger", "cloak and sword"],
          "Animation": ["animation", "cartoon", 'animated'],
          "Biography": ["biography", "biographies", "biographical"],
          "Comedy": ["comedy", "comedies", "comic", "comical", "funny", "comedian",
                     "humorous", "jocular", "grotesque", "buffo", "entertaining"],
          "Crime": ["crime", "criminal"],
          "Documentary": ["documentary", "documentaries", "doc", "docs", "record"],
          "Drama": ["drama", "dramatic"],
          "Family": ["family", "families"],
          "Fantasy": ["fantasy", "fantasies", "phantasy", "phantasies", "fantastic", "phantastic"],
          "Film-noir": ["film noir"],
          "Game-show": ["game show", "play show", "competition"],
          "History": ["history", "histories", "historical"],
          "Horror": ["horror", "nightmare", "awful", "scaring", "scared", "scary", "scarey",
                     "spooky", "spookies", "eerie", "eery", "uncanny", "uncannies", "fearful"],
          "Music": ["music"],
          "Musical": ["musical"],
          "Mystery": ["mystery", "mysteries", "mystic", "mystical", "mysterious"],
          "News": ["news", "tidings"],
          "Reality-tv": ["reality tv", "reality", "realities", "reality show"],
          "Romance": ["romance", "romantic", "love story", "love stories"],
          "Sci-fi": ["science fiction", "fiction", "sci fi"],
          "Short": ["short"],
          "Sport": ["sport", "sporty", "sports"],
          "Talk-show": ["talk show", 'conversation', "interview", "chat show"],
          "Thriller": ["thriller"],
          "War": ["war movie", "military", "militaries", "martial"],
          "Western": ["western", "west"]
          }

ALL_GENRES = sum(list(GENRES.values()), [])
ALL_GENRES_STR = r"("

for i, genre in enumerate(ALL_GENRES):
    ALL_GENRES_STR += genre
    if i == len(ALL_GENRES) - 1:
        ALL_GENRES_STR += ")"
    else:
        ALL_GENRES_STR += "|"

# all_genres_str looks like:
# '(crime|drama|mystery|thriller|action|romance)' etc


def list_unique_values(dictionary):
    """
    Return all the unique values from `dictionary`'s values lists except `None`
    and `dictionary`'s keys where these values appeared

    Args:
        dictionary: dictionary which values are lists or None

    Returns:
        dict where keys are unique values from `dictionary` and values
        are keys from `dictionary` where these values appeared
    """
    allel = {}

    for keyel, el in zip(dictionary.keys(), dictionary.values()):
        if el is not None:
            for subel in el:
                if subel in allel:
                    allel[subel] += [keyel]
                else:
                    allel[subel] = [keyel]
    return allel
