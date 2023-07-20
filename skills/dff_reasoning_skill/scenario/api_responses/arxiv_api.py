import arxiv
from df_engine.core import Context, Actor
from scenario.utils import compose_input_for_API


def arxiv_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    api_input = compose_input_for_API(ctx, actor)
    search = arxiv.Search(query=api_input, max_results=2, sort_by=arxiv.SortCriterion.SubmittedDate)

    response = ""
    for result in search.results():
        response += f"TITLE: {result.title}.\nSUMMARY: {result.summary}\nLINK: {result}\n\n"

    return response
