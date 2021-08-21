import logging

from zdialog import ZDialog, UserContext, Response

from src import Loader
from src.skill.utils import *
from src.consts import (
    # LOGS_PATH,
    HISTORY_DB_PATH,
    NUM_NEWS_TO_PRINT,
    SIMILARITY_THRESHOLD,
    FIRST_SIMILARITY_THRESHOLD,
    MAX_SUBTOPICS_NUM,
)
from src.content import *
from src.utils import format_output_from_indices


logger = logging.getLogger()
# fh = logging.FileHandler(LOGS_PATH)
# fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
# logger.addHandler(fh)

loader = Loader(logger)
loader.start()


class AlexaPrizeSkill(metaclass=ZDialog):
    logger = logger
    loader = loader
    chat_logs_db_path = HISTORY_DB_PATH
    on_invalid_command = format_output_from_indices([], [], "none", ON_INVALID_COMMAND)
    on_error = format_output_from_indices([], [], "error", ON_ERROR)

    @staticmethod
    def generate_response(
        context: UserContext,
        indices: Union[List[int], List[str]],
        mode: str,
        prefix: str,
        to_state: Optional[str] = "body",
    ) -> Response:
        message = format_output_from_indices(loader.texts, indices, mode, prefix)
        context.payload["news_id"] = list(indices)[0] if indices else None
        return Response(message=message, to_state=to_state)

    def respond_to_headline(context: UserContext) -> Optional[Response]:
        indices, scores = score_news(loader.model, context.message)
        if scores[0] > FIRST_SIMILARITY_THRESHOLD or (
            NUM_NEWS_TO_PRINT > 1 and scores[NUM_NEWS_TO_PRINT - 1] > SIMILARITY_THRESHOLD
        ):
            prefix = HEADLINE_PREFIX(context.raw_message)
            return AlexaPrizeSkill.generate_response(context, indices, "headline", prefix)
        return None

    def respond_to_topic(context: UserContext) -> Optional[Response]:
        topic = parse_topic(loader.lda_model.get_topics(), context.message)
        if topic:
            subtopics = loader.lda_model.get_subtopics_summaries(topic)

            if subtopics:
                context.payload["topic"] = topic
                message = CHOOSE_SUBTOPIC(topic, format_subtopics_summaries(subtopics))
                return AlexaPrizeSkill.generate_response(context, [], "subtopic", message, "subtopic")

            indices = loader.lda_model.subtopics_news_indices[topic][0]
            return AlexaPrizeSkill.generate_response(context, indices, "topic", TOPIC_PREFIX(topic))
        return None

    def respond_to_entity(context: UserContext) -> Optional[Response]:
        if is_list_of_strings(context.raw_request):
            news = score_news_by_entities(loader.ner_index, context.raw_request)
            if news:
                return AlexaPrizeSkill.generate_response(context, news, "entity", ENTITY_PREFIX())
        return None

    @ZDialog.handler(commands=["/start"], priority=2)
    def hello(context: UserContext):
        return AlexaPrizeSkill.generate_response(context, [], "none", HELLO_TEXT, None)

    @ZDialog.handler()
    def top_news(context: UserContext):
        context.message = clean_message(context.message)

        response = AlexaPrizeSkill.respond_to_topic(context)
        if response is None:
            response = AlexaPrizeSkill.respond_to_headline(context)
        if response is None:
            response = AlexaPrizeSkill.respond_to_entity(context)
        if response is None:
            return AlexaPrizeSkill.generate_response(context, loader.latest_news, "none", NOTHING_FOUND)
        return response

    def subtopic_by_id(context: UserContext) -> Optional[Response]:
        message = context.message.strip()
        topic = context.payload["topic"]
        subtopic_id = None

        if re.match(f"^[0-9]*$", message):
            subtopic_id = int(message) - 1

        if subtopic_id is None:
            message = re.split("[^a-z]+", message)
            indices = {"first": 0, "second": 1, "third": 2, "fourth": 3, "fifth": 4, "last": MAX_SUBTOPICS_NUM - 1}

            scores = []
            for w in indices:
                score = get_match_score([w], message)
                scores.append((score, w))

            score, w = max(scores, key=lambda x: x[0])
            if score > 0:
                extra_words_num = (1 - get_match_score(message, [w])) * len(message)
                if extra_words_num < 3:
                    subtopic_id = indices[w]

        subtopics = loader.lda_model.get_subtopics_summaries(topic)
        subtopics = [i for i, _ in subtopics]

        if subtopic_id is not None and 0 <= subtopic_id < len(subtopics):
            subtopic = subtopics[subtopic_id]
            indices = loader.lda_model.subtopics_news_indices[topic][subtopic]

            prefix = SUBTOPIC_PREFIX(subtopic_id + 1, topic)
            return AlexaPrizeSkill.generate_response(context, indices, "subtopic", prefix)
        return None

    def any_subtopic(context: UserContext) -> Optional[Response]:
        message = context.message.strip()
        topic = context.payload["topic"]

        if re.search("(^| )(any( ?one)?|do[ ]?n[`'o ]?t know)( |$)", message):
            subtopics = loader.lda_model.get_subtopics_summaries(topic)

            indices = []
            for i, _ in subtopics:
                indices.extend(loader.lda_model.subtopics_news_indices[topic][i])

            return AlexaPrizeSkill.generate_response(context, indices, "subtopic", TOPIC_PREFIX(topic))
        return None

    def subtopic_by_key_phrases(context: UserContext) -> Optional[Response]:
        topic = context.payload["topic"]
        words = re.split("[^a-zA-Z]+", context.raw_message)

        subtopics = loader.lda_model.get_subtopics_summaries(topic)
        scores = defaultdict(int)
        for i, key_phrases in subtopics:
            for phrase in key_phrases:
                phrase = re.split("[^a-z]+", phrase.lower())
                scores[i] += get_match_score(phrase, words)
                scores[i] += get_match_score(get_paired(phrase), get_paired(words))

        if scores:
            subtopics = [i for i, _ in subtopics]

            subtopic, score = max(scores.items(), key=lambda x: x[1])
            subtopic_id = subtopics.index(subtopic)

            if score > 0.32:
                indices = loader.lda_model.subtopics_news_indices[topic][subtopic]

                prefix = SUBTOPIC_PREFIX(subtopic_id + 1, topic)
                return AlexaPrizeSkill.generate_response(context, indices, "subtopic", prefix)
        return None

    @ZDialog.handler(state="subtopic")
    def subtopic(context: UserContext):
        response = AlexaPrizeSkill.subtopic_by_id(context)
        if response is None:
            response = AlexaPrizeSkill.any_subtopic(context)
        if response is None:
            response = AlexaPrizeSkill.subtopic_by_key_phrases(context)
        if response is None:
            context.message = "last"
            return AlexaPrizeSkill.subtopic_by_id(context)
        return response

    @ZDialog.handler(state="body")
    def body(context: UserContext):
        message = re.split("[^a-z]+", context.message)

        positive = ["yes", "details", "more", "want"]
        negative = ["no", "back", "don", "not", "return"]
        score = get_match_score(positive, message) * len(positive) - get_match_score(negative, message) * len(negative)

        words = positive + negative
        extra_words_num = (1 - get_match_score(message, words)) * len(message)
        if extra_words_num < 3:
            if score > 0.8 and "news_id" in context.payload and context.payload["news_id"] is not None:
                news_id = int(context.payload["news_id"])
                body = format_body(loader.texts[news_id])
                return AlexaPrizeSkill.generate_response(context, [], "body", body, "exit")

            if score < -0.8:
                return AlexaPrizeSkill.generate_response(context, [], "none", HELLO_TEXT, "exit")

        return AlexaPrizeSkill.top_news(context)
