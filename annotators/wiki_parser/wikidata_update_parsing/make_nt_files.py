import argparse
import json
import multiprocessing as mp
import os
import re


parser = argparse.ArgumentParser()
parser.add_argument("-d", action="store", dest="parsing_dir")
parser.add_argument("-nt", action="store", dest="nt_dir")
args = parser.parse_args()


def run(i):
    files_in_dir = os.listdir(args.parsing_dir)
    black_list = set(
        [
            "Q13442814",  # scientific paper
            "Q67206691",  # infrared source
            "Q4167836",  # wikimedia category
            "Q7318358",  # review article
            "Q7187",  # gene
            "Q11173",  # chemical compound
            "Q8054",  # protein
            "Q4167410",  # disambiguation page
            "Q871232",  # editorial
            "Q1931185",  # astronomical radio source
            "Q30612",  # clinical trial
            "Q11266439",  # wikipedia template
            "Q2247863",  # high proper-motion star
            "Q1457376",  # eclipsing binary star
            "Q3863",  # asteroid
            "Q2782326",  # case report
            "Q83373",  # quasar
            "Q13406463",  # wikimedia list article
            "Q2154519",  # astrophysical x-ray source
            "Q49008",  # prime number
            "Q815382",  # meta-analysis
            "Q1153690",  # long period variable
            "Q726242",  # RR lyrae variable
            "Q427087",  # non-coding RNA
            "Q204107",  # galaxy cluster
            "Q71963409",  # compact group of galaxies
            "Q67206701",  # IR source
            "Q1151284",  # D galaxy
            "Q72802727",  # possible red giant star
            "Q66619666",  # Red giant branch star
            "Q22808320",  # wikimedia disambiguation page
            "Q67206785",  # near IR-source
            "Q277338",  # pseudogene
            "Q1348305",  # erratum
            "Q29654788",  # unicode character
            "Q13433827",  # encyclopedia article
            "Q72802508",  # emission-line galaxy
            "Q46587",  # active galactic nucleus
            "Q72802977",  # young stellar object candidate
            "Q11282",  # H II region
            "Q59542487",  # wikimedia set category
            "Q72803170",  # low-mass star
            "Q1332364",  # rotating ellipsoidal variable
            "Q497654",  # young stellar object
            "Q17329259",  # encyclopedia entry
            "Q4423781",  # dictionary entry
            "Q11753321",  # wikimedia navigation template
            "Q17633526",  # wikinews article
            "Q191067",  # article
            "Q13442814",  # scholarly article
        ]
    )

    black_list_rels = set(
        [
            "P59",  # constellation
            "P6259",  # epoch
            "P6257",  # right ascension
            "P6258",  # declination
            "P528",  # catalog code
            "P2215",  # proper motion
            "P2216",  # radial velocity
            "P2214",  # parallax
            "P171",  # parent taxon
            "P105",  # chromosome
            "P1435",  # heritage designation
            "P421",  # located in time zone
            "P1090",  # redshift
            "P217",  # inventory number
            "P6216",  # copyright status
            "P7959",  # historic county
            "P6879",  # effective temperature
            "P7015",  # surface gravity
            "P910",  # topic main category
            "P6224",  # level of description
            "P8363",  # study type
            "P225",  # taxon name
            "P881",  # type of variable star
            "P1436",  # collection or exhibition size
            "P1001",  # applied to jurisdiction
            "P463",  # the peerage person id
            "P2227",  # metallicity
            "P7261",  # use restriction status
            "P856",  # official website
            "P2002",  # twitter username
            "P7228",  # access restriction status
            "P1889",  # different from
            "P6099",  # clinical trial phase
            "P5008",  # on focus list of Wikimedia project
            "P1260",  # swedish open cultural heritage url
            "P18",  # image
            "P1538",  # number of households
            "P566",  # basionym
            "P2860",  # cites work
            "P1215",  # apparent magnitude
            "P1087",  # elo rating
            "P4080",  # number of houses
            "P6499",  # literate population
            "P6498",  # illiterate population
            "P1539",  # female population
            "P1540",  # male population
            "P703",  # found in taxon
            "P709",  # historic scotland id
            "P282",  # writing system
            "P3872",  # patronage
            "P1433",  # published in
            "P576",  # dissolved, abolished or demolished
            "P4533",  # Czech street ID
            "P7256",  # computer performance
            "P684",  # ortholog
            "P128",  # regulates
            "P1598",  # consecrator
            "P7763",  # copyright status
        ]
    )

    num_file = 0
    num_statements = 0
    not_included = 0
    added_triplets = 0
    out = open(f"{args.nt_dir}/wikidata_{i}.nt", "w")
    for j in range(1823):
        if f"{i}_{j}.json" in files_in_dir:
            fl = open(f"{args.parsing_dir}/{i}_{j}.json", "r")
            num_file += 1
            if num_file % 100 == 0:
                print(num_file, i, not_included, added_triplets)
            data = json.load(fl)
            for elem in data:
                triplets = data[elem]
                entity_types = set()
                for triplet in triplets:
                    if triplet[0] == "P31":
                        entity_types = set([obj[0] for obj in triplet[1:]])
                        break

                if entity_types.intersection(black_list):
                    not_included += 1
                else:
                    for triplet in triplets:
                        if triplet[0] == "name_ru":
                            name = triplet[1].replace('"', "'").replace("\\", "\\\\")
                            line = f'<http://we/{elem}> <http://wl> "{name}"@ru .'
                            out.write(line + "\n")
                            added_triplets += 1
                        elif triplet[0] == "name_en":
                            name = triplet[1].replace('"', "'").replace("\\", "\\\\")
                            line = f'<http://we/{elem}> <http://wl> "{name}"@en .'
                            out.write(line + "\n")
                            added_triplets += 1
                        elif triplet[0] == "aliases_ru":
                            for alias in triplet[1:]:
                                alias = alias.replace('"', "'").replace("\\", "\\\\")
                                line = f'<http://we/{elem}> <http://wal> "{name}"@ru .'
                                out.write(line + "\n")
                                added_triplets += 1
                        elif triplet[0] == "aliases_en":
                            for alias in triplet[1:]:
                                alias = alias.replace('"', "'").replace("\\", "\\\\")
                                line = f'<http://we/{elem}> <http://wal> "{name}"@en .'
                                out.write(line + "\n")
                                added_triplets += 1
                        elif triplet[0] == "descr_ru":
                            descr = triplet[1].replace('"', "'").replace("\\", "\\\\")
                            line = f'<http://we/{elem}> <http://wd> "{descr}"@ru .'
                            out.write(line + "\n")
                            added_triplets += 1
                        elif triplet[0] == "descr_en":
                            descr = triplet[1].replace('"', "'").replace("\\", "\\\\")
                            line = f'<http://we/{elem}> <http://wd> "{descr}"@en .'
                            out.write(line + "\n")
                            added_triplets += 1
                        else:
                            rel, *objects = triplet
                            if rel == "P2583" and elem == "Q111":
                                print(triplet)
                            if rel not in black_list_rels:
                                for obj in objects:
                                    if len(obj) == 1:
                                        if obj[0].startswith("Q"):
                                            line = f"<http://we/{elem}> <http://wpd/{rel}> <http://we/{obj[0]}> ."
                                            out.write(line + "\n")
                                        else:
                                            obj_line = obj[0].replace('"', "'")
                                            if re.findall(r"[\d]{3,4}-[\d]{1,2}-[\d]{1,2}", obj_line):
                                                line = f'<http://we/{elem}> <http://wpd/{rel}> "{obj_line}^^T" .'
                                            else:
                                                line = f'<http://we/{elem}> <http://wpd/{rel}> "{obj_line}^^D" .'
                                            out.write(line + "\n")
                                        added_triplets += 1
                                    if len(obj) >= 3:
                                        obj_1 = obj[0]
                                        line = (
                                            f"<http://we/{elem}> <http://wp/{rel}> <http://ws/{i}_{num_statements}> ."
                                        )
                                        out.write(line + "\n")

                                        if obj_1.startswith("Q"):
                                            line = (
                                                f"<http://ws/{i}_{num_statements}> <http://wps/{rel}> "
                                                + f"<http://we/{obj_1}> ."
                                            )
                                            out.write(line + "\n")
                                            line = f"<http://we/{elem}> <http://wpd/{rel}> <http://we/{obj_1}> ."
                                            out.write(line + "\n")
                                        else:
                                            obj_1 = obj_1.replace('"', "'")
                                            if re.findall(r"[\d]{3,4}-[\d]{1,2}-[\d]{1,2}", obj_1):
                                                line = (
                                                    f"<http://ws/{i}_{num_statements}> <http://wps/{rel}> "
                                                    + f'"{obj_1}^^T" .'
                                                )
                                            else:
                                                line = (
                                                    f"<http://ws/{i}_{num_statements}> <http://wps/{rel}> "
                                                    + f'"{obj_1}^^D" .'
                                                )
                                            out.write(line + "\n")

                                            if re.findall(r"[\d]{3,4}-[\d]{1,2}-[\d]{1,2}", obj_1):
                                                line = f'<http://we/{elem}> <http://wpd/{rel}> "{obj_1}^^T" .'
                                            else:
                                                line = f'<http://we/{elem}> <http://wpd/{rel}> "{obj_1}^^D" .'
                                            out.write(line + "\n")

                                        cur_rel = ""
                                        for obj_elem in obj[1:]:
                                            if obj_elem.startswith("P") and obj_elem[1].isdigit():
                                                cur_rel = obj_elem
                                            else:
                                                if cur_rel:
                                                    if obj_elem.startswith("Q"):
                                                        line = (
                                                            f"<http://ws/{i}_{num_statements}> "
                                                            + f"<http://wpq/{cur_rel}> <http://we/{obj_elem}> ."
                                                        )
                                                        out.write(line + "\n")
                                                    else:
                                                        obj_elem = obj_elem.replace('"', "'")
                                                        if re.findall(r"[\d]{3,4}-[\d]{1,2}-[\d]{1,2}", obj_elem):
                                                            line = (
                                                                f"<http://ws/{i}_{num_statements}> "
                                                                + f'<http://wpq/{cur_rel}> "{obj_elem}^^T" .'
                                                            )
                                                        else:
                                                            line = (
                                                                f"<http://ws/{i}_{num_statements}> "
                                                                + f'<http://wpq/{cur_rel}> "{obj_elem}^^D" .'
                                                            )
                                                        out.write(line + "\n")

                                        added_triplets += len(obj)
                                        num_statements += 1

    out.close()
    print("finished", i)


procs = []
for i in range(8):
    proc = mp.Process(target=run, args=(i,))
    procs.append(proc)
    proc.start()

for proc in procs:
    proc.join()

print("total finish")
