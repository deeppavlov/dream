import re

WHY_MINECRAFT = re.compile(r"\b(why are you here|what are you doing here|what can you do|let's do something|what can you do)", re.IGNORECASE)

BUILD_OBJECT_MINECRAFT = re.compile(r"\bbuild\b", re.IGNORECASE)