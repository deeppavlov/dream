GENRES = {"crime": ["criminal"],
          "drama": ["dramatic"],
          "mystery": ["mystic", "mystical", "mysterious"],
          "thriller": [],
          "action": [],
          "romance": ["romantic", "love story"],
          "comedy": ["comic", "comical", "funny", "humorous", "jocular", "grotesque", "buffo", "entertaining"],
          "short": [],
          "documentary": ["doc", "docs", "record"],
          "adventure": [r"cloak[\s|-]and[\s|-]dagger", r"cloak[\s|-]and[\s|-]sword"],
          "reality-tv": ["reality", r"reality[\s|-]show"],
          "sci-fi": [r"science[\s|-]fiction", r"sci[\s|-]fi"],
          "animation": ["cartoon", 'animated'],
          "family": ["home"],
          "horror": ["nightmare", "awful", r"scar(ing|ed|y/ey)", "spooky", "eer(ie|y)", "uncanny", "fearful"],
          "fantasy": ["fantastic", "phantasy"],
          "history": ["historical"],
          "biography": ["biographical"],
          "news": ["tidings"],
          "music": [],
          "war": ["war(fare|time)", "military", "martial"],
          "western": ["west(erly)?"],
          "talk-show": [r"talk[\s|-]show", 'conversation', "interview", r"chat[\s|-]show"],
          "musical": [],
          "film-noir": [r"film[\s|-]noir"],
          "sport": ["sport(y|s)?"],
          "game-show": [r"game[\s|-]show", r"play[\s|-]show", "competition"],
          "adult": [r"grown[\s|-]up"]
          }

all_genres = list(GENRES.keys()) + sum(list(GENRES.values()), [])
all_genres_str = r"("

for i, genre in enumerate(all_genres):
    all_genres_str += genre
    if i == len(all_genres) - 1:
        all_genres_str += ")"
    else:
        all_genres_str += "|"

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
