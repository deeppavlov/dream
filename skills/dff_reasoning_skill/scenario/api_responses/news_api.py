from df_engine.core import Context, Actor
from os import getenv
import requests


ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
available_variables = {f"{var}": getenv(var, None) for var in ENVVARS_TO_SEND}


def news_api_response(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    query_params = {"source": "bbc-news", "sortBy": "top", "apiKey": available_variables["NEWS_API_KEY"]}
    main_url = " https://newsapi.org/v1/articles"
    res = requests.get(main_url, params=query_params)
    open_bbc_page = res.json()
    article = open_bbc_page["articles"]
    results = []
    for ar in article:
        results.append(ar["title"])

    return "\n".join(results)
