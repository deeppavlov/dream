from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Sequence, Union, Callable

import requests

from core.config import MAX_WORKERS


def _make_request(name, url, payload):
    r = requests.post(url, json=payload)
    if r.status_code != 200:
        raise RuntimeError(f'Got {r.status_code} status code for {url}')
    return [{name: response} for response in r.json()['responses']]


class RestCaller:
    """
    Call to REST services, annotations or skills.
    """

    def __init__(self, max_workers: int = MAX_WORKERS,
                 names: Optional[Sequence[str]] = None,
                 urls: Optional[Sequence[str]] = None,
                 state_formatters: Optional[Sequence[Callable], Callable] = None) -> None:
        self.names = tuple(names or ())
        self.urls = tuple(urls or ())
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.state_formatters = state_formatters

    def __call__(self, payload: Union[Dict, Sequence[Dict]],
                 names: Optional[Sequence[str]] = None,
                 urls: Optional[Sequence[str]] = None,
                 state_formatters: Optional[Sequence[Callable], Callable] = None) -> List[
        Dict[str, Dict[str, Any]]]:

        names = names if names is not None else self.names
        urls = urls if urls is not None else self.urls
        state_formatters = state_formatters if state_formatters is not None else self.state_formatters

        if names is None:
            raise ValueError('No service names were provided.')
        if urls is None:
            raise ValueError('No service urls were provided')
        if state_formatters is None:
            raise ValueError('No state formatters were provided.')

        if isinstance(payload, Dict):
            if isinstance(state_formatters, Callable):
                formatted_payload = [state_formatters(payload)] * len(names)
            else:
                formatted_payload = [formatter(payload) for formatter in state_formatters]
        else:
            if isinstance(state_formatters, Callable):
                formatted_payload = [state_formatters(p) for p in payload]
            else:
                formatted_payload = [formatter(p) for formatter, p in
                                     zip(state_formatters, payload)]

        total_result = []
        for preprocessed in zip(*self.executor.map(_make_request, names, urls, formatted_payload)):
            res = {}
            for data in preprocessed:
                res.update(data)

            total_result.append(res)

        return total_result
