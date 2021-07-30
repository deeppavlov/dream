import argparse
import logging
import re
import string
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


LISTS_OF_BEST_SELLING_GAMES_BY_PLATFORM = \
    "https://en.wikipedia.org/wiki/Lists_of_best-selling_video_games_by_platform"
LIST_OF_MOST_PLAYED_MOBILE_GAMES = "https://en.wikipedia.org/wiki/List_of_most-played_mobile_games_by_player_count"
WIKIPEDIA = "https://en.wikipedia.org"
COLS_WITH_WIKI_REFS = [
    ["Title", "Game"],
    "Genre(s)",
    ["Developer(s)", "Developer / Publisher"],
    "Publisher(s)",
    "Programmer(s)",
    "Licensor(s)",
    "Series"
]
COLS_WITH_WIKI_REFS_NAMES = [c[0] if isinstance(c, list) else c for c in COLS_WITH_WIKI_REFS]
WIKI_REF_COLS = [
    "game_page", "genre_page", "developer_page", "publisher_page", "programmer_page", "licensor_page", "series_page"]
SIMPLE_COLS = ["Release date", ["Sales", "Copies sold", "Downloads", "Total copies sold"], "As of"]
SIMPLE_COL_NAMES = [c[0] if isinstance(c, list) else c for c in SIMPLE_COLS]
NUMBER_COL = "No."
JOINED_NUMBER_COL = "Position by sales for platform model"
JOINED_SALES_COL = "Sales, Downloads, or Users"
JOINED_DROPPED_COLS = ["Publisher(s)", "Licensor(s)", "publisher_page", "licensor_page"]
JOINED_RENAMING = {NUMBER_COL: JOINED_NUMBER_COL, SIMPLE_COL_NAMES[1]: JOINED_SALES_COL}

COLUMN_NAMES = [NUMBER_COL] + COLS_WITH_WIKI_REFS_NAMES + WIKI_REF_COLS + SIMPLE_COL_NAMES

MILLION_COMPILED_PATTERN = re.compile(r"(0\.0*[1-9][0-9]*|[1-9][0-9]*(?:\.[0-9]+)?) (million|billion)")
NUMBER_COMPILED_PATTERN = re.compile(r"[1-9][0-9]*(?:[\.,][0-9]{3})*")
PUNCTUATION_COMPILED_PATTERN = re.compile(r"[\.,]")

UNKNOWN_COMPILED_PATTERN = re.compile("^(?:N/A|Unknown|Un\xadknown|Un-known)$", flags=re.I)

ALTERNATIVE_TITLE_COL_PREFIX = "Alternative title"
ALTERNATIVE_TITLES = {
    "PlayerUnknown's Battlegrounds": "PUBG",
    "Harry Potter and the Philosopher's Stone": "Harry Potter and the Sorcerer's Stone",
    "PUBG Mobile": "PlayerUnknown's Battlegrounds Mobile",
}
ALTERNATIVE_TITLE_PATTERNS = [
    (re.compile(r"Grand Theft Auto"), "GTA")
]
MISSING_GAMES = [
    {
        "Title": "Fortnite",
        "Genre(s)": "survival;battle royale;sandbox",
        "Release date": "July 25, 2017",
        "Developer(s)": "Epic Games",
        "game_page": "/wiki/Fortnite",
        "developer_page": "/wiki/Epic_Games",
        "genre_page": "/wiki/Survival_game /wiki/Battle_royale_game /wiki/Sandbox_game",
        JOINED_SALES_COL: 125000000,
    },
    {
        "Title": "Fortnite: Save the World",
        "Genre(s)": "third-person shooter;survival;tower defence",
        "Release date": "July 29, 2020",
        "Developer(s)": "Epic Games",
        "Series": "Fortnite",
        "game_page": "/wiki/Fortnite:_Save_the_World",
        "developer_page": "/wiki/Epic_Games",
        "genre_page": "/wiki/Third-person_shooter /wiki/Survival_game /wiki/Tower_defense",
        "series_page": "/wiki/Fortnite",
    },
    {
        "Title": "Fortnite Battle Royale",
        "Genre(s)": "third-person shooter;battle royale",
        "Release date": "September 26, 2017",
        "Developer(s)": "Epic Games",
        "Series": "Fortnite",
        "game_page": "/wiki/Fortnite_Battle_Royale",
        "developer_page": "/wiki/Epic_Games",
        "genre_page": "/wiki/Third-person_shooter /wiki/Battle_royale_game",
        "series_page": "/wiki/Fortnite",
    },
    {
        "Title": "Fortnite Creative",
        "Genre(s)": "sandbox",
        "Release date": "December 13, 2018",
        "Developer(s)": "Epic Games",
        "Series": "Fortnite",
        "game_page": "/wiki/Fortnite_Creative",
        "developer_page": "/wiki/Epic_Games",
        "genre_page": "/wiki/Sandbox_game",
        "series_page": "/wiki/Fortnite",
    },
    {
        "Title": "Roblox",
        "Genre(s)": "game creation system;massively multiplayer online",
        "Release date": "September 1, 2006",
        "Developer(s)": "Roblox Corporation",
        "game_page": "/wiki/Roblox",
        "developer_page": "/wiki/Roblox_Corporation",
        "genre_page": "/wiki/Game_creation_system /wiki/Massively_multiplayer_online_game",
        JOINED_SALES_COL: 175000000,
    }
]

BROKEN_ROWS_IN_HTML_TABLES = {}


def get_args():
    parser = argparse.ArgumentParser(
        description=f"Downloads tables from https://en.wikipedia.org/wiki/Lists_of_best-selling_video_games_by_platform"
                    f" and https://en.wikipedia.org/wiki/List_of_most-played_video_games_by_player_count into .tsv "
                    f"files. The script extracts hyper references for game, developer, publisher and so on if they are "
                    f"available. This references are stored in columns 'game_page', 'developer_page' and so on. "
                    f"If game has several genres, developers, etc., their names are separated with semicolons, e.g. "
                    f"'action;adventure;puzzle'. Hyper references for multiple entities are separated by spaces, e.g. "
                    f"'/wiki/Adventure_game /wiki/Sports_game'. Joined table (`joined_output` parameter script "
                    f"parameter) is created. Joined table has additional columns 'Alternative title 1/2/3' and "
                    f"'record is from list' and lacks columns {', '.join([repr(c) for c in JOINED_DROPPED_COLS])}. "
                    f"Several columns are renamed according to mapping {JOINED_RENAMING}. If game titles collected for "
                    f"different platform game lists are similar the record from the first list is taken."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
    )
    parser.add_argument(
        "joined_output",
        type=Path,
    )
    args = parser.parse_args()
    args.output_dir = args.output_dir.expanduser()
    args.joined_output = args.joined_output.expanduser()
    return args


def text_to_integer(text, list_name, href):
    m = MILLION_COMPILED_PATTERN.search(text)
    if m:
        number = int(float(m.group(1)) * (10 ** 6 if m.group(2) == "million" else 10 ** 9))
    else:
        m = NUMBER_COMPILED_PATTERN.search(text)
        if m is None:
            raise ValueError(f"Text '{text}' from list '{list_name}' by href {href} is not number.")
        number = int(PUNCTUATION_COMPILED_PATTERN.sub('', m.group(0)))
    return number


def get_lists():
    lists_response = requests.get(LISTS_OF_BEST_SELLING_GAMES_BY_PLATFORM)
    soup = BeautifulSoup(lists_response.content, "html.parser")
    content = soup.find_all("div", class_="mw-parser-output")[0]
    children = content.findChildren(recursive=False)
    start = None
    end = None
    for i, elem in enumerate(children):
        span = elem.find("span", class_="mw-headline")
        if elem.name == "h2" and span is not None and span.text == "Platforms":
            start = i + 1
            break
    for i, elem in enumerate(children):
        span = elem.find("span", class_="mw-headline")
        if elem.name == "h2" and span is not None and span.text == "See also":
            end = i
    children = children[start:end]
    headers = children[::2]
    inner_lists = children[1::2]
    result = {}
    for h3, ul in zip(headers, inner_lists):
        platform_name = h3.find("span", class_="mw-headline").text.strip()
        result[platform_name] = {}
        for li in ul.findAll("li"):
            a = li.find("a")
            href = WIKIPEDIA + a["href"]
            list_name = a.text.strip()
            result[platform_name][list_name] = {"href": href.strip()}
    return result


def extract_text_without_upper_index(elem):
    text = ""
    for content in elem.contents:
        if hasattr(content, "name") and content.name is not None:
            if content.name == "span":
                text += content.text + ' '
        else:
            text += str(content).strip() + ' '
    text = re.sub(r'\s+', ' ', text.strip())
    if not text or UNKNOWN_COMPILED_PATTERN.match(text):
        text = None
    return text


def get_column_indices(column_names, searched_cols, list_name, href):
    col_indices = []
    missing = []
    for n in searched_cols:
        if isinstance(n, str) and n in column_names:
            col_indices.append(column_names.index(n))
        elif isinstance(n, list) and any([nn in column_names for nn in n]):
            for nn in n:
                if nn in column_names:
                    col_indices.append(column_names.index(nn))
        else:
            col_indices.append(None)
            missing.append(n)
    return col_indices, missing


def get_text_href_from_elem(elem):
    a = elem.find("a")
    if a is None:
        href = ""
        i_elem = elem.find("i")
        if i_elem is None:
            span_elem = elem.find("span")
            text = elem.text.strip() if span_elem is None else span_elem.text.strip()
        else:
            text = i_elem.text.strip()
    else:
        text = a.text.strip()
        href = a["href"]
    return text, href


def get_texts_and_hrefs_from_cell_with_separator(cell):
    texts, hrefs = [], []
    sep = " / " if " / " in str(cell.text) else ", "
    for content in cell.contents:
        if content.name is not None and content.name == "a":
            texts.append(content.text.strip())
            hrefs.append(content.get("href"))
        else:
            parts = str(content).split(sep)
            for part in parts:
                part = part.strip()
                if part:
                    texts.append(part)
                    hrefs.append("")
    return texts, hrefs


def get_texts_and_hrefs_from_cell(cell, col_name, list_name, row_i):
    texts, hrefs = [], []
    if cell.findChildren(recursive=False):
        list_elements = cell.findChildren("li")
        if list_elements:
            for elem in list_elements:
                text, href = get_text_href_from_elem(elem)
                texts.append(text)
                hrefs.append(href)
        else:
            cell_children = cell.findChildren(recursive=False)
            if len(cell_children) == 1 and cell_children[0].name == "i" \
                    or len(cell_children) == 2 and cell_children[0].name == "i" and cell_children[1].name == "sup":
                cell = cell_children[0]
            if " / " in cell.text or ", " in cell.text:
                _texts, _hrefs = get_texts_and_hrefs_from_cell_with_separator(cell)
                texts += _texts
                hrefs += _hrefs
            else:
                text, href = get_text_href_from_elem(cell)
                texts.append(text)
                hrefs.append(href)
    else:
        if " / " in cell.text or ", " in cell.text:
            _texts, _hrefs = get_texts_and_hrefs_from_cell_with_separator(cell)
            texts += _texts
            hrefs += _hrefs
        else:
            texts.append(cell.text.strip())
            hrefs.append("")
    for i in range(len(texts) - 1, -1, -1):
        if not texts[i] or UNKNOWN_COMPILED_PATTERN.match(texts[i]):
            del texts[i]
            del hrefs[i]
    texts = ';'.join(texts) if texts else None
    hrefs = ' '.join(hrefs) if hrefs and any(hrefs) else None
    return texts, hrefs


def get_cell(cells, cell_indices, first_cell_is_missing):
    cell_indices = list(cell_indices)
    for i, cell in enumerate(cells):
        if cell.get("colspan"):
            colspan_shift = int(cell.get("colspan")) - 1
            for j, ind in enumerate(cell_indices):
                if ind is not None:
                    if ind > i + colspan_shift:
                        cell_indices[j] -= colspan_shift
                    if i < ind <= i + colspan_shift:
                        cell_indices[j] = None
    for i in cell_indices:
        cell = None if i is None else cells[i - first_cell_is_missing]
        yield cell


def fix_genre_capitalization(genre):
    if genre[0] in string.ascii_uppercase and genre[1] in string.ascii_lowercase:
        fixed = genre[0].lower() + genre[1:]
    else:
        fixed = genre
    return fixed


def get_table(href, list_name):
    table_response = requests.get(href)
    soup = BeautifulSoup(table_response.content, "html.parser")
    table = soup.find("table", class_="wikitable plainrowheaders sortable")
    if table is None:
        table = soup.find("table", class_="wikitable sortable")
    rows = table.findAll("tr")
    column_names = [
        th.contents[0].text.strip() if hasattr(th.contents[0], "text") else str(th.contents[0]).strip()
        for th in rows[0].findAll("th")]
    data = pd.DataFrame({c: [] for c in COLUMN_NAMES})
    wiki_col_indices, missing_1 = get_column_indices(column_names, COLS_WITH_WIKI_REFS, list_name, href)
    simple_col_indices, missing_2 = get_column_indices(column_names, SIMPLE_COLS, list_name, href)
    if missing_1 + missing_2:
        logger.info(f"Columns {missing_1 + missing_2} are missing in list '{list_name}' by href {href}")
    number_col_is_missing = NUMBER_COL not in column_names
    logger.info(f"column_names for list '{list_name}': {column_names}")
    zero_col_rowspan = 0
    last_number_col_value = None
    for i, r in enumerate(rows[1:]):
        if i in BROKEN_ROWS_IN_HTML_TABLES.get(href, []):
            continue
        cells = r.findChildren(recursive=False)
        if number_col_is_missing:
            row_data = {NUMBER_COL: None}
            first_cell_is_missing = False
        else:
            if zero_col_rowspan:
                zero_col_rowspan -= 1
                row_data = {NUMBER_COL: last_number_col_value}
                first_cell_is_missing = True
            else:
                number_col_value = cells[0].text.strip()
                row_data = {NUMBER_COL: number_col_value}
                last_number_col_value = number_col_value
                first_cell_is_missing = False
                if cells[0].get("rowspan") is not None:
                    zero_col_rowspan = int(cells[0]["rowspan"]) - 1
        for col_name, wiki_col_name, cell in zip(
                COLS_WITH_WIKI_REFS_NAMES, WIKI_REF_COLS, get_cell(cells, wiki_col_indices, first_cell_is_missing)):
            row_data[col_name], row_data[wiki_col_name] = (None, None) if cell is None \
                else get_texts_and_hrefs_from_cell(cell, col_name, list_name, i)
            if col_name == COLS_WITH_WIKI_REFS_NAMES[0]:  # Title
                if row_data[col_name] is not None:
                    row_data[col_name] = row_data[col_name].split(";")[0]
                if row_data[wiki_col_name] is not None:
                    row_data[wiki_col_name] = row_data[wiki_col_name].split()[0]
            elif col_name == COLS_WITH_WIKI_REFS_NAMES[1]:  # Genre
                if row_data[col_name] is not None:
                    row_data[col_name] = ";".join(
                        [fix_genre_capitalization(g) for g in row_data[col_name].split(';')])
        for col_name, cell in zip(SIMPLE_COL_NAMES, get_cell(cells, simple_col_indices, first_cell_is_missing)):
            row_data[col_name] = None if cell is None else extract_text_without_upper_index(cell)
        data = data.append(row_data, ignore_index=True)
    data["Sales"] = data["Sales"].map(lambda x: text_to_integer(str(x), list_name, href))
    return data


def get_model_name_from_list_name(list_name):
    prefix = "List of best-selling "
    suffixes = [" video games", " games"]
    err_msg = f"Cannot extract model name from list name '{list_name}'"
    if list_name.startswith(prefix):
        model_name = list_name[len(prefix):]
    else:
        raise ValueError(err_msg)
    if list_name.endswith(suffixes[0]):
        model_name = model_name[:-len(suffixes[0])]
    elif list_name.endswith(suffixes[1]):
        model_name = model_name[:-len(suffixes[1])]
    else:
        raise ValueError(err_msg)
    return model_name


def join(single_table, dict_of_tables):
    table = single_table.copy()
    table.insert(
        0, "record is from list", pd.Series(["List of most-played mobile games by player count"] * table.shape[0]))
    table = table.set_index("Title")
    for platform, v in dict_of_tables.items():
        for list_name, vv in v.items():
            data = vv["data"]
            data.insert(0, "record is from list", pd.Series([list_name] * data.shape[0]))
            data = data.set_index("Title")
            table = table.append(data.loc[data.index.difference(table.index), :])
    table = table.reset_index().sort_values("Sales", ascending=False)
    table = table.rename(columns=JOINED_RENAMING)
    table = table.drop(JOINED_DROPPED_COLS, axis=1)
    return table


def insert_alternative_title_columns(df, ncols):
    title_col_index = df.columns.get_loc('Title')
    for i in range(ncols):
        df.insert(title_col_index + i + 1, f"Alternative title {i+1}", pd.Series([None] * df.shape[0]))
    return df


def add_alternative_names(df):
    df = df.set_index("Title")
    for title, alternative_title in ALTERNATIVE_TITLES.items():
        df.loc[title, f"{ALTERNATIVE_TITLE_COL_PREFIX} 1"] = alternative_title
    df = df.reset_index()
    for pattern, repl in ALTERNATIVE_TITLE_PATTERNS:
        matched = df[COLS_WITH_WIKI_REFS_NAMES[0]].apply(lambda x: True if pattern.search(x) else False)
        titles = df.loc[matched, COLS_WITH_WIKI_REFS_NAMES[0]]
        alternative_titles = titles.apply(lambda x: pattern.sub(repl, x))
        df.loc[alternative_titles.index, f"{ALTERNATIVE_TITLE_COL_PREFIX} 1"] = alternative_titles.values
    return df


def add_missing_popular_games(df):
    for mg in MISSING_GAMES:
        df = df.append(mg, ignore_index=True)
    return df


def main():
    args = get_args()
    most_played_mobile = get_table(LIST_OF_MOST_PLAYED_MOBILE_GAMES, "mobile")
    fn = args.output_dir / Path("most_played_mobile_games.tsv")
    fn.parent.mkdir(exist_ok=True)
    most_played_mobile.to_csv(fn, sep='\t', index=False)
    lists = get_lists()
    del lists["Other"]
    for platform, platform_info in lists.items():
        logger.info(f"Collecting data for platform '{platform}'")
        for list_name, list_info in platform_info.items():
            list_info["data"] = get_table(list_info["href"], list_name)
            fn = args.output_dir / Path(platform) / Path(list_name.replace(' ', '_') + '.tsv')
            fn.parent.mkdir(exist_ok=True)
            list_info["data"].to_csv(fn, sep='\t', index=False)
    joined = join(most_played_mobile, lists)
    joined = insert_alternative_title_columns(joined, 3)
    joined = add_alternative_names(joined)
    joined = add_missing_popular_games(joined)
    args.joined_output.parent.mkdir(exist_ok=True)
    joined.to_csv(args.joined_output, sep='\t', index=False)


if __name__ == "__main__":
    main()
