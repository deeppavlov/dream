from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Sequence, Union

import requests

from core.transform_config import MAX_WORKERS


def _make_request(name, url, formatter, payload):
    r = requests.post(url, json=formatter(payload))
    if r.status_code != 200:
        raise RuntimeError(f'Got {r.status_code} status code for {url}')
    return [{name: formatter(response, mode='out')} for response in r.json()]


class RestCaller:
    """
    Call to REST services, annotations or skills.
    """

    def __init__(self, max_workers: int = MAX_WORKERS,
                 names: Optional[Sequence[str]] = None,
                 urls: Optional[Sequence[str]] = None,
                 formatters = None) -> None:
        self.names = tuple(names or ())
        self.urls = tuple(urls or ())
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.formatters = formatters

    def __call__(self, payload: Union[Dict, Sequence[Dict]],
                 names: Optional[Sequence[str]] = None,
                 urls: Optional[Sequence[str]] = None,
                 formatters = None) -> List[
        Dict[str, Dict[str, Any]]]:

        names = names if names is not None else self.names
        urls = urls if urls is not None else self.urls
        formatters = formatters if formatters is not None else self.formatters

        if names is None:
            raise ValueError('No service names were provided.')
        if urls is None:
            raise ValueError('No service urls were provided')
        if formatters is None:
            raise ValueError('No state formatters were provided.')

        if not isinstance(payload, Sequence):
            payload = [payload] * len(names)

        total_result = []
        for preprocessed in zip(*self.executor.map(_make_request, names, urls, formatters,
                                                   payload)):
            res = {}
            for data in preprocessed:
                res.update(data)

            total_result.append(res)

        return total_result
