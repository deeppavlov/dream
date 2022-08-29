# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import logging

import sentry_sdk

from deeppavlov.core.common.registry import register
from deeppavlov.core.models.estimator import Component

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


def split_page(page):
    if isinstance(page, str):
        page_split = page.split("\n")
    else:
        page_split = page
    titles = []
    main_page_dict = {}
    text_list = []
    dict_level = {2: {}, 3: {}, 4: {}}
    if page_split:
        for elem in page_split:
            if elem:
                find_title = re.findall(r"^([=]{1,4})", elem)
                if elem.startswith("{{"):
                    main_pages = elem.strip()[2:-2].split("|")[1:]
                    if titles:
                        main_page_dict[titles[-1][0]] = main_pages
                if find_title:
                    cur_level = len(find_title[0])
                    eq_str = "=" * cur_level
                    title = re.findall(f"{eq_str}(.*?){eq_str}", elem)
                    title = title[0].strip()
                    if text_list:
                        if titles:
                            last_title, last_level = titles[-1]
                            if cur_level <= last_level:
                                while titles and last_level >= cur_level:
                                    if titles[-1][1] < cur_level:
                                        last_title, last_level = titles[-1]
                                    else:
                                        last_title, last_level = titles.pop()
                                    if dict_level.get(last_level + 1, {}):
                                        if last_title in dict_level[last_level]:
                                            dict_level[last_level][last_title] = {
                                                **dict_level[last_level + 1],
                                                **dict_level[last_level][last_title],
                                            }
                                        else:
                                            dict_level[last_level][last_title] = dict_level[last_level + 1]
                                        dict_level[last_level + 1] = {}
                                    else:
                                        dict_level[last_level][last_title] = text_list
                                        text_list = []
                            else:
                                dict_level[last_level][last_title] = {"first_par": text_list}
                                text_list = []
                        else:
                            dict_level[2]["first_par"] = text_list
                            text_list = []

                    titles.append([title, cur_level])
                else:
                    if not elem.startswith("{{"):
                        text_list.append(elem)

        if text_list:
            if titles:
                last_title, last_level = titles[-1]
                if cur_level <= last_level:
                    while titles:
                        last_title, last_level = titles.pop()
                        if last_level + 1 in dict_level and dict_level[last_level + 1]:
                            if last_title in dict_level[last_level]:
                                dict_level[last_level][last_title] = {
                                    **dict_level[last_level + 1],
                                    **dict_level[last_level][last_title],
                                }
                            else:
                                dict_level[last_level][last_title] = dict_level[last_level + 1]
                            dict_level[last_level + 1] = {}
                        else:
                            dict_level[last_level][last_title] = text_list
                            text_list = []
                else:
                    dict_level[last_level]["first_par"] = text_list
                    text_list = []

    return dict_level[2], main_page_dict


@register("page_preprocessor")
class PagePreprocessor(Component):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, pages_batch):
        processed_pages_batch = []
        main_pages_batch = []
        for pages_list in pages_batch:
            processed_pages_list = []
            main_pages_list = []
            for page in pages_list:
                processed_page, main_page_dict = split_page(page)
                processed_pages_list.append(processed_page)
                main_pages_list.append(main_page_dict)
            processed_pages_batch.append(processed_pages_list)
            main_pages_batch.append(main_pages_list)

        return processed_pages_batch, main_pages_batch


@register("whow_page_preprocessor")
class WhowPagePreprocessor(Component):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, pages_batch):
        processed_pages_batch = []
        for pages_list in pages_batch:
            processed_pages_list = []
            for page in pages_list:
                page_dict = {}
                if page:
                    keys_and_values = page.split("\n")
                    keys = [keys_and_values[i] for i in range(0, len(keys_and_values), 2)]
                    values = [keys_and_values[i] for i in range(1, len(keys_and_values), 2)]
                    for key, value in zip(keys, values):
                        if key == "intro":
                            page_dict["intro"] = value
                        else:
                            page_dict[key] = value.split("\t")
                processed_pages_list.append(page_dict)
            processed_pages_batch.append(processed_pages_list)

        return processed_pages_batch
