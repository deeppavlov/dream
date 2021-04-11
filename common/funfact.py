import re

from common.utils import is_yes


FUNFACT_COMPILED_PATTERN = re.compile(r"(funfact|fun fact|tell me something)", re.IGNORECASE)


def funfact_requested(annotated_user_utt, annotated_bot_utt):
    turn_on_funfact = FUNFACT_COMPILED_PATTERN.search(annotated_user_utt['text'])
    previous_was_funfact = annotated_bot_utt.get('active_skill', '') == 'dff_funfact_skill'
    agree_next = is_yes(annotated_user_utt)
    flag = turn_on_funfact or (previous_was_funfact and agree_next)
    return flag


FUNFACT_LIST = ['Banging your head against a wall for one hour burns 150 calories.',
                'In Switzerland, it is illegal to own just one guinea pig,'
                ' because guinea pigs are very sociable.',
                'Bananas are curved because they grow towards the sun.',
                'The original London Bridge is now in Arizona.',
                'The smallest bone in your body is in your ear.',
                'In the 16th Century, Turkish women could initiate a divorce '
                'if their husbands didn’t provide them with enough coffee.',
                'Approximately 10-20% of US power outages are caused by squirrels '
                'chewing power lines',
                'Honeybees can recognize human faces.',
                'Pirates wore earrings because they believed it improved their eyesight.']
