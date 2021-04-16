import re


YOUR_FAVORITE_COMPILED_PATTERN = re.compile("(you|your|yours|you have( a | ))favorite", re.IGNORECASE)


def check_bot_favorites(user_utt):
    return any(
        [
            ("my" not in user_utt) and ("favorite" in user_utt),
            re.search(YOUR_FAVORITE_COMPILED_PATTERN, user_utt)
        ]
    )
