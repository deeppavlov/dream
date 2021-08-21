from common.dialogflow_framework.extensions.facts_utils import provide_facts_response


def fact_provider(page_source, wiki_page):
    def response(vars):
        return provide_facts_response(vars, page_source, wiki_page)

    return response
