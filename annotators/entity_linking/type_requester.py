import asyncio
from typing import List, Optional
from logging import getLogger

import aiohttp

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.component import Component

REQUEST_TIMEOUT = 5

log = getLogger(__name__)
loop = asyncio.get_event_loop()


@register("type_requester")
class TypeRequester(Component):
    def __init__(self, *args, **kwargs):
        pass

    async def request_wikidata(self, session, id: str, type_id: bool = False) -> Optional[str]:
        ans = None
        try:
            async with session.get(
                f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={id}", timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    json = await resp.json()
                    if type_id:
                        ans = json["entities"][id]["labels"]["en"]["value"]
                    else:
                        ans = json["entities"][id]["claims"]["P31"][0]["mainsnak"]["datavalue"]["value"]["id"]
        except asyncio.TimeoutError:
            log.warning(f"TimeoutError for {id}")
        except Exception as e:
            log.error(repr(e))
        finally:
            return ans

    async def process_id(self, session, id):
        type_id = await self.request_wikidata(session, id)
        return await self.request_wikidata(session, type_id, True)

    async def process_group(self, session, entity_ids):
        results = await asyncio.gather(*[self.process_id(session, id) for id in entity_ids])
        return results

    async def async_call(self, x: List[List[List[str]]]) -> List[List[List[Optional[str]]]]:
        async with aiohttp.ClientSession(loop=loop) as session:
            results = await asyncio.gather(*[self.process_group(session, entity_ids) for entity_ids in x[0]])
            return [results]

    def __call__(self, x: List[List[List[str]]]) -> List[List[List[Optional[str]]]]:
        return loop.run_until_complete(self.async_call(x))
