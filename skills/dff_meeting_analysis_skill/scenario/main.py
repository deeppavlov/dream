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
SHORT_SUMMARY = re.compile(
    r"^.?/short_summary.?$",
    re.IGNORECASE,
)
LONG_SUMMARY = re.compile(
    r"^.?/long_summary.?$",
    re.IGNORECASE,
)
FUTURE_TASKS = re.compile(
    r"((((future)|(to-?do)|(current)) tasks)|(tasks in progress))|(^.?/current_tasks.?$)",
    re.IGNORECASE,
)
COMPLETED_TASKS = re.compile(
    r"(((completed)|(finished)) tasks)|(^.?/completed_tasks.?$)",
    re.IGNORECASE,
)
DECISIONS = re.compile(
    r"decisions?",
    re.IGNORECASE,
)
PROGRESS_BY_AREAS = re.compile(
    r"(progress ((made )?(by))?((did)|(have))? (((.* )?teams?)|(areas)))|(^.?/progress_by_areas.?$)",
    re.IGNORECASE,
)
WEEKLY_REPORT = re.compile(
    r"weekly report",
    re.IGNORECASE,
)
FULL_REPORT = re.compile(
    r"(((full)|(complete)|(entire)) ((report)|(overview)))|(^.?/full_report.?$)",
    re.IGNORECASE,
)
PROBLEMS = re.compile(
    r"^.?/problems.?$",
    re.IGNORECASE,
)
# тут можно еще спрашивать ллмку. но пока оставляем в таком виде, только побольше вариантов.
# на будущее -- след.итерация добавляем ключ select_task_by_llm -- тогда выбираем ллмкой, если нет то regex

flows = {
    GLOBAL: {
        TRANSITIONS: {
            ("service", "no_document", 1.7): loc_cnd.no_document_in_use(),
            ("generation", "decisions", 1.5): cnd.regexp(DECISIONS),
            ("generation", "future_tasks", 1.5): cnd.regexp(FUTURE_TASKS),
            ("generation", "completed_tasks", 1.5): cnd.regexp(COMPLETED_TASKS),
            ("generation", "summary_short", 1.5): cnd.regexp(SHORT_SUMMARY),
            ("generation", "summary_long", 1.5): cnd.regexp(LONG_SUMMARY),
            ("generation", "summary", 1.5): cnd.regexp(SUMMARY),
            ("generation", "progress_by_areas", 1.5): cnd.regexp(PROGRESS_BY_AREAS),
            ("generation", "full_report", 1.5): cnd.regexp(FULL_REPORT),
            ("generation", "weekly_report", 1.5): cnd.regexp(WEEKLY_REPORT),
            ("generation", "problems", 1.5): cnd.regexp(PROBLEMS),
            ("generation", "question_answering", 1.1): loc_cnd.go_to_question_answering(),
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
        "no_document": {
            RESPONSE: "Please, upload the transcript that you want to discuss.",
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
        "summary_short": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="summary_short"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "summary_long": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="summary_long"),
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
        "progress_by_areas": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="progress_by_areas"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "full_report": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="full_report"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "weekly_report": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="weekly_report"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "problems": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="problems"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
        "question_answering": {
            RESPONSE: loc_rsp.analyze_transcript(prompt_type="question_answering"),
            TRANSITIONS: {("generation", "question_answering"): cnd.true()},
        },
    },
}

actor = Actor(flows, start_label=("service", "start"), fallback_node_label=("service", "fallback"))
