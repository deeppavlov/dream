import re

GAMES_COMPILED_PATTERN = re.compile(
    r"(\bvideo ?game|\bgam(e|es|ing)\b|\bplay ?station|\bplaying\b|\bx ?box\b|"
    r"\bplay(ed|ing|s).*\b(tablet|pc|computer)\b)",
    re.IGNORECASE,
)
TRIGGER_PHRASES = ["do you love video games?"]

FALLBACK_ACKN_TEXT = "I like computer games, we can always talk about them when you want."


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def game_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get("text", "").lower() for phrase in TRIGGER_PHRASES])
