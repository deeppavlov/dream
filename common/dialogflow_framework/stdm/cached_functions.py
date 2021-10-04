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

import logging
import collections

logger = logging.getLogger(__name__)


CACHED_MAXSIZE = 1000


def get_function_id(func):
    return f"name:{func.__name__}:id:{id(func)}"


CACHED_FUNCTIONS = collections.defaultdict(dict)


def add_cached_function(func):
    func_id = get_function_id(func)
    CACHED_FUNCTIONS[func_id]["func"] = func
    CACHED_FUNCTIONS[func_id]["cache"] = {}


def clear_cache():
    for cached_func in CACHED_FUNCTIONS.values():
        cached_func["cache"].clear()


def drop_cache_overhead(func_id, cached_maxsize):
    permitted_var_hashes = list(CACHED_FUNCTIONS[func_id]["cache"])[-cached_maxsize:]
    for var_hash in CACHED_FUNCTIONS[func_id]["cache"]:
        if var_hash not in permitted_var_hashes:
            del CACHED_FUNCTIONS[func_id]["cache"][var_hash]


def exec_cached_function(func, *args, **kwargs):
    func_id = get_function_id(func)
    var_hash = hash(str(vars))
    if var_hash not in CACHED_FUNCTIONS[func_id]["cache"]:
        drop_cache_overhead(func_id, CACHED_MAXSIZE - 1)
        CACHED_FUNCTIONS[func_id]["cache"][var_hash] = CACHED_FUNCTIONS[func_id]["func"](*args, **kwargs)
    exec_result = CACHED_FUNCTIONS[func_id]["cache"][var_hash]
    return exec_result
