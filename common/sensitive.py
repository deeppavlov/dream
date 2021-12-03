from common.utils import get_topics, get_intents


sensitive_topics = {"Politics", "Religion", "Sex_Profanity"}
sensitive_dialogact_topics = {"Politics", "Inappropriate_Content"}
sensitive_all_intents = {
    "Opinion_RequestIntent",  # cobot_dialogact
    "opinion_request",  # intent_catcher
    "open_question_opinion",
    "open_question_personal",
    "yes_no_question",  # midas
}


def is_sensitive_topic_and_request(annotated_uttr):
    cobot_dialogact_topics = set(get_topics(annotated_uttr, which="cobot_dialogact_topics"))
    cobot_topics = set(get_topics(annotated_uttr, which="cobot_topics"))
    sensitive_topics_detected = any([t in sensitive_topics for t in cobot_topics]) or any(
        [t in sensitive_dialogact_topics for t in cobot_dialogact_topics]
    )

    all_intents = get_intents(annotated_uttr, probs=False, which="all")
    sensitive_dialogacts_detected = any([t in sensitive_all_intents for t in all_intents])

    if sensitive_topics_detected and sensitive_dialogacts_detected:
        return True
    return False


def is_badlisted_words(annotated_uttr):
    user_uttr_annotations = annotated_uttr["annotations"]
    blist_topics_detected = sum(user_uttr_annotations.get("badlisted_words", {}).values())
    if blist_topics_detected:
        return True
    return False


def is_sensitive_situation(annotated_uttr):
    if is_sensitive_topic_and_request(annotated_uttr) or is_badlisted_words(annotated_uttr):
        return True
    return False
