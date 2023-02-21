from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component


@register("question_sign_checker")
class QuestionSignChecker(Component):
    """This class adds question sign if it is absent or replaces dot with question sign"""

    def __init__(self, **kwargs):
        pass

    def __call__(self, questions):
        questions_sanitized = []
        for question in questions:
            if not question.endswith("?"):
                if question.endswith("."):
                    question = question[:-1] + "?"
                else:
                    question += "?"
            questions_sanitized.append(question)
        return questions_sanitized
