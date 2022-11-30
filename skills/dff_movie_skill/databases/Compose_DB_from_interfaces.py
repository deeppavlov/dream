#!/usr/bin/env python

import json
import numpy as np
import pandas as pd
import wget
from time import time


collect_movies_based_on_rating = False
collect_movies_based_on_numvotes = True

for url in [
    "https://datasets.imdbws.com/name.basics.tsv.gz",
    "https://datasets.imdbws.com/title.ratings.tsv.gz",
    "https://datasets.imdbws.com/title.akas.tsv.gz",
    "https://datasets.imdbws.com/title.basics.tsv.gz",
    "https://datasets.imdbws.com/title.crew.tsv.gz",
    "https://datasets.imdbws.com/title.episode.tsv.gz",
    "https://datasets.imdbws.com/title.principals.tsv.gz",
    "https://datasets.imdbws.com/title.episode.tsv.gz",
]:
    filename = wget.download(url)

# # Choose imdb-ids of most popular movies

fpath = "./title.ratings.tsv.gz"
df_ratings = pd.read_table(fpath, low_memory=False)

df = pd.read_table(
    "./title.basics.tsv.gz", low_memory=False, na_values={"startYear": ["\\N"], "endYear": ["\\N"], "isAdult": ["\\N"]}
)

df = df.merge(df_ratings, on="tconst")

# fill start year values
df["startYear"] = df["startYear"].fillna(value=df["startYear"])
df["startYear"] = df["startYear"].fillna(value=0)
df["endYear"] = df["endYear"].fillna(value=df["startYear"])
df["isAdult"] = df["isAdult"].fillna(value=0)

df = df.astype(dtype={"startYear": np.int32, "endYear": np.int32, "isAdult": np.int32})

target = ["movie", "tvMovie", "tvSeries", "tvMiniSeries"]
ind_drop = df[~df["titleType"].isin(target)].index
df = df.drop(ind_drop)

if collect_movies_based_on_rating:
    movies_ids = []
    movies_ids.extend(df.loc[(df["startYear"] <= 1990) & (df["averageRating"] > 8), "tconst"].values)
    movies_ids.extend(
        df.loc[(df["startYear"] > 1990) & (df["startYear"] <= 2005) & (df["averageRating"] > 7), "tconst"].values
    )
    movies_ids.extend(
        df.loc[(df["startYear"] > 2005) & (df["startYear"] <= 2015) & (df["averageRating"] > 6), "tconst"].values
    )
    movies_ids.extend(
        df.loc[(df["startYear"] > 2015) & (df["startYear"] <= 2021) & (df["averageRating"] > 5), "tconst"].values
    )

    with open("imdb_ids.txt", "w") as f:
        for movie_id in movies_ids:
            f.write(str(movie_id) + "\n")

if collect_movies_based_on_numvotes:
    movies_ids = []
    movies_ids.extend(df.loc[df.loc[:, "numVotes"] > 1000, "tconst"].values)
    movies_ids.extend(df.loc[df.loc[:, "averageRating"] > 6.0, "tconst"].values)
    movies_ids = list(set(movies_ids))

    with open("imdb_ids.txt", "w") as f:
        for movie_id in movies_ids:
            f.write(str(movie_id) + "\n")

with open("imdb_ids.txt", "r") as f:
    all_movies_ids = f.read().splitlines()

all_movies_ids = list(set(all_movies_ids))
print(f"Total number of considered movies: {len(all_movies_ids)}")

# # Collect titles and ratings

t0 = time()
fpath = "./title.ratings.tsv.gz"
df_ratings = pd.read_table(fpath, low_memory=False)

ind_drop = df_ratings[~df_ratings["tconst"].isin(all_movies_ids)].index
df_ratings = df_ratings.drop(ind_drop)
assert df_ratings.shape[0] == len(all_movies_ids), print("Number of samples less than number of movies")

fpath = "./title.basics.tsv.gz"

df = pd.read_table(fpath, low_memory=False, na_values={"startYear": ["\\N"], "endYear": ["\\N"], "isAdult": ["\\N"]})

ind_drop = df[~df["tconst"].isin(all_movies_ids)].index
df = df.drop(ind_drop)

df = df.merge(df_ratings, on="tconst")

df.rename(
    columns={
        "originalTitle": "original title",
        "primaryTitle": "title",
        "genres": "genre",
        "averageRating": "imdb_rating",
        "tconst": "imdb_id",
    },
    inplace=True,
)

df.drop_duplicates(inplace=True)

df["titleType"] = df["titleType"].apply(lambda x: "Series" if "Series" in x else "")
df["genre"] = [",".join([x, y]) if y != "" else x for x, y in zip(df["genre"], df["titleType"])]
df["genre"] = df["genre"].apply(lambda x: x if x != "\\N" else "")
df["genre"] = df["genre"].apply(lambda x: x.split(","))

df.fillna({"startYear": 0, "endYear": 0}, inplace=True)
df["startYear"] = df["startYear"].astype("int")
df["endYear"] = df["endYear"].astype("int")
df.drop(["titleType", "isAdult", "runtimeMinutes"], axis=1, inplace=True)
assert df.shape[0] == len(all_movies_ids), print("Number of samples less than number of movies")

print(f"Total time: {time() - t0}")

# # Collect names of actors etc

t0 = time()
fpath = "./title.principals.tsv.gz"

df_principals = pd.read_table(fpath)
df_principals = df_principals.loc[:, ["tconst", "nconst", "ordering", "category", "characters"]]
df_principals.rename(columns={"tconst": "imdb_id"}, inplace=True)
print(df_principals.head())

ind_drop = df_principals[~df_principals["imdb_id"].isin(all_movies_ids)].index
df_principals = df_principals.drop(ind_drop)
print(df_principals.head())

ind_drop = df_principals[~df_principals["ordering"].isin([1, 2, 3, 4, 5, 6])].index
df_principals = df_principals.drop(ind_drop)
print(df_principals.head())

df_principals["category"] = df_principals["category"].apply(lambda x: x if x != "actress" else "actor")
target_profs = ["director", "producer", "actor", "writer"]
ind_drop = df_principals[~df_principals["category"].isin(target_profs)].index
df_principals = df_principals.drop(ind_drop)
print(df_principals.head())

fpath = "./name.basics.tsv.gz"

df_names = pd.read_table(fpath)
df_names = df_names.loc[:, ["primaryName", "nconst"]]
print(df_names.head())

df_principals = df_principals.merge(df_names, on="nconst")
print(df_principals["characters"])

special_char = df_principals.loc[4, "characters"]
df_principals["characters"] = df_principals["characters"].apply(
    lambda x: [] if x == special_char or len(x) == 0 else json.loads(x)
)
print(df_principals.head())

print(f"Total time: {time() - t0}")

# # Collect persons
t0 = time()


def collect_movie_persons(x):
    return pd.Series(
        {
            f"{role}s": x.loc[x.sort_values(by=["ordering"])["category"] == prof, name].values.tolist()
            for prof, role, name in zip(
                ["director", "producer", "actor", "writer", "actor"],
                ["director", "producer", "actor", "writer", "character"],
                ["primaryName", "primaryName", "primaryName", "primaryName", "characters"],
            )
        }
    )


df_principals = pd.DataFrame(df_principals.groupby("imdb_id").apply(collect_movie_persons))
print(df_principals.head())
df_principals["characters"] = df_principals["characters"].apply(lambda x: sum(x, []) if isinstance(x, list) else [])
print(df_principals.head())

df.set_index("imdb_id", inplace=True)
df = df.join(df_principals, on="imdb_id")
df.reset_index(inplace=True)

df.fillna(value={f"{prof}s": "" for prof in target_profs}, inplace=True)

assert df.shape[0] == len(all_movies_ids), print("Number of samples less than number of movies")

print(f"Total time: {time() - t0}")

# # Collect alternative titles

t0 = time()

fpath = "./title.akas.tsv.gz"

df_akas = pd.read_table(fpath, low_memory=False)
df_akas = df_akas.loc[df_akas["region"] == "US", :]
df_akas.rename(columns={"titleId": "imdb_id"}, inplace=True)

ind_drop = df_akas[~df_akas["imdb_id"].isin(all_movies_ids)].index
df_akas = df_akas.drop(ind_drop)

grouped_data = df_akas.groupby("imdb_id")["title"].apply(lambda x: "::".join(x))
df_titles = pd.DataFrame(grouped_data)
df_titles.rename(columns={"title": "all_titles"}, inplace=True)

df.set_index("imdb_id", inplace=True)
df = df.join(df_titles, on="imdb_id")
df.reset_index(inplace=True)
df.fillna(value={"all_titles": ""}, inplace=True)

assert df.shape[0] == len(all_movies_ids), print("Number of samples less than number of movies")

print(f"Total time: {time() - t0}")

database = df.to_dict("records")
for el in database:
    el["genre"] = el["genre"] if el["genre"] != "" else None
    el["startYear"] = el["startYear"] if el["startYear"] != 0 else None
    el["endYear"] = el["endYear"] if el["endYear"] != 0 else None
    el["all_titles"] = el["all_titles"].split("::") if el["all_titles"] != "" else []
    for prof in ["director", "producer", "actor", "writer"]:
        el[f"{prof}s"] = list(el[f"{prof}s"]) if list(el[f"{prof}s"]) != "" else []

with open("database_most_popular_main_info.json", "w") as f:
    json.dump(database, f, indent=2)
