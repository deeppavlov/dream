import argparse
import json
import logging
import os
import re

import requests

from common.gaming import get_igdb_client_token, get_igdb_post_kwargs


logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


CLIENT_ID = "7mch7slb8ftokz50w7puvhis9ia1nu"  # Fedor Ignatov
CLIENT_SECRET = "gwnwc9a090iwq2up1oa2bd6cr3np7i"  # Fedor Ignatov

CLIENT_TOKEN = get_igdb_client_token(CLIENT_ID, CLIENT_SECRET)
logger.info(f"CLIENT_TOKEN={CLIENT_TOKEN}")
if CLIENT_TOKEN is None:
    IGDB_POST_KWARGS = None
else:
    IGDB_POST_KWARGS = get_igdb_post_kwargs(CLIENT_TOKEN, CLIENT_ID)
    IGDB_POST_KWARGS["timeout"] = 20.


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "list_of_game_names",
        help="JSON file containing list of game names for downloading. Element of the list can be either string "
             "(a game name) or a list of strings (alternative names of the same game). In latter case the first "
             "element of an inner list will be used for search."
    )
    parser.add_argument(
        "output_id_to_game",
        help="Path to JSON file where results will be saved."
    )
    parser.add_argument(
        "output_lowercased_name_to_game"
    )
    args = parser.parse_args()
    return args


GAME_SEARCH_TMPL = 'search "{}"; fields *;'

AND_PATTERN = re.compile(r"\band\b", flags=re.I)


def generate_name_spellings(name):
    return [name, AND_PATTERN.sub("&", name)]


ALTERNATIVE_NAME_TMPL = 'fields *; where uuid = {};'


def add_alternative_name_values(game_info):
    logger.info(f"Collecting alternative names for game '{game_info.get('name')}'")
    alt_name_ids = game_info.get("alternative_names", [])
    if alt_name_ids:
        for id_ in alt_name_ids:
            search_body = ALTERNATIVE_NAME_TMPL.format(id_)
            results = requests.post(
                "https://api.igdb.com/v4/alternative_names",
                data=search_body,
                **IGDB_POST_KWARGS,
            )
            results = results.json()
            if not results:
                logger.info(
                    f"No alternative name with id {id_} was found. Original name is '{game_info.get('name')}'")
            elif len(results) > 1:
                logger.info(
                    f"Found more than one alternative name description for id {id_}. Original name is "
                    f"'{game_info.get('name')}'. Found descriptions: {results}")
            else:
                if "alternative_name_values" not in game_info:
                    game_info["alternative_name_values"] = {id_: results[0]}
                else:
                    game_info[id_] = results[0]


def look_for_game_in_search_results(search_results, comp, name, game_name_spellings, found_quality_comment):
    best_result = None
    candidates = []
    for game_info in search_results:
        if any([comp(name, game_info.get('name', '')) for name in game_name_spellings]):
            candidates.append(game_info)
        elif "alternative_names" in game_info:
            add_alternative_name_values(game_info)
            if "alternative_name_values" in game_info:
                ans = [an.get("name", "") for an in game_info["alternative_name_values"].values()]
                if any([comp(n, info_n) for n in game_name_spellings for info_n in ans]):
                    logger.info(f"Found {found_quality_comment}match with one of alternative names {ans}. name={name}")
                    best_result = game_info
                    candidates.append(game_info)
    if candidates:
        logger.info(f"Found {found_quality_comment}match for game '{name}'")
        best_result = sorted(candidates, key=lambda x: -x['rating_count'] if 'rating_count' in x else 1)[0]
    return best_result


def search_game_on_igdb(name):
    names = generate_name_spellings(name)
    search_body = GAME_SEARCH_TMPL.format(name)
    search_results = requests.post(
        "https://api.igdb.com/v4/games",
        data=search_body,
        **IGDB_POST_KWARGS,
    )
    search_results = search_results.json()
    best_result = look_for_game_in_search_results(
        search_results, lambda x, y: x.lower() == y.lower(), name, names, "exact ")
    if best_result is None:
        best_result = look_for_game_in_search_results(
            search_results, lambda x, y: x.lower() in y.lower(), name, names, "orig name in found name ")
    if best_result is None:
        best_result = look_for_game_in_search_results(
            search_results, lambda x, y: y.lower() in x.lower(), name, names, "found name in orig name ")
    return best_result, search_results


def main():
    args = get_args()
    with open(args.list_of_game_names) as f:
        game_names = json.load(f)
    output_id_to_game = {}
    lowercased_name_to_game = {}
    for gn in game_names:
        if isinstance(gn, str):
            name = gn
            best_result, search_results = search_game_on_igdb(name)
        else:
            best_result = None
            name = None
            for n in gn:
                name = n
                best_result, search_results = search_game_on_igdb(name)
                if best_result is not None:
                    break
        if best_result is None:
            logger.info(f"No data for game name '{gn}' was found.")
            continue
        id_ = best_result.get("id")
        if id_ is None:
            logger.info(f"No id for game name '{name}'. Result: {best_result}")
            continue
        key = gn if isinstance(gn, str) else gn[0]
        lowercased_name_to_game[key] = best_result
        output_id_to_game[str(best_result["id"])] = best_result
        logger.info(f"'{gn}' is processed successfully")
    os.makedirs(os.path.split(args.output_id_to_game)[0], exist_ok=True)
    with open(args.output_id_to_game, 'w') as f:
        json.dump(output_id_to_game, f, indent=2)
    os.makedirs(os.path.split(args.output_lowercased_name_to_game)[0], exist_ok=True)
    with open(args.output_lowercased_name_to_game, 'w') as f:
        json.dump(lowercased_name_to_game, f, indent=2)


if __name__ == "__main__":
    main()
