from df_engine.core import Context, Actor
from common.dialogflow_framework.extensions.facts_utils import provide_facts_response


def fact_provider(page_source, wiki_page):
    def response(ctx: Context, actor: Actor, *args, **kwargs):
        return provide_facts_response(ctx, actor, page_source, wiki_page)

    return response
