import logging
import re

from df_engine.core.keywords import TRANSITIONS, RESPONSE, GLOBAL
from df_engine.core import Actor
import df_engine.conditions as cnd
import df_engine.labels as lbl
from . import condition as loc_cnd

from . import response as loc_rsp

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)
SUMMARY = re.compile(
    r"(summary)|(summari(z|s)e)",
    re.IGNORECASE,
)
FUTURE_TASKS = re.compile(
    r"(((future)|(to-?do)|(current)) tasks)|(tasks in progress)",
    re.IGNORECASE,
)
COMPLETED_TASKS = re.compile(
    r"((completed)|(finished)) tasks",
    re.IGNORECASE,
)
DECISIONS = re.compile(
    r"(decide)|(decision)",
    re.IGNORECASE,
)
# тут можно еще спрашивать ллмку. но пока оставляем в таком виде, только побольше вариантов.
# на будущее -- след.итерация добавляем ключ select_task_by_llm -- тогда выбираем ллмкой, если нет то regex

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("service", "fallback", 1.7): loc_cnd.no_document_in_use(),
            ("generation", "decisions", 1.5): cnd.regexp(DECISIONS),
            ("generation", "future_tasks", 1.5): cnd.regexp(FUTURE_TASKS),
            ("generation", "completed_tasks", 1.5): cnd.regexp(COMPLETED_TASKS),
            ("generation", "summary", 1.5): cnd.regexp(SUMMARY),
            ("generation", "question_answering", 1.1): cnd.true(),
        }
    },
    "service": {
        "start": {
            RESPONSE: "",
            TRANSITIONS: {"fallback": cnd.true()},
        },
        "fallback": {
            RESPONSE: "Sorry, I cannot help you with that.",
            TRANSITIONS: {
                lbl.repeat(0.2): cnd.true(),
            },
        },
    },
    "generation": {
        "summary": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="summary"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "future_tasks": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="future_tasks"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "completed_tasks": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="completed_tasks"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "decisions": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="decisions"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "question_answering": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="question_answering"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_node_label=("service", "fallback"))
