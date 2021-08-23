import re
from common.utils import join_sentences_in_or_pattern


YOUR_FAVORITE_COMPILED_PATTERN = re.compile(
    join_sentences_in_or_pattern(
        [
            "(you|your|yours|you have a).*favou?rite",
            r"what( kinds? of | )[a-z ]+ do you (like|love|prefer|adore|fond of)"
        ]
    ),
    re.IGNORECASE
)
